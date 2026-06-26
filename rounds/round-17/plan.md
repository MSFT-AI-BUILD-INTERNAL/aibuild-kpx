# Round 17 Plan — F20 (CHANGELOG [Unreleased] 정리)

## 배경
R5~R16 누적 변경 사항이 `CHANGELOG.md`의 `[Unreleased]`에 반영되지 않은 상태.
릴리스 준비/리뷰 대상이 한눈에 보이지 않는다.

- **F5/F12/F15**: 보류 유지.
- **F20**: `[Unreleased] > Added`에 두 항목 추가 — R5~R9(크로스벤더 라이브 API),
  R10~R16(marker 기반 docs 자동화).

## 변경 사항
**파일**: `CHANGELOG.md` 1개 (코드/테스트 변경 없음)

신규 항목 2개를 `### Added` 마지막에 append:

1. **Cross-vendor live API benchmark (R5–R9)** — `lite-judged` tier, backoff cap
   (`MAX_TOTAL_WAIT_S=60`), judge-fallback to rule-based with provenance.
   5 벤더(OpenAI/Microsoft/Mistral/Meta/DeepSeek) V4 결과 −11%~−17% tok-in,
   Δq ±1.7 이내.
2. **Marker-bracketed docs panel automation (R10–R16)** —
   `bench_real.render_results_panel` 모듈, CLI 옵션 6개, F9 fb 태그,
   CONTRIBUTING/bench_real README 워크플로 문서, 12 unit tests.

## 합의 산출물
- `rounds/round-17/{plan.md, votes.json, artifact.md, evaluation.md}`
- 문서: `CHANGELOG.md`

## 가설
H1. Keep a Changelog 형식(`### Added/Changed/Fixed`) 준수.
H2. 라운드 범위 표기(`R5–R9`, `R10–R16`)로 rounds/ 디렉터리와 추적 가능.
H3. 코드/테스트 변경 0, pytest 55 PASS 유지.
H4. 항목 길이가 다른 Added 항목과 균형(~5~10줄/항목).
