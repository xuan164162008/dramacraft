"""
Baidu Qianfan LLM client implementation.

This module provides integration with Baidu's Qianfan platform for ERNIE series models.
Supports ERNIE-Bot, ERNIE-Bot-turbo, and other Baidu LLM models.
"""

import time
from typing import Any, Optional

import httpx

from .base import (
    AuthenticationError,
    BaseLLMClient,
    ContentFilterError,
    GenerationParams,
    LLMError,
    LLMResponse,
    ModelNotFoundError,
    RateLimitError,
)


class BaiduQianfanClient(BaseLLMClient):
    """Baidu Qianfan LLM client."""

    # Baidu Qianfan API endpoints
    BASE_URL = "https://aip.baidubce.com"
    TOKEN_URL = f"{BASE_URL}/oauth/2.0/token"

    # Model endpoints mapping
    MODEL_ENDPOINTS = {
        "ERNIE-Bot": "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
        "ERNIE-Bot-turbo": "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant",
        "ERNIE-Bot-4": "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro",
        "ERNIE-3.5-8K": "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
        "ERNIE-Speed": "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_speed",
        "ERNIE-Lite-8K": "/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-lite-8k",
    }

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        model_name: str = "ERNIE-Bot-turbo",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Baidu Qianfan client.

        Args:
            api_key: Baidu API key
            secret_key: Baidu secret key
            model_name: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Delay between retries
        """
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            model_name=model_name,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "baidu"

    @property
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        return list(self.MODEL_ENDPOINTS.keys())

    async def _get_access_token(self) -> str:
        """
        Get or refresh access token for Baidu API.

        Returns:
            Valid access token

        Raises:
            AuthenticationError: If authentication fails
        """
        current_time = time.time()

        # Check if we have a valid token
        if self._access_token and current_time < self._token_expires_at:
            return self._access_token

        # Request new token
        try:
            response = await self._client.post(
                self.TOKEN_URL,
                params={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.secret_key,
                }
            )
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                raise AuthenticationError(
                    f"Authentication failed: {data.get('error_description', data['error'])}",
                    provider=self.provider_name,
                    error_code=data.get("error"),
                )

            self._access_token = data["access_token"]
            # Set expiration time (subtract 5 minutes for safety)
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = current_time + expires_in - 300

            return self._access_token

        except httpx.HTTPError as e:
            raise AuthenticationError(
                f"Failed to get access token: {str(e)}",
                provider=self.provider_name,
            ) from e

    async def _make_request(
        self,
        prompt: str,
        params: GenerationParams,
    ) -> dict[str, Any]:
        """
        Make request to Baidu Qianfan API.

        Args:
            prompt: Input prompt
            params: Generation parameters

        Returns:
            Raw API response

        Raises:
            LLMError: If request fails
        """
        # Get access token
        access_token = await self._get_access_token()

        # Get model endpoint
        if self.model_name not in self.MODEL_ENDPOINTS:
            raise ModelNotFoundError(
                f"Model '{self.model_name}' not supported",
                provider=self.provider_name,
            )

        endpoint = self.MODEL_ENDPOINTS[self.model_name]
        url = f"{self.BASE_URL}{endpoint}?access_token={access_token}"

        # Prepare request payload
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "max_output_tokens": params.max_tokens,
            "temperature": params.temperature,
            "stream": params.stream,
        }

        # Add optional parameters
        if params.top_p is not None:
            payload["top_p"] = params.top_p

        if params.frequency_penalty is not None:
            payload["penalty_score"] = params.frequency_penalty

        if params.stop_sequences:
            payload["stop"] = params.stop_sequences

        try:
            response = await self._client.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                }
            )

            # Handle HTTP errors
            if response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded",
                    provider=self.provider_name,
                    error_code="rate_limit",
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
        Parse Baidu API response.

        Args:
            response: Raw API response

        Returns:
            Parsed LLM response

        Raises:
            LLMError: If parsing fails
        """
        try:
            # Check for API errors
            if "error_code" in response:
                error_code = response["error_code"]
                error_msg = response.get("error_msg", "Unknown error")

                # Map specific error codes
                if error_code == 18:
                    raise RateLimitError(
                        f"Rate limit exceeded: {error_msg}",
                        provider=self.provider_name,
                        error_code=str(error_code),
                    )
                elif error_code in [1, 2, 3, 4]:
                    raise AuthenticationError(
                        f"Authentication error: {error_msg}",
                        provider=self.provider_name,
                        error_code=str(error_code),
                    )
                elif error_code == 336003:
                    raise ContentFilterError(
                        f"Content filtered: {error_msg}",
                        provider=self.provider_name,
                        error_code=str(error_code),
                    )
                else:
                    raise LLMError(
                        f"API error {error_code}: {error_msg}",
                        provider=self.provider_name,
                        error_code=str(error_code),
                    )

            # Extract response data
            result = response.get("result", "")
            usage = response.get("usage", {})

            # Determine finish reason
            finish_reason = "stop"
            if response.get("is_truncated", False):
                finish_reason = "length"

            return LLMResponse(
                text=result,
                provider=self.provider_name,
                model=self.model_name,
                tokens_used=usage.get("total_tokens"),
                finish_reason=finish_reason,
                metadata={
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens"),
                    "is_truncated": response.get("is_truncated", False),
                    "need_clear_history": response.get("need_clear_history", False),
                    "ban_round": response.get("ban_round", 0),
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
