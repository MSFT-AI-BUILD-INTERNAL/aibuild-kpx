# Round 11 Plan — F8 (docs auto-patch) + F9 (fallback ratio in panel)

## 배경
R10 후속 권고 3건 중 docs 자동화/투명성에 해당하는 두 건을 처리.

- **F5** (37 case 표본 보강): quota 부담으로 별도 사이클 이월 유지.
- **F8**: `render_results_panel`이 docs/benchmark-results.html의 marker bracket을
  직접 교체. 멱등성 보장 (동일 입력 → 동일 출력).
- **F9**: row JSONL의 `judge_axes.fallback == "rule_based"` 카운트를 집계해
  per-model 패널 항목에 `fb=k` 태그로 노출. F6의 효과를 사후 관측 가능.

## 변경 사항
1. **bench_real/render_results_panel.py**
   - `_load_per_variant`: variant 통계에 `fb` 필드 추가 (rule_based fallback rows 수)
   - `_render`: row dict에 `fb = fb_V0 + fb_V4`, HTML/console에 `fb=k` 태그 (k>0일 때만)
   - `_patch_doc(doc_path, fragment)` 신규: marker 사이를 atomic replace (`*.tmp` → os.replace)
   - CLI: `--patch-doc PATH` 옵션 추가

## 합의 산출물
- `rounds/round-11/{plan.md, votes.json, artifact.md, evaluation.md}`
- 코드: `bench_real/render_results_panel.py` (라인 ~38, ~75, ~110 신규/수정)
- 문서: `docs/benchmark-results.html` (auto-patch 결과)

## 가설
H1. `--patch-doc` 1회/2회 실행 결과 MD5 동일 (멱등).
H2. patch 후 HTML 균형 (unmatched=0, unclosed=0).
H3. 현재 R7/R8/R9 데이터에는 judge 실패 fallback이 없어 모든 row의 `fb=0`,
    따라서 패널 텍스트에 `fb=` 태그 미출력.
H4. pytest 43건 회귀 0.
