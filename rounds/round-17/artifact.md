# Round 17 Artifact — F20

## 실행 메타
- 일시: 2026-05-25
- 비용: **$0.00**
- 변경 파일: 1 (`CHANGELOG.md`)
- 코드/테스트 변경: **없음**

## CHANGELOG.md `[Unreleased] > Added` append

```markdown
- **Cross-vendor live API benchmark (R5–R9)** — bench_real now ships
  lite-judged tier (always-on LLM judge), backoff cap (MAX_TOTAL_WAIT_S=60)
  in adapters/github_models.py, and judge-fallback to rule-based scoring on
  judge error (provenance preserved in judge_axes.fallback). Validated 5
  vendors (OpenAI, Microsoft, Mistral, Meta, DeepSeek) at V4 with
  −11% to −17% tok-in savings and Δq within ±1.7.

- **Marker-bracketed docs panel automation (R10–R16)** — new
  bench_real.render_results_panel module renders the live-API panel in
  docs/benchmark-results.html §07b from per-model JSONLs. Supports
  --list-panels, --patch-doc, --panel, --backup, --dry-run, --diff-out;
  idempotent atomic write; F9 fb=k tag surfaces judge_axes.fallback ratio.
  Workflow documented in CONTRIBUTING.md and bench_real/README.md;
  regression-guarded by 12 unit tests in tests/test_render_results_panel.py.
```

## 추적성 매핑 (H2)

| 라운드 범위 | 라운드 산출물 | CHANGELOG 항목 |
|---|---|---|
| R5–R9 | rounds/round-{5..9}/ | Cross-vendor live API benchmark |
| R10 | rounds/round-10/ (F6/F7) | Marker docs automation |
| R11 | rounds/round-11/ (F8/F9) | ↳ +`--patch-doc` + `fb=k` |
| R12 | rounds/round-12/ (F10/F11) | ↳ +`--backup` + `--panel` |
| R13 | rounds/round-13/ (F13/F14) | ↳ +`--dry-run` + `--list-panels` |
| R14 | rounds/round-14/ (F16/F17) | ↳ +`--diff-out` + 12 tests |
| R15 | rounds/round-15/ (F18) | ↳ CONTRIBUTING workflow |
| R16 | rounds/round-16/ (F19) | ↳ bench_real/README inbound link |

## 검증

### H1/H4 — 형식 및 분량
- 두 항목 모두 `### Added` 아래, `- **Title** — body` 패턴 (기존 항목과 동일).
- 각 항목 ~7줄, 기존 "Benchmark traceability metadata"(4줄)~"Executive summary"(3줄)와 동급.

### H3 — 회귀
```
$ PYTHONPATH=. pytest -q
....................................................... [100%]
55 passed
```

## 후속 권고
- **F5**: 표본 보강 (별도 quota 사이클)
- **F12**: 자동 렌더러와 함께 신규 패널 marker
- **F15**: 다중 패널 일괄 patch
- **F21**: 릴리스 시점에 `[Unreleased]` → `[0.3.0]` 헤더 전환
