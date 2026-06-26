## Round 6 — Live API benchmark via GitHub Models (all chat-capable models)

### Goal
외부 API 키 없이 호출 가능한 모든 LLM 에 대해 실 호출 벤치마크를 수행하고, V0 vs V3/V4 의 토큰 절감 + 응답 품질을 비교한다.

### Decision context (사용자 입력)
1. 사용자 키 없음 → GitHub Copilot/Models API 사용 합의.
2. 예산상한: 옵션 (a) "no cap" — GitHub Models 는 USD 과금 없이 quota 기반이므로 실제 사용자 비용 $0.
3. 케이스 범위: "전 케이스" — `lite` tier 가 이미 전 37 cases 를 커버 (V0,V3,V4 × repeats=1).
4. 모델: 현재 사용 가능한 모든 chat 모델 (43종 카탈로그 중 embeddings/reasoning 제외 ~30종).

### Local evidence
- `bench_real/adapters/{openai,anthropic,google}.py` 는 각 vendor API 키 필요 → 키 0개 상태에서 사용 불가.
- `gh auth status` 통과, `https://models.github.ai/catalog/models` 가 43종 응답.
- 인퍼런스 ping (openai/gpt-4o-mini, max_tokens=10) 정상 응답 확인.

### External evidence
- GitHub Models API 는 OpenAI Chat Completions 와 호환 (`/inference/chat/completions`).
- reasoning 계열 (o1/o3/o4, mai-ds-r1, phi-4-reasoning, deepseek-r1) 은 `system` role 비허용 + `max_completion_tokens` 사용 → 별도 분기 필요.
- 카탈로그에는 있지만 inference 미배포 모델 존재 가능 (e.g. ai21-jamba 확인됨).

### Proposed change set
1. **신규 adapter** `bench_real/adapters/github_models.py`
   - 토큰: `GITHUB_MODELS_TOKEN` → `GITHUB_TOKEN` → `gh auth token` 순서로 자동 해석.
   - 429/5xx 에 대해 exp backoff + Retry-After 존중 (최대 4회).
   - reasoning 모델은 system 을 user 에 fold + `max_completion_tokens` 사용.
2. **factory 등록**: `get_adapter("github")` 추가.
3. **runner choices** 에 `github`, `google` 추가.
4. **멀티-모델 wrapper** `bench_real/run_all_github.py`
   - 카탈로그 자동 페치, embeddings/reasoning 기본 제외, `--only`/`--include-reasoning` 옵션.
   - per-model subprocess + `--per-model-timeout` (기본 1800s) 로 stuck 모델 격리.
   - 결과: 모델별 `runs/<tier>-<run_id>/<safe_model>.jsonl` + 통합 `runs/<tier>-<run_id>.jsonl` + `_summary.json`.
5. **집계 스크립트** `bench_real/aggregate.py`
   - 모델 × 변형 별 평균 토큰/품질/지연/오류 + V0→V4 절감률.

### Execution (kicked off, in background)
```bash
PYTHONPATH=. nohup python -u -m bench_real.run_all_github \
  --tier lite --run-id r6-all --judge-adapter mock \
  --per-model-timeout 1200 > bench_real/runs/r6-all.log 2>&1 &
```
- 30 chat 모델 × 111 cells = ~3,330 호출
- ETA: 2–4 시간 (모델별 지연 편차 큼)
- judge=mock (cross-vendor LLM judge 는 호출량 2배 + rate-limit 위험 → 후속 라운드)

### Out of scope
- reasoning 모델 6종 (o1/o3/o4/r1/phi-4-reasoning): 별도 max_completion_tokens 분기는 구현했으나 1차 run 에서 제외 (응답 시간 + 토큰 폭증).
- standard/deep tier (V0..V5 × repeats=3, 6배 규모): 1차 lite 결과 검증 후 결정.
- 카탈로그 등록 후 inference 미배포 모델 (e.g. ai21-jamba): 자동 식별 불가, 결과에서 err=111 로 드러남.

### Cheap validation
- `PYTHONPATH=. pytest -q` 통과 (43 tests).
- 스모크 1: `runner --adapter github --model openai/gpt-4o-mini --max-cases 2` → 6/6 OK.
- 스모크 2: wrapper 로 2 모델 dry run → gpt-4o-mini 6 cells OK, phi-4-mini hang → timeout 추가.
