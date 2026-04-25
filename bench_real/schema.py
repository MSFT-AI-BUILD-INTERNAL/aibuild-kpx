"""Case + result schemas. JSON-backed (no yaml dep)."""
from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class Case:
    id: str
    task: str          # T01..T07
    system: str        # system prompt
    user: str          # user message
    expected: dict     # {type: pytest|json_schema|rouge_l|chrf|refusal_label|exact, ...}
    lang: str = "en"   # en|ko|ja|zh ; used for P6
    tags: list[str] = field(default_factory=list)


@dataclass
class CellResult:
    run_id: str
    case_id: str
    task: str
    variant: str
    model: str
    repeat: int = 0

    tokens_in_kpx: int = 0
    tokens_in_tiktoken: int | None = None
    tokens_in_api: int | None = None
    tokens_out_api: int | None = None
    tokens_total_api: int | None = None
    latency_ms: int = 0

    tier1_score: float | None = None    # 0..100
    tier2_score: float | None = None    # 0..100, only on spot-check
    quality_score: float | None = None

    output_excerpt: str = ""
    error: str = ""
    cost_usd: float = 0.0


def load_cases(paths: list[Path]) -> list[Case]:
    out: list[Case] = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        for row in data:
            out.append(Case(**row))
    return out


def case_dict(c: Case) -> dict[str, Any]:
    return asdict(c)


def result_dict(r: CellResult) -> dict[str, Any]:
    return asdict(r)
