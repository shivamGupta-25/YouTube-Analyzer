#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Helper utility functions for the YouTube Channel Analyzer.
"""

import datetime
import re


def extract_channel_id_from_url(url_or_id: str) -> str:
    """
    Accepts:
      - a channel ID (starts with UC...)
      - a channel URL (https://www.youtube.com/channel/UC...)
      - a user or custom URL (https://www.youtube.com/c/SomeName) [falls back to API lookup]
    Returns channelId or raises ValueError if can't find.
    """
    text = url_or_id.strip()
    if text.startswith("UC") and len(text) > 20:
        return text
    # try channel URL pattern
    m = re.search(r"(?:youtube\.com\/channel\/)([A-Za-z0-9_\-]+)", text)
    if m:
        return m.group(1)
    # if it's a /user/ or /c/, return as-is and let API resolve
    m2 = re.search(r"(?:youtube\.com\/(?:user|c)\/)([^\/\?\&]+)", text)
    if m2:
        return text  # will resolve below
    # maybe user pasted full url with query or short url
    # If none matched, return as-is (might be the channel id)
    return text


def parse_iso8601_duration(dur: str) -> int:
    """
    Parse ISO 8601 duration (e.g., PT1H2M20S) and return seconds.
    Simple parser without external libs.
    """
    if not dur:
        return 0
    # regex to capture hours/minutes/seconds
    pattern = re.compile(r'P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?')
    m = pattern.match(dur)
    if not m:
        return 0
    parts = m.groupdict()
    seconds = int(parts.get("days") or 0) * 86400 + int(parts.get("hours") or 0) * 3600 + int(parts.get("minutes") or 0) * 60 + int(parts.get("seconds") or 0)
    return seconds


def format_duration(seconds: int) -> str:
    """
    Convert seconds to HH:MM:SS string.
    """
    if not seconds:
        return "00:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def iso8601_to_datetime(s: str) -> datetime.datetime:
    """Convert ISO 8601 string to datetime object."""
    # Example: 2021-08-03T15:30:20Z
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


def safe_int(x):
    """Safely convert value to integer, return None on failure."""
    try:
        return int(x)
    except Exception:
        return None


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename, handling Unicode properly"""
    if not name:
        return "youtube_data"
    # Ensure we have a Unicode string
    name = str(name)
    # Replace invalid characters with underscore (Windows filename restrictions)
    invalid_chars = '<>:"/\\|?*\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    for char in invalid_chars:
        name = name.replace(char, '_')
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    # Limit length to avoid Windows path issues (max 255 chars for filename)
    if len(name) > 200:
        name = name[:200]
    # Ensure name is not empty after sanitization
    if not name:
        return "youtube_data"
    return name
