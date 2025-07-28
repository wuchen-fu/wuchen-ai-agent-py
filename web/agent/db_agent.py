import os

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from dotenv import find_dotenv, load_dotenv
from langchain_openai.chat_models import ChatOpenAI
from langgraph.prebuilt import create_react_agent

dotenv_path = find_dotenv(filename='.env.dev', usecwd=True)
load_dotenv(dotenv_path=dotenv_path)

chatModel = ChatOpenAI(
    model=os.getenv('DASH_SCOPE_MODEL'),
    api_key=os.getenv('DASH_SCOPE_API_KEY'),
    base_url=os.getenv('DASH_SCOPE_URL'))


MSQL_UEL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(
    os.getenv('DB_MYSQL_USER'),
              os.getenv('DB_MYSQL_PASSWORD'),
              os.getenv('DB_MYSQL_URL'),
os.getenv('DB_MYSQL_PORT'),
os.getenv('DB_MYSQL_DATABASE')
)
# print(MSQL_UEL)

db_mysql = SQLDatabase.from_uri(MSQL_UEL)
# print(f'dialect:{db_mysql.dialect}')
# print(db_mysql.get_usable_table_names())
# print(db_mysql.run('select * from ai_chat_message limit 2'))
toolkit = SQLDatabaseToolkit(db=db_mysql,llm=chatModel)
tools = toolkit.get_tools()
# for tool in tools:
#     print(f'{tool.name}:{tool.description}\n')
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

agent = create_react_agent(
    chatModel,
    tools,
    prompt=system_prompt,
)
for step in agent.stream(
        {'messages': [{'role': 'user', 'content': '查询对话中为用户消息的数据'}]},
        stream_mode='values'
):
    step['messages'][-1].pretty_print()
