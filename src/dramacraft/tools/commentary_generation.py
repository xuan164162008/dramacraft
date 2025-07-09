"""
解说生成工具 - 为单个视频生成AI解说文案
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    from mcp import Tool
except ImportError:
    from ..server import Tool

from ..config.json_schemas import CommentaryGenerationConfig
from ..features.commentary import CommentaryGenerator
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CommentaryResult:
    """解说生成结果"""
    commentary_text: str
    segments: list
    total_duration: float
    segment_count: int
    style_score: float
    output_path: Optional[str] = None


class CommentaryGenerationTool:
    """解说生成工具"""

    def __init__(self):
        self.generator = CommentaryGenerator()

    @staticmethod
    def get_tool_definition() -> Tool:
        """获取工具定义"""
        return Tool(
            name="generate_commentary",
            description="🎤 智能解说生成 - 为单个视频生成AI解说文案（辅助功能）",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "视频文件路径，如：'视频文件.mp4'"
                    },
                    "style": {
                        "type": "string",
                        "enum": ["humorous", "professional", "dramatic", "suspense", "romantic", "action"],
                        "default": "humorous",
                        "description": "解说风格：humorous(搞笑)/professional(专业)/dramatic(戏剧性)"
                    },
                    "target_audience": {
                        "type": "string",
                        "enum": ["年轻人", "青少年", "中年人", "大众", "专业人士"],
                        "default": "年轻人",
                        "description": "目标受众"
                    },
                    "include_intro": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含开场白"
                    },
                    "include_interaction": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含互动元素"
                    },
                    "include_outro": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含结尾"
                    },
                    "commentary_length": {
                        "type": "string",
                        "enum": ["auto", "short", "medium", "long"],
                        "default": "auto",
                        "description": "解说长度：auto(自动)/short(短)/medium(中)/long(长)"
                    },
                    "emotion_emphasis": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.7,
                        "description": "情感强调程度(0-1)"
                    },
                    "humor_level": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "default": 0.8,
                        "description": "幽默程度(0-1)"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "srt", "vtt"],
                        "default": "text",
                        "description": "输出格式：text(纯文本)/srt(字幕)/vtt(WebVTT)"
                    },
                    "output_dir": {
                        "type": "string",
                        "default": "./output",
                        "description": "输出目录"
                    }
                },
                "required": ["video_path"]
            }
        )

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行解说生成"""
        try:
            # 验证参数
            config = CommentaryGenerationConfig(**params)

            # 检查视频文件
            video_path = Path(config.video_path)
            if not video_path.exists():
                return {
                    "type": "text",
                    "text": f"❌ 解说生成失败：视频文件不存在 - {video_path}"
                }

            logger.info(f"开始为视频生成解说: {video_path}")

            # 生成解说
            result = await self._generate_commentary(config)

            # 返回成功结果
            return {
                "type": "text",
                "text": f"""✅ 解说生成完成！

📹 **视频文件**: {config.video_path}
🎤 **解说风格**: {config.style}
👥 **目标受众**: {config.target_audience}
⏱️ **总时长**: {result.total_duration:.1f}秒
📝 **片段数量**: {result.segment_count}个
⭐ **风格评分**: {result.style_score:.2f}

📄 **解说内容预览**:
{result.commentary_text[:200]}...

💾 **输出文件**: {result.output_path or '内存中'}

🎯 **使用建议**:
- 可以配合 `create_jianying_draft` 工具创建剪映项目
- 可以调整 `humor_level` 和 `emotion_emphasis` 参数优化效果
"""
            }

        except Exception as e:
            logger.error(f"解说生成失败: {e}")
            return {
                "type": "text",
                "text": f"❌ 解说生成失败: {str(e)}"
            }

    async def _generate_commentary(self, config: CommentaryGenerationConfig) -> CommentaryResult:
        """生成解说内容"""

        # 分析视频内容
        video_analysis = await self.generator.analyze_video_content(
            video_path=Path(config.video_path)
        )

        # 生成解说文案
        commentary_data = await self.generator.generate_commentary(
            analysis=video_analysis,
            style=config.style,
            target_audience=config.target_audience,
            include_intro=config.include_intro,
            include_interaction=config.include_interaction,
            include_outro=config.include_outro,
            emotion_emphasis=config.emotion_emphasis,
            humor_level=config.humor_level
        )

        # 创建输出目录
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存解说文件
        output_path = None
        if config.output_format == "text":
            output_path = output_dir / f"{Path(config.video_path).stem}_commentary.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(commentary_data.full_text)
        elif config.output_format == "srt":
            output_path = output_dir / f"{Path(config.video_path).stem}_commentary.srt"
            srt_content = self._generate_srt(commentary_data.segments)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
        elif config.output_format == "vtt":
            output_path = output_dir / f"{Path(config.video_path).stem}_commentary.vtt"
            vtt_content = self._generate_vtt(commentary_data.segments)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(vtt_content)

        return CommentaryResult(
            commentary_text=commentary_data.full_text,
            segments=commentary_data.segments,
            total_duration=video_analysis.duration,
            segment_count=len(commentary_data.segments),
            style_score=commentary_data.style_score,
            output_path=str(output_path) if output_path else None
        )

    def _generate_srt(self, segments: list) -> str:
        """生成SRT字幕格式"""
        srt_lines = []
        for i, segment in enumerate(segments, 1):
            start_time = self._format_srt_time(segment.get('start_time', 0))
            end_time = self._format_srt_time(segment.get('end_time', 0))
            text = segment.get('text', '')

            srt_lines.extend([
                str(i),
                f"{start_time} --> {end_time}",
                text,
                ""
            ])

        return "\n".join(srt_lines)

    def _generate_vtt(self, segments: list) -> str:
        """生成WebVTT字幕格式"""
        vtt_lines = ["WEBVTT", ""]

        for segment in segments:
            start_time = self._format_vtt_time(segment.get('start_time', 0))
            end_time = self._format_vtt_time(segment.get('end_time', 0))
            text = segment.get('text', '')

            vtt_lines.extend([
                f"{start_time} --> {end_time}",
                text,
                ""
            ])

        return "\n".join(vtt_lines)

    def _format_srt_time(self, seconds: float) -> str:
        """格式化SRT时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _format_vtt_time(self, seconds: float) -> str:
        """格式化WebVTT时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
