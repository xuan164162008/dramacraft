"""
Abstract base class for LLM clients.

This module provides the base interface for all LLM providers with common
functionality for text generation, prompt handling, and response processing.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class LLMProvider(Enum):
    """Supported LLM providers."""
    BAIDU = "baidu"
    ALIBABA = "alibaba"
    TENCENT = "tencent"


@dataclass
class LLMResponse:
    """Response from LLM generation."""

    text: str
    """Generated text content."""

    provider: str
    """LLM provider name."""

    model: str
    """Model name used for generation."""

    tokens_used: Optional[int] = None
    """Number of tokens used in generation."""

    finish_reason: Optional[str] = None
    """Reason for completion (e.g., 'stop', 'length', 'content_filter')."""

    response_time: Optional[float] = None
    """Response time in seconds."""

    timestamp: Optional[datetime] = None
    """Timestamp of the response."""

    metadata: Optional[dict[str, Any]] = None
    """Additional metadata from the provider."""

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.details = details or {}


class RateLimitError(LLMError):
    """Exception raised when rate limit is exceeded."""
    pass


class AuthenticationError(LLMError):
    """Exception raised when authentication fails."""
    pass


class ModelNotFoundError(LLMError):
    """Exception raised when the specified model is not found."""
    pass


class ContentFilterError(LLMError):
    """Exception raised when content is filtered by the provider."""
    pass


@dataclass
class GenerationParams:
    """Parameters for text generation."""

    max_tokens: int = 2000
    """Maximum number of tokens to generate."""

    temperature: float = 0.7
    """Temperature for randomness (0.0 to 2.0)."""

    top_p: Optional[float] = None
    """Top-p sampling parameter."""

    top_k: Optional[int] = None
    """Top-k sampling parameter."""

    frequency_penalty: Optional[float] = None
    """Frequency penalty for repetition."""

    presence_penalty: Optional[float] = None
    """Presence penalty for repetition."""

    stop_sequences: Optional[list[str]] = None
    """Stop sequences to end generation."""

    stream: bool = False
    """Whether to stream the response."""


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    def __init__(
        self,
        api_key: str,
        secret_key: Optional[str] = None,
        model_name: str = "default",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: API key for the LLM provider
            secret_key: Secret key for the LLM provider (if required)
            model_name: Name of the model to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Rate limiting
        self._last_request_time = 0.0
        self._min_request_interval = 0.1  # Minimum interval between requests

        # Statistics
        self._total_requests = 0
        self._total_tokens = 0
        self._total_errors = 0

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """Return list of supported models."""
        pass

    @abstractmethod
    async def _make_request(
        self,
        prompt: str,
        params: GenerationParams,
    ) -> dict[str, Any]:
        """
        Make the actual API request to the LLM provider.

        Args:
            prompt: The input prompt
            params: Generation parameters

        Returns:
            Raw response from the API

        Raises:
            LLMError: If the request fails
        """
        pass

    @abstractmethod
    def _parse_response(self, response: dict[str, Any]) -> LLMResponse:
        """
        Parse the raw API response into a standardized format.

        Args:
            response: Raw response from the API

        Returns:
            Parsed LLM response

        Raises:
            LLMError: If parsing fails
        """
        pass

    async def generate(
        self,
        prompt: str,
        params: Optional[GenerationParams] = None,
    ) -> LLMResponse:
        """
        Generate text using the LLM.

        Args:
            prompt: The input prompt
            params: Generation parameters (uses defaults if None)

        Returns:
            Generated response

        Raises:
            LLMError: If generation fails
        """
        if params is None:
            params = GenerationParams()

        # Validate model
        if self.model_name not in self.supported_models:
            raise ModelNotFoundError(
                f"Model '{self.model_name}' not supported by {self.provider_name}",
                provider=self.provider_name
            )

        # Rate limiting
        await self._enforce_rate_limit()

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()

                # Make the request
                response = await self._make_request(prompt, params)

                # Parse the response
                parsed_response = self._parse_response(response)
                parsed_response.response_time = time.time() - start_time

                # Update statistics
                self._total_requests += 1
                if parsed_response.tokens_used:
                    self._total_tokens += parsed_response.tokens_used

                return parsed_response

            except Exception as e:
                last_error = e
                self._total_errors += 1

                if attempt < self.max_retries:
                    # Wait before retrying
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    # Convert to LLMError if needed
                    if not isinstance(e, LLMError):
                        raise LLMError(
                            f"Request failed after {self.max_retries} retries: {str(e)}",
                            provider=self.provider_name
                        ) from e
                    raise

        # This should never be reached, but just in case
        if last_error:
            raise last_error

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)

        self._last_request_time = time.time()

    def get_statistics(self) -> dict[str, Any]:
        """Get client statistics."""
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_errors": self._total_errors,
            "error_rate": self._total_errors / max(self._total_requests, 1),
        }

    def reset_statistics(self) -> None:
        """Reset client statistics."""
        self._total_requests = 0
        self._total_tokens = 0
        self._total_errors = 0
