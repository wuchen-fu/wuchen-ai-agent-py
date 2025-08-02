import logging
import os
from typing import List, Optional

from dotenv import find_dotenv, load_dotenv
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.tools import BaseTool
from langchain_openai.chat_models import ChatOpenAI
from chat_memory.mongo_chat_memory import MongoChatMemory
from tools.custom_toolkit_manage import CustomToolkitManage

from web.agent.base_agent import BaseAgent

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


# 初始化数据库连接和工具
def init_db_agent_components():
    """
    初始化数据库代理组件

    Returns:
        tuple: (chat_model, tools, system_prompt)
    """
    try:
        # 初始化聊天模型
        chat_model = ChatOpenAI(
            model=os.getenv('DASH_SCOPE_MODEL'),
            api_key=os.getenv('DASH_SCOPE_API_KEY'),
            base_url=os.getenv('DASH_SCOPE_URL')
        )

        # 初始化数据库连接
        mysql_url = build_mysql_url()
        db_mysql = SQLDatabase.from_uri(mysql_url)

        # 初始化工具包
        toolkit = SQLDatabaseToolkit(db=db_mysql, llm=chat_model)
        tools = toolkit.get_tools()

        # 系统提示词
        system_prompt = """
        你是一个被设计用于与 SQL 数据库交互的智能代理。
        在收到用户的问题后，生成一条语法正确的SQL查询语句来执行,然后查看查询结果并返回答案。
        除非用户明确指定希望获取的示例数量，否则查询结果最多返回 20 条记录。
        可以根据相关字段对结果进行排序，以返回数据库中最匹配的数据。
        永远不要从特定表中查询所有字段（不要使用 SELECT *），只查询与问题相关的字段。
        在执行查询之前，你必须仔细检查查询语句。
        如果在执行查询时出现错误，必须重写查询并重新尝试。
        严禁执行任何数据库DML语句（如 INSERT、UPDATE、DELETE、DROP 等）。
        查询开始前，你必须列出数据库中的所有表，以了解可查询的内容，不要跳过这一步。
        然后查询与问题最相关的表的 schema（模式结构）
        """

        return chat_model, tools, system_prompt.strip()

    except Exception as e:
        logger.error(f"初始化数据库代理组件时出错: {e}")
        raise


class DBAgent:
    """
    数据库智能体，继承自BaseAgent
    用于与SQL数据库交互的智能代理
    """

    def __init__(self, chat_model=None, tools: Optional[List[BaseTool]] = None):
        """
        初始化数据库智能体

        Args:
            chat_model: 聊天模型实例（可选）
            tools: 工具列表（可选）
        """
        default_chat_model, default_tools, system_prompt = init_db_agent_components()
        chat_model = chat_model or default_chat_model
        tools = tools or default_tools

        # 添加数据库工具
        if tools:
            tools.extend(CustomToolkitManage().get_tools())
        else:
            tools = CustomToolkitManage().get_tools()
            
        # 创建MongoChatMemory实例用于持久化存储对话历史
        mongo_memory = MongoChatMemory()
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(chat_model, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools)
        self.chain_agent = RunnableWithMessageHistory(
            agent_executor,
            MongoChatMemory.get_session_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )

        # 调用父类构造函数
        # super().__init__(chat_model, system_prompt, mongo_memory, None, tools)
        
        # self.mongo_memory = mongo_memory

    def chat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> str:
        """
        与数据库智能体进行对话

        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）

        Returns:
            str: 智能体的回复
        """
        try:
            # 设置MongoDB会话上下文
            # user_id = user_id or "default_user"
            # if hasattr(self.mongo_memory, 'set_session_context'):
            #     self.mongo_memory.set_session_context(chat_id, user_id)
            # elif hasattr(self.mongo_memory, 'session_id') and hasattr(self.mongo_memory, 'user_id'):
            #     self.mongo_memory.session_id = chat_id
            #     self.mongo_memory.user_id = user_id

            # 使用代理执行器处理消息
            response = self.chain_agent.invoke(
                {"question": message},
                config={"configurable": {"session_id": chat_id}}
            )

            if isinstance(response, dict):
                if "output" in response:
                    return response["output"]
                elif "messages" in response:
                    # 获取最后一条消息作为响应
                    last_message = response["messages"][-1]
                    if hasattr(last_message, 'content'):
                        return last_message.content
                    else:
                        return str(last_message)
            else:
                return str(response)

        except Exception as e:
            logger.error(f"数据库智能体对话出错: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，我在处理您的问题时遇到了错误。"

    async def achat(self, message: str, chat_id: str, user_id: Optional[str] = None) -> str:
        """
        异步与数据库智能体进行对话

        Args:
            message: 用户消息
            chat_id: 聊天ID
            user_id: 用户ID（可选）

        Returns:
            str: 智能体的回复
        """
        try:
            # 设置MongoDB会话上下文
            # user_id = user_id or "default_user"
            # if hasattr(self.mongo_memory, 'set_session_context'):
            #     self.mongo_memory.set_session_context(chat_id, user_id)
            # elif hasattr(self.mongo_memory, 'session_id') and hasattr(self.mongo_memory, 'user_id'):
            #     self.mongo_memory.session_id = chat_id
            #     self.mongo_memory.user_id = user_id

            # 使用代理执行器处理消息
            response = await self.chain_agent.ainvoke(
                {"question": message},
                config={"configurable": {"session_id": chat_id}}
            )

            if isinstance(response, dict):
                if "output" in response:
                    return response["output"]
                elif "messages" in response:
                    # 获取最后一条消息作为响应
                    last_message = response["messages"][-1]
                    if hasattr(last_message, 'content'):
                        return last_message.content
                    else:
                        return str(last_message)
            else:
                return str(response)

        except Exception as e:
            logger.error(f"数据库智能体对话出错: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，我在处理您的问题时遇到了错误。"