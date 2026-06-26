# Round 9 Plan — Hardening + DeepSeek 재시도 + 문서 갱신 (F1-1/F2/F3/F4)

## 배경
R8에서 4개 후속 항목이 이월되었음:
- **F1-1**: DeepSeek-v3 quota 회복 후 재시도
- **F2**: `bench_real/adapters/github_models.py` 429 backoff 누적 시간 cap
- **F3**: `lite-judged` tier 추가 (CLI flag 의존 제거)
- **F4**: `docs/benchmark-results.html`에 R6/R7/R8 통합 결과 반영

R9에서 모두 처리한다.

## 사전 진단
2026-05-22 시점 probe 결과:
- `deepseek/deepseek-v3-0324` → HTTP 200 (회복)
- `meta/llama-4-scout-17b-16e-instruct` → HTTP 200 (회복)
∴ R7 원본 judge로 DeepSeek 직접 비교 가능.

## 변경 사항
1. **F2** — `bench_real/adapters/github_models.py`
   - 누적 backoff cap `MAX_TOTAL_WAIT_S = 60.0`s 도입
   - 단일 wait cap 60s → 30s 축소
   - retry 4회 + 누적 60s 초과 시 즉시 HTTP 에러 반환
2. **F3** — `bench_real/runner.py` + `bench_real/tasks/__init__.py`
   - `TIER_VARIANTS`/`TIER_REPEATS`/`TIER_TIER2_RATE`/`TIER_BUDGET`에 `lite-judged` 추가
     (lite와 동일 case/variant, `tier2_rate=1.0`)
   - `--tier` choices에 `lite-judged` 추가
3. **F1-1** — `bench_real/runs/lite-r9-deepseek/deepseek__deepseek-v3-0324.jsonl`
   - tier=`lite-judged`, V0/V4 × 10케이스, judge=`meta/llama-4-scout-17b-16e-instruct`
   - R7 judge와 동일 → R7 표에 직접 추가 가능
4. **F4** — `docs/benchmark-results.html`
   - 새 섹션 `07b 라이브 API 벤치마크 (R6–R9, 2026-05)` 추가
   - R6 30모델 요약 + R7+R8+R9 통합 V4 절감 막대차트 + 운영 경험치

## 합의 산출물
- `rounds/round-9/{plan.md, votes.json, artifact.md, evaluation.md}`
- 코드 변경 3건, 데이터 1건, 문서 1건

## 가설
H1. F2 cap이 정상 모델 동작에 부작용 없음 (smoke로 검증).
H2. F3 lite-judged tier가 기존 lite와 동등한 case set + 100% judge로 실행.
H3. DeepSeek-v3 V4가 R7 패턴(tok_in 약 −15%, Δq ≤2pt)을 재현.
H4. 문서 갱신 후 HTML 태그 균형 유지(parser 검증).
