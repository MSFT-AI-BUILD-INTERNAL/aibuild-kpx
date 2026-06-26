# Round 12 Plan — F10 (--backup) + F11 (marker id parameterization)

## 배경
R11 후속 3건 중 docs patch 안전성/일반화에 해당하는 두 건을 처리.

- **F5**: 표본 보강 — quota 사이클 분리 유지.
- **F10**: `--backup` 옵션으로 marker 손상/오작동 대비 `<doc>.bak` 생성.
- **F11**: marker id를 panel별 파라미터로 일반화 → 한 모듈로 다중 패널 갱신 가능.

## 변경 사항
**파일**: `bench_real/render_results_panel.py`

1. `_markers(panel) -> (start_prefix, end_full)` 신규: marker 문자열을 panel id로 파생.
2. `_patch_doc(doc_path, fragment, panel="07b", backup=False)`:
   - `panel` 인자로 marker 선택
   - `backup=True` 시 `<doc>.bak`에 원본 텍스트 저장 (atomic write 전)
   - 잘못된 panel id → SystemExit (조용한 손상 방지)
3. CLI: `--panel` (기본 `07b`), `--backup` 플래그 추가.

## 합의 산출물
- `rounds/round-12/{plan.md, votes.json, artifact.md, evaluation.md}`
- 코드: `bench_real/render_results_panel.py`

## 가설
H1. `--backup` 사용 시 `<doc>.bak` MD5 = patch 직전 docs MD5와 일치.
H2. `--panel nonexistent` → SystemExit, docs 파일 불변(MD5 동일).
H3. 기본 동작(`--panel` 미지정) → R11과 동일한 결과(MD5 `be85f7aa…`).
H4. pytest 43건 회귀 0, HTML 균형 0/0.
