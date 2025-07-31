from typing import Callable, Any, Union, Dict, List, Optional
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from chat_memory.chat_history import BaseChatHistory


class ChatHistoryManager:
    """
    管理聊天历史的类，类似于LangChain的RunnableWithMessageHistory
    负责在调用Runnable之前加载消息历史，在调用之后保存响应
    """

    def __init__(
        self,
        runnable: Runnable,
        get_session_history: Callable[[str], BaseChatHistory],
        input_messages_key: Optional[str] = None,
        history_messages_key: Optional[str] = None,
        output_messages_key: Optional[str] = None,
    ):
        """
        初始化聊天历史管理器
        
        Args:
            runnable: 要包装的Runnable对象
            get_session_history: 获取会话历史的函数，接收session_id，返回BaseChatHistory实例
            input_messages_key: 输入消息的键名
            history_messages_key: 历史消息在提示词中的键名
            output_messages_key: 输出消息的键名
        """
        self.runnable = runnable
        self.get_session_history = get_session_history
        self.input_messages_key = input_messages_key
        self.history_messages_key = history_messages_key or "chat_history"
        self.output_messages_key = output_messages_key

    def invoke(self, input: Union[Dict[str, Any], List[BaseMessage]], config: Optional[Dict[str, Any]] = None) -> Any:
        """
        调用Runnable，自动管理聊天历史
        
        Args:
            input: 输入数据，可以是字典或BaseMessage列表
            config: 配置信息，必须包含configurable.session_id
            
        Returns:
            Runnable的输出结果
        """
        # 获取session_id
        if not config or "configurable" not in config or "session_id" not in config["configurable"]:
            raise ValueError("config必须包含configurable.session_id")
        
        session_id = config["configurable"]["session_id"]
        chat_history = self.get_session_history(session_id)
        
        # 获取历史消息
        history_messages = chat_history.get_messages()
        
        # 准备输入数据
        if isinstance(input, list):
            # 输入是BaseMessage列表
            messages = input
        elif isinstance(input, dict):
            # 输入是字典
            if self.input_messages_key and self.input_messages_key in input:
                messages = input[self.input_messages_key]
            else:
                messages = []
            
            # 将历史消息添加到输入中
            input[self.history_messages_key] = history_messages
        else:
            raise ValueError("输入必须是字典或BaseMessage列表")
        
        # 调用Runnable
        response = self.runnable.invoke(input, config)
        
        # 保存消息到历史记录
        # 保存输入消息
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, BaseMessage):
                    chat_history.add_message(message)
        elif isinstance(messages, BaseMessage):
            chat_history.add_message(messages)
        
        # 保存响应消息
        if self.output_messages_key and isinstance(response, dict) and self.output_messages_key in response:
            # 从响应字典中提取输出消息
            output_message = response[self.output_messages_key]
            if isinstance(output_message, str):
                chat_history.add_ai_message(output_message)
            elif isinstance(output_message, BaseMessage):
                chat_history.add_message(output_message)
        else:
            # 直接保存响应
            if isinstance(response, str):
                chat_history.add_ai_message(response)
            elif isinstance(response, BaseMessage):
                chat_history.add_message(response)
        
        return response

    async def ainvoke(self, input: Union[Dict[str, Any], List[BaseMessage]], config: Optional[Dict[str, Any]] = None) -> Any:
        """
        异步调用Runnable，自动管理聊天历史
        
        Args:
            input: 输入数据，可以是字典或BaseMessage列表
            config: 配置信息，必须包含configurable.session_id
            
        Returns:
            Runnable的输出结果
        """
        # 获取session_id
        if not config or "configurable" not in config or "session_id" not in config["configurable"]:
            raise ValueError("config必须包含configurable.session_id")
        
        session_id = config["configurable"]["session_id"]
        chat_history = self.get_session_history(session_id)
        
        # 获取历史消息
        history_messages = chat_history.get_messages()
        
        # 准备输入数据
        if isinstance(input, list):
            # 输入是BaseMessage列表
            messages = input
        elif isinstance(input, dict):
            # 输入是字典
            if self.input_messages_key and self.input_messages_key in input:
                messages = input[self.input_messages_key]
            else:
                messages = []
            
            # 将历史消息添加到输入中
            input[self.history_messages_key] = history_messages
        else:
            raise ValueError("输入必须是字典或BaseMessage列表")
        
        # 调用Runnable
        response = await self.runnable.ainvoke(input, config)
        
        # 保存消息到历史记录
        # 保存输入消息
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, BaseMessage):
                    chat_history.add_message(message)
        elif isinstance(messages, BaseMessage):
            chat_history.add_message(messages)
        
        # 保存响应消息
        if self.output_messages_key and isinstance(response, dict) and self.output_messages_key in response:
            # 从响应字典中提取输出消息
            output_message = response[self.output_messages_key]
            if isinstance(output_message, str):
                chat_history.add_ai_message(output_message)
            elif isinstance(output_message, BaseMessage):
                chat_history.add_message(output_message)
        else:
            # 直接保存响应
            if isinstance(response, str):
                chat_history.add_ai_message(response)
            elif isinstance(response, BaseMessage):
                chat_history.add_message(response)
        
        return response

    def stream(self, input: Union[Dict[str, Any], List[BaseMessage]], config: Optional[Dict[str, Any]] = None):
        """
        流式调用Runnable，自动管理聊天历史
        
        Args:
            input: 输入数据，可以是字典或BaseMessage列表
            config: 配置信息，必须包含configurable.session_id
            
        Yields:
            Runnable的流式输出结果
        """
        # 获取session_id
        if not config or "configurable" not in config or "session_id" not in config["configurable"]:
            raise ValueError("config必须包含configurable.session_id")
        
        session_id = config["configurable"]["session_id"]
        chat_history = self.get_session_history(session_id)
        
        # 获取历史消息
        history_messages = chat_history.get_messages()
        
        # 准备输入数据
        if isinstance(input, list):
            # 输入是BaseMessage列表
            messages = input
        elif isinstance(input, dict):
            # 输入是字典
            if self.input_messages_key and self.input_messages_key in input:
                messages = input[self.input_messages_key]
            else:
                messages = []
            
            # 将历史消息添加到输入中
            input[self.history_messages_key] = history_messages
        else:
            raise ValueError("输入必须是字典或BaseMessage列表")
        
        # 保存输入消息
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, BaseMessage):
                    chat_history.add_message(message)
        elif isinstance(messages, BaseMessage):
            chat_history.add_message(messages)
        
        # 用于收集响应内容
        full_response = ""
        
        # 流式调用Runnable
        for chunk in self.runnable.stream(input, config):
            full_response += chunk.content if hasattr(chunk, 'content') else str(chunk)
            yield chunk
        
        # 保存完整响应到历史记录
        chat_history.add_ai_message(full_response)

    async def astream(self, input: Union[Dict[str, Any], List[BaseMessage]], config: Optional[Dict[str, Any]] = None):
        """
        异步流式调用Runnable，自动管理聊天历史
        
        Args:
            input: 输入数据，可以是字典或BaseMessage列表
            config: 配置信息，必须包含configurable.session_id
            
        Yields:
            Runnable的流式输出结果
        """
        # 获取session_id
        if not config or "configurable" not in config or "session_id" not in config["configurable"]:
            raise ValueError("config必须包含configurable.session_id")
        
        session_id = config["configurable"]["session_id"]
        chat_history = self.get_session_history(session_id)
        
        # 获取历史消息
        history_messages = chat_history.get_messages()
        
        # 准备输入数据
        if isinstance(input, list):
            # 输入是BaseMessage列表
            messages = input
        elif isinstance(input, dict):
            # 输入是字典
            if self.input_messages_key and self.input_messages_key in input:
                messages = input[self.input_messages_key]
            else:
                messages = []
            
            # 将历史消息添加到输入中
            input[self.history_messages_key] = history_messages
        else:
            raise ValueError("输入必须是字典或BaseMessage列表")
        
        # 保存输入消息
        if isinstance(messages, list):
            for message in messages:
                if isinstance(message, BaseMessage):
                    chat_history.add_message(message)
        elif isinstance(messages, BaseMessage):
            chat_history.add_message(messages)
        
        # 用于收集响应内容
        full_response = ""
        
        # 异步流式调用Runnable
        async for chunk in self.runnable.astream(input, config):
            content = chunk.content if hasattr(chunk, 'content') else str(chunk)
            full_response += content
            yield chunk
        
        # 保存完整响应到历史记录
        chat_history.add_ai_message(full_response)