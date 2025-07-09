"""
Factory for creating LLM clients.

This module provides a factory function to create LLM clients based on
provider configuration.
"""

from ..config import LLMConfig
from .alibaba import AlibabaTongyiClient
from .baidu import BaiduQianfanClient
from .base import BaseLLMClient, LLMError


def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    """
    Create an LLM client based on configuration.

    Args:
        config: LLM configuration

    Returns:
        Configured LLM client

    Raises:
        LLMError: If provider is not supported or configuration is invalid
    """
    provider = config.provider.lower()

    if provider == "baidu":
        if not config.secret_key:
            raise LLMError(
                "Baidu provider requires both api_key and secret_key",
                provider="baidu",
            )

        return BaiduQianfanClient(
            api_key=config.api_key,
            secret_key=config.secret_key,
            model_name=config.model_name,
            timeout=config.timeout,
        )

    elif provider == "alibaba":
        return AlibabaTongyiClient(
            api_key=config.api_key,
            model_name=config.model_name,
            timeout=config.timeout,
        )

    elif provider == "tencent":
        # TODO: Implement Tencent Hunyuan client
        raise LLMError(
            "Tencent provider not yet implemented",
            provider="tencent",
        )

    else:
        raise LLMError(
            f"Unsupported LLM provider: {provider}",
            provider=provider,
        )
