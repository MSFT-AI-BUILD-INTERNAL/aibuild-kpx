"""CLI for the offline code-preservation analysis.

Usage::

    python -m bench_real.analysis.run_code_analysis
    # → bench_real/analysis/results/code_preservation.json
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .code_preservation import analyze_corpus


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_real.analysis.run_code_analysis")
    ap.add_argument("--out", default=None,
                    help="output JSON (default: bench_real/analysis/results/"
                         "code_preservation.json)")
    args = ap.parse_args(argv)

    here = Path(__file__).resolve().parent
    out = Path(args.out) if args.out else here / "results" / "code_preservation.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    res = analyze_corpus()
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2),
                   encoding="utf-8")

    print(f"[analysis] {len(res['cells'])} cells across "
          f"{len(res['summary_by_variant'])} variants")
    print(f"[analysis] saved → {out}")
    print()
    print("variant | n  | tok_save | fence | inline | signpost | py_ast | idem | invar_ok")
    print("--------+----+----------+-------+--------+----------+--------+------+---------")
    for v, s in res["summary_by_variant"].items():
        print(f"{v:7} | {s['n']:2} | {s['token_savings_mean']:+7.2f}% | "
              f"{s['fences_preserved_total']}/{s['fences_in_total']:<2} | "
              f"{s['inlines_preserved_total']:>2}/{s['inlines_in_total']:<2}  | "
              f"{s['signposts_preserved_total']:>2}/{s['signposts_in_total']:<2}    | "
              f"{s['py_blocks_ast_stable']}/{s['py_blocks_in']:<2}    | "
              f"{s['idempotent_count']:>2}/{s['n']:<2} | "
              f"{s['invariants_pass_count']:>2}/{s['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
