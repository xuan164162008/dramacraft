"""
Core video editing features for Video MCP service.

This module implements the three main video editing features:
- Short Drama Commentary Generation
- Short Drama Remix/Compilation
- First-Person Narrative Commentary
"""

from .commentary import CommentaryGenerator
from .narrative import NarrativeGenerator
from .remix import RemixGenerator

__all__ = [
    "CommentaryGenerator",
    "RemixGenerator",
    "NarrativeGenerator",
]
