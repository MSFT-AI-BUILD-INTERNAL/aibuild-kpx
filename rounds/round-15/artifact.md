# Round 15 Artifact — F18

## 실행 메타
- 일시: 2026-05-25
- 비용: **$0.00** (문서 변경 + smoke만)
- 변경 파일: 1 (`CONTRIBUTING.md`)
- 코드/테스트 변경: **없음**

## CONTRIBUTING.md 신규 섹션

[CONTRIBUTING.md](../../CONTRIBUTING.md) 끝에 추가:

```markdown
## Updating the live-benchmark panel (docs/benchmark-results.html §07b)

Section 07b is auto-generated from per-model JSONLs ... bracketed by HTML markers
(<!-- panel:07b:start ... --> / <!-- panel:07b:end -->).

# 1) discover existing markers
PYTHONPATH=. python -m bench_real.render_results_panel \
  --list-panels docs/benchmark-results.html

# 2) preview the change (no file is written; docs unchanged)
... --patch-doc docs/benchmark-results.html --dry-run

# 3) apply the change, keeping a one-generation backup
... --patch-doc docs/benchmark-results.html --backup
```

핵심 노트:
- `--dry-run` + `--diff-out PATH` 직교 사용 → 리뷰용 diff 파일 + docs 무변경
- 잘못된 `--panel <id>` → SystemExit (docs 무손상)
- `judge_axes.fallback == "rule_based"` (F6 발동) → 패널에 `fb=k` 자동 노출
- 신규 라운드 추가: `lite-r<N>-<tag>/*.jsonl` 디렉터리 드롭 후 `--inputs`에 `r<N>=path`
  append → 3단계 재실행. 동일 입력 → 동일 MD5(결정성).
- 회귀 보호: [tests/test_render_results_panel.py](../../tests/test_render_results_panel.py)

## Smoke 검증

### H1 — 문서의 명령들이 실제 동작
```
$ ... --list-panels docs/benchmark-results.html
07b

$ ... --patch-doc docs/benchmark-results.html --dry-run
   r8  meta/llama-3.3-70b-instruct  save=+10.96%  Δq=-1.00  n=5/5
[dry-run] docs/benchmark-results.html panel=07b: no change
```

### H2 — docs 무변경
```
$ md5 docs/benchmark-results.html   # dry-run 전
be85f7aa56994e4462c66f0d14b99c5d
$ md5 docs/benchmark-results.html   # dry-run 후
be85f7aa56994e4462c66f0d14b99c5d   # 동일
```

### H3 — pytest 회귀
```
$ PYTHONPATH=. pytest -q
....................................................... [100%]
55 passed
```

### H4 — 분량
`wc -l CONTRIBUTING.md` → **79 줄** (이전 38줄 + 41줄 추가)

## 후속 권고
- **F5**: 표본 보강 (별도 quota 사이클)
- **F12**: 자동 렌더러와 함께 신규 패널 marker
- **F15**: 다중 패널 일괄 patch
- **F19**: README 최상단 또는 `bench_real/README.md`에서 본 워크플로 섹션을 inbound link로 안내
