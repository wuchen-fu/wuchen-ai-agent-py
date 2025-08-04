try:
    from config import config
except ImportError:
    # 如果直接导入失败，尝试相对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import config

import json
import logging
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator, Union, Generator, Callable, Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from web.agent.model_provider import ModelProviderManager
from web.agent.agent_factory import MultiAgentManager
from sse_starlette.sse import EventSourceResponse

# 移除自定义SSE辅助函数和相关注释

# 响应模型定义
class ModelsResponse(BaseModel):
    """
    模型列表响应模型
    
    用于描述系统中所有可用模型的信息，按提供商分组。
    """
    
    models: Dict[str, List[str]] = Field(
        ...,
        description="模型信息字典\n\n按提供商分组的模型列表。\n- 键(key): 模型提供商名称，如 \"qwen\"\n- 值(value): 该提供商下可用的模型名称列表，如 [\"qwen-turbo\", \"qwen-plus\"]",
        example={
            "qwen": ["qwen-turbo", "qwen-plus", "qwen-max"]
        }
    )
    
class ErrorResponse(BaseModel):
    """
    错误响应模型
    
    用于描述发生错误时的统一响应格式。
    """
    
    error: str = Field(
        ...,
        description="错误信息描述",
        example="获取模型列表失败"
    )
    
class ChatResponseUnion(BaseModel):
    """
    聊天响应联合模型
    
    用于描述聊天接口的可能响应类型。
    """
    
    chat_id: str
    message: str
    error: Optional[bool] = None

class StreamChatResponseDoc(BaseModel):
    data: str = Field(..., description="流式返回的内容块（字符串）")
    event: Optional[str] = Field(None, description="SSE事件类型，如'end'表示结束，'error'表示错误")

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# 初始化模型提供商管理器并自动注册配置中的提供商
try:
    model_provider_manager = ModelProviderManager(auto_register_providers=True)
except Exception as e:
    logger.error(f"初始化模型提供商管理器失败: {e}")
    model_provider_manager = None

# 初始化Agent管理器
try:
    agent_configs = config.get_agent_configs()
    # 创建多Agent管理器
    multi_agent_manager = MultiAgentManager(agent_configs, model_provider_manager)
except Exception as e:
    logger.error(f"初始化Agent管理器失败: {e}")
    agent_configs = {}
    multi_agent_manager = None


class ChatRequest(BaseModel):
    """
    聊天请求模型
    
    用于向AI助手发送聊天消息的请求数据模型。
    """
    
    message: str = Field(
        ...,
        description="用户发送的聊天消息内容",
        example="你好，能帮我写一篇科幻小说吗？"
    )
    
    chat_id: Optional[str] = Field(
        None,
        description="聊天会话ID（可选）\n\n用于标识一个聊天会话的唯一ID。如果未提供，服务器将自动生成一个。\n相同ID的请求会被认为是同一个会话的一部分。",
        example="chat_123456"
    )
    
    agent_type: str = Field(
        "default",
        description="AI助手类型\n\n指定要使用的AI助手类型。可用的助手类型可以通过 /agents 接口获取。\n默认值为\"default\"。",
        example="writing"
    )
    
    provider_name: Optional[str] = Field(
        None,
        description="模型提供商名称（可选）\n\n指定要使用的模型提供商，如\"qwen\"。如果未指定，将使用系统默认的提供商。\n可用的提供商列表可以通过 /models 接口获取。",
        example="qwen"
    )
    
    model_name: Optional[str] = Field(
        None,
        description="模型名称（可选）\n\n指定要使用的具体模型名称。如果未指定，将使用该提供商的默认模型。\n不同提供商支持的模型列表可以通过 /models 接口获取。",
        example="qwen-plus"
    )
    
    user_id: Optional[str] = Field(
        None,
        description="用户ID（可选）\n\n用于标识用户的唯一ID。如果未提供，系统会使用默认值。\n建议前端生成并持久化存储用户ID以保持会话一致性。",
        example="user_789012"
    )


