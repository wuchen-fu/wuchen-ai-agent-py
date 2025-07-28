import os

from dotenv import find_dotenv, load_dotenv
from langchain_core.tools import Tool, tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import SearchApiAPIWrapper
from langchain_tavily import TavilySearch
from langgraph.prebuilt import chat_agent_executor

dotenv_path = find_dotenv(filename='.env.dev',usecwd=True)
# 加载 .env 文件
load_dotenv(dotenv_path=dotenv_path)


search_wrapper = SearchApiAPIWrapper(engine='baidu',searchapi_api_key=os.getenv('SERPAPI_API_KEY'))
@tool
def web_search(query: str) -> str:
    """
    网络搜索工具，用于查询最新的互联网信息。

    当用户需要了解实时信息时使用此工具，包括:
    - 天气预报和当前天气情况
    - 新闻资讯和时事动态
    - 其他需要从网络获取的实时数据

    参数:
        query: 用户想要搜索的具体内容

    返回:
        搜索结果
    """
    try:
        result = search_wrapper.run(query)
        return result
    except Exception as e:
        return f"搜索过程中发生错误: {str(e)}"



# search = TavilySearch(max_results=5)

# chat_model_tools = chatModel.bind_tools(tools)
# chat_model_tools = chatModel.bind_tools([search_tool])
# 创建代理 支持工具调用的chatModel方法
# agent = chat_agent_executor.create_tool_calling_executor(chatModel, tools)
# resp = chat_model_tools.invoke([HumanMessage(content='今天北京的天气怎么样')])
# resp = agent.invoke({'messages':[HumanMessage(content='你好今天北京气温多少度,北京后面一周的天气怎么样')]})
# print(f'resp: {resp['messages'][-1].content}')
# print(f'resp_tools: {resp.tool_calls}')