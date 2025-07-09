"""
AI导演模块 - 智能剪映操控和自动化编辑。

本模块通过大模型API实现智能视频编辑决策，
自动生成剪映草稿并执行复杂的编辑操作。
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from ..llm.base import BaseLLMClient, GenerationParams
from ..utils.logging import get_logger
from ..video.draft import JianYingDraftManager
from ..video.processor import VideoInfo, VideoProcessor


@dataclass
class EditingDecision:
    """编辑决策。"""

    action: str
    """操作类型(cut, merge, add_effect, add_subtitle等)。"""

    target: str
    """目标对象(video, audio, subtitle)。"""

    parameters: dict[str, Any]
    """操作参数。"""

    confidence: float
    """决策置信度。"""

    reasoning: str
    """决策理由。"""


@dataclass
class EditingPlan:
    """编辑计划。"""

    project_name: str
    """项目名称。"""

    objective: str
    """编辑目标。"""

    decisions: list[EditingDecision]
    """编辑决策列表。"""

    estimated_duration: float
    """预估时长。"""

    complexity_score: float
    """复杂度评分。"""


class AIDirector:
    """AI导演 - 智能视频编辑决策引擎。"""

    def __init__(
        self,
        llm_client: BaseLLMClient,
        draft_manager: JianYingDraftManager,
        video_processor: VideoProcessor
    ):
        """
        初始化AI导演。

        Args:
            llm_client: 大模型客户端
            draft_manager: 草稿管理器
            video_processor: 视频处理器
        """
        self.llm_client = llm_client
        self.draft_manager = draft_manager
        self.video_processor = video_processor
        self.logger = get_logger("ai.director")

        self.logger.info("AI导演已初始化")

    async def analyze_video_content(
        self,
        video_path: Union[str, Path],
        analysis_depth: str = "detailed"
    ) -> dict[str, Any]:
        """
        分析视频内容，为编辑决策提供基础。

        Args:
            video_path: 视频文件路径
            analysis_depth: 分析深度(basic, detailed, comprehensive)

        Returns:
            视频分析结果
        """
        video_path = Path(video_path)
        self.logger.info(f"分析视频内容: {video_path}")

        # 获取基础视频信息
        video_info = self.video_processor.get_video_info(video_path)

        # 场景检测
        scenes = self.video_processor.detect_scenes(video_path)

        # 使用大模型分析视频内容
        analysis_prompt = self._build_video_analysis_prompt(
            video_info, scenes, analysis_depth
        )

        params = GenerationParams(max_tokens=2000, temperature=0.3)
        response = await self.llm_client.generate(analysis_prompt, params)

        # 解析分析结果
        analysis_result = self._parse_analysis_response(response.text, video_info, scenes)

        return analysis_result

    def _build_video_analysis_prompt(
        self,
        video_info: VideoInfo,
        scenes: list[Any],
        analysis_depth: str
    ) -> str:
        """构建视频分析提示词。"""
        scene_count = len(scenes)
        width, height = video_info.resolution
        prompt = f"""
作为专业的视频编辑AI导演，请分析以下短剧视频的内容特征：

## 视频基础信息
- 文件路径: {video_info.path.name}
- 时长: {video_info.duration:.1f}秒
- 分辨率: {width}x{height}
- 帧率: {video_info.fps}fps
- 文件大小: {video_info.size_mb:.1f}MB

## 场景信息
检测到 {scene_count} 个场景：
"""

        for i, scene in enumerate(scenes[:5]):  # 只显示前5个场景
            scene_num = i + 1
            prompt += f"- 场景{scene_num}: {scene.start_time:.1f}s-{scene.end_time:.1f}s, 亮度:{scene.average_brightness:.2f}, 运动强度:{scene.motion_intensity:.2f}\n"

        if analysis_depth == "comprehensive":
            prompt += """
## 分析要求 (综合分析)
请从以下维度深度分析视频内容：

