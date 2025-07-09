# 🤖 大模型集成模块

大模型集成模块提供对国产中文大模型的统一接口，支持百度千帆、阿里通义、腾讯混元等主流平台。

## 🎯 模块概述

### 支持的大模型平台

- **🌟 百度千帆**: 完整的 API 集成和优化
- **⚡ 阿里通义**: 原生 SDK 支持
- **🚀 腾讯混元**: 专业级接口适配
- **🎯 智能切换**: 根据任务类型自动选择最优模型

### 核心特性

- **统一接口**: 所有平台使用相同的API接口
- **异步支持**: 基于 asyncio 的高性能异步调用
- **错误恢复**: 完善的重试机制和错误处理
- **性能监控**: 实时监控API调用性能和成功率
- **智能路由**: 根据任务类型和负载自动选择模型

### 主要组件

- `BaseLLMClient`: 基础LLM客户端抽象类
- `BaiduLLMClient`: 百度千帆客户端
- `AlibabaLLMClient`: 阿里通义客户端
- `TencentLLMClient`: 腾讯混元客户端
- `LLMFactory`: LLM客户端工厂

## 🔧 API 参考

### BaseLLMClient

```python
from dramacraft.llm.base import BaseLLMClient, GenerationResult, GenerationParams

class BaseLLMClient:
    """LLM客户端基类。"""
    
    async def generate(
        self, 
        prompt: str, 
        params: Optional[GenerationParams] = None
    ) -> GenerationResult:
        """
        生成文本内容。
        
        Args:
            prompt: 输入提示词
            params: 生成参数
            
        Returns:
            生成结果
        """
```

### GenerationParams

```python
@dataclass
class GenerationParams:
    """生成参数。"""
    
    temperature: float = 0.7
    """温度参数，控制随机性。"""
    
    max_tokens: int = 2000
    """最大生成令牌数。"""
    
    top_p: float = 0.9
    """Top-p采样参数。"""
    
    frequency_penalty: float = 0.0
    """频率惩罚。"""
    
    presence_penalty: float = 0.0
    """存在惩罚。"""
    
    stop_sequences: Optional[List[str]] = None
    """停止序列。"""
```

### GenerationResult

```python
@dataclass
class GenerationResult:
    """生成结果。"""
    
    text: str
    """生成的文本内容。"""
    
    usage: Dict[str, int]
    """令牌使用统计。"""
    
    model: Optional[str] = None
    """使用的模型名称。"""
    
    finish_reason: Optional[str] = None
    """完成原因。"""
    
    response_time: Optional[float] = None
    """响应时间(秒)。"""
```

### LLM工厂

```python
from dramacraft.llm.factory import create_llm_client
from dramacraft.config import LLMConfig

def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    """
    创建LLM客户端。
    
    Args:
        config: LLM配置
        
    Returns:
        LLM客户端实例
    """
```

## 💡 使用示例

### 基础使用

```python
import asyncio
from dramacraft.llm.factory import create_llm_client
from dramacraft.config import DramaCraftConfig

async def basic_llm_example():
    """基础LLM使用示例。"""
    
    # 加载配置
    config = DramaCraftConfig()
    
    # 创建LLM客户端
    llm_client = create_llm_client(config.llm)
    
    # 生成文本
    prompt = "请为这个短剧场景生成搞笑的解说文案：两个人在咖啡厅里尴尬地相视而坐。"
    result = await llm_client.generate(prompt)
    
    print(f"生成内容: {result.text}")
    print(f"令牌使用: {result.usage}")
    print(f"响应时间: {result.response_time:.2f}秒")

asyncio.run(basic_llm_example())
```

### 自定义生成参数

```python
from dramacraft.llm.base import GenerationParams

async def custom_params_example():
    """自定义参数示例。"""
    
    config = DramaCraftConfig()
    llm_client = create_llm_client(config.llm)
    
    # 自定义生成参数
    params = GenerationParams(
        temperature=0.8,        # 提高创造性
        max_tokens=1000,        # 限制长度
        top_p=0.95,            # 调整采样
        stop_sequences=["。", "！", "？"]  # 停止条件
    )
    
    prompt = "创作一个搞笑的短剧开场白"
    result = await llm_client.generate(prompt, params)
    
    print(f"创作内容: {result.text}")

asyncio.run(custom_params_example())
```

### 批量生成

```python
async def batch_generation_example():
    """批量生成示例。"""
    
    config = DramaCraftConfig()
    llm_client = create_llm_client(config.llm)
    
    # 批量提示词
    prompts = [
        "为搞笑短剧生成开场白",
        "为悬疑短剧生成开场白", 
        "为爱情短剧生成开场白"
    ]
    
    # 并发生成
    tasks = [llm_client.generate(prompt) for prompt in prompts]
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results):
        print(f"提示词 {i+1}: {result.text[:50]}...")

asyncio.run(batch_generation_example())
```

