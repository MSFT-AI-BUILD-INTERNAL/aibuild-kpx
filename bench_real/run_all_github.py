"""Loop bench_real.runner over all chat-capable GitHub Models.

Usage:
    PYTHONPATH=. python -m bench_real.run_all_github \
        --tier standard --run-id r6-all --cap-usd 1e9

- Skips embeddings and reasoning models by default (use --include-reasoning to opt in;
  reasoning models are slow + handled separately by the adapter).
- Calls bench_real.runner as a subprocess for each model so failures isolate.
- Writes one JSONL per model under bench_real/runs/<tier>-<run_id>/<safe_model>.jsonl
  then concatenates into bench_real/runs/<tier>-<run_id>.jsonl on completion.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


CATALOG_URL = "https://models.github.ai/catalog/models"

EMBEDDING_IDS = {"openai/text-embedding-3-small", "openai/text-embedding-3-large"}

REASONING_PREFIXES = ("openai/o1", "openai/o3", "openai/o4",
                      "microsoft/phi-4-reasoning",
                      "microsoft/phi-4-mini-reasoning",
                      "microsoft/mai-ds-r1",
                      "deepseek/deepseek-r1")


def _gh_token() -> str:
    tok = os.environ.get("GITHUB_MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    return subprocess.run(["gh", "auth", "token"], capture_output=True,
                          text=True, check=True).stdout.strip()


def list_chat_models(include_reasoning: bool = False) -> list[str]:
    req = urllib.request.Request(CATALOG_URL, headers={
        "Authorization": f"Bearer {_gh_token()}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        catalog = json.loads(resp.read().decode("utf-8"))
    out = []
    for m in catalog:
        mid = m["id"]
        if mid in EMBEDDING_IDS:
            continue
        if not include_reasoning and any(mid.startswith(p) for p in REASONING_PREFIXES):
            continue
        out.append(mid)
    return sorted(out)


def _safe(name: str) -> str:
    return name.replace("/", "__")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["lite", "standard", "deep"], default="lite")
    ap.add_argument("--run-id", default=time.strftime("r6-%Y%m%d-%H%M%S"))
    ap.add_argument("--cap-usd", type=float, default=1e9,
                    help="per-model cost cap; default effectively unbounded")
    ap.add_argument("--judge-adapter", default="github")
    ap.add_argument("--judge-model", default="meta/llama-3.3-70b-instruct",
                    help="cross-publisher judge; default Llama 3.3 70B")
    ap.add_argument("--include-reasoning", action="store_true")
    ap.add_argument("--max-cases", type=int, default=None)
    ap.add_argument("--only", default=None,
                    help="comma-separated subset of model IDs (overrides catalog)")
    ap.add_argument("--per-model-timeout", type=int, default=1800,
                    help="per-model wallclock timeout in seconds (default 30 min)")
    args = ap.parse_args()

    if args.only:
        models = [m.strip() for m in args.only.split(",") if m.strip()]
    else:
        models = list_chat_models(include_reasoning=args.include_reasoning)

    print(f"[run_all_github] tier={args.tier} run_id={args.run_id} "
          f"models={len(models)} judge={args.judge_adapter}/{args.judge_model}")
    for m in models:
        print(f"  - {m}")

    runs_dir = Path("bench_real/runs") / f"{args.tier}-{args.run_id}"
    runs_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []
    t_start = time.time()
    for i, model in enumerate(models, 1):
        out_path = runs_dir / f"{_safe(model)}.jsonl"
        cmd = [
            sys.executable, "-m", "bench_real.runner",
            "--tier", args.tier,
            "--adapter", "github",
            "--model", model,
            "--judge-adapter", args.judge_adapter,
            "--judge-model", args.judge_model,
            "--cap-usd", str(args.cap_usd),
            "--run-id", f"{args.run_id}__{_safe(model)}",
            "--out", str(out_path),
        ]
        if args.max_cases:
            cmd += ["--max-cases", str(args.max_cases)]
        print(f"\n[{i}/{len(models)}] {model} → {out_path.name}")
        t0 = time.time()
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        try:
            rc = subprocess.call(cmd, env=env, timeout=args.per_model_timeout)
        except subprocess.TimeoutExpired:
            print(f"[{i}/{len(models)}] {model} TIMEOUT after "
                  f"{args.per_model_timeout}s, moving on")
            rc = -1
        dt = time.time() - t0
        # Count rows and errors.
        n, n_err = 0, 0
        if out_path.exists():
            with out_path.open() as f:
                for line in f:
                    try:
                        row = json.loads(line)
                        n += 1
                        if row.get("error"):
                            n_err += 1
                    except Exception:
                        pass
        summary.append({
            "model": model,
            "rc": rc,
            "rows": n,
            "errors": n_err,
            "elapsed_s": round(dt, 1),
        })
        print(f"[{i}/{len(models)}] {model} done: rows={n} err={n_err} "
              f"rc={rc} dt={dt:.0f}s")

    # Concatenate per-model JSONLs into one combined file.
    combined = Path("bench_real/runs") / f"{args.tier}-{args.run_id}.jsonl"
    with combined.open("w", encoding="utf-8") as out:
        for s in summary:
            p = runs_dir / f"{_safe(s['model'])}.jsonl"
            if p.exists():
                out.write(p.read_text(encoding="utf-8"))
    summary_path = runs_dir / "_summary.json"
    summary_path.write_text(json.dumps({
        "run_id": args.run_id,
        "tier": args.tier,
        "judge": f"{args.judge_adapter}/{args.judge_model}",
        "elapsed_total_s": round(time.time() - t_start, 1),
        "n_models": len(models),
        "per_model": summary,
        "combined_jsonl": str(combined),
    }, indent=2, ensure_ascii=False))
    print(f"\n[run_all_github] combined → {combined}")
    print(f"[run_all_github] summary  → {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
