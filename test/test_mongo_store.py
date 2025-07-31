import os
from typing import List, Dict, Any, Optional
from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pymongo import MongoClient
from pymongo.database import Database
import uuid
from datetime import datetime

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)


class MongoStore:
    """
    MongoDB持久化记忆存储工具模块
    提供存储、获取和删除对话记录的功能
    """

    def __init__(self):
        """
        初始化MongoDB记忆存储，配置信息从环境变量中读取
        """
        # MongoDB配置，直接从环境变量获取
        self.mongo_user = os.getenv('DB_MONGO_USER')
        self.mongo_password = os.getenv('DB_MONGO_PASSWORD')
        self.mongo_host = os.getenv('DB_MONGO_URL')
        self.mongo_db_name = os.getenv('DB_MONGO_DATABASE', 'ai_agent')
        self.mongo_collection_name = os.getenv('DB_MONGO_COLLECTION', 'messages')

        # 构建MongoDB连接URI
        if self.mongo_user and self.mongo_password:
            mongo_uri = f"mongodb+srv://{self.mongo_user}:{self.mongo_password}@{self.mongo_host}/?retryWrites=true&w=majority&appName=Cluster0"
        else:
            mongo_uri = f"mongodb://{self.mongo_host}/"

        # 初始化MongoDB客户端
        self.client = MongoClient(mongo_uri)
        self.db: Database = self.client[self.mongo_db_name]
        self.collection = self.db[self.mongo_collection_name]

    def save_message(self, user_id: str, session_id: str, message: BaseMessage,
                     message_type: str = "human") -> None:
        """
        存储对话记录到MongoDB

        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 消息内容（BaseMessage对象）
            message_type: 消息类型（human/ai/system）
        """
        # 处理BaseMessage的content属性
        if isinstance(message.content, str):
            message_content = message.content
        else:
            # 如果是列表，将其转换为字符串
            message_content = str(message.content)

        # 根据消息类型格式化存储内容
        if message_type.lower() == "human":
            data = f"User: {message_content}"
        elif message_type.lower() == "ai":
            data = f"AI: {message_content}"
        else:
            data = f"{message_type.capitalize()}: {message_content}"

        # 构造存储文档
        document = {
            "user_id": user_id,
            "session_id": session_id,
            "message_type": message_type.lower(),
            "message": message_content,
            "formatted_data": data,
            "created_at": datetime.utcnow(),
            "uuid": str(uuid.uuid4())
        }

        # 存储消息到MongoDB
        self.collection.insert_one(document)

    def get_messages(self, user_id: str, session_id: Optional[str] = None,
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        从MongoDB获取对话记录

        Args:
            user_id: 用户ID
            session_id: 会话ID（可选）
            limit: 限制返回记录数（可选）

        Returns:
            对话记录列表
        """
        # 构造查询条件
        query = {"user_id": user_id}
        if session_id:
            query["session_id"] = session_id

        # 执行查询
        cursor = self.collection.find(query).sort("created_at", 1)

        # 如果有限制，返回指定数量的记录
        if limit:
            cursor = cursor.limit(limit)

        # 处理结果
        result = []
        for doc in cursor:
            result.append({
                "user_id": doc["user_id"],
                "session_id": doc["session_id"],
                "message_type": doc["message_type"],
                "message": doc["message"],
                "formatted_data": doc["formatted_data"],
                "created_at": doc["created_at"],
                "uuid": doc["uuid"]
            })

        return result

    def delete_messages(self, user_id: str, session_ids: Optional[List[str]] = None) -> int:
        """
        从MongoDB删除对话记录

        Args:
            user_id: 用户ID
            session_ids: 要删除的会话ID列表，如果为None则删除该用户所有记录

        Returns:
            删除的记录数
        """
        # 构造删除条件
        query = {"user_id": user_id}
        if session_ids:
            query["session_id"] = {"$in": session_ids}

        # 执行删除
        result = self.collection.delete_many(query)
        return result.deleted_count


# 单例模式的全局MongoDB记忆存储实例
_mongo_store_instance = None


def get_mongo_store() -> MongoStore:
    """
    获取全局MongoDB记忆存储实例（单例模式）

    Returns:
        MongoStore实例
    """
    global _mongo_store_instance
    if _mongo_store_instance is None:
        _mongo_store_instance = MongoStore()
    return _mongo_store_instance