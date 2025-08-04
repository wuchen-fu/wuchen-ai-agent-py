import logging
from typing import List, Optional, Dict, Any

from .model_provider import OpenAIAdaptationProvider

logger = logging.getLogger(__name__)


class QwenProvider(OpenAIAdaptationProvider):
    """通义千问提供商实现"""

    # 提供商配置
    DEFAULT_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    DEFAULT_MODEL = 'qwen-turbo'
    PROVIDER_NAME = '通义千问'
    AVAILABLE_MODELS = [
        'qwen-turbo',
        'qwen-plus',
        'qwen-max'
    ]
