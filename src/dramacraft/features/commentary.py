"""
Short Drama Commentary Generation feature.

This module provides AI-powered commentary script generation for short drama videos
using Chinese LLM APIs with sophisticated prompt engineering.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from ..llm.base import BaseLLMClient, GenerationParams
from ..utils.helpers import format_duration, validate_video_file
from ..utils.logging import get_logger

logger = get_logger("features.commentary")


@dataclass
class VideoAnalysis:
    """Video analysis results."""

    duration: float
    """Video duration in seconds."""

    resolution: tuple[int, int]
    """Video resolution (width, height)."""

    fps: float
    """Frames per second."""

    scenes: list[dict[str, Any]]
    """Detected scenes with timestamps."""

    characters: list[str]
    """Detected character names/descriptions."""

    dialogue: list[dict[str, Any]]
    """Extracted dialogue with timestamps."""

    emotions: list[str]
    """Detected emotional tones."""

    themes: list[str]
    """Identified themes and topics."""


@dataclass
class CommentaryScript:
    """Generated commentary script."""

    title: str
    """Commentary title."""

    introduction: str
    """Opening introduction."""

    segments: list[dict[str, Any]]
    """Commentary segments with timestamps."""

    conclusion: str
    """Closing conclusion."""

    total_duration: float
    """Estimated total commentary duration."""

    style: str
    """Commentary style used."""

    metadata: dict[str, Any]
    """Additional metadata."""


class CommentaryGenerator:
    """Generator for short drama commentary scripts."""

    # Commentary styles and their characteristics
    COMMENTARY_STYLES = {
        "analytical": {
            "name": "分析解读型",
            "description": "深度分析剧情、人物关系和主题",
            "tone": "客观、专业、深入",
            "focus": ["剧情分析", "人物心理", "主题探讨", "细节解读"]
        },
        "emotional": {
            "name": "情感共鸣型",
            "description": "强调情感体验和观众共鸣",
            "tone": "感性、温暖、贴近观众",
            "focus": ["情感表达", "观众共鸣", "生活感悟", "情绪引导"]
        },
        "humorous": {
            "name": "幽默吐槽型",
            "description": "轻松幽默的吐槽和调侃",
            "tone": "轻松、幽默、接地气",
            "focus": ["搞笑点评", "梗的运用", "轻松调侃", "娱乐性"]
        },
        "critical": {
            "name": "批判思考型",
            "description": "批判性思考和社会议题探讨",
            "tone": "理性、犀利、有深度",
            "focus": ["社会现象", "价值观念", "现实意义", "深度思考"]
        },
        "storytelling": {
            "name": "故事讲述型",
            "description": "以讲故事的方式进行解说",
            "tone": "生动、引人入胜、有节奏感",
            "focus": ["故事重构", "情节推进", "悬念设置", "节奏控制"]
        }
    }

    def __init__(self, llm_client: BaseLLMClient):
        """
        Initialize commentary generator.

        Args:
            llm_client: LLM client for text generation
        """
        self.llm_client = llm_client
        self.logger = get_logger("features.commentary")

    async def generate_commentary(
        self,
        video_path: Union[str, Path],
        style: str = "analytical",
        target_duration: Optional[float] = None,
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> CommentaryScript:
        """
        Generate commentary script for a short drama video.

        Args:
            video_path: Path to the video file
            style: Commentary style to use
            target_duration: Target commentary duration in seconds
            custom_prompt: Custom prompt template
            **kwargs: Additional generation parameters

        Returns:
            Generated commentary script

        Raises:
            ValueError: If video file is invalid or style is unsupported
            LLMError: If text generation fails
        """
        video_path = Path(video_path)

        # Validate video file
        if not validate_video_file(video_path):
            raise ValueError(f"Invalid video file: {video_path}")

        # Validate style
        if style not in self.COMMENTARY_STYLES:
            raise ValueError(f"Unsupported commentary style: {style}")

        self.logger.info(f"Generating {style} commentary for {video_path.name}")

        # Analyze video (placeholder - would use actual video analysis)
        video_analysis = await self._analyze_video(video_path)

        # Generate commentary script
        script = await self._generate_script(
            video_analysis=video_analysis,
            style=style,
            target_duration=target_duration,
            custom_prompt=custom_prompt,
            **kwargs
        )

        self.logger.info(f"Generated commentary script with {len(script.segments)} segments")
        return script

    async def _analyze_video(self, video_path: Path) -> VideoAnalysis:
        """
        Analyze video content (placeholder implementation).

        Args:
            video_path: Path to video file

        Returns:
            Video analysis results
        """
        # TODO: Implement actual video analysis using computer vision
        # For now, return mock analysis
        return VideoAnalysis(
            duration=120.0,  # 2 minutes
            resolution=(1920, 1080),
            fps=30.0,
            scenes=[
                {"start": 0.0, "end": 30.0, "description": "开场介绍"},
                {"start": 30.0, "end": 90.0, "description": "主要情节"},
                {"start": 90.0, "end": 120.0, "description": "结局高潮"}
            ],
            characters=["女主角", "男主角", "配角"],
            dialogue=[
                {"start": 5.0, "speaker": "女主角", "text": "这样的生活我受够了"},
                {"start": 45.0, "speaker": "男主角", "text": "我会保护你的"},
                {"start": 100.0, "speaker": "女主角", "text": "谢谢你一直陪伴我"}
            ],
            emotions=["紧张", "感动", "温暖", "希望"],
            themes=["爱情", "成长", "坚持", "勇气"]
        )

    async def _generate_script(
        self,
        video_analysis: VideoAnalysis,
        style: str,
        target_duration: Optional[float] = None,
        custom_prompt: Optional[str] = None,
        **kwargs
    ) -> CommentaryScript:
        """
        Generate commentary script using LLM.

        Args:
            video_analysis: Video analysis results
            style: Commentary style
            target_duration: Target duration
            custom_prompt: Custom prompt template
            **kwargs: Additional parameters

        Returns:
            Generated commentary script
        """
        style_info = self.COMMENTARY_STYLES[style]

        # Build prompt
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = self._build_prompt(video_analysis, style_info, target_duration)

        # Generation parameters
        params = GenerationParams(
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.7),
            top_p=kwargs.get("top_p", 0.9),
        )

        # Generate commentary
        response = await self.llm_client.generate(prompt, params)

        # Parse response into structured script
        script = self._parse_script_response(response.text, video_analysis, style)

        return script

    def _build_prompt(
        self,
        analysis: VideoAnalysis,
        style_info: dict[str, Any],
        target_duration: Optional[float] = None
    ) -> str:
        """
        Build prompt for commentary generation.

        Args:
            analysis: Video analysis results
            style_info: Style information
            target_duration: Target duration

        Returns:
            Generated prompt
        """
        duration_text = format_duration(analysis.duration)
        target_text = f"，目标解说时长约{format_duration(target_duration)}" if target_duration else ""

        prompt = f"""
