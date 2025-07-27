import os

from dotenv import find_dotenv, load_dotenv
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import SearchApiAPIWrapper
from langchain_tavily import TavilySearch
from langgraph.prebuilt import chat_agent_executor

dotenv_path = find_dotenv(filename='.env.dev',usecwd=True)
# 加载 .env 文件
load_dotenv(dotenv_path=dotenv_path)
chatModel = ChatOpenAI(
    model=os.getenv('DASH_SCOPE_MODEL'),
    api_key=os.getenv('DASH_SCOPE_API_KEY'),
    base_url=os.getenv('DASH_SCOPE_URL'))
search = SearchApiAPIWrapper(engine='baidu',searchapi_api_key=os.getenv('SERPAPI_API_KEY'))
search_tool = Tool(
    name="WebSearch",
    func=search.run,
    description="当需要查询互联网信息时使用..."
)
# search = TavilySearch(max_results=5)

tools = [search_tool]
# chat_model_tools = chatModel.bind_tools(tools)
# chat_model_tools = chatModel.bind_tools([search_tool])
# 创建代理 支持工具调用的chatModel方法
agent = chat_agent_executor.create_tool_calling_executor(chatModel, tools)
# resp = chat_model_tools.invoke([HumanMessage(content='今天北京的天气怎么样')])
resp = agent.invoke({'messages':[HumanMessage(content='你好今天北京气温多少度,北京后面一周的天气怎么样')]})
print(f'resp: {resp['messages'][-1].content}')
# print(f'resp_tools: {resp.tool_calls}')