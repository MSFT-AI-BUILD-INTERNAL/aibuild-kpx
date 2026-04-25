"""Apply safe in-place compressions."""
from __future__ import annotations
from typing import Iterable
from kpx.methods import SAFE_TRANSFORMS, _collapse_blank_lines


def compress(text: str, methods: Iterable[str] | None = None) -> str:
    """Apply selected safe transforms in order. Default = all SAFE_TRANSFORMS.

    The output is whitespace-normalized and ``compress(compress(x)) ==
    compress(x)`` for any input ``x`` and any subset of methods. The trailing
    newline of ``text`` is preserved on the output for shell-friendliness.
    """
    selected = list(methods) if methods else list(SAFE_TRANSFORMS.keys())
    out = text
    for mid in selected:
        fn = SAFE_TRANSFORMS.get(mid)
        if fn is None:
            raise ValueError(f"Unknown or non-safe method: {mid}")
        out = fn(out)
    out = _collapse_blank_lines(out)
    if text.endswith("\n") and not out.endswith("\n"):
        out += "\n"
    return out
