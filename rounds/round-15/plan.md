# Round 15 Plan — F18 (CONTRIBUTING 워크플로 문서화)

## 배경
R10~R14에서 `bench_real/render_results_panel.py`에 누적된 marker 기반 docs 자동화
워크플로(F7~F17)가 사용 절차 문서 없이 코드와 테스트에만 존재한다. 신규 라운드
추가 시 절차를 잊거나 잘못된 옵션 조합을 쓸 위험을 차단한다.

- **F5/F12/F15**: 트리거 조건(quota, 신규 패널/렌더러) 미충족으로 보류 유지.
- **F18**: `CONTRIBUTING.md`에 1쪽 분량의 "Updating the live-benchmark panel" 섹션 추가.

## 변경 사항
**파일**: `CONTRIBUTING.md` 1개 (코드/테스트 변경 없음)

3단계 워크플로를 코드 블록으로 명시:
1. `--list-panels`로 marker 발견
2. `--patch-doc --dry-run`로 영향 미리보기 (docs 무변경)
3. `--patch-doc --backup`로 실제 적용 + 1세대 백업

부가 노트:
- `--dry-run`/`--diff-out` 직교 사용
- 잘못된 `--panel` id는 SystemExit
- F9 `judge_axes.fallback` → `fb=k` 자동 노출
- 회귀 보호는 `tests/test_render_results_panel.py`

## 합의 산출물
- `rounds/round-15/{plan.md, votes.json, artifact.md, evaluation.md}`
- 문서: `CONTRIBUTING.md`

## 가설
H1. 추가된 명령이 그대로 실행 가능 (smoke로 3단계 모두 검증).
H2. `--dry-run` 명령 실행 후 docs MD5 불변(`be85f7aa…`).
H3. pytest 55 PASS 유지 (코드/테스트 미변경).
H4. CONTRIBUTING.md 분량이 합리적(≤100줄).
