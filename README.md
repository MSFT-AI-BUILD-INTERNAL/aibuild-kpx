# kpx — Karpathy-Optimization

> **Prompt-side** LLM token optimization toolkit, designed as a complement to [`rtk`](https://github.com/rtk-ai/rtk) (which handles shell-output side).
> Implements 30 token-saving methods catalogued in [docs/METHODS.md](docs/METHODS.md), all tagged with one of Andrej Karpathy's 8 mental-model framings.

## Why kpx vs rtk?

| Layer | Tool | What |
|---|---|---|
| Shell output → LLM | **rtk** | Filters tool/git/test command output (60–90% savings) |
| Prompt → LLM | **kpx** | Filters/compresses system prompts, RAG chunks, few-shot, history (this lib) |
| Both | use together | Stack savings end-to-end |

Built directly on Karpathy's 8 mental models:
- **F1 LLM OS** — context = RAM (budget tracking)
- **F2 Software 3.0** — prompt = code (lint/dead-code removal)
- **F3 Context Engineering** — "just the right info"
- **F4 Animals vs Ghosts** — externalize memory
- **F5 Verifiability** — structured output
- **F8 Pretraining = lossy compression** — strip known facts

## Install

```bash
pip install -e .
# or, with optional YAML support for `kpx format`:
pip install -e '.[yaml]'
```

## CLI

```bash
# Audit a prompt against all 30 methods (returns score + recommendations)
kpx audit prompt.md

# Apply auto-safe compressions (M03/M04/M09/M15/M24/M25)
kpx compress prompt.md -o prompt.compressed.md

# Token budget for context window
kpx budget prompt.md --window 200000

# List implemented methods
kpx methods
```

## Python API

```python
from kpx import audit, compress, estimate_tokens
from kpx.methods import strip_fillers, strip_known_facts, minimize_system_prompt

text = open("prompt.md").read()
report = audit(text)
print(report.score, report.recommendations)

compressed = compress(text, methods=["M03", "M09", "M24"])
print(estimate_tokens(text), "→", estimate_tokens(compressed))
```

## Implemented methods (MVP)

| ID | Method | Status |
|---|---|---|
| M01 | RAM 인지 (budget tracking) | ✅ `kpx budget` |
| M03 | 사전학습 인코딩 사실 제거 | ✅ `strip_known_facts` |
| M04 | System prompt 최소화 (lint) | ✅ `minimize_system_prompt` |
| M09 | Output filler 제거 (지침 생성) | ✅ `strip_fillers` (instruction injector) |
| M15 | 직렬화 포맷 비교 | ✅ `format_compare` |
| M19 | Lossy 요약 (휴리스틱) | ✅ `lossy_summary` |
| M24 | Polite filler 제거 | ✅ `strip_polite` |
| M25 | 중복 role 태그 제거 | ✅ `strip_role_tags` |
| (audit-only) | M02·M05·M06·M07·M08·M10·M11·M16·M17·M18·M20·M21·M22·M23·M26·M27·M28·M29 | ⚠️ 권고만 (구현 외부 의존) |

## Roadmap (R53+ 후보)
- M11 prompt caching adapter (Anthropic / OpenAI prefix 추출)
- M27 constrained decoding helper (JSON schema 생성)
- M07 sliding-window 대화 요약 (LLM call 필요 → optional dep)
- VS Code 확장 / Copilot Chat hook

## License
MIT
