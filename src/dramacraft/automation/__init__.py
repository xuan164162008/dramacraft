"""
自动化模块。

本模块提供完整的视频编辑自动化功能，包括剪映集成和工作流管理。
"""

from .jianying_engine import (
    AutomationProgress,
    AutomationResult,
    AutomationStage,
    JianYingAutomationEngine,
)

__all__ = [
    "JianYingAutomationEngine",
    "AutomationStage",
    "AutomationProgress",
    "AutomationResult"
]
