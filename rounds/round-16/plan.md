# Round 16 Plan — F19 (bench_real/README inbound link)

## 배경
R15에서 CONTRIBUTING.md에 추가한 marker 워크플로 섹션이 인근 문서에서 검색되지 않는다.
`bench_real/README.md`가 본 모듈의 1차 진입점이므로 inbound 링크를 추가해
발견 가능성을 확보한다.

- **F5/F12/F15**: 보류 유지 (트리거 조건 미충족).
- **F19**: `bench_real/README.md`에 `Updating docs/benchmark-results.html §07b` 섹션
  (3줄)을 추가, CONTRIBUTING 섹션과 테스트 파일로 링크.

## 변경 사항
**파일**: `bench_real/README.md` (`## Legacy v0.2.0 self-QA suite` 직전 신규 섹션 8줄)

```markdown
## Updating docs/benchmark-results.html §07b (live API panel)

... documented in [`../CONTRIBUTING.md` ▶ Updating the live-benchmark panel](../CONTRIBUTING.md#updating-the-live-benchmark-panel-docsbenchmark-resultshtml-07b).
Regression-guarded by [`../tests/test_render_results_panel.py`](../tests/test_render_results_panel.py).
```

GitHub 슬러그 규칙(소문자, 백틱·괄호·점·슬래시·§ 제거, 공백→하이픈) 기준으로
anchor가 CONTRIBUTING 헤딩과 정확히 일치하도록 작성.

## 합의 산출물
- `rounds/round-16/{plan.md, votes.json, artifact.md, evaluation.md}`
- 문서: `bench_real/README.md`

## 가설
H1. CONTRIBUTING 헤딩의 GitHub 슬러그 = `updating-the-live-benchmark-panel-docsbenchmark-resultshtml-07b`, README anchor와 일치.
H2. pytest 55 PASS 유지 (코드/테스트 미변경).
H3. bench_real/README.md 분량 합리적(≤200줄).
