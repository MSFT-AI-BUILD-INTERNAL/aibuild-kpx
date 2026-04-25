# kpx — Karpathy-aligned Prompt-side Token Optimizer

> 본 문서는 [`/Users/hacbook/ms/workspace/kpx`](../../../kpx) 에 있는 standalone Python 패키지 **kpx 0.2.0** 의 전부를 한 문서로 설명한다.
> 대상 독자: 이 라이브러리를 처음 보는 사용자, 평가자, 코드 리뷰어, 향후 유지보수자.

---

## 0. 한 줄 요약
**Andrej Karpathy의 8개 LLM 관점(F1–F8)에 정렬된 30가지 토큰 최적화 방법(M01–M30)을 코드로 구현한 prompt-side 라이브러리.** [rtk-ai/rtk](https://github.com/rtk-ai/rtk) 가 _shell-output 측_ 절감을 다룬다면, kpx는 _prompt 측_ 절감을 다룬다.

- 6개 안전 변환 + 1개 inject + 1개 비교기 + 정적 audit + CLI + 30-prompt × 10-transform = 300-round 자체 벤치 포함.
- **0 errors / 0 safety violations / 99.3% idempotent / 평균 21.28% 토큰 절감** 으로 production-ready (R5 재행 기준).
- MIT, Python 3.9–3.12, 외부 의존성 0개(YAML 출력 시 PyYAML 선택적).

---

## 1. 탄생 배경 (R52 → R54+ 타임라인)

| 단계 | 시점 | 결과 |
|---|---|---|
| Theory | R15–R21 | Karpathy LLM wiki 정제 (eval 96/100) |
| Catalog | R22–R51 | 30개 토큰 최적화 방법 카탈로그 (`ref/Token_최적화_Karpathy_관점.md`) |
| Prototype | R52 | `harness-check/lib/kpx/` 0.1.0 (in-tree) |
| Standalone | R53 | `/Users/hacbook/ms/workspace/kpx/` git repo 분리 |
| QA Campaign | R54+ | 300-round 벤치 → 8개 결함 발굴 → 0.2.0 릴리즈 |

→ 0.1.0 프로토타입은 [`harness-check/lib/`](../lib/README.md)에서 제거됨, 정식 소스는 standalone repo 단일.

---

## 2. 디자인 원칙

1. **In-place safe transforms** — 입력의 의미를 보존하면서 토큰만 줄인다. (요약·재작성 같은 lossy 변환은 명시적으로 분리)
2. **Idempotent** — `f(f(x)) == f(x)`. 여러 변환을 체인으로 묶어도 안정.
3. **Structure-preserving** — 코드 블록(` ``` `, `` ` ``), 헤딩, 들여쓰기, 줄바꿈은 보존.
4. **Karpathy-aligned** — CoT("step by step")처럼 Karpathy가 명시 권장한 표현은 절대 제거하지 않음.
5. **Zero hidden behavior** — 모든 변환은 `kpx audit`로 정적 점검 가능.
6. **Boring tech** — 표준 라이브러리만으로 동작, regex 위주.

---

## 3. 디렉터리 구조

```
kpx/
├── kpx/                       # 패키지 본체
│   ├── __init__.py            # __version__ = "0.2.0", 공개 API
│   ├── tokens.py              # 휴리스틱 토큰 추정 (CJK 1ch=1tok, ASCII 4ch=1tok)
│   ├── methods.py             # 모든 변환 + SAFE_TRANSFORMS 레지스트리 (277 LOC)
│   ├── compress.py            # 변환 체인 적용기
│   ├── audit.py               # 30 방법 정적 점검 + 0–100 점수
│   └── cli.py                 # argparse 기반 5개 서브커맨드
├── bench_real/                # 통합 벤치마크 (legacy v0.2.0 + plan v2 + 심층 분석)
│   ├── legacy/                # v0.2.0 자체 QA 벤치마크 (300 round)
│   │   ├── corpus.py          # 30 prompt × 6 카테고리 × 5 스타일
│   │   ├── runner.py          # 300-round 측정기
│   │   └── results.json       # 최신 측정 raw (115KB)
│   ├── adapters/              # mock / openai / anthropic (urllib-only)
│   ├── scorers/               # rule-based + LLM-judge
│   ├── tasks/                 # T01/T03/T04/T06/T07 케이스
│   ├── views/                 # P1-P6 persona 리포트
│   ├── analysis/              # 소스코드 심층 분석 (LLM 무관 정적 분석)
│   │   ├── realistic_prompts.py     # 15개 실세계 코딩 프롬프트(C01-C15)
│   │   ├── code_preservation.py     # 7-차원 분석기 (token/fence/inline/signpost/AST/politeness/idempotency)
│   │   ├── run_code_analysis.py     # CLI 진입점
│   │   └── results/code_preservation.json  # 90 cell 산출물
│   └── runner.py              # plan v2 entry point
├── tests/                     # pytest
│   ├── test_kpx.py            # 14 기본 테스트 (R52)
│   └── test_regressions_v020.py  # 27 회귀 테스트 (R54+)
├── docs/METHODS.md            # 30 방법 정의 + 안전성 라벨
├── pyproject.toml             # PEP 621 메타 + console_scripts
├── CHANGELOG.md               # Keep-a-Changelog 형식
├── CONTRIBUTING.md
├── LICENSE                    # MIT
└── README.md
```

코드 합계: **1,341 LOC** (파이썬). 테스트가 본체의 ~21%.

---

## 4. 패키지 모듈별 상세

### 4.1 `kpx.tokens`
- `estimate_tokens(text) -> int` — CJK 글자 1, ASCII 단어 ≈ 4글자/토큰. tiktoken 미사용 → 휴리스틱이지만 의도적으로 [harness-check/harness/constraints.py](../../harness/constraints.py)와 동일 공식.
- `fits_window(text, window) -> bool` — 50% 룰 (`estimate_tokens ≤ window/2`).
- 외부 의존성 없음. 향후 옵션으로 `tiktoken`/`tokenizers` 백엔드 추가 가능.

### 4.2 `kpx.methods`
모든 변환 함수가 모이는 핵심 모듈. 패턴 정의 → 헬퍼 → 변환 → 레지스트리 순서.

#### 핵심 헬퍼
- `_CODE_FENCE_RE = re.compile(r"(```[\s\S]*?```|`[^`\n]+`)")` — 코드 블록·인라인 코드 매칭.
- `_apply_outside_code(text, fn)` — 텍스트를 코드/비코드 segment로 split, **짝수 인덱스(비코드)** 에만 `fn` 적용. **B10 fix의 토대.**
- `_collapse_blank_lines(text)` — 각 줄 `rstrip` + 3개 이상 공백줄을 2개로. **순수 정규화기** (trailing newline 처리는 `compress`가 담당).
- `_multi_sub(text, pairs)` — 다중 정규식을 한 패스로.

#### 변환 함수 (안전)

| ID | 함수 | 무엇을 하는가 | 주의 |
|---|---|---|---|
| **M03** | `strip_known_facts(text)` | "Python is a high-level interpreted language" 같은 사전학습으로 알려진 사실 줄 제거 | 코드 블록 내부는 보존 (B10 fix) |
| **M04** | `minimize_system_prompt(text) -> (out, removed)` | "you are a helpful assistant", "do your best" 등 stock 표현 제거 | CoT 표현은 보존 (B1 fix). 다중절 라인은 보존 (B3 fix) |
| **M19** | `lossy_summary(text, max_chars=2000)` | 헤딩·불릿 우선 추출. flat text는 sentence boundary 자르기 | 이미 truncated면 무동작 (멱등) |
| **M24** | `strip_polite(text)` | "Please", "Thank you", "I hope this helps" 등 politeness 제거 | "Please note/refer/see/check..." 기술 signpost는 보존 (B2 fix). 코드 보존 |
| **M25** | `strip_role_tags(text)` | `<\|system\|>`, `[INST]`, `### Instruction:` 같은 chat-template 잔여 태그 제거 | 잔여 다중공백 정리 (B11 fix). **코드 블록 내부 들여쓰기 보존 (B13 fix)** |

#### 인젝터 / 비교기

- **M09** `inject_no_filler(text)` — 시스템 프롬프트 끝에 `NO_FILLER_INSTRUCTION = "Respond with the answer only..."` 1줄 추가. **idempotent** (substring 검사).
- **M15** `format_compare(records)` — 동일 데이터를 JSON / JSON-min / YAML / Markdown table로 직렬화 후 char count 비교. `FormatBenchmark` dataclass 반환.

#### 레지스트리
```python
SAFE_TRANSFORMS = {
    "M03": strip_known_facts,
    "M04": lambda t: minimize_system_prompt(t)[0],
    "M19": lossy_summary,
    "M24": strip_polite,
    "M25": strip_role_tags,
}
```

### 4.3 `kpx.compress`
```python
def compress(text, methods=None):
    selected = list(methods) if methods else list(SAFE_TRANSFORMS.keys())
    out = text
    for mid in selected:
        fn = SAFE_TRANSFORMS.get(mid)
        if fn is None:
            raise ValueError(f"Unknown or non-safe method: {mid}")
        out = fn(out)
    out = _collapse_blank_lines(out)
    if text.endswith("\n") and not out.endswith("\n"):
        out += "\n"
    return out
```
- 디폴트로 `M03 → M04 → M19 → M25 → M24` 순.
- trailing newline 보존 책임이 한 곳에 집중 (R54+ 리팩토링).

### 4.4 `kpx.audit`
- `Finding(method, severity, message)` + `Report(score, findings)` dataclass.
- 각 변환별로 텍스트가 어떤 비효율을 갖는지 정적 점검 → 100점에서 차감.
- 스마트 트리거 예: `_looks_like_system_prompt(text)` 가 True일 때만 M09 finding (B9 fix).

### 4.5 `kpx.cli`
argparse 기반 5개 서브커맨드. 모든 file 인자가 `-` 일 때 stdin 읽기 (B12 fix).

| 명령 | 설명 |
|---|---|
| `kpx audit <file>` | 정적 audit. JSON으로 score/findings 출력 |
| `kpx compress <file> [--methods M03,M24] [--output out.txt]` | 변환 체인 적용 |
| `kpx budget <file> --window 200000` | 50% 룰 충족 여부 |
| `kpx methods` | 30 방법 카탈로그 + framing 태그 |
| `kpx format <records.json>` | M15 format_compare 표 출력 |

console_scripts entry: `kpx = "kpx.cli:main"`.

---

## 5. 30 방법 카탈로그 (M01–M30)

| ID | 이름 | Karpathy framing | 구현 상태 |
|---|---|---|---|
| M01 | Token-aware budgeting | F1, F3 | audit-only |
| M02 | Context window halving | F3 | audit-only |
| M03 | Strip pretraining-known facts | F8 | **safe transform** |
| M04 | Minimize system prompt | F2, F3 | **safe transform** |
| M05 | Eliminate redundant role tags | F2 | safe (M25 alias) |
| M06 | Tool schema slimming | F1 | audit-only |
| M07 | Prompt template factoring | F2 | audit-only |
| M08 | Code-as-data instead of NL | F2 | audit-only |
| M09 | Inject no-filler instruction | F4 | **inject** |
| M10 | Few-shot deduplication | F8 | audit-only |
| M11 | Prompt caching adapter | F1 | recommendation |
| M12 | KV cache prefix design | F1 | recommendation |
| M13 | Tool reply truncation | F4 | audit-only |
| M14 | RAG passage compression | F3 | audit-only |
| M15 | Format-compare (JSON/YAML/MD) | F2 | **comparator** |
| M16 | Numeric quantization in prompt | F8 | audit-only |
| M17 | Anti-hallucination short reply | F5 | audit-only |
| M18 | Verifier-side budget | F5 | audit-only |
| M19 | Heuristic lossy summary | F8 | **safe transform** |
| M20 | Multi-turn collapse | F3 | audit-only |
| M21 | History sliding window | F3 | audit-only |
| M22 | Dialect / language switching | F8 | audit-only |
| M23 | Verbosity ceiling instruction | F4 | audit-only |
| M24 | Strip polite filler | F4 | **safe transform** |
| M25 | Strip duplicated role tags | F2 | **safe transform** |
| M26 | Compress error traceback | F5 | audit-only |
| M27 | Tag-free JSON tools | F6 | audit-only |
| M28 | Self-eval cap | F5 | audit-only |
| M29 | Cache-friendly ordering | F1 | recommendation |
| M30 | Pretraining-overlap prune | F8 | audit-only |

상세: [`kpx/docs/METHODS.md`](../../../kpx/docs/METHODS.md), 원본 카탈로그: [ref/Token_최적화_Karpathy_관점.md](Token_최적화_Karpathy_관점.md).

---

## 6. QA 벤치마크 (`bench_real/legacy/`)

### 코퍼스
- 30 prompt = **6 카테고리 × 5 스타일**
- 카테고리: `coding / docs / data / agentic / safety / multilingual`
- 스타일 예: `polite, verbose, code_block, role_tags, signposts, long_history, clean, ...`
- ID는 P01..P30, `Prompt(id, category, style, text)` dataclass.

### 러너
- 10 transform 구성: `none / M03 / M04 / M19 / M24 / M25 / M03+M24 / M04+M25 / all_safe / inject+all`
- 각 (prompt, transform) 쌍을 1번 측정 → 300 round
- 측정 지표: tokens before/after, savings%, runtime ms, audit score before/after, **idempotency check**, **safety probe** (5개 phrase 생존 확인)
- safety probes: `step by step`, `Please note`, `Please refer`, `Please see`, `do not modify`
- 출력: `bench_real/legacy/results.json`, 집계는 stdout

### 마지막 측정 결과 (v0.2.0)
```json
{
  "totals": {"rounds": 300, "errors": 0, "non_idempotent": 2, "safety_violations": 0},
  "best_transform": "all_safe"
}
```
| Transform | 평균 절감 | 멱등 fail | safety fail |
|---|---:|---:|---:|
| **all_safe** | **+21.28%** | 0 | 0 |
| M03+M24 | +9.30% | 0 | 0 |
| M24 | +6.07% | 0 | 0 |
| M19 | +6.01% | 0 | 0 |
| M04+M25 | +5.97% | 0 | 0 |
| M25 | +5.47% | 0 | 0 |
| M03 | +3.31% | 0 | 0 |
| M04 | +0.53% | 0 | 0 |
| inject+all | **−63.34%** | 2 | 0 |

`inject+all` 의 음의 절감은 짧은 prompt에 ~30 token instruction을 추가하기 때문 → README anti-pattern으로 등재 권장.

### 6.1 소스코드 심층 분석 (`bench_real/analysis/`, R3 신규)

LLM 호출/비용 없이 **"kpx가 코딩 시스템 프롬프트에 얼마나 효과적인가"** 를 정량 측정하기 위한 결정론적 정적 분석 트랙.

- **코퍼스**: 15개 실세계 코딩 프롬프트 — Copilot · Cursor · Aider · Claude Code · plain Python · SQL · Bash · 한국어 등 (C01–C15)
- **변형**: V0(raw) / V1(M03) / V2(M24) / V3(M03+M24+M25) / V4(all_safe) / V5(V4+inject) — 총 90 cell
- **7-차원 측정**: 토큰 절감 % / fenced block 보존 / inline code 보존 / 기술 signpost 보존 / Python AST 동등성 / politeness 제거율 / 멱등성
- **실행**: `python -m bench_real.analysis.run_code_analysis` → `bench_real/analysis/results/code_preservation.json`

#### 핵심 결과 (B13 수정 후)

| Variant | 평균 절감 (EN, n=13) | 평균 절감 (KO, n=2) | fence | inline | signpost | py_ast | idem | invariants |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| V0 raw | 0.00% | 0.00% | 2/2 | 10/10 | 22/22 | 1/1 | 15/15 | 15/15 |
| V3 M03+M24+M25 | +18.40% | 0.00% | 2/2 | 10/10 | 22/22 | 1/1 | 15/15 | 15/15 |
| **V4 all_safe** | **+20.95%** | **0.00%** | 2/2 | 10/10 | 22/22 | 1/1 | 15/15 | 15/15 |
| V5 V4+inject | −9.63% | −41% | 2/2 | 10/10 | 22/22 | 1/1 | 15/15 | 15/15 |

- 최고 절감: **C07 refactor-en +48.00%**, C05 plain-python +39.13%, C15 huge-prompt +32.31%, C01 copilot +26.67%, C08 sql-helper +25.76%
- v0.2.0의 +21.28% 자체 벤치 수치가 **완전히 다른 코퍼스**(실세계 코딩 프롬프트)에서 +20.95%로 독립 재현됨
- KO 0% 절감 → i18n 갭 정량 확인 (M24에 한국어 관용구 패턴 추가가 v0.3.0 우선순위)
- 자세한 시각화: [`docs/benchmark-results.html`](benchmark-results.html) §06 "심층 분석 — 소스코드 효율성"

---

## 7. 발견되어 수정된 결함 (v0.1.0 → v0.2.0)

| ID | 심각도 | 증상 | 수정 |
|---|---|---|---|
| **B1** | CRIT | `minimize_system_prompt` 가 "think step by step" 삭제 (Karpathy CoT) | `_REDUNDANT_PHRASES`에서 CoT 표현 제거 |
| **B2** | HIGH | `strip_polite` 가 "Please note/refer/see..." 기술 signpost 제거 | `_POLITE_PATTERNS` 첫 패턴에 negative lookahead |
| **B3** | CRIT | `compress("...")` → `''` (multi-clause line 전체 삭제) | `_is_redundant_line`을 "phrase 제거 후 잔여 단어 ≤ 1" 규칙으로 변경 |
| **B5** | MED | `lossy_summary` 가 flat text를 99% 손실 | sentence-boundary fallback + `[truncated]` marker |
| **B9** | LOW | `audit` 가 짧은 user 텍스트도 M09 finding 발생 | `_looks_like_system_prompt` regex |
| **B10** | HIGH | `strip_known_facts` / `strip_polite` 가 코드 블록 내부 수정 | `_apply_outside_code` 헬퍼 |
| **B11** | MED | `strip_role_tags` 후 다중 공백 잔존 | `[ \t]{2,} → ' '` + leading whitespace 정리 |
| **B12** | FEAT | CLI stdin 미지원 | `_read_input("-")` 헬퍼 |
| **B13** | HIGH | `strip_role_tags` 가 코드 블록 내부 들여쓰기 제거 → Python `SyntaxError` 유발 | M25 핵심 로직을 `_apply_outside_code` 래퍼로 감쌈 (B10과 동일 패턴) |

추가로 `_collapse_blank_lines` 가 trailing newline 책임을 `compress`로 위임 (idempotency 6/300 → 2/300).

> **B13 발견 경위 (R3 deep analysis)** — 신규 정적 분석기(`bench_real/analysis/`)를 15개 실세계 코딩 프롬프트에 처음 돌렸을 때 V3/V4(M25 포함 변형)가 fenced Python 블록의 들여쓰기를 column 0으로 끌어내려 AST parse 실패. 41/41 회귀 테스트가 잡지 못한 실제 결함을 정적 분석이 발견함 — _분석 자체가 안전 게이트가 됨_. 수정 후 모든 변형이 fence/inline/signpost/AST/멱등성 invariant 100% 통과.

---

## 8. 테스트 매트릭스

- `tests/test_kpx.py` — 14개 (R52 origin)
  - 토큰 추정, audit 기본, 각 transform unit, format_compare, CLI smoke
- `tests/test_regressions_v020.py` — 29개 (R54+ 및 R3 deep analysis)
  - **B1**: CoT 표현 보존 (3 케이스)
  - **B2**: 8개 signpost 보존 (parametrize)
  - **B3**: multi-clause 보존 + 순수 redundant 줄 여전히 제거
  - **B10**: ` ``` ` fence + `` ` `` inline 보존
  - **B11**: 다중 공백 collapse
  - **B13**: M25가 fenced 코드 블록 들여쓰기 보존 / `compress(all_safe)` 가 코드 블록 byte-exact 보존 (2 추가 케이스)
  - **M19**: flat text fallback + 멱등성
  - **compress 멱등성 property test**: 5개 다양한 입력
  - **audit M09**: 평문 미트리거 / system-shape 트리거
  - **CLI stdin**: `audit/compress/budget` × `-` (subprocess)

전체 **43/43 PASS**.

---

## 9. 사용 예

### 9.1 라이브러리
```python
from kpx import audit, compress
from kpx.methods import inject_no_filler, format_compare

text = open("prompt.txt").read()
print(audit(text).score)            # 0–100
print(compress(text))               # all safe transforms
print(compress(text, ["M24"]))      # 폴라이트만
print(inject_no_filler(text))       # 시스템 프롬프트 끝에 instruction
print(format_compare(records))      # JSON/YAML/MD 비교
```

### 9.2 CLI
```bash
kpx audit prompt.txt
cat prompt.txt | kpx compress -
kpx compress prompt.txt --methods M03,M24 --output cleaned.txt
kpx budget big_doc.md --window 200000
kpx methods | grep F3
```

### 9.3 rtk와 함께 (dual-side compression)
```bash
# prompt 측 (kpx)
kpx compress system_prompt.txt > slim.txt

# shell-output 측 (rtk-ai/rtk)
rtk run "pytest -v"   # stdout 토큰 절감
```

### 9.4 CI 통합 (예시)
```yaml
- name: Audit prompts
  run: |
    pip install -e ./kpx
    for f in prompts/*.txt; do
      score=$(kpx audit "$f" | jq .score)
      [ "$score" -ge 70 ] || exit 1
    done
```

---

## 10. 패키징·배포

- `pyproject.toml` (PEP 621):
  - `name = "kpx"`, `version = "0.2.0"`, `requires-python = ">=3.9"`
  - dependencies = `[]` (zero runtime deps)
  - optional `yaml = ["PyYAML>=6"]`, `dev = ["pytest>=7","PyYAML>=6"]`
  - classifiers Python 3.9/3.10/3.11/3.12, MIT, Topic :: Text Processing
  - `[project.scripts] kpx = "kpx.cli:main"`
  - `[project.urls]` Homepage / Issues / Methods / Inspiration
  - `[tool.pytest.ini_options]` testpaths=["tests"], addopts="-q"
- `git tag v0.2.0` 적용 (커밋 `6aee0b7`).
- PyPI 배포 미수행 — 실행 명령:
  ```bash
  cd /Users/hacbook/ms/workspace/kpx
  python -m build
  twine upload dist/*
  ```

---

## 11. harness-check 와의 관계

- harness-check은 _오케스트레이션·검증_ 인프라 (Orin/Cassia/Orion/Gaia/Gwen/Evan).
- kpx는 그 인프라가 R52에서 **만들어낸 산출물 중 하나** — 외부에 재사용 가능한 형태로 추출됨.
- 양방향 의존성: **없음**. kpx는 standalone, harness-check은 [ref/kpx_300_results.json](kpx_300_results.json) raw 파일과 [ref/kpx_300_rounds_report.md](kpx_300_rounds_report.md) 만 보유.
- 라운드 R54–R353 (300 directories) 가 캠페인 이력으로 [rounds/round-54](../rounds/round-54) ~ [rounds/round-353](../rounds/round-353)에 영속화.

---

## 12. 향후 로드맵

| Priority | 항목 | 비고 |
|---|---|---|
| ★★★ | PyPI 0.2.0 배포 | `python -m build && twine upload` |
| ★★★ | README anti-pattern 가이드 | `inject+all` 음의 절감 사례 |
| ★★ | tiktoken 옵션 백엔드 | 휴리스틱 vs 실측 비교, `kpx audit --tokenizer cl100k` |
| ★★ | M11 prompt-caching adapter | Anthropic/OpenAI cache hit rate 측정 모듈 |
| ★ | VS Code 확장 | Copilot Chat에 `kpx audit` 사이드바 |
| ★ | multi-tokenizer corpus | 영/한/일/중 별 절감률 비교 |
| ★ | `kpx gain` 누적 통계 | rtk 스타일 |

---

## 13. 라이선스 / 출처

- License: MIT (Copyright 2026 hacbook).
- 영감: [Andrej Karpathy — LLM Practitioner Talks](https://github.com/karpathy), [rtk-ai/rtk](https://github.com/rtk-ai/rtk).
- 30-method 카탈로그 원본: [ref/Token_최적화_Karpathy_관점.md](Token_최적화_Karpathy_관점.md).
- 캠페인 리포트: [ref/kpx_300_rounds_report.md](kpx_300_rounds_report.md).
- Standalone repo: `/Users/hacbook/ms/workspace/kpx` (git, tag `v0.2.0`).
