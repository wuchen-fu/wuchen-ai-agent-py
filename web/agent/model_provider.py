import logging
import os
from typing import Dict, List, Optional, Any, Type
from abc import ABC, abstractmethod
import importlib
import pkgutil
import inspect
from langchain_openai import ChatOpenAI

# 导入配置
from config import config

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """AI提供商抽象基类 - 定义统一接口规范"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """初始化提供商配置"""
        self.name = name
        self.config = config
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()

    @abstractmethod
    def get_chat_model(self, model_name: str = None, **kwargs):
        """获取聊天模型实例 - 所有提供商必须实现"""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """列出支持的模型 - 所有提供商必须实现"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置有效性 - 所有提供商必须实现"""
        pass

    def get_provider_name(self) -> str:
        """获取提供商显示名称"""
        return getattr(self, 'PROVIDER_NAME', self.provider_name.capitalize())


class OpenAIAdaptationProvider(BaseAIProvider):
    """OpenAI兼容提供商基类 - 统一OpenAI SDK调用方式"""

    # 子类需要重写的配置
    DEFAULT_BASE_URL = None
    DEFAULT_MODEL = None
    PROVIDER_NAME = None
    AVAILABLE_MODELS = []

    def __init__(self, name: str, config: Dict[str, Any]):
        """初始化OpenAI兼容客户端"""
        super().__init__(name, config)
        # 注意：这里不直接初始化客户端，因为get_chat_model方法会直接创建新的实例
        # 而不是使用共享的client

    def get_chat_model(self, model_name: str = None, **kwargs):
        """获取聊天模型实例"""
        if not model_name:
            model_name = self.config.get('model', self.DEFAULT_MODEL) or (
                self.AVAILABLE_MODELS[0] if self.AVAILABLE_MODELS else None)

        if not model_name:
            raise ValueError("未指定模型且没有默认模型可用")

        return ChatOpenAI(
            model=model_name,
            api_key=self.config.get('api_key'),
            base_url=self.config.get('base_url', self.DEFAULT_BASE_URL),
            max_tokens=self.config.get('max_tokens', 1000),
            temperature=self.config.get('temperature', 0.7),
            **kwargs
        )

    def list_models(self) -> List[str]:
        """列出支持的模型"""
        return self.AVAILABLE_MODELS

    def validate_config(self) -> bool:
        """验证配置有效性"""
        api_key = self.config.get('api_key')
        has_models = bool(self.AVAILABLE_MODELS)
        is_valid = bool(api_key and has_models)
        logger.debug(f"验证配置: api_key={bool(api_key)}, has_models={has_models}, valid={is_valid}")
        return is_valid


class ModelProviderManager:
    """模型提供商管理器"""
    
    def __init__(self, auto_register_providers: bool = False):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._default_provider: Optional[str] = None
        self._discovered_providers: Optional[Dict[str, Type[BaseAIProvider]]] = None
        
        # 如果需要自动注册提供商
        if auto_register_providers:
            self.auto_register_providers_from_config()
    
    def _discover_providers(self) -> Dict[str, Type[BaseAIProvider]]:
        """动态发现所有提供商类 - 这是魔法发生的地方"""
        if self._discovered_providers is not None:
            return self._discovered_providers

        providers = {}

        # 扫描当前包中的所有模块
        try:
            import web.agent as agent_package
            package_path = agent_package.__path__

            for importer, modname, ispkg in pkgutil.iter_modules(package_path):
                # 跳过不需要的模块
                if modname in ['base_agent', 'agent_factory', '__init__', 'model_provider', 'agent_factory']:
                    continue
                    
                try:
                    # 动态导入模块
                    module = importlib.import_module(f'web.agent.{modname}')
                    logger.debug(f"导入模块: {modname}")

                    # 查找继承自OpenAIAdaptationProvider的类（排除基类本身）
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, OpenAIAdaptationProvider) and 
                            obj != OpenAIAdaptationProvider and
                            hasattr(obj, 'PROVIDER_NAME')):

                            provider_key = name.lower().replace('provider', '')
                            providers[provider_key] = obj
                            logger.debug(f"发现提供商: {provider_key} -> {name}")

                except Exception as e:
                    logger.warning(f"导入模块 {modname} 时出错: {e}")
        except ImportError as e:
            logger.warning(f"导入agent包时出错: {e}")

        self._discovered_providers = providers
        logger.info(f"动态发现 {len(providers)} 个提供商: {list(providers.keys())}")
        return providers
    
    def auto_register_providers_from_config(self):
        """从配置文件自动注册模型提供商"""
        # 发现所有提供商类
        provider_classes = self._discover_providers()
        
        # 从配置获取所有AI提供商配置
        ai_configs = config.get_all_ai_configs()
        logger.info(f"配置中找到 {len(ai_configs)} 个AI提供商配置: {list(ai_configs.keys())}")
        
        # 根据配置注册提供商
        for provider_name, provider_config in ai_configs.items():
            logger.info(f"尝试注册提供商 {provider_name}，配置: {provider_config}")
            if provider_name in provider_classes:
                try:
                    provider_class = provider_classes[provider_name]
                    provider_instance = provider_class(provider_name, provider_config)
                    
                    # 验证配置
                    if provider_instance.validate_config():
                        is_default = (provider_name == config.DEFAULT_AI_PROVIDER)
                        self.register_provider(provider_name, provider_instance, is_default)
                        logger.info(f"成功注册模型提供商: {provider_name}")
                    else:
                        logger.warning(f"模型提供商 {provider_name} 配置验证失败")
                except Exception as e:
                    logger.error(f"注册模型提供商 {provider_name} 时出错: {e}")
            else:
                logger.warning(f"未找到模型提供商类: {provider_name}")
    
    def register_provider(self, name: str, provider: BaseAIProvider, is_default: bool = False):
        """注册模型提供商"""
        self._providers[name] = provider
        if is_default or self._default_provider is None:
            self._default_provider = name
        logger.info(f"注册模型提供商: {name}，默认提供商: {self._default_provider}")
    
    def get_provider(self, name: str = None) -> Optional[BaseAIProvider]:
        """获取模型提供商"""
        if not name:
            name = self._default_provider
        
        if not name:
            logger.warning("未找到默认提供商")
            return None
            
        provider = self._providers.get(name)
        if not provider:
            logger.warning(f"未找到提供商: {name}")
        return provider
    
    def get_chat_model(self, provider_name: str = None, model_name: str = None, **kwargs):
        """获取聊天模型实例"""
        logger.info(f"Getting chat model from provider: {provider_name}, model: {model_name}")
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"未找到模型提供商: {provider_name}")
        
        return provider.get_chat_model(model_name, **kwargs)
    
    def list_providers(self) -> List[str]:
        """列出所有提供商"""
        return list(self._providers.keys())
    
    def list_models(self, provider_name: str = None) -> List[str]:
        """列出指定提供商的模型"""
        provider = self.get_provider(provider_name)
        if not provider:
            return []
        return provider.list_models()
    
    def get_default_provider(self) -> Optional[str]:
        """获取默认提供商名称"""
        logger.info(f"默认提供商: {self._default_provider}")
        return self._default_provider

    def get_all_available_models(self) -> Dict[str, List[str]]:
        """获取所有可用模型"""
        all_models = {}
        for provider_name in self.list_providers():
            all_models[provider_name] = self.list_models(provider_name)
        return all_models

    def get_provider_display_name(self, provider_name: str) -> str:
        """获取提供商显示名称"""
        provider = self.get_provider(provider_name)
        if provider:
            return provider.get_provider_name()
        return provider_name.capitalize()
        
    def list_configured_providers(self) -> List[str]:
        """获取所有配置的提供商"""
        return list(self._providers.keys())