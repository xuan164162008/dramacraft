"""
标准化JSON配置格式定义
确保AI编辑器中参数传递的一致性和可维护性
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class VideoStyle(str, Enum):
    """视频风格枚举"""
    HUMOROUS = "humorous"
    PROFESSIONAL = "professional"
    DRAMATIC = "dramatic"
    SUSPENSE = "suspense"
    ROMANTIC = "romantic"
    ACTION = "action"


class TargetAudience(str, Enum):
    """目标受众枚举"""
    YOUNG_ADULTS = "年轻人"
    TEENAGERS = "青少年"
    MIDDLE_AGED = "中年人"
    GENERAL = "大众"
    PROFESSIONALS = "专业人士"


class OutputQuality(str, Enum):
    """输出质量枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


# ==================== 主要工具配置 ====================

class SeriesCompilationConfig(BaseModel):
    """系列合集制作标准配置"""

    # 必需参数
    video_paths: list[str] = Field(..., description="视频文件路径列表")
    series_title: str = Field(..., description="系列标题")

    # 基础设置
    target_duration: float = Field(default=120.0, ge=30, le=600, description="目标时长(秒)")
    style: VideoStyle = Field(default=VideoStyle.HUMOROUS, description="视频风格")
    target_audience: TargetAudience = Field(default=TargetAudience.YOUNG_ADULTS, description="目标受众")

    # 质量控制
    quality_threshold: float = Field(default=0.6, ge=0, le=1, description="质量阈值(0-1)")
    excitement_threshold: float = Field(default=0.7, ge=0, le=1, description="精彩程度阈值(0-1)")
    output_quality: OutputQuality = Field(default=OutputQuality.HIGH, description="输出质量")

    # 功能开关
    create_jianying_project: bool = Field(default=True, description="创建剪映项目")
    generate_commentary: bool = Field(default=True, description="生成解说文案")
    include_transitions: bool = Field(default=True, description="包含转场效果")
    include_background_music: bool = Field(default=True, description="包含背景音乐")

    # 高级设置
    parallel_analysis: bool = Field(default=True, description="并行分析")
    max_concurrent: int = Field(default=3, ge=1, le=8, description="最大并发数")
    output_dir: str = Field(default="./output", description="输出目录")

    # 自定义设置
    custom_settings: Optional[dict[str, Any]] = Field(default=None, description="自定义设置")

    class Config:
        """Pydantic配置"""
        use_enum_values = True
        json_encoders = {
            VideoStyle: lambda v: v.value,
            TargetAudience: lambda v: v.value,
            OutputQuality: lambda v: v.value
        }


class CommentaryGenerationConfig(BaseModel):
    """解说生成标准配置"""

    # 必需参数
    video_path: str = Field(..., description="视频文件路径")

    # 基础设置
    style: VideoStyle = Field(default=VideoStyle.HUMOROUS, description="解说风格")
    target_audience: TargetAudience = Field(default=TargetAudience.YOUNG_ADULTS, description="目标受众")

    # 解说选项
    include_intro: bool = Field(default=True, description="包含开场")
    include_interaction: bool = Field(default=True, description="包含互动元素")
    include_outro: bool = Field(default=True, description="包含结尾")
    commentary_length: Optional[str] = Field(default="auto", description="解说长度: auto/short/medium/long")

    # 高级设置
    emotion_emphasis: float = Field(default=0.7, ge=0, le=1, description="情感强调程度")
    humor_level: float = Field(default=0.8, ge=0, le=1, description="幽默程度")
    interaction_frequency: float = Field(default=0.6, ge=0, le=1, description="互动频率")

    # 输出设置
    output_format: str = Field(default="text", description="输出格式: text/srt/vtt")
    output_dir: str = Field(default="./output", description="输出目录")

    class Config:
        use_enum_values = True


class VideoAnalysisConfig(BaseModel):
    """视频分析标准配置"""

    # 必需参数
    video_path: str = Field(..., description="视频文件路径")

    # 分析深度
    analysis_depth: str = Field(default="comprehensive", description="分析深度: basic/detailed/comprehensive")

    # 分析选项
    include_scenes: bool = Field(default=True, description="包含场景分析")
    include_emotions: bool = Field(default=True, description="包含情绪分析")
    include_characters: bool = Field(default=True, description="包含角色分析")
    include_dialogue: bool = Field(default=True, description="包含对话分析")
    include_visual_elements: bool = Field(default=True, description="包含视觉元素分析")
    include_highlights: bool = Field(default=True, description="包含精彩片段识别")

    # 高级设置
    frame_sampling_rate: float = Field(default=1.0, ge=0.1, le=5.0, description="帧采样率(秒)")
    quality_threshold: float = Field(default=0.5, ge=0, le=1, description="质量阈值")

    # 输出设置
    output_format: str = Field(default="json", description="输出格式: json/yaml/xml")
    output_dir: str = Field(default="./output", description="输出目录")


