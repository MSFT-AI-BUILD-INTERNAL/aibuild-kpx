# Round 11 Artifact — F8 + F9

## 실행 메타
- 일시: 2026-05-25
- 비용: **$0.00** (라이브 API 미사용; 기존 R7/R8/R9 JSONL 재집계 + docs patch)
- 변경 파일: 코드 1개, 문서 1개 (자동 재생성)

## F8 — Docs auto-patch (`--patch-doc`)

**파일**: [bench_real/render_results_panel.py](../../bench_real/render_results_panel.py)

```python
def _patch_doc(doc_path: Path, fragment: str) -> None:
    text = doc_path.read_text(encoding="utf-8")
    s = text.find(START_MARK)
    if s < 0: raise SystemExit(...)
    e = text.find(END_MARK, s)
    if e < 0: raise SystemExit(...)
    new_text = text[:s] + fragment.rstrip("\n") + text[e + len(END_MARK):]
    tmp = doc_path.with_suffix(doc_path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    os.replace(tmp, doc_path)
```

설계 포인트:
- marker 미존재 시 `SystemExit`으로 즉시 실패 (조용한 손상 방지)
- `*.tmp` + `os.replace` 로 atomic write
- fragment의 trailing `\n`을 제거해 marker 이후 구조 무영향

CLI:
```
python -m bench_real.render_results_panel \
  --inputs r7=... r8=... r9=... \
  --out bench_real/runs/_panel_07b.html \
  --patch-doc docs/benchmark-results.html
```

### 멱등성 검증 (H1)
```
[render] 5 rows → bench_real/runs/_panel_07b.html
[patch] docs/benchmark-results.html updated (1268 bytes injected)
MD5 (1회) = be85f7aa56994e4462c66f0d14b99c5d
MD5 (2회) = be85f7aa56994e4462c66f0d14b99c5d
```
동일 입력 → 동일 출력 ✅

### HTML 균형 (H2)
`unmatched=0, unclosed=0` ✅

## F9 — Judge-fallback transparency

**파일**: 동일 파일

```python
# _load_per_variant 내
fb = sum(1 for r in ok
         if (r.get("judge_axes") or {}).get("fallback") == "rule_based")
per_v[v] = {"q": q, "tok_in": ti, "n": n, "fb": fb}

# _render 내
"fb": int(per_v["V0"].get("fb", 0)) + int(per_v["V4"].get("fb", 0))
fb_tag = f", fb={r['fb']}" if r["fb"] else ""
```

### 현재 데이터 (H3)
R7/R8/R9 모두 judge가 정상 응답 → `fb=0`, 태그 미출력. 패널 시각이 깨끗.
F6이 발동된 차기 라운드부터 `(n=10/10, fb=2, r12)` 형태로 자동 표시.

## 회귀 검증
- `PYTHONPATH=. pytest -q` → **43 passed** (H4) ✅
- patch 후 docs/benchmark-results.html 균형 OK
- 멱등성 MD5 일치

## 후속 권고
- **F5** (재유지): 단일 모델 37 케이스 표본 보강. quota 사이클에 별도 처리.
- **F10**: `_patch_doc` 실패 시(marker 손상) backup 생성 옵션 (`--backup`).
- **F11**: 다른 패널(p1~p6 view)에도 marker 도입해 동일 패턴 일반화.
