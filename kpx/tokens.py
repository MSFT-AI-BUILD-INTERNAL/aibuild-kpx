"""Token estimation. Mirrors harness/constraints.py heuristic for consistency."""
from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token (English) / ~1.5 chars (CJK).

    Mirrors the heuristic in harness/constraints.py so audits match the
    project-wide budget gate.
    """
    if not text:
        return 0
    cjk = sum(1 for c in text if "\u3000" <= c <= "\u9fff" or "\uac00" <= c <= "\ud7af")
    other = len(text) - cjk
    return max(1, cjk + other // 4 + (1 if other % 4 else 0))


def fits_window(text: str, window: int, ratio: float = 0.5) -> bool:
    """50% rule from harness.constraints.must_split inverted."""
    return estimate_tokens(text) <= int(window * ratio)
