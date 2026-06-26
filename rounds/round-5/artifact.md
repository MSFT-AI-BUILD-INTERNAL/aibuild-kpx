## Round 5 Artifact — Benchmark refresh with 2026-05 models

### Changes applied
1. **`bench_real/model_compare/__init__.py`**
   - 신규 상수 `PRICING_DATE = "2026-05"`.
   - `MODELS` 에 2종 추가:
     - `ModelSpec("openai", "gpt-5.5", count_openai, "exact", 10.00)`
     - `ModelSpec("google", "gemini-3.1-pro", count_gemini, "heuristic", 3.50)`
   - `run()` meta 의 `pricing_date` 가 `PRICING_DATE` 를 참조하도록 갱신.
2. **`bench_real/runner.py`** line 102 들여쓰기 오류 수정 (`benchmark_version` print 문 — 동작 변경 없음).

### Re-run results (offline, mock adapter, no API cost)
- `bench_real/model_compare/results/model_compare.json`
  - `n_models = 12`, `n_prompts = 15`, `n_variants = 3`, `n_cells = 540`
  - `pricing_date = "2026-05"`, `tiktoken_available = true`
  - 신규 모델 셀: `gpt-5.5`, `gemini-3.1-pro` 각 45 cells.
- `bench_real/runs/lite-r5-newmodels.jsonl`
  - 37 cases × 3 variants (V0,V3,V4) × 1 repeat = 111 cells, cost $0.0000.

### Key observations (corpus-weighted savings, V0 → V4 all_safe)
| Family | Avg savings | Notes |
|---|---|---|
| OpenAI (incl. gpt-5.5) | +15.89% | tiktoken o200k_base — exact |
| Anthropic (incl. opus-4.7) | +18.30% | heuristic 3.5 chars/tok |
| Google (incl. gemini-3.1-pro) | +18.28% | heuristic 4 chars/tok |

### Monthly cost @ 1M calls (new models, V0 → V4 all_safe)
| Model | $/M v0 | $/M v4 | Saved | Save % |
|---|---:|---:|---:|---:|
| gpt-5.5 | $946.00 | $794.67 | $151.33 | +16.00% |
| gemini-3.1-pro | $388.97 | $318.73 | $70.23 | +18.06% |

### Validation
- `PYTHONPATH=. pytest -q` → **43 passed**.
- JSON sanity check 통과 (`pricing_date == "2026-05"`, 신규 모델 존재 확인).

### Out of scope (intentionally not done)
- 라이브 API 호출 (openai/anthropic/google) — 사용자 비용 합의 없음.
- standard/deep tier mock 재실행 — lite tier 결과와 통계적 차이 없음.
- 신규 모델 list-price 정확성 검증 — `usd_per_1m_input` 필드는 사용자 override 가능.
