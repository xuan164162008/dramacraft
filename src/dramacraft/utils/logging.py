"""
Logging utilities for Video MCP service.

This module provides centralized logging configuration and utilities.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from ..config import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """
    Set up logging configuration.

    Args:
        config: Logging configuration
    """
    # Create logger
    logger = logging.getLogger("video_mcp")
    logger.setLevel(getattr(logging, config.level))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(config.format)

    # Console handler with Rich
    console = Console()
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if config.file_path:
        file_path = Path(config.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            filename=file_path,
            maxBytes=config.max_file_size,
            backupCount=config.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Set root logger level to prevent duplicate messages
    logging.getLogger().setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to video_mcp)

    Returns:
        Logger instance
    """
    if name is None:
        name = "video_mcp"
    elif not name.startswith("video_mcp"):
        name = f"video_mcp.{name}"

    return logging.getLogger(name)
