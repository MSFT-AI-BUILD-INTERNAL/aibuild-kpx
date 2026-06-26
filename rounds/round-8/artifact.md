# Round 8 Artifact — R7 Timeout Retry Results

## 실행 메타
- 일시: 2026-05-21 (R7 직후 quota 회복 시도 2회)
- 메인 adapter: `github` (GitHub Models)
- Judge: `openai/gpt-4o-mini` (R7의 `llama-4-scout`가 영구 429 throttled로 교체)
- 비용: **$0.00** (quota 기반)
- 데이터: [bench_real/runs/lite-r8-retry-v2/](../../bench_real/runs/lite-r8-retry-v2/)
- 로그: [bench_real/runs/r8-retry-v2.log](../../bench_real/runs/r8-retry-v2.log)
- 드라이버: [bench_real/run_r8_retry.py](../../bench_real/run_r8_retry.py)

## 진단 결과 (R7 timeout 원인 규명)
직접 curl probe로 모델별 HTTP 상태 확인:

| 모델 | 역할 | HTTP | 비고 |
|---|---|---|---|
| mistral-ai/ministral-3b | main | 200 | live |
| meta/llama-3.3-70b-instruct | main | 200 | live |
| deepseek/deepseek-v3-0324 | main | **429** | quota 차단 |
| meta/llama-4-scout-17b-16e-instruct | **R7 judge** | **429** | **영구 차단 → R7 timeout 원인** |
| openai/gpt-4o-mini | 신 judge | 200 | live |

결론: R7에서 `ministral-3b`·`llama-3.3-70b`가 0행이었던 것은 **메인 모델 문제가
아니라 judge call(`llama-4-scout`)의 429 영구 차단**으로 runner가 backoff retry를
반복하면서 1200s timeout에 도달했기 때문이다.

## 모델별 결과

| Model | Variant | n | quality | tier2 | tok_in_api | tok_out_api |
|---|---|---|---|---|---|---|
| mistral-ai/ministral-3b | V0 | 5/5 | **99.5** | 99.0 | 58.6 | 43.0 |
| mistral-ai/ministral-3b | V4 | 5/5 | **99.5** | 99.0 | **48.4** | 42.8 |
| meta/llama-3.3-70b-instruct | V0 | 5/5 | 97.5 | 95.0 | 89.4 | 83.4 |
| meta/llama-3.3-70b-instruct | V4 | 5/5 | 96.5 | 93.0 | **79.6** | 95.4 |
| deepseek/deepseek-v3-0324 | — | 0/10 | — | — | — | — |

집계: [bench_real/runs/lite-r8-retry-v2/_aggregate.json](../../bench_real/runs/lite-r8-retry-v2/_aggregate.json)

## V0 → V4 델타

| Model | tok_in 절감 | Δquality | Δtier2 |
|---|---|---|---|
| mistral-ai/ministral-3b | **−17.4%** | 0.0 | 0.0 |
| meta/llama-3.3-70b-instruct | **−11.0%** | −1.0 | −2.0 |

## Judge axes (success-only)

```
ministral-3b    V0: correctness 25.0  completeness 25.0  faithfulness 25.0  conciseness 24.0
ministral-3b    V4: correctness 25.0  completeness 25.0  faithfulness 25.0  conciseness 24.0
llama-3.3-70b   V0: correctness 25.0  completeness 24.0  faithfulness 25.0  conciseness 21.0
llama-3.3-70b   V4: correctness 25.0  completeness 23.0  faithfulness 25.0  conciseness 20.0
```

- ministral-3b: 4축 V0=V4 동일 (perfect 보존)
- llama-3.3-70b: faithfulness/correctness 25/25 유지, completeness/conciseness 각 −1
  (Δquality −1.0의 분해)

## 핵심 발견
1. **H1 검증 ✅** : 두 모델 모두 tok_in −11% ~ −17% 절감, Δquality 0 ~ −1.0pt (±2pt 이내).
2. **H2 검증 ✅** : 두 모델 모두 faithfulness/correctness 25/25 — 의미 왜곡 0건.
3. **R7+R8 합산** : OpenAI/Microsoft/Mistral/Meta 4개 벤더 완료, **모두 V4가 안전**.
4. R7 timeout의 진짜 원인은 judge 모델 throttle이었음. main 모델 책임이 아니며,
   `bench_real/adapters/github_models.py`의 429 backoff 정책이 무한 재시도에 가까운
   동작(4회 재시도 × Retry-After=수십초)을 유발했다는 함의도 있음 — 후속 개선 후보.

## 한계
- DeepSeek-v3-0324: HTTP 429 영구 차단으로 0행. 모델 자체의 daily quota 소진 추정.
  → F1-1로 차기 라운드 이월.
- max-cases 5라는 작은 표본. 그러나 within-model paired comparison(같은 case_id의
  V0 vs V4)으로 통계적 노이즈는 R7과 동등.
- judge가 R7과 다름(`gpt-4o-mini` vs `llama-4-scout`) → R7 절대 점수와 직접 비교 불가.

## 회귀 검증
- `PYTHONPATH=. pytest -q` → 43 passed (변경 없음, R7과 동일).

## R7+R8 통합 V0→V4 결과 표

| Model | Vendor | tok_in 절감 | Δquality | judge |
|---|---|---|---|---|
| openai/gpt-4o-mini | OpenAI | −15.5% | −0.2 | llama-4-scout (R7) |
| microsoft/phi-4 | Microsoft | −14.9% | +1.7 | llama-4-scout (R7) |
| mistral-ai/ministral-3b | Mistral | **−17.4%** | 0.0 | gpt-4o-mini (R8) |
| meta/llama-3.3-70b-instruct | Meta | −11.0% | −1.0 | gpt-4o-mini (R8) |
| deepseek/deepseek-v3-0324 | DeepSeek | TIMEOUT | — | — |

**4/5 모델, 4/5 벤더에서 V4 압축 효능 검증.**

## 후속 권고
- F1-1. DeepSeek-v3 quota 회복 후 재시도 (다음 daily reset)
- F2. github_models 어댑터의 429 backoff에 최대 누적 시간 cap 추가 (예: 60s 후 포기)
- F3. `lite-judged` tier 추가 (`tier2_rate=1.0` 하드코딩)로 CLI flag 의존 제거
- F4. [docs/benchmark-results.html](../../docs/benchmark-results.html)에 R7+R8 통합 표 반영
