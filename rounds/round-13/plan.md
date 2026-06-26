# Round 13 Plan — F13 (--dry-run) + F14 (--list-panels)

## 배경
R12 후속 3건 중 docs patch UX/투명성 두 건을 처리.

- **F5**: 표본 보강 — quota 사이클 분리 유지.
- **F12**: 비 07b 패널 첫 marker 적용 — 현재 docs에 대응 자동 렌더러가 없어 단순
  marker 래핑만으로는 의미가 작음. 자동 렌더링 가능한 패널이 생기는 라운드에 함께 처리.
- **F13**: `--dry-run` — patch 적용 없이 unified diff 출력. CI/리뷰 흐름에 필수.
- **F14**: `--list-panels` — 임의 HTML 문서의 marker id를 열거. 신규 라운드 진입 전
  대상 패널을 확인하는 보조 명령.

## 변경 사항
**파일**: `bench_real/render_results_panel.py`

1. `_patch_doc(..., dry_run=False)`:
   - `dry_run=True` 시 `difflib.unified_diff(n=2)`로 변경 영역만 출력 후 종료
   - 변경 없을 때는 `[dry-run] ... : no change` 한 줄 출력
2. `_list_panels(doc_path)` 신규: 정규식 `<!--\s*panel:([A-Za-z0-9_\-]+):start` 매칭, 순서 유지 dedup.
3. CLI:
   - `--inputs`/`--out`를 옵션화 (`--list-panels` 단독 사용 가능하도록)
   - `--dry-run` 플래그 추가
   - `--list-panels PATH` 옵션 추가 (단독 종료 경로)

## 합의 산출물
- `rounds/round-13/{plan.md, votes.json, artifact.md, evaluation.md}`
- 코드: `bench_real/render_results_panel.py`

## 가설
H1. `--list-panels docs/benchmark-results.html` → `07b` 한 줄 출력.
H2. `--dry-run` (변경 없음) → `no change` 출력, docs MD5 불변.
H3. `--dry-run` (변경 있음) → unified diff에 `---/+++` 헤더 + `@@ -866,19` 위치 + 4개 모델 행 삭제 표시(`-`), docs MD5 불변.
H4. 기존 호출(`--patch-doc` 단독) → R12와 동일 MD5 `be85f7aa…` 유지.
H5. pytest 43 PASS.
