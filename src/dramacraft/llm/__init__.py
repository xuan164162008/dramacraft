"""
LLM integration module for Video MCP service.

This module provides abstraction layer for Chinese LLM APIs with proper error handling,
rate limiting, and configuration management.

Supported providers:
- Baidu Qianfan (百度千帆)
- Alibaba Tongyi Qianwen (阿里通义千问)
- Tencent Hunyuan (腾讯混元)
"""

from .base import BaseLLMClient, LLMError, LLMResponse
from .factory import create_llm_client

__all__ = [
    "BaseLLMClient",
    "LLMResponse",
    "LLMError",
    "create_llm_client",
]
