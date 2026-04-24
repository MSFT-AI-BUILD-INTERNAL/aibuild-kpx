"""Apply safe in-place compressions."""
from __future__ import annotations
from typing import Iterable
from kpx.methods import SAFE_TRANSFORMS


def compress(text: str, methods: Iterable[str] | None = None) -> str:
    """Apply selected safe transforms in order. Default = all SAFE_TRANSFORMS."""
    selected = list(methods) if methods else list(SAFE_TRANSFORMS.keys())
    out = text
    for mid in selected:
        fn = SAFE_TRANSFORMS.get(mid)
        if fn is None:
            raise ValueError(f"Unknown or non-safe method: {mid}")
        out = fn(out)
    return out