1. **内容类型识别**
   - 短剧类型(都市、古装、悬疑、喜剧等)
   - 情节发展阶段(开头、发展、高潮、结局)
   - 主要角色数量和特征

2. **视觉特征分析**
   - 画面构图风格
   - 色彩基调和情绪表达
   - 镜头运动特点
   - 场景转换节奏

3. **编辑建议**
   - 适合的剪辑风格
   - 推荐的特效类型
   - 字幕添加建议
   - 音乐配乐建议

4. **观众吸引力评估**
   - 内容亮点识别
   - 潜在的观众群体
   - 传播价值评估
"""
        elif analysis_depth == "detailed":
            prompt += """
## 分析要求 (详细分析)
请分析以下关键要素：

1. **内容特征**
   - 短剧主题和类型
   - 情节关键节点
   - 角色关系

2. **技术特征**
   - 画面质量评估
   - 音频质量评估
   - 剪辑节奏分析

3. **编辑建议**
   - 剪辑优化建议
   - 特效添加建议
   - 字幕处理建议
"""
        else:  # basic
            prompt += """
## 分析要求 (基础分析)
请提供以下基础分析：

1. **内容概述**
   - 视频主要内容
   - 情节简述

2. **技术评估**
   - 画面和音频质量
   - 基础编辑建议
"""

        prompt += """
## 输出格式
请按以下JSON格式输出分析结果：

```json
{
    "content_type": "短剧类型",
    "theme": "主题描述",
    "plot_summary": "情节概述",
    "characters": ["角色1", "角色2"],
    "visual_style": {
        "composition": "构图风格",
        "color_tone": "色彩基调",
        "camera_movement": "镜头运动"
    },
    "technical_quality": {
        "video_quality": "画面质量评分(1-10)",
        "audio_quality": "音频质量评分(1-10)",
        "editing_rhythm": "剪辑节奏评价"
    },
    "editing_suggestions": {
        "style": "推荐剪辑风格",
        "effects": ["推荐特效1", "推荐特效2"],
        "subtitle_style": "字幕风格建议",
        "music_style": "配乐风格建议"
    },
    "highlights": ["亮点1", "亮点2"],
    "target_audience": "目标观众群体",
    "viral_potential": "传播潜力评分(1-10)"
}
```

请基于视频的实际特征进行专业分析。
"""

        return prompt.strip()

    def _parse_analysis_response(
        self,
        response_text: str,
        video_info: VideoInfo,
        scenes: list[Any]
    ) -> dict[str, Any]:
        """解析视频分析响应。"""
        try:
            # 提取JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                analysis_data = json.loads(json_text)
            else:
                # 如果没有找到JSON，创建基础分析
                analysis_data = {
                    "content_type": "短剧",
                    "theme": "未知主题",
                    "plot_summary": "需要进一步分析",
                    "characters": [],
                    "visual_style": {},
                    "technical_quality": {},
                    "editing_suggestions": {},
                    "highlights": [],
                    "target_audience": "通用观众",
                    "viral_potential": 5
                }

            # 添加技术信息
            analysis_data["technical_info"] = {
                "duration": video_info.duration,
                "resolution": video_info.resolution,
                "fps": video_info.fps,
                "file_size_mb": video_info.size_mb,
                "scene_count": len(scenes)
            }

            return analysis_data

        except json.JSONDecodeError as e:
            self.logger.warning(f"解析分析响应失败: {e}")
            return {
                "content_type": "短剧",
                "theme": "解析失败",
                "error": str(e),
                "technical_info": {
                    "duration": video_info.duration,
                    "resolution": video_info.resolution,
                    "fps": video_info.fps,
                    "file_size_mb": video_info.size_mb,
                    "scene_count": len(scenes)
                }
            }

    async def create_editing_plan(
        self,
        video_analysis: dict[str, Any],
        editing_objective: str,
        style_preferences: Optional[dict[str, Any]] = None
    ) -> EditingPlan:
        """
        基于视频分析创建编辑计划。

        Args:
            video_analysis: 视频分析结果
            editing_objective: 编辑目标
            style_preferences: 风格偏好

        Returns:
            编辑计划
        """
        self.logger.info(f"创建编辑计划: {editing_objective}")

        # 构建编辑计划提示词
        plan_prompt = self._build_editing_plan_prompt(
            video_analysis, editing_objective, style_preferences
        )

        params = GenerationParams(max_tokens=2500, temperature=0.5)
        response = await self.llm_client.generate(plan_prompt, params)

        # 解析编辑计划
        editing_plan = self._parse_editing_plan_response(
            response.text, editing_objective
        )

        return editing_plan

    def _build_editing_plan_prompt(
        self,
        video_analysis: dict[str, Any],
        editing_objective: str,
        style_preferences: Optional[dict[str, Any]]
    ) -> str:
        """构建编辑计划提示词。"""
        analysis_json = json.dumps(video_analysis, ensure_ascii=False, indent=2)
        style_json = json.dumps(style_preferences or {}, ensure_ascii=False, indent=2)

        prompt = f"""