class ChatResponse(BaseModel):
    """
    聊天响应模型
    
    用于描述AI助手回复的响应数据模型。
    """
    
    chat_id: str = Field(
        ...,
        description="聊天会话ID\n\n用于标识一个聊天会话的唯一ID。如果请求中未提供chat_id，服务器将自动生成一个。\n客户端应使用相同的chat_id进行后续对话，以保持会话上下文。",
        example="chat_123456"
    )
    
    message: str = Field(
        ...,
        description="AI助手的回复内容\n\nAI助手对用户消息的回复内容。可能是完整回复（在非流式接口中），\n或者是错误信息（当error字段为True时）。",
        example="你好！我很乐意帮你写一篇科幻小说..."
    )
    
    error: Optional[bool] = Field(
        None,
        description="错误标识（可选）\n\n标识该响应是否为错误响应。\n- True: 表示发生了错误，message字段包含错误信息\n- None/False: 表示正常响应，message字段包含AI助手的回复内容\n- 该字段仅在发生错误时出现",
        example=False
    )


class AgentInfo(BaseModel):
    """
    Agent信息模型
    
    描述单个Agent的详细信息。
    """
    
    id: str = Field(
        ...,
        description="Agent ID\n\nAgent的唯一标识符，用于在请求中指定要使用的Agent类型。\n例如: \"writing\", \"db\" 等。",
        example="writing"
    )
    
    name: str = Field(
        ...,
        description="Agent名称\n\nAgent的显示名称，用于在用户界面中展示。\n例如: \"写作助手\", \"数据查询助手\" 等。",
        example="写作助手"
    )


class AgentListResponse(BaseModel):
    """
    Agent列表响应模型
    
    用于描述系统中所有Agent的配置和可用性状态。
    """
    
    configured_agents: List[str] = Field(
        ...,
        description="已配置的Agent列表\n\n系统中配置的所有Agent类型ID列表，无论其当前是否可用。",
        example=["writing", "db"]
    )
    
    available_agents: List[str] = Field(
        ...,
        description="可用的Agent列表\n\n成功初始化并可使用的Agent类型ID列表。\n这些Agent可以正常处理用户请求。",
        example=["writing"]
    )
    
    unavailable_agents: List[str] = Field(
        ...,
        description="不可用的Agent列表\n\n配置了但初始化失败的Agent类型ID列表。\n这些Agent当前无法处理用户请求。",
        example=["db"]
    )
    
    agent_details: List[AgentInfo] = Field(
        ...,
        description="Agent详细信息列表\n\n包含所有已配置Agent的详细信息，包括ID和显示名称。\n前端可根据这些信息构建Agent选择界面。",
        example=[
            {"id": "writing", "name": "写作助手"},
            {"id": "db", "name": "数据库助手"}
        ]
    )


@router.get("/agents", response_model=Union[AgentListResponse, ErrorResponse])
async def list_agents():
    """
    获取可用Agent列表
    
    获取系统中所有配置的AI助手信息，包括可用的和不可用的。
    可用于前端展示可选择的AI助手列表。
    
    Returns:
        AgentListResponse: 包含不同类型Agent列表的字典
        
        返回字段说明:
        - configured_agents (List[str]): 系统中配置的所有Agent类型列表
        - available_agents (List[str]): 成功初始化并可使用的Agent类型列表
        - unavailable_agents (List[str]): 配置了但初始化失败的Agent类型列表
        - agent_details (List[AgentInfo]): Agent详细信息列表，包括ID和名称
        
    Examples:
        成功响应示例:
        ```json
        {
            "configured_agents": ["writing", "db"],
            "available_agents": ["writing"],
            "unavailable_agents": ["db"],
            "agent_details": [
                {
                    "id": "writing",
                    "name": "写作助手"
                },
                {
                    "id": "db",
                    "name": "数据库助手"
                }
            ]
        }
        ```
        
        错误响应示例:
        ```json
        {
            "error": "获取Agent列表失败"
        }
        ```
    """
    try:
        if not multi_agent_manager:
            return {"error": "Agent管理器未初始化"}
            
        # 获取所有配置的Agent（包括初始化失败的）
        configured_agents = list(agent_configs.keys())
        # 获取成功初始化的Agent
        available_agents = multi_agent_manager.get_available_agents()
        
        # 创建Agent详细信息列表
        agent_details = []
        for agent_id in configured_agents:
            try:
                # 获取Agent实例以获取AGENT_NAME
                agent = multi_agent_manager.get_agent(agent_id)
                agent_name = agent.AGENT_NAME if agent and hasattr(agent, 'AGENT_NAME') and agent.AGENT_NAME else f'{agent_id}助手'
                
                # 添加Agent信息
                agent_details.append(AgentInfo(
                    id=agent_id,
                    name=agent_name
                ))
            except Exception as e:
                logger.warning(f"获取Agent {agent_id} 信息时出错: {e}")
                agent_details.append(AgentInfo(
                    id=agent_id,
                    name=f'{agent_id}助手'
                ))
        
        return AgentListResponse(
            configured_agents=configured_agents,
            available_agents=available_agents,
            unavailable_agents=[agent for agent in configured_agents if agent not in available_agents],
            agent_details=agent_details
        )
    except Exception as e:
        logger.error(f"获取Agent列表时出错: {e}")
        return ErrorResponse(error="获取Agent列表失败")


