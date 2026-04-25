"""kpx 300-round campaign runner.

30 prompts × 10 transform configurations = 300 rounds.
Each round measures: tokens before/after, runtime, idempotency, score delta,
content-loss safety probes (CoT preserved? code block intact? signposts kept?).
"""
from __future__ import annotations
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from kpx import audit, compress, estimate_tokens
from kpx.methods import inject_no_filler

from bench_real.legacy.corpus import all_prompts, Prompt


# 10 transform configurations
TRANSFORMS: list[tuple[str, Callable[[str], str]]] = [
    ("none",          lambda t: t),
    ("M03",           lambda t: compress(t, methods=["M03"])),
    ("M04",           lambda t: compress(t, methods=["M04"])),
    ("M19",           lambda t: compress(t, methods=["M19"])),
    ("M24",           lambda t: compress(t, methods=["M24"])),
    ("M25",           lambda t: compress(t, methods=["M25"])),
    ("M03+M24",       lambda t: compress(t, methods=["M03", "M24"])),
    ("M04+M25",       lambda t: compress(t, methods=["M04", "M25"])),
    ("all_safe",      lambda t: compress(t)),
    ("inject+all",    lambda t: inject_no_filler(compress(t))),
]


# Content-loss safety probes — these substrings MUST survive compression.
SAFETY_PROBES = [
    "step by step",        # CoT (Karpathy explicitly advocates)
    "Please note",         # technical signpost
    "Please refer",        # technical signpost
    "Please see",          # technical signpost
    "do not modify",       # in-code preservation marker
]


@dataclass
class Result:
    round: int
    prompt_id: str
    category: str
    style: str
    transform: str
    tokens_before: int
    tokens_after: int
    savings_pct: float
    runtime_ms: float
    score_before: int
    score_after: int
    idempotent: bool
    safety_violations: list[str] = field(default_factory=list)
    error: str = ""


def _safety_violations(before: str, after: str) -> list[str]:
    out = []
    for probe in SAFETY_PROBES:
        if probe in before and probe not in after:
            out.append(probe)
    return out


def run_one(round_num: int, prompt: Prompt, transform_name: str,
            transform: Callable[[str], str]) -> Result:
    start = time.perf_counter()
    error = ""
    after = prompt.text
    idempotent = True
    try:
        after = transform(prompt.text)
        # idempotency check — applying twice yields same result
        idempotent = transform(after) == after
    except Exception as e:
        error = f"{type(e).__name__}: {e}"
    runtime_ms = (time.perf_counter() - start) * 1000

    tb = estimate_tokens(prompt.text)
    ta = estimate_tokens(after)
    savings = (tb - ta) / tb * 100 if tb else 0.0

    rep_b = audit(prompt.text)
    rep_a = audit(after)
    return Result(
        round=round_num,
        prompt_id=prompt.id,
        category=prompt.category,
        style=prompt.style,
        transform=transform_name,
        tokens_before=tb,
        tokens_after=ta,
        savings_pct=round(savings, 2),
        runtime_ms=round(runtime_ms, 3),
        score_before=rep_b.score,
        score_after=rep_a.score,
        idempotent=idempotent,
        safety_violations=_safety_violations(prompt.text, after),
        error=error,
    )


def run_all() -> list[Result]:
    prompts = all_prompts()
    results: list[Result] = []
    n = 0
    for prompt in prompts:
        for tname, tfn in TRANSFORMS:
            n += 1
            results.append(run_one(n, prompt, tname, tfn))
    return results


def aggregate(results: list[Result]) -> dict:
    by_xform: dict[str, dict] = {}
    for r in results:
        b = by_xform.setdefault(r.transform, {
            "n": 0, "savings_total": 0.0, "score_delta": 0,
            "errors": 0, "non_idempotent": 0, "safety_violations": 0,
            "runtime_ms_total": 0.0,
        })
        b["n"] += 1
        b["savings_total"] += r.savings_pct
        b["score_delta"] += r.score_after - r.score_before
        b["errors"] += 1 if r.error else 0
        b["non_idempotent"] += 0 if r.idempotent else 1
        b["safety_violations"] += len(r.safety_violations)
        b["runtime_ms_total"] += r.runtime_ms
    summary = []
    for tname, b in by_xform.items():
        summary.append({
            "transform": tname,
            "n": b["n"],
            "avg_savings_pct": round(b["savings_total"] / b["n"], 2),
            "avg_score_delta": round(b["score_delta"] / b["n"], 2),
            "avg_runtime_ms": round(b["runtime_ms_total"] / b["n"], 3),
            "errors": b["errors"],
            "non_idempotent": b["non_idempotent"],
            "safety_violations": b["safety_violations"],
        })
    summary.sort(key=lambda x: -x["avg_savings_pct"])

    totals = {
        "rounds": len(results),
        "errors": sum(1 for r in results if r.error),
        "non_idempotent": sum(1 for r in results if not r.idempotent),
        "safety_violations": sum(len(r.safety_violations) for r in results),
        "best_transform": summary[0]["transform"] if summary else "n/a",
    }
    return {"totals": totals, "by_transform": summary}


def main(out_path: str = "bench_real/legacy/results.json") -> dict:
    results = run_all()
    agg = aggregate(results)
    payload = {
        "results": [asdict(r) for r in results],
        "summary": agg,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    return payload


if __name__ == "__main__":
    payload = main()
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
