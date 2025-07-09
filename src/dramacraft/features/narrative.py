"""
First-Person Narrative Commentary feature.

This module provides first-person perspective narration script generation
for short drama content with character analysis and perspective switching.
"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

from ..llm.base import BaseLLMClient, GenerationParams
from ..utils.helpers import validate_video_file
from ..utils.logging import get_logger

logger = get_logger("features.narrative")


class NarrativePerspective(Enum):
    """First-person narrative perspectives."""

    PROTAGONIST = "protagonist"      # 主角视角
    ANTAGONIST = "antagonist"        # 反派视角
    SUPPORTING = "supporting"        # 配角视角
    OBSERVER = "observer"           # 旁观者视角
    MULTIPLE = "multiple"           # 多角色轮换视角


@dataclass
class Character:
    """Character information for narrative generation."""

    name: str
    """Character name or identifier."""

    role: str
    """Character role (protagonist, antagonist, etc.)."""

    personality: list[str]
    """Personality traits."""

    background: str
    """Character background."""

    relationships: dict[str, str]
    """Relationships with other characters."""

    emotional_arc: list[str]
    """Emotional journey throughout the story."""

    key_scenes: list[dict[str, Any]]
    """Key scenes involving this character."""

    voice_characteristics: dict[str, str]
    """Narrative voice characteristics."""


@dataclass
class NarrativeSegment:
    """A segment of first-person narrative."""

    start_time: float
    """Segment start time in seconds."""

    end_time: float
    """Segment end time in seconds."""

    narrator: str
    """Character providing the narration."""

    perspective: NarrativePerspective
    """Narrative perspective used."""

    content: str
    """Narrative content."""

    inner_thoughts: str
    """Character's inner thoughts."""

    emotional_state: str
    """Character's emotional state."""

    scene_context: str
    """Context of the scene being narrated."""

    narrative_techniques: list[str]
    """Narrative techniques used."""


@dataclass
class NarrativeScript:
    """Complete first-person narrative script."""

    title: str
    """Narrative title."""

    perspective: NarrativePerspective
    """Primary narrative perspective."""

    main_narrator: str
    """Main narrator character."""

    segments: list[NarrativeSegment]
    """Narrative segments."""

    character_profiles: list[Character]
    """Character profiles used."""

    narrative_style: str
    """Overall narrative style."""

    themes: list[str]
    """Narrative themes."""

    total_duration: float
    """Total narrative duration."""

    metadata: dict[str, Any]
    """Additional metadata."""


