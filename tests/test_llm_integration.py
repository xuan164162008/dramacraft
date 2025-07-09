"""
LLM集成测试模块。

测试各种大模型API的集成功能，包括百度千帆、阿里通义等。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.dramacraft.llm.base import BaseLLMClient, GenerationResult, GenerationParams
from src.dramacraft.llm.baidu import BaiduLLMClient
from src.dramacraft.llm.alibaba import AlibabaLLMClient
from src.dramacraft.llm.factory import create_llm_client
from src.dramacraft.config import LLMConfig


class TestBaseLLMClient:
    """基础LLM客户端测试。"""
    
    def test_base_client_abstract(self):
        """测试基础客户端是抽象类。"""
        with pytest.raises(TypeError):
            BaseLLMClient()
    
    def test_generation_result_creation(self):
        """测试生成结果创建。"""
        result = GenerationResult(
            text="测试文本",
            usage={"prompt_tokens": 10, "completion_tokens": 20}
        )
        
        assert result.text == "测试文本"
        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 20
    
    def test_generation_params_creation(self):
        """测试生成参数创建。"""
        params = GenerationParams(
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9
        )
        
        assert params.temperature == 0.7
        assert params.max_tokens == 1000
        assert params.top_p == 0.9


class TestBaiduLLMClient:
    """百度LLM客户端测试。"""
    
    @pytest.fixture
    def baidu_config(self):
        """百度配置。"""
        return LLMConfig(
            provider="baidu",
            api_key="test_api_key",
            secret_key="test_secret_key",
            model="ernie-bot-turbo"
        )
    
    @pytest.fixture
    def baidu_client(self, baidu_config):
        """百度客户端。"""
        return BaiduLLMClient(baidu_config)
    
    def test_client_initialization(self, baidu_client):
        """测试客户端初始化。"""
        assert baidu_client.api_key == "test_api_key"
        assert baidu_client.secret_key == "test_secret_key"
        assert baidu_client.model == "ernie-bot-turbo"
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self, baidu_client):
        """测试获取访问令牌成功。"""
        mock_response = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.status_code = 200
            
            token = await baidu_client._get_access_token()
            assert token == "test_token"
    
    @pytest.mark.asyncio
    async def test_get_access_token_failure(self, baidu_client):
        """测试获取访问令牌失败。"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.text = "Invalid credentials"
            
            with pytest.raises(Exception):
                await baidu_client._get_access_token()
    
    @pytest.mark.asyncio
    async def test_generate_success(self, baidu_client):
        """测试生成成功。"""
        mock_token_response = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        
        mock_generate_response = {
            "result": "这是生成的文本",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            # 模拟获取token和生成请求
            mock_post.side_effect = [
                Mock(json=lambda: mock_token_response, status_code=200),
                Mock(json=lambda: mock_generate_response, status_code=200)
            ]
            
            result = await baidu_client.generate("测试提示词")
            
            assert result.text == "这是生成的文本"
            assert result.usage["prompt_tokens"] == 10
            assert result.usage["completion_tokens"] == 20
    
    @pytest.mark.asyncio
    async def test_generate_with_params(self, baidu_client):
        """测试带参数生成。"""
        params = GenerationParams(temperature=0.8, max_tokens=500)
        
        with patch.object(baidu_client, '_get_access_token', return_value="test_token"):
            with patch('httpx.AsyncClient.post') as mock_post:
                mock_post.return_value.json.return_value = {
                    "result": "生成文本",
                    "usage": {"prompt_tokens": 5, "completion_tokens": 10}
                }
                mock_post.return_value.status_code = 200
                
                result = await baidu_client.generate("测试", params)
                
                # 验证请求参数
                call_args = mock_post.call_args
                request_data = call_args[1]['json']
                assert request_data['temperature'] == 0.8
                assert request_data['max_output_tokens'] == 500


class TestAlibabaLLMClient:
    """阿里巴巴LLM客户端测试。"""
    
    @pytest.fixture
    def alibaba_config(self):
        """阿里巴巴配置。"""
        return LLMConfig(
            provider="alibaba",
            api_key="test_api_key",
            model="qwen-turbo"
        )
    
    @pytest.fixture
    def alibaba_client(self, alibaba_config):
        """阿里巴巴客户端。"""
        return AlibabaLLMClient(alibaba_config)
    
    def test_client_initialization(self, alibaba_client):
        """测试客户端初始化。"""
        assert alibaba_client.api_key == "test_api_key"
        assert alibaba_client.model == "qwen-turbo"
    
    @pytest.mark.asyncio
    async def test_generate_success(self, alibaba_client):
        """测试生成成功。"""
        mock_response = {
            "output": {
                "text": "这是阿里生成的文本"
            },
            "usage": {
                "input_tokens": 15,
                "output_tokens": 25
            }
        }
        
        with patch('dashscope.Generation.acall') as mock_call:
            mock_call.return_value.output = mock_response["output"]
            mock_call.return_value.usage = mock_response["usage"]
            mock_call.return_value.status_code = 200
            
            result = await alibaba_client.generate("测试提示词")
            
            assert result.text == "这是阿里生成的文本"
            assert result.usage["prompt_tokens"] == 15
            assert result.usage["completion_tokens"] == 25
    
    @pytest.mark.asyncio
    async def test_generate_failure(self, alibaba_client):
        """测试生成失败。"""
        with patch('dashscope.Generation.acall') as mock_call:
            mock_call.return_value.status_code = 400
            mock_call.return_value.message = "API调用失败"
            
            with pytest.raises(Exception):
                await alibaba_client.generate("测试提示词")


class TestLLMFactory:
    """LLM工厂测试。"""
    
    def test_create_baidu_client(self):
        """测试创建百度客户端。"""
        config = LLMConfig(
            provider="baidu",
            api_key="test_key",
            secret_key="test_secret"
        )
        
        client = create_llm_client(config)
        assert isinstance(client, BaiduLLMClient)
    
    def test_create_alibaba_client(self):
        """测试创建阿里巴巴客户端。"""
        config = LLMConfig(
            provider="alibaba",
            api_key="test_key"
        )
        
        client = create_llm_client(config)
        assert isinstance(client, AlibabaLLMClient)
    
    def test_create_unsupported_client(self):
        """测试创建不支持的客户端。"""
        config = LLMConfig(
            provider="unsupported",
            api_key="test_key"
        )
        
        with pytest.raises(ValueError, match="不支持的LLM提供商"):
            create_llm_client(config)


class TestLLMIntegration:
    """LLM集成测试。"""
    
    @pytest.mark.asyncio
    async def test_multiple_clients_concurrent(self):
        """测试多个客户端并发调用。"""
        baidu_config = LLMConfig(
            provider="baidu",
            api_key="baidu_key",
            secret_key="baidu_secret"
        )
        
        alibaba_config = LLMConfig(
            provider="alibaba",
            api_key="alibaba_key"
        )
        
        baidu_client = BaiduLLMClient(baidu_config)
        alibaba_client = AlibabaLLMClient(alibaba_config)
        
        # 模拟并发调用
        with patch.object(baidu_client, 'generate') as mock_baidu:
            with patch.object(alibaba_client, 'generate') as mock_alibaba:
                mock_baidu.return_value = GenerationResult("百度结果", {})
                mock_alibaba.return_value = GenerationResult("阿里结果", {})
                
                # 并发执行
                results = await asyncio.gather(
                    baidu_client.generate("测试1"),
                    alibaba_client.generate("测试2")
                )
                
                assert len(results) == 2
                assert results[0].text == "百度结果"
                assert results[1].text == "阿里结果"
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """测试重试机制。"""
        config = LLMConfig(
            provider="baidu",
            api_key="test_key",
            secret_key="test_secret",
            max_retries=3
        )
        
        client = BaiduLLMClient(config)
        
        # 模拟前两次失败，第三次成功
        call_count = 0
        
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("临时错误")
            return GenerationResult("成功结果", {})
        
        with patch.object(client, '_make_request', side_effect=mock_generate):
            result = await client.generate("测试")
            assert result.text == "成功结果"
            assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """测试速率限制。"""
        config = LLMConfig(
            provider="baidu",
            api_key="test_key",
            secret_key="test_secret",
            rate_limit=2  # 每秒2次请求
        )
        
        client = BaiduLLMClient(config)
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = GenerationResult("结果", {})
            
            # 快速发送多个请求
            start_time = asyncio.get_event_loop().time()
            
            tasks = [client.generate(f"测试{i}") for i in range(5)]
            await asyncio.gather(*tasks)
            
            end_time = asyncio.get_event_loop().time()
            
            # 验证总时间符合速率限制
            assert end_time - start_time >= 2.0  # 至少需要2秒


class TestErrorHandling:
    """错误处理测试。"""
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """测试网络错误处理。"""
        config = LLMConfig(
            provider="baidu",
            api_key="test_key",
            secret_key="test_secret"
        )
        
        client = BaiduLLMClient(config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("网络连接失败")
            
            with pytest.raises(Exception, match="网络连接失败"):
                await client.generate("测试")
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """测试API错误处理。"""
        config = LLMConfig(
            provider="baidu",
            api_key="invalid_key",
            secret_key="invalid_secret"
        )
        
        client = BaiduLLMClient(config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value.status_code = 401
            mock_post.return_value.text = "Unauthorized"
            
            with pytest.raises(Exception):
                await client.generate("测试")
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理。"""
        config = LLMConfig(
            provider="baidu",
            api_key="test_key",
            secret_key="test_secret",
            timeout=1.0
        )
        
        client = BaiduLLMClient(config)
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError("请求超时")
            
            with pytest.raises(Exception):
                await client.generate("测试")
