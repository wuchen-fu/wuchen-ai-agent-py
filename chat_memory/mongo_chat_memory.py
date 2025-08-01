import json
import logging
import os
from datetime import datetime
from typing import Optional

from langchain_mongodb import MongoDBChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict
from pymongo import MongoClient, errors

logger = logging.getLogger(__name__)


class EnhancedMongoDBChatMessageHistory(MongoDBChatMessageHistory):
    """
    增强版MongoDB聊天历史记录类，继承自MongoDBChatMessageHistory
    添加用户ID和时间戳支持
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
        history_key: str = "History",
        create_index: bool = True,
        history_size: Optional[int] = None,
        index_kwargs: Optional[dict] = None,
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
            history_key: 历史记录字段名
            create_index: 是否创建索引
            history_size: 历史记录大小限制
            index_kwargs: 索引参数
            client: MongoDB客户端实例
        """
        # 调用父类初始化
        super().__init__(
            connection_string=connection_string,
            session_id=session_id,
            database_name=database_name,
            collection_name=collection_name,
            session_id_key=session_id_key,
            history_key=history_key,
            create_index=create_index,
            history_size=history_size,
            index_kwargs=index_kwargs,
            client=client,
        )
        
        # 添加用户ID属性
        self.user_id = user_id
        self.user_id_key = "UserId"

    def add_message(self, message: BaseMessage) -> None:
        """将消息添加到MongoDB记录中，包含用户ID和时间戳"""
        try:
            # 获取当前时间戳
            timestamp = datetime.now()
            
            self.collection.insert_one(
                {
                    self.session_id_key: self.session_id,
                    self.user_id_key: self.user_id,
                    self.history_key: json.dumps(message_to_dict(message), ensure_ascii=False),
                    "timestamp": timestamp,
                    "message_type": message.type
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

class mongo_chat_memory:
    """
    MongoDB聊天记忆类，用于存储和检索聊天记录
    """
    def __init__(self):
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
