"""YouTube URL parsing helpers. No network calls — pure validation."""

import re
from typing import Optional

_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})"),
]


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract 11-character video ID from a YouTube URL. Returns None if invalid."""
    url = url.strip()
    for pattern in _PATTERNS:
        m = pattern.search(url)
        if m:
            return m.group(1)
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", url):
        return url
    return None
