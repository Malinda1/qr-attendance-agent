"""
Helper Utilities
Common utility functions used across the application
"""

import re
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path


def extract_qr_id(url: str) -> Optional[str]:
    """
    Extract ID from QR code URL
    
    Args:
        url: QR code URL
        
    Returns:
        Extracted ID or None if not found
    """
    match = re.search(r'id=([^&]+)', url)
    return match.group(1) if match else None


def parse_qr_id(qr_id: str) -> Optional[Tuple[str, str]]:
    """
    Parse QR ID into its components
    
    Args:
        qr_id: QR code ID (format: XXXXX_YYYYY)
        
    Returns:
        Tuple of (first_part, second_part) or None if invalid
    """
    parts = qr_id.split('_')
    return tuple(parts) if len(parts) == 2 else None


def validate_nsbm_url(url: str) -> bool:
    """
    Validate if URL is a valid NSBM attendance URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^https://students\.nsbm\.ac\.lk/attendence/(index|login)\.php\?id=[0-9]+_[0-9]+$'
    return bool(re.match(pattern, url))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string
    
    Args:
        dt: Datetime object (uses current time if None)
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def get_file_size(file_path: Path) -> str:
    """
    Get human-readable file size
    
    Args:
        file_path: Path to file
        
    Returns:
        File size as string (e.g., "1.5 MB")
    """
    size = file_path.stat().st_size
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    
    return f"{size:.2f} TB"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate string to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_module_name(module_name: str) -> bool:
    """
    Validate module name format
    
    Args:
        module_name: Module name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Module name should be 3-100 characters, alphanumeric with spaces and hyphens
    pattern = r'^[A-Za-z0-9\s\-]{3,100}$'
    return bool(re.match(pattern, module_name))


__all__ = [
    "extract_qr_id",
    "parse_qr_id",
    "validate_nsbm_url",
    "sanitize_filename",
    "format_timestamp",
    "get_file_size",
    "truncate_string",
    "is_valid_module_name"
]