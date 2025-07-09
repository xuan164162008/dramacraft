"""
时间轴精确同步系统。

本模块提供精确的时间轴控制，确保文案、音乐、特效与视频内容完全同步，
实现毫秒级的时间精度控制。
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Optional

from ..analysis.deep_analyzer import DeepAnalysisResult, FrameAnalysis
from ..llm.base import BaseLLMClient
from ..utils.logging import get_logger


@dataclass
class TimelineEvent:
    """时间轴事件。"""

    id: str
    """事件ID。"""

    start_time: Decimal
    """开始时间(毫秒精度)。"""

    end_time: Decimal
    """结束时间(毫秒精度)。"""

    event_type: str
    """事件类型(subtitle, audio, effect, transition)。"""

    content: str
    """事件内容。"""

    properties: dict[str, Any]
    """事件属性。"""

    sync_points: list[Decimal]
    """同步点时间戳。"""

    priority: int
    """优先级(1-10)。"""


@dataclass
class SyncRule:
    """同步规则。"""

    rule_id: str
    """规则ID。"""

    trigger_condition: str
    """触发条件。"""

    sync_action: str
    """同步动作。"""

    timing_offset: Decimal
    """时间偏移(毫秒)。"""

    duration_adjustment: Optional[Decimal]
    """时长调整。"""


@dataclass
class SynchronizedTimeline:
    """同步时间轴。"""

    video_duration: Decimal
    """视频总时长(毫秒)。"""

    frame_rate: Decimal
    """帧率。"""

    events: list[TimelineEvent]
    """时间轴事件列表。"""

    sync_rules: list[SyncRule]
    """同步规则。"""

    quality_score: float
    """同步质量评分(0-1)。"""

    metadata: dict[str, Any]
    """元数据。"""


class TimelineSynchronizer:
    """时间轴同步器。"""

    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化时间轴同步器。

        Args:
            llm_client: 大模型客户端
        """
        self.llm_client = llm_client
        self.logger = get_logger("sync.timeline_sync")

        # 时间精度设置(毫秒)
        self.time_precision = Decimal('0.001')

        # 同步容差(毫秒)
        self.sync_tolerance = Decimal('50')  # 50ms容差

        self.logger.info("时间轴同步器已初始化")

    async def create_synchronized_timeline(
        self,
        analysis_result: DeepAnalysisResult,
        commentary_segments: list[dict[str, Any]],
        audio_enhancements: Optional[list[dict[str, Any]]] = None,
        effects: Optional[list[dict[str, Any]]] = None
    ) -> SynchronizedTimeline:
        """
        创建同步时间轴。

        Args:
            analysis_result: 深度分析结果
            commentary_segments: 解说片段
            audio_enhancements: 音频增强
            effects: 特效列表

        Returns:
            同步时间轴
        """
        self.logger.info("创建同步时间轴")

        # 转换时间精度
        video_duration = self._to_precise_time(analysis_result.total_duration * 1000)
        frame_rate = Decimal(str(analysis_result.frame_rate))

        # 创建基础事件
        events = []

        # 添加解说事件
        subtitle_events = await self._create_subtitle_events(
            commentary_segments, analysis_result
        )
        events.extend(subtitle_events)

        # 添加音频增强事件
        if audio_enhancements:
            audio_events = await self._create_audio_events(
                audio_enhancements, analysis_result
            )
            events.extend(audio_events)

        # 添加特效事件
        if effects:
            effect_events = await self._create_effect_events(
                effects, analysis_result
            )
            events.extend(effect_events)

        # 生成同步规则
        sync_rules = await self._generate_sync_rules(analysis_result, events)

        # 应用同步规则
        synchronized_events = await self._apply_sync_rules(events, sync_rules)

        # 解决时间冲突
        resolved_events = await self._resolve_timing_conflicts(synchronized_events)

        # 计算同步质量
        quality_score = self._calculate_sync_quality(resolved_events, analysis_result)

        timeline = SynchronizedTimeline(
            video_duration=video_duration,
            frame_rate=frame_rate,
            events=resolved_events,
            sync_rules=sync_rules,
            quality_score=quality_score,
            metadata={
                "created_at": self._get_current_timestamp(),
                "total_events": len(resolved_events),
                "sync_precision": str(self.time_precision)
            }
        )

        self.logger.info(f"同步时间轴创建完成: {len(resolved_events)}个事件")
        return timeline

    async def _create_subtitle_events(
        self,
        commentary_segments: list[dict[str, Any]],
        analysis_result: DeepAnalysisResult
    ) -> list[TimelineEvent]:
        """创建字幕事件。"""
        events = []

        for i, segment in enumerate(commentary_segments):
            # 精确计算时间
            start_time = self._to_precise_time(segment.get("start_time", 0) * 1000)
            end_time = self._to_precise_time(segment.get("end_time", 0) * 1000)

            # 查找对应的视频内容
            sync_points = await self._find_content_sync_points(
                start_time, end_time, analysis_result
            )

            # 调整时间以匹配内容
            adjusted_start, adjusted_end = await self._adjust_subtitle_timing(
                start_time, end_time, segment.get("content", ""), sync_points
            )

            event = TimelineEvent(
                id=f"subtitle_{i}",
                start_time=adjusted_start,
                end_time=adjusted_end,
                event_type="subtitle",
                content=segment.get("content", ""),
                properties={
                    "style": segment.get("style", {}),
                    "position": segment.get("position", "bottom"),
                    "font_size": segment.get("font_size", 24),
                    "color": segment.get("color", "#FFFFFF"),
                    "background": segment.get("background", "transparent"),
                    "animation": segment.get("animation", "fade_in")
                },
                sync_points=sync_points,
                priority=8  # 字幕优先级较高
            )

            events.append(event)

        return events

    async def _create_audio_events(
        self,
        audio_enhancements: list[dict[str, Any]],
        analysis_result: DeepAnalysisResult
    ) -> list[TimelineEvent]:
        """创建音频事件。"""
        events = []

        for i, enhancement in enumerate(audio_enhancements):
            start_time = self._to_precise_time(enhancement.get("start_time", 0) * 1000)
            end_time = self._to_precise_time(enhancement.get("end_time", 0) * 1000)

            # 音频同步点基于场景变化
            sync_points = await self._find_audio_sync_points(
                start_time, end_time, analysis_result
            )

            event = TimelineEvent(
                id=f"audio_{i}",
                start_time=start_time,
                end_time=end_time,
                event_type="audio",
                content=enhancement.get("file_path", ""),
                properties={
                    "volume": enhancement.get("volume", 0.5),
                    "fade_in": enhancement.get("fade_in", 1000),
                    "fade_out": enhancement.get("fade_out", 1000),
                    "loop": enhancement.get("loop", False),
                    "audio_type": enhancement.get("type", "background_music")
                },
                sync_points=sync_points,
                priority=5  # 音频优先级中等
            )

            events.append(event)

        return events

    async def _create_effect_events(
        self,
        effects: list[dict[str, Any]],
        analysis_result: DeepAnalysisResult
    ) -> list[TimelineEvent]:
        """创建特效事件。"""
        events = []

        for i, effect in enumerate(effects):
            start_time = self._to_precise_time(effect.get("start_time", 0) * 1000)
            end_time = self._to_precise_time(effect.get("end_time", 0) * 1000)

            # 特效同步点基于动作和场景变化
            sync_points = await self._find_effect_sync_points(
                start_time, end_time, analysis_result, effect.get("type", "")
            )

            event = TimelineEvent(
                id=f"effect_{i}",
                start_time=start_time,
                end_time=end_time,
                event_type="effect",
                content=effect.get("type", ""),
                properties={
                    "effect_name": effect.get("name", ""),
                    "intensity": effect.get("intensity", 0.5),
                    "parameters": effect.get("parameters", {}),
                    "blend_mode": effect.get("blend_mode", "normal")
                },
                sync_points=sync_points,
                priority=3  # 特效优先级较低
            )

            events.append(event)

        return events

    async def _find_content_sync_points(
        self,
        start_time: Decimal,
        end_time: Decimal,
        analysis_result: DeepAnalysisResult
    ) -> list[Decimal]:
        """查找内容同步点。"""
        sync_points = []

        # 转换为秒进行比较
        start_sec = float(start_time) / 1000
        end_sec = float(end_time) / 1000

        # 查找场景变化点
        for scene in analysis_result.scene_segments:
            if start_sec <= scene.start_time <= end_sec:
                sync_points.append(self._to_precise_time(scene.start_time * 1000))
            if start_sec <= scene.end_time <= end_sec:
                sync_points.append(self._to_precise_time(scene.end_time * 1000))

        # 查找关键帧
        for frame in analysis_result.frame_analyses:
            if start_sec <= frame.timestamp <= end_sec:
                # 检查是否是关键帧（情绪变化、动作变化等）
                if self._is_key_frame(frame):
                    sync_points.append(self._to_precise_time(frame.timestamp * 1000))

        # 查找语音边界
        for audio in analysis_result.audio_segments:
            if audio.audio_type == "speech":
                if start_sec <= audio.start_time <= end_sec:
                    sync_points.append(self._to_precise_time(audio.start_time * 1000))
                if start_sec <= audio.end_time <= end_sec:
                    sync_points.append(self._to_precise_time(audio.end_time * 1000))

        # 排序并去重
        sync_points = sorted(set(sync_points))
        return sync_points

    def _is_key_frame(self, frame: FrameAnalysis) -> bool:
        """判断是否为关键帧。"""
        # 简化的关键帧判断逻辑
        return (
            frame.face_count > 0 or  # 有人脸
            frame.motion_intensity > 0.5 or  # 高运动强度
            frame.emotional_tone in ["happy", "sad", "tense"]  # 强烈情绪
        )

    async def _adjust_subtitle_timing(
        self,
        start_time: Decimal,
        end_time: Decimal,
        content: str,
        sync_points: list[Decimal]
    ) -> tuple[Decimal, Decimal]:
        """调整字幕时间以匹配内容。"""
        # 计算字幕阅读时间
        reading_time = self._calculate_reading_time(content)

        # 如果有同步点，优先对齐到同步点
        if sync_points:
            # 找到最接近的同步点作为开始时间
            closest_start = min(sync_points, key=lambda x: abs(x - start_time))

            # 如果距离在容差范围内，则对齐
            if abs(closest_start - start_time) <= self.sync_tolerance:
                adjusted_start = closest_start
                adjusted_end = adjusted_start + reading_time

                # 检查结束时间是否也有合适的同步点
                for point in sync_points:
                    if abs(point - adjusted_end) <= self.sync_tolerance:
                        adjusted_end = point
                        break

                return adjusted_start, adjusted_end

        # 如果没有合适的同步点，保持原时间但确保足够的阅读时间
        duration = end_time - start_time
        if duration < reading_time:
            end_time = start_time + reading_time

        return start_time, end_time

    def _calculate_reading_time(self, text: str) -> Decimal:
        """计算文本阅读时间。"""
        # 中文阅读速度约为每分钟300字
        char_count = len(text)
        reading_speed = 5  # 每秒5个字符
        min_display_time = Decimal('1000')  # 最少显示1秒

        calculated_time = Decimal(str(char_count / reading_speed * 1000))
        return max(calculated_time, min_display_time)

    async def _find_audio_sync_points(
        self,
        start_time: Decimal,
        end_time: Decimal,
        analysis_result: DeepAnalysisResult
    ) -> list[Decimal]:
        """查找音频同步点。"""
        sync_points = []

        start_sec = float(start_time) / 1000
        end_sec = float(end_time) / 1000

        # 音频同步主要基于场景变化和情绪变化
        for scene in analysis_result.scene_segments:
            if start_sec <= scene.start_time <= end_sec:
                sync_points.append(self._to_precise_time(scene.start_time * 1000))

        # 查找情绪变化点
        prev_emotion = None
        for frame in analysis_result.frame_analyses:
            if start_sec <= frame.timestamp <= end_sec:
                if prev_emotion and prev_emotion != frame.emotional_tone:
                    sync_points.append(self._to_precise_time(frame.timestamp * 1000))
                prev_emotion = frame.emotional_tone

        return sorted(set(sync_points))

    async def _find_effect_sync_points(
        self,
        start_time: Decimal,
        end_time: Decimal,
        analysis_result: DeepAnalysisResult,
        effect_type: str
    ) -> list[Decimal]:
        """查找特效同步点。"""
        sync_points = []

        start_sec = float(start_time) / 1000
        end_sec = float(end_time) / 1000

        # 根据特效类型选择不同的同步策略
        if effect_type in ["transition", "fade"]:
            # 转场特效同步到场景边界
            for scene in analysis_result.scene_segments:
                if start_sec <= scene.start_time <= end_sec:
                    sync_points.append(self._to_precise_time(scene.start_time * 1000))
                if start_sec <= scene.end_time <= end_sec:
                    sync_points.append(self._to_precise_time(scene.end_time * 1000))

        elif effect_type in ["highlight", "emphasis"]:
            # 强调特效同步到关键帧
            for frame in analysis_result.frame_analyses:
                if start_sec <= frame.timestamp <= end_sec and self._is_key_frame(frame):
                    sync_points.append(self._to_precise_time(frame.timestamp * 1000))

        return sorted(set(sync_points))

    async def _generate_sync_rules(
        self,
        analysis_result: DeepAnalysisResult,
        events: list[TimelineEvent]
    ) -> list[SyncRule]:
        """生成同步规则。"""
        rules = []

        # 规则1: 字幕与语音同步
        rules.append(SyncRule(
            rule_id="subtitle_speech_sync",
            trigger_condition="subtitle_overlaps_speech",
            sync_action="align_to_speech_boundary",
            timing_offset=Decimal('100'),  # 100ms提前
            duration_adjustment=None
        ))

        # 规则2: 音乐与场景情绪同步
        rules.append(SyncRule(
            rule_id="music_emotion_sync",
            trigger_condition="scene_emotion_change",
            sync_action="fade_transition",
            timing_offset=Decimal('500'),  # 500ms渐变
            duration_adjustment=None
        ))

        # 规则3: 特效与动作同步
        rules.append(SyncRule(
            rule_id="effect_action_sync",
            trigger_condition="high_motion_detected",
            sync_action="align_to_motion_peak",
            timing_offset=Decimal('0'),
            duration_adjustment=None
        ))

        return rules

    async def _apply_sync_rules(
        self,
        events: list[TimelineEvent],
        sync_rules: list[SyncRule]
    ) -> list[TimelineEvent]:
        """应用同步规则。"""
        synchronized_events = []

        for event in events:
            adjusted_event = event

            # 应用相关的同步规则
            for rule in sync_rules:
                if self._rule_applies_to_event(rule, event):
                    adjusted_event = await self._apply_rule_to_event(rule, adjusted_event)

            synchronized_events.append(adjusted_event)

        return synchronized_events

    def _rule_applies_to_event(self, rule: SyncRule, event: TimelineEvent) -> bool:
        """判断规则是否适用于事件。"""
        if rule.rule_id == "subtitle_speech_sync" and event.event_type == "subtitle":
            return True
        elif rule.rule_id == "music_emotion_sync" and event.event_type == "audio":
            return True
        elif rule.rule_id == "effect_action_sync" and event.event_type == "effect":
            return True
        return False

    async def _apply_rule_to_event(
        self,
        rule: SyncRule,
        event: TimelineEvent
    ) -> TimelineEvent:
        """将规则应用到事件。"""
        # 创建事件副本
        adjusted_event = TimelineEvent(
            id=event.id,
            start_time=event.start_time + rule.timing_offset,
            end_time=event.end_time + rule.timing_offset,
            event_type=event.event_type,
            content=event.content,
            properties=event.properties.copy(),
            sync_points=event.sync_points.copy(),
            priority=event.priority
        )

        # 应用时长调整
        if rule.duration_adjustment:
            adjusted_event.end_time = adjusted_event.start_time + rule.duration_adjustment

        return adjusted_event

    async def _resolve_timing_conflicts(
        self,
        events: list[TimelineEvent]
    ) -> list[TimelineEvent]:
        """解决时间冲突。"""
        # 按开始时间排序
        sorted_events = sorted(events, key=lambda e: e.start_time)
        resolved_events = []

        for event in sorted_events:
            # 检查与已有事件的冲突
            conflicts = self._find_conflicts(event, resolved_events)

            if conflicts:
                # 根据优先级解决冲突
                resolved_event = await self._resolve_conflict(event, conflicts)
                resolved_events.append(resolved_event)
            else:
                resolved_events.append(event)

        return resolved_events

    def _find_conflicts(
        self,
        event: TimelineEvent,
        existing_events: list[TimelineEvent]
    ) -> list[TimelineEvent]:
        """查找时间冲突。"""
        conflicts = []

        for existing in existing_events:
            # 检查时间重叠
            if (event.start_time < existing.end_time and
                event.end_time > existing.start_time):
                # 同类型事件才算冲突
                if event.event_type == existing.event_type:
                    conflicts.append(existing)

        return conflicts

    async def _resolve_conflict(
        self,
        new_event: TimelineEvent,
        conflicting_events: list[TimelineEvent]
    ) -> TimelineEvent:
        """解决单个冲突。"""
        # 简单策略：优先级高的事件保持不变，优先级低的事件调整时间
        highest_priority = max(conflicting_events, key=lambda e: e.priority)

        if new_event.priority > highest_priority.priority:
            # 新事件优先级更高，保持不变
            return new_event
        else:
            # 调整新事件时间到冲突事件之后
            latest_end = max(e.end_time for e in conflicting_events)
            duration = new_event.end_time - new_event.start_time

            adjusted_event = TimelineEvent(
                id=new_event.id,
                start_time=latest_end + self.sync_tolerance,
                end_time=latest_end + self.sync_tolerance + duration,
                event_type=new_event.event_type,
                content=new_event.content,
                properties=new_event.properties,
                sync_points=new_event.sync_points,
                priority=new_event.priority
            )

            return adjusted_event

    def _calculate_sync_quality(
        self,
        events: list[TimelineEvent],
        analysis_result: DeepAnalysisResult
    ) -> float:
        """计算同步质量评分。"""
        if not events:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for event in events:
            # 计算事件的同步质量
            event_score = 0.0

            # 检查是否对齐到同步点
            aligned_to_sync_point = any(
                abs(event.start_time - point) <= self.sync_tolerance
                for point in event.sync_points
            )

            if aligned_to_sync_point:
                event_score += 0.4

            # 检查时间合理性
            if event.event_type == "subtitle":
                reading_time = self._calculate_reading_time(event.content)
                actual_duration = event.end_time - event.start_time
                if actual_duration >= reading_time:
                    event_score += 0.3

            # 检查优先级冲突
            if not self._has_priority_conflicts(event, events):
                event_score += 0.3

            # 权重基于事件优先级
            weight = event.priority
            total_score += event_score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _has_priority_conflicts(
        self,
        event: TimelineEvent,
        all_events: list[TimelineEvent]
    ) -> bool:
        """检查优先级冲突。"""
        for other in all_events:
            if (other.id != event.id and
                other.event_type == event.event_type and
                event.start_time < other.end_time and
                event.end_time > other.start_time and
                other.priority > event.priority):
                return True
        return False

    def _to_precise_time(self, milliseconds: float) -> Decimal:
        """转换为精确时间。"""
        return Decimal(str(milliseconds)).quantize(self.time_precision, rounding=ROUND_HALF_UP)

    def _get_current_timestamp(self) -> int:
        """获取当前时间戳。"""
        import time
        return int(time.time() * 1000)
