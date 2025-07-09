"""
多集视频系列数据模型
重构后的核心数据结构，支持多集合并工作流
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class VideoQuality(str, Enum):
    """视频质量枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    EXTRACTING = "extracting"
    MERGING = "merging"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class HighlightSegment(BaseModel):
    """精彩片段模型"""

    episode_index: int = Field(..., description="所属集数索引")
    start_time: float = Field(..., description="开始时间(秒)")
    end_time: float = Field(..., description="结束时间(秒)")
    duration: float = Field(..., description="片段时长(秒)")
    quality_score: float = Field(..., ge=0, le=1, description="质量评分(0-1)")
    excitement_level: float = Field(..., ge=0, le=1, description="精彩程度(0-1)")
    content_type: str = Field(..., description="内容类型(搞笑/悬疑/动作等)")
    description: str = Field(..., description="片段描述")
    keywords: list[str] = Field(default_factory=list, description="关键词")

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('结束时间必须大于开始时间')
        return v


class EpisodeInfo(BaseModel):
    """单集信息模型"""

    index: int = Field(..., description="集数索引")
    title: str = Field(..., description="集数标题")
    file_path: Path = Field(..., description="视频文件路径")
    duration: float = Field(..., description="视频时长(秒)")
    resolution: str = Field(..., description="分辨率")
    fps: float = Field(..., description="帧率")
    file_size: int = Field(..., description="文件大小(字节)")
    format: str = Field(..., description="视频格式")

    # 分析结果
    analysis_completed: bool = Field(default=False, description="是否已完成分析")
    quality_score: float = Field(default=0.0, ge=0, le=1, description="整体质量评分")
    highlight_segments: list[HighlightSegment] = Field(default_factory=list, description="精彩片段列表")
    scene_count: int = Field(default=0, description="场景数量")
    character_count: int = Field(default=0, description="角色数量")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    analyzed_at: Optional[datetime] = None

    @validator('file_path')
    def validate_file_path(cls, v):
        if not v.exists():
            raise ValueError(f'视频文件不存在: {v}')
        return v


class SeriesMetadata(BaseModel):
    """系列元数据"""

    title: str = Field(..., description="系列标题")
    description: str = Field(default="", description="系列描述")
    genre: str = Field(default="", description="类型/风格")
    target_audience: str = Field(default="年轻人", description="目标受众")
    style_preferences: dict[str, Any] = Field(default_factory=dict, description="风格偏好")
    tags: list[str] = Field(default_factory=list, description="标签")


class CompilationSettings(BaseModel):
    """合集制作设置"""

    target_duration: float = Field(default=120.0, description="目标时长(秒)")
    max_duration: float = Field(default=180.0, description="最大时长(秒)")
    min_segment_duration: float = Field(default=3.0, description="最小片段时长(秒)")
    max_segment_duration: float = Field(default=15.0, description="最大片段时长(秒)")

    quality_threshold: float = Field(default=0.6, ge=0, le=1, description="质量阈值")
    excitement_threshold: float = Field(default=0.7, ge=0, le=1, description="精彩程度阈值")

    include_transitions: bool = Field(default=True, description="是否包含转场")
    include_background_music: bool = Field(default=True, description="是否包含背景音乐")
    include_commentary: bool = Field(default=True, description="是否包含解说")

    output_quality: VideoQuality = Field(default=VideoQuality.HIGH, description="输出质量")
    output_format: str = Field(default="mp4", description="输出格式")


class SeriesCompilationResult(BaseModel):
    """系列合集结果"""

    output_path: Path = Field(..., description="输出文件路径")
    duration: float = Field(..., description="最终时长(秒)")
    segment_count: int = Field(..., description="片段数量")
    episodes_used: list[int] = Field(..., description="使用的集数索引")

    quality_score: float = Field(..., ge=0, le=1, description="整体质量评分")
    processing_time: float = Field(..., description="处理时间(秒)")

    # 生成的内容
    commentary_text: str = Field(default="", description="解说文案")
    jianying_project_path: Optional[Path] = None

    # 详细信息
    selected_segments: list[HighlightSegment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.now)


class SeriesInfo(BaseModel):
    """视频系列信息模型 - 新的核心数据结构"""

    # 基本信息
    series_id: str = Field(..., description="系列唯一标识")
    metadata: SeriesMetadata = Field(..., description="系列元数据")

    # 集数信息
    episodes: list[EpisodeInfo] = Field(..., description="集数列表")
    total_episodes: int = Field(..., description="总集数")
    total_duration: float = Field(default=0.0, description="总时长(秒)")

    # 处理状态
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="处理状态")
    progress: float = Field(default=0.0, ge=0, le=1, description="处理进度")

    # 分析结果
    analysis_completed: bool = Field(default=False, description="是否完成分析")
    total_highlight_segments: int = Field(default=0, description="总精彩片段数")
    average_quality_score: float = Field(default=0.0, ge=0, le=1, description="平均质量评分")

    # 合集设置和结果
    compilation_settings: Optional[CompilationSettings] = None
    compilation_result: Optional[SeriesCompilationResult] = None

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @validator('episodes')
    def validate_episodes(cls, v):
        if not v:
            raise ValueError('至少需要一集视频')
        return v

    @validator('total_episodes')
    def validate_total_episodes(cls, v, values):
        if 'episodes' in values and v != len(values['episodes']):
            raise ValueError('总集数与实际集数不匹配')
        return v

    def update_progress(self, new_status: ProcessingStatus, progress: float = None):
        """更新处理状态和进度"""
        self.status = new_status
        if progress is not None:
            self.progress = progress
        self.updated_at = datetime.now()

    def get_total_highlights(self) -> list[HighlightSegment]:
        """获取所有精彩片段"""
        highlights = []
        for episode in self.episodes:
            highlights.extend(episode.highlight_segments)
        return sorted(highlights, key=lambda x: x.quality_score, reverse=True)

    def get_best_segments(self, count: int = 10) -> list[HighlightSegment]:
        """获取最佳片段"""
        all_highlights = self.get_total_highlights()
        return all_highlights[:count]

    def calculate_statistics(self) -> dict[str, Any]:
        """计算统计信息"""
        all_highlights = self.get_total_highlights()

        return {
            "total_episodes": self.total_episodes,
            "total_duration": self.total_duration,
            "total_highlights": len(all_highlights),
            "average_quality": self.average_quality_score,
            "best_episode_index": max(self.episodes, key=lambda x: x.quality_score).index if self.episodes else None,
            "content_types": list({h.content_type for h in all_highlights}),
            "total_excitement_time": sum(h.duration for h in all_highlights if h.excitement_level > 0.8)
        }


class SeriesProcessingConfig(BaseModel):
    """系列处理配置"""

    # 分析配置
    enable_deep_analysis: bool = Field(default=True, description="启用深度分析")
    parallel_processing: bool = Field(default=True, description="并行处理")
    max_concurrent_episodes: int = Field(default=3, description="最大并发集数")

    # 质量配置
    min_quality_threshold: float = Field(default=0.5, description="最低质量阈值")
    auto_enhance: bool = Field(default=True, description="自动增强")

    # 输出配置
    auto_create_jianying: bool = Field(default=True, description="自动创建剪映项目")
    auto_generate_commentary: bool = Field(default=True, description="自动生成解说")

    # 缓存配置
    enable_cache: bool = Field(default=True, description="启用缓存")
    cache_duration: int = Field(default=3600, description="缓存时长(秒)")


# 导出所有模型
__all__ = [
    'VideoQuality',
    'ProcessingStatus',
    'HighlightSegment',
    'EpisodeInfo',
    'SeriesMetadata',
    'CompilationSettings',
    'SeriesCompilationResult',
    'SeriesInfo',
    'SeriesProcessingConfig'
]
