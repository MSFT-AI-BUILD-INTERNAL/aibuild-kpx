"""Task case loader. Lite vs Standard vs Deep selection."""
from __future__ import annotations
from pathlib import Path

from ..schema import Case, load_cases


_TASK_FILES = {
    "T01": "t01_coding.json",
    "T02": "t02_bugfix.json",
    "T03": "t03_docs.json",
    "T04": "t04_json.json",
    "T05": "t05_tools.json",
    "T06": "t06_safety.json",
    "T07": "t07_translation.json",
}

# Per plan v2 §6 — case counts per tier.
TIER_BUDGET = {
    "lite":     {"T01": 10, "T03": 6,  "T04": 6,  "T06": 10, "T07": 5},
    "standard": {"T01": 15, "T02": 5,  "T03": 12, "T04": 12, "T05": 8, "T06": 10, "T07": 10},
    "deep":     {"T01": 15, "T02": 10, "T03": 12, "T04": 12, "T05": 8, "T06": 10, "T07": 10},
}


def load_tier(tier: str) -> list[Case]:
    """Load cases for the requested tier, capped at TIER_BUDGET."""
    here = Path(__file__).resolve().parent
    budget = TIER_BUDGET[tier]
    out: list[Case] = []
    for tid, n in budget.items():
        fname = _TASK_FILES.get(tid)
        if not fname:
            continue
        path = here / fname
        if not path.exists():
            continue
        cases = load_cases([path])
        out.extend(cases[:n])
    return out
