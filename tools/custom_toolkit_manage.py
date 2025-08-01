# tools/composite_toolkit.py
from langchain_core.tools.base import BaseToolkit
from typing import List
from langchain_core.tools import BaseTool

from tools.web_search_toolkit import WebSearchToolkit


class CustomToolkitManage(BaseToolkit):
    """组合工具包，包含所有子工具包"""

    def get_tools(self) -> List[BaseTool]:
        """返回所有工具包中的工具"""
        tools = []
        tools.extend(WebSearchToolkit().get_tools())
        return tools
