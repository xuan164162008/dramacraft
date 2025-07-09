"""
DramaCraft配置模块测试。
"""

import pytest
from pathlib import Path
import tempfile
import json

from dramacraft.config import (
    DramaCraftConfig,
    LLMConfig,
    VideoConfig,
    JianYingConfig,
    LoggingConfig
)


class TestLLMConfig:
    """LLM配置测试类。"""
    
    def test_default_config(self):
        """测试默认配置。"""
        config = LLMConfig(api_key="test_key")
        
        assert config.provider == "baidu"
        assert config.api_key == "test_key"
        assert config.model_name == "ERNIE-Bot-turbo"
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
        assert config.timeout == 30
    
    def test_custom_config(self):
        """测试自定义配置。"""
        config = LLMConfig(
            provider="alibaba",
            api_key="test_key",
            model_name="qwen-turbo",
            max_tokens=1500,
            temperature=0.5
        )
        
        assert config.provider == "alibaba"
        assert config.model_name == "qwen-turbo"
        assert config.max_tokens == 1500
        assert config.temperature == 0.5
    
    def test_validation(self):
        """测试配置验证。"""
        # 测试无效的温度值
        with pytest.raises(ValueError):
            LLMConfig(api_key="test", temperature=3.0)
        
        # 测试无效的max_tokens
        with pytest.raises(ValueError):
            LLMConfig(api_key="test", max_tokens=0)


class TestVideoConfig:
    """视频配置测试类。"""
    
    def test_default_config(self):
        """测试默认配置。"""
        config = VideoConfig()
        
        assert config.output_dir == Path("./output")
        assert config.temp_dir == Path("./temp")
        assert config.max_video_duration == 600
        assert config.video_quality == "medium"
        assert config.subtitle_font_size == 24
        assert config.subtitle_font_color == "white"
    
    def test_custom_paths(self):
        """测试自定义路径。"""
        config = VideoConfig(
            output_dir=Path("/custom/output"),
            temp_dir=Path("/custom/temp")
        )
        
        assert config.output_dir == Path("/custom/output")
        assert config.temp_dir == Path("/custom/temp")


class TestJianYingConfig:
    """剪映配置测试类。"""
    
    def test_default_config(self):
        """测试默认配置。"""
        config = JianYingConfig()
        
        assert config.installation_path is None
        assert config.project_template_dir == Path("./templates")
        assert config.automation_delay == 1.0
        assert config.screenshot_on_error is True
    
    def test_custom_config(self):
        """测试自定义配置。"""
        config = JianYingConfig(
            installation_path=Path("/Applications/JianYing.app"),
            automation_delay=0.5,
            screenshot_on_error=False
        )
        
        assert config.installation_path == Path("/Applications/JianYing.app")
        assert config.automation_delay == 0.5
        assert config.screenshot_on_error is False


class TestLoggingConfig:
    """日志配置测试类。"""
    
    def test_default_config(self):
        """测试默认配置。"""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.file_path is None
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5
    
    def test_custom_config(self):
        """测试自定义配置。"""
        config = LoggingConfig(
            level="DEBUG",
            file_path=Path("./logs/test.log"),
            max_file_size=5 * 1024 * 1024,
            backup_count=3
        )
        
        assert config.level == "DEBUG"
        assert config.file_path == Path("./logs/test.log")
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.backup_count == 3


class TestDramaCraftConfig:
    """DramaCraft主配置测试类。"""
    
    def test_default_config(self):
        """测试默认配置。"""
        # 需要提供必需的API密钥
        import os
        os.environ["LLM__API_KEY"] = "test_key"
        
        try:
            config = DramaCraftConfig()
            
            assert config.service_name == "dramacraft"
            assert config.service_version == "0.1.0"
            assert config.host == "localhost"
            assert config.port == 8000
            assert config.debug is False
            assert config.max_concurrent_requests == 10
            
            # 检查子配置
            assert isinstance(config.llm, LLMConfig)
            assert isinstance(config.video, VideoConfig)
            assert isinstance(config.jianying, JianYingConfig)
            assert isinstance(config.logging, LoggingConfig)
            
        finally:
            del os.environ["LLM__API_KEY"]
    
    def test_create_directories(self):
        """测试目录创建。"""
        import os
        os.environ["LLM__API_KEY"] = "test_key"
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                config = DramaCraftConfig()
                config.video.output_dir = temp_path / "output"
                config.video.temp_dir = temp_path / "temp"
                config.jianying.project_template_dir = temp_path / "templates"
                
                config.create_directories()
                
                assert config.video.output_dir.exists()
                assert config.video.temp_dir.exists()
                assert config.jianying.project_template_dir.exists()
                
        finally:
            del os.environ["LLM__API_KEY"]
    
    def test_from_file_json(self):
        """测试从JSON文件加载配置。"""
        config_data = {
            "service_name": "test_service",
            "llm": {
                "provider": "alibaba",
                "api_key": "test_key",
                "model_name": "qwen-turbo"
            },
            "video": {
                "output_dir": "./test_output",
                "video_quality": "high"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)
        
        try:
            config = DramaCraftConfig.from_file(config_file)
            
            assert config.service_name == "test_service"
            assert config.llm.provider == "alibaba"
            assert config.llm.model_name == "qwen-turbo"
            assert config.video.output_dir == Path("./test_output")
            assert config.video.video_quality == "high"
            
        finally:
            config_file.unlink()
    
    def test_to_dict(self):
        """测试配置转换为字典。"""
        import os
        os.environ["LLM__API_KEY"] = "test_key"
        
        try:
            config = DramaCraftConfig()
            config_dict = config.to_dict()
            
            assert isinstance(config_dict, dict)
            assert "service_name" in config_dict
            assert "llm" in config_dict
            assert "video" in config_dict
            assert "jianying" in config_dict
            assert "logging" in config_dict
            
        finally:
            del os.environ["LLM__API_KEY"]


class TestConfigValidation:
    """配置验证测试类。"""
    
    def test_invalid_provider(self):
        """测试无效的LLM提供商。"""
        with pytest.raises(ValueError):
            LLMConfig(provider="invalid", api_key="test")
    
    def test_invalid_video_quality(self):
        """测试无效的视频质量。"""
        with pytest.raises(ValueError):
            VideoConfig(video_quality="invalid")
    
    def test_invalid_logging_level(self):
        """测试无效的日志级别。"""
        with pytest.raises(ValueError):
            LoggingConfig(level="INVALID")
    
    def test_invalid_port(self):
        """测试无效的端口号。"""
        import os
        os.environ["LLM__API_KEY"] = "test_key"
        
        try:
            with pytest.raises(ValueError):
                DramaCraftConfig(port=99999)  # 超出有效范围
                
        finally:
            del os.environ["LLM__API_KEY"]


if __name__ == "__main__":
    pytest.main([__file__])
