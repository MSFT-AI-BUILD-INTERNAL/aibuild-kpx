"""View orchestrator. Generates all persona reports for a results.jsonl."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from . import p1_dev_report, p2_exec_summary, p3_safety_audit, p4_calibration, p6_i18n_report


def render_all(results_path: Path, out_dir: Path) -> dict[str, Path]:
    results_path = Path(results_path); out_dir = Path(out_dir)
    return {
        "P1": p1_dev_report.render(results_path, out_dir),
        "P2": p2_exec_summary.render(results_path, out_dir),
        "P3": p3_safety_audit.render(results_path, out_dir),
        "P4": p4_calibration.render(results_path, out_dir),
        "P6": p6_i18n_report.render(results_path, out_dir),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_real.views.render")
    ap.add_argument("results", help="path to results.jsonl")
    ap.add_argument("--out", default=None,
                    help="output dir (default: <results-parent>/views/)")
    args = ap.parse_args(argv)
    results = Path(args.results)
    out_dir = Path(args.out) if args.out else results.parent / "views"
    paths = render_all(results, out_dir)
    for k, p in paths.items():
        print(f"[render] {k:3} → {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
