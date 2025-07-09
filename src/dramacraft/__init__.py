"""
DramaCraft - 专业的短剧视频编辑MCP服务，集成剪映和中文大模型。

本包提供了一个模型上下文协议(MCP)服务，集成国产中文大模型API，
自动化剪映(JianYing)中的短剧视频编辑工作流程。

核心功能：
- 短剧解说文案生成
- 短剧混剪/合集制作
- 第一人称叙述解说

该服务采用清晰的模块化架构设计，遵循Python最佳实践。
"""

__version__ = "0.1.0"
__author__ = "Agions"
__email__ = "contact@1051736049@qq.com"

from .config import DramaCraftConfig
from .server import DramaCraftServer

__all__ = [
    "DramaCraftServer",
    "DramaCraftConfig",
    "__version__",
]
