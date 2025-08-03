import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

# 用于存储会话历史的全局存储
store: Dict[str, BaseChatMessageHistory] = {}


class BaseAgent(ABC):
    """
    智能体基类，只作为初始智能体构造对话
    知识库是否使用和对话是否记录由继承的实体类自行实现
    """
    
    def __init__(self, chat_model, system_prompt: str,
                 memory: Optional[BaseChatMessageHistory] = None,
                 # rag_chain: Optional[Runnable] = None,
                 all_tools: Optional[List[BaseTool]] = None):
        """
        初始化基础智能体
        
        Args:
            chat_model: 聊天模型实例
            system_prompt: 系统提示词
            memory: 聊天历史存储对象（可选）
            rag_chain: RAG链（可选）
            all_tools: 工具列表（可选）
        """
        self.chat_model = chat_model
        self.system_prompt = system_prompt
        # self.rag_chain = rag_chain
        self.all_tools = all_tools or []
        self.memory = memory
        
        # 创建提示词模板
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        # 创建默认的代理执行器
        self.agent_executor = self._create_default_agent_executor()

    def _create_default_agent_executor(self):
        """
        创建默认的代理执行器
        
        Returns:
            AgentExecutor: 默认的代理执行器
        """
        # 绑定工具到模型
        if self.all_tools:
            bound_model = self.chat_model.bind_tools(self.all_tools)
        else:
            bound_model = self.chat_model
            
        # 创建代理
        agent = create_tool_calling_agent(bound_model, self.all_tools, self.prompt)
        
        # 创建代理执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.all_tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        # 如果没有提供聊天历史后端，则使用内存存储
        if self.memory is None:
            def get_session_history(session_id: str) -> BaseChatMessageHistory:
                if session_id not in store:
                    store[session_id] = InMemoryChatMessageHistory()
                return store[session_id]
            
            # 创建带历史记录的执行器
            return RunnableWithMessageHistory(
                agent_executor,
                get_session_history,
                input_messages_key="question",
                history_messages_key="chat_history"
            )
        else:
            # 如果提供了聊天历史后端，直接返回基础执行器
            # 子类可以重写此方法以提供更复杂的实现
            return agent_executor

    def set_memory(self, memory: BaseChatMessageHistory):
        """
        设置历史记录后端
        
        Args:
            memory: 历史记录后端实例
        """
        self.memory = memory

    def get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """
        获取会话历史记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史记录对象
        """
        # 如果没有指定后端，则使用传入的后端或创建内存后端
        if self.memory is not None:
            return self.memory
        else:
            # 使用InMemoryChatMessageHistory作为默认处理
            return InMemoryChatMessageHistory()

    def add_tool(self, tool: BaseTool):
        """
        添加工具到智能体
        
        Args:
            tool: 要添加的工具
        """
        if self.all_tools is not None:
            self.all_tools.append(tool)
            # 重新创建代理执行器以包含新工具
            self.agent_executor = self._create_default_agent_executor()

    def add_tools(self, tools: List[BaseTool]):
        """
        批量添加工具到智能体
        
        Args:
            tools: 要添加的工具列表
        """
        if self.all_tools is not None:
            self.all_tools.extend(tools)
            # 重新创建代理执行器以包含新工具
            self.agent_executor = self._create_default_agent_executor()

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