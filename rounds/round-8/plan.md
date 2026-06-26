# Round 8 Plan — R7 Timeout 3종 재실행 (F1 후속)

## 배경
R7에서 `meta/llama-4-scout-17b-16e-instruct`를 cross-vendor judge로 사용했는데,
무료 GitHub Models quota가 누적 사용으로 인해 해당 judge 모델이 **HTTP 429 영구
throttle**되었음 (R7 종료 후 30분, 1시간이 지나도 동일).
직접 probe로 확인:
- mistral-ai/ministral-3b → HTTP 200 (live)
- meta/llama-3.3-70b-instruct → HTTP 200 (live)
- deepseek/deepseek-v3-0324 → HTTP 429
- meta/llama-4-scout-17b-16e-instruct → HTTP 429 (judge — 차단됨)
∴ R7 timeout은 메인 모델 문제가 아니라 **judge 호출 영구 차단**으로 인한 행 미생성.

## 변경 사항 (스코프 축소)
- **Judge 모델 교체**: `meta/llama-4-scout-17b-16e-instruct` → `openai/gpt-4o-mini`
  - 사유: 3개 타깃(Mistral, Meta, DeepSeek) 모두에 대해 cross-vendor 유지 + 살아있음
  - 분석 한계: 절대 점수는 R7과 직접 비교 불가, **within-model V0/V4 delta**만 유효
- **케이스 축소**: max-cases 10 → 5 (quota 부담 감소)
- **per-model timeout**: 1200s → 900s
- 새 드라이버: [bench_real/run_r8_retry.py](../../bench_real/run_r8_retry.py)

## 합의 산출물
- `rounds/round-8/{plan.md, votes.json, artifact.md, evaluation.md}`
- 데이터: `bench_real/runs/lite-r8-retry-v2/*.jsonl` + `_aggregate.json`,
  `_summary.json`, `bench_real/runs/r8-retry-v2.log`

## 가설
H1. R7과 동일하게 V4가 입력 토큰 ≥10% 절감, quality 변화 ±2pt 이내.
H2. faithfulness 회귀 0 (이전 R7과 동일 보장).

## 위험
- DeepSeek-v3 가용성: probe 시점 429. 본 실행에서도 0행 가능성 높음.
