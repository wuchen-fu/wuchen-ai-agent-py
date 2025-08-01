import os
from typing import List

from dotenv import find_dotenv, load_dotenv
from langchain_core.tools import Tool, tool, BaseToolkit, BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage,HumanMessage,SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_community.utilities import SearchApiAPIWrapper
from langchain_tavily import TavilySearch
from langgraph.prebuilt import chat_agent_executor

dotenv_path = find_dotenv(filename='.env.dev',usecwd=True)
# 加载 .env 文件
load_dotenv(dotenv_path=dotenv_path)

'''
name
str
函数名
工具的唯一标识符，供大模型调用时使用
description
str
函数文档字符串
描述工具的功能，帮助大模型理解何时使用该工具
args_schema
Type[BaseModel]
None
定义工具参数的结构和验证规则
return_direct
bool
False
控制是否直接返回结果，跳过模型处理
infer_schema
bool
True
控制是否从函数签名自动推断参数结构
'''

@tool
def web_search(query: str) -> str:
    """
    网络搜索工具，用于查询最新的互联网信息。

    当用户需要了解实时信息时使用此工具，包括:
    - 天气预报和当前天气情况
    - 新闻资讯和时事动态
    - 其他需要从网络获取的实时数据

    参数:
        query: 用户想要搜索的具体内容(必须填写)

    返回:
        搜索结果
    """
    try:
        search_wrapper = SearchApiAPIWrapper(engine='baidu', searchapi_api_key=os.getenv('SERPAPI_API_KEY'))
        result = search_wrapper.run(query)
        return result
    except Exception as e:
        return f"搜索过程中发生错误: {str(e)}"


class WebSearchToolkit(BaseToolkit):
    """网络搜索工具包"""

    def get_tools(self) -> List[BaseTool]:
        """返回工具包中的所有工具"""
        return [web_search]