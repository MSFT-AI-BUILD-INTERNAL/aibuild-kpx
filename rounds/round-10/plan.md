# Round 10 Plan — F6 (judge fallback) + F7 (panel auto-render)

## 배경
R9 후속 3건 중 2건을 처리한다.

- **F5** (max_cases 10→37): 1회 실행에 quota 폭증 위험이 커서 차기 라운드로 이월
  (R7/R8/R9에서 이미 5/5 벤더 검증을 마쳤으므로 표본 보강의 한계 효용이 작음).
- **F6**: judge 호출이 transient error/parse 실패로 떨어졌을 때, tier2를 0으로 두는
  대신 rule-based 점수로 fallback. provenance를 `judge_axes`에 명시.
- **F7**: `_aggregate.json` + JSONL에서 docs `07b` 섹션의 V4 절감 막대차트를 자동
  렌더링. 새 라운드 추가 시 manual 수정 없이 갱신 가능.

## 변경 사항
1. **F6 — runner.py**
   ```python
   if axes is not None and "error" in axes:
       fb_score, _ = score_rule_based(res.text, case.expected)
       axes = {"fallback":"rule_based","judge_error":axes["error"],
               "rule_based_score": fb_score}
       tier2 = fb_score
   ```
   - 적용 조건: judge가 (네트워크 오류, JSON parse 실패, axes 누락) 중 하나일 때.
   - 영향: `quality = 0.5*tier1 + 0.5*tier2`가 `0.5*tier1 + 0.5*tier1`이 되어 tier1로
     수렴(과도한 penalty 방지). `judge_axes` 보존으로 사후 필터링 가능.

2. **F7 — bench_real/render_results_panel.py (신규)**
   - 입력: 라운드 ID와 `lite-*` 디렉터리 쌍 (예: `r7=bench_real/runs/lite-r7-xjudge`)
   - 출력: HTML fragment (`<!-- panel:07b:start -->` ~ `<!-- panel:07b:end -->`)
   - 동작: per-model JSONL → V0 vs V4 평균 tok_in/quality → 절감%·Δq로 정렬 → bar-row 생성
   - docs에 마커 삽입 후 manual copy-paste로 갱신 (write-doc은 별도)

3. **docs/benchmark-results.html**
   - 기존 07b의 V4 절감 panel을 marker 사이로 옮기고 render 출력으로 교체

## 합의 산출물
- `rounds/round-10/{plan.md, votes.json, artifact.md, evaluation.md}`
- 코드: `bench_real/runner.py`(F6), `bench_real/render_results_panel.py`(F7 신규)
- 문서: `docs/benchmark-results.html`(panel marker)
- 생성물: `bench_real/runs/_panel_07b.html`

## 가설
H1. F6은 정상 judge 흐름(`error` not in axes)에는 영향 없음 → pytest 회귀 0.
H2. F6 fallback이 발동되어도 `quality_score`는 tier1과 일치(50/50 가중치 + tier1=tier2).
H3. F7 render 출력의 절감/Δq 수치가 직접 집계와 ±0.1pt 이내 일치.
H4. docs HTML 태그 균형 유지.
