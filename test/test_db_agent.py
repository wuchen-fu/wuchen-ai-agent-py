#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DB Agent 测试示例
"""

import asyncio
import os
from dotenv import find_dotenv, load_dotenv

# 添加项目根目录到Python路径
import sys

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from chat_memory.mongo_chat_memory import MongoChatMemory
from tools.custom_toolkit_manage import CustomToolkitManage

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from web.agent.db_agent import DBAgent

# 加载环境变量
dotenv_path = find_dotenv(filename='../.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

chid = 'asdasdajsdsa2223'

def test_db_agent_sync():
    """测试同步数据库代理"""
    print("=== 测试同步数据库代理 ===")
    
    try:
        # 创建数据库代理实例
        print("创建数据库代理实例...")
        db_agent = DBAgent()
        print("数据库代理实例创建成功")
        
        print("发送查询: ")
        resp = db_agent.chat("查询用户对话消息记录", chid, "test_user")
        print(f"回复: {resp}")
        
        # 测试第二条消息，验证历史记录功能
        # resp2 = db_agent.chat("我刚才问了什么", chid, "test_user")
        # print(f"回复: {resp2}")
                
    except Exception as e:
        print(f"测试出错: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_db_agent_async():
    """测试异步数据库代理"""
    print("\n=== 测试异步数据库代理 ===")
    
    try:
        # 创建数据库代理实例
        db_agent = DBAgent()
        
        # 测试查询
        test_queries = [
            "描述ai_chat_message表的结构",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- 异步测试查询 {i}: {query} ---")
            try:
                response = await db_agent.achat(query, f"async_test_session_{i}", "test_user")
                print(f"回复: {response}")
            except Exception as e:
                print(f"查询出错: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"创建数据库代理时出错: {e}")
        import traceback
        traceback.print_exc()


def test_db_agent_sync_with_history():
    chat_model = ChatOpenAI(
        model=os.getenv('DASH_SCOPE_MODEL'),
        api_key=os.getenv('DASH_SCOPE_API_KEY'),
        base_url=os.getenv('DASH_SCOPE_URL')
    )

    # 初始化数据库连接
    mysql_url = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
        os.getenv('DB_MYSQL_USER'),
        os.getenv('DB_MYSQL_PASSWORD'),
        os.getenv('DB_MYSQL_URL'),
        os.getenv('DB_MYSQL_PORT'),
        os.getenv('DB_MYSQL_DATABASE')
    )
    db_mysql = SQLDatabase.from_uri(mysql_url)

    # 初始化工具包
    toolkit = SQLDatabaseToolkit(db=db_mysql, llm=chat_model)
    tools = toolkit.get_tools()

    # 添加自定义工具
    tools.extend(CustomToolkitManage().get_tools())

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
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    agent = create_tool_calling_agent(chat_model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        MongoChatMemory.get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )
    resp = agent_with_chat_history.invoke(
        {'question': '吉水县今天的天气怎么样？'},
        config={"configurable": {"session_id": "sync_test_session"}}
    )
    print(resp)
def main():
    """主测试函数"""
    print("开始测试 DB Agent...")
    # test_db_agent_sync_with_history()
    # 测试同步功能
    test_db_agent_sync()
    
    # # 测试异步功能
    # asyncio.run(test_db_agent_async())
    
    print("\n测试完成。")


if __name__ == "__main__":
    main()