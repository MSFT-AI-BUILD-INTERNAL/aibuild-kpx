"""Aggregate bench_real JSONL into per-model + per-variant summary.

Usage:
    PYTHONPATH=. python -m bench_real.aggregate \
        --runs-dir bench_real/runs/lite-r6-all \
        --out bench_real/runs/lite-r6-all/_aggregate.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from collections import defaultdict


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", required=True,
                    help="directory containing per-model .jsonl files")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    files = sorted(runs_dir.glob("*.jsonl"))
    print(f"[aggregate] {len(files)} model files in {runs_dir}")

    # per (model, variant) accumulators
    bucket: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "n": 0, "n_err": 0, "tok_in": 0, "tok_out": 0,
        "latency_ms": 0, "quality_sum": 0.0,
    })

    for f in files:
        with f.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                key = (r.get("model", "?"), r.get("variant", "?"))
                b = bucket[key]
                b["n"] += 1
                if r.get("error"):
                    b["n_err"] += 1
                    continue
                b["tok_in"] += r.get("tokens_in_api") or 0
                b["tok_out"] += r.get("tokens_out_api") or 0
                b["latency_ms"] += r.get("latency_ms") or 0
                b["quality_sum"] += r.get("quality_score") or 0.0

    # build per-model rows
    by_model: dict[str, dict] = defaultdict(lambda: {})
    for (model, variant), b in bucket.items():
        n_ok = b["n"] - b["n_err"]
        by_model[model][variant] = {
            "n": b["n"],
            "n_ok": n_ok,
            "n_err": b["n_err"],
            "avg_tok_in": round(b["tok_in"] / n_ok, 1) if n_ok else None,
            "avg_tok_out": round(b["tok_out"] / n_ok, 1) if n_ok else None,
            "avg_latency_ms": round(b["latency_ms"] / n_ok, 1) if n_ok else None,
            "avg_quality": round(b["quality_sum"] / n_ok, 2) if n_ok else None,
        }

    # compute V0->V4 savings per model
    summary = []
    for model, vmap in sorted(by_model.items()):
        v0 = vmap.get("V0", {})
        v4 = vmap.get("V4", {})
        v3 = vmap.get("V3", {})
        saving_v3 = (round((v0["avg_tok_in"] - v3["avg_tok_in"])
                           / v0["avg_tok_in"] * 100.0, 2)
                     if v0.get("avg_tok_in") and v3.get("avg_tok_in") else None)
        saving_v4 = (round((v0["avg_tok_in"] - v4["avg_tok_in"])
                           / v0["avg_tok_in"] * 100.0, 2)
                     if v0.get("avg_tok_in") and v4.get("avg_tok_in") else None)
        q_v0 = v0.get("avg_quality")
        q_v4 = v4.get("avg_quality")
        dq = (round(q_v4 - q_v0, 2)
              if q_v0 is not None and q_v4 is not None else None)
        summary.append({
            "model": model,
            "variants": vmap,
            "saving_pct_v0_to_v3": saving_v3,
            "saving_pct_v0_to_v4": saving_v4,
            "quality_delta_v0_to_v4": dq,
        })

    out = {
        "runs_dir": str(runs_dir),
        "n_models": len(by_model),
        "summary": summary,
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"[aggregate] wrote → {args.out}")

    # console table
    print(f"\n{'model':<46} {'tok_v0':>7} {'tok_v4':>7} "
          f"{'save%':>7} {'q_v0':>6} {'q_v4':>6} {'Δq':>6} {'err':>4}")
    for r in summary:
        v0 = r["variants"].get("V0", {})
        v4 = r["variants"].get("V4", {})
        n_err_total = sum(v.get("n_err", 0) for v in r["variants"].values())
        print(f"{r['model']:<46} "
              f"{(v0.get('avg_tok_in') or 0):>7.1f} "
              f"{(v4.get('avg_tok_in') or 0):>7.1f} "
              f"{(r['saving_pct_v0_to_v4'] or 0):>+6.2f}% "
              f"{(v0.get('avg_quality') or 0):>6.1f} "
              f"{(v4.get('avg_quality') or 0):>6.1f} "
              f"{(r['quality_delta_v0_to_v4'] or 0):>+5.1f} "
              f"{n_err_total:>4d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
