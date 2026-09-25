"""
Text normalization utilities for detection pipeline preprocessing.
"""

import re
from typing import List


def normalize_text(text: str) -> str:
    """
    Apply conservative text normalization.

    - Replaces multi-whitespace (tabs, newlines, repeated spaces) with a single space.
    - Strips leading and trailing whitespace.
    - Preserves case in original return for contextual needs, but provides a clean base.
    """
    if not text:
        return ""
    # Collapse multiple whitespace characters into single space
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()


def extract_urls(text: str) -> List[str]:
    """
    Extract web links, domain patterns, and messaging links from text.
    """
    url_pattern = r"(?:https?://|www\.)[^\s/$.?#].[^\s]*|wa\.me/[^\s]+|t\.me/[^\s]+"
    return re.findall(url_pattern, text, flags=re.IGNORECASE)


def has_word(text: str, word: str) -> bool:
    """Check if a distinct word appears in text (case-insensitive word boundary)."""
    pattern = rf"\b{re.escape(word)}\b"
    return bool(re.search(pattern, text, flags=re.IGNORECASE))
