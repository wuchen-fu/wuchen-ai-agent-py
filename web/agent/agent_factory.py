import inspect
from typing import List

from langchain_core.tools import BaseTool

from .base_agent import BaseAgent


def create_agent_by_type(agent_type: str, chat_model, **kwargs) -> BaseAgent:
    """
    根据类型创建智能体
    
    Args:
        agent_type: 智能体类型 ('writing', 'general', 'custom')
        chat_model: 聊天模型实例
        **kwargs: 其他参数
        
    Returns:
        BaseAgent: 创建的智能体实例
    """
    # 动态导入具体的智能体类
    if agent_type == "writing":
        from .writing_agent import WritingAgent
        return WritingAgent(chat_model, **kwargs)
    elif agent_type == "general":
        # 如果没有general_agent，则使用base_agent
        from .writing_agent import WritingAgent
        return WritingAgent(chat_model, **kwargs)
    elif agent_type == "custom":
        # 如果没有custom_agent，则使用base_agent
        from .writing_agent import WritingAgent
        return WritingAgent(chat_model, **kwargs)
    else:
        raise ValueError(f"不支持的智能体类型: {agent_type}")


def create_writing_agent(chat_model, memory_backend: str = "memory") -> BaseAgent:
    """
    创建写作智能体
    
    Args:
        chat_model: 聊天模型实例
        memory_backend: 记忆后端类型
        
    Returns:
        BaseAgent: 写作智能体实例
    """
    return create_agent_by_type("writing", chat_model, memory_backend=memory_backend)


def create_general_agent(chat_model, memory_backend: str = "memory") -> BaseAgent:
    """
    创建通用智能体
    
    Args:
        chat_model: 聊天模型实例
        memory_backend: 记忆后端类型
        
    Returns:
        BaseAgent: 通用智能体实例
    """
    return create_agent_by_type("general", chat_model, memory_backend=memory_backend)


def create_custom_agent(chat_model,
                       system_message: str,
                       tools: List[BaseTool],
                       memory_backend: str = "memory") -> BaseAgent:
    """
    创建自定义智能体
    
    Args:
        chat_model: 聊天模型实例
        system_message: 系统消息
        tools: 工具列表
        memory_backend: 记忆后端类型
        
    Returns:
        BaseAgent: 自定义智能体实例
    """
    return create_agent_by_type(
        "custom", 
        chat_model, 
        system_message=system_message, 
        tools=tools,
        memory_backend=memory_backend
    )