class NarrativeGenerator:
    """Generator for first-person narrative commentary."""

    # Narrative style configurations
    NARRATIVE_STYLES = {
        "introspective": {
            "name": "内心独白式",
            "description": "深入角色内心，展现思想和情感",
            "techniques": ["内心独白", "情感剖析", "回忆闪回", "心理描写"],
            "tone": "深沉、内省、真实",
            "focus": "角色心理变化和成长"
        },
        "confessional": {
            "name": "告白倾诉式",
            "description": "以告白的方式向观众倾诉",
            "techniques": ["直接告白", "情感倾诉", "秘密分享", "真心话"],
            "tone": "真诚、亲密、坦率",
            "focus": "情感表达和观众连接"
        },
        "reflective": {
            "name": "回顾反思式",
            "description": "回顾过往，反思人生经历",
            "techniques": ["时间跳跃", "对比反思", "经验总结", "智慧分享"],
            "tone": "成熟、睿智、感悟",
            "focus": "人生感悟和成长启示"
        },
        "dramatic": {
            "name": "戏剧化叙述",
            "description": "戏剧性强，情感起伏大",
            "techniques": ["情感爆发", "戏剧冲突", "紧张悬念", "高潮迭起"],
            "tone": "激烈、紧张、引人入胜",
            "focus": "戏剧冲突和情节张力"
        },
        "intimate": {
            "name": "亲密对话式",
            "description": "像朋友间的亲密对话",
            "techniques": ["日常对话", "亲密分享", "幽默调侃", "温暖陪伴"],
            "tone": "温暖、亲切、贴近",
            "focus": "情感共鸣和陪伴感"
        }
    }

    def __init__(self, llm_client: BaseLLMClient):
        """
        Initialize narrative generator.

        Args:
            llm_client: LLM client for text generation
        """
        self.llm_client = llm_client
        self.logger = get_logger("features.narrative")

    async def generate_narrative(
        self,
        video_path: Union[str, Path],
        perspective: NarrativePerspective = NarrativePerspective.PROTAGONIST,
        narrative_style: str = "introspective",
        target_character: Optional[str] = None,
        custom_character_info: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> NarrativeScript:
        """
        Generate first-person narrative script for a short drama video.

        Args:
            video_path: Path to the video file
            perspective: Narrative perspective to use
            narrative_style: Style of narration
            target_character: Specific character to focus on
            custom_character_info: Custom character information
            **kwargs: Additional generation parameters

        Returns:
            Generated narrative script

        Raises:
            ValueError: If video file is invalid or parameters are unsupported
            LLMError: If text generation fails
        """
        video_path = Path(video_path)

        # Validate video file
        if not validate_video_file(video_path):
            raise ValueError(f"Invalid video file: {video_path}")

        # Validate narrative style
        if narrative_style not in self.NARRATIVE_STYLES:
            raise ValueError(f"Unsupported narrative style: {narrative_style}")

        self.logger.info(f"Generating {perspective.value} narrative for {video_path.name}")

        # Analyze characters and story
        characters = await self._analyze_characters(video_path, custom_character_info)

        # Select main narrator
        main_narrator = self._select_narrator(characters, perspective, target_character)

        # Generate narrative script
        script = await self._generate_narrative_script(
            video_path=video_path,
            characters=characters,
            main_narrator=main_narrator,
            perspective=perspective,
            narrative_style=narrative_style,
            **kwargs
        )

        self.logger.info(f"Generated narrative script with {len(script.segments)} segments")
        return script

    async def _analyze_characters(
        self,
        video_path: Path,
        custom_info: Optional[dict[str, Any]] = None
    ) -> list[Character]:
        """
        Analyze characters in the video.

        Args:
            video_path: Path to video file
            custom_info: Custom character information

        Returns:
            List of analyzed characters
        """
        # Build character analysis prompt
        prompt = self._build_character_analysis_prompt(video_path, custom_info)

        # Generate analysis
        params = GenerationParams(max_tokens=1500, temperature=0.3)
        response = await self.llm_client.generate(prompt, params)

        # Parse characters from response
        characters = self._parse_characters_response(response.text)

        return characters

    def _build_character_analysis_prompt(
        self,
        video_path: Path,
        custom_info: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for character analysis.

        Args:
            video_path: Video file path
            custom_info: Custom character information

        Returns:
            Character analysis prompt
        """
        prompt = f"""
请分析短剧视频《{video_path.stem}》中的主要角色，为第一人称叙述做准备。

## 分析要求
请深入分析每个主要角色的：
1. 基本信息（姓名、角色定位）
2. 性格特征和行为模式
3. 情感变化和心理状态
4. 人物关系和互动方式
5. 叙述声音特点

"""

        if custom_info:
            prompt += f"## 已知角色信息\n{json.dumps(custom_info, ensure_ascii=False, indent=2)}\n\n"

        prompt += """
## 输出格式
请按以下JSON格式输出角色分析：

```json
{
    "characters": [
        {
            "name": "角色名称",
            "role": "protagonist/antagonist/supporting",
            "personality": ["性格特征1", "性格特征2"],
            "background": "角色背景描述",
            "relationships": {
                "其他角色": "关系描述"
            },
            "emotional_arc": ["初始状态", "发展过程", "最终状态"],
            "key_scenes": [
                {
                    "scene": "场景描述",
                    "emotion": "情感状态",
                    "significance": "重要性"
                }
            ],
            "voice_characteristics": {
                "tone": "叙述语调",
                "style": "表达风格",
                "vocabulary": "用词特点",
                "perspective": "视角特点"
            }
        }
    ],
    "story_summary": "故事概要",
    "main_themes": ["主题1", "主题2"],
    "narrative_potential": "第一人称叙述的潜力分析"
}
```

请确保：
1. 角色分析深入且准确
2. 叙述声音特点鲜明
3. 适合第一人称叙述
4. 体现角色的独特性

开始分析：
"""

        return prompt.strip()

    def _parse_characters_response(self, response_text: str) -> list[Character]:
        """
        Parse LLM response into character objects.

        Args:
            response_text: Raw LLM response

        Returns:
            List of parsed characters
        """
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)

            characters = []
            for char_data in data.get("characters", []):
                character = Character(
                    name=char_data.get("name", "Unknown"),
                    role=char_data.get("role", "supporting"),
                    personality=char_data.get("personality", []),
                    background=char_data.get("background", ""),
                    relationships=char_data.get("relationships", {}),
                    emotional_arc=char_data.get("emotional_arc", []),
                    key_scenes=char_data.get("key_scenes", []),
                    voice_characteristics=char_data.get("voice_characteristics", {})
                )
                characters.append(character)

            return characters

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse characters response: {e}")

            # Fallback: create basic character
            return [
                Character(
                    name="主角",
                    role="protagonist",
                    personality=["复杂", "有深度"],
                    background="故事主人公",
                    relationships={},
                    emotional_arc=["开始", "发展", "结束"],
                    key_scenes=[],
                    voice_characteristics={
                        "tone": "真诚",
                        "style": "内省",
                        "vocabulary": "日常",
                        "perspective": "第一人称"
                    }
                )
            ]

    def _select_narrator(
        self,
        characters: list[Character],
        perspective: NarrativePerspective,
        target_character: Optional[str] = None
    ) -> str:
        """
        Select the main narrator based on perspective and characters.

        Args:
            characters: Available characters
            perspective: Desired perspective
            target_character: Specific character to use

        Returns:
            Selected narrator name
        """
        if target_character:
            # Use specified character if available
            for char in characters:
                if char.name == target_character:
                    return char.name

        # Select based on perspective
        if perspective == NarrativePerspective.PROTAGONIST:
            for char in characters:
                if char.role == "protagonist":
                    return char.name
        elif perspective == NarrativePerspective.ANTAGONIST:
            for char in characters:
                if char.role == "antagonist":
                    return char.name
        elif perspective == NarrativePerspective.SUPPORTING:
            for char in characters:
                if char.role == "supporting":
                    return char.name

        # Fallback to first character
        return characters[0].name if characters else "Unknown"

    async def _generate_narrative_script(
        self,
        video_path: Path,
        characters: list[Character],
        main_narrator: str,
        perspective: NarrativePerspective,
        narrative_style: str,
        **kwargs
    ) -> NarrativeScript:
        """
        Generate the complete narrative script.

        Args:
            video_path: Video file path
            characters: Character information
            main_narrator: Main narrator character
            perspective: Narrative perspective
            narrative_style: Narrative style
            **kwargs: Additional parameters

        Returns:
            Generated narrative script
        """
        style_config = self.NARRATIVE_STYLES[narrative_style]

        # Find narrator character
        narrator_char = None
        for char in characters:
            if char.name == main_narrator:
                narrator_char = char
                break

        if not narrator_char:
            narrator_char = characters[0] if characters else None

        # Build narrative generation prompt
        prompt = self._build_narrative_prompt(
            video_path, narrator_char, style_config, perspective
        )

        # Generate narrative
        params = GenerationParams(
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.8),
            top_p=kwargs.get("top_p", 0.9),
        )

        response = await self.llm_client.generate(prompt, params)

        # Parse narrative script
        script = self._parse_narrative_response(
            response.text, characters, main_narrator, perspective, narrative_style
        )

        return script

    def _build_narrative_prompt(
        self,
        video_path: Path,
        narrator_char: Optional[Character],
        style_config: dict[str, Any],
        perspective: NarrativePerspective
    ) -> str:
        """Build prompt for narrative generation."""
        char_info = ""
        if narrator_char:
            char_info = f"""
## 叙述者角色信息
- 姓名：{narrator_char.name}
- 角色定位：{narrator_char.role}
- 性格特征：{', '.join(narrator_char.personality)}
- 叙述特点：{narrator_char.voice_characteristics}
"""

        prompt = f"""
请为短剧视频《{video_path.stem}》创作第一人称叙述解说。

{char_info}

## 叙述要求
- 视角：{perspective.value}（{self._get_perspective_description(perspective)}）
- 风格：{style_config['name']} - {style_config['description']}
- 叙述技巧：{', '.join(style_config['techniques'])}
- 语调：{style_config['tone']}
- 重点：{style_config['focus']}

## 输出格式
请按以下JSON格式输出叙述脚本：

```json
{{
    "title": "叙述标题",
    "segments": [
        {{
            "start_time": 0,
            "end_time": 30,
            "narrator": "叙述者名称",
            "content": "第一人称叙述内容",
            "inner_thoughts": "内心想法",
            "emotional_state": "情感状态",
            "scene_context": "场景背景",
            "narrative_techniques": ["使用的叙述技巧"]
        }}
    ],
    "narrative_style": "整体叙述风格",
    "themes": ["叙述主题"],
    "character_voice": "角色声音特色描述"
}}
```

请确保：
1. 真实的第一人称视角和语调
2. 符合角色性格和背景
3. 运用指定的叙述技巧
4. 情感真挚，引起共鸣
5. 适合短视频观看习惯

开始创作第一人称叙述：
"""

        return prompt.strip()

    def _get_perspective_description(self, perspective: NarrativePerspective) -> str:
        """Get description for perspective type."""
        descriptions = {
            NarrativePerspective.PROTAGONIST: "主角视角，以主人公的身份讲述",
            NarrativePerspective.ANTAGONIST: "反派视角，从对立角色的角度叙述",
            NarrativePerspective.SUPPORTING: "配角视角，以旁观者或参与者身份叙述",
            NarrativePerspective.OBSERVER: "观察者视角，以第三方观察者身份叙述",
            NarrativePerspective.MULTIPLE: "多角色视角，在不同角色间切换"
        }
        return descriptions.get(perspective, "未知视角")

    def _parse_narrative_response(
        self,
        response_text: str,
        characters: list[Character],
        main_narrator: str,
        perspective: NarrativePerspective,
        narrative_style: str
    ) -> NarrativeScript:
        """Parse LLM response into narrative script."""
        try:
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")

            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)

            # Parse segments
            segments = []
            total_duration = 0.0

            for seg_data in data.get("segments", []):
                segment = NarrativeSegment(
                    start_time=seg_data.get("start_time", 0),
                    end_time=seg_data.get("end_time", 0),
                    narrator=seg_data.get("narrator", main_narrator),
                    perspective=perspective,
                    content=seg_data.get("content", ""),
                    inner_thoughts=seg_data.get("inner_thoughts", ""),
                    emotional_state=seg_data.get("emotional_state", ""),
                    scene_context=seg_data.get("scene_context", ""),
                    narrative_techniques=seg_data.get("narrative_techniques", [])
                )
                segments.append(segment)
                total_duration = max(total_duration, segment.end_time)

            return NarrativeScript(
                title=data.get("title", "第一人称叙述"),
                perspective=perspective,
                main_narrator=main_narrator,
                segments=segments,
                character_profiles=characters,
                narrative_style=narrative_style,
                themes=data.get("themes", []),
                total_duration=total_duration,
                metadata={
                    "character_voice": data.get("character_voice", ""),
                    "segments_count": len(segments),
                    "style_config": self.NARRATIVE_STYLES[narrative_style]
                }
            )

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse narrative response: {e}")

            # Fallback: create basic script
            return NarrativeScript(
                title="第一人称叙述",
                perspective=perspective,
                main_narrator=main_narrator,
                segments=[
                    NarrativeSegment(
                        start_time=0,
                        end_time=60,
                        narrator=main_narrator,
                        perspective=perspective,
                        content=response_text[:500] + "..." if len(response_text) > 500 else response_text,
                        inner_thoughts="",
                        emotional_state="neutral",
                        scene_context="",
                        narrative_techniques=[]
                    )
                ],
                character_profiles=characters,
                narrative_style=narrative_style,
                themes=[],
                total_duration=60.0,
                metadata={"fallback_parsing": True}
            )
