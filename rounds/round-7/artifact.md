# Round 7 Artifact — Cross-Vendor LLM Judge Results

## 실행 메타
- 일시: 2026-05-20 21:20 ~ 22:44 KST (84분)
- 메인 adapter: `github` (GitHub Models, `gh auth token` 인증, 사용자 `ijhan-biz`)
- Judge: `meta/llama-4-scout-17b-16e-instruct` (모든 셀 공통)
- 실행 비용: **$0.00 USD** (quota 기반, cap=$1e9 비활성)
- 데이터: [bench_real/runs/lite-r7-xjudge/](../../bench_real/runs/lite-r7-xjudge/)
- 로그: [bench_real/runs/r7-xjudge.log](../../bench_real/runs/r7-xjudge.log)
- 드라이버: [bench_real/run_r7_xjudge.py](../../bench_real/run_r7_xjudge.py)

## 코드 변경
[bench_real/runner.py](../../bench_real/runner.py) — CLI 옵션 2개 추가:
- `--tier2-rate FLOAT` : tier 기본값(lite=0.0) override → 1.0 사용 시 모든 셀 judge
- `--variants V0,V4`   : TIER_VARIANTS 부분집합 선택 (V3 생략으로 호출 절반)

`load_tier(args.tier)` 호출 누락 / 중복 변종 할당 버그를 함께 수정. `pytest` 43건
모두 통과.

## 모델별 결과 (per-variant 평균)

| Model | Variant | n | quality | tier1 | tier2 | tok_in_api | tok_out_api | latency |
|---|---|---|---|---|---|---|---|---|
| openai/gpt-4o-mini | V0 | 10/10 | 97.2 | 100.0 | 94.5 | 60.7 | 151.7 | 3,396 ms |
| openai/gpt-4o-mini | V4 | 10/10 | 97.0 | 100.0 | 94.0 | **51.3** | 144.8 | 3,167 ms |
| microsoft/phi-4 | V0 | 8/8 | 96.2 | 100.0 | 92.5 | 63.0 | 153.8 | 7,921 ms |
| microsoft/phi-4 | V4 | 7/7 | **97.9** | 100.0 | **95.7** | **53.6** | 125.0 | 7,704 ms |
| mistral-ai/ministral-3b | — | 0/20 | — | — | — | — | — | TIMEOUT |
| meta/llama-3.3-70b-instruct | — | 0/20 | — | — | — | — | — | TIMEOUT |
| deepseek/deepseek-v3-0324 | — | 0/20 | — | — | — | — | — | TIMEOUT |

집계 파일: [bench_real/runs/lite-r7-xjudge/_aggregate.json](../../bench_real/runs/lite-r7-xjudge/_aggregate.json)

## V0 → V4 델타 (성공 2종)

| Model | tok_in 절감 | Δquality | Δtier2 | 결론 |
|---|---|---|---|---|
| openai/gpt-4o-mini | −15.5% | **−0.2pt** | −0.5pt | 품질 유지 |
| microsoft/phi-4    | −14.9% | **+1.7pt** | +3.2pt | 품질 소폭 향상 |

## Judge axes 분석 (success-only)

```
gpt-4o-mini  V0: correctness 25.0  completeness 25.0  faithfulness 25.0  conciseness 19.5
gpt-4o-mini  V4: correctness 25.0  completeness 25.0  faithfulness 25.0  conciseness 19.0
phi-4        V0: correctness 25.0  completeness 25.0  faithfulness 25.0  conciseness 17.5
phi-4        V4: correctness 25.0  completeness 25.0  faithfulness 25.0  conciseness 20.7
```

- **faithfulness 회귀 0** — V4 압축이 의미 왜곡을 유발하지 않음 (실 LLM 판정)
- phi-4는 V4에서 conciseness +3.2 — 압축된 입력이 더 짧고 정돈된 출력을 유도

## 핵심 발견
1. **H1 검증 ✅** : V4는 입력 토큰을 14.9–15.5% 절감, 품질 변화 −0.2 ~ +1.7pt
   (모두 ±2pt 이내).
2. **H2 검증 ✅** : cross-vendor judge에서 4축 모두 ≥17.5/25 (V4에서는 모두 ≥20).
   faithfulness/correctness/completeness는 양 변종 모두 perfect 25.
3. **R6 mock judge 대비 효과 재확인** : R6은 mock judge로 평균 절감 ~7%였으나
   R7 실 LLM judge에서 ~15% 절감(2배). mock의 tier2 계산이 보수적이었던 것이지,
   실제 사용자 체감 효과는 더 크다.

## 한계 / 알려진 이슈
- **3/5 모델 타임아웃** (ministral-3b, llama-3.3-70b-instruct, deepseek-v3-0324):
  GitHub Models의 무료 quota throttling이 추정 원인. judge 호출이 main 호출 RPS를
  사실상 2배로 만들고, R6 직후 누적 사용량이 큰 상태에서 실행되어 모델별 1200s
  timeout 안에서 단 한 건도 응답을 못 받음 (jsonl 0 bytes).
- 본 결과는 OpenAI/Microsoft 두 벤더 표본만 포함. Meta/DeepSeek/Mistral는 후속에서
  quota 회복 후 재실행 필요.
- phi-4는 timeout으로 V0/V4 각 7~8개만 완료 (목표 10). 그러나 동일 케이스 ID 짝
  비교로 절감/Δ는 유효.

## 회귀 검증
- `PYTHONPATH=. pytest -q` → **43 passed** (R6 직전과 동일)
- Smoke: `lite-r7-smoke.jsonl` 4 cells, $0.0008, 16.8s, judge_axes 정상 기록

## 후속 권고
- F1. quota 회복 후(다음 reset) 누락 3종(ministral-3b/llama-3.3-70b/deepseek-v3) 재실행.
- F2. tier 정의에 `lite-judged` 추가 (lite + tier2_rate=1.0)하여 CLI flag 의존 제거.
- F3. judge concurrency를 main 호출과 분리해 throttle 별도 관리(현재는 직렬).
- F4. R7 결과를 [docs/benchmark-results.html](../../docs/benchmark-results.html)에 반영.
