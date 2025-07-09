"""
Short Drama Remix/Compilation feature.

This module provides automated video compilation and remixing capabilities
for short drama content using AI-driven scene selection and editing logic.
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from ..llm.base import BaseLLMClient, GenerationParams
from ..utils.helpers import format_duration, safe_filename, validate_video_file
from ..utils.logging import get_logger

logger = get_logger("features.remix")


class RemixStyle(Enum):
    """Remix compilation styles."""

    HIGHLIGHTS = "highlights"  # 精彩片段合集
    EMOTIONAL = "emotional"    # 情感高潮合集
    FUNNY = "funny"           # 搞笑片段合集
    ROMANTIC = "romantic"     # 浪漫片段合集
    DRAMATIC = "dramatic"     # 戏剧冲突合集
    CHARACTER = "character"   # 角色专题合集
    THEME = "theme"          # 主题专题合集


@dataclass
class VideoClip:
    """Video clip information."""

    source_file: Path
    """Source video file path."""

    start_time: float
    """Start time in seconds."""

    end_time: float
    """End time in seconds."""

    duration: float
    """Clip duration in seconds."""

    score: float
    """Relevance/quality score (0-1)."""

    tags: list[str]
    """Content tags."""

    description: str
    """Clip description."""

    emotions: list[str]
    """Detected emotions."""

    characters: list[str]
    """Characters in clip."""


@dataclass
class RemixPlan:
    """Remix compilation plan."""

    title: str
    """Compilation title."""

    style: RemixStyle
    """Remix style."""

    target_duration: float
    """Target total duration."""

    clips: list[VideoClip]
    """Selected clips in order."""

    transitions: list[dict[str, Any]]
    """Transition effects between clips."""

    music_suggestions: list[str]
    """Suggested background music."""

    text_overlays: list[dict[str, Any]]
    """Text overlay suggestions."""

    metadata: dict[str, Any]
    """Additional metadata."""


@dataclass
class RemixResult:
    """Remix compilation result."""

    output_path: Path
    """Output video file path."""

    plan: RemixPlan
    """Compilation plan used."""

    actual_duration: float
    """Actual output duration."""

    clips_used: int
    """Number of clips used."""

    processing_time: float
    """Processing time in seconds."""

    quality_score: float
    """Overall quality score."""

    metadata: dict[str, Any]
    """Processing metadata."""


class RemixGenerator:
    """Generator for short drama remix/compilation videos."""

    # Style configurations
    STYLE_CONFIGS = {
        RemixStyle.HIGHLIGHTS: {
            "name": "精彩片段合集",
            "description": "汇集最精彩、最吸引人的片段",
            "clip_duration_range": (5, 15),
            "target_emotions": ["excitement", "surprise", "tension"],
            "selection_criteria": ["high_action", "plot_twist", "emotional_peak"],
            "transition_style": "dynamic",
            "music_style": "upbeat"
        },
        RemixStyle.EMOTIONAL: {
            "name": "情感高潮合集",
            "description": "专注于情感表达强烈的片段",
            "clip_duration_range": (8, 20),
            "target_emotions": ["love", "sadness", "joy", "anger"],
            "selection_criteria": ["emotional_intensity", "character_development"],
            "transition_style": "smooth",
            "music_style": "emotional"
        },
        RemixStyle.FUNNY: {
            "name": "搞笑片段合集",
            "description": "收集幽默搞笑的精彩瞬间",
            "clip_duration_range": (3, 10),
            "target_emotions": ["humor", "joy", "surprise"],
            "selection_criteria": ["comedy_timing", "funny_dialogue", "visual_gags"],
            "transition_style": "quick",
            "music_style": "playful"
        },
        RemixStyle.ROMANTIC: {
            "name": "浪漫片段合集",
            "description": "浪漫温馨的爱情片段",
            "clip_duration_range": (10, 25),
            "target_emotions": ["love", "tenderness", "happiness"],
            "selection_criteria": ["romantic_scenes", "couple_interactions"],
            "transition_style": "gentle",
            "music_style": "romantic"
        },
        RemixStyle.DRAMATIC: {
            "name": "戏剧冲突合集",
            "description": "戏剧性强、冲突激烈的片段",
            "clip_duration_range": (6, 18),
            "target_emotions": ["tension", "anger", "conflict"],
            "selection_criteria": ["conflict_scenes", "dramatic_dialogue"],
            "transition_style": "intense",
            "music_style": "dramatic"
        },
        RemixStyle.CHARACTER: {
            "name": "角色专题合集",
            "description": "聚焦特定角色的精彩表现",
            "clip_duration_range": (5, 20),
            "target_emotions": ["varied"],
            "selection_criteria": ["character_focus", "character_development"],
            "transition_style": "character_focused",
            "music_style": "character_theme"
        },
        RemixStyle.THEME: {
            "name": "主题专题合集",
            "description": "围绕特定主题的内容合集",
            "clip_duration_range": (8, 22),
            "target_emotions": ["varied"],
            "selection_criteria": ["theme_relevance", "message_clarity"],
            "transition_style": "thematic",
            "music_style": "thematic"
        }
    }

    def __init__(self, llm_client: BaseLLMClient):
        """
        Initialize remix generator.

        Args:
            llm_client: LLM client for content analysis
        """
        self.llm_client = llm_client
        self.logger = get_logger("features.remix")

    async def create_remix(
        self,
        source_videos: list[Union[str, Path]],
        style: RemixStyle,
        target_duration: float = 60.0,
        output_path: Optional[Union[str, Path]] = None,
        custom_criteria: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> RemixResult:
        """
        Create a remix compilation from source videos.

        Args:
            source_videos: List of source video file paths
            style: Remix style to use
            target_duration: Target duration in seconds
            output_path: Output file path (auto-generated if None)
            custom_criteria: Custom selection criteria
            **kwargs: Additional parameters

        Returns:
            Remix compilation result

        Raises:
            ValueError: If inputs are invalid
            LLMError: If content analysis fails
        """
        # Validate inputs
        source_paths = [Path(v) for v in source_videos]
        for path in source_paths:
            if not validate_video_file(path):
                raise ValueError(f"Invalid video file: {path}")

        self.logger.info(f"Creating {style.value} remix from {len(source_paths)} videos")

        # Analyze source videos
        all_clips = []
        for video_path in source_paths:
            clips = await self._analyze_video_for_clips(video_path, style)
            all_clips.extend(clips)

        self.logger.info(f"Analyzed {len(all_clips)} potential clips")

        # Create remix plan
        plan = await self._create_remix_plan(
            clips=all_clips,
            style=style,
            target_duration=target_duration,
            custom_criteria=custom_criteria,
            **kwargs
        )

        # Generate output path if not provided
        if output_path is None:
            style_name = self.STYLE_CONFIGS[style]["name"]
            filename = safe_filename(f"{style_name}_remix_{int(target_duration)}s.mp4")
            output_path = Path("output") / filename
        else:
            output_path = Path(output_path)

        # Create the remix video (placeholder - would use actual video editing)
        result = await self._create_remix_video(plan, output_path)

        self.logger.info(f"Created remix video: {output_path}")
        return result

    async def _analyze_video_for_clips(
        self,
        video_path: Path,
        style: RemixStyle
    ) -> list[VideoClip]:
        """
        Analyze video and extract potential clips for remix.

        Args:
            video_path: Path to video file
            style: Target remix style

        Returns:
            List of potential video clips
        """
        style_config = self.STYLE_CONFIGS[style]

        # Build analysis prompt
        prompt = self._build_analysis_prompt(video_path, style_config)

        # Generate analysis
        params = GenerationParams(max_tokens=1500, temperature=0.3)
        response = await self.llm_client.generate(prompt, params)

        # Parse clips from response
        clips = self._parse_clips_response(response.text, video_path)

        return clips

    def _build_analysis_prompt(
        self,
        video_path: Path,
        style_config: dict[str, Any]
    ) -> str:
        """
        Build prompt for video clip analysis.

        Args:
            video_path: Video file path
            style_config: Style configuration

        Returns:
            Analysis prompt
        """
        prompt = f"""
