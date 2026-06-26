# Round 18 — Artifact (F21)

## Change
`CHANGELOG.md` 상단에서 `[Unreleased]` 섹션이 누적한 R5–R16 항목을 정식 릴리스로 굳혔습니다.

### Diff (요지)
```diff
 ## [Unreleased]

+## [0.3.0] - 2026-05-25
+
 ### Added
 - **Benchmark traceability metadata** — `bench_real.runner` now accepts ...
 - **Executive summary risk reporting** — ...
 - **Benchmark improvement rounds** — rounds/round-1..4 ...
 - **Cross-vendor live API benchmark (R5–R9)** — lite-judged tier, MAX_TOTAL_WAIT_S=60, judge-fallback ...
 - **Marker-bracketed docs panel automation (R10–R16)** — render_results_panel + 6 CLI opts + fb=k + 12 tests ...

 ### Changed
 - **Benchmark docs** — ...
```

## Verification
- `head -12 CHANGELOG.md` 확인: 빈 `[Unreleased]` + `[0.3.0] - 2026-05-25` 헤더 노출, 이전 항목 무손실.
- `PYTHONPATH=. pytest -q` → **55 passed** (regression 없음).
- `docs/benchmark-results.html` §07b 마커·MD5 영향 없음 (CHANGELOG 단독 편집).

## Deferred
- **F5**: `GITHUB_TOKEN` 환경변수 미설정. 사용자가 토큰을 export 한 뒤 별도 라운드에서 진행.
  - 예정 명령: `PYTHONPATH=. python -m bench_real.runner --tier lite-judged --adapter github --model openai/gpt-4o-mini --judge-adapter github --judge-model openai/gpt-4o-mini --run-id r19-sample-expand`
