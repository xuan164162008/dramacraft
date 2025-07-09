"""
DramaCraft 测试套件

提供企业级测试框架：
- 单元测试
- 集成测试
- 性能测试
- 安全测试
- 端到端测试
"""

import pytest
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Generator

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 测试配置
TEST_CONFIG = {
    "test_data_dir": Path(__file__).parent / "data",
    "temp_dir": Path(__file__).parent / "temp",
    "fixtures_dir": Path(__file__).parent / "fixtures",
    "mock_ai_responses": True,
    "test_timeout": 30,
    "performance_thresholds": {
        "api_response_time": 200,  # ms
        "video_analysis_time": 30,  # seconds
        "memory_usage_limit": 1024,  # MB
    }
}

# 创建测试目录
for directory in [TEST_CONFIG["temp_dir"], TEST_CONFIG["fixtures_dir"]]:
    directory.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """测试配置fixture"""
    return TEST_CONFIG


@pytest.fixture(scope="function")
def temp_dir(test_config: Dict[str, Any]) -> Path:
    """临时目录fixture"""
    return test_config["temp_dir"]


@pytest.fixture(scope="session")
def test_data_dir(test_config: Dict[str, Any]) -> Path:
    """测试数据目录fixture"""
    return test_config["test_data_dir"]
