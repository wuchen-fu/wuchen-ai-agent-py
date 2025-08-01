from abc import ABC, abstractmethod
from typing import List, Union, Optional, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class BaseChatHistory(ABC):
    """
    抽象基类，定义聊天历史存储的接口
    类似于LangChain的BaseChatMessageHistory
    """

    @abstractmethod
    def add_message(self, message: BaseMessage) -> None:
        """
        添加一条消息到聊天历史
        
        Args:
            message: 要添加的消息
        """
        pass

    @abstractmethod
    def add_user_message(self, message: Union[str, BaseMessage]) -> None:
        """
        添加用户消息到聊天历史
        
        Args:
            message: 用户消息内容或消息对象
        """
        pass

    @abstractmethod
    def add_ai_message(self, message: Union[str, BaseMessage]) -> None:
        """
        添加AI消息到聊天历史
        
        Args:
            message: AI消息内容或消息对象
        """
        pass

    @abstractmethod
    def get_messages(self) -> List[BaseMessage]:
        """
        获取所有聊天历史消息
        
        Returns:
            消息列表
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        清空聊天历史
        """
        pass


class InMemoryChatHistory(BaseChatHistory):
    """
    基于内存的聊天历史存储实现
    """

    def __init__(self):
        self.messages: List[BaseMessage] = []

    def add_message(self, message: BaseMessage) -> None:
        """
        添加一条消息到聊天历史
        
        Args:
            message: 要添加的消息
        """
        self.messages.append(message)

    def add_user_message(self, message: Union[str, BaseMessage]) -> None:
        """
        添加用户消息到聊天历史
        
        Args:
            message: 用户消息内容或消息对象
        """
        if isinstance(message, str):
            self.messages.append(HumanMessage(content=message))
        else:
            self.messages.append(message)

    def add_ai_message(self, message: Union[str, BaseMessage]) -> None:
        """
        添加AI消息到聊天历史
        
        Args:
            message: AI消息内容或消息对象
        """
        if isinstance(message, str):
            self.messages.append(AIMessage(content=message))
        else:
            self.messages.append(message)

    def get_messages(self) -> List[BaseMessage]:
        """
        获取所有聊天历史消息
        
        Returns:
            消息列表
        """
        return self.messages

    def clear(self) -> None:
        """
        清空聊天历史
        """
        self.messages = []


class RedisChatHistory(BaseChatHistory):
    """
    基于Redis的聊天历史存储实现
    """

    def __init__(self, memory_store, user_id: str, session_id: str):
        self.memory_store = memory_store
        self.user_id = user_id
        self.session_id = session_id

    def add_message(self, message: BaseMessage) -> None:
        """
        添加一条消息到聊天历史和Redis存储
        
        Args:
            message: 要添加的消息
        """
        # 保存到Redis
        if isinstance(message, HumanMessage):
            message_type = "human"
        elif isinstance(message, AIMessage):
            message_type = "ai"
        elif isinstance(message, SystemMessage):
            message_type = "system"
        else:
            message_type = "other"
            
        self.memory_store.save_message(
            user_id=self.user_id,
            session_id=f"{self.session_id}_{message_type}",
            message=message,
            message_type=message_type
        )

    def add_user_message(self, message: Union[str, BaseMessage]) -> None:
        """
        添加用户消息到聊天历史
        
        Args:
            message: 用户消息内容或消息对象
        """
        if isinstance(message, str):
            msg = HumanMessage(content=message)
        else:
            msg = message
        self.add_message(msg)

    def add_ai_message(self, message: Union[str, BaseMessage]) -> None:
        """
        添加AI消息到聊天历史
        
        Args:
            message: AI消息内容或消息对象
        """
        if isinstance(message, str):
            msg = AIMessage(content=message)
        else:
            msg = message
        self.add_message(msg)

    def get_messages(self) -> List[BaseMessage]:
        """
        从Redis获取所有聊天历史消息
        
        Returns:
            消息列表
        """
        redis_messages = self.memory_store.get_messages(self.user_id)
        
        # 按时间排序消息
        sorted_messages = sorted(redis_messages, key=lambda x: x.get('created_at', ''))
        
        # 将Redis中的消息转换为LangChain消息类型
        messages = []
        for msg in sorted_messages:
            # 解析存储的数据格式 "User: message" 或 "AI: message"
            data = msg.get('value', {}).get('data', '')
            if data.startswith('User: '):
                content = data[6:]  # 去掉 "User: " 前缀
                messages.append(HumanMessage(content=content))
            elif data.startswith('AI: '):
                content = data[4:]  # 去掉 "AI: " 前缀
                messages.append(AIMessage(content=content))
        
        return messages

    def clear(self) -> None:
        """
        清空聊天历史
        """
        # 清空Redis中的聊天历史
        self.memory_store.delete_messages(self.user_id)