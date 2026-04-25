"""End-to-end benchmark runner.

Usage:
    python -m bench_real.runner --tier lite --adapter mock --cap-usd 0.01

Resumes by skipping rows already in results.jsonl with the same
(run_id, case_id, variant, repeat) key.
"""
from __future__ import annotations
import argparse
import json
import os
import random
import sys
import time
from dataclasses import asdict
from pathlib import Path

from .adapters import get_adapter
from .cost_cap import CostCap, estimate_cost
from .schema import CellResult
from .scorers import score_rule_based, score_llm_judge
from .tasks import load_tier
from .tokenizers import count_kpx, count_tiktoken
from .variants import apply_variant, VARIANTS, LITE_VARIANTS


TIER_VARIANTS = {
    "lite":     LITE_VARIANTS,                       # V0, V3, V4
    "standard": VARIANTS,                            # V0..V5
    "deep":     VARIANTS,                            # V0..V5
}
TIER_REPEATS = {"lite": 1, "standard": 3, "deep": 5}
TIER_TIER2_RATE = {"lite": 0.0, "standard": 0.20, "deep": 0.20}


def _existing_keys(out_path: Path) -> set[tuple]:
    if not out_path.exists():
        return set()
    keys = set()
    with out_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                keys.add((row.get("run_id"), row.get("case_id"),
                          row.get("variant"), row.get("repeat")))
            except Exception:
                continue
    return keys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_real.runner")
    ap.add_argument("--tier", choices=["lite", "standard", "deep"], default="lite")
    ap.add_argument("--adapter", choices=["mock", "openai", "anthropic"], default="mock")
    ap.add_argument("--model", default=None)
    ap.add_argument("--judge-adapter", default="mock",
                    help="adapter for tier-2 LLM judge (cross-vendor in real runs)")
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--cap-usd", type=float, default=3.0)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--out", default=None,
                    help="results.jsonl path (default: runs/<tier>-<run_id>.jsonl)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-cases", type=int, default=None,
                    help="cap on number of cases (debug)")
    ap.add_argument("--no-resume", action="store_true")
    args = ap.parse_args(argv)

    random.seed(args.seed)

    run_id = args.run_id or time.strftime("%Y%m%d-%H%M%S")
    here = Path(__file__).resolve().parent
    runs_dir = here / "runs"
    runs_dir.mkdir(exist_ok=True)
    out_path = Path(args.out) if args.out else runs_dir / f"{args.tier}-{run_id}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cases = load_tier(args.tier)
    if args.max_cases:
        cases = cases[:args.max_cases]
    variants = TIER_VARIANTS[args.tier]
    repeats = TIER_REPEATS[args.tier]
    tier2_rate = TIER_TIER2_RATE[args.tier]

    adapter = get_adapter(args.adapter, model=args.model)
    judge = get_adapter(args.judge_adapter, model=args.judge_model)
    cap = CostCap(cap_usd=args.cap_usd)

    seen = set() if args.no_resume else _existing_keys(out_path)
    total_cells = len(cases) * len(variants) * repeats
    print(f"[runner] tier={args.tier} cases={len(cases)} variants={variants} "
          f"repeats={repeats} total_cells={total_cells} adapter={args.adapter} "
          f"model={adapter.model} cap=${args.cap_usd:.2f}")
    print(f"[runner] writing → {out_path}")
    if seen:
        print(f"[runner] resuming, {len(seen)} cells already in {out_path.name}")

    written = 0
    skipped = 0
    capped = False
    t_start = time.time()

    with out_path.open("a", encoding="utf-8") as f:
        for case in cases:
            if capped:
                break
            for variant in variants:
                if capped:
                    break
                sys_v, usr_v = apply_variant(variant, case.system, case.user)
                for rep in range(repeats):
                    key = (run_id, case.id, variant, rep)
                    if key in seen:
                        skipped += 1
                        continue
                    if cap.exceeded:
                        print(f"[runner] cost cap hit at ${cap.spent_usd:.4f}, stopping")
                        capped = True
                        break

                    res = adapter.call(sys_v, usr_v, max_tokens=512, temperature=0.0)
                    p_api = res.prompt_tokens or 0
                    c_api = res.completion_tokens or 0
                    cost = estimate_cost(adapter.model, p_api, c_api)
                    cap.add(cost)

                    # tier-1 score
                    if res.error:
                        tier1, note = 0.0, f"adapter error: {res.error}"
                    else:
                        tier1, note = score_rule_based(res.text, case.expected)

                    # tier-2 spot check (only for variants that matter)
                    tier2 = None
                    axes = None
                    if (tier2_rate > 0 and variant in ("V0", "V3", "V4", "V5")
                            and not res.error and random.random() < tier2_rate):
                        tier2, axes = score_llm_judge(
                            judge, system=case.system, user=case.user,
                            response=res.text,
                        )

                    quality = tier1 if tier2 is None else 0.5 * tier1 + 0.5 * tier2

                    cell = CellResult(
                        run_id=run_id,
                        case_id=case.id,
                        task=case.task,
                        variant=variant,
                        model=adapter.model,
                        repeat=rep,
                        tokens_in_kpx=count_kpx(sys_v) + count_kpx(usr_v),
                        tokens_in_tiktoken=(
                            (count_tiktoken(sys_v, adapter.model) or 0)
                            + (count_tiktoken(usr_v, adapter.model) or 0)
                            if count_tiktoken(sys_v, adapter.model) is not None else None
                        ),
                        tokens_in_api=p_api or None,
                        tokens_out_api=c_api or None,
                        tokens_total_api=res.total_tokens or None,
                        latency_ms=res.latency_ms,
                        tier1_score=tier1,
                        tier2_score=tier2,
                        quality_score=quality,
                        output_excerpt=(res.text or "")[:300],
                        error=res.error or "",
                        cost_usd=cost,
                    )
                    row = asdict(cell)
                    if axes is not None:
                        row["judge_axes"] = axes
                    row["lang"] = case.lang
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    f.flush()
                    written += 1
                    if written % 25 == 0:
                        print(f"[runner] {written} cells, ${cap.spent_usd:.4f} spent, "
                              f"elapsed {time.time()-t_start:.1f}s")

    elapsed = time.time() - t_start
    print(f"[runner] done. wrote={written} skipped={skipped} "
          f"cost=${cap.spent_usd:.4f} elapsed={elapsed:.1f}s")
    print(f"[runner] results → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