作为专业的视频编辑AI导演，请基于视频分析结果制定详细的编辑计划。

## 视频分析结果
{analysis_json}

## 编辑目标
{editing_objective}

## 风格偏好
{style_json}

## 编辑计划要求
请制定一个详细的编辑计划，包含具体的编辑操作步骤：

1. **项目规划**
   - 确定项目名称
   - 设定编辑目标
   - 评估复杂度

2. **编辑决策**
   - 剪切和合并操作
   - 特效添加
   - 字幕处理
   - 音频调整
   - 转场效果

3. **质量控制**
   - 每个决策的置信度
   - 决策理由说明

## 输出格式
请按以下JSON格式输出编辑计划：

```json
{{
    "project_name": "项目名称",
    "objective": "编辑目标描述",
    "estimated_duration": 预估时长秒数,
    "complexity_score": 复杂度评分1-10,
    "decisions": [
        {{
            "action": "操作类型",
            "target": "目标对象",
            "parameters": {{
                "具体参数": "参数值"
            }},
            "confidence": 置信度0-1,
            "reasoning": "决策理由"
        }}
    ]
}}
```

可用的操作类型包括：
- cut: 剪切视频片段
- merge: 合并视频片段
- add_effect: 添加特效
- add_subtitle: 添加字幕
- adjust_audio: 调整音频
- add_transition: 添加转场
- color_correction: 色彩校正
- speed_adjustment: 速度调整

