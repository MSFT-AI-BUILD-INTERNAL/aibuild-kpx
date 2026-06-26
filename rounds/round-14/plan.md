# Round 14 Plan — F16 (--diff-out) + F17 (unit tests for render_results_panel)

## 배경
R10~R13에서 `bench_real/render_results_panel.py`에 누적된 기능(F7~F14)이 단위
테스트 없이 smoke만으로 검증돼 왔다. 회귀 위험을 차단하기 위해 전용 unit tests를
도입한다. 인접 작업으로 F16(`--diff-out`)도 함께 처리.

- **F5/F12**: 정책 유지(quota·렌더러 부재로 별도 라운드).
- **F15**: 다중 패널 일괄 patch — 실제 두 번째 패널 등장 라운드와 함께 처리.
- **F16**: `--diff-out PATH` — dry-run 결과(또는 실제 patch 시 사전 diff)를 파일로 저장.
- **F17**: `tests/test_render_results_panel.py` 신규 — F7/F9/F10/F11/F13/F14/F16 행위 고정.

## 변경 사항
1. `bench_real/render_results_panel.py`
   - `_patch_doc(..., diff_out: Path | None = None)`: dry-run 또는 실제 patch 양쪽에서
     diff 텍스트를 생성·기록. dry-run과 무관하게 단독 사용 가능.
   - CLI: `--diff-out PATH` 추가.

2. `tests/test_render_results_panel.py` 신규 (12개 케이스)
   - `_markers`: 기본/특수문자 panel id
   - `_list_panels`: 순서 유지 dedup, 빈 문서
   - `_patch_doc`: replace, idempotent, backup, dry-run write 차단, no-change 메시지,
     wrong-panel SystemExit(+docs 무손상), diff-out 파일
   - `_load_per_variant`: 평균·n·fb 카운트, error row 스킵

## 합의 산출물
- `rounds/round-14/{plan.md, votes.json, artifact.md, evaluation.md}`
- 코드: `bench_real/render_results_panel.py`, `tests/test_render_results_panel.py` (신규)

## 가설
H1. 신규 테스트 12개 모두 PASS, 기존 43건 회귀 0 → 총 55 PASS.
H2. `--diff-out` 단독 호출 시 diff 파일 생성, docs는 patch 모드 시 실제로 갱신됨.
H3. `--dry-run --diff-out` 동시 사용 시 docs 불변 + diff 파일 동일 내용.
H4. 테스트는 marker를 포함한 fragment를 사용해 실제 `_render` 출력 형식과 일치.
