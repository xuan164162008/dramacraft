"""
Video processing module for Video MCP service.

This module provides video processing utilities and JianYing integration
for automated video editing workflows.
"""

from .jianying import JianYingIntegrator
from .processor import VideoProcessor

__all__ = [
    "VideoProcessor",
    "JianYingIntegrator",
]
