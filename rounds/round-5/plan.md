## Round 5 — New-model refresh of full benchmark suite

### Goal
2026-05 시점의 신규 출시 모델을 벤치마크 모델 목록에 반영하고 전체 벤치마크를 재실행한다.

### Local evidence
- `bench_real/model_compare/__init__.py` MODELS 리스트는 2026-04 가격 기준이며, GPT-5.5 와 Gemini 3.1 Pro 가 누락되어 있다 (orin.agent.md 플래너 라인업 참조).
- `bench_real/runner.py` line 102 들여쓰기 오류로 `python -m bench_real.runner` 실행이 SyntaxError 로 막혀 있다.

### Proposed change set
1. `MODELS` 에 신규 모델 2종 추가:
   - `gpt-5.5` (OpenAI, exact tiktoken, $10.00 / 1M input — 2026-05 estimate)
   - `gemini-3.1-pro` (Google, heuristic 4 chars/token, $3.50 / 1M input — 2026-05 estimate)
2. `PRICING_DATE` 상수 신설, 결과 meta `pricing_date` 를 `2026-05` 로 갱신 (과거 비교 오염 방지: Round 4 권고 #3).
3. `bench_real/runner.py` 라인 102 들여쓰기 오류 수정 (1줄, 동작 변경 없음).
4. 벤치마크 재실행:
   - `python -m bench_real.model_compare.run` → `results/model_compare.json`
   - `python -m bench_real.runner --tier lite --adapter mock --cap-usd 0.01 --run-id r5-newmodels`
5. **라이브 API 호출은 본 라운드 범위 외** (사용자 명시 합의/예산 없음).

### Out of scope
- 가격표 정확성 검증 (사용자 override 가능, 명시적 estimate 라벨 유지).
- standard/deep tier 재실행 (mock adapter 한정에서는 lite 와 정성적 차이 없음).

### Cheap validation
- `pytest -q` 전체 통과.
- 결과 JSON 의 `meta.n_models == 12`, `pricing_date == "2026-05"`, cells 에 `gpt-5.5` / `gemini-3.1-pro` 존재.