请确保编辑计划具有可执行性和专业性。
"""

        return prompt.strip()

    def _parse_editing_plan_response(
        self,
        response_text: str,
        editing_objective: str
    ) -> EditingPlan:
        """解析编辑计划响应。"""
        try:
            # 提取JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                plan_data = json.loads(json_text)
            else:
                # 创建基础计划
                plan_data = {
                    "project_name": "AI编辑项目",
                    "objective": editing_objective,
                    "estimated_duration": 60.0,
                    "complexity_score": 5.0,
                    "decisions": []
                }

            # 解析编辑决策
            decisions = []
            for decision_data in plan_data.get("decisions", []):
                decision = EditingDecision(
                    action=decision_data.get("action", "unknown"),
                    target=decision_data.get("target", "video"),
                    parameters=decision_data.get("parameters", {}),
                    confidence=decision_data.get("confidence", 0.5),
                    reasoning=decision_data.get("reasoning", "AI决策")
                )
                decisions.append(decision)

            return EditingPlan(
                project_name=plan_data.get("project_name", "AI编辑项目"),
                objective=plan_data.get("objective", editing_objective),
                decisions=decisions,
                estimated_duration=plan_data.get("estimated_duration", 60.0),
                complexity_score=plan_data.get("complexity_score", 5.0)
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"解析编辑计划失败: {e}")
            return EditingPlan(
                project_name="AI编辑项目",
                objective=editing_objective,
                decisions=[],
                estimated_duration=60.0,
                complexity_score=1.0
            )

    async def execute_editing_plan(
        self,
        editing_plan: EditingPlan,
        source_videos: list[Union[str, Path]],
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        执行编辑计划，生成剪映草稿。

        Args:
            editing_plan: 编辑计划
            source_videos: 源视频文件列表
            output_dir: 输出目录

        Returns:
            生成的草稿文件路径
        """
        self.logger.info(f"执行编辑计划: {editing_plan.project_name}")

        # 准备视频片段
        video_clips = []
        for _i, video_path in enumerate(source_videos):
            video_info = self.video_processor.get_video_info(video_path)
            clip = {
                "path": str(video_path),
                "duration": int(video_info.duration * 1000),  # 转换为毫秒
                "width": video_info.resolution[0],
                "height": video_info.resolution[1],
                "start_time": 0,
                "end_time": int(video_info.duration * 1000)
            }
            video_clips.append(clip)

        # 处理编辑决策
        audio_clips = []
        subtitles = []
        effects = []

        for decision in editing_plan.decisions:
            if decision.action == "add_subtitle":
                subtitle = {
                    "text": decision.parameters.get("text", "字幕文本"),
                    "start_time": decision.parameters.get("start_time", 0),
                    "duration": decision.parameters.get("duration", 2000),
                    "style": decision.parameters.get("style", {})
                }
                subtitles.append(subtitle)

            elif decision.action == "add_effect":
                effect = {
                    "type": decision.parameters.get("type", "fade"),
                    "start_time": decision.parameters.get("start_time", 0),
                    "end_time": decision.parameters.get("end_time", 1000),
                    "parameters": decision.parameters
                }
                effects.append(effect)

        # 创建剪映草稿
        draft_file = self.draft_manager.create_draft(
            project_name=editing_plan.project_name,
            video_clips=video_clips,
            audio_clips=audio_clips if audio_clips else None,
            subtitles=subtitles if subtitles else None,
            effects=effects if effects else None
        )

        self.logger.info(f"编辑计划执行完成，草稿文件: {draft_file}")
        return draft_file

    async def smart_edit_workflow(
        self,
        video_paths: list[Union[str, Path]],
        editing_objective: str,
        style_preferences: Optional[dict[str, Any]] = None,
        auto_import: bool = False
    ) -> dict[str, Any]:
        """
        智能编辑工作流程 - 一键完成从分析到草稿生成。

        Args:
            video_paths: 视频文件路径列表
            editing_objective: 编辑目标
            style_preferences: 风格偏好
            auto_import: 是否自动导入到剪映

        Returns:
            工作流程结果
        """
        self.logger.info(f"开始智能编辑工作流程: {editing_objective}")

        workflow_result = {
            "success": False,
            "video_analyses": [],
            "editing_plan": None,
            "draft_file": None,
            "imported_to_jianying": False,
            "error": None
        }

        try:
            # 1. 分析所有视频
            for video_path in video_paths:
                analysis = await self.analyze_video_content(video_path, "detailed")
                workflow_result["video_analyses"].append(analysis)

            # 2. 创建编辑计划
            # 使用第一个视频的分析结果作为主要参考
            main_analysis = workflow_result["video_analyses"][0]
            editing_plan = await self.create_editing_plan(
                main_analysis, editing_objective, style_preferences
            )
            workflow_result["editing_plan"] = editing_plan

            # 3. 执行编辑计划
            draft_file = await self.execute_editing_plan(editing_plan, video_paths)
            workflow_result["draft_file"] = str(draft_file)

            # 4. 自动导入到剪映（如果启用）
            if auto_import:
                imported = self.draft_manager.import_to_jianying(draft_file)
                workflow_result["imported_to_jianying"] = imported

            workflow_result["success"] = True
            self.logger.info("智能编辑工作流程完成")

        except Exception as e:
            self.logger.error(f"智能编辑工作流程失败: {e}")
            workflow_result["error"] = str(e)

        return workflow_result