@router.post("/stream_chat", response_model=StreamChatResponseDoc, summary="流式对话接口")
async def stream_chat(request: ChatRequest):
    """
    与指定的AI助手进行流式对话。流式响应会逐步返回AI助手的回复，提供更好的用户体验。

    - 成功时：多次返回 {"data": "内容"}，最后返回 {"event": "end", "data": "[DONE]"}
    - 错误时：返回 {"event": "error", "data": "错误信息"}
    """
    chat_id = request.chat_id or str(uuid.uuid4())
    # 检查Agent管理器是否可用
    if not multi_agent_manager:
        async def error_gen():
            yield {"data": f"Agent管理器未初始化", "event": "error"}
        return EventSourceResponse(error_gen())
    # 获取指定的Agent
    agent = multi_agent_manager.get_agent(request.agent_type)
    if not agent:
        async def error_gen():
            yield {"data": f"Agent '{request.agent_type}' 不可用或初始化失败", "event": "error"}
        return EventSourceResponse(error_gen())
    # 检查模型提供商管理器是否可用
    if not model_provider_manager:
        async def error_gen():
            yield {"data": "模型提供商管理器未初始化", "event": "error"}
        return EventSourceResponse(error_gen())
    provider_name = request.provider_name if request.provider_name in model_provider_manager.list_configured_providers() else model_provider_manager.get_default_provider()
    def response_stream():
        for chunk in agent.stream_chat(
            message=request.message,
            chat_id=chat_id,
            user_id=request.user_id,
            provider_name=provider_name,
            model_name=request.model_name
        ):
            yield {"data": chunk}
        yield {"event": "end", "data": "[DONE]"}
    return EventSourceResponse(response_stream())


@router.get("/models", response_model=Union[ModelsResponse, ErrorResponse])
async def list_models():
    """
    获取可用模型列表
    
    获取系统中所有配置并可用的AI模型信息，按提供商分组。
    可用于前端展示模型选择列表。
    
    Returns:
        ModelsResponse: 包含可用模型信息的字典
        
        成功时返回字段说明:
        - models (Dict[str, List[str]]): 按提供商分组的模型列表
          - key (str): 模型提供商名称
          - value (List[str]): 该提供商下可用的模型名称列表
          
        失败时返回字段说明:
        - error (str): 错误信息描述
        
    Examples:
        成功响应示例:
        ```json
        {
            "models": {
                "qwen": ["qwen-turbo", "qwen-plus", "qwen-max"]
            }
        }
        ```
        
        错误响应示例:
        ```json
        {
            "error": "获取模型列表失败"
        }
        ```
    """
    try:
        if not model_provider_manager:
            return ErrorResponse(error="模型提供商管理器未初始化")
            
        models = model_provider_manager.get_all_available_models()
        return ModelsResponse(models=models)
    except Exception as e:
        logger.error(f"获取模型列表时出错: {e}")
        return ErrorResponse(error="获取模型列表失败")

