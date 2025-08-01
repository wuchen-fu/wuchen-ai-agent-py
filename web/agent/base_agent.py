import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from langchain.agents import AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import BaseTool

from chat_memory.chat_history import BaseChatHistory
from tools.tool_config import ToolConfig

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    智能体基类，只作为初始智能体构造对话
    知识库是否使用和对话是否记录由继承的实体类自行实现
    """
    
    def __init__(self, chat_model,
                 prompt_template: ChatPromptTemplate,
                 chat_memory : BaseChatMessageHistory,
                 rag_chain: Optional[Runnable] = None):
        """
        初始化基础智能体
        
        Args:
            chat_model: 聊天模型实例
            prompt_template: 提示词模板
            rag_chain: RAG链（可选）
        """
        self.chat_model = chat_model
        self.prompt_template = prompt_template
        self.rag_chain = rag_chain
        self.all_tools = ToolConfig()
        
        # 创建基础链
        self.chain = prompt_template | chat_model
        
        
        # 在初始化时将工具绑定到模型
        self._bind_tools_to_model()
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.history_backend: Optional[BaseChatHistory] = None
        self.history_map: Dict[str, BaseChatHistory] = {}
        
        # 创建带历史记录的链
        self.history_chain = RunnableWithMessageHistory(
            self.chain,
            self.get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

    def _bind_tools_to_model(self):
        """
        将工具绑定到模型
        """
        tools = self.all_tools.get_tools()
        if tools:
            # 使用标准的bind_tools方法将工具绑定到模型
            self.chat_model = self.chat_model.bind_tools(tools)
            # 更新基础链以包含绑定工具的模型
            self.chain = self.prompt_template | self.chat_model
    def set_history_backend(self, history_backend: BaseChatHistory):
        """
        设置历史记录后端
        
        Args:
            history_backend: 历史记录后端实例
        """
        self.history_backend = history_backend

    def get_session_history(self, session_id: str) -> BaseChatHistory:
        """
        获取会话历史记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史记录对象
        """
        if session_id not in self.history_map:
            # 如果没有指定后端，则使用传入的后端或创建内存后端
            if self.history_backend:
                self.history_map[session_id] = self.history_backend
            else:
                from chat_memory.chat_history import InMemoryChatHistory
                self.history_map[session_id] = InMemoryChatHistory()
        
        return self.history_map[session_id]

    def add_tool(self, tool: BaseTool):
        """
        添加工具到智能体
        
        Args:
            tool: 要添加的工具
        """
        self.all_tools.add_tool(tool)
        # 重新绑定所有工具到模型
        self._bind_tools_to_model()

    def add_tools(self, tools: List[BaseTool]):
        """
        批量添加工具到智能体
        
        Args:
            tools: 要添加的工具列表
        """
        self.all_tools.add_tools(tools)
        # 重新绑定所有工具到模型
        self._bind_tools_to_model()

    @abstractmethod
    def _build_agent(self) -> AgentExecutor:
        """
        构建智能体，由子类实现
        
        Returns:
            AgentExecutor: 构建的智能体执行器
        """
        pass

    @abstractmethod
    def chat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> str:
        """
        与智能体进行对话，由子类实现
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            
        Returns:
            智能体的回复
        """
        pass

    @abstractmethod
    async def achat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> str:
        """
        异步与智能体进行对话，由子类实现
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            
        Returns:
            智能体的回复
        """
        pass

    def get_history(self, chat_id: str) -> List[BaseMessage]:
        """
        获取指定会话的历史记录，由子类实现
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            历史消息列表
        """
        # 默认实现返回空列表，子类应重写此方法
        return []

    def clear_history(self, chat_id: str):
        """
        清除指定会话的历史记录，由子类实现
        
        Args:
            chat_id: 聊天ID
        """
        # 默认实现不执行任何操作，子类应重写此方法
        pass