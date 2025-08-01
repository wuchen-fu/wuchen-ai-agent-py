import logging
from typing import Optional, List, Dict

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory as LangChainRunnableWithMessageHistory, Runnable

from tools.rag_tool import get_vector_store
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
'''

prompt_template = ChatPromptTemplate.from_messages([
    ('system', system_prompt),
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

    def __init__(self, chat_model, rag_chain: Optional[Runnable] = None):
        """
        初始化写作智能体
        
        Args:
            chat_model: 聊天模型实例
            rag_chain: RAG链（可选）
        """
        # 设置全局chat_model引用
        global chain1, chain2, chain
        
        # 初始化RAG链
        if chain1 is None:
            chain1 = create_stuff_documents_chain(chat_model, prompt_template)
            
        if chain2 is None:
            chain2 = create_history_aware_retriever(chat_model, get_vector_store().as_retriever(), 
                                                  ChatPromptTemplate.from_messages([
                                                      ('system', '''
给我一个历史的聊天记录以即用户最新提出的问题。
在我们的聊天记录中引用我们的上下文内容，得到一个独立的问题。
当没有聊天记录的时候，不需要回答这个问题。
直接返回问题就可以了。
                                                      '''),
                                                      MessagesPlaceholder(variable_name='chat_history'),
                                                      ('human', '{input}'),
                                                  ]))
            
        if chain is None:
            chain = create_retrieval_chain(chain2, chain1)
        
        # 调用父类构造函数
        super().__init__(chat_model, prompt_template, rag_chain or chain)
        
        # 覆盖BaseAgent的history_chain以使用LangChain的实现
        self.history_chain = LangChainRunnableWithMessageHistory(
            self.rag_chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )
        
        self.history_map: Dict[str, ChatMessageHistory] = {}

    def get_session_history(self, session_id: str) -> ChatMessageHistory:
        """
        获取会话历史记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史记录对象
        """
        if session_id not in self.history_map:
            self.history_map[session_id] = ChatMessageHistory()
        return self.history_map[session_id]

    def _build_agent(self) -> AgentExecutor:
        """
        构建智能体
        
        Returns:
            AgentExecutor: 构建的智能体执行器
        """
        # 写作智能体暂时不使用工具
        return create_tool_calling_agent(
            self.chat_model, 
            self.tools, 
            self.prompt_template
        )

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