import logging
from typing import List, Dict, Type, Optional, Any
import importlib
import pkgutil
import inspect

from langchain_core.tools import BaseTool

from .base_agent import BaseAgent
from .model_provider import ModelProviderManager

logger = logging.getLogger(__name__)


class ModelProvider:
    """AI模型提供商管理器"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class):
        """注册模型提供商"""
        cls._providers[name.lower()] = provider_class
        logger.debug(f"注册模型提供商: {name}")
    
    @classmethod
    def get_provider(cls, name: str, config: Dict[str, Any]):
        """获取模型提供商实例"""
        provider_class = cls._providers.get(name.lower())
        if not provider_class:
            raise ValueError(f"不支持的模型提供商: {name}")
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls):
        """获取所有可用的模型提供商"""
        return list(cls._providers.keys())


class AgentFactory:
    """Agent工厂 - 统一管理所有Agent类型"""

    # Agent实例缓存
    _instances: Dict[str, BaseAgent] = {}
    # 动态发现的Agent类缓存
    _discovered_agents: Optional[Dict[str, Type[BaseAgent]]] = None

    @classmethod
    def _discover_agents(cls) -> Dict[str, Type[BaseAgent]]:
        """动态发现所有Agent类"""
        if cls._discovered_agents is not None:
            return cls._discovered_agents

        agents = {}

        # 扫描当前包中的所有模块
        try:
            import web.agent as agent_package
            package_path = agent_package.__path__

            for importer, modname, ispkg in pkgutil.iter_modules(package_path):
                # 跳过基类、工厂和初始化模块
                if modname in ['base_agent', 'agent_factory', '__init__', 'supervisor_agnet', 'model_provider', 'openai_provider']:
                    continue
                    
                try:
                    # 动态导入模块
                    module = importlib.import_module(f'web.agent.{modname}')

                    # 查找继承自BaseAgent的类（排除BaseAgent本身）
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseAgent) and 
                            obj != BaseAgent and
                            hasattr(obj, 'AGENT_TYPE')):
                            
                            agent_key = obj.AGENT_TYPE or name.lower().replace('agent', '')
                            agents[agent_key] = obj
                            logger.debug(f"发现Agent: {agent_key} -> {name}")

                except Exception as e:
                    logger.warning(f"导入模块 {modname} 时出错: {e}")
        except ImportError as e:
            logger.warning(f"导入agent包时出错: {e}")

        cls._discovered_agents = agents
        logger.info(f"动态发现 {len(agents)} 个Agent: {list(agents.keys())}")
        return agents

    @classmethod
    def create_agent(cls, agent_type: str, config: Optional[Dict[str, Any]] = None,
                     model_provider_manager: Optional[ModelProviderManager] = None) -> BaseAgent:
        """
        创建Agent实例
        
        Args:
            agent_type: Agent类型
            config: Agent配置
            model_provider_manager: 模型提供商管理器
            
        Returns:
            BaseAgent: Agent实例
        """
        # 创建配置键用于缓存
        config_key = f"{agent_type}_{str(config)}"
        if config_key in cls._instances:
            return cls._instances[config_key]

        # 动态发现Agent
        agents = cls._discover_agents()
        
        # 查找对应的Agent类
        agent_class = agents.get(agent_type.lower())
        if not agent_class:
            # 如果找不到特定类型，尝试使用默认的通用Agent
            agent_class = agents.get('writing')  # 默认使用writing agent
            if not agent_class:
                raise ValueError(f"不支持的Agent类型: {agent_type}")

        # 确保配置中包含模型提供商管理器
        if config is None:
            config = {}
        if model_provider_manager:
            config['model_provider_manager'] = model_provider_manager
            
        # 创建实例并缓存
        instance = agent_class(config)
        cls._instances[config_key] = instance
        return instance

    @classmethod
    def get_available_agents(cls) -> List[str]:
        """
        获取所有可用的Agent列表
        
        Returns:
            List[str]: 可用Agent列表
        """
        agents = cls._discover_agents()
        return list(agents.keys())


class MultiAgentManager:
    """多Agent管理器 - 统一管理多个Agent实例"""

    def __init__(self, agent_configs: Dict[str, Dict[str, Any]],
                 model_provider_manager: Optional[ModelProviderManager] = None):
        """
        初始化多Agent管理器

        Args:
            agent_configs: 多个Agent的配置，格式：{agent_name: config}
            model_provider_manager: 模型提供商管理器
        """
        self.agents: Dict[str, BaseAgent] = {}
        self.default_agent = None
        self.model_provider_manager = model_provider_manager

        # 初始化所有配置的Agent
        for agent_name, config in agent_configs.items():
            try:
                agent = AgentFactory.create_agent(agent_name, config, model_provider_manager)
                self.agents[agent_name] = agent
                logger.info(f"Agent {agent_name} 初始化成功")

                # 设置默认Agent
                if self.default_agent is None:
                    self.default_agent = agent_name
            except Exception as e:
                logger.error(f"Agent {agent_name} 初始化失败: {e}")

    def get_available_agents(self) -> List[str]:
        """获取所有可用的Agent列表"""
        return list(self.agents.keys())

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        获取指定的Agent实例
        
        Args:
            agent_name: Agent名称
            
        Returns:
            BaseAgent: Agent实例，如果不存在则返回None
        """
        return self.agents.get(agent_name)

    def get_default_agent(self) -> Optional[BaseAgent]:
        """
        获取默认Agent实例
        
        Returns:
            BaseAgent: 默认Agent实例，如果没有则返回None
        """
        if self.default_agent:
            return self.agents.get(self.default_agent)
        return None


# 保持向后兼容性的函数
def create_agent_by_type(agent_type: str, chat_model, **kwargs) -> BaseAgent:
    """
    根据类型创建智能体（向后兼容）
    
    Args:
        agent_type: 智能体类型 ('writing', 'general', 'custom')
        chat_model: 聊天模型实例
        **kwargs: 其他参数
        
    Returns:
        BaseAgent: 创建的智能体实例
    """
    config = {"chat_model": chat_model, **kwargs}
    return AgentFactory.create_agent(agent_type, config)


def create_writing_agent(chat_model, memory_backend: str = "memory") -> BaseAgent:
    """
    创建写作智能体（向后兼容）
    
    Args:
        chat_model: 聊天模型实例
        memory_backend: 记忆后端类型
        
    Returns:
        BaseAgent: 写作智能体实例
    """
    config = {
        "chat_model": chat_model,
        "memory_backend": memory_backend
    }
    return AgentFactory.create_agent("writing", config)


def create_general_agent(chat_model, memory_backend: str = "memory") -> BaseAgent:
    """
    创建通用智能体（向后兼容）
    
    Args:
        chat_model: 聊天模型实例
        memory_backend: 记忆后端类型
        
    Returns:
        BaseAgent: 通用智能体实例
    """
    config = {
        "chat_model": chat_model,
        "memory_backend": memory_backend
    }
    return AgentFactory.create_agent("writing", config)  # 使用writing作为通用agent


def create_custom_agent(chat_model,
                       system_message: str,
                       tools: List[BaseTool],
                       memory_backend: str = "memory") -> BaseAgent:
    """
    创建自定义智能体（向后兼容）
    
    Args:
        chat_model: 聊天模型实例
        system_message: 系统消息
        tools: 工具列表
        memory_backend: 记忆后端类型
        
    Returns:
        BaseAgent: 自定义智能体实例
    """
    config = {
        "chat_model": chat_model,
        "system_message": system_message,
        "tools": tools,
        "memory_backend": memory_backend
    }
    return AgentFactory.create_agent("writing", config)  # 使用writing作为自定义agent