import os
import sys
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from tools.rag_tool import get_vector_store

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)


class SimpleRAGAgent:
    """
    简化版RAG Agent，减少LLM调用次数以降低成本
    """
    def __init__(self):
        # 获取向量存储
        vector_store = get_vector_store()
        self.retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        # 使用单个模型处理所有任务以降低成本
        self.chat_model = ChatOpenAI(
            model=os.getenv('DASH_SCOPE_MODEL'),
            api_key=os.getenv('DASH_SCOPE_API_KEY'),
            base_url=os.getenv('DASH_SCOPE_URL')
        )

        # 简化的提示词模板
        self.prompt_template = PromptTemplate.from_template(
            """
            你是问答任务的助手。使用以下检索到的上下文来回答问题。
            如果检索到的上下文与问题无关，请根据你的知识回答问题。
            不知道答案就说不知道。保持回答合理简洁。
            
            问题: {question} 
            
            检索到的上下文: 
            {context}
            """
        )

    def _format_docs(self, docs):
        """
        格式化检索到的文档
        """
        return "\n\n".join(doc.page_content for doc in docs)

    def invoke(self, query: str):
        """
        简化版RAG流程，只需调用一次LLM
        
        Args:
            query: 用户查询
            
        Returns:
            模型回答
        """
        # 检索相关文档
        docs = self.retriever.invoke(query)
        context = self._format_docs(docs)
        
        # 构造提示词
        prompt = self.prompt_template.format(question=query, context=context)
        
        # 调用LLM生成答案（仅一次调用）
        response = self.chat_model.invoke(prompt)
        
        return response.content

    def stream(self, query: str):
        """
        流式调用简化版RAG流程
        
        Args:
            query: 用户查询
            
        Yields:
            模型回答的流式内容
        """
        # 检索相关文档
        docs = self.retriever.invoke(query)
        context = self._format_docs(docs)
        
        # 构造提示词
        prompt = self.prompt_template.format(question=query, context=context)
        
        # 流式调用LLM生成答案（仅一次调用）
        response = self.chat_model.stream(prompt)
        
        for chunk in response:
            yield chunk.content