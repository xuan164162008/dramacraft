"""
DramaCraft MCP工具集
提供完整的视频编辑工具，符合MCP 1.0+标准
"""

from typing import Any, Dict, List

from .batch_processing import BatchProcessingTool
from .commentary_generation import CommentaryGenerationTool
from .jianying_draft import JianYingDraftTool
from .narrative_generation import NarrativeGenerationTool
from .remix_creation import RemixCreationTool
from .series_compilation import SeriesCompilationTool
from .smart_video_edit import SmartVideoEditTool
from .video_analysis import VideoAnalysisTool

# 所有可用工具
ALL_TOOLS = [
    SeriesCompilationTool,
    CommentaryGenerationTool,
    VideoAnalysisTool,
    JianYingDraftTool,
    SmartVideoEditTool,
    RemixCreationTool,
    NarrativeGenerationTool,
    BatchProcessingTool,
]

# 工具优先级映射
TOOL_PRIORITY = {
    "create_series_compilation": 1,  # 主要功能
    "generate_commentary": 2,        # 辅助功能
    "analyze_video": 2,              # 分析功能
    "create_jianying_draft": 2,      # 集成功能
    "smart_video_edit": 3,           # 传统功能
    "create_remix": 3,               # 传统功能
    "generate_narrative": 4,         # 扩展功能
    "batch_process": 4,              # 效率功能
}

def get_all_tool_definitions():
    """获取所有工具定义"""
    return [tool.get_tool_definition() for tool in ALL_TOOLS]

def get_tool_by_name(name: str):
    """根据名称获取工具类"""
    tool_map = {tool.get_tool_definition().name: tool for tool in ALL_TOOLS}
    return tool_map.get(name)

def get_tools_by_priority():
    """按优先级获取工具"""
    tools_with_priority = []
    for tool in ALL_TOOLS:
        tool_def = tool.get_tool_definition()
        priority = TOOL_PRIORITY.get(tool_def.name, 5)
        tools_with_priority.append((priority, tool))

    return [tool for _, tool in sorted(tools_with_priority)]

__all__ = [
    'ALL_TOOLS',
    'TOOL_PRIORITY',
    'get_all_tool_definitions',
    'get_tool_by_name',
    'get_tools_by_priority',
    'SeriesCompilationTool',
    'CommentaryGenerationTool',
    'VideoAnalysisTool',
    'JianYingDraftTool',
    'SmartVideoEditTool',
    'RemixCreationTool',
    'NarrativeGenerationTool',
    'BatchProcessingTool',
]