### 错误处理

```python
from dramacraft.llm.exceptions import LLMError, RateLimitError, AuthenticationError

async def error_handling_example():
    """错误处理示例。"""
    
    config = DramaCraftConfig()
    llm_client = create_llm_client(config.llm)
    
    try:
        result = await llm_client.generate("生成内容")
        print(f"成功: {result.text}")
        
    except AuthenticationError:
        print("认证失败，请检查API密钥")
        
    except RateLimitError:
        print("请求频率过高，请稍后重试")
        
    except LLMError as e:
        print(f"LLM调用失败: {e}")
        
    except Exception as e:
        print(f"未知错误: {e}")

asyncio.run(error_handling_example())
```

## ⚙️ 配置说明

### 百度千帆配置

```python
llm_config = {
    "provider": "baidu",
    "api_key": "your_api_key",
    "secret_key": "your_secret_key",
    "model": "ernie-bot-turbo",
    "endpoint": "https://aip.baidubce.com",
    "timeout": 30.0,
    "max_retries": 3,
    "retry_delay": 1.0
}
```

### 阿里通义配置

```python
llm_config = {
    "provider": "alibaba", 
    "api_key": "your_api_key",
    "model": "qwen-turbo",
    "region": "cn-beijing",
    "timeout": 30.0,
    "max_retries": 3
}
```

### 腾讯混元配置

```python
llm_config = {
    "provider": "tencent",
    "secret_id": "your_secret_id", 
    "secret_key": "your_secret_key",
    "model": "hunyuan-lite",
    "region": "ap-beijing",
    "timeout": 30.0,
    "max_retries": 3
}
```

### 通用配置选项

```python
llm_config = {
    # 基础配置
    "provider": "baidu",           # 提供商: baidu/alibaba/tencent
    "model": "ernie-bot-turbo",    # 模型名称
    
    # 认证配置
    "api_key": "your_api_key",     # API密钥
    "secret_key": "your_secret",   # 密钥(百度需要)
    
    # 生成参数
    "temperature": 0.7,            # 默认温度
    "max_tokens": 2000,            # 默认最大令牌
    "top_p": 0.9,                  # 默认top_p
    
    # 性能配置
    "timeout": 30.0,               # 请求超时(秒)
    "max_retries": 3,              # 最大重试次数
    "retry_delay": 1.0,            # 重试延迟(秒)
    "rate_limit": 10,              # 每秒请求限制
    
    # 缓存配置
    "cache_enabled": True,         # 是否启用缓存
    "cache_ttl": 3600,            # 缓存过期时间(秒)
    
    # 监控配置
    "monitoring_enabled": True,    # 是否启用监控
    "log_requests": False         # 是否记录请求日志
}
```

## 🔍 故障排除

### 常见问题

**Q: API调用失败，返回认证错误？**
A: 检查以下配置：
- 确认API密钥正确且有效
- 检查密钥是否有相应权限
- 验证账户余额是否充足
- 确认网络连接正常

**Q: 请求超时怎么办？**
A: 尝试以下解决方案：
- 增加 `timeout` 设置
- 检查网络连接稳定性
- 减少 `max_tokens` 降低处理时间
- 启用重试机制

**Q: 生成质量不理想？**
A: 调整以下参数：
- 优化提示词的描述和格式
- 调整 `temperature` 控制创造性
- 修改 `top_p` 影响多样性
- 尝试不同的模型

**Q: 请求频率限制？**
A: 处理方法：
- 设置合理的 `rate_limit`
- 使用指数退避重试
- 考虑升级API套餐
- 实现请求队列管理

### 性能优化

1. **缓存策略**: 启用缓存避免重复请求
2. **并发控制**: 合理设置并发数量
3. **参数调优**: 根据任务调整生成参数
4. **错误恢复**: 实现智能重试机制
5. **监控告警**: 设置性能监控和告警

### 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger("dramacraft.llm").setLevel(logging.DEBUG)

# 监控API调用
from dramacraft.monitoring.performance import get_performance_monitor
monitor = get_performance_monitor()
metrics = monitor.get_llm_metrics()

# 测试连接
async def test_connection():
    try:
        result = await llm_client.generate("测试")
        print("连接正常")
    except Exception as e:
        print(f"连接失败: {e}")
```

## 📚 相关文档

- [配置管理](../../config.py)
- [性能监控模块](../monitoring/docs/README.md)
- [错误处理指南](../../../docs/troubleshooting.md)
- [API使用示例](../../../examples/llm_examples.py)
