"""Minimal chrF (character n-gram F-score). Default n=6, beta=2 (chrF++)."""
from __future__ import annotations
from collections import Counter


def _ngrams(text: str, n: int) -> Counter:
    text = text.replace(" ", "")
    return Counter(text[i:i+n] for i in range(len(text) - n + 1) if len(text) >= n)


def chrf(hyp: str, ref: str, max_n: int = 6, beta: float = 2.0) -> float:
    if not hyp or not ref:
        return 0.0
    f_scores = []
    for n in range(1, max_n + 1):
        h, r = _ngrams(hyp, n), _ngrams(ref, n)
        if not h or not r:
            continue
        overlap = sum((h & r).values())
        prec = overlap / max(1, sum(h.values()))
        rec  = overlap / max(1, sum(r.values()))
        if prec + rec == 0:
            f_scores.append(0.0)
            continue
        b2 = beta * beta
        f_scores.append((1 + b2) * prec * rec / (b2 * prec + rec))
    return 100.0 * (sum(f_scores) / len(f_scores)) if f_scores else 0.0
