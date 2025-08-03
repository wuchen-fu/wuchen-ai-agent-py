import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Iterator, AsyncIterator

from langchain_core.messages import BaseMessage
from langchain_core.tools import BaseTool
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_openai.chat_models import ChatOpenAI
import os

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    智能体基类，只负责定义接口规范
    所有具体功能由子类实现
    """
    
    # 子类需要重写的配置
    AGENT_TYPE = None

    def __init__(self, config: Optional[Dict] = None):
        """
        初始化基础智能体配置
        
        Args:
            config: 智能体配置字典
        """
        self.config = config or {}
        self.model_provider_manager = self.config.get('model_provider_manager')

    def get_chat_model(self, provider_name: str = None, model_name: str = None, **kwargs):
        """
        获取聊天模型实例
        
        Args:
            provider_name: 模型提供商名称
            model_name: 模型名称
            **kwargs: 其他参数
            
        Returns:
            聊天模型实例
        """
        if self.model_provider_manager:
            # 如果没有指定提供商，使用默认提供商
            if not provider_name:
                provider_name = self.model_provider_manager.get_default_provider()
                logger.info(f"使用默认提供商: {provider_name}")
            
            try:
                return self.model_provider_manager.get_chat_model(provider_name, model_name, **kwargs)
            except Exception as e:
                logger.warning(f"从提供商管理器获取模型失败: {e}")
                # 如果从提供商管理器获取失败，回退到环境变量配置的默认模型
                pass
        
        # 如果没有模型提供商管理器或获取失败，从配置中获取chat_model或使用环境变量创建
        chat_model = self.config.get("chat_model")
        if chat_model:
            return chat_model
            
        # 最后的回退方案：使用环境变量配置的默认模型
        logger.info("使用环境变量配置的默认模型")
        return ChatOpenAI(
            model=os.getenv('QWEN_MODEL'),
            api_key=os.getenv('QWEN_API_KEY'),
            base_url=os.getenv('QWEN_URL')
        )

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
    def stream_chat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> Iterator[str]:
        """
        与智能体进行流式对话，由子类实现
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            
        Yields:
            智能体的回复片段
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

    @abstractmethod
    async def astream_chat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> AsyncIterator[str]:
        """
        异步与智能体进行流式对话，由子类实现
        
        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            
        Yields:
            智能体的回复片段
        """
        pass

    @abstractmethod
    def get_history(self, chat_id: str) -> List[BaseMessage]:
        """
        获取指定会话的历史记录，由子类实现
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            历史消息列表
        """
        pass

    @abstractmethod
    def clear_history(self, chat_id: str):
        """
        清除指定会话的历史记录，由子类实现
        
        Args:
            chat_id: 聊天ID
        """
        pass

    def get_agent_type(self) -> str:
        """
        获取Agent类型
        
        Returns:
            Agent类型字符串
        """
        return self.AGENT_TYPE or self.__class__.__name__.lower().replace('agent', '')