请分析短剧视频《{video_path.stem}》，为制作{style_config['name']}找出合适的片段。

## 分析目标
- 风格：{style_config['name']} - {style_config['description']}
- 目标情感：{', '.join(style_config['target_emotions'])}
- 选择标准：{', '.join(style_config['selection_criteria'])}
- 片段时长：{style_config['clip_duration_range'][0]}-{style_config['clip_duration_range'][1]}秒

## 输出要求
请按以下JSON格式输出分析结果：

```json
{{
    "clips": [
        {{
            "start_time": 0,
            "end_time": 10,
            "duration": 10,
            "score": 0.9,
            "tags": ["精彩", "高潮"],
            "description": "片段内容描述",
            "emotions": ["excitement", "tension"],
            "characters": ["主角", "配角"],
            "reason": "选择这个片段的原因"
        }}
    ],
    "video_summary": "视频整体内容概述",
    "style_match": "与目标风格的匹配度分析"
}}
```

请确保：
1. 选择最符合{style_config['name']}风格的片段
2. 片段时长在合理范围内
3. 评分反映片段质量和相关性
4. 描述准确且有助于后续编辑

开始分析：
"""

        return prompt.strip()

    def _parse_clips_response(
        self,
        response_text: str,
        video_path: Path
    ) -> list[VideoClip]:
        """
        Parse LLM response into video clips.

        Args:
            response_text: Raw LLM response
            video_path: Source video path

        Returns:
            List of parsed video clips
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)

            clips = []
            for clip_data in data.get("clips", []):
                clip = VideoClip(
                    source_file=video_path,
                    start_time=clip_data.get("start_time", 0),
                    end_time=clip_data.get("end_time", 0),
                    duration=clip_data.get("duration", 0),
                    score=clip_data.get("score", 0.5),
                    tags=clip_data.get("tags", []),
                    description=clip_data.get("description", ""),
                    emotions=clip_data.get("emotions", []),
                    characters=clip_data.get("characters", [])
                )
                clips.append(clip)

            return clips

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse clips response: {e}")

            # Fallback: create basic clips
            return [
                VideoClip(
                    source_file=video_path,
                    start_time=0,
                    end_time=30,
                    duration=30,
                    score=0.7,
                    tags=["fallback"],
                    description="Fallback clip",
                    emotions=["neutral"],
                    characters=["unknown"]
                )
            ]

    async def _create_remix_plan(
        self,
        clips: list[VideoClip],
        style: RemixStyle,
        target_duration: float,
        custom_criteria: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> RemixPlan:
        """
        Create a remix plan by selecting and ordering clips.

        Args:
            clips: Available video clips
            style: Remix style
            target_duration: Target duration
            custom_criteria: Custom selection criteria
            **kwargs: Additional parameters

        Returns:
            Remix plan
        """
        style_config = self.STYLE_CONFIGS[style]

        # Sort clips by score
        sorted_clips = sorted(clips, key=lambda c: c.score, reverse=True)

        # Select clips to fit target duration
        selected_clips = []
        total_duration = 0.0

        for clip in sorted_clips:
            if total_duration + clip.duration <= target_duration:
                selected_clips.append(clip)
                total_duration += clip.duration

            if total_duration >= target_duration * 0.9:  # 90% of target
                break

        # Create transitions
        transitions = []
        for _i in range(len(selected_clips) - 1):
            transitions.append({
                "type": style_config["transition_style"],
                "duration": 0.5,
                "effect": "fade"
            })

        # Generate music suggestions
        music_suggestions = self._generate_music_suggestions(style_config)

        # Generate text overlays
        text_overlays = self._generate_text_overlays(selected_clips, style)

        return RemixPlan(
            title=f"{style_config['name']} - {format_duration(target_duration)}",
            style=style,
            target_duration=target_duration,
            clips=selected_clips,
            transitions=transitions,
            music_suggestions=music_suggestions,
            text_overlays=text_overlays,
            metadata={
                "total_clips_analyzed": len(clips),
                "clips_selected": len(selected_clips),
                "actual_duration": total_duration,
                "style_config": style_config
            }
        )

    def _generate_music_suggestions(
        self,
        style_config: dict[str, Any]
    ) -> list[str]:
        """Generate music suggestions based on style."""
        music_style = style_config["music_style"]

        suggestions = {
            "upbeat": ["动感电子乐", "流行摇滚", "节奏感强的配乐"],
            "emotional": ["抒情钢琴曲", "温暖弦乐", "感人配乐"],
            "playful": ["轻快爵士乐", "俏皮电子音", "欢快配乐"],
            "romantic": ["浪漫钢琴曲", "温柔弦乐", "爱情主题配乐"],
            "dramatic": ["史诗配乐", "紧张音效", "戏剧性音乐"],
            "character_theme": ["角色主题曲", "个性化配乐"],
            "thematic": ["主题相关音乐", "氛围配乐"]
        }

        return suggestions.get(music_style, ["通用背景音乐"])

    def _generate_text_overlays(
        self,
        clips: list[VideoClip],
        style: RemixStyle
    ) -> list[dict[str, Any]]:
        """Generate text overlay suggestions."""
        overlays = []

        # Title overlay
        overlays.append({
            "type": "title",
            "text": f"{self.STYLE_CONFIGS[style]['name']}",
            "position": "center",
            "duration": 3.0,
            "style": "large_bold"
        })

        # Clip descriptions
        for i, clip in enumerate(clips):
            if clip.description and len(clip.description) < 50:
                overlays.append({
                    "type": "description",
                    "text": clip.description,
                    "position": "bottom",
                    "start_time": sum(c.duration for c in clips[:i]),
                    "duration": min(clip.duration, 5.0),
                    "style": "subtitle"
                })

        return overlays

    async def _create_remix_video(
        self,
        plan: RemixPlan,
        output_path: Path
    ) -> RemixResult:
        """
        Create the actual remix video (placeholder implementation).

        Args:
            plan: Remix plan
            output_path: Output file path

        Returns:
            Remix result
        """
        # TODO: Implement actual video editing using moviepy
        # For now, return mock result

        import time
        start_time = time.time()

        # Simulate video processing
        actual_duration = sum(clip.duration for clip in plan.clips)

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Mock video creation (would use moviepy here)
        output_path.touch()  # Create empty file as placeholder

        processing_time = time.time() - start_time

        return RemixResult(
            output_path=output_path,
            plan=plan,
            actual_duration=actual_duration,
            clips_used=len(plan.clips),
            processing_time=processing_time,
            quality_score=0.85,  # Mock quality score
            metadata={
                "mock_creation": True,
                "clips_processed": len(plan.clips),
                "transitions_applied": len(plan.transitions)
            }
        )
