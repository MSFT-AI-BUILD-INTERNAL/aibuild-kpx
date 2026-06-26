# bench_real — kpx benchmark harness (plan v2)

Real benchmark suite for the [kpx](../kpx) prompt-side token optimizer.
Implements the persona-driven plan in
[../docs/benchmark-plan.html](../docs/benchmark-plan.html).

## Quick start (no API key needed)

```bash
# from repo root
python -m bench_real.runner --tier lite --adapter mock --cap-usd 0.01
python -m bench_real.views.render bench_real/runs/lite-<run-id>.jsonl
open bench_real/runs/views/p1_dev_report.html
```

The mock adapter is deterministic and free; it exercises every code path
end-to-end so you can validate plumbing before paying for tokens.

## Real runs

```bash
export OPENAI_API_KEY=sk-...
python -m bench_real.runner --tier lite --adapter openai \
  --model gpt-4o-mini --cap-usd 3.00 \
  --benchmark-version 2026-05 --split public

# Standard tier (M-A + M-B, n=3, ~$15 budget)
export ANTHROPIC_API_KEY=sk-ant-...
python -m bench_real.runner --tier standard --adapter openai \
    --model gpt-4o-mini --cap-usd 7.00 --judge-adapter anthropic \
  --judge-model claude-sonnet-4.7 --benchmark-version 2026-05 --split public
python -m bench_real.runner --tier standard --adapter anthropic \
    --model claude-sonnet-4.7 --cap-usd 8.00 --judge-adapter openai \
  --judge-model gpt-4o-mini --benchmark-version 2026-05 --split private-holdout
```

Re-running with the same `--run-id` resumes by skipping rows already in the
results file.

For traceability and real-world validation, each result row can now include:

- `benchmark_version` (e.g., `2026-05`)
- `split` (e.g., `public`, `private-holdout`)
- case `tags` for slice analysis

## Tiers

| Tier     | Cases | Variants            | Repeats | Tier-2 spot | Models            | Budget |
|----------|------:|---------------------|--------:|------------:|-------------------|-------:|
| lite     |    37 | V0, V3, V4          |       1 |          0% | M-A only          |  ~$3   |
| standard |    72 | V0..V5              |       3 |         20% | M-A + M-B         | ~$15   |
| deep     |    77 | V0..V5              |       5 |         20% | M-A + M-B + M-C   | ~$60   |

## Layout

```
bench_real/
  __init__.py           module marker
  schema.py             Case, CellResult dataclasses
  variants.py           V0..V5 — system-prompt transforms
  tokenizers.py         kpx + tiktoken counts
  cost_cap.py           USD price table + CostCap
  adapters/
    __init__.py         CallResult, get_adapter()
    mock.py             deterministic stub
    openai.py           Chat Completions via urllib
    anthropic.py        Messages API via urllib
  scorers/
    __init__.py
    rule_based.py       pytest, json_schema, rouge_l, chrf, refusal_label, exact, tool_choice
    code_sandbox.py     subprocess-isolated Python execution (timeout=5s)
    chrf.py             character n-gram F-score
    rouge.py            LCS-based ROUGE-L
    llm_judge.py        4-axis cross-vendor LLM judge
  tasks/
    t01_coding.json     10 Python function tasks
    t03_docs.json       6 doc summaries (3 EN + 3 KO)
    t04_json.json       6 JSON extraction tasks
    t06_safety.json     10 safety cases (5 refuse + 5 answer)
    t07_translation.json 5 KR↔EN translations
  views/
    p1_dev_report.py    HTML heatmap (task × variant)
    p2_exec_summary.py  1-page MD with $/month scenarios
    p3_safety_audit.py  JSON + SVG badge (RED/GREEN)
    p4_calibration.py   kpx vs API-reported tokens
    p6_i18n_report.py   per-language token + quality table
    render.py           orchestrator
  runner.py             entrypoint
  judge_prompt.md       LLM-as-judge instructions
  decisions_template.md RED/GREEN matrix template (post-run)
  runs/                 outputs (gitignored)
```

## Variants (per plan v2 §7)

- **V0** — raw (control)
- **V1** — `M03` only (strip known facts)
- **V2** — `M24` only (strip polite)
- **V3** — `M03 + M24 + M25`
- **V4** — `M03 + M04 + M19 + M24 + M25` (all SAFE)
- **V5** — V4 + `inject_no_filler`

All variants apply to the **system prompt only**. The user message is
always passed through unchanged — this is kpx's actual scope.

## Persona thresholds (release blocker)

| Persona | Metric                              | Threshold           |
|---------|-------------------------------------|---------------------|
| P1 dev  | task pass rate vs V0                | Δ ≥ −2 pt           |
| P2 exec | input-token reduction               | ≥ 5% (target 8%)    |
| P3 safety | refusal preservation              | Δ ≥ −2 pt **(blocker)** |
| P4 calib | kpx vs API-reported error          | mean abs ≤ 5%       |
| P6 i18n | per-language Δquality                | Δ ≥ −2 pt for any lang |

If P3 fails, no release. Other personas: investigate before shipping.

## Practical reporting updates

`p2_exec_summary.md` now includes:

- quality mean with 95% confidence interval per variant
- cost per quality point (efficiency signal)
- task-level risk view (worst task delta vs V0)

This helps detect variants that look good on aggregate but regress on specific
task families.

## Cost cap

`--cap-usd N` enforces a hard ceiling using the price table in
`cost_cap.py`. The runner stops cleanly when the cap is hit; resume to
continue from the next free cell.

## Reproducibility

- `--seed 42` (default) seeds tier-2 spot-check sampling.
- `temperature=0.0` for both target and judge adapters.
- `--run-id <name>` makes resume-able runs (`runs/<tier>-<run-id>.jsonl`).

## Updating `docs/benchmark-results.html` §07b (live API panel)

Per-model JSONLs under `bench_real/runs/lite-r*-*/` feed the marker-bracketed
panel in section 07b of `docs/benchmark-results.html`. The workflow
(`--list-panels` → `--dry-run` preview → `--backup` apply, plus notes on
`--diff-out`, panel-id safety, F9 `fb=k` tag, and determinism) is documented
in [`../CONTRIBUTING.md` ▶ Updating the live-benchmark panel](../CONTRIBUTING.md#updating-the-live-benchmark-panel-docsbenchmark-resultshtml-07b).
Regression-guarded by [`../tests/test_render_results_panel.py`](../tests/test_render_results_panel.py).

## Legacy v0.2.0 self-QA suite

The previous zero-dependency 300-round campaign (30 prompts × 10 transforms,
source of the **+21.36% all_safe** claim in CHANGELOG) is preserved at
[`legacy/`](legacy/). Run with:

```bash
python -m bench_real.legacy.runner
# → bench_real/legacy/results.json
```

It needs no API keys and no network — purely a token-counting / safety-probe
benchmark over kpx itself.
