import os
import json
import logging
from typing import List, Optional, Dict
from datetime import datetime

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
    HumanMessage,
    AIMessage
)
from langchain_mongodb import MongoDBChatMessageHistory
from pymongo import MongoClient, errors
from pymongo.driver_info import DriverInfo
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


class EnhancedMongoDBChatMessageHistory(BaseChatMessageHistory):
    """
    增强版MongoDB聊天历史记录类，支持存储用户ID等额外信息
    """

    def __init__(
        self,
        connection_string: Optional[str],
        session_id: str,
        user_id: str = "default_user",
        database_name: str = "chat_history",
        collection_name: str = "message_store",
        *,
        session_id_key: str = "SessionId",
        user_id_key: str = "UserId",
        history_key: str = "History",
        metadata_key: str = "Metadata",
        create_index: bool = True,
        history_size: Optional[int] = None,
        index_kwargs: Optional[Dict] = None,
        client: Optional[MongoClient] = None,
    ):
        """
        初始化增强版MongoDB聊天历史记录
        
        Args:
            connection_string: MongoDB连接字符串
            session_id: 会话ID
            user_id: 用户ID
            database_name: 数据库名称
            collection_name: 集合名称
            session_id_key: 会话ID字段名
            user_id_key: 用户ID字段名
            history_key: 历史记录字段名
            metadata_key: 元数据字段名
            create_index: 是否创建索引
            history_size: 历史记录大小限制
            index_kwargs: 索引参数
            client: MongoDB客户端实例
        """
        self.session_id = session_id
        self.user_id = user_id
        self.database_name = database_name
        self.collection_name = collection_name
        self.session_id_key = session_id_key
        self.user_id_key = user_id_key
        self.history_key = history_key
        self.metadata_key = metadata_key
        self.history_size = history_size

        if client:
            if connection_string:
                raise ValueError("Must provide connection_string or client, not both")
            self.client = client
        elif connection_string:
            try:
                self.client = MongoClient(
                    connection_string,
                    driver=DriverInfo(name="Langchain", version="unknown"),
                )
            except errors.ConnectionFailure as error:
                logger.error(error)
        else:
            raise ValueError("Either connection_string or client must be provided")

        self.db = self.client[database_name]
        self.collection = self.db[collection_name]

        if create_index:
            index_kwargs = index_kwargs or {}
            # 为会话ID和用户ID创建复合索引
            self.collection.create_index(
                [self.session_id_key, self.user_id_key], 
                **index_kwargs
            )

    @property
    def messages(self) -> List[BaseMessage]:
        """从MongoDB检索消息"""
        try:
            if self.history_size is None:
                cursor = self.collection.find({
                    self.session_id_key: self.session_id,
                    self.user_id_key: self.user_id
                }).sort("_id", 1)  # 按照插入顺序排序
            else:
                skip_count = max(
                    0,
                    self.collection.count_documents({
                        self.session_id_key: self.session_id,
                        self.user_id_key: self.user_id
                    }) - self.history_size,
                )
                cursor = self.collection.find(
                    {
                        self.session_id_key: self.session_id,
                        self.user_id_key: self.user_id
                    }, 
                    skip=skip_count
                ).sort("_id", 1)  # 按照插入顺序排序
        except errors.OperationFailure as error:
            logger.error(error)
            return []

        if cursor:
            items = [json.loads(document[self.history_key]) for document in cursor]
        else:
            items = []

        messages = messages_from_dict(items)
        return messages

    def add_message(self, message: BaseMessage) -> None:
        """将消息添加到MongoDB记录中"""
        try:
            # 确保中文不会被转义
            message_dict = message_to_dict(message)
            message_json = json.dumps(message_dict, ensure_ascii=False)
            
            # 获取当前时间戳
            timestamp = datetime.now()
            
            metadata_json = json.dumps({
                "created_at": timestamp.isoformat(),
                "message_type": message.type
            }, ensure_ascii=False)
            
            self.collection.insert_one(
                {
                    self.session_id_key: self.session_id,
                    self.user_id_key: self.user_id,
                    self.history_key: message_json,
                    self.metadata_key: metadata_json,
                    "timestamp": timestamp  # 添加时间戳字段
                }
            )
        except errors.WriteError as err:
            logger.error(err)

    def clear(self) -> None:
        """从MongoDB清除会话记忆"""
        try:
            self.collection.delete_many({
                self.session_id_key: self.session_id,
                self.user_id_key: self.user_id
            })
        except errors.WriteError as err:
            logger.error(err)

    def close(self) -> None:
        """关闭MongoDBChatMessageHistory使用的资源"""
        self.client.close()


class MongoStore:
    """
    MongoDB存储管理类
    """
    
    def __init__(self):
        """
        初始化MongoStore
        """
        # MongoDB连接配置
        if os.getenv('DB_MONGO_URL') and 'cluster' in os.getenv('DB_MONGO_URL', ''):
            # MongoDB Atlas集群（使用SRV记录）
            self.connection_string = 'mongodb+srv://{}:{}@{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_DATABASE')
            )
        else:
            # 本地或普通MongoDB实例
            self.connection_string = 'mongodb://{}:{}@{}:{}/{}?authSource=admin'.format(
                os.getenv('DB_MONGO_USER'),
                os.getenv('DB_MONGO_PASSWORD'),
                os.getenv('DB_MONGO_URL'),
                os.getenv('DB_MONGO_PORT'),
                os.getenv('DB_MONGO_DATABASE')
            )
            
        self.db_name = os.getenv('DB_MONGO_DATABASE', 'chat_history')
        self.collection_name = os.getenv('DB_MONGO_COLLECTION', 'message_store')

    def get_session_history(self, session_id: str, user_id: str = "default_user") -> EnhancedMongoDBChatMessageHistory:
        """
        获取指定会话的MongoDB聊天历史记录
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            EnhancedMongoDBChatMessageHistory: 增强版聊天历史记录对象
        """
        return EnhancedMongoDBChatMessageHistory(
            connection_string=self.connection_string,
            session_id=session_id,
            user_id=user_id,
            database_name=self.db_name,
            collection_name=self.collection_name
        )

    def add_message(self, session_id: str, message: str, message_type: str = "human", user_id: str = "default_user"):
        """
        添加消息到MongoDB存储
        
        Args:
            session_id: 会话ID
            message: 消息内容
            message_type: 消息类型 ("human" 或 "ai")
            user_id: 用户ID
        """
        history = self.get_session_history(session_id, user_id)
        if message_type == "human":
            history.add_user_message(message)
        else:
            history.add_ai_message(message)

    def get_messages(self, session_id: str, user_id: str = "default_user") -> List[BaseMessage]:
        """
        从MongoDB存储获取消息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            List[BaseMessage]: 消息列表
        """
        history = self.get_session_history(session_id, user_id)
        return history.messages

    def clear_history(self, session_id: str, user_id: str = "default_user"):
        """
        清除指定会话的历史记录
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
        """
        history = self.get_session_history(session_id, user_id)
        history.clear()


def get_mongo_store() -> MongoStore:
    """
    获取MongoStore单例实例
    
    Returns:
        MongoStore: MongoStore实例
    """
    return MongoStore()