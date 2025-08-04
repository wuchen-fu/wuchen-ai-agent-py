import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """基础模型提供商抽象类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    @abstractmethod
    def get_chat_model(self, model_name: str = None, **kwargs):
        """获取聊天模型实例"""
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """列出支持的模型"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass


class ModelProviderManager:
    """模型提供商管理器"""
    
    def __init__(self):
        self._providers: Dict[str, BaseModelProvider] = {}
        self._default_provider: Optional[str] = None
    
    def register_provider(self, name: str, provider: BaseModelProvider, is_default: bool = False):
        """注册模型提供商"""
        self._providers[name] = provider
        if is_default or self._default_provider is None:
            self._default_provider = name
        logger.info(f"注册模型提供商: {name}")
    
    def get_provider(self, name: str = None) -> Optional[BaseModelProvider]:
        """获取模型提供商"""
        if not name:
            name = self._default_provider
        
        if not name:
            return None
            
        return self._providers.get(name)
    
    def get_chat_model(self, provider_name: str = None, model_name: str = None, **kwargs):
        """获取聊天模型实例"""
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
        return self._default_provider