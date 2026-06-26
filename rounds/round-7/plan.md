# Round 7 Plan — Cross-Vendor LLM Judge Re-evaluation

## 배경 (R6 평가의 미해결 항목)
R6에서 GitHub Models로 30개 모델 라이브 실행을 완료했으나, `--judge-adapter mock`만 사용
했기 때문에 `tier1_score=100`은 **kpx 마커 보존 검사**(round-trip)만 반영하고
`tier2_score`는 mock 점수(고정 0.9 추정)였다. 즉 **실제 LLM 품질 영향**은 검증되지 않았다.
R7은 V0 vs V4 압축이 **실제 LLM 채점자**의 4축 평가(correctness/completeness/
faithfulness/conciseness)에서도 동등한 품질을 유지하는지 검증한다.

## 범위
- **대상 모델 5종(GitHub Models, 무료 quota)** — 벤더/규모 다양성:
  - openai/gpt-4o-mini (소형 OpenAI)
  - microsoft/phi-4 (Microsoft)
  - mistral-ai/ministral-3b (소형 Mistral)
  - meta/llama-3.3-70b-instruct (대형 Meta)
  - deepseek/deepseek-v3-0324 (R6 최고 성능 +14.14%)
- **변종**: V0 (raw) vs V4 (M03+M04+M19+M24+M25)
- **케이스**: lite 풀 37개 중 처음 10개 (`--max-cases 10`)
- **반복**: 1회
- **Tier 2 비율**: `--tier2-rate 1.0` (모든 셀에 judge 적용)
- **Judge**: `meta/llama-4-scout-17b-16e-instruct` (cross-vendor: OpenAI 셀에는
  Meta judge, Meta 셀에는 Meta judge — 동일 judge 고정으로 vendor bias 제거 후
  V0/V4 상대 비교)
- **예산 cap**: `--cap-usd 1e9` (실비용 $0)
- **셀 수**: 5 × 2 × 10 × 1 = 100 메인 호출 + 100 judge 호출 = 200 API 호출

## 변경 사항 (runner)
- `bench_real/runner.py`에 CLI 옵션 2개 추가:
  - `--tier2-rate FLOAT` — tier에서 정한 기본값 override (lite=0.0 → 1.0)
  - `--variants V0,V4` — TIER_VARIANTS 부분집합 선택
- 새 드라이버 `bench_real/run_r7_xjudge.py` — 5 모델을 subprocess로 순차 실행
  (per-model timeout 1200s).

## 합의 산출물
- `rounds/round-7/{plan.md, votes.json, artifact.md, evaluation.md}`
- 데이터: `bench_real/runs/lite-r7-xjudge/*.jsonl` + `_aggregate.json`,
  `_summary.json`, `bench_real/runs/r7-xjudge.log`

## 가설
H1. **V4는 입력 토큰을 ≥10% 절감**하며 LLM judge 품질(quality_score)은 V0 대비
   −2.0pt 이내로 유지된다 (R5/R6에서 마커 보존은 검증되었으므로 의미 보존 검증).
H2. cross-vendor judge에서 axes 4축이 모두 ≥22/25를 유지한다 (faithfulness 회귀 없음).

## 위험
- GitHub Models 무료 quota throttling: judge 호출이 main 호출 RPS를 두 배로 만들어
  rate limit/timeout 가능성. 모델별 1200s timeout으로 격리.
- 일부 모델(deepseek-v3, 70B급)은 단일 호출 latency 자체가 길어 10케이스 미완료 위험.
