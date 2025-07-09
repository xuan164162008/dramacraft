"""
自动化特效和转场系统。

本模块实现智能特效添加和转场效果系统，根据视频内容、情绪变化和场景转换
自动选择和应用合适的视觉特效和转场效果。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import numpy as np

from ..analysis.deep_analyzer import DeepAnalysisResult, FrameAnalysis, SceneSegment
from ..llm.base import BaseLLMClient
from ..utils.logging import get_logger


class EffectType(Enum):
    """特效类型枚举。"""
    TRANSITION = "transition"
    FILTER = "filter"
    OVERLAY = "overlay"
    ANIMATION = "animation"
    COLOR_CORRECTION = "color_correction"
    PARTICLE = "particle"
    DISTORTION = "distortion"


class TransitionType(Enum):
    """转场类型枚举。"""
    CUT = "cut"
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    SLIDE = "slide"
    ZOOM = "zoom"
    ROTATE = "rotate"
    BLUR = "blur"
    GLITCH = "glitch"


@dataclass
class EffectTemplate:
    """特效模板。"""

    effect_id: str
    """特效ID。"""

    name: str
    """特效名称。"""

    effect_type: EffectType
    """特效类型。"""

    description: str
    """特效描述。"""

    parameters: dict[str, Any]
    """默认参数。"""

    mood_tags: list[str]
    """情绪标签。"""

    scene_tags: list[str]
    """场景标签。"""

    intensity_range: tuple[float, float]
    """强度范围(0-1)。"""

    duration_range: tuple[float, float]
    """时长范围(秒)。"""

    compatibility: list[str]
    """兼容的其他特效。"""


@dataclass
class TransitionTemplate:
    """转场模板。"""

    transition_id: str
    """转场ID。"""

    name: str
    """转场名称。"""

    transition_type: TransitionType
    """转场类型。"""

    description: str
    """转场描述。"""

    parameters: dict[str, Any]
    """默认参数。"""

    scene_change_types: list[str]
    """适用的场景变化类型。"""

    mood_compatibility: list[str]
    """情绪兼容性。"""

    duration_range: tuple[float, float]
    """时长范围(秒)。"""

    complexity: float
    """复杂度(0-1)。"""


@dataclass
class AppliedEffect:
    """应用的特效。"""

    effect_id: str
    """特效ID。"""

    start_time: float
    """开始时间(秒)。"""

    end_time: float
    """结束时间(秒)。"""

    parameters: dict[str, Any]
    """实际参数。"""

    intensity: float
    """强度(0-1)。"""

    layer: int
    """图层。"""

    blend_mode: str
    """混合模式。"""

    confidence: float
    """应用置信度(0-1)。"""


@dataclass
class AppliedTransition:
    """应用的转场。"""

    transition_id: str
    """转场ID。"""

    start_time: float
    """开始时间(秒)。"""

    duration: float
    """持续时间(秒)。"""

    parameters: dict[str, Any]
    """实际参数。"""

    from_scene: str
    """源场景ID。"""

    to_scene: str
    """目标场景ID。"""

    confidence: float
    """应用置信度(0-1)。"""


@dataclass
class EffectPlan:
    """特效计划。"""

    applied_effects: list[AppliedEffect]
    """应用的特效列表。"""

    applied_transitions: list[AppliedTransition]
    """应用的转场列表。"""

    total_effects: int
    """总特效数量。"""

    total_transitions: int
    """总转场数量。"""

    complexity_score: float
    """复杂度评分(0-1)。"""

    estimated_render_time: float
    """预估渲染时间(秒)。"""


class AutoEffectsEngine:
    """自动化特效引擎。"""

    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化自动化特效引擎。

        Args:
            llm_client: 大模型客户端
        """
        self.llm_client = llm_client
        self.logger = get_logger("effects.auto_effects")

        # 初始化特效和转场模板
        self.effect_templates = self._init_effect_templates()
        self.transition_templates = self._init_transition_templates()

        self.logger.info("自动化特效引擎已初始化")

    def _init_effect_templates(self) -> dict[str, EffectTemplate]:
        """初始化特效模板。"""
        templates = {}

        # 滤镜特效
        templates["warm_filter"] = EffectTemplate(
            effect_id="warm_filter",
            name="暖色滤镜",
            effect_type=EffectType.FILTER,
            description="增加画面暖色调，营造温馨氛围",
            parameters={
                "temperature": 200,
                "saturation": 1.2,
                "brightness": 1.1
            },
            mood_tags=["happy", "romantic", "warm"],
            scene_tags=["indoor", "close_up"],
            intensity_range=(0.3, 0.8),
            duration_range=(1.0, 10.0),
            compatibility=["soft_glow", "vignette"]
        )

        templates["cool_filter"] = EffectTemplate(
            effect_id="cool_filter",
            name="冷色滤镜",
            effect_type=EffectType.FILTER,
            description="增加画面冷色调，营造冷静或忧郁氛围",
            parameters={
                "temperature": -200,
                "saturation": 0.9,
                "contrast": 1.1
            },
            mood_tags=["sad", "tense", "calm"],
            scene_tags=["outdoor", "wide_shot"],
            intensity_range=(0.2, 0.7),
            duration_range=(2.0, 15.0),
            compatibility=["blur_background", "desaturate"]
        )

        # 动画特效
        templates["zoom_in"] = EffectTemplate(
            effect_id="zoom_in",
            name="放大动画",
            effect_type=EffectType.ANIMATION,
            description="缓慢放大画面，增强戏剧效果",
            parameters={
                "start_scale": 1.0,
                "end_scale": 1.2,
                "easing": "ease_in_out"
            },
            mood_tags=["tense", "dramatic", "focus"],
            scene_tags=["close_up", "dramatic"],
            intensity_range=(0.1, 0.3),
            duration_range=(2.0, 5.0),
            compatibility=["slow_motion"]
        )

        templates["shake"] = EffectTemplate(
            effect_id="shake",
            name="震动效果",
            effect_type=EffectType.ANIMATION,
            description="轻微震动效果，增加紧张感",
            parameters={
                "amplitude": 5,
                "frequency": 10,
                "decay": 0.8
            },
            mood_tags=["tense", "action", "shock"],
            scene_tags=["action", "conflict"],
            intensity_range=(0.2, 0.6),
            duration_range=(0.5, 2.0),
            compatibility=["flash", "distortion"]
        )

        # 粒子特效
        templates["sparkle"] = EffectTemplate(
            effect_id="sparkle",
            name="闪光粒子",
            effect_type=EffectType.PARTICLE,
            description="添加闪光粒子效果，增加梦幻感",
            parameters={
                "particle_count": 50,
                "size_range": (2, 8),
                "opacity": 0.7,
                "color": "#FFD700"
            },
            mood_tags=["happy", "magical", "romantic"],
            scene_tags=["celebration", "romantic"],
            intensity_range=(0.3, 0.8),
            duration_range=(1.0, 5.0),
            compatibility=["soft_glow", "warm_filter"]
        )

        # 色彩校正
        templates["high_contrast"] = EffectTemplate(
            effect_id="high_contrast",
            name="高对比度",
            effect_type=EffectType.COLOR_CORRECTION,
            description="增加画面对比度，突出视觉冲击",
            parameters={
                "contrast": 1.5,
                "shadows": -20,
                "highlights": 20
            },
            mood_tags=["dramatic", "intense", "bold"],
            scene_tags=["action", "dramatic"],
            intensity_range=(0.2, 0.6),
            duration_range=(1.0, 8.0),
            compatibility=["desaturate", "vignette"]
        )

        return templates

    def _init_transition_templates(self) -> dict[str, TransitionTemplate]:
        """初始化转场模板。"""
        templates = {}

        templates["fade_black"] = TransitionTemplate(
            transition_id="fade_black",
            name="黑场淡入淡出",
            transition_type=TransitionType.FADE,
            description="通过黑场实现平滑转场",
            parameters={
                "color": "#000000",
                "curve": "ease_in_out"
            },
            scene_change_types=["time_jump", "location_change"],
            mood_compatibility=["sad", "dramatic", "tense"],
            duration_range=(0.5, 2.0),
            complexity=0.2
        )

        templates["dissolve"] = TransitionTemplate(
            transition_id="dissolve",
            name="溶解转场",
            transition_type=TransitionType.DISSOLVE,
            description="两个画面逐渐融合",
            parameters={
                "opacity_curve": "linear",
                "blend_mode": "normal"
            },
            scene_change_types=["mood_change", "perspective_change"],
            mood_compatibility=["romantic", "dreamy", "calm"],
            duration_range=(1.0, 3.0),
            complexity=0.4
        )

        templates["slide_left"] = TransitionTemplate(
            transition_id="slide_left",
            name="左滑转场",
            transition_type=TransitionType.SLIDE,
            description="画面从右向左滑动切换",
            parameters={
                "direction": "left",
                "easing": "ease_out"
            },
            scene_change_types=["sequence", "progression"],
            mood_compatibility=["energetic", "dynamic", "modern"],
            duration_range=(0.3, 1.0),
            complexity=0.3
        )

        templates["zoom_transition"] = TransitionTemplate(
            transition_id="zoom_transition",
            name="缩放转场",
            transition_type=TransitionType.ZOOM,
            description="通过缩放效果实现转场",
            parameters={
                "zoom_factor": 2.0,
                "center_point": (0.5, 0.5),
                "blur_amount": 5
            },
            scene_change_types=["focus_change", "detail_to_wide"],
            mood_compatibility=["dramatic", "intense", "focus"],
            duration_range=(0.8, 2.0),
            complexity=0.6
        )

        templates["glitch"] = TransitionTemplate(
            transition_id="glitch",
            name="故障转场",
            transition_type=TransitionType.GLITCH,
            description="数字故障风格转场效果",
            parameters={
                "intensity": 0.5,
                "frequency": 20,
                "color_shift": True
            },
            scene_change_types=["shock", "revelation", "tech"],
            mood_compatibility=["tense", "modern", "edgy"],
            duration_range=(0.2, 0.8),
            complexity=0.8
        )

        return templates

    async def generate_effect_plan(
        self,
        analysis_result: DeepAnalysisResult,
        style_preferences: Optional[dict[str, Any]] = None
    ) -> EffectPlan:
        """
        生成特效计划。

        Args:
            analysis_result: 深度分析结果
            style_preferences: 风格偏好

        Returns:
            特效计划
        """
        self.logger.info("生成自动化特效计划")

        # 分析场景转换点
        scene_transitions = self._analyze_scene_transitions(analysis_result.scene_segments)

        # 生成转场效果
        applied_transitions = await self._generate_transitions(
            scene_transitions, analysis_result, style_preferences
        )

        # 生成特效
        applied_effects = await self._generate_effects(
            analysis_result, style_preferences
        )

        # 计算复杂度和渲染时间
        complexity_score = self._calculate_complexity(applied_effects, applied_transitions)
        render_time = self._estimate_render_time(applied_effects, applied_transitions)

        plan = EffectPlan(
            applied_effects=applied_effects,
            applied_transitions=applied_transitions,
            total_effects=len(applied_effects),
            total_transitions=len(applied_transitions),
            complexity_score=complexity_score,
            estimated_render_time=render_time
        )

        self.logger.info(f"特效计划生成完成: {len(applied_effects)}个特效, {len(applied_transitions)}个转场")
        return plan

    def _analyze_scene_transitions(self, scenes: list[SceneSegment]) -> list[dict[str, Any]]:
        """分析场景转换。"""
        transitions = []

        for i in range(len(scenes) - 1):
            current_scene = scenes[i]
            next_scene = scenes[i + 1]

            # 分析转换类型
            transition_type = self._classify_scene_transition(current_scene, next_scene)

            # 计算转换强度
            intensity = self._calculate_transition_intensity(current_scene, next_scene)

            transition = {
                "from_scene": current_scene,
                "to_scene": next_scene,
                "transition_point": current_scene.end_time,
                "transition_type": transition_type,
                "intensity": intensity,
                "mood_change": self._analyze_mood_change(current_scene, next_scene)
            }

            transitions.append(transition)

        return transitions

    def _classify_scene_transition(
        self,
        current_scene: SceneSegment,
        next_scene: SceneSegment
    ) -> str:
        """分类场景转换类型。"""
        # 基于场景描述和视觉风格判断转换类型
        if current_scene.location != next_scene.location:
            return "location_change"
        elif current_scene.visual_style != next_scene.visual_style:
            return "style_change"
        elif len(current_scene.characters) != len(next_scene.characters):
            return "character_change"
        elif current_scene.narrative_importance > 0.8 and next_scene.narrative_importance > 0.8:
            return "dramatic_shift"
        else:
            return "sequence"

    def _calculate_transition_intensity(
        self,
        current_scene: SceneSegment,
        next_scene: SceneSegment
    ) -> float:
        """计算转换强度。"""
        # 基于多个因素计算转换强度
        factors = []

        # 叙事重要性差异
        importance_diff = abs(current_scene.narrative_importance - next_scene.narrative_importance)
        factors.append(importance_diff)

        # 情绪变化强度
        if current_scene.emotional_arc and next_scene.emotional_arc:
            emotion_change = len(set(current_scene.emotional_arc) - set(next_scene.emotional_arc))
            factors.append(emotion_change / max(len(current_scene.emotional_arc), 1))

        # 角色变化
        character_change = abs(len(current_scene.characters) - len(next_scene.characters))
        factors.append(min(character_change / 3, 1.0))  # 标准化到0-1

        return np.mean(factors) if factors else 0.5

    def _analyze_mood_change(
        self,
        current_scene: SceneSegment,
        next_scene: SceneSegment
    ) -> dict[str, Any]:
        """分析情绪变化。"""
        current_emotions = set(current_scene.emotional_arc) if current_scene.emotional_arc else set()
        next_emotions = set(next_scene.emotional_arc) if next_scene.emotional_arc else set()

        return {
            "from_emotions": list(current_emotions),
            "to_emotions": list(next_emotions),
            "new_emotions": list(next_emotions - current_emotions),
            "lost_emotions": list(current_emotions - next_emotions),
            "intensity": len(next_emotions.symmetric_difference(current_emotions)) / max(len(current_emotions | next_emotions), 1)
        }

    async def _generate_transitions(
        self,
        scene_transitions: list[dict[str, Any]],
        analysis_result: DeepAnalysisResult,
        style_preferences: Optional[dict[str, Any]]
    ) -> list[AppliedTransition]:
        """生成转场效果。"""
        applied_transitions = []

        for transition_data in scene_transitions:
            # 选择最适合的转场模板
            best_template = await self._select_transition_template(
                transition_data, style_preferences
            )

            if best_template:
                # 计算转场参数
                duration = self._calculate_transition_duration(
                    transition_data, best_template
                )

                # 调整参数
                parameters = self._adjust_transition_parameters(
                    best_template.parameters, transition_data
                )

                applied_transition = AppliedTransition(
                    transition_id=best_template.transition_id,
                    start_time=transition_data["transition_point"] - duration / 2,
                    duration=duration,
                    parameters=parameters,
                    from_scene=transition_data["from_scene"].scene_id,
                    to_scene=transition_data["to_scene"].scene_id,
                    confidence=self._calculate_transition_confidence(
                        best_template, transition_data
                    )
                )

                applied_transitions.append(applied_transition)

        return applied_transitions

    async def _select_transition_template(
        self,
        transition_data: dict[str, Any],
        style_preferences: Optional[dict[str, Any]]
    ) -> Optional[TransitionTemplate]:
        """选择转场模板。"""
        best_template = None
        best_score = 0.0

        for template in self.transition_templates.values():
            score = self._score_transition_template(template, transition_data, style_preferences)

            if score > best_score:
                best_score = score
                best_template = template

        return best_template if best_score > 0.3 else None

    def _score_transition_template(
        self,
        template: TransitionTemplate,
        transition_data: dict[str, Any],
        style_preferences: Optional[dict[str, Any]]
    ) -> float:
        """评分转场模板。"""
        score = 0.0

        # 转换类型匹配
        if transition_data["transition_type"] in template.scene_change_types:
            score += 0.4

        # 情绪兼容性
        mood_change = transition_data["mood_change"]
        if mood_change["to_emotions"]:
            for emotion in mood_change["to_emotions"]:
                if emotion in template.mood_compatibility:
                    score += 0.3 / len(mood_change["to_emotions"])

        # 强度匹配
        intensity = transition_data["intensity"]
        if template.complexity <= intensity + 0.2:  # 允许一定容差
            score += 0.2

        # 风格偏好
        if style_preferences:
            preferred_style = style_preferences.get("transition_style", "")
            if preferred_style in template.name.lower():
                score += 0.1

        return min(score, 1.0)

    def _calculate_transition_duration(
        self,
        transition_data: dict[str, Any],
        template: TransitionTemplate
    ) -> float:
        """计算转场时长。"""
        min_duration, max_duration = template.duration_range
        intensity = transition_data["intensity"]

        # 根据强度调整时长
        duration = min_duration + (max_duration - min_duration) * intensity

        return duration

    def _adjust_transition_parameters(
        self,
        base_parameters: dict[str, Any],
        transition_data: dict[str, Any]
    ) -> dict[str, Any]:
        """调整转场参数。"""
        adjusted = base_parameters.copy()

        # 根据转换强度调整参数
        intensity = transition_data["intensity"]

        # 调整透明度相关参数
        if "opacity" in adjusted:
            adjusted["opacity"] = min(adjusted["opacity"] * (0.5 + intensity * 0.5), 1.0)

        # 调整速度相关参数
        if "speed" in adjusted:
            adjusted["speed"] = adjusted["speed"] * (0.8 + intensity * 0.4)

        return adjusted

    def _calculate_transition_confidence(
        self,
        template: TransitionTemplate,
        transition_data: dict[str, Any]
    ) -> float:
        """计算转场置信度。"""
        # 基于模板匹配度和转换数据质量
        match_score = self._score_transition_template(template, transition_data, None)
        data_quality = min(transition_data["intensity"] * 2, 1.0)  # 强度越高质量越好

        return (match_score + data_quality) / 2

    async def _generate_effects(
        self,
        analysis_result: DeepAnalysisResult,
        style_preferences: Optional[dict[str, Any]]
    ) -> list[AppliedEffect]:
        """生成特效。"""
        applied_effects = []

        # 为每个场景生成特效
        for scene in analysis_result.scene_segments:
            scene_effects = await self._generate_scene_effects(
                scene, analysis_result, style_preferences
            )
            applied_effects.extend(scene_effects)

        # 为关键帧生成特效
        key_frame_effects = await self._generate_keyframe_effects(
            analysis_result.frame_analyses, style_preferences
        )
        applied_effects.extend(key_frame_effects)

        # 去重和优化
        optimized_effects = self._optimize_effects(applied_effects)

        return optimized_effects

    async def _generate_scene_effects(
        self,
        scene: SceneSegment,
        analysis_result: DeepAnalysisResult,
        style_preferences: Optional[dict[str, Any]]
    ) -> list[AppliedEffect]:
        """为场景生成特效。"""
        effects = []

        # 获取场景对应的帧分析
        scene_frames = [
            frame for frame in analysis_result.frame_analyses
            if scene.start_time <= frame.timestamp <= scene.end_time
        ]

        if not scene_frames:
            return effects

        # 分析场景特征
        avg_brightness = np.mean([frame.brightness for frame in scene_frames])
        avg_motion = np.mean([frame.motion_intensity for frame in scene_frames])
        dominant_emotion = self._get_dominant_emotion(scene.emotional_arc)

        # 选择合适的特效模板
        suitable_templates = self._find_suitable_effect_templates(
            dominant_emotion, scene.visual_style, avg_brightness, avg_motion
        )

        # 应用特效
        for template in suitable_templates[:3]:  # 最多3个特效
            effect = await self._create_applied_effect(
                template, scene, avg_brightness, avg_motion, style_preferences
            )
            if effect:
                effects.append(effect)

        return effects

    def _get_dominant_emotion(self, emotional_arc: list[str]) -> str:
        """获取主导情绪。"""
        if not emotional_arc:
            return "neutral"

        # 统计情绪出现频率
        emotion_count = {}
        for emotion in emotional_arc:
            emotion_count[emotion] = emotion_count.get(emotion, 0) + 1

        return max(emotion_count.items(), key=lambda x: x[1])[0]

    def _find_suitable_effect_templates(
        self,
        emotion: str,
        visual_style: str,
        brightness: float,
        motion: float
    ) -> list[EffectTemplate]:
        """查找合适的特效模板。"""
        suitable = []

        for template in self.effect_templates.values():
            score = 0.0

            # 情绪匹配
            if emotion in template.mood_tags:
                score += 0.4

            # 场景匹配
            if visual_style in template.scene_tags:
                score += 0.3

            # 亮度匹配
            if template.effect_type == EffectType.FILTER:
                if brightness < 0.3 and "dark" in template.name.lower():
                    score += 0.2
                elif brightness > 0.7 and "bright" in template.name.lower():
                    score += 0.2

            # 运动匹配
            if template.effect_type == EffectType.ANIMATION:
                if motion > 0.5 and "dynamic" in template.description.lower():
                    score += 0.1
                elif motion < 0.3 and "calm" in template.description.lower():
                    score += 0.1

            if score > 0.3:  # 阈值
                suitable.append((template, score))

        # 按分数排序
        suitable.sort(key=lambda x: x[1], reverse=True)
        return [template for template, score in suitable]

    async def _create_applied_effect(
        self,
        template: EffectTemplate,
        scene: SceneSegment,
        brightness: float,
        motion: float,
        style_preferences: Optional[dict[str, Any]]
    ) -> Optional[AppliedEffect]:
        """创建应用的特效。"""
        # 计算特效强度
        intensity = self._calculate_effect_intensity(template, brightness, motion)

        # 计算时长
        duration = scene.end_time - scene.start_time
        max_effect_duration = min(duration, template.duration_range[1])
        effect_duration = min(max_effect_duration, template.duration_range[0] +
                            (template.duration_range[1] - template.duration_range[0]) * intensity)

        # 计算开始时间（可能不是整个场景）
        if effect_duration < duration:
            # 在场景中选择最佳位置
            start_offset = (duration - effect_duration) * 0.3  # 偏向开始
            start_time = scene.start_time + start_offset
        else:
            start_time = scene.start_time

        # 调整参数
        parameters = self._adjust_effect_parameters(
            template.parameters, intensity, brightness, motion
        )

        # 计算置信度
        confidence = self._calculate_effect_confidence(template, scene, intensity)

        if confidence < 0.4:  # 置信度太低
            return None

        return AppliedEffect(
            effect_id=template.effect_id,
            start_time=start_time,
            end_time=start_time + effect_duration,
            parameters=parameters,
            intensity=intensity,
            layer=self._determine_effect_layer(template.effect_type),
            blend_mode=self._determine_blend_mode(template.effect_type),
            confidence=confidence
        )

    def _calculate_effect_intensity(
        self,
        template: EffectTemplate,
        brightness: float,
        motion: float
    ) -> float:
        """计算特效强度。"""
        min_intensity, max_intensity = template.intensity_range

        # 基于场景特征计算强度
        if template.effect_type == EffectType.FILTER:
            # 滤镜强度基于亮度
            if "warm" in template.effect_id:
                intensity = min_intensity + (1 - brightness) * (max_intensity - min_intensity)
            elif "cool" in template.effect_id:
                intensity = min_intensity + brightness * (max_intensity - min_intensity)
            else:
                intensity = (min_intensity + max_intensity) / 2

        elif template.effect_type == EffectType.ANIMATION:
            # 动画强度基于运动
            intensity = min_intensity + motion * (max_intensity - min_intensity)

        else:
            # 其他类型使用中等强度
            intensity = (min_intensity + max_intensity) / 2

        return np.clip(intensity, min_intensity, max_intensity)

    def _adjust_effect_parameters(
        self,
        base_parameters: dict[str, Any],
        intensity: float,
        brightness: float,
        motion: float
    ) -> dict[str, Any]:
        """调整特效参数。"""
        adjusted = base_parameters.copy()

        # 根据强度调整数值参数
        for key, value in adjusted.items():
            if isinstance(value, (int, float)):
                if key in ["opacity", "alpha", "strength"]:
                    adjusted[key] = value * intensity
                elif key in ["size", "amplitude", "scale"]:
                    adjusted[key] = value * (0.5 + intensity * 0.5)

        # 根据亮度调整颜色参数
        if "color" in adjusted and brightness < 0.3:
            # 暗场景增加亮度
            adjusted["brightness_boost"] = 0.2

        return adjusted

    def _calculate_effect_confidence(
        self,
        template: EffectTemplate,
        scene: SceneSegment,
        intensity: float
    ) -> float:
        """计算特效置信度。"""
        confidence = 0.5  # 基础置信度

        # 情绪匹配度
        if scene.emotional_arc:
            emotion_match = any(emotion in template.mood_tags for emotion in scene.emotional_arc)
            if emotion_match:
                confidence += 0.3

        # 场景重要性
        confidence += scene.narrative_importance * 0.2

        # 强度合理性
        if template.intensity_range[0] <= intensity <= template.intensity_range[1]:
            confidence += 0.1

        return min(confidence, 1.0)

    def _determine_effect_layer(self, effect_type: EffectType) -> int:
        """确定特效图层。"""
        layer_map = {
            EffectType.FILTER: 1,
            EffectType.COLOR_CORRECTION: 2,
            EffectType.ANIMATION: 3,
            EffectType.OVERLAY: 4,
            EffectType.PARTICLE: 5,
            EffectType.DISTORTION: 6
        }
        return layer_map.get(effect_type, 3)

    def _determine_blend_mode(self, effect_type: EffectType) -> str:
        """确定混合模式。"""
        blend_map = {
            EffectType.FILTER: "normal",
            EffectType.COLOR_CORRECTION: "normal",
            EffectType.ANIMATION: "normal",
            EffectType.OVERLAY: "overlay",
            EffectType.PARTICLE: "screen",
            EffectType.DISTORTION: "normal"
        }
        return blend_map.get(effect_type, "normal")

    async def _generate_keyframe_effects(
        self,
        frame_analyses: list[FrameAnalysis],
        style_preferences: Optional[dict[str, Any]]
    ) -> list[AppliedEffect]:
        """为关键帧生成特效。"""
        effects = []

        # 识别关键帧
        key_frames = self._identify_key_frames(frame_analyses)

        for frame in key_frames:
            # 为关键帧生成短时特效
            frame_effects = await self._generate_frame_effects(frame, style_preferences)
            effects.extend(frame_effects)

        return effects

    def _identify_key_frames(self, frame_analyses: list[FrameAnalysis]) -> list[FrameAnalysis]:
        """识别关键帧。"""
        key_frames = []

        if not frame_analyses:
            return key_frames

        # 检测情绪变化点
        prev_emotion = None
        for frame in frame_analyses:
            if prev_emotion and prev_emotion != frame.emotional_tone:
                key_frames.append(frame)
            prev_emotion = frame.emotional_tone

        # 检测高运动强度帧
        motion_threshold = np.percentile([f.motion_intensity for f in frame_analyses], 80)
        for frame in frame_analyses:
            if frame.motion_intensity > motion_threshold:
                key_frames.append(frame)

        # 检测人脸数量变化
        prev_face_count = None
        for frame in frame_analyses:
            if prev_face_count is not None and prev_face_count != frame.face_count:
                key_frames.append(frame)
            prev_face_count = frame.face_count

        # 去重并按时间排序
        unique_frames = list({frame.timestamp: frame for frame in key_frames}.values())
        return sorted(unique_frames, key=lambda f: f.timestamp)

    async def _generate_frame_effects(
        self,
        frame: FrameAnalysis,
        style_preferences: Optional[dict[str, Any]]
    ) -> list[AppliedEffect]:
        """为单个关键帧生成特效。"""
        effects = []

        # 基于帧特征选择特效
        if frame.motion_intensity > 0.7:
            # 高运动强度 - 添加震动或缩放效果
            shake_effect = self._create_frame_effect(
                "shake", frame, duration=0.5, intensity=frame.motion_intensity
            )
            if shake_effect:
                effects.append(shake_effect)

        if frame.face_count > 2:
            # 多人场景 - 添加高亮效果
            highlight_effect = self._create_frame_effect(
                "high_contrast", frame, duration=1.0, intensity=0.6
            )
            if highlight_effect:
                effects.append(highlight_effect)

        if frame.emotional_tone in ["happy", "romantic"]:
            # 积极情绪 - 添加粒子效果
            particle_effect = self._create_frame_effect(
                "sparkle", frame, duration=2.0, intensity=0.5
            )
            if particle_effect:
                effects.append(particle_effect)

        return effects

    def _create_frame_effect(
        self,
        effect_id: str,
        frame: FrameAnalysis,
        duration: float,
        intensity: float
    ) -> Optional[AppliedEffect]:
        """为帧创建特效。"""
        if effect_id not in self.effect_templates:
            return None

        template = self.effect_templates[effect_id]

        # 调整参数
        parameters = self._adjust_effect_parameters(
            template.parameters, intensity, frame.brightness, frame.motion_intensity
        )

        return AppliedEffect(
            effect_id=effect_id,
            start_time=frame.timestamp,
            end_time=frame.timestamp + duration,
            parameters=parameters,
            intensity=intensity,
            layer=self._determine_effect_layer(template.effect_type),
            blend_mode=self._determine_blend_mode(template.effect_type),
            confidence=0.7  # 关键帧特效置信度较高
        )

    def _optimize_effects(self, effects: list[AppliedEffect]) -> list[AppliedEffect]:
        """优化特效列表。"""
        if not effects:
            return effects

        # 按开始时间排序
        sorted_effects = sorted(effects, key=lambda e: e.start_time)

        # 去除重叠的相同特效
        optimized = []
        for effect in sorted_effects:
            # 检查是否与已有特效重叠
            overlapping = [
                e for e in optimized
                if (e.effect_id == effect.effect_id and
                    e.start_time < effect.end_time and
                    e.end_time > effect.start_time)
            ]

            if not overlapping:
                optimized.append(effect)
            else:
                # 合并重叠的特效
                merged = self._merge_overlapping_effects(overlapping[0], effect)
                optimized = [e for e in optimized if e != overlapping[0]]
                optimized.append(merged)

        # 限制同时特效数量
        return self._limit_concurrent_effects(optimized)

    def _merge_overlapping_effects(
        self,
        effect1: AppliedEffect,
        effect2: AppliedEffect
    ) -> AppliedEffect:
        """合并重叠的特效。"""
        # 使用置信度更高的特效作为基础
        base_effect = effect1 if effect1.confidence >= effect2.confidence else effect2

        # 扩展时间范围
        start_time = min(effect1.start_time, effect2.start_time)
        end_time = max(effect1.end_time, effect2.end_time)

        # 平均强度
        avg_intensity = (effect1.intensity + effect2.intensity) / 2

        return AppliedEffect(
            effect_id=base_effect.effect_id,
            start_time=start_time,
            end_time=end_time,
            parameters=base_effect.parameters,
            intensity=avg_intensity,
            layer=base_effect.layer,
            blend_mode=base_effect.blend_mode,
            confidence=max(effect1.confidence, effect2.confidence)
        )

    def _limit_concurrent_effects(
        self,
        effects: list[AppliedEffect],
        max_concurrent: int = 3
    ) -> list[AppliedEffect]:
        """限制同时特效数量。"""
        if len(effects) <= max_concurrent:
            return effects

        # 按置信度排序，保留最高置信度的特效
        sorted_by_confidence = sorted(effects, key=lambda e: e.confidence, reverse=True)

        # 检查时间重叠，确保不超过最大并发数
        final_effects = []

        for effect in sorted_by_confidence:
            # 计算与当前特效重叠的数量
            overlapping_count = sum(
                1 for e in final_effects
                if e.start_time < effect.end_time and e.end_time > effect.start_time
            )

            if overlapping_count < max_concurrent:
                final_effects.append(effect)

        return sorted(final_effects, key=lambda e: e.start_time)

    def _calculate_complexity(
        self,
        effects: list[AppliedEffect],
        transitions: list[AppliedTransition]
    ) -> float:
        """计算复杂度评分。"""
        if not effects and not transitions:
            return 0.0

        # 特效复杂度
        effect_complexity = 0.0
        for effect in effects:
            template = self.effect_templates.get(effect.effect_id)
            if template:
                # 基于特效类型和强度计算复杂度
                type_complexity = {
                    EffectType.FILTER: 0.2,
                    EffectType.COLOR_CORRECTION: 0.3,
                    EffectType.ANIMATION: 0.6,
                    EffectType.OVERLAY: 0.4,
                    EffectType.PARTICLE: 0.8,
                    EffectType.DISTORTION: 0.9
                }.get(template.effect_type, 0.5)

                effect_complexity += type_complexity * effect.intensity

        # 转场复杂度
        transition_complexity = sum(t.duration * 0.5 for t in transitions)

        # 并发复杂度
        max_concurrent = self._calculate_max_concurrent_effects(effects)
        concurrent_complexity = max_concurrent * 0.1

        total_complexity = (effect_complexity + transition_complexity + concurrent_complexity)

        # 标准化到0-1范围
        return min(total_complexity / 10, 1.0)

    def _calculate_max_concurrent_effects(self, effects: list[AppliedEffect]) -> int:
        """计算最大并发特效数。"""
        if not effects:
            return 0

        # 创建时间点事件
        events = []
        for effect in effects:
            events.append((effect.start_time, 1))  # 开始
            events.append((effect.end_time, -1))   # 结束

        # 按时间排序
        events.sort()

        # 计算最大并发数
        current_count = 0
        max_count = 0

        for _time, delta in events:
            current_count += delta
            max_count = max(max_count, current_count)

        return max_count

    def _estimate_render_time(
        self,
        effects: list[AppliedEffect],
        transitions: list[AppliedTransition]
    ) -> float:
        """估算渲染时间。"""
        base_time = 10.0  # 基础渲染时间(秒)

        # 特效渲染时间
        effect_time = 0.0
        for effect in effects:
            template = self.effect_templates.get(effect.effect_id)
            if template:
                # 不同类型特效的渲染时间系数
                time_factor = {
                    EffectType.FILTER: 0.5,
                    EffectType.COLOR_CORRECTION: 0.3,
                    EffectType.ANIMATION: 2.0,
                    EffectType.OVERLAY: 1.0,
                    EffectType.PARTICLE: 3.0,
                    EffectType.DISTORTION: 2.5
                }.get(template.effect_type, 1.0)

                duration = effect.end_time - effect.start_time
                effect_time += duration * time_factor * effect.intensity

        # 转场渲染时间
        transition_time = sum(t.duration * 1.5 for t in transitions)

        return base_time + effect_time + transition_time
