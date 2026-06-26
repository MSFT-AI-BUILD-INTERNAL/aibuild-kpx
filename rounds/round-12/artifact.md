# Round 12 Artifact — F10 + F11

## 실행 메타
- 일시: 2026-05-25
- 비용: **$0.00** (코드 변경 + smoke만)
- 변경 파일: 1개 (`bench_real/render_results_panel.py`)

## F10 — `--backup` 옵션

```python
def _patch_doc(doc_path, fragment, panel="07b", backup=False):
    ...
    if backup:
        bak = doc_path.with_suffix(doc_path.suffix + ".bak")
        bak.write_text(text, encoding="utf-8")   # 원본 보존
        print(f"[patch] backup → {bak}")
    tmp = doc_path.with_suffix(doc_path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    os.replace(tmp, doc_path)                    # atomic
```

- `.bak`은 atomic replace **이전**에 작성 → docs 무손상 보장
- 같은 경로에 덮어쓰기(1세대 유지)로 디스크 누적 없음

### 검증 (H1)
```
$ md5 docs/benchmark-results.html               # patch 직전
MD5 = be85f7aa56994e4462c66f0d14b99c5d
$ ... --patch-doc ... --backup
[patch] backup → docs/benchmark-results.html.bak
[patch] docs/benchmark-results.html panel=07b (1268 bytes injected)
$ md5 docs/benchmark-results.html docs/benchmark-results.html.bak
docs/benchmark-results.html      = be85f7aa56994e4462c66f0d14b99c5d
docs/benchmark-results.html.bak  = be85f7aa56994e4462c66f0d14b99c5d   # 동일
```
input == output(멱등) 이므로 두 MD5가 같음. backup 무결성 ✅

## F11 — Marker id parameterization

```python
def _markers(panel: str) -> tuple[str, str]:
    return (f"<!-- panel:{panel}:start", f"<!-- panel:{panel}:end -->")
```

CLI:
- `--panel 07b` (기본): R11 동작과 100% 호환
- `--panel <id>`: 임의 패널 갱신

### 안전 실패 검증 (H2)
```
$ ... --panel nonexistent
[render] 1 rows → /tmp/_p.html
start marker '<!-- panel:nonexistent:start' not found in docs/benchmark-results.html
$ md5 docs/benchmark-results.html
be85f7aa56994e4462c66f0d14b99c5d   # 불변
```
- SystemExit 즉시 종료 → docs 미수정 ✅

### 호환성 검증 (H3)
`--panel` 미지정 시 R11과 동일한 MD5 `be85f7aa56994e4462c66f0d14b99c5d` ✅

## 회귀 검증
- `PYTHONPATH=. pytest -q` → **43 passed** (H4) ✅
- HTML 균형: `unmatched=0, unclosed=0` ✅

## 후속 권고
- **F5**: 표본 보강 (별도 quota 사이클).
- **F12**: 첫 비 07b 패널 적용 — `bench_real/runs/views/p2_exec_summary.md` 등에 marker
  도입하고 F11로 갱신 자동화.
- **F13**: `--dry-run` 옵션 — patch diff만 출력하고 파일 미수정.
