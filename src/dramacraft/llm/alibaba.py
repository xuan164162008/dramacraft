"""
Alibaba Tongyi Qianwen LLM client implementation.

This module provides integration with Alibaba's Tongyi Qianwen platform
using the DashScope API for Qwen series models.
"""

from typing import Any

import httpx

from .base import (
    AuthenticationError,
    BaseLLMClient,
    ContentFilterError,
    GenerationParams,
    LLMError,
    LLMResponse,
    RateLimitError,
)


class AlibabaTongyiClient(BaseLLMClient):
    """Alibaba Tongyi Qianwen LLM client."""

    # DashScope API configuration
    BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    # Supported models
    SUPPORTED_MODELS = [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-max-1201",
        "qwen-max-longcontext",
        "qwen1.5-72b-chat",
        "qwen1.5-14b-chat",
        "qwen1.5-7b-chat",
        "qwen-72b-chat",
        "qwen-14b-chat",
        "qwen-7b-chat",
    ]

    def __init__(
        self,
        api_key: str,
        model_name: str = "qwen-turbo",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Alibaba Tongyi client.

        Args:
            api_key: DashScope API key
            model_name: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries
        """
        super().__init__(
            api_key=api_key,
            secret_key=None,  # Not needed for DashScope
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "alibaba"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return self.SUPPORTED_MODELS.copy()

    async def _make_request(
        self,
        prompt: str,
        params: GenerationParams,
    ) -> dict[str, Any]:
        """
        Make request to Alibaba DashScope API.

        Args:
            prompt: Input prompt
            params: Generation parameters

        Returns:
            Raw API response

        Raises:
            LLMError: If request fails
        """
        # Prepare request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "disable",  # Disable server-sent events
        }

        # Prepare request payload
        payload = {
            "model": self.model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ]
            },
            "parameters": {
                "max_tokens": params.max_tokens,
                "temperature": params.temperature,
                "result_format": "message",
            }
        }

        # Add optional parameters
        if params.top_p is not None:
            payload["parameters"]["top_p"] = params.top_p

        if params.top_k is not None:
            payload["parameters"]["top_k"] = params.top_k

        if params.frequency_penalty is not None:
            payload["parameters"]["repetition_penalty"] = 1.0 + params.frequency_penalty

        if params.stop_sequences:
            payload["parameters"]["stop"] = params.stop_sequences

        if params.stream:
            payload["parameters"]["incremental_output"] = True
            headers["X-DashScope-SSE"] = "enable"

        try:
            response = await self._client.post(
                self.BASE_URL,
                json=payload,
                headers=headers,
            )

            # Handle HTTP errors
            if response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded",
                    provider=self.provider_name,
                    error_code="rate_limit",
                )
            elif response.status_code == 401:
                raise AuthenticationError(
                    "Invalid API key",
                    provider=self.provider_name,
                    error_code="invalid_api_key",
                )
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("message", "Bad request")
                raise LLMError(
                    f"Bad request: {error_msg}",
                    provider=self.provider_name,
                    error_code="bad_request",
                    details=error_data,
                )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            raise LLMError(
                f"HTTP request failed: {str(e)}",
                provider=self.provider_name,
            ) from e

    def _parse_response(self, response: dict[str, Any]) -> LLMResponse:
        """
        Parse Alibaba DashScope API response.

        Args:
            response: Raw API response

        Returns:
            Parsed LLM response

        Raises:
            LLMError: If parsing fails
        """
        try:
            # Check for API errors
            if response.get("status_code") != 200:
                error_code = response.get("code", "unknown")
                error_msg = response.get("message", "Unknown error")

                # Map specific error codes
                if "InvalidApiKey" in error_code:
                    raise AuthenticationError(
                        f"Invalid API key: {error_msg}",
                        provider=self.provider_name,
                        error_code=error_code,
                    )
                elif "Throttling" in error_code or "FlowControl" in error_code:
                    raise RateLimitError(
                        f"Rate limit exceeded: {error_msg}",
                        provider=self.provider_name,
                        error_code=error_code,
                    )
                elif "DataInspection" in error_code:
                    raise ContentFilterError(
                        f"Content filtered: {error_msg}",
                        provider=self.provider_name,
                        error_code=error_code,
                    )
                else:
                    raise LLMError(
                        f"API error {error_code}: {error_msg}",
                        provider=self.provider_name,
                        error_code=error_code,
                    )

            # Extract response data
            output = response.get("output", {})
            usage = response.get("usage", {})

            # Get the generated text
            choices = output.get("choices", [])
            if not choices:
                raise LLMError(
                    "No choices in response",
                    provider=self.provider_name,
                )

            choice = choices[0]
            message = choice.get("message", {})
            text = message.get("content", "")

            # Determine finish reason
            finish_reason = choice.get("finish_reason", "stop")

            return LLMResponse(
                text=text,
                provider=self.provider_name,
                model=self.model_name,
                tokens_used=usage.get("total_tokens"),
                finish_reason=finish_reason,
                metadata={
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "request_id": response.get("request_id"),
                    "choice_index": choice.get("index", 0),
                }
            )

        except KeyError as e:
            raise LLMError(
                f"Failed to parse response: missing key {str(e)}",
                provider=self.provider_name,
            ) from e
        except Exception as e:
            raise LLMError(
                f"Failed to parse response: {str(e)}",
                provider=self.provider_name,
            ) from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
