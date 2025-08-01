"""
Agent模块初始化文件
"""

# 确保模块可以正确导入
import os
import sys

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from .base_agent import BaseAgent
from .agent_factory import create_agent_by_type, create_writing_agent, create_general_agent, create_custom_agent
from chat_memory.chat_history import BaseChatHistory, InMemoryChatHistory, RedisChatHistory
from tools.tool_config import ToolConfig

__all__ = [
    "BaseAgent",
    "create_agent_by_type",
    "create_writing_agent",
    "create_general_agent",
    "create_custom_agent",
    "BaseChatHistory",
    "InMemoryChatHistory",
    "RedisChatHistory",
    "ToolConfig"
]