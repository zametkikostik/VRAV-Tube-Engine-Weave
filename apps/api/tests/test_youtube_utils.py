"""Unit tests for YouTube URL parsing."""

from app.utils.youtube import extract_youtube_video_id


def test_standard_watch_url():
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_short_url():
    assert extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_shorts():
    assert extract_youtube_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_bare_id():
    assert extract_youtube_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_invalid():
    assert extract_youtube_video_id("https://example.com/video") is None
    assert extract_youtube_video_id("") is None
