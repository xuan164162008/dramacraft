"""
Helper utilities for Video MCP service.

This module provides common utility functions used across the service.
"""

import hashlib
import mimetypes
import os
import time
from pathlib import Path
from typing import Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_video_file(file_path: Union[str, Path]) -> bool:
    """
    Validate if a file is a supported video format.

    Args:
        file_path: Path to the video file

    Returns:
        True if the file is a valid video format
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        return False

    # Check file extension
    video_extensions = {
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv',
        '.webm', '.m4v', '.3gp', '.ogv', '.ts', '.mts'
    }

    if file_path.suffix.lower() not in video_extensions:
        return False

    # Check MIME type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type and not mime_type.startswith('video/'):
        return False

    return True


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "1h 23m 45s")
    """
    if seconds < 0:
        return "0s"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def generate_file_hash(file_path: Union[str, Path], algorithm: str = "md5") -> str:
    """
    Generate hash for a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (md5, sha1, sha256)

    Returns:
        Hex digest of the file hash
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Create a safe filename by removing/replacing invalid characters.

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Safe filename
    """
    # Characters to remove or replace
    invalid_chars = '<>:"/\\|?*'

    # Replace invalid characters with underscores
    safe_name = filename
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')

    # Remove leading/trailing dots and spaces
    safe_name = safe_name.strip('. ')

    # Ensure it's not empty
    if not safe_name:
        safe_name = f"file_{int(time.time())}"

    # Truncate if too long
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        max_name_length = max_length - len(ext)
        safe_name = name[:max_name_length] + ext

    return safe_name


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in MB
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return 0.0

    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 * 1024)


def split_text_by_length(text: str, max_length: int = 1000) -> list[str]:
    """
    Split text into chunks of maximum length.

    Args:
        text: Text to split
        max_length: Maximum length per chunk

    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_pos = 0

    while current_pos < len(text):
        # Find the end position for this chunk
        end_pos = current_pos + max_length

        if end_pos >= len(text):
            # Last chunk
            chunks.append(text[current_pos:])
            break

        # Try to break at a sentence boundary
        chunk = text[current_pos:end_pos]

        # Look for sentence endings
        for delimiter in ['. ', '! ', '? ', '\n\n', '\n']:
            last_delimiter = chunk.rfind(delimiter)
            if last_delimiter > max_length * 0.7:  # Don't break too early
                end_pos = current_pos + last_delimiter + len(delimiter)
                break

        chunks.append(text[current_pos:end_pos])
        current_pos = end_pos

    return chunks


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    truncate_length = max_length - len(suffix)
    return text[:truncate_length] + suffix
