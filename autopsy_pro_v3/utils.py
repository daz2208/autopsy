"""Utility functions for Autopsy Pro"""
import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def safe_read_text(path: Path, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read text file with fallback encodings
    """
    encodings = [encoding, 'utf-8', 'latin-1', 'cp1252']
    
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            return None
    
    logger.warning(f"Could not decode {path} with any encoding")
    return None


def stable_uid(project: str, filename: str, line: str) -> str:
    """
    Generate stable unique identifier for a fragment
    """
    key = f"{project}:{filename}:{line}"
    return hashlib.md5(key.encode()).hexdigest()[:16]


def format_size(bytes_size: int) -> str:
    """Format byte size to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as filename"""
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Limit length
    if len(name) > 200:
        name = name[:200]
    
    return name.strip()


def truncate_string(s: str, max_len: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(s) <= max_len:
        return s
    return s[:max_len - len(suffix)] + suffix
