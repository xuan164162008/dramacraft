"""
端到端自动化工作流。

本模块实现从视频输入到剪映项目输出的完整自动化流程，
包括质量验证、错误处理和进度监控。
"""

import asyncio
import json
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Union

from ..analysis.deep_analyzer import DeepAnalysisResult, DeepVideoAnalyzer
from ..audio.enhancer import AudioEnhancementResult, AudioEnhancer
from ..effects.auto_effects import AutoEffectsEngine, EffectPlan
from ..llm.base import BaseLLMClient
from ..sync.timeline_sync import SynchronizedTimeline, TimelineSynchronizer
from ..utils.helpers import ensure_directory, validate_video_file
from ..utils.logging import get_logger
from ..video.jianying_format import JianYingFormatConverter


class WorkflowStage(Enum):
    """工作流阶段枚举。"""
    INITIALIZATION = "initialization"
    VIDEO_ANALYSIS = "video_analysis"
    CONTENT_GENERATION = "content_generation"
    TIMELINE_SYNC = "timeline_sync"
    AUDIO_ENHANCEMENT = "audio_enhancement"
    EFFECTS_GENERATION = "effects_generation"
    PROJECT_CREATION = "project_creation"
    QUALITY_VALIDATION = "quality_validation"
    FINALIZATION = "finalization"


