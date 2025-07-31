import os
import uuid
from typing import List, Dict, Any, Optional, Union
from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.store.redis import RedisStore
from langgraph.checkpoint.redis import RedisSaver

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)


class MemoryStore:
    """
    持久化记忆存储工具模块
    提供存储、获取和删除对话记录的功能
    """

    def __init__(self):
        """
        初始化记忆存储，配置信息从环境变量中读取
        """
        # Redis配置，直接从环境变量获取
        self.redis_host = os.getenv('REDIS_HOST')
        self.redis_port = os.getenv('REDIS_PORT')
        self.redis_password = os.getenv('REDIS_PASSWORD')
        self.redis_db = os.getenv('REDIS_DB', '0')  # 默认使用数据库0

        # 构建Redis连接URI
        if self.redis_password:
            db_uri = f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        else:
            db_uri = f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

        # 初始化Redis组件
        self.store = RedisStore.from_conn_string(db_uri)
        self.checkpointer = RedisSaver.from_conn_string(db_uri)

        # 设置存储
        self.store.setup()
        self.checkpointer.setup()

    def save_message(self, user_id: str, session_id: str, message: Union[BaseMessage, str],
                     message_type: str = "human") -> None:
        """
        存储对话记录

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 消息内容（可以是BaseMessage对象或字符串）
            message_type: 消息类型（human/ai/system）
        """
        namespace = ("memories", user_id)
        
        # 正确处理BaseMessage的content属性
        if isinstance(message, BaseMessage):
            # BaseMessage.content可以是str或list[Union[str, dict]]类型
            if isinstance(message.content, str):
                message_content = message.content
            else:
                # 如果是列表，将其转换为字符串
                message_content = str(message.content)
                
            # 如果传入的是BaseMessage对象，根据实际的消息类型设置message_type
            if isinstance(message, HumanMessage):
                actual_message_type = "human"
            elif isinstance(message, AIMessage):
                actual_message_type = "ai"
            else:
                actual_message_type = message_type
        else:
            message_content = str(message)
            actual_message_type = message_type

        # 根据消息类型格式化存储内容
        if actual_message_type.lower() == "human":
            data = f"User: {message_content}"
        elif actual_message_type.lower() == "ai":
            data = f"AI: {message_content}"
        else:
            data = f"{actual_message_type.capitalize()}: {message_content}"

        # 存储消息
        self.store.put(namespace, str(session_id), {"data": data})

    def get_messages(self, user_id: str, query: Optional[str] = None,
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取对话记录

        Args:
            user_id: 用户ID
            query: 查询关键字（可选）
            limit: 限制返回记录数（可选）

        Returns:
            对话记录列表
        """
        namespace = ("memories", user_id)

        # 搜索记忆
        if query:
            memories = self.store.search(namespace, query=query)
        else:
            memories = self.store.list(namespace)

        # 处理结果
        result = []
        for memory in memories:
            result.append({
                "key": memory.key,
                "value": memory.value,
                "created_at": getattr(memory, 'created_at', None),
                "updated_at": getattr(memory, 'updated_at', None)
            })

        # 如果有限制，返回指定数量的记录
        if limit:
            result = result[:limit]

        return result

    def delete_messages(self, user_id: str, session_ids: Optional[List[str]] = None) -> int:
        """
        删除对话记录

        Args:
            user_id: 用户ID
            session_ids: 要删除的会话ID列表，如果为None则删除该用户所有记录

        Returns:
            删除的记录数
        """
        namespace = ("memories", user_id)
        deleted_count = 0

        if session_ids:
            # 删除指定的会话记录
            for session_id in session_ids:
                try:
                    self.store.delete(namespace, str(session_id))
                    deleted_count += 1
                except Exception:
                    # 记录删除失败，但继续处理其他记录
                    pass
        else:
            # 删除该用户的所有记录
            memories = self.store.list(namespace)
            for memory in memories:
                try:
                    self.store.delete(namespace, memory.key)
                    deleted_count += 1
                except Exception:
                    pass

        return deleted_count

    def get_session_history(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定会话的历史记录

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            会话记录详情，如果不存在则返回None
        """
        namespace = ("memories", user_id)

        try:
            memory = self.store.get(namespace, str(session_id))
            if memory:
                return {
                    "key": memory.key,
                    "value": memory.value,
                    "created_at": getattr(memory, 'created_at', None),
                    "updated_at": getattr(memory, 'updated_at', None)
                }
            return None
        except Exception:
            return None


# 单例模式的全局记忆存储实例
_memory_store_instance = None


def get_memory_store() -> MemoryStore:
    """
    获取全局记忆存储实例（单例模式）

    Returns:
        MemoryStore实例
    """
    global _memory_store_instance
    if _memory_store_instance is None:
        _memory_store_instance = MemoryStore()
    return _memory_store_instance