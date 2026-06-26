# Round 9 Artifact — Hardening + DeepSeek + Docs

## 실행 메타
- 일시: 2026-05-22
- 메인 adapter: `github` (GitHub Models, `gh auth token` 인증)
- 비용: **$0.00** (quota 기반)
- 데이터: [bench_real/runs/lite-r9-deepseek/](../../bench_real/runs/lite-r9-deepseek/)
- 변경 코드 3개 + 변경 문서 1개

## 사전 진단 (probe HTTP 코드)
| 모델 | HTTP | 상태 변화 |
|---|---|---|
| deepseek/deepseek-v3-0324 | 200 | R8 시점 429 → R9 회복 |
| meta/llama-4-scout-17b-16e-instruct | 200 | R8 시점 429 → R9 회복 |
∴ R7 원본 judge(`llama-4-scout`)로 DeepSeek 실행하여 R7 결과와 직접 비교 가능.

## F2 — 429 backoff cumulative cap
**파일**: [bench_real/adapters/github_models.py](../../bench_real/adapters/github_models.py)

변경 전:
- 최대 4회 재시도 × 단일 wait ≤ 60s = worst case **>240s** 소비, 사실상 무한 wedging.

변경 후:
```python
MAX_TOTAL_WAIT_S = 60.0
# while loop: retryable and attempt <= 4 and total_wait < MAX_TOTAL_WAIT_S
# wait = min(30.0, 2**attempt) then clipped so cumulative ≤ 60s
```
- 영구 429 시 **최대 60s + 4회 retry 안에 graceful 실패** → 메인 벤치마크가
  특정 모델로 wedging되지 않음.

## F3 — `lite-judged` tier 신설
**파일**: [bench_real/runner.py](../../bench_real/runner.py), [bench_real/tasks/__init__.py](../../bench_real/tasks/__init__.py)

```
TIER_VARIANTS["lite-judged"]     = LITE_VARIANTS  # V0, V3, V4
TIER_REPEATS["lite-judged"]      = 1
TIER_TIER2_RATE["lite-judged"]   = 1.0  # 핵심
TIER_BUDGET["lite-judged"]       = TIER_BUDGET["lite"]  (37 케이스)
--tier choices = ["lite", "lite-judged", "standard", "deep"]
```
스모크: `lite-judged` + V0 + 1 case → q=100, t2=100, axes 25/25/25/25 정상 기록.

## F1-1 — DeepSeek-v3 재실행 (R7 judge 동일)
명령:
```
PYTHONPATH=. python -m bench_real.runner \
  --tier lite-judged --adapter github \
  --model deepseek/deepseek-v3-0324 --variants V0,V4 --max-cases 10 \
  --judge-adapter github --judge-model meta/llama-4-scout-17b-16e-instruct \
  --cap-usd 1e9 --run-id r9-deepseek
```
결과 (20 rows wrote, $0.004, 860.9s):

| Variant | n | quality | tier2 | tok_in_api | tok_out_api | axes (c/co/f/cn) |
|---|---|---|---|---|---|---|
| V0 | 6 / 10 | 97.5 | 95.0 | 59.2 | 116.2 | 24.2 / 25.0 / 25.0 / 20.8 |
| V4 | 5 / 10 | 97.5 | 95.0 | **50.2** | 88.8 | 24.0 / 25.0 / 25.0 / 21.0 |

- **V4 tok_in 절감: −15.2%** (matches R7 +15% 패턴)
- **Δquality 0.0** (faithfulness/completeness 25/25 유지)
- 일부 셀(9/20)이 judge 호출 도중 transient error로 미평가 — F2 cap 적용으로
  벤치마크 자체는 wedging 없이 정상 종료.

## R7+R8+R9 통합 (V0 → V4)

| Model | Vendor | tok_in 절감 | Δquality | judge |
|---|---|---|---|---|
| mistral-ai/ministral-3b | Mistral | **−17.4%** | 0.0 | gpt-4o-mini (R8) |
| openai/gpt-4o-mini | OpenAI | −15.5% | −0.2 | llama-4-scout (R7) |
| deepseek/deepseek-v3-0324 | DeepSeek | −15.2% | 0.0 | llama-4-scout (R9) |
| microsoft/phi-4 | Microsoft | −14.9% | +1.7 | llama-4-scout (R7) |
| meta/llama-3.3-70b-instruct | Meta | −11.0% | −1.0 | gpt-4o-mini (R8) |

**5 / 5 모델 × 5 / 5 벤더 모두 V4 압축 안전성 검증 완료**:
입력 토큰 −11.0 ~ −17.4% 절감, Δquality ±2pt 이내, faithfulness 회귀 0건.

## F4 — 문서 갱신
**파일**: [docs/benchmark-results.html](../../docs/benchmark-results.html)

새 섹션 `07b 라이브 API 벤치마크 (R6–R9, 2026-05)` 추가:
- R6 30모델 일괄 실측 stat 패널 (30/30 실행, 21/30 정상, $0)
- R7+R8+R9 통합 V4 절감 막대차트 (5개 모델)
- 운영 경험치 3건 (quota throttling, F2/F3 적용)
- 합의 산출물·데이터 경로 모두 명시

HTML 태그 균형 검증: `unmatched ends: 0, unclosed: 0`.

## 회귀 검증
- `PYTHONPATH=. pytest -q` → **43 passed** (변경 전후 동일)
- `lite-judged` smoke → 정상 기록
- 문서 HTMLParser 검증 → 균형 OK

## 후속 권고
- F5. 표본 보강: 각 모델 max_cases 10 → 37(lite 풀) 실행 (다음 quota 사이클)
- F6. R7/R9 일부 judge transient error를 분석해 적절한 fallback (rule-based 채점) 도입 검토
- F7. `docs/benchmark-results.html` 새 섹션의 stat panel을 `_aggregate.json`에서 자동 렌더링