class WorkflowStatus(Enum):
    """工作流状态枚举。"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowProgress:
    """工作流进度。"""

    current_stage: WorkflowStage
    """当前阶段。"""

    stage_progress: float
    """当前阶段进度(0-1)。"""

    overall_progress: float
    """总体进度(0-1)。"""

    status: WorkflowStatus
    """工作流状态。"""

    message: str
    """状态消息。"""

    start_time: float
    """开始时间。"""

    elapsed_time: float
    """已用时间(秒)。"""

    estimated_remaining: Optional[float]
    """预估剩余时间(秒)。"""


@dataclass
class WorkflowResult:
    """工作流结果。"""

    success: bool
    """是否成功。"""

    draft_file_path: Optional[Path]
    """生成的草稿文件路径。"""

    analysis_result: Optional[DeepAnalysisResult]
    """视频分析结果。"""

    timeline: Optional[SynchronizedTimeline]
    """同步时间轴。"""

    effect_plan: Optional[EffectPlan]
    """特效计划。"""

    audio_result: Optional[AudioEnhancementResult]
    """音频增强结果。"""

    quality_metrics: dict[str, float]
    """质量指标。"""

    processing_time: float
    """处理时间(秒)。"""

    error_message: Optional[str]
    """错误信息。"""


class AutomationWorkflow:
    """端到端自动化工作流。"""

    def __init__(self, llm_client: BaseLLMClient, output_dir: Optional[Path] = None):
        """
        初始化自动化工作流。

        Args:
            llm_client: 大模型客户端
            output_dir: 输出目录
        """
        self.llm_client = llm_client
        self.output_dir = output_dir or Path("output")
        self.logger = get_logger("workflow.automation")

        # 初始化各个组件
        self.video_analyzer = DeepVideoAnalyzer(llm_client)
        self.timeline_synchronizer = TimelineSynchronizer(llm_client)
        self.audio_enhancer = AudioEnhancer(llm_client)
        self.effects_engine = AutoEffectsEngine(llm_client)
        self.format_converter = JianYingFormatConverter()

        # 确保输出目录存在
        ensure_directory(self.output_dir)

        # 工作流配置
        self.stage_weights = {
            WorkflowStage.INITIALIZATION: 0.05,
            WorkflowStage.VIDEO_ANALYSIS: 0.25,
            WorkflowStage.CONTENT_GENERATION: 0.15,
            WorkflowStage.TIMELINE_SYNC: 0.15,
            WorkflowStage.AUDIO_ENHANCEMENT: 0.15,
            WorkflowStage.EFFECTS_GENERATION: 0.10,
            WorkflowStage.PROJECT_CREATION: 0.10,
            WorkflowStage.QUALITY_VALIDATION: 0.03,
            WorkflowStage.FINALIZATION: 0.02
        }

        self.logger.info("端到端自动化工作流已初始化")

    async def execute_workflow(
        self,
        video_paths: list[Union[str, Path]],
        project_name: str,
        editing_objective: str,
        style_preferences: Optional[dict[str, Any]] = None,
        progress_callback: Optional[Callable[[WorkflowProgress], None]] = None
    ) -> WorkflowResult:
        """
        执行完整的自动化工作流。

        Args:
            video_paths: 视频文件路径列表
            project_name: 项目名称
            editing_objective: 编辑目标
            style_preferences: 风格偏好
            progress_callback: 进度回调函数

        Returns:
            工作流结果
        """
        start_time = time.time()

        # 初始化进度跟踪
        progress = WorkflowProgress(
            current_stage=WorkflowStage.INITIALIZATION,
            stage_progress=0.0,
            overall_progress=0.0,
            status=WorkflowStatus.RUNNING,
            message="初始化工作流...",
            start_time=start_time,
            elapsed_time=0.0,
            estimated_remaining=None
        )

        if progress_callback:
            progress_callback(progress)

        try:
            # 阶段1: 初始化
            await self._update_progress(progress, WorkflowStage.INITIALIZATION, 0.5, "验证输入文件...", progress_callback)
            video_paths = [Path(p) for p in video_paths]
            for video_path in video_paths:
                if not validate_video_file(video_path):
                    raise ValueError(f"无效的视频文件: {video_path}")

            await self._update_progress(progress, WorkflowStage.INITIALIZATION, 1.0, "初始化完成", progress_callback)

            # 阶段2: 视频分析
            await self._update_progress(progress, WorkflowStage.VIDEO_ANALYSIS, 0.0, "开始深度视频分析...", progress_callback)

            analysis_results = []
            for i, video_path in enumerate(video_paths):
                await self._update_progress(
                    progress, WorkflowStage.VIDEO_ANALYSIS,
                    i / len(video_paths),
                    f"分析视频 {i+1}/{len(video_paths)}: {video_path.name}",
                    progress_callback
                )

                analysis = await self.video_analyzer.analyze_video_deeply(
                    video_path, analysis_interval=1.0, include_audio=True
                )
                analysis_results.append(analysis)

            # 合并分析结果（使用第一个作为主要参考）
            main_analysis = analysis_results[0]
            await self._update_progress(progress, WorkflowStage.VIDEO_ANALYSIS, 1.0, "视频分析完成", progress_callback)

            # 阶段3: 内容生成
            await self._update_progress(progress, WorkflowStage.CONTENT_GENERATION, 0.0, "生成解说内容...", progress_callback)

            commentary_segments = await self._generate_commentary(
                main_analysis, editing_objective, style_preferences
            )

            await self._update_progress(progress, WorkflowStage.CONTENT_GENERATION, 1.0, "内容生成完成", progress_callback)

            # 阶段4: 时间轴同步
            await self._update_progress(progress, WorkflowStage.TIMELINE_SYNC, 0.0, "创建同步时间轴...", progress_callback)

            timeline = await self.timeline_synchronizer.create_synchronized_timeline(
                main_analysis, commentary_segments
            )

            await self._update_progress(progress, WorkflowStage.TIMELINE_SYNC, 1.0, "时间轴同步完成", progress_callback)

            # 阶段5: 音频增强
            await self._update_progress(progress, WorkflowStage.AUDIO_ENHANCEMENT, 0.0, "增强音频...", progress_callback)

            audio_result = await self.audio_enhancer.enhance_audio(
                video_paths[0], main_analysis, style_preferences
            )

            await self._update_progress(progress, WorkflowStage.AUDIO_ENHANCEMENT, 1.0, "音频增强完成", progress_callback)

            # 阶段6: 特效生成
            await self._update_progress(progress, WorkflowStage.EFFECTS_GENERATION, 0.0, "生成特效计划...", progress_callback)

            effect_plan = await self.effects_engine.generate_effect_plan(
                main_analysis, style_preferences
            )

            await self._update_progress(progress, WorkflowStage.EFFECTS_GENERATION, 1.0, "特效生成完成", progress_callback)

            # 阶段7: 项目创建
            await self._update_progress(progress, WorkflowStage.PROJECT_CREATION, 0.0, "创建剪映项目...", progress_callback)

            # 准备视频片段数据
            video_clips = []
            for i, (video_path, analysis) in enumerate(zip(video_paths, analysis_results)):
                clip = {
                    "path": str(video_path),
                    "duration": int(analysis.total_duration * 1000),
                    "width": analysis.resolution[0],
                    "height": analysis.resolution[1],
                    "start_time": 0,
                    "end_time": int(analysis.total_duration * 1000)
                }
                video_clips.append(clip)

            # 生成项目文件
            draft_file = self.format_converter.create_complete_project(
                project_name, timeline, effect_plan, audio_result, video_clips, self.output_dir
            )

            await self._update_progress(progress, WorkflowStage.PROJECT_CREATION, 1.0, "项目创建完成", progress_callback)

            # 阶段8: 质量验证
            await self._update_progress(progress, WorkflowStage.QUALITY_VALIDATION, 0.0, "验证项目质量...", progress_callback)

            quality_metrics = await self._validate_project_quality(
                draft_file, timeline, effect_plan, audio_result
            )

            await self._update_progress(progress, WorkflowStage.QUALITY_VALIDATION, 1.0, "质量验证完成", progress_callback)

            # 阶段9: 完成
            await self._update_progress(progress, WorkflowStage.FINALIZATION, 0.5, "生成报告...", progress_callback)

            processing_time = time.time() - start_time

            # 生成工作流报告
            await self._generate_workflow_report(
                project_name, main_analysis, timeline, effect_plan,
                audio_result, quality_metrics, processing_time
            )

            await self._update_progress(progress, WorkflowStage.FINALIZATION, 1.0, "工作流完成", progress_callback)

            # 更新最终状态
            progress.status = WorkflowStatus.COMPLETED
            progress.overall_progress = 1.0
            progress.message = f"工作流成功完成，耗时 {processing_time:.1f} 秒"
            if progress_callback:
                progress_callback(progress)

            return WorkflowResult(
                success=True,
                draft_file_path=draft_file,
                analysis_result=main_analysis,
                timeline=timeline,
                effect_plan=effect_plan,
                audio_result=audio_result,
                quality_metrics=quality_metrics,
                processing_time=processing_time,
                error_message=None
            )

        except Exception as e:
            self.logger.error(f"工作流执行失败: {e}")

            processing_time = time.time() - start_time

            # 更新失败状态
            progress.status = WorkflowStatus.FAILED
            progress.message = f"工作流失败: {str(e)}"
            progress.elapsed_time = processing_time
            if progress_callback:
                progress_callback(progress)

            return WorkflowResult(
                success=False,
                draft_file_path=None,
                analysis_result=None,
                timeline=None,
                effect_plan=None,
                audio_result=None,
                quality_metrics={},
                processing_time=processing_time,
                error_message=str(e)
            )

    async def _update_progress(
        self,
        progress: WorkflowProgress,
        stage: WorkflowStage,
        stage_progress: float,
        message: str,
        callback: Optional[Callable[[WorkflowProgress], None]]
    ):
        """更新进度。"""
        progress.current_stage = stage
        progress.stage_progress = stage_progress
        progress.message = message
        progress.elapsed_time = time.time() - progress.start_time

        # 计算总体进度
        completed_weight = sum(
            self.stage_weights[s] for s in WorkflowStage
            if list(WorkflowStage).index(s) < list(WorkflowStage).index(stage)
        )
        current_weight = self.stage_weights[stage] * stage_progress
        progress.overall_progress = completed_weight + current_weight

        # 估算剩余时间
        if progress.overall_progress > 0.1:
            estimated_total = progress.elapsed_time / progress.overall_progress
            progress.estimated_remaining = estimated_total - progress.elapsed_time

        if callback:
            callback(progress)

        # 短暂延迟以确保UI更新
        await asyncio.sleep(0.1)

    async def _generate_commentary(
        self,
        analysis_result: DeepAnalysisResult,
        editing_objective: str,
        style_preferences: Optional[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """生成解说内容。"""
        from ..features.commentary import CommentaryGenerator

        commentary_generator = CommentaryGenerator(self.llm_client)

        # 确定解说风格
        style = "analytical"
        if style_preferences:
            style = style_preferences.get("commentary_style", "analytical")

        # 生成解说
        commentary_result = await commentary_generator.generate_commentary(
            str(analysis_result.video_path),
            style=style,
            target_duration=analysis_result.total_duration
        )

        # 转换为时间轴事件格式
        segments = []
        if hasattr(commentary_result, 'segments'):
            for segment in commentary_result.segments:
                segments.append({
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "content": segment.get("content", ""),
                    "style": {
                        "font_size": 24,
                        "color": "#FFFFFF",
                        "position": "bottom",
                        "animation": "fade_in"
                    }
                })

        return segments

    async def _validate_project_quality(
        self,
        draft_file: Path,
        timeline: SynchronizedTimeline,
        effect_plan: EffectPlan,
        audio_result: AudioEnhancementResult
    ) -> dict[str, float]:
        """验证项目质量。"""
        quality_metrics = {}

        # 文件完整性检查
        quality_metrics["file_integrity"] = 1.0 if draft_file.exists() else 0.0

        # 时间轴质量
        quality_metrics["timeline_quality"] = timeline.quality_score

        # 特效复杂度合理性
        quality_metrics["effects_complexity"] = min(effect_plan.complexity_score, 1.0)

        # 音频质量
        if audio_result.quality_metrics:
            quality_metrics["audio_quality"] = audio_result.quality_metrics.get("overall_quality", 0.5)
        else:
            quality_metrics["audio_quality"] = 0.5

        # 事件同步质量
        sync_quality = self._calculate_sync_quality(timeline)
        quality_metrics["sync_quality"] = sync_quality

        # 总体质量评分
        weights = {
            "file_integrity": 0.2,
            "timeline_quality": 0.3,
            "effects_complexity": 0.2,
            "audio_quality": 0.2,
            "sync_quality": 0.1
        }

        overall_quality = sum(
            quality_metrics[key] * weights[key]
            for key in weights if key in quality_metrics
        )
        quality_metrics["overall_quality"] = overall_quality

        return quality_metrics

    def _calculate_sync_quality(self, timeline: SynchronizedTimeline) -> float:
        """计算同步质量。"""
        if not timeline.events:
            return 0.0

        # 检查事件时间重叠
        subtitle_events = [e for e in timeline.events if e.event_type == "subtitle"]
        overlap_penalty = 0.0

        for i, event1 in enumerate(subtitle_events):
            for event2 in subtitle_events[i+1:]:
                if (event1.start_time < event2.end_time and
                    event1.end_time > event2.start_time):
                    overlap_penalty += 0.1

        # 检查事件间隔合理性
        gap_quality = 1.0
        for i in range(len(subtitle_events) - 1):
            gap = float(subtitle_events[i+1].start_time - subtitle_events[i].end_time)
            if gap < 0.5:  # 间隔太短
                gap_quality -= 0.1
            elif gap > 5.0:  # 间隔太长
                gap_quality -= 0.05

        sync_quality = max(0.0, 1.0 - overlap_penalty) * max(0.0, gap_quality)
        return min(sync_quality, 1.0)

    async def _generate_workflow_report(
        self,
        project_name: str,
        analysis_result: DeepAnalysisResult,
        timeline: SynchronizedTimeline,
        effect_plan: EffectPlan,
        audio_result: AudioEnhancementResult,
        quality_metrics: dict[str, float],
        processing_time: float
    ) -> None:
        """生成工作流报告。"""
        report = {
            "project_name": project_name,
            "processing_time": processing_time,
            "video_analysis": {
                "total_duration": analysis_result.total_duration,
                "frame_rate": analysis_result.frame_rate,
                "resolution": analysis_result.resolution,
                "scenes_detected": len(analysis_result.scene_segments),
                "frames_analyzed": len(analysis_result.frame_analyses)
            },
            "timeline_sync": {
                "total_events": len(timeline.events),
                "quality_score": timeline.quality_score,
                "subtitle_events": len([e for e in timeline.events if e.event_type == "subtitle"]),
                "audio_events": len([e for e in timeline.events if e.event_type == "audio"])
            },
            "effects_plan": {
                "total_effects": effect_plan.total_effects,
                "total_transitions": effect_plan.total_transitions,
                "complexity_score": effect_plan.complexity_score,
                "estimated_render_time": effect_plan.estimated_render_time
            },
            "audio_enhancement": {
                "processing_time": audio_result.processing_time,
                "music_recommendations": len(audio_result.music_recommendations),
                "quality_metrics": audio_result.quality_metrics
            },
            "quality_metrics": quality_metrics,
            "timestamp": int(time.time())
        }

        # 保存报告
        report_file = self.output_dir / f"{project_name}_workflow_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        self.logger.info(f"工作流报告已保存: {report_file}")


class WorkflowValidator:
    """工作流验证器。"""

    def __init__(self):
        """初始化验证器。"""
        self.logger = get_logger("workflow.validator")

    def validate_inputs(
        self,
        video_paths: list[Path],
        project_name: str,
        editing_objective: str
    ) -> dict[str, Any]:
        """验证输入参数。"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # 验证视频文件
        for video_path in video_paths:
            if not video_path.exists():
                validation_result["errors"].append(f"视频文件不存在: {video_path}")
                validation_result["valid"] = False
            elif not validate_video_file(video_path):
                validation_result["errors"].append(f"无效的视频文件格式: {video_path}")
                validation_result["valid"] = False

        # 验证项目名称
        if not project_name or not project_name.strip():
            validation_result["errors"].append("项目名称不能为空")
            validation_result["valid"] = False
        elif len(project_name) > 100:
            validation_result["warnings"].append("项目名称过长，建议控制在100字符以内")

        # 验证编辑目标
        if not editing_objective or not editing_objective.strip():
            validation_result["errors"].append("编辑目标不能为空")
            validation_result["valid"] = False
        elif len(editing_objective) < 10:
            validation_result["warnings"].append("编辑目标描述过于简单，建议提供更详细的说明")

        return validation_result

    def validate_output(self, result: WorkflowResult) -> dict[str, Any]:
        """验证输出结果。"""
        validation_result = {
            "valid": result.success,
            "errors": [],
            "warnings": [],
            "quality_score": 0.0
        }

        if not result.success:
            validation_result["errors"].append(f"工作流执行失败: {result.error_message}")
            return validation_result

        # 验证输出文件
        if not result.draft_file_path or not result.draft_file_path.exists():
            validation_result["errors"].append("草稿文件生成失败")
            validation_result["valid"] = False

        # 验证质量指标
        if result.quality_metrics:
            overall_quality = result.quality_metrics.get("overall_quality", 0.0)
            validation_result["quality_score"] = overall_quality

            if overall_quality < 0.6:
                validation_result["warnings"].append("项目质量较低，建议检查输入参数")
            elif overall_quality < 0.4:
                validation_result["errors"].append("项目质量过低，可能存在严重问题")
                validation_result["valid"] = False

        # 验证处理时间
        if result.processing_time > 600:  # 10分钟
            validation_result["warnings"].append("处理时间较长，建议优化输入视频")

        return validation_result