@router.post("/chat", response_model=Union[ChatResponseUnion, ErrorResponse])
async def chat(request: ChatRequest):
    """
    非流式对话接口
    
    与指定的AI助手进行非流式对话。一次性返回完整的AI助手回复，
    适用于不需要实时显示回复内容的场景。
    
    Args:
        request (ChatRequest): 聊天请求对象，包含用户消息和相关配置
        
    Returns:
        dict: 包含聊天结果的字典
        
        成功时返回字段说明:
        - chat_id (str): 聊天会话ID
        - message (str): AI助手的完整回复内容
        
        失败时返回字段说明:
        - chat_id (str): 聊天会话ID
        - message (str): 错误信息描述
        - error (bool): 标识这是一个错误响应
        
        或者:
        - error (str): 错误信息描述
        
    Examples:
        请求示例:
        ```
        POST /api/chat
        Content-Type: application/json
        
        {
            "message": "你好，能帮我写一篇科幻小说吗？",
            "agent_type": "writing",
            "chat_id": "chat_123456"
        }
        ```
        
        成功响应示例:
        ```json
        {
            "chat_id": "chat_123456",
            "message": "你好！我很乐意帮你写一篇科幻小说..."
        }
        ```
        
        Agent不可用响应示例:
        ```json
        {
            "chat_id": "chat_123456",
            "message": "Agent 'writing' 不可用或初始化失败",
            "error": true
        }
        ```
    """
    try:
        # 如果没有提供chat_id，则生成一个新的
        chat_id = request.chat_id or str(uuid.uuid4())
        
        # 检查Agent管理器是否可用
        if not multi_agent_manager:
            error_msg = "Agent管理器未初始化"
            logger.error(error_msg)
            return ChatResponseUnion(chat_id=chat_id, message=error_msg, error=True)
        
        # 获取指定的Agent
        agent = multi_agent_manager.get_agent(request.agent_type)
        if not agent:
            # 如果没有找到指定的Agent，直接返回错误信息而不是使用默认Agent
            error_msg = f"Agent '{request.agent_type}' 不可用或初始化失败"
            logger.warning(error_msg)
            return ChatResponseUnion(chat_id=chat_id, message=error_msg, error=True)
        
        logger.info(f"收到聊天请求: chat_id={chat_id}, message={request.message}")
        
        # 检查模型提供商管理器是否可用
        if not model_provider_manager:
            error_msg = "模型提供商管理器未初始化"
            logger.error(error_msg)
            return ChatResponseUnion(chat_id=chat_id, message=error_msg, error=True)
            
        # 如果没有提供provider_name或者无效，则使用默认提供商
        provider_name = request.provider_name if request.provider_name in model_provider_manager.list_configured_providers() else model_provider_manager.get_default_provider()
        
        # 提取user_id
        user_id = request.user_id
        logger.info(f"处理聊天请求: chat_id={chat_id}, message={request.message}, user_id={user_id}")

        # 使用Agent进行对话，支持用户指定的模型或默认提供商
        response = await agent.achat(
            message=request.message,
            chat_id=chat_id,
            user_id=user_id,  # 使用提取的user_id
            provider_name=provider_name,
            model_name=request.model_name
        )
        
        return ChatResponseUnion(
            chat_id=chat_id,
            message=response
        )
        
    except Exception as e:
        logger.error(f"处理聊天请求时出错: {e}", exc_info=True)
        return ErrorResponse(error="处理请求时发生错误")


@router.get("/health")
async def health_check():
    """
    健康检查接口
    
    用于检查服务是否正常运行。通常用于负载均衡器的健康检查
    或者前端应用启动时检查服务状态。
    
    Returns:
        dict: 服务健康状态信息
        
        返回字段说明:
        - status (str): 服务状态，"healthy"表示健康
        - message (str): 状态描述信息
        
    Examples:
        成功响应示例:
        ```json
        {
            "status": "healthy",
            "message": "服务运行正常"
        }
        ```
    """
    # 检查关键组件状态
    status = "healthy"
    message = "服务运行正常"
    
    if not model_provider_manager:
        status = "degraded"
        message = "模型提供商管理器未初始化"
    
    if not multi_agent_manager:
        status = "degraded"
        message = "Agent管理器未初始化"
    
    return {"status": status, "message": message}

# 确保正确导出router
__all__ = ['router']
