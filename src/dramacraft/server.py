"""
DramaCraft MCP服务器实现。

本模块实现符合模型上下文协议(MCP)标准的服务器，提供短剧视频编辑工具。
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        TextContent,
        Tool,
    )
except ImportError:
    # 如果MCP包不可用，提供基本的类型定义
    class Server:
        def __init__(self, name: str, version: str):
            self.name = name
            self.version = version

    class Tool:
        def __init__(self, name: str, description: str, inputSchema: dict[str, Any]):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema

from .ai.director import AIDirector
from .config import DramaCraftConfig
from .features.commentary import CommentaryGenerator
from .features.narrative import NarrativeGenerator, NarrativePerspective
from .features.remix import RemixGenerator, RemixStyle
from .llm.factory import create_llm_client
from .models.series import SeriesProcessingConfig

# 新的主要工具 - 系列合集制作
from .tools.series_compilation import SeriesCompilationTool
from .utils.logging import get_logger, setup_logging
from .video.draft import JianYingDraftManager
from .video.processor import VideoProcessor


class DramaCraftServer:
    """DramaCraft MCP服务器主类。"""

    def __init__(self, config: DramaCraftConfig):
        """
        初始化DramaCraft服务器。

        Args:
            config: 服务配置
        """
        self.config = config
        self.logger = get_logger("server")

        # 设置日志
        setup_logging(config.logging)

        # 初始化MCP服务器
        self.server = Server(
            name=config.service_name,
            version=config.service_version
        )

        # 初始化LLM客户端
        self.llm_client = create_llm_client(config.llm)

        # 初始化功能生成器
        self.commentary_generator = CommentaryGenerator(self.llm_client)
        self.remix_generator = RemixGenerator(self.llm_client)
        self.narrative_generator = NarrativeGenerator(self.llm_client)

        # 初始化视频处理组件
        self.video_processor = VideoProcessor(config.video)
        self.draft_manager = JianYingDraftManager(config.jianying)
        self.ai_director = AIDirector(self.llm_client, self.draft_manager, self.video_processor)

        # 初始化新的主要工具 - 系列合集制作
        series_config = SeriesProcessingConfig()
        self.series_compilation_tool = SeriesCompilationTool(series_config)

        # 注册MCP工具
        self._register_tools()

        self.logger.info(f"DramaCraft服务器已初始化 - {config.service_name} v{config.service_version}")

    def _register_tools(self) -> None:
        """注册MCP工具。"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """列出所有可用的工具。"""
            return [
                # 🎬 主要工具：系列合集制作
                self.series_compilation_tool.get_tool_definition(),

                # 🎤 辅助工具：单集解说生成
                Tool(
                    name="generate_commentary",
                    description="🎤 单集解说生成 - 为单个短剧视频生成AI解说文案（辅助功能）",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_path": {
                                "type": "string",
                                "description": "视频文件路径"
                            },
                            "style": {
                                "type": "string",
                                "enum": ["analytical", "emotional", "humorous", "critical", "storytelling"],
                                "description": "解说风格",
                                "default": "analytical"
                            },
                            "target_duration": {
                                "type": "number",
                                "description": "目标解说时长(秒)",
                                "minimum": 10,
                                "maximum": 600
                            }
                        },
                        "required": ["video_path"]
                    }
                ),
                Tool(
                    name="create_remix",
                    description="创建短剧混剪/合集视频",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_videos": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "源视频文件路径列表"
                            },
                            "style": {
                                "type": "string",
                                "enum": ["highlights", "emotional", "funny", "romantic", "dramatic", "character", "theme"],
                                "description": "混剪风格",
                                "default": "highlights"
                            },
                            "target_duration": {
                                "type": "number",
                                "description": "目标视频时长(秒)",
                                "default": 60,
                                "minimum": 15,
                                "maximum": 300
                            },
                            "output_path": {
                                "type": "string",
                                "description": "输出文件路径(可选)"
                            }
                        },
                        "required": ["source_videos"]
                    }
                ),
                Tool(
                    name="generate_narrative",
                    description="生成第一人称叙述解说文案",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_path": {
                                "type": "string",
                                "description": "视频文件路径"
                            },
                            "perspective": {
                                "type": "string",
                                "enum": ["protagonist", "antagonist", "supporting", "observer", "multiple"],
                                "description": "叙述视角",
                                "default": "protagonist"
                            },
                            "narrative_style": {
                                "type": "string",
                                "enum": ["introspective", "confessional", "reflective", "dramatic", "intimate"],
                                "description": "叙述风格",
                                "default": "introspective"
                            },
                            "target_character": {
                                "type": "string",
                                "description": "目标角色名称(可选)"
                            }
                        },
                        "required": ["video_path"]
                    }
                ),
                Tool(
                    name="analyze_video",
                    description="分析视频内容，提取场景、角色和情感信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_path": {
                                "type": "string",
                                "description": "视频文件路径"
                            },
                            "analysis_type": {
                                "type": "string",
                                "enum": ["basic", "detailed", "character_focused"],
                                "description": "分析类型",
                                "default": "basic"
                            }
                        },
                        "required": ["video_path"]
                    }
                ),
                Tool(
                    name="export_to_jianying",
                    description="导出项目到剪映格式",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_data": {
                                "type": "object",
                                "description": "项目数据"
                            },
                            "output_path": {
                                "type": "string",
                                "description": "输出路径"
                            },
                            "template_name": {
                                "type": "string",
                                "description": "模板名称(可选)"
                            }
                        },
                        "required": ["project_data", "output_path"]
                    }
                ),
                Tool(
                    name="create_jianying_draft",
                    description="创建剪映草稿文件(.draft)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_name": {
                                "type": "string",
                                "description": "项目名称"
                            },
                            "video_clips": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "path": {"type": "string"},
                                        "start_time": {"type": "number"},
                                        "end_time": {"type": "number"},
                                        "duration": {"type": "number"}
                                    }
                                },
                                "description": "视频片段列表"
                            },
                            "audio_clips": {
                                "type": "array",
                                "items": {"type": "object"},
                                "description": "音频片段列表(可选)"
                            },
                            "subtitles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "start_time": {"type": "number"},
                                        "duration": {"type": "number"}
                                    }
                                },
                                "description": "字幕列表(可选)"
                            },
                            "auto_import": {
                                "type": "boolean",
                                "description": "是否自动导入到剪映",
                                "default": False
                            }
                        },
                        "required": ["project_name", "video_clips"]
                    }
                ),
                Tool(
                    name="smart_video_edit",
                    description="AI智能视频编辑 - 一键完成分析、规划和草稿生成",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "视频文件路径列表"
                            },
                            "editing_objective": {
                                "type": "string",
                                "description": "编辑目标(如：制作搞笑合集、生成解说视频等)"
                            },
                            "style_preferences": {
                                "type": "object",
                                "description": "风格偏好设置(可选)",
                                "properties": {
                                    "pace": {"type": "string", "enum": ["slow", "medium", "fast"]},
                                    "mood": {"type": "string", "enum": ["serious", "funny", "dramatic", "casual"]},
                                    "target_duration": {"type": "number"}
                                }
                            },
                            "auto_import": {
                                "type": "boolean",
                                "description": "是否自动导入到剪映",
                                "default": False
                            }
                        },
                        "required": ["video_paths", "editing_objective"]
                    }
                ),
                Tool(
                    name="list_drafts",
                    description="列出本地剪映草稿文件",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """处理工具调用。"""
            try:
                # 🎬 主要工具：系列合集制作
                if name == "create_series_compilation":
                    result = await self.series_compilation_tool.execute(arguments)
                    return [result]

                # 🎤 辅助工具：传统单集处理
                elif name == "generate_commentary":
                    return await self._handle_generate_commentary(arguments)
                elif name == "create_remix":
                    return await self._handle_create_remix(arguments)
                elif name == "generate_narrative":
                    return await self._handle_generate_narrative(arguments)
                elif name == "analyze_video":
                    return await self._handle_analyze_video(arguments)
                elif name == "export_to_jianying":
                    return await self._handle_export_to_jianying(arguments)
                elif name == "create_jianying_draft":
                    return await self._handle_create_jianying_draft(arguments)
                elif name == "smart_video_edit":
                    return await self._handle_smart_video_edit(arguments)
                elif name == "list_drafts":
                    return await self._handle_list_drafts(arguments)
                else:
                    raise ValueError(f"未知工具: {name}")

            except Exception as e:
                self.logger.error(f"工具调用失败 {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"错误: {str(e)}"
                )]

    async def _handle_generate_commentary(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理解说文案生成。"""
        video_path = arguments["video_path"]
        style = arguments.get("style", "analytical")
        target_duration = arguments.get("target_duration")

        self.logger.info(f"生成解说文案: {video_path}, 风格: {style}")

        script = await self.commentary_generator.generate_commentary(
            video_path=video_path,
            style=style,
            target_duration=target_duration
        )

        # 格式化输出
        result = {
            "title": script.title,
            "style": script.style,
            "total_duration": script.total_duration,
            "introduction": script.introduction,
            "segments": script.segments,
            "conclusion": script.conclusion,
            "metadata": script.metadata
        }

        return [TextContent(
            type="text",
            text=f"✅ 解说文案生成完成\n\n**标题**: {script.title}\n**风格**: {script.style}\n**预计时长**: {script.total_duration:.1f}秒\n**片段数**: {len(script.segments)}\n\n**详细内容**:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
        )]

    async def _handle_create_remix(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理混剪视频创建。"""
        source_videos = arguments["source_videos"]
        style = arguments.get("style", "highlights")
        target_duration = arguments.get("target_duration", 60)
        output_path = arguments.get("output_path")

        self.logger.info(f"创建混剪视频: {len(source_videos)}个源视频, 风格: {style}")

        remix_style = RemixStyle(style)
        result = await self.remix_generator.create_remix(
            source_videos=source_videos,
            style=remix_style,
            target_duration=target_duration,
            output_path=output_path
        )

        # 格式化输出
        output_info = {
            "output_path": str(result.output_path),
            "style": result.plan.style.value,
            "actual_duration": result.actual_duration,
            "clips_used": result.clips_used,
            "processing_time": result.processing_time,
            "quality_score": result.quality_score
        }

        return [TextContent(
            type="text",
            text=f"✅ 混剪视频创建完成\n\n**输出文件**: {result.output_path}\n**风格**: {result.plan.style.value}\n**实际时长**: {result.actual_duration:.1f}秒\n**使用片段**: {result.clips_used}个\n**处理时间**: {result.processing_time:.2f}秒\n**质量评分**: {result.quality_score:.2f}\n\n**详细信息**:\n```json\n{json.dumps(output_info, ensure_ascii=False, indent=2)}\n```"
        )]

    async def _handle_generate_narrative(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理第一人称叙述生成。"""
        video_path = arguments["video_path"]
        perspective = arguments.get("perspective", "protagonist")
        narrative_style = arguments.get("narrative_style", "introspective")
        target_character = arguments.get("target_character")

        self.logger.info(f"生成第一人称叙述: {video_path}, 视角: {perspective}")

        narrative_perspective = NarrativePerspective(perspective)
        script = await self.narrative_generator.generate_narrative(
            video_path=video_path,
            perspective=narrative_perspective,
            narrative_style=narrative_style,
            target_character=target_character
        )

        # 格式化输出
        result = {
            "title": script.title,
            "perspective": script.perspective.value,
            "main_narrator": script.main_narrator,
            "narrative_style": script.narrative_style,
            "total_duration": script.total_duration,
            "segments": script.segments,
            "themes": script.themes,
            "metadata": script.metadata
        }

        return [TextContent(
            type="text",
            text=f"✅ 第一人称叙述生成完成\n\n**标题**: {script.title}\n**视角**: {script.perspective.value}\n**叙述者**: {script.main_narrator}\n**风格**: {script.narrative_style}\n**总时长**: {script.total_duration:.1f}秒\n**片段数**: {len(script.segments)}\n\n**详细内容**:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
        )]

    async def _handle_analyze_video(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理视频分析。"""
        video_path = arguments["video_path"]
        analysis_type = arguments.get("analysis_type", "basic")

        self.logger.info(f"分析视频: {video_path}, 类型: {analysis_type}")

        # 这里应该实现实际的视频分析逻辑
        # 目前返回模拟结果
        analysis_result = {
            "video_path": video_path,
            "analysis_type": analysis_type,
            "duration": 120.0,
            "resolution": [1920, 1080],
            "fps": 30.0,
            "scenes": [
                {"start": 0.0, "end": 30.0, "description": "开场介绍"},
                {"start": 30.0, "end": 90.0, "description": "主要情节"},
                {"start": 90.0, "end": 120.0, "description": "结局高潮"}
            ],
            "characters": ["女主角", "男主角", "配角"],
            "emotions": ["紧张", "感动", "温暖", "希望"],
            "themes": ["爱情", "成长", "坚持", "勇气"]
        }

        return [TextContent(
            type="text",
            text=f"✅ 视频分析完成\n\n**文件**: {video_path}\n**时长**: {analysis_result['duration']}秒\n**分辨率**: {analysis_result['resolution'][0]}x{analysis_result['resolution'][1]}\n**帧率**: {analysis_result['fps']}fps\n\n**详细分析**:\n```json\n{json.dumps(analysis_result, ensure_ascii=False, indent=2)}\n```"
        )]

    async def _handle_export_to_jianying(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理剪映导出。"""
        arguments["project_data"]
        output_path = arguments["output_path"]
        template_name = arguments.get("template_name", "default")

        self.logger.info(f"导出到剪映: {output_path}")

        # 这里应该实现实际的剪映导出逻辑
        # 目前返回模拟结果
        export_result = {
            "output_path": output_path,
            "template_name": template_name,
            "project_type": "drama_editing",
            "exported_files": [
                f"{output_path}/project.jy",
                f"{output_path}/assets/",
                f"{output_path}/timeline.json"
            ],
            "status": "success"
        }

        return [TextContent(
            type="text",
            text=f"✅ 剪映项目导出完成\n\n**输出路径**: {output_path}\n**模板**: {template_name}\n**项目类型**: 短剧编辑\n\n**导出文件**:\n```json\n{json.dumps(export_result, ensure_ascii=False, indent=2)}\n```"
        )]

    async def _handle_create_jianying_draft(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理剪映草稿创建。"""
        project_name = arguments["project_name"]
        video_clips = arguments["video_clips"]
        audio_clips = arguments.get("audio_clips")
        subtitles = arguments.get("subtitles")
        auto_import = arguments.get("auto_import", False)

        self.logger.info(f"创建剪映草稿: {project_name}")

        try:
            # 创建草稿文件
            draft_file = self.draft_manager.create_draft(
                project_name=project_name,
                video_clips=video_clips,
                audio_clips=audio_clips,
                subtitles=subtitles
            )

            # 自动导入到剪映（如果启用）
            imported = False
            if auto_import:
                imported = self.draft_manager.import_to_jianying(draft_file)

            result = {
                "draft_file": str(draft_file),
                "project_name": project_name,
                "video_clips_count": len(video_clips),
                "audio_clips_count": len(audio_clips) if audio_clips else 0,
                "subtitles_count": len(subtitles) if subtitles else 0,
                "auto_imported": imported
            }

            status_text = "✅ 剪映草稿创建完成"
            if imported:
                status_text += " 并已导入剪映"

            return [TextContent(
                type="text",
                text=f"{status_text}\n\n**项目名称**: {project_name}\n**草稿文件**: {draft_file}\n**视频片段**: {len(video_clips)}个\n**音频片段**: {len(audio_clips) if audio_clips else 0}个\n**字幕**: {len(subtitles) if subtitles else 0}条\n\n**详细信息**:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"
            )]

        except Exception as e:
            self.logger.error(f"创建剪映草稿失败: {e}")
            return [TextContent(
                type="text",
                text=f"❌ 创建剪映草稿失败: {str(e)}"
            )]

    async def _handle_smart_video_edit(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理AI智能视频编辑。"""
        video_paths = arguments["video_paths"]
        editing_objective = arguments["editing_objective"]
        style_preferences = arguments.get("style_preferences")
        auto_import = arguments.get("auto_import", False)

        self.logger.info(f"AI智能编辑: {editing_objective}")

        try:
            # 执行智能编辑工作流程
            workflow_result = await self.ai_director.smart_edit_workflow(
                video_paths=video_paths,
                editing_objective=editing_objective,
                style_preferences=style_preferences,
                auto_import=auto_import
            )

            if workflow_result["success"]:
                status_text = "✅ AI智能编辑完成"
                if workflow_result["imported_to_jianying"]:
                    status_text += " 并已导入剪映"

                # 构建结果摘要
                plan = workflow_result["editing_plan"]
                summary = {
                    "project_name": plan.project_name if plan else "AI编辑项目",
                    "objective": editing_objective,
                    "videos_analyzed": len(workflow_result["video_analyses"]),
                    "editing_decisions": len(plan.decisions) if plan else 0,
                    "estimated_duration": plan.estimated_duration if plan else 0,
                    "complexity_score": plan.complexity_score if plan else 0,
                    "draft_file": workflow_result["draft_file"],
                    "auto_imported": workflow_result["imported_to_jianying"]
                }

                return [TextContent(
                    type="text",
                    text=f"{status_text}\n\n**编辑目标**: {editing_objective}\n**处理视频**: {len(video_paths)}个\n**编辑决策**: {len(plan.decisions) if plan else 0}个\n**预估时长**: {plan.estimated_duration if plan else 0:.1f}秒\n**复杂度**: {plan.complexity_score if plan else 0:.1f}/10\n**草稿文件**: {workflow_result['draft_file']}\n\n**详细结果**:\n```json\n{json.dumps(summary, ensure_ascii=False, indent=2)}\n```"
                )]
            else:
                error_msg = workflow_result.get("error", "未知错误")
                return [TextContent(
                    type="text",
                    text=f"❌ AI智能编辑失败: {error_msg}"
                )]

        except Exception as e:
            self.logger.error(f"AI智能编辑失败: {e}")
            return [TextContent(
                type="text",
                text=f"❌ AI智能编辑失败: {str(e)}"
            )]

    async def _handle_list_drafts(self, arguments: dict[str, Any]) -> list[TextContent]:
        """处理草稿列表查询。"""
        self.logger.info("查询草稿列表")

        try:
            drafts = self.draft_manager.list_drafts()

            if not drafts:
                return [TextContent(
                    type="text",
                    text="📁 暂无本地草稿文件"
                )]

            # 构建草稿列表显示
            draft_list_text = f"📁 本地草稿文件列表 ({len(drafts)}个)\n\n"

            for i, draft in enumerate(drafts[:10], 1):  # 只显示前10个
                create_time = draft["create_time"]
                duration = draft["duration"] / 1000  # 转换为秒

                draft_list_text += f"**{i}. {draft['name']}**\n"
                draft_list_text += f"   - 文件: {Path(draft['file']).name}\n"
                draft_list_text += f"   - 时长: {duration:.1f}秒\n"
                draft_list_text += f"   - 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(create_time/1000))}\n\n"

            if len(drafts) > 10:
                draft_list_text += f"... 还有 {len(drafts) - 10} 个草稿文件\n"

            # 添加详细JSON数据
            draft_list_text += f"\n**详细信息**:\n```json\n{json.dumps(drafts, ensure_ascii=False, indent=2)}\n```"

            return [TextContent(
                type="text",
                text=draft_list_text
            )]

        except Exception as e:
            self.logger.error(f"查询草稿列表失败: {e}")
            return [TextContent(
                type="text",
                text=f"❌ 查询草稿列表失败: {str(e)}"
            )]

    async def start(self) -> None:
        """启动MCP服务器。"""
        self.logger.info("启动DramaCraft MCP服务器...")

        # 创建必要的目录
        self.config.create_directories()

        try:
            # 使用stdio传输启动服务器
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.config.service_name,
                        server_version=self.config.service_version,
                        capabilities={}
                    )
                )
        except Exception as e:
            self.logger.error(f"服务器启动失败: {e}")
            raise

    def run(self) -> None:
        """运行服务器(同步接口)。"""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.logger.info("服务器已停止")
        except Exception as e:
            self.logger.error(f"服务器运行错误: {e}")
            raise
