import logging
import os
from typing import List, Optional, Iterator, AsyncIterator, Any

from dotenv import find_dotenv, load_dotenv
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.runnables.utils import ConfigurableFieldSpec
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI

from chat_memory.mongo_chat_memory import MongoChatMemory
from tools.custom_toolkit_manage import CustomToolkitManage
from web.agent.base_agent import BaseAgent
from langchain_core.messages import BaseMessage

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)


# 数据库连接URL构建函数
def build_mysql_url() -> str:
    """
    构建MySQL数据库连接URL

    Returns:
        str: MySQL连接URL
    """
    return 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
        os.getenv('DB_MYSQL_USER'),
        os.getenv('DB_MYSQL_PASSWORD'),
        os.getenv('DB_MYSQL_URL'),
        os.getenv('DB_MYSQL_PORT'),
        os.getenv('DB_MYSQL_DATABASE')
    )


class DBAgent(BaseAgent):
    """
    数据库智能体，继承自BaseAgent
    用于与SQL数据库交互的智能代理
    """
    
    AGENT_TYPE = "db"

    def __init__(self, config: Optional[dict] = None):
        """
        初始化数据库智能体

        Args:
            config: 配置字典
        """
        # 处理向后兼容性 - 如果config是chat_model实例而不是字典
        if config and not isinstance(config, dict):
            config = {"chat_model": config}
            
        super().__init__(config)
        
        # 获取聊天模型（如果配置中没有提供，则使用默认模型）
        self.chat_model = self.get_chat_model()
        if not self.chat_model:
            # 初始化默认聊天模型
            self.chat_model = ChatOpenAI(
                model=os.getenv('QWEN_MODEL'),
                api_key=os.getenv('QWEN_API_KEY'),
                base_url=os.getenv('QWEN_URL')
            )
        
        # 初始化数据库连接
        mysql_url = build_mysql_url()
        db_mysql = SQLDatabase.from_uri(mysql_url)

        # 初始化工具包
        toolkit = SQLDatabaseToolkit(db=db_mysql, llm=self.chat_model)
        self.tools = toolkit.get_tools()

        # 添加自定义工具
        self.tools.extend(CustomToolkitManage().get_tools())
        
        # 系统提示词
        self.system_prompt = """
        你是一个被设计用于与 SQL 数据库交互的智能代理。
        在收到用户的问题后，生成一条语法正确的SQL查询语句来执行,默认使用时间排序,然后查看查询结果并返回答案。
        除非用户明确指定希望获取的数量，否则查询结果默认返回 20 条记录。
        可以根据相关字段对结果进行排序，以返回数据库中最匹配的数据。
        永远不要从特定表中查询所有字段（不要使用 SELECT *），只查询与问题相关的字段。
        在执行查询之前，你必须仔细检查查询语句。
        如果在执行查询时出现错误，必须重写查询并重新尝试。
        严禁执行任何数据库DML语句（如 INSERT、UPDATE、DELETE、DROP 等）。
        查询开始前，你必须列出数据库中的所有表，以了解可查询的内容，不要跳过这一步。
        然后查询与问题最相关的表的 schema（模式结构）
        """

        # 创建MongoChatMemory实例用于持久化存储对话历史
        self.mongo_memory = MongoChatMemory()
        
        # 创建代理执行器
        self.agent_executor = self._create_agent_executor()

    def _create_agent_executor(self, chat_model=None):
        """创建代理执行器"""
        try:
            from langchain.agents import create_tool_calling_agent
            from langchain.agents import AgentExecutor
            
            # 使用传入的模型或实例变量
            model_to_use = chat_model or self.chat_model
            
            # 创建提示词模板
            from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            # 绑定工具到模型
            bound_model = model_to_use.bind_tools(self.tools)
            
            # 创建代理
            agent = create_tool_calling_agent(bound_model, self.tools, prompt)
            
            # 创建代理执行器
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True
            )
            
            # 创建适配MongoChatMemory的会话历史获取函数
            def get_session_history(session_id: str, user_id: str = "default_user"):
                return MongoChatMemory.get_session_history(session_id, user_id)
            
            # 创建带历史记录的执行器
            return RunnableWithMessageHistory(
                agent_executor,
                get_session_history,
                input_messages_key="question",
                history_messages_key="chat_history",
                history_factory_config=[
                    ConfigurableFieldSpec(
                        id="user_id",
                        annotation=str,
                        name="User ID",
                        description="Unique identifier for the user.",
                        default="default_user",
                        is_shared=True,
                    ),
                    ConfigurableFieldSpec(
                        id="session_id",
                        annotation=str,
                        name="Session ID",
                        description="Unique identifier for the conversation.",
                        default="",
                        is_shared=True,
                    ),
                ],
            )
        except Exception as e:
            logger.error(f"创建代理执行器时出错: {e}")
            raise

    def _extract_response_content(self, response: Any) -> str:
        """
        从响应中提取内容
        
        Args:
            response: 原始响应
            
        Returns:
            str: 提取的内容
        """
        if isinstance(response, dict):
            # 优先处理output字段
            if "output" in response:
                return response["output"]
            # 处理messages字段
            elif "messages" in response and response["messages"]:
                last_message = response["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                else:
                    return str(last_message)
            else:
                # 返回整个字典的字符串表示
                return str(response)
        else:
            return str(response)

    def _extract_stream_content(self, chunk: Any) -> str:
        """
        从流式响应块中提取内容
        
        Args:
            chunk: 流式响应块
            
        Returns:
            str: 提取的内容
        """
        if isinstance(chunk, dict):
            # 优先处理output字段
            if "output" in chunk:
                return chunk["output"]
            # 处理messages字段
            elif "messages" in chunk and chunk["messages"]:
                last_message = chunk["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
                else:
                    return str(last_message)
            else:
                # 返回整个字典的字符串表示
                return str(chunk)
        else:
            return str(chunk)

    def chat(self, message: str, chat_id: str, user_id: Optional[str] = None,
             provider_name: str = None, model_name: str = None) -> str:
        """
        与数据库智能体进行对话

        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）

        Returns:
            str: 智能体的回复
        """
        try:
            user_id = user_id or "default_user"
            
            # 确定要使用的执行器
            if provider_name or model_name:
                # 获取指定的聊天模型
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    # 为指定模型创建临时执行器
                    agent_executor = self._create_agent_executor(chat_model)
                else:
                    # 如果无法获取指定模型，使用默认执行器
                    agent_executor = self.agent_executor
            else:
                # 使用默认执行器
                agent_executor = self.agent_executor

            # 使用代理执行器处理消息
            response = agent_executor.invoke(
                {"question": message},
                config={"configurable": {"session_id": chat_id, "user_id": user_id}}
            )

            return self._extract_response_content(response)

        except Exception as e:
            logger.error(f"数据库智能体对话出错: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，我在处理您的问题时遇到了错误。"

    def stream_chat(self, message: str, chat_id: str, user_id: Optional[str] = None,
                    provider_name: str = None, model_name: str = None) -> Iterator[str]:
        """
        与数据库智能体进行流式对话

        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）

        Yields:
            str: 智能体的回复片段
        """
        try:
            user_id = user_id or "default_user"
            
            # 确定要使用的执行器
            if provider_name or model_name:
                # 获取指定的聊天模型
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    # 为指定模型创建临时执行器
                    agent_executor = self._create_agent_executor(chat_model)
                else:
                    # 如果无法获取指定模型，使用默认执行器
                    agent_executor = self.agent_executor
            else:
                # 使用默认执行器
                agent_executor = self.agent_executor

            # 使用代理执行器处理消息并流式返回
            for chunk in agent_executor.stream(
                {"question": message},
                config={"configurable": {"session_id": chat_id, "user_id": user_id}}
            ):
                content = self._extract_stream_content(chunk)
                if content:
                    yield content

        except Exception as e:
            logger.error(f"数据库智能体流式对话出错: {e}")
            import traceback
            traceback.print_exc()
            yield "抱歉，我在处理您的问题时遇到了错误。"

    async def achat(self, message: str, chat_id: str, user_id: Optional[str] = None,
                    provider_name: str = None, model_name: str = None) -> str:
        """
        异步与数据库智能体进行对话

        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）

        Returns:
            str: 智能体的回复
        """
        try:
            user_id = user_id or "default_user"
            
            # 确定要使用的执行器
            if provider_name or model_name:
                # 获取指定的聊天模型
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    # 为指定模型创建临时执行器
                    agent_executor = self._create_agent_executor(chat_model)
                else:
                    # 如果无法获取指定模型，使用默认执行器
                    agent_executor = self.agent_executor
            else:
                # 使用默认执行器
                agent_executor = self.agent_executor

            # 使用代理执行器处理消息
            response = await agent_executor.ainvoke(
                {"question": message},
                config={"configurable": {"session_id": chat_id, "user_id": user_id}}
            )

            return self._extract_response_content(response)

        except Exception as e:
            logger.error(f"数据库智能体对话出错: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，我在处理您的问题时遇到了错误。"

    async def astream_chat(self, message: str, chat_id: str, user_id: Optional[str] = None,
                           provider_name: str = None, model_name: str = None) -> AsyncIterator[str]:
        """
        异步与数据库智能体进行流式对话

        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）
            provider_name: 模型提供商名称（可选）
            model_name: 模型名称（可选）

        Yields:
            str: 智能体的回复片段
        """
        try:
            user_id = user_id or "default_user"
            
            # 确定要使用的执行器
            if provider_name or model_name:
                # 获取指定的聊天模型
                chat_model = self.get_chat_model(provider_name, model_name)
                if chat_model:
                    # 为指定模型创建临时执行器
                    agent_executor = self._create_agent_executor(chat_model)
                else:
                    # 如果无法获取指定模型，使用默认执行器
                    agent_executor = self.agent_executor
            else:
                # 使用默认执行器
                agent_executor = self.agent_executor

            # 使用代理执行器处理消息并流式返回
            async for chunk in agent_executor.astream(
                {"question": message},
                config={"configurable": {"session_id": chat_id, "user_id": user_id}}
            ):
                content = self._extract_stream_content(chunk)
                if content:
                    yield content

        except Exception as e:
            logger.error(f"数据库智能体异步流式对话出错: {e}")
            import traceback
            traceback.print_exc()
            yield "抱歉，我在处理您的问题时遇到了错误。"

    def get_history(self, chat_id: str) -> List[BaseMessage]:
        """
        获取指定会话的历史记录
        
        Args:
            chat_id: 聊天ID
            
        Returns:
            历史消息列表
        """
        try:
            history = MongoChatMemory.get_session_history(chat_id)
            return history.messages
        except Exception as e:
            logger.error(f"获取历史记录出错: {e}")
            return []

    def clear_history(self, chat_id: str):
        """
        清除指定会话的历史记录
        
        Args:
            chat_id: 聊天ID
        """
        try:
            history = MongoChatMemory.get_session_history(chat_id)
            history.clear()
        except Exception as e:
            logger.error(f"清除历史记录出错: {e}")