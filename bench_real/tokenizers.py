"""Token counting helpers.

- ``count_kpx`` always available (kpx heuristic).
- ``count_tiktoken`` returns None if tiktoken not installed.
"""
from __future__ import annotations
from typing import Optional

from kpx.tokens import estimate_tokens

try:
    import tiktoken  # type: ignore
    _HAS_TIKTOKEN = True
except Exception:
    _HAS_TIKTOKEN = False


_ENCODING_FOR_MODEL = {
    "gpt-4o-mini": "o200k_base",
    "gpt-4o": "o200k_base",
    "gpt-5-mini": "o200k_base",
    "gpt-4-turbo": "cl100k_base",
}


def count_kpx(text: str) -> int:
    return estimate_tokens(text)


def count_tiktoken(text: str, model: str) -> Optional[int]:
    if not _HAS_TIKTOKEN:
        return None
    enc_name = _ENCODING_FOR_MODEL.get(model, "o200k_base")
    try:
        enc = tiktoken.get_encoding(enc_name)
    except Exception:
        return None
    return len(enc.encode(text))
