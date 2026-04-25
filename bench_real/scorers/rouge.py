"""Minimal ROUGE-L (LCS-based F-score), word-tokenized."""
from __future__ import annotations
import re


def _tokens(s: str) -> list[str]:
    return re.findall(r"\w+", s.lower())


def _lcs_len(a: list[str], b: list[str]) -> int:
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0] * (len(b) + 1)
        for j, y in enumerate(b, 1):
            cur[j] = prev[j-1] + 1 if x == y else max(prev[j], cur[j-1])
        prev = cur
    return prev[-1]


def rouge_l(hyp: str, ref: str, beta: float = 1.2) -> float:
    h, r = _tokens(hyp), _tokens(ref)
    if not h or not r:
        return 0.0
    lcs = _lcs_len(h, r)
    if lcs == 0:
        return 0.0
    p = lcs / len(h)
    rec = lcs / len(r)
    b2 = beta * beta
    return 100.0 * (1 + b2) * p * rec / (b2 * p + rec)
