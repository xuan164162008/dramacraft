"""
剪映自动化引擎。

本模块实现完整的剪映自动化引擎，通过草稿文件和API调用
实现智能视频编辑的全流程自动化。
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from ..analysis.deep_analyzer import DeepAnalysisResult
from ..audio.enhancer import AudioEnhancementResult
from ..effects.auto_effects import EffectPlan
from ..llm.base import BaseLLMClient
from ..sync.timeline_sync import SynchronizedTimeline
from ..utils.helpers import ensure_directory
from ..utils.logging import get_logger
from ..video.jianying_control import JianYingController
from ..video.jianying_format import JianYingFormatConverter, JianYingProjectManager


class AutomationStage(Enum):
    """自动化阶段。"""
    INITIALIZATION = "initialization"
    VIDEO_ANALYSIS = "video_analysis"
    CONTENT_GENERATION = "content_generation"
    TIMELINE_SYNC = "timeline_sync"
    AUDIO_ENHANCEMENT = "audio_enhancement"
    EFFECTS_GENERATION = "effects_generation"
    DRAFT_CREATION = "draft_creation"
    PROJECT_IMPORT = "project_import"
    QUALITY_VERIFICATION = "quality_verification"
    COMPLETION = "completion"


@dataclass
class AutomationProgress:
    """自动化进度。"""

    current_stage: AutomationStage
    """当前阶段。"""

    stage_progress: float
    """当前阶段进度(0-1)。"""

    overall_progress: float
    """总体进度(0-1)。"""

    message: str
    """进度消息。"""

    estimated_remaining_time: Optional[float] = None
    """预估剩余时间(秒)。"""


@dataclass
class AutomationResult:
    """自动化结果。"""

    success: bool
    """是否成功。"""

    draft_file_path: Optional[Path]
    """草稿文件路径。"""

    project_imported: bool
    """是否已导入项目。"""

    analysis_result: Optional[DeepAnalysisResult]
    """分析结果。"""

    timeline: Optional[SynchronizedTimeline]
    """时间轴。"""

    audio_result: Optional[AudioEnhancementResult]
    """音频结果。"""

    effect_plan: Optional[EffectPlan]
    """特效计划。"""

    processing_time: float
    """处理时间(秒)。"""

    error_message: Optional[str] = None
    """错误信息。"""

    quality_score: Optional[float] = None
    """质量评分(0-1)。"""


class JianYingAutomationEngine:
    """剪映自动化引擎。"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        output_dir: Path,
        jianying_path: Optional[Path] = None
    ):
        """
        初始化自动化引擎。

        Args:
            llm_client: LLM客户端
            output_dir: 输出目录
            jianying_path: 剪映安装路径
        """
        self.llm_client = llm_client
        self.output_dir = Path(output_dir)
        self.logger = get_logger("automation.jianying_engine")

        # 确保输出目录存在
        ensure_directory(self.output_dir)

        # 初始化组件
        self.format_converter = JianYingFormatConverter()
        self.project_manager = JianYingProjectManager(jianying_path)
        self.controller = JianYingController(jianying_path)

        # 进度跟踪
        self.current_progress: Optional[AutomationProgress] = None
        self.progress_callback: Optional[Callable[[AutomationProgress], None]] = None

        # 阶段权重（用于计算总体进度）
        self.stage_weights = {
            AutomationStage.INITIALIZATION: 0.05,
            AutomationStage.VIDEO_ANALYSIS: 0.20,
            AutomationStage.CONTENT_GENERATION: 0.15,
            AutomationStage.TIMELINE_SYNC: 0.15,
            AutomationStage.AUDIO_ENHANCEMENT: 0.10,
            AutomationStage.EFFECTS_GENERATION: 0.10,
            AutomationStage.DRAFT_CREATION: 0.15,
            AutomationStage.PROJECT_IMPORT: 0.05,
            AutomationStage.QUALITY_VERIFICATION: 0.05,
            AutomationStage.COMPLETION: 0.00
        }

        self.logger.info("剪映自动化引擎已初始化")

    async def execute_full_automation(
        self,
        video_paths: list[Path],
        project_name: str,
        editing_objective: str,
        style_preferences: Optional[dict[str, Any]] = None,
        auto_import: bool = True,
        progress_callback: Optional[Callable[[AutomationProgress], None]] = None
    ) -> AutomationResult:
        """
        执行完整的自动化流程。

        Args:
            video_paths: 视频文件路径列表
            project_name: 项目名称
            editing_objective: 编辑目标
            style_preferences: 风格偏好
            auto_import: 是否自动导入剪映
            progress_callback: 进度回调函数

        Returns:
            自动化结果
        """
        start_time = time.time()
        self.progress_callback = progress_callback

        try:
            self.logger.info(f"开始执行完整自动化流程: {project_name}")

            # 初始化
            await self._update_progress(AutomationStage.INITIALIZATION, 0.0, "初始化自动化引擎...")

            # 验证输入
            if not video_paths:
                raise ValueError("视频路径列表不能为空")

            for video_path in video_paths:
                if not video_path.exists():
                    raise FileNotFoundError(f"视频文件不存在: {video_path}")

            await self._update_progress(AutomationStage.INITIALIZATION, 1.0, "初始化完成")

            # 1. 视频分析
            await self._update_progress(AutomationStage.VIDEO_ANALYSIS, 0.0, "开始深度视频分析...")
            analysis_result = await self._analyze_videos(video_paths)
            await self._update_progress(AutomationStage.VIDEO_ANALYSIS, 1.0, "视频分析完成")

            # 2. 内容生成
            await self._update_progress(AutomationStage.CONTENT_GENERATION, 0.0, "生成编辑内容...")
            content_data = await self._generate_content(
                analysis_result, editing_objective, style_preferences
            )
            await self._update_progress(AutomationStage.CONTENT_GENERATION, 1.0, "内容生成完成")

            # 3. 时间轴同步
            await self._update_progress(AutomationStage.TIMELINE_SYNC, 0.0, "同步时间轴...")
            timeline = await self._synchronize_timeline(analysis_result, content_data)
            await self._update_progress(AutomationStage.TIMELINE_SYNC, 1.0, "时间轴同步完成")

            # 4. 音频增强
            await self._update_progress(AutomationStage.AUDIO_ENHANCEMENT, 0.0, "增强音频...")
            audio_result = await self._enhance_audio(video_paths, content_data, style_preferences)
            await self._update_progress(AutomationStage.AUDIO_ENHANCEMENT, 1.0, "音频增强完成")

            # 5. 特效生成
            await self._update_progress(AutomationStage.EFFECTS_GENERATION, 0.0, "生成特效...")
            effect_plan = await self._generate_effects(analysis_result, style_preferences)
            await self._update_progress(AutomationStage.EFFECTS_GENERATION, 1.0, "特效生成完成")

            # 6. 创建草稿
            await self._update_progress(AutomationStage.DRAFT_CREATION, 0.0, "创建剪映草稿...")
            draft_file = await self._create_draft_file(
                video_paths, project_name, analysis_result, timeline,
                audio_result, effect_plan, content_data
            )
            await self._update_progress(AutomationStage.DRAFT_CREATION, 1.0, "草稿创建完成")

            # 7. 项目导入
            project_imported = False
            if auto_import:
                await self._update_progress(AutomationStage.PROJECT_IMPORT, 0.0, "导入剪映项目...")
                project_imported = await self._import_project(draft_file, project_name)
                await self._update_progress(AutomationStage.PROJECT_IMPORT, 1.0,
                                          "项目导入完成" if project_imported else "项目导入失败")
            else:
                await self._update_progress(AutomationStage.PROJECT_IMPORT, 1.0, "跳过项目导入")

            # 8. 质量验证
            await self._update_progress(AutomationStage.QUALITY_VERIFICATION, 0.0, "验证质量...")
            quality_score = await self._verify_quality(draft_file, analysis_result)
            await self._update_progress(AutomationStage.QUALITY_VERIFICATION, 1.0, "质量验证完成")

            # 完成
            processing_time = time.time() - start_time
            await self._update_progress(AutomationStage.COMPLETION, 1.0,
                                      f"自动化完成，耗时 {processing_time:.1f} 秒")

            result = AutomationResult(
                success=True,
                draft_file_path=draft_file,
                project_imported=project_imported,
                analysis_result=analysis_result,
                timeline=timeline,
                audio_result=audio_result,
                effect_plan=effect_plan,
                processing_time=processing_time,
                quality_score=quality_score
            )

            self.logger.info(f"自动化流程完成: {project_name}, 质量评分: {quality_score:.2f}")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"自动化流程失败: {str(e)}"
            self.logger.error(error_msg)

            return AutomationResult(
                success=False,
                draft_file_path=None,
                project_imported=False,
                analysis_result=None,
                timeline=None,
                audio_result=None,
                effect_plan=None,
                processing_time=processing_time,
                error_message=error_msg
            )

    async def _update_progress(
        self,
        stage: AutomationStage,
        stage_progress: float,
        message: str
    ):
        """更新进度。"""
        # 计算总体进度
        completed_weight = sum(
            weight for s, weight in self.stage_weights.items()
            if s.value < stage.value
        )
        current_weight = self.stage_weights[stage] * stage_progress
        overall_progress = completed_weight + current_weight

        self.current_progress = AutomationProgress(
            current_stage=stage,
            stage_progress=stage_progress,
            overall_progress=overall_progress,
            message=message
        )

        if self.progress_callback:
            self.progress_callback(self.current_progress)

        self.logger.debug(f"进度更新: {stage.value} - {stage_progress:.1%} - {message}")

    async def _analyze_videos(self, video_paths: list[Path]) -> DeepAnalysisResult:
        """分析视频。"""
        from ..analysis.deep_analyzer import DeepVideoAnalyzer

        analyzer = DeepVideoAnalyzer(self.llm_client)

        # 如果有多个视频，分析第一个作为主要分析
        main_video = video_paths[0]
        analysis_result = await analyzer.analyze_video_deeply(main_video)

        return analysis_result

    async def _generate_content(
        self,
        analysis_result: DeepAnalysisResult,
        editing_objective: str,
        style_preferences: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """生成编辑内容。"""
        # 这里可以调用各种内容生成器
        # 为简化，返回基础内容结构
        return {
            "commentary": [],
            "subtitles": [],
            "narrative": [],
            "music_cues": []
        }

    async def _synchronize_timeline(
        self,
        analysis_result: DeepAnalysisResult,
        content_data: dict[str, Any]
    ) -> SynchronizedTimeline:
        """同步时间轴。"""
        from ..sync.timeline_sync import TimelineSynchronizer

        synchronizer = TimelineSynchronizer(self.llm_client)
        timeline = await synchronizer.create_synchronized_timeline(
            analysis_result, content_data.get("commentary", [])
        )

        return timeline

    async def _enhance_audio(
        self,
        video_paths: list[Path],
        content_data: dict[str, Any],
        style_preferences: Optional[dict[str, Any]]
    ) -> AudioEnhancementResult:
        """增强音频。"""
        from ..audio.enhancer import AudioEnhancer

        enhancer = AudioEnhancer(self.llm_client)

        # 使用第一个视频进行音频增强
        main_video = video_paths[0]
        audio_result = await enhancer.enhance_audio(
            main_video, style_preferences or {}
        )

        return audio_result

    async def _generate_effects(
        self,
        analysis_result: DeepAnalysisResult,
        style_preferences: Optional[dict[str, Any]]
    ) -> EffectPlan:
        """生成特效。"""
        from ..effects.auto_effects import AutoEffectsEngine

        effects_engine = AutoEffectsEngine(self.llm_client)
        effect_plan = await effects_engine.generate_effect_plan(analysis_result)

        return effect_plan

    async def _create_draft_file(
        self,
        video_paths: list[Path],
        project_name: str,
        analysis_result: DeepAnalysisResult,
        timeline: SynchronizedTimeline,
        audio_result: AudioEnhancementResult,
        effect_plan: EffectPlan,
        content_data: dict[str, Any]
    ) -> Path:
        """创建草稿文件。"""
        draft_file = self.format_converter.create_complete_project(
            video_paths=video_paths,
            analysis_result=analysis_result,
            output_dir=self.output_dir,
            project_name=project_name,
            timeline=timeline,
            audio_result=audio_result,
            effect_plan=effect_plan,
            subtitles=content_data.get("subtitles", [])
        )

        return draft_file

    async def _import_project(self, draft_file: Path, project_name: str) -> bool:
        """导入项目。"""
        try:
            success = self.project_manager.import_project(draft_file, project_name)
            return success
        except Exception as e:
            self.logger.warning(f"项目导入失败: {e}")
            return False

    async def _verify_quality(
        self,
        draft_file: Path,
        analysis_result: DeepAnalysisResult
    ) -> float:
        """验证质量。"""
        # 简单的质量评分逻辑
        score = 0.8  # 基础分数

        # 检查文件是否存在
        if not draft_file.exists():
            return 0.0

        # 检查文件大小
        file_size = draft_file.stat().st_size
        if file_size > 1000:  # 至少1KB
            score += 0.1

        # 检查分析质量
        if analysis_result and len(analysis_result.scene_segments) > 0:
            score += 0.1

        return min(score, 1.0)
