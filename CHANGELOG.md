# Changelog

All notable changes to kpx are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
