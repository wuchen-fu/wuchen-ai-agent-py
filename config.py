import os
import logging
from typing import List, Optional, Dict, Any


class Config:
    """应用配置类"""

    # 应用配置
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    APP_NAME: str = os.getenv('APP_NAME', 'AI聊天应用演示')
    APP_VERSION: str = os.getenv('APP_VERSION', '1.0.0')

    # Redis配置
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    REDIS_DB: int = int(os.getenv('REDIS_DB', 0))

    # Redis过期时间配置（秒）
    CONVERSATION_EXPIRE_TIME: int = int(os.getenv('CONVERSATION_EXPIRE_TIME', 7 * 24 * 3600))  # 7天
    SESSION_EXPIRE_TIME: int = int(os.getenv('SESSION_EXPIRE_TIME', 30 * 24 * 3600))  # 30天

    # AI提供商配置
    DEFAULT_AI_PROVIDER: str = os.getenv('DEFAULT_AI_PROVIDER', 'qwen')

    # AI提供商默认配置
    _DEFAULT_AI_CONFIG = {
        'max_tokens': 1000,
        'temperature': 0.7
    }

    # 默认配置映射 - 只包含当前系统支持的qwen提供商
    _DEFAULT_PROVIDER_CONFIGS = {
        'qwen': {'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1', 'model': 'qwen-turbo'}
    }

    @classmethod
    def _build_provider_config(cls, provider: str) -> dict:
        """构建单个AI提供商配置"""
        provider_upper = provider.upper()
        
        # 获取该提供商的默认配置
        provider_defaults = cls._DEFAULT_PROVIDER_CONFIGS.get(provider, {})
        
        config = {
            'api_key': os.getenv(f'{provider_upper}_API_KEY', ''),
            'base_url': os.getenv(f'{provider_upper}_BASE_URL', provider_defaults.get('base_url', '')),
            'model': os.getenv(f'{provider_upper}_MODEL', provider_defaults.get('model', '')),
            'max_tokens': int(os.getenv(f'{provider_upper}_MAX_TOKENS', cls._DEFAULT_AI_CONFIG['max_tokens'])),
            'temperature': float(os.getenv(f'{provider_upper}_TEMPERATURE', cls._DEFAULT_AI_CONFIG['temperature']))
        }
        
        # 记录配置信息用于调试
        logging.debug(f"提供商 {provider} 的配置: {config}")
        return config

    # AI提供商配置 - 动态生成
    @classmethod
    def _get_ai_providers_config(cls) -> dict:
        """获取所有AI提供商配置"""
        # 从默认配置映射中动态获取所有支持的提供商
        supported_providers = list(cls._DEFAULT_PROVIDER_CONFIGS.keys())
        return {provider: cls._build_provider_config(provider) for provider in supported_providers}

    # 延迟初始化AI提供商配置
    @property
    def AI_PROVIDERS_CONFIG(self) -> dict:
        if not hasattr(self, '_ai_providers_config'):
            self._ai_providers_config = self._get_ai_providers_config()
        return self._ai_providers_config

    # 对话配置
    MAX_HISTORY_MESSAGES: int = int(os.getenv('MAX_HISTORY_MESSAGES', 20))  # 最大历史消息数
    MAX_MESSAGE_LENGTH: int = int(os.getenv('MAX_MESSAGE_LENGTH', 50))  # 会话列表中显示的最大消息长度

    # 日志配置
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'DEBUG' if DEBUG else 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')
    LOG_FILE: str = os.getenv('LOG_FILE', 'app.log')

    # 服务器配置
    HOST: str = os.getenv('HOST', "localhost")
    PORT: int = int(os.getenv('PORT', 9091))

    @classmethod
    def get_redis_config(cls) -> dict:
        """获取Redis连接配置"""
        config = {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'decode_responses': True
        }

        if cls.REDIS_PASSWORD:
            config['password'] = cls.REDIS_PASSWORD

        return config

    @classmethod
    def get_all_ai_configs(cls) -> dict:
        """获取所有已配置API Key的AI提供商配置"""
        configs = cls._get_ai_providers_config()
        # 只返回有API密钥的配置
        filtered_configs = {name: config for name, config in configs.items() if config.get('api_key')}
        logging.info(f"过滤后的AI配置: {filtered_configs}")
        return filtered_configs

    @classmethod
    def get_log_level(cls) -> int:
        """获取日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(cls.LOG_LEVEL.upper(), logging.INFO)

    @classmethod
    def validate_config(cls) -> None:
        """验证必需的配置项"""
        # 检查是否至少配置了一个AI提供商
        providers_configured = cls.get_configured_providers()

        if not providers_configured:
            raise ValueError("至少需要配置一个AI提供商的API密钥")

        # 检查默认提供商是否已配置
        if cls.DEFAULT_AI_PROVIDER not in providers_configured:
            # 如果默认提供商未配置，使用第一个已配置的提供商
            cls.DEFAULT_AI_PROVIDER = providers_configured[0]
            print(f"警告: 默认AI提供商未配置或无效，自动设置为: {cls.DEFAULT_AI_PROVIDER}")

    @classmethod
    def get_configured_providers(cls) -> List[str]:
        """获取已配置API Key的AI提供商列表"""
        return list(cls.get_all_ai_configs().keys())

    @classmethod
    def get_log_file_path(cls) -> str:
        """获取日志文件完整路径"""
        return os.path.join(cls.LOG_DIR, cls.LOG_FILE)

    @classmethod
    def get_agent_configs(cls) -> Dict[str, Dict[str, Any]]:
        """获取Agent配置"""
        return {
            "writing": {

            },
            "db": {
                # 数据库Agent的配置
            }
        }


# 创建配置实例
config = Config()