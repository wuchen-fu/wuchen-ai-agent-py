import os
import sys
from typing import Literal
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import PromptTemplate
from tools.rag_tool import get_vector_store
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)


class GradeDocuments(BaseModel):
    """
    使用二分类判断对文档进行评分以进行相关性检查
    """
    binary_score: str = Field(
        description="相关性判断：如果相关，则为\"True\"，如果不相关，则为\"False\""
    )


class RAGAgent:
    def __init__(self):
        # 导入向量
        vector_store = get_vector_store()
        retriever = vector_store.as_retriever()

        self.retriever_tool = create_retriever_tool(
            retriever=retriever,
            name="retriever_tool",
            description="向量数据库工具,根据用户的提问搜索向量库并返回有用的文档信息"
        )

        # 聊天检索和响应模型
        self.chat_model_qa = ChatOpenAI(
            model=os.getenv('QWEN_MODEL'),
            api_key=os.getenv('QWEN_API_KEY'),
            base_url=os.getenv('QWEN_URL')
        )

        # 文档相关性评估模型
        self.chat_model_grader = ChatOpenAI(
            model=os.getenv('QWEN_MODEL'),
            api_key=os.getenv('QWEN_API_KEY'),
            base_url=os.getenv('QWEN_URL')
        )

        # 文档相关性评估提示词
        self.grade_prompt = PromptTemplate.from_template(
            """
            您是评估检索到的文档与用户问题的相关性的评分员。
            这是检索到的文档：
            
            {context}
            
            这是用户问题：{question}
            如果文档包含与用户问题相关的关键字或语义含义，请将其评为相关。
            给一个二分类判断'True'或'False'判断，以表明该文档是否与问题相关。
            请以JSON格式返回结果，返回格式示例：{{"binary_score": "True"}} 或 {{"binary_score": "False"}}
            """
        )

        # 问题重写提示词
        self.rewrite_prompt = PromptTemplate.from_template(
            """
            分析问题的语义意图并更并尝试推理潜在的语义意图含义,进行问题的重写
            原始问题:
            {question}
            
            重写后的问题:
            """
        )

        # 回答生成提示词
        self.generate_prompt = PromptTemplate.from_template(
            """
            你是问答任务的助手。
            使用以下检索到的上下文来回答问题。
            不知道答案就说不知道。
            保持回答合理简洁。
            Question: {question} 
            Context: {context}
            """
        )

        # 组装graph工作流
        self.workflow = StateGraph(MessagesState)

        # 定义节点
        self.workflow.add_node("generate_query_or_respond", self._generate_query_or_respond)
        self.workflow.add_node("retrieve", ToolNode([self.retriever_tool]))
        self.workflow.add_node("rewrite_question", self._rewrite_question)
        self.workflow.add_node("generate_answer", self._generate_answer)

        # 定义边
        self.workflow.add_edge("__start__", "generate_query_or_respond")

        # 决定是否检索
        self.workflow.add_conditional_edges(
            "generate_query_or_respond",
            tools_condition,
            {
                "tools": "retrieve",
                "__end__": "__end__",
            },
        )

        # 评估文档相关性
        self.workflow.add_conditional_edges(
            "retrieve",
            self._grade_documents,
        )
        self.workflow.add_edge("generate_answer", "__end__")
        self.workflow.add_edge("rewrite_question", "generate_query_or_respond")

        # 编译工作流
        self.app = self.workflow.compile()

    def _generate_query_or_respond(self, state: MessagesState):
        """
        根据对话状态调用模型,决定是否使用检索工具
        """
        response = (
            self.chat_model_qa
            .bind_tools([self.retriever_tool]).invoke(state["messages"])
        )
        return {"messages": [response]}

    def _grade_documents(self, state: MessagesState) -> Literal["generate_answer", "rewrite_question"]:
        """
        确定检索到的文档是否与问题相关。
        """
        question = state["messages"][0].content
        context = state["messages"][-1].content

        prompt = self.grade_prompt.format(question=question, context=context)
        response = (
            self.chat_model_grader
            .with_structured_output(GradeDocuments).invoke(
                [{"role": "user", "content": prompt}]
            )
        )
        score = response.binary_score

        if score == "True":
            return "generate_answer"
        else:
            return "rewrite_question"

    def _rewrite_question(self, state: MessagesState):
        """
        当检索结果不相关时，重写用户原始提问
        """
        question = state["messages"][0].content
        prompt = self.rewrite_prompt.format(question=question)
        resp = self.chat_model_qa.invoke([{"role": "user", "content": prompt}])
        return {"messages": [{"role": "user", "content": resp.content}]}

    def _generate_answer(self, state: MessagesState):
        """
        将相关文档上下文与问题一起传给模型，生成简洁回答
        """
        question = state["messages"][0].content
        context = state["messages"][-1].content
        prompt = self.generate_prompt.format(question=question, context=context)
        resp = self.chat_model_qa.invoke([{"role": "user", "content": prompt}])
        return {"messages": [resp]}

    def invoke(self, input_query: str):
        """
        调用RAG Agent处理用户查询
        """
        user_input = {
            "messages": [{"role": "user", "content": input_query}]
        }
        return self.app.invoke(user_input)

    def stream(self, input_query: str):
        """
        流式调用RAG Agent处理用户查询
        """
        user_input = {
            "messages": [{"role": "user", "content": input_query}]
        }
        return self.app.stream(user_input)