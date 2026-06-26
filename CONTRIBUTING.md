# Contributing to kpx

Thanks for considering a contribution!

## Scope
kpx covers **prompt-side** LLM token optimization. Shell-output filtering belongs to
[`rtk`](https://github.com/rtk-ai/rtk). PRs that overlap with rtk's surface (filtering
git/cargo/pytest output) will likely be closed.

## Development setup

```bash
git clone <your-fork-url>
cd kpx
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

## Adding a new method

1. Locate the method ID (`M01`–`M30`) in [docs/METHODS.md](docs/METHODS.md).
2. If the transform is **static and safe** (no LLM call, idempotent on already-clean
   text), implement it in `kpx/methods.py` and register in `SAFE_TRANSFORMS`.
3. If it requires an external LLM / vector DB / vendor SDK, surface it as an
   **audit recommendation** in `kpx/audit.py` and document the optional dep.
4. Add at least one positive and one negative test in `tests/`.
5. Update `CHANGELOG.md` under `## [Unreleased]`.

## PR checklist
- [ ] `pytest -q` green
- [ ] No new required runtime deps (optional deps go behind `extras_require`)
- [ ] Method ID cited in commit message and PR title (e.g. `feat(M11): prompt cache adapter`)
- [ ] Docs updated if user-facing behavior changes

## Code style
- Pure stdlib for the core. PyYAML and similar are optional.
- Type hints encouraged but not enforced.
- Keep `kpx audit` self-applying: `kpx audit README.md` should not regress in score.

## Updating the live-benchmark panel (`docs/benchmark-results.html` §07b)

Section 07b is auto-generated from per-model JSONLs under `bench_real/runs/lite-r*-*/`
and bracketed by HTML markers (`<!-- panel:07b:start ... -->` / `<!-- panel:07b:end -->`).
Use [bench_real/render_results_panel.py](bench_real/render_results_panel.py).

```bash
# 1) discover existing markers in the doc
PYTHONPATH=. python -m bench_real.render_results_panel \
  --list-panels docs/benchmark-results.html

# 2) preview the change (no file is written; docs unchanged)
PYTHONPATH=. python -m bench_real.render_results_panel \
  --inputs r7=bench_real/runs/lite-r7-xjudge \
           r8=bench_real/runs/lite-r8-retry-v2 \
           r9=bench_real/runs/lite-r9-deepseek \
  --out bench_real/runs/_panel_07b.html \
  --patch-doc docs/benchmark-results.html --dry-run

# 3) apply the change, keeping a one-generation backup
PYTHONPATH=. python -m bench_real.render_results_panel \
  --inputs r7=... r8=... r9=... \
  --out bench_real/runs/_panel_07b.html \
  --patch-doc docs/benchmark-results.html --backup
```

Adding a new round? Drop its `lite-r<N>-<tag>/*.jsonl` directory under
`bench_real/runs/`, append `r<N>=path` to `--inputs`, and re-run step 3. The
fragment is regenerated deterministically (same inputs → same MD5).

Notes:
- `--dry-run` and `--diff-out PATH` are orthogonal: combine them to write a
  reviewable diff while leaving the doc untouched.
- A wrong `--panel <id>` exits non-zero before touching the file.
- Rows with `judge_axes.fallback == "rule_based"` (judge failed, see runner F6)
  are counted and surfaced as `fb=k` in the panel row; absent when k=0.
- Unit tests for this workflow live in
  [tests/test_render_results_panel.py](tests/test_render_results_panel.py).

