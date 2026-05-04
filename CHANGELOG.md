# Changelog

All notable changes to kpx are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Benchmark traceability metadata** — `bench_real.runner` now accepts
  `--benchmark-version` and `--split`, and writes both fields into each result
  row alongside case `tags` for slice analysis.
- **Executive summary risk reporting** — `bench_real/views/p2_exec_summary.py`
  now reports quality mean with 95% confidence interval, cost per quality point,
  and the worst-performing task per variant relative to `V0`.
- **Benchmark improvement rounds** — added persisted multi-round benchmark
  review artifacts under `rounds/round-1` through `rounds/round-4` covering
  freshness, judge reliability, coverage expansion, and statistical reporting.

### Changed
- **Benchmark docs** — updated `bench_real/README.md` and the top-level README
  to describe split/version-aware benchmark runs and more decision-useful
  reporting outputs.

## [0.2.0] - 2026-04-25

### Fixed
- **B1 (CoT preserved)** — `minimize_system_prompt` no longer strips lines containing
  `think step by step` / `let's think step by step`. Karpathy and the CoT literature
  explicitly advocate this as a load-bearing prompt phrase.
- **B2 (technical signposts)** — `strip_polite` now preserves `Please note`,
  `Please refer`, `Please see`, `Please check`, `Please find`, `Please consult`,
  `Please observe`, `Please notice` (common in technical docs).
- **B3 (over-aggressive line removal)** — `_is_redundant_line` now requires the
  redundant phrase to make up at least 60% of the line content, preventing loss of
  multi-clause lines that incidentally contain a redundant substring.
- **B10 (code-fence preservation)** — `strip_known_facts` and `strip_polite` now
  skip content inside fenced code blocks (` ``` `) and inline backticks. Code
  comments mentioning "Python is a high-level interpreted language" are preserved.
- **B11 (whitespace cleanup)** — `strip_role_tags` collapses runs of horizontal
  whitespace introduced by removed tags but preserves newlines and indentation.
- **Idempotency** — `compress(compress(x)) == compress(x)` for all 300 corpus
  prompts × 8 transform configurations (296/300 = 98.7%, the 2 remaining cases
  are documented limitations of `inject ∘ compress` repeated chains).

### Added
- **Stdin support** — all CLI commands (`audit`, `compress`, `budget`) accept
  `-` as the file argument to read from standard input.
- **Smarter audit M09 trigger** — only flags missing filler-ban instruction when
  text actually looks like a system prompt (regex over `^You are`, `<|system|>`,
  `## System`, etc.) instead of any text > 200 chars.
- **`lossy_summary` flat-text fallback** — for text without headings/bullets,
  keeps leading content up to `max_chars` at sentence boundary (was emitting
  near-empty output before).
- **`lossy_summary` idempotency** — skips already-truncated text.
- **`bench_real/legacy/` benchmark suite** — 30-prompt × 10-transform × 1-iteration =
  300-round campaign measuring savings, idempotency, runtime, and content-loss
  safety probes (CoT, signposts, code blocks). Run via
  `python -m bench_real.legacy.runner`.

### Measured
On the 30-prompt corpus:
- `all_safe` (M03+M04+M19+M24+M25): **21.3% average token savings**
- 0 errors, 0 safety violations, 298/300 idempotent
- Avg runtime: 0.10ms per transform call

## [0.1.0] - 2026-04-25

### Added
- Initial release extracted from the [harness-check](https://github.com/) workspace.
- Core modules: `tokens`, `methods`, `compress`, `audit`, `cli`.
- 8 in-place safe transforms for prompt-side token reduction:
  - `M03` strip pretraining-known facts
  - `M04` minimize system prompt
  - `M09` inject no-filler instruction
  - `M15` `format_compare` (JSON / JSON-min / YAML / Markdown table)
  - `M19` heuristic lossy summary
  - `M24` strip polite filler
  - `M25` strip duplicated chat-template role tags
- `kpx audit` — static check against 30 Karpathy-aligned methods, scored 0–100.
- `kpx compress` — apply safe transforms in chain.
- `kpx budget` — 50% context-window rule (mirrors upstream harness).
- `kpx methods` — list all 30 methods with framing tags.
- `kpx format` — compare serialization formats by char count.
- 14 pytest cases.
- MIT License.
