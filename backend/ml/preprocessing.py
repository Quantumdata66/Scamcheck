"""
Text Preprocessing Module for ScamCheck ML Pipeline.

Provides reusable text cleaning and normalization routines designed for
TF-IDF vectorization and machine learning classifiers.
"""

import re
from typing import List, Union
import numpy as np


# Common regex patterns for entity normalization
URL_PATTERN = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_+.~#?&/=]*",
    re.IGNORECASE
)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
)
CRYPTO_ADDR_PATTERN = re.compile(
    r"\b(?:0x[a-fA-F0-9]{40}|bc1[a-z0-9]{39,59}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b"
)
CURRENCY_PATTERN = re.compile(
    r"[\$\£\€]\s*[\d,]+(?:\.\d+)?|\b[\d,]+(?:\.\d+)?\s*(?:usd|usdt|usdc|gbp|eur|btc|eth)\b",
    re.IGNORECASE
)


def clean_text(text: str, normalize_entities: bool = True) -> str:
    """
    Standardize raw message text for feature extraction.

    Transformations:
    - Normalizes URLs to token '__url__'
    - Normalizes Phone Numbers to token '__phone__'
    - Normalizes Email Addresses to token '__email__'
    - Normalizes Crypto Wallet Addresses to token '__crypto_addr__'
    - Normalizes Currency amounts to token '__currency__'
    - Converts to lowercase
    - Normalizes multi-spaces and leading/trailing whitespace
    """
    if not isinstance(text, str):
        return ""

    cleaned = text

    if normalize_entities:
        cleaned = URL_PATTERN.sub(" __url__ ", cleaned)
        cleaned = PHONE_PATTERN.sub(" __phone__ ", cleaned)
        cleaned = EMAIL_PATTERN.sub(" __email__ ", cleaned)
        cleaned = CRYPTO_ADDR_PATTERN.sub(" __crypto_addr__ ", cleaned)
        cleaned = CURRENCY_PATTERN.sub(" __currency__ ", cleaned)

    # Convert to lowercase
    cleaned = cleaned.lower()

    # Normalize excessive punctuation (e.g. '!!!', '???', '$$$')
    cleaned = re.sub(r"([!?$*#])\1+", r" \1 ", cleaned)

    # Normalize whitespace
    cleaned = " ".join(cleaned.split())

    return cleaned


def batch_clean_texts(texts: Union[List[str], np.ndarray], normalize_entities: bool = True) -> List[str]:
    """Clean a collection of raw text strings."""
    return [clean_text(t, normalize_entities=normalize_entities) for t in texts]