请为一个短剧视频生成{style_info['name']}的解说文案。

## 视频信息
- 时长：{duration_text}
- 主要角色：{', '.join(analysis.characters)}
- 情感基调：{', '.join(analysis.emotions)}
- 核心主题：{', '.join(analysis.themes)}

## 场景分析
"""

        for i, scene in enumerate(analysis.scenes, 1):
            start_time = format_duration(scene['start'])
            end_time = format_duration(scene['end'])
            prompt += f"{i}. {start_time}-{end_time}: {scene['description']}\n"

        prompt += """
## 关键对话
"""

        for dialogue in analysis.dialogue:
            time_text = format_duration(dialogue['start'])
            prompt += f"- {time_text} {dialogue['speaker']}：\"{dialogue['text']}\"\n"

        prompt += f"""
## 解说要求
- 风格：{style_info['name']} - {style_info['description']}
- 语调：{style_info['tone']}
- 重点关注：{', '.join(style_info['focus'])}
- 视频时长：{duration_text}{target_text}

## 输出格式
请按以下JSON格式输出解说文案：

```json
{{
    "title": "解说标题",
    "introduction": "开场介绍文案（30-60秒）",
    "segments": [
        {{
            "start_time": 0,
            "end_time": 30,
            "content": "这一段的解说内容",
            "key_points": ["重点1", "重点2"],
            "tone": "这段的语调特点"
        }}
    ],
    "conclusion": "结尾总结文案（20-40秒）",
    "style_notes": "风格特色说明"
}}
```

请确保解说内容：
1. 符合{style_info['name']}的特点
2. 语言生动有趣，贴近观众
3. 节奏感强，有起伏变化
4. 突出视频的亮点和看点
5. 适合短视频平台的观看习惯

开始生成解说文案：
"""

        return prompt.strip()

    def _parse_script_response(
        self,
        response_text: str,
        analysis: VideoAnalysis,
        style: str
    ) -> CommentaryScript:
        """
        Parse LLM response into structured commentary script.

        Args:
            response_text: Raw LLM response
            analysis: Video analysis
            style: Commentary style

        Returns:
            Parsed commentary script
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)

            # Calculate estimated duration
            total_duration = 0.0
            for segment in data.get("segments", []):
                start = segment.get("start_time", 0)
                end = segment.get("end_time", 0)
                total_duration += (end - start)

            # Add introduction and conclusion time
            total_duration += 45.0  # Estimated intro time
            total_duration += 30.0  # Estimated conclusion time

            return CommentaryScript(
                title=data.get("title", "短剧解说"),
                introduction=data.get("introduction", ""),
                segments=data.get("segments", []),
                conclusion=data.get("conclusion", ""),
                total_duration=total_duration,
                style=style,
                metadata={
                    "style_notes": data.get("style_notes", ""),
                    "video_duration": analysis.duration,
                    "generated_segments": len(data.get("segments", [])),
                }
            )

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")

            # Fallback: create basic script from raw text
            return CommentaryScript(
                title="短剧解说",
                introduction=response_text[:200] + "..." if len(response_text) > 200 else response_text,
                segments=[{
                    "start_time": 0,
                    "end_time": analysis.duration,
                    "content": response_text,
                    "key_points": [],
                    "tone": "general"
                }],
                conclusion="以上就是本期的短剧解说，感谢观看！",
                total_duration=analysis.duration + 60.0,
                style=style,
                metadata={"fallback_parsing": True}
            )
