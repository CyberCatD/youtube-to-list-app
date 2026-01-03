import re
from typing import Optional

YOUTUBE_URL_PATTERNS = [
    r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}',
    r'^https?://youtu\.be/[\w-]{11}',
    r'^https?://(?:www\.)?youtube\.com/embed/[\w-]{11}',
    r'^https?://(?:www\.)?youtube\.com/shorts/[\w-]{11}',
]

def validate_youtube_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validates YouTube URL format and extracts video ID.
    Returns (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    for pattern in YOUTUBE_URL_PATTERNS:
        if re.match(pattern, url):
            return True, None
    
    return False, "Invalid YouTube URL format"

def sanitize_url(url: str) -> str:
    """Remove tracking parameters while preserving video ID"""
    # For watch URLs, keep only the v= parameter
    if 'watch?' in url and 'v=' in url:
        base_url = url.split('?')[0]
        video_id = url.split('v=')[1].split('&')[0]
        return f"{base_url}?v={video_id}"
    # For other formats (youtu.be, shorts, embed), remove all query params
    return url.split('?')[0].split('&')[0]
