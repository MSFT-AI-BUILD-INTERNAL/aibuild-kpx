# kpx — Karpathy-Optimization

> **Prompt-side** LLM token optimization toolkit, designed as a complement to [`rtk`](https://github.com/rtk-ai/rtk) (which handles shell-output side).
> Implements **30 token-saving methods** ([docs/METHODS.md](docs/METHODS.md) · [methods.html ▶ view][doc-methods]), all tagged with one of Andrej Karpathy's 8 mental-model framings.

---

## 📊 Benchmarks

> **kpx v0.2.0 + R3/R5/R6/R7** — measured 2026-04-26, 4-track / 951 total cells

| Track | What | Cells | Headline |
|---|---|---:|---|
| **A — Legacy** | 300-round random corpus | 300 | **+21.28 %** mean token reduction |
| **B — Real LLM** | Plan v2, 7 personas × 3 vendors | 111 | **+20.95 %** weighted, byte-exact |
| **C — Deep code** | 90-cell static invariant analysis | 90 | found **B13** (M25 fenced-code indent) → fixed |
| **D — Model compare** | 10 models × 15 prompts × 3 runs | 450 | **+17.45 %** corpus-weighted, Anthropic 1.32× tokens vs OpenAI |

Benchmark reporting now records split/version metadata and highlights uncertainty
and task-level risk in the executive summary, so benchmark wins are easier to
trust in real deployment decisions.

**Full results & charts:** [benchmark-results.html ▶ view][doc-results] · **methodology:** [benchmark-plan.html ▶ view][doc-plan] · **method catalog:** [methods.html ▶ view][doc-methods] · **project overview:** [project-overview.html ▶ view][doc-overview]

<sub>HTML 페이지는 raw.githack.com 으로 즉시 렌더링됩니다. 저장소에서 보려면 [docs/](docs/) 폴더를 직접 참조하세요.</sub>

Top-line takeaway from Track D (model_compare, 450 cells, monthly cost @ 1 M req):

| Model | $/1 M tokens (in) | After kpx | Savings/month |
|---|---:|---:|---:|
| claude-opus-4.7 | $15.00 | $345 → $285 | **−$60** |
| gpt-5.4 | $5.00 | $75.7 → $62.6 | −$13.1 |
| claude-sonnet-4.7 | $3.00 | $69 → $57 | −$12 |
| gpt-4o | $2.50 | $37.8 → $31.3 | −$6.5 |
| gemini-2.5-pro | $2.50 | $37.6 → $31.1 | −$6.5 |

Reproduce: `python -m bench_real.runner --track model_compare`

### 토큰 소비를 어떻게 측정했나

벤치마크의 모든 셀은 **변형(variant)별 입력 프롬프트**(V0 원본 vs V3/V4/V5 kpx 압축본)를
동일한 케이스에 적용한 뒤, 세 가지 경로로 토큰을 동시에 기록합니다
([bench_real/runner.py](bench_real/runner.py), [bench_real/schema.py](bench_real/schema.py)):

| 필드 | 출처 | 용도 |
|---|---|---|
| `tokens_in_kpx` | kpx 휴리스틱 ([kpx/tokens.py](kpx/tokens.py) `estimate_tokens`) | 의존성 없는 기본 카운트. 영어 ≈ 4자/토큰, CJK ≈ 1자/토큰 |
| `tokens_in_tiktoken` | OpenAI `tiktoken` (`o200k_base` / `cl100k_base`) | 설치 시 OpenAI 계열 정확 카운트, 휴리스틱 검증용 |
| `tokens_in_api` / `tokens_out_api` / `tokens_total_api` | 실제 API 응답의 `usage` (prompt/completion/total) | **소비량의 정답값(ground truth)** |

- **절감률**은 같은 케이스의 V0 대비 압축 변형의 입력 토큰 감소분으로 계산합니다.
  `tokens_in_kpx`를 1차 지표로 쓰되, OpenAI 모델은 `tokens_in_tiktoken`과
  실제 `usage`로 교차 검증합니다(보고서의 "byte-exact"/가중 절감률).
- **비용**은 입·출력 토큰에 모델별 단가를 곱해 셀마다 `cost_usd`로 적립하고,
  전체 실행은 `CostCap` 상한으로 차단합니다
  ([bench_real/cost_cap.py](bench_real/cost_cap.py) `estimate_cost`).
- 휴리스틱 카운터는 하네스의 컨텍스트-50% 분할 규칙과 동일한 식을 공유하므로,
  감사(`kpx audit`)와 벤치마크가 같은 토큰 기준을 사용합니다.

CLI에서 단일 프롬프트의 토큰을 직접 확인하려면 `kpx budget prompt.md --window 200000`.

---

## Why kpx vs rtk?

| Layer | Tool | What |
|---|---|---|
| Shell output → LLM | **rtk** | Filters tool/git/test command output (60–90 % savings) |
| Prompt → LLM | **kpx** | Filters/compresses system prompts, RAG chunks, few-shot, history (this lib) |
| Both | use together | Stack savings end-to-end |

Built directly on Karpathy's 8 mental models:

- **F1 LLM OS** — context = RAM (budget tracking)
- **F2 Software 3.0** — prompt = code (lint / dead-code removal)
- **F3 Context Engineering** — "just the right info"
- **F4 Animals vs Ghosts** — externalize memory
- **F5 Verifiability** — structured output
- **F8 Pretraining = lossy compression** — strip known facts

Full taxonomy in [docs/methods.html ▶ view][doc-methods].

## Install

```bash
pip install -e .
# or, with optional YAML support for `kpx format`:
pip install -e '.[yaml]'
```

Zero runtime deps. Python 3.9+. Optional: `tiktoken` for exact OpenAI counts, `pyyaml` for `kpx format yaml`.

## CLI

```bash
# Audit a prompt against all 30 methods (returns score + recommendations)
kpx audit prompt.md

# Apply auto-safe compressions (M03/M04/M19/M24/M25 + M09 inject)
kpx compress prompt.md -o prompt.compressed.md

# Token budget for context window
kpx budget prompt.md --window 200000

# List implemented methods
kpx methods
```

## Python API

```python
from kpx import audit, compress, estimate_tokens
from kpx.methods import strip_known_facts, minimize_system_prompt, strip_role_tags

text = open("prompt.md").read()
report = audit(text)
print(report.score, report.recommendations)

compressed = compress(text, methods=["M03", "M24", "M25"])
print(estimate_tokens(text), "→", estimate_tokens(compressed))
```

All safe transforms preserve fenced/inline code blocks via `_apply_outside_code` — verified by **29 byte-exact regression tests** in [tests/test_regressions_v020.py](tests/test_regressions_v020.py).

## Implemented methods (v0.2.0)

| ID | Method | Status |
|---|---|---|
| M01 | RAM 인지 (budget tracking) | ✅ `kpx budget` |
| M03 | 사전학습 인코딩 사실 제거 | ✅ `strip_known_facts` |
| M04 | System prompt 최소화 (lint) | ✅ `minimize_system_prompt` |
| M09 | Output filler 제거 (지침 주입) | ✅ `inject_no_filler` |
| M15 | 직렬화 포맷 비교 | ✅ `format_compare` |
| M19 | Lossy 요약 (휴리스틱) | ✅ `lossy_summary` |
| M24 | Polite filler 제거 | ✅ `strip_polite` |
| M25 | 중복 role 태그 제거 | ✅ `strip_role_tags` (B13 코드 보존 fix) |
| (audit / external) | M02·M05·M06·M07·M08·M10·M11·M16·M17·M18·M20·M21·M22·M23·M26·M27·M28·M29·M30 | ⚠️ 권고만 (외부 의존 / 프로세스) |

전체 30 방법 카탈로그 → [docs/methods.html ▶ view][doc-methods].

## Tests

```bash
PYTHONPATH=. pytest tests/ -q   # 43/43 PASS (14 core + 29 regression)
```

## Roadmap (R8+ 후보)

- M11 prompt caching adapter (Anthropic / OpenAI prefix 추출)
- M27 constrained decoding helper (JSON schema 생성)
- M07 sliding-window 대화 요약 (LLM call 필요 → optional dep)
- VS Code 확장 / Copilot Chat hook

## License

MIT — see [LICENSE](LICENSE). Built on top of public Andrej Karpathy talks / blog posts cited in [docs/methods.html ▶ view][doc-methods].

[doc-results]: https://raw.githack.com/MSFT-AI-BUILD-INTERNAL/aibuild-kpx/main/docs/benchmark-results.html
[doc-plan]: https://raw.githack.com/MSFT-AI-BUILD-INTERNAL/aibuild-kpx/main/docs/benchmark-plan.html
[doc-methods]: https://raw.githack.com/MSFT-AI-BUILD-INTERNAL/aibuild-kpx/main/docs/methods.html
[doc-overview]: https://raw.githack.com/MSFT-AI-BUILD-INTERNAL/aibuild-kpx/main/docs/project-overview.html
