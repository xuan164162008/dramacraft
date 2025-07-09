"""
DramaCraft服务配置管理模块。

本模块提供基于pydantic的配置管理，支持环境变量、配置文件和安全的API密钥处理。
"""

from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """大语言模型提供商配置。"""

    provider: Literal["baidu", "alibaba", "tencent"] = Field(
        default="baidu",
        description="要使用的大模型提供商"
    )
    api_key: str = Field(
        description="大模型提供商的API密钥"
    )
    secret_key: Optional[str] = Field(
        default=None,
        description="大模型提供商的密钥(如果需要)"
    )
    model_name: str = Field(
        default="ERNIE-Bot-turbo",
        description="要使用的模型名称"
    )
    max_tokens: int = Field(
        default=2000,
        ge=1,
        le=8000,
        description="生成的最大token数"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="文本生成的温度参数"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="请求超时时间(秒)"
    )


class VideoConfig(BaseModel):
    """视频处理配置。"""

    output_dir: Path = Field(
        default=Path("./output"),
        description="输出文件目录"
    )
    temp_dir: Path = Field(
        default=Path("./temp"),
        description="临时文件目录"
    )
    max_video_duration: int = Field(
        default=600,
        ge=1,
        le=3600,
        description="最大视频时长(秒)"
    )
    video_quality: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="视频处理质量"
    )
    subtitle_font_size: int = Field(
        default=24,
        ge=12,
        le=72,
        description="字幕字体大小"
    )
    subtitle_font_color: str = Field(
        default="white",
        description="字幕字体颜色"
    )


class JianYingConfig(BaseModel):
    """Configuration for JianYing integration."""

    installation_path: Optional[Path] = Field(
        default=None,
        description="Path to JianYing installation"
    )
    project_template_dir: Path = Field(
        default=Path("./templates"),
        description="Directory for JianYing project templates"
    )
    automation_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Delay between automation actions in seconds"
    )
    screenshot_on_error: bool = Field(
        default=True,
        description="Take screenshot on automation errors"
    )


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file_path: Optional[Path] = Field(
        default=None,
        description="Path to log file (if None, logs to console only)"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        ge=1024,
        description="Maximum log file size in bytes"
    )
    backup_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of backup log files to keep"
    )


class DramaCraftConfig(BaseSettings):
    """DramaCraft服务的主配置类。"""

    # 服务配置
    service_name: str = Field(
        default="dramacraft",
        description="MCP服务名称"
    )
    service_version: str = Field(
        default="0.1.0",
        description="MCP服务版本"
    )
    host: str = Field(
        default="localhost",
        description="Host to bind the service to"
    )
    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Port to bind the service to"
    )

    # Component configurations
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM provider configuration"
    )
    video: VideoConfig = Field(
        default_factory=VideoConfig,
        description="Video processing configuration"
    )
    jianying: JianYingConfig = Field(
        default_factory=JianYingConfig,
        description="JianYing integration configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )

    # Additional settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    max_concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent requests"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False

    @validator("llm", pre=True)
    def validate_llm_config(cls, v):
        """Validate LLM configuration."""
        if isinstance(v, dict):
            return LLMConfig(**v)
        return v

    @validator("video", pre=True)
    def validate_video_config(cls, v):
        """Validate video configuration."""
        if isinstance(v, dict):
            return VideoConfig(**v)
        return v

    @validator("jianying", pre=True)
    def validate_jianying_config(cls, v):
        """Validate JianYing configuration."""
        if isinstance(v, dict):
            return JianYingConfig(**v)
        return v

    @validator("logging", pre=True)
    def validate_logging_config(cls, v):
        """Validate logging configuration."""
        if isinstance(v, dict):
            return LoggingConfig(**v)
        return v

    def create_directories(self) -> None:
        """Create necessary directories."""
        self.video.output_dir.mkdir(parents=True, exist_ok=True)
        self.video.temp_dir.mkdir(parents=True, exist_ok=True)
        self.jianying.project_template_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()

    @classmethod
    def from_file(cls, config_path: Path) -> "DramaCraftConfig":
        """Load configuration from file."""
        if config_path.suffix.lower() == ".json":
            import json
            with open(config_path, encoding="utf-8") as f:
                config_data = json.load(f)
        elif config_path.suffix.lower() in [".yaml", ".yml"]:
            import yaml
            with open(config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported config file format: {config_path.suffix}")

        return cls(**config_data)