class JianYingProjectConfig(BaseModel):
    """剪映项目创建标准配置"""

    # 必需参数
    video_path: str = Field(..., description="视频文件路径")
    project_name: str = Field(..., description="项目名称")

    # 项目设置
    resolution: str = Field(default="1920x1080", description="分辨率")
    frame_rate: float = Field(default=30.0, description="帧率")

    # 内容设置
    commentary_text: Optional[str] = Field(default=None, description="解说文案")
    include_subtitles: bool = Field(default=True, description="包含字幕")
    include_background_music: bool = Field(default=False, description="包含背景音乐")
    include_transitions: bool = Field(default=True, description="包含转场")

    # 高级设置
    auto_import: bool = Field(default=True, description="自动导入剪映")
    backup_original: bool = Field(default=True, description="备份原始项目")

    # 输出设置
    output_dir: str = Field(default="./output", description="输出目录")


# ==================== 配置工厂 ====================

class ConfigFactory:
    """配置工厂类 - 生成标准JSON配置"""

    @staticmethod
    def create_series_compilation_config(**kwargs) -> dict[str, Any]:
        """创建系列合集制作配置"""
        config = SeriesCompilationConfig(**kwargs)
        return config.dict(exclude_none=True)

    @staticmethod
    def create_commentary_config(**kwargs) -> dict[str, Any]:
        """创建解说生成配置"""
        config = CommentaryGenerationConfig(**kwargs)
        return config.dict(exclude_none=True)

    @staticmethod
    def create_analysis_config(**kwargs) -> dict[str, Any]:
        """创建视频分析配置"""
        config = VideoAnalysisConfig(**kwargs)
        return config.dict(exclude_none=True)

    @staticmethod
    def create_jianying_config(**kwargs) -> dict[str, Any]:
        """创建剪映项目配置"""
        config = JianYingProjectConfig(**kwargs)
        return config.dict(exclude_none=True)

    @staticmethod
    def get_config_template(tool_name: str) -> dict[str, Any]:
        """获取配置模板"""
        templates = {
            "create_series_compilation": {
                "video_paths": ["第1集.mp4", "第2集.mp4", "第3集.mp4"],
                "series_title": "搞笑短剧精彩合集",
                "target_duration": 120,
                "style": "humorous",
                "target_audience": "年轻人",
                "quality_threshold": 0.6,
                "excitement_threshold": 0.7,
                "create_jianying_project": True,
                "generate_commentary": True
            },
            "generate_commentary": {
                "video_path": "视频文件.mp4",
                "style": "humorous",
                "target_audience": "年轻人",
                "include_intro": True,
                "include_interaction": True,
                "include_outro": True
            },
            "analyze_video": {
                "video_path": "视频文件.mp4",
                "analysis_depth": "comprehensive",
                "include_scenes": True,
                "include_emotions": True,
                "include_characters": True,
                "include_highlights": True
            },
            "create_jianying_draft": {
                "video_path": "视频文件.mp4",
                "project_name": "我的项目",
                "commentary_text": "解说文案内容",
                "include_subtitles": True,
                "auto_import": True
            }
        }
        return templates.get(tool_name, {})

    @staticmethod
    def validate_config(tool_name: str, config: dict[str, Any]) -> bool:
        """验证配置格式"""
        try:
            if tool_name == "create_series_compilation":
                SeriesCompilationConfig(**config)
            elif tool_name == "generate_commentary":
                CommentaryGenerationConfig(**config)
            elif tool_name == "analyze_video":
                VideoAnalysisConfig(**config)
            elif tool_name == "create_jianying_draft":
                JianYingProjectConfig(**config)
            else:
                return False
            return True
        except Exception:
            return False


# ==================== 导出 ====================

__all__ = [
    'VideoStyle',
    'TargetAudience',
    'OutputQuality',
    'SeriesCompilationConfig',
    'CommentaryGenerationConfig',
    'VideoAnalysisConfig',
    'JianYingProjectConfig',
    'ConfigFactory'
]
