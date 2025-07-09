"""
系列合集制作工具 - 新的主要工作流
将多集视频智能合并成精彩合集
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

from ..analysis.video_analyzer import DeepVideoAnalyzer
from ..features.commentary_generator import CommentaryGenerator
from ..features.highlight_extractor import HighlightExtractor
from ..features.video_merger import VideoMerger
from ..integration.jianying_creator import JianYingCreator
from ..models.series import (
    CompilationSettings,
    EpisodeInfo,
    HighlightSegment,
    ProcessingStatus,
    SeriesCompilationResult,
    SeriesInfo,
    SeriesMetadata,
    SeriesProcessingConfig,
)
from ..utils.file_manager import FileManager

logger = logging.getLogger(__name__)


class SeriesCompilationParams(BaseModel):
    """系列合集制作参数"""

    # 必需参数
    video_paths: list[str] = Field(..., description="视频文件路径列表")
    series_title: str = Field(..., description="系列标题")

    # 可选参数
    target_duration: float = Field(default=120.0, description="目标时长(秒)")
    style: str = Field(default="humorous", description="风格: humorous/professional/dramatic")
    target_audience: str = Field(default="年轻人", description="目标受众")

    # 高级设置
    quality_threshold: float = Field(default=0.6, ge=0, le=1, description="质量阈值")
    excitement_threshold: float = Field(default=0.7, ge=0, le=1, description="精彩程度阈值")

    # 输出设置
    output_dir: str = Field(default="./output", description="输出目录")
    create_jianying_project: bool = Field(default=True, description="创建剪映项目")
    generate_commentary: bool = Field(default=True, description="生成解说文案")

    # 处理设置
    parallel_analysis: bool = Field(default=True, description="并行分析")
    max_concurrent: int = Field(default=3, description="最大并发数")


class SeriesCompilationTool:
    """系列合集制作工具 - 新的主要工具"""

    def __init__(self, config: SeriesProcessingConfig):
        self.config = config
        self.analyzer = DeepVideoAnalyzer()
        self.extractor = HighlightExtractor()
        self.merger = VideoMerger()
        self.commentary_generator = CommentaryGenerator()
        self.jianying_creator = JianYingCreator()
        self.file_manager = FileManager()

    @staticmethod
    def get_tool_definition() -> Tool:
        """获取工具定义"""
        return Tool(
            name="create_series_compilation",
            description="🎬 智能多集合并 - 将多个短剧集数合并成精彩合集（主要功能）",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "视频文件路径列表，如：['第1集.mp4', '第2集.mp4', '第3集.mp4']"
                    },
                    "series_title": {
                        "type": "string",
                        "description": "系列标题，如：'搞笑短剧精彩合集'"
                    },
                    "target_duration": {
                        "type": "number",
                        "default": 120.0,
                        "description": "目标时长(秒)，默认2分钟"
                    },
                    "style": {
                        "type": "string",
                        "enum": ["humorous", "professional", "dramatic", "suspense"],
                        "default": "humorous",
                        "description": "合集风格"
                    },
                    "target_audience": {
                        "type": "string",
                        "default": "年轻人",
                        "description": "目标受众"
                    },
                    "quality_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.6,
                        "description": "质量阈值(0-1)"
                    },
                    "excitement_threshold": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.7,
                        "description": "精彩程度阈值(0-1)"
                    },
                    "output_dir": {
                        "type": "string",
                        "default": "./output",
                        "description": "输出目录"
                    },
                    "create_jianying_project": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否创建剪映项目"
                    },
                    "generate_commentary": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否生成解说文案"
                    },
                    "parallel_analysis": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否并行分析"
                    },
                    "max_concurrent": {
                        "type": "integer",
                        "default": 3,
                        "description": "最大并发数"
                    }
                },
                "required": ["video_paths", "series_title"]
            }
        )

    async def execute(self, params: dict[str, Any]) -> TextContent:
        """执行系列合集制作"""
        try:
            # 验证参数
            validated_params = SeriesCompilationParams(**params)

            # 创建系列信息
            series_info = await self._create_series_info(validated_params)

            # 执行完整的合集制作流程
            result = await self._process_series_compilation(series_info, validated_params)

            # 格式化返回结果
            return self._format_result(result)

        except Exception as e:
            logger.error(f"系列合集制作失败: {e}")
            return TextContent(
                type="text",
                text=f"❌ 系列合集制作失败: {str(e)}"
            )

    async def _create_series_info(self, params: SeriesCompilationParams) -> SeriesInfo:
        """创建系列信息"""
        # 验证视频文件
        episodes = []
        total_duration = 0.0

        for i, video_path in enumerate(params.video_paths):
            path = Path(video_path)
            if not path.exists():
                raise FileNotFoundError(f"视频文件不存在: {video_path}")

            # 获取视频基本信息
            video_info = await self.file_manager.get_video_info(path)

            episode = EpisodeInfo(
                index=i,
                title=f"第{i+1}集",
                file_path=path,
                duration=video_info.duration,
                resolution=video_info.resolution,
                fps=video_info.fps,
                file_size=video_info.file_size,
                format=video_info.format
            )

            episodes.append(episode)
            total_duration += video_info.duration

        # 创建系列元数据
        metadata = SeriesMetadata(
            title=params.series_title,
            description=f"由{len(episodes)}集组成的精彩合集",
            target_audience=params.target_audience,
            style_preferences={
                "style": params.style,
                "target_duration": params.target_duration,
                "quality_threshold": params.quality_threshold,
                "excitement_threshold": params.excitement_threshold
            }
        )

        # 创建合集设置
        compilation_settings = CompilationSettings(
            target_duration=params.target_duration,
            quality_threshold=params.quality_threshold,
            excitement_threshold=params.excitement_threshold,
            include_commentary=params.generate_commentary
        )

        # 创建系列信息
        series_info = SeriesInfo(
            series_id=f"series_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            metadata=metadata,
            episodes=episodes,
            total_episodes=len(episodes),
            total_duration=total_duration,
            compilation_settings=compilation_settings
        )

        return series_info

    async def _process_series_compilation(
        self,
        series_info: SeriesInfo,
        params: SeriesCompilationParams
    ) -> SeriesCompilationResult:
        """处理系列合集制作"""

        logger.info(f"开始处理系列合集: {series_info.metadata.title}")
        start_time = datetime.now()

        # 第一步：批量分析视频
        series_info.update_progress(ProcessingStatus.ANALYZING, 0.1)
        await self._analyze_episodes(series_info, params)

        # 第二步：提取精彩片段
        series_info.update_progress(ProcessingStatus.EXTRACTING, 0.3)
        selected_segments = await self._extract_highlights(series_info)

        # 第三步：合并视频
        series_info.update_progress(ProcessingStatus.MERGING, 0.6)
        merged_video_path = await self._merge_segments(series_info, selected_segments, params)

        # 第四步：生成解说文案
        series_info.update_progress(ProcessingStatus.GENERATING, 0.8)
        commentary_text = ""
        if params.generate_commentary:
            commentary_text = await self._generate_commentary(series_info, selected_segments)

        # 第五步：创建剪映项目
        jianying_project_path = None
        if params.create_jianying_project:
            jianying_project_path = await self._create_jianying_project(
                series_info, merged_video_path, commentary_text
            )

        # 完成处理
        series_info.update_progress(ProcessingStatus.COMPLETED, 1.0)

        # 创建结果
        processing_time = (datetime.now() - start_time).total_seconds()

        result = SeriesCompilationResult(
            output_path=merged_video_path,
            duration=sum(s.duration for s in selected_segments),
            segment_count=len(selected_segments),
            episodes_used=[s.episode_index for s in selected_segments],
            quality_score=sum(s.quality_score for s in selected_segments) / len(selected_segments),
            processing_time=processing_time,
            commentary_text=commentary_text,
            jianying_project_path=jianying_project_path,
            selected_segments=selected_segments
        )

        series_info.compilation_result = result
        return result

    async def _analyze_episodes(self, series_info: SeriesInfo, params: SeriesCompilationParams):
        """批量分析集数"""
        if params.parallel_analysis:
            # 并行分析
            semaphore = asyncio.Semaphore(params.max_concurrent)
            tasks = []

            for episode in series_info.episodes:
                task = self._analyze_single_episode(episode, semaphore)
                tasks.append(task)

            await asyncio.gather(*tasks)
        else:
            # 串行分析
            for episode in series_info.episodes:
                await self._analyze_single_episode(episode)

        # 更新系列统计信息
        series_info.analysis_completed = True
        series_info.total_highlight_segments = sum(
            len(ep.highlight_segments) for ep in series_info.episodes
        )
        series_info.average_quality_score = sum(
            ep.quality_score for ep in series_info.episodes
        ) / len(series_info.episodes)

    async def _analyze_single_episode(self, episode: EpisodeInfo, semaphore=None):
        """分析单集"""
        async def _analyze():
            logger.info(f"分析第{episode.index + 1}集: {episode.file_path}")

            # 深度分析视频
            analysis_result = await self.analyzer.analyze_video_deeply(
                episode.file_path,
                include_highlights=True
            )

            # 更新集数信息
            episode.quality_score = analysis_result.quality_score
            episode.highlight_segments = analysis_result.highlight_segments
            episode.scene_count = len(analysis_result.scenes)
            episode.character_count = len(analysis_result.characters)
            episode.analysis_completed = True
            episode.analyzed_at = datetime.now()

            logger.info(f"第{episode.index + 1}集分析完成，发现{len(episode.highlight_segments)}个精彩片段")

        if semaphore:
            async with semaphore:
                await _analyze()
        else:
            await _analyze()

    async def _extract_highlights(self, series_info: SeriesInfo) -> list[HighlightSegment]:
        """提取精彩片段"""
        settings = series_info.compilation_settings
        all_highlights = series_info.get_total_highlights()

        # 过滤符合条件的片段
        filtered_highlights = [
            h for h in all_highlights
            if h.quality_score >= settings.quality_threshold
            and h.excitement_level >= settings.excitement_threshold
        ]

        # 智能选择片段以达到目标时长
        selected_segments = await self.extractor.select_optimal_segments(
            filtered_highlights,
            target_duration=settings.target_duration,
            max_duration=settings.max_duration
        )

        logger.info(f"从{len(all_highlights)}个片段中选择了{len(selected_segments)}个精彩片段")
        return selected_segments

    async def _merge_segments(
        self,
        series_info: SeriesInfo,
        segments: list[HighlightSegment],
        params: SeriesCompilationParams
    ) -> Path:
        """合并视频片段"""
        output_dir = Path(params.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_filename = f"{series_info.metadata.title}_合集.mp4"
        output_path = output_dir / output_filename

        # 准备合并参数
        merge_params = {
            "segments": segments,
            "episodes": series_info.episodes,
            "output_path": output_path,
            "settings": series_info.compilation_settings
        }

        # 执行合并
        await self.merger.merge_segments(**merge_params)

        logger.info(f"视频合并完成: {output_path}")
        return output_path

    async def _generate_commentary(
        self,
        series_info: SeriesInfo,
        segments: list[HighlightSegment]
    ) -> str:
        """生成解说文案"""
        commentary_params = {
            "series_info": series_info,
            "segments": segments,
            "style": series_info.metadata.style_preferences.get("style", "humorous"),
            "target_audience": series_info.metadata.target_audience
        }

        commentary_text = await self.commentary_generator.generate_series_commentary(**commentary_params)

        logger.info("解说文案生成完成")
        return commentary_text

    async def _create_jianying_project(
        self,
        series_info: SeriesInfo,
        video_path: Path,
        commentary_text: str
    ) -> Optional[Path]:
        """创建剪映项目"""
        try:
            project_params = {
                "series_info": series_info,
                "video_path": video_path,
                "commentary_text": commentary_text
            }

            project_path = await self.jianying_creator.create_series_project(**project_params)

            logger.info(f"剪映项目创建完成: {project_path}")
            return project_path

        except Exception as e:
            logger.warning(f"剪映项目创建失败: {e}")
            return None

    def _format_result(self, result: SeriesCompilationResult) -> TextContent:
        """格式化返回结果"""

        # 计算统计信息
        episodes_text = "、".join([f"第{i+1}集" for i in result.episodes_used])

        response_text = f"""🎬 **系列合集制作完成！**

📊 **处理结果**：
- ✅ 合集时长：{result.duration:.1f}秒
- 🎞️ 精彩片段：{result.segment_count}个
- 📺 使用集数：{episodes_text}
- ⭐ 质量评分：{result.quality_score:.2f}/1.0
- ⏱️ 处理时间：{result.processing_time:.1f}秒

📁 **生成文件**：
- 🎬 合集视频：`{result.output_path}`"""

        if result.commentary_text:
            response_text += f"\n- 🎤 解说文案：已生成（{len(result.commentary_text)}字）"

        if result.jianying_project_path:
            response_text += f"\n- 📁 剪映项目：`{result.jianying_project_path}`"

        response_text += """

🎯 **使用建议**：
1. 查看生成的合集视频，确认质量满意
2. 如需调整，可修改质量阈值或精彩程度阈值重新生成
3. 在剪映中进一步编辑和优化
4. 导出时建议使用高质量设置

✨ **系列合集制作是 DramaCraft 的主要功能，为您的短剧创作提供最佳体验！**"""

        return TextContent(type="text", text=response_text)
