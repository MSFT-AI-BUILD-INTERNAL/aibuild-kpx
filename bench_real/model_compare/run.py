"""CLI: per-model token-usage benchmark.

Usage:
    python -m bench_real.model_compare.run

Optional live-call mode (requires API keys):
    python -m bench_real.model_compare.run --live --max-calls 3 \\
        --providers openai,google --variant V4_all_safe
"""
from __future__ import annotations
import argparse
import json
import os
import sys

from bench_real.model_compare import write, MODELS, VARIANT_METHODS, _apply_variant
from bench_real.analysis.realistic_prompts import CORPUS
from bench_real.adapters import get_adapter


def _print_offline_summary(out: dict) -> None:
    print(f"\n[model_compare] cells={out['meta']['n_cells']} "
          f"prompts={out['meta']['n_prompts']} "
          f"models={out['meta']['n_models']} "
          f"variants={out['meta']['n_variants']} "
          f"tiktoken={out['meta']['tiktoken_available']}")

    print("\n=== savings by variant (corpus-weighted, all models) ===")
    print(f"{'variant':<14} {'n':>4} {'avg %':>8} {'corpus %':>9}")
    for r in out["summary_by_variant"]:
        print(f"  {r['variant']:<12} {r['n_cells']:>4} "
              f"{r['savings_pct_avg']:>+7.2f}% {r['savings_pct_corpus']:>+8.2f}%")

    print("\n=== savings by model × variant (corpus-weighted) ===")
    print(f"{'model':<24} {'variant':<14} {'tok_v0':>7} {'tok':>7} "
          f"{'avg %':>8} {'$/1k':>8}")
    for r in sorted(out["summary_by_model_variant"],
                    key=lambda r: (r["model"], r["variant"])):
        print(f"  {r['model']:<22} {r['variant']:<14} "
              f"{r['tokens_v0_total']:>7} {r['tokens_total']:>7} "
              f"{r['savings_pct_avg']:>+7.2f}% "
              f"${r['usd_per_1k_prompts']:>6.4f}")

    print("\n=== monthly cost @ 1M calls (V0 → V4 all_safe) ===")
    print(f"{'model':<24} {'avg_v0':>7} {'avg_v4':>7} "
          f"{'$/M v0':>10} {'$/M v4':>10} {'$ saved':>10} {'save %':>8}")
    for r in sorted(out["cost_at_scale_1M_calls"],
                    key=lambda r: -r["monthly_savings_usd"]):
        print(f"  {r['model']:<22} {r['avg_prompt_tokens_v0']:>7.1f} "
              f"{r['avg_prompt_tokens_v4']:>7.1f} "
              f"${r['usd_per_1M_calls_v0']:>8.2f} "
              f"${r['usd_per_1M_calls_v4']:>8.2f} "
              f"${r['monthly_savings_usd']:>8.2f} "
              f"{r['monthly_savings_pct']:>+7.2f}%")


def _live_mode(args) -> dict:
    """Optional: hit real APIs. Skips providers without keys."""
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    methods = VARIANT_METHODS[args.variant]
    prompts = CORPUS[: args.max_calls]
    rows: list[dict] = []
    for prov in providers:
        # default model per provider
        model = {"openai": "gpt-4o-mini",
                 "anthropic": "claude-haiku-4.5",
                 "google": "gemini-1.5-flash"}.get(prov, prov)
        try:
            ad = get_adapter(prov, model=model)
        except Exception as e:
            print(f"[live] skip {prov}: {e}", file=sys.stderr)
            continue
        for p in prompts:
            sys_text = _apply_variant(p.text, methods)
            r = ad.call(system=sys_text,
                        user="Acknowledge in one short sentence.",
                        max_tokens=64)
            rows.append({
                "provider": prov,
                "model": ad.model,
                "prompt_id": p.id,
                "variant": args.variant,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "latency_ms": r.latency_ms,
                "error": r.error,
            })
            print(f"  [{prov}/{ad.model}] {p.id} {args.variant}: "
                  f"in={r.prompt_tokens} out={r.completion_tokens} "
                  f"lat={r.latency_ms}ms err={r.error}")
    return {"live_rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out",
                    default="bench_real/model_compare/results/model_compare.json")
    ap.add_argument("--live", action="store_true",
                    help="also hit real APIs (requires keys)")
    ap.add_argument("--providers", default="openai,anthropic,google")
    ap.add_argument("--variant", default="V4_all_safe",
                    choices=list(VARIANT_METHODS.keys()))
    ap.add_argument("--max-calls", type=int, default=2,
                    help="prompts per provider in --live mode")
    args = ap.parse_args()

    out = write(args.out)
    print(f"[model_compare] saved → {os.path.abspath(args.out)}")
    _print_offline_summary(out)

    if args.live:
        live = _live_mode(args)
        out["live"] = live
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
        print(f"\n[live] {len(live['live_rows'])} calls, see JSON for details")


if __name__ == "__main__":
    main()
