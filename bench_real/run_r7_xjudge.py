"""Round 7 driver: cross-vendor LLM judge on representative subset.

5 models × V0/V4 × 10 cases × judge=github(meta/llama-4-scout).
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path


MODELS = [
    "openai/gpt-4o-mini",
    "microsoft/phi-4",
    "mistral-ai/ministral-3b",
    "meta/llama-3.3-70b-instruct",
    "deepseek/deepseek-v3-0324",
]
JUDGE = "meta/llama-4-scout-17b-16e-instruct"
RUN_ID = "r7-xjudge"
TIER = "lite"
VARIANTS = "V0,V4"
MAX_CASES = 10


def main() -> int:
    runs_dir = Path("bench_real/runs") / f"{TIER}-{RUN_ID}"
    runs_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    t_start = time.time()
    for i, model in enumerate(MODELS, 1):
        safe = model.replace("/", "__")
        out = runs_dir / f"{safe}.jsonl"
        cmd = [sys.executable, "-m", "bench_real.runner",
               "--tier", TIER, "--adapter", "github", "--model", model,
               "--variants", VARIANTS, "--max-cases", str(MAX_CASES),
               "--tier2-rate", "1.0",
               "--judge-adapter", "github", "--judge-model", JUDGE,
               "--cap-usd", "1e9",
               "--run-id", f"{RUN_ID}__{safe}",
               "--out", str(out)]
        print(f"\n[{i}/{len(MODELS)}] {model} → {out.name}")
        t0 = time.time()
        env = os.environ.copy(); env["PYTHONPATH"] = "."
        try:
            rc = subprocess.call(cmd, env=env, timeout=1200)
        except subprocess.TimeoutExpired:
            rc = -1
            print(f"  TIMEOUT after 1200s")
        dt = time.time() - t0
        n, n_err = 0, 0
        if out.exists():
            for line in out.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    n += 1
                    if r.get("error"):
                        n_err += 1
                except Exception:
                    pass
        summary.append({"model": model, "rc": rc, "rows": n,
                        "errors": n_err, "elapsed_s": round(dt, 1)})
        print(f"[{i}/{len(MODELS)}] {model} done: rows={n} err={n_err} dt={dt:.0f}s")
    (runs_dir / "_summary.json").write_text(json.dumps({
        "run_id": RUN_ID, "tier": TIER, "variants": VARIANTS,
        "max_cases": MAX_CASES, "judge": JUDGE,
        "elapsed_total_s": round(time.time() - t_start, 1),
        "per_model": summary,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
