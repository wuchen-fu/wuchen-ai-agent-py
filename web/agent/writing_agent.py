import logging
from typing import Optional, List, Dict

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory as LangChainRunnableWithMessageHistory, Runnable, \
    RunnableWithMessageHistory

from chat_memory.mongo_chat_memory import MongoChatMemory
from tools.rag_tool import get_vector_store
from tools.web_search_toolkit import WebSearchToolkit
from .base_agent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 提示词模板
system_prompt = '''
   你是一位专业的的小说作者，有丰富的小说经验和指导新人写小说经验。
   引导用户描述内容、设定,以及想法,给出相对应的指导
   核心能力：
   教学指导：将复杂技巧拆解为三步实操法
   文本分析：诊断+带注释修改示范
   创作示范：生成符合网文平台特性的内容
   你要用下面检索器检索出来的内容回答问题。
   如果不知道的话,就自行判断是否要通过工具进行网络查询
   工作规则：  
   1. 基于「上下文-问题转化器」输出的独立问题，先查看检索内容（{context}）：  
      - 若{context}有相关信息，结合信息回答；  
      - 若{context}无相关信息，进入工具调用判断。  

   2. 工具调用判断（不限制问题领域）：  
      - 无论问题属于小说创作、生活服务、信息查询等任何领域，只要存在对应的绑定工具，就调用工具获取信息后回答；  
      - 若没有对应工具，基于自身知识回答（若自身不知道，明确说明“无法回答该问题”）。 
   '''

qa_prompt = ChatPromptTemplate.from_messages([
    ('system', '''
                   你是「上下文-问题转化器」，负责从历史聊天记录和用户最新提问中，提炼出独立、完整的核心问题。  
                   工作规则：  
                   1. 若有历史记录，分析与最新问题的关联，提炼出不依赖上下文也能理解的问题。  
                   2. 若历史记录与新问题无关（或无历史记录），直接返回新问题作为独立问题。  
                   3. 仅返回问题，不添加任何额外内容。
                   '''),
    MessagesPlaceholder(variable_name='chat_history'),
    ('human', '{input}'),
])

vector_store = get_vector_store()

# 定义全局变量，将在初始化时设置
chat_model = None

# 提问链路和RAG链将在创建实例时初始化
chain1 = None
chain2 = None
chain = None


class WritingAgent(BaseAgent):
    """
    写作智能体，继承自BaseAgent
    实现具体的对话逻辑、历史记录管理等
    """

    def __init__(self, chat_model):
        """
        初始化写作智能体
        
        Args:
            chat_model: 聊天模型实例
            rag_chain: RAG链（可选）
        """
        prompt_template = ChatPromptTemplate.from_messages([
            ('system', system_prompt),
            MessagesPlaceholder(variable_name='chat_history'),
            ('human', '{input}'),
        ])
        bind_chat = chat_model.bind_tools(WebSearchToolkit().get_tools())
        # 问题重写lian
        qa_chain = create_history_aware_retriever(bind_chat, get_vector_store().as_retriever(), qa_prompt)

        # 提问链
        question_chain = create_stuff_documents_chain(bind_chat, prompt_template)

        rag_chain = create_retrieval_chain(qa_chain, question_chain)

        # 覆盖BaseAgent的history_chain以使用LangChain的实现
        self.history_chain = RunnableWithMessageHistory(
            rag_chain,
            MongoChatMemory.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )
        
        # 调用父类构造函数
        super().__init__(chat_model, system_prompt, None,None)

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        获取会话历史记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史记录对象
        """

    def _build_agent(self) -> AgentExecutor:
        """
        构建智能体
        
        Returns:
            AgentExecutor: 构建的智能体执行器
        """

    def chat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> str:
        """
        与智能体进行对话
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            
        Returns:
            智能体的回复
        """
        try:
            # 准备输入数据
            input_data = {"input": message}
            
            # 使用带历史记录的链进行调用
            config = {"configurable": {"session_id": chat_id}}
            response = self.history_chain.invoke(input_data, config=config)
            
            # 返回响应内容
            if isinstance(response, dict):
                return response.get("answer", str(response))
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"智能体对话出错: {e}")
            return "抱歉，我在处理您的问题时遇到了错误。"

    async def achat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> str:
        """
        异步与智能体进行对话
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            
        Returns:
            智能体的回复
        """
        try:
            # 准备输入数据
            input_data = {"input": message}
            
            # 使用带历史记录的链进行调用
            config = {"configurable": {"session_id": chat_id}}
            response = await self.history_chain.ainvoke(input_data, config=config)
            
            # 返回响应内容
            if isinstance(response, dict):
                return response.get("answer", str(response))
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"智能体对话出错: {e}")
            return "抱歉，我在处理您的问题时遇到了错误。"

    def get_history(self, chat_id: str) -> List[BaseMessage]:
        """
        获取指定会话的历史记录
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            历史消息列表
        """
        history = self.get_session_history(chat_id)
        return history.messages

    def clear_history(self, chat_id: str):
        """
        清除指定会话的历史记录
        
        Args:
            chat_id: 聊天ID
        """
        history = self.get_session_history(chat_id)
        history.clear()
        if chat_id in self.history_map:
            del self.history_map[chat_id]