"""Utility functions for text processing and time conversion."""
import re
from datetime import datetime


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return text
    # Remove HTML tags
    clean_text = re.sub(r"<[^>]+>", "", text)
    # Normalize all whitespace (spaces, newlines, tabs, etc.) to single spaces
    clean_text = re.sub(r"\s+", " ", clean_text)
    # Clean up extra whitespace at start/end
    clean_text = clean_text.strip()
    return clean_text


def to_epoch_time(iso_timestamp: str) -> int:
    """Convert ISO 8601 UTC timestamp to epoch time."""
    if not iso_timestamp:
        return 0
    # Parse ISO 8601 format like "2026-01-16T22:36:55Z"
    dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    return int(dt.timestamp())
