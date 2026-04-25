"""Result loader + statistics helpers shared across all views."""
from __future__ import annotations
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev


def load_jsonl(path: Path) -> list[dict]:
    if not Path(path).exists():
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def group_by(rows: list[dict], *keys: str) -> dict:
    """Group rows by one or more keys.

    Single key  → dict[str, list[dict]]
    Multi-key   → dict[tuple, list[dict]]
    """
    out: dict = defaultdict(list)
    if len(keys) == 1:
        k = keys[0]
        for r in rows:
            out[r.get(k)].append(r)
    else:
        for r in rows:
            out[tuple(r.get(k) for k in keys)].append(r)
    return out


def agg_quality(rows: list[dict]) -> dict:
    q = [r["quality_score"] for r in rows if r.get("quality_score") is not None]
    if not q:
        return {"n": 0, "mean": None, "median": None, "std": None}
    return {
        "n": len(q),
        "mean": mean(q),
        "median": median(q),
        "std": pstdev(q) if len(q) > 1 else 0.0,
    }


def agg_tokens(rows: list[dict]) -> dict:
    t = [r["tokens_in_kpx"] for r in rows if r.get("tokens_in_kpx") is not None]
    return {"n": len(t), "mean": mean(t) if t else 0.0}


def reduction_pct(baseline: float, candidate: float) -> float:
    if not baseline:
        return 0.0
    return 100.0 * (baseline - candidate) / baseline


def quality_delta_pct(baseline: float, candidate: float) -> float:
    """Negative = degraded, positive = improved."""
    if baseline is None or candidate is None or not baseline:
        return 0.0
    return 100.0 * (candidate - baseline) / baseline
