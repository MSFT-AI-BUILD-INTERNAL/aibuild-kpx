# Round 16 Artifact — F19

## 실행 메타
- 일시: 2026-05-25
- 비용: **$0.00**
- 변경 파일: 1 (`bench_real/README.md`)
- 코드/테스트 변경: **없음**

## bench_real/README.md 신규 섹션 (Legacy 직전)

```markdown
## Updating docs/benchmark-results.html §07b (live API panel)

Per-model JSONLs under bench_real/runs/lite-r*-*/ feed the marker-bracketed
panel in section 07b of docs/benchmark-results.html. The workflow
(--list-panels → --dry-run preview → --backup apply, plus notes on
--diff-out, panel-id safety, F9 fb=k tag, and determinism) is documented
in ../CONTRIBUTING.md ▶ Updating the live-benchmark panel.
Regression-guarded by ../tests/test_render_results_panel.py.
```

## Anchor 정합성 (H1)

CONTRIBUTING 헤딩:
```
## Updating the live-benchmark panel (`docs/benchmark-results.html` §07b)
```

GitHub 슬러그 규칙 적용:
- 소문자화
- 백틱/괄호/§ 제거
- `.`, `/` 제거
- 공백 → `-`

→ `updating-the-live-benchmark-panel-docsbenchmark-resultshtml-07b`

README anchor:
```
#updating-the-live-benchmark-panel-docsbenchmark-resultshtml-07b
```
**정확히 일치** ✅

## Smoke

```
$ grep -n "Updating the live-benchmark panel" CONTRIBUTING.md
41:## Updating the live-benchmark panel (`docs/benchmark-results.html` §07b)

$ grep -n "live-benchmark panel" bench_real/README.md
147:in [`../CONTRIBUTING.md` ▶ Updating the live-benchmark panel](...).

$ wc -l bench_real/README.md
162 bench_real/README.md   # 154 → 162 (H3)
```

## 회귀 (H2)
```
$ PYTHONPATH=. pytest -q
....................................................... [100%]
55 passed
```

## 후속 권고
- **F5**: 표본 보강 (별도 quota 사이클)
- **F12**: 자동 렌더러와 함께 신규 패널 marker
- **F15**: 다중 패널 일괄 patch
- **F20**: CHANGELOG `## [Unreleased]`에 F6~F19 항목 한 줄씩 정리
