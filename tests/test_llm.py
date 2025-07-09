"""
LLM模块测试。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from dramacraft.llm.base import (
    BaseLLMClient,
    LLMResponse,
    LLMError,
    GenerationParams,
    RateLimitError,
    AuthenticationError
)
from dramacraft.llm.factory import create_llm_client
from dramacraft.config import LLMConfig


class MockLLMClient(BaseLLMClient):
    """模拟LLM客户端用于测试。"""
    
    @property
    def provider_name(self) -> str:
        return "mock"
    
    @property
    def supported_models(self) -> list:
        return ["mock-model"]
    
    async def _make_request(self, prompt: str, params: GenerationParams) -> dict:
        return {
            "result": f"Mock response for: {prompt[:50]}...",
            "usage": {
                "total_tokens": 100,
                "prompt_tokens": 50,
                "completion_tokens": 50
            }
        }
    
    def _parse_response(self, response: dict) -> LLMResponse:
        return LLMResponse(
            text=response["result"],
            provider=self.provider_name,
            model=self.model_name,
            tokens_used=response["usage"]["total_tokens"],
            finish_reason="stop"
        )


class TestBaseLLMClient:
    """基础LLM客户端测试类。"""
    
    @pytest.fixture
    def mock_client(self):
        """创建模拟客户端。"""
        return MockLLMClient(
            api_key="test_key",
            model_name="mock-model"
        )
    
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_client):
        """测试成功生成。"""
        prompt = "测试提示词"
        params = GenerationParams(max_tokens=100, temperature=0.7)
        
        response = await mock_client.generate(prompt, params)
        
        assert isinstance(response, LLMResponse)
        assert response.provider == "mock"
        assert response.model == "mock-model"
        assert response.tokens_used == 100
        assert "Mock response" in response.text
    
    @pytest.mark.asyncio
    async def test_generate_with_default_params(self, mock_client):
        """测试使用默认参数生成。"""
        prompt = "测试提示词"
        
        response = await mock_client.generate(prompt)
        
        assert isinstance(response, LLMResponse)
        assert response.text is not None
    
    @pytest.mark.asyncio
    async def test_unsupported_model(self, mock_client):
        """测试不支持的模型。"""
        mock_client.model_name = "unsupported-model"
        
        with pytest.raises(LLMError):
            await mock_client.generate("test prompt")
    
    def test_statistics(self, mock_client):
        """测试统计信息。"""
        stats = mock_client.get_statistics()
        
        assert "provider" in stats
        assert "model" in stats
        assert "total_requests" in stats
        assert "total_tokens" in stats
        assert "total_errors" in stats
        assert "error_rate" in stats
        
        assert stats["provider"] == "mock"
        assert stats["model"] == "mock-model"
        assert stats["total_requests"] == 0
    
    def test_reset_statistics(self, mock_client):
        """测试重置统计信息。"""
        # 设置一些统计数据
        mock_client._total_requests = 10
        mock_client._total_tokens = 1000
        mock_client._total_errors = 2
        
        mock_client.reset_statistics()
        
        stats = mock_client.get_statistics()
        assert stats["total_requests"] == 0
        assert stats["total_tokens"] == 0
        assert stats["total_errors"] == 0


class TestGenerationParams:
    """生成参数测试类。"""
    
    def test_default_params(self):
        """测试默认参数。"""
        params = GenerationParams()
        
        assert params.max_tokens == 2000
        assert params.temperature == 0.7
        assert params.top_p is None
        assert params.top_k is None
        assert params.stream is False
    
    def test_custom_params(self):
        """测试自定义参数。"""
        params = GenerationParams(
            max_tokens=1500,
            temperature=0.5,
            top_p=0.9,
            top_k=50,
            stream=True
        )
        
        assert params.max_tokens == 1500
        assert params.temperature == 0.5
        assert params.top_p == 0.9
        assert params.top_k == 50
        assert params.stream is True


class TestLLMResponse:
    """LLM响应测试类。"""
    
    def test_response_creation(self):
        """测试响应创建。"""
        response = LLMResponse(
            text="测试响应",
            provider="test",
            model="test-model",
            tokens_used=50,
            finish_reason="stop"
        )
        
        assert response.text == "测试响应"
        assert response.provider == "test"
        assert response.model == "test-model"
        assert response.tokens_used == 50
        assert response.finish_reason == "stop"
        assert response.timestamp is not None
    
    def test_response_with_metadata(self):
        """测试带元数据的响应。"""
        metadata = {"custom_field": "custom_value"}
        
        response = LLMResponse(
            text="测试响应",
            provider="test",
            model="test-model",
            metadata=metadata
        )
        
        assert response.metadata == metadata


class TestLLMErrors:
    """LLM错误测试类。"""
    
    def test_base_llm_error(self):
        """测试基础LLM错误。"""
        error = LLMError(
            message="测试错误",
            provider="test",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert str(error) == "测试错误"
        assert error.provider == "test"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
    
    def test_rate_limit_error(self):
        """测试速率限制错误。"""
        error = RateLimitError(
            message="速率限制",
            provider="test"
        )
        
        assert isinstance(error, LLMError)
        assert "速率限制" in str(error)
    
    def test_authentication_error(self):
        """测试认证错误。"""
        error = AuthenticationError(
            message="认证失败",
            provider="test"
        )
        
        assert isinstance(error, LLMError)
        assert "认证失败" in str(error)


class TestLLMFactory:
    """LLM工厂测试类。"""
    
    def test_create_baidu_client(self):
        """测试创建百度客户端。"""
        config = LLMConfig(
            provider="baidu",
            api_key="test_key",
            secret_key="test_secret",
            model_name="ERNIE-Bot-turbo"
        )
        
        with patch('dramacraft.llm.factory.BaiduQianfanClient') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            client = create_llm_client(config)
            
            mock_class.assert_called_once_with(
                api_key="test_key",
                secret_key="test_secret",
                model_name="ERNIE-Bot-turbo",
                timeout=30
            )
            assert client == mock_instance
    
    def test_create_alibaba_client(self):
        """测试创建阿里巴巴客户端。"""
        config = LLMConfig(
            provider="alibaba",
            api_key="test_key",
            model_name="qwen-turbo"
        )
        
        with patch('dramacraft.llm.factory.AlibabaTongyiClient') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            client = create_llm_client(config)
            
            mock_class.assert_called_once_with(
                api_key="test_key",
                model_name="qwen-turbo",
                timeout=30
            )
            assert client == mock_instance
    
    def test_create_unsupported_provider(self):
        """测试创建不支持的提供商。"""
        config = LLMConfig(
            provider="unsupported",
            api_key="test_key"
        )
        
        with pytest.raises(LLMError) as exc_info:
            create_llm_client(config)
        
        assert "Unsupported LLM provider" in str(exc_info.value)
    
    def test_baidu_missing_secret_key(self):
        """测试百度客户端缺少密钥。"""
        config = LLMConfig(
            provider="baidu",
            api_key="test_key"
            # 缺少 secret_key
        )
        
        with pytest.raises(LLMError) as exc_info:
            create_llm_client(config)
        
        assert "requires both api_key and secret_key" in str(exc_info.value)


class TestRetryLogic:
    """重试逻辑测试类。"""
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """测试失败时重试。"""
        client = MockLLMClient(
            api_key="test_key",
            model_name="mock-model",
            max_retries=2,
            retry_delay=0.1
        )
        
        # 模拟前两次失败，第三次成功
        call_count = 0
        original_make_request = client._make_request
        
        async def failing_request(prompt, params):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("模拟失败")
            return await original_make_request(prompt, params)
        
        client._make_request = failing_request
        
        response = await client.generate("test prompt")
        
        assert call_count == 3
        assert isinstance(response, LLMResponse)
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """测试超过最大重试次数。"""
        client = MockLLMClient(
            api_key="test_key",
            model_name="mock-model",
            max_retries=1,
            retry_delay=0.1
        )
        
        # 模拟总是失败
        async def always_failing_request(prompt, params):
            raise Exception("总是失败")
        
        client._make_request = always_failing_request
        
        with pytest.raises(LLMError):
            await client.generate("test prompt")


if __name__ == "__main__":
    pytest.main([__file__])
