## Round 6 Artifact — Live API benchmark via GitHub Models

### Implementation delivered
| File | Purpose |
|---|---|
| [bench_real/adapters/github_models.py](bench_real/adapters/github_models.py) | OpenAI-호환 GitHub Models adapter (gh token 자동, 429/5xx exp backoff, reasoning 모델 분기) |
| [bench_real/adapters/\_\_init\_\_.py](bench_real/adapters/__init__.py#L46) | `get_adapter("github")` 등록 |
| [bench_real/runner.py](bench_real/runner.py#L56) | `--adapter` choices 에 `github`, `google` 추가 |
| [bench_real/run_all_github.py](bench_real/run_all_github.py) | 카탈로그 자동 페치 + per-model subprocess + timeout + 통합 JSONL |
| [bench_real/aggregate.py](bench_real/aggregate.py) | 모델 × 변형 별 평균 토큰/품질/지연/오류 + V0→V4 절감률 |

### Execution status (background)
- 명령: `nohup python -u -m bench_real.run_all_github --tier lite --run-id r6-all --judge-adapter mock --per-model-timeout 1200`
- 로그: [bench_real/runs/r6-all.log](bench_real/runs/r6-all.log)
- 출력: `bench_real/runs/lite-r6-all/<safe_model>.jsonl` (30 파일 예정) + 통합 `bench_real/runs/lite-r6-all.jsonl`
- 진행률 (이 라운드 영속화 시점): **3/30 모델** (~1 시간 경과)
- ETA: 가변 (모델별 latency 편차 큼. 7B급 ~2s/cell, 70B+ ~20s/cell, 일부 5xx 백오프 ~30s/cell)
- 사용자 USD 비용: **$0** (GitHub Models quota 기반)

### Partial findings (3 models 완료)
| Model | n | ok | err | avg tok V0 | avg tok V4 | save% | quality V0→V4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| ai21-labs/ai21-jamba-1.5-large | 111 | 0 | 111 | – | – | – | – (HTTP 400 `unknown_model` — 카탈로그 등록되나 inference 미배포) |
| cohere/cohere-command-a | 111 | 105 | 6 | 58.7 | 53.7 | **+8.52%** | 86.5 → 85.4 (Δ −1.1) |
| cohere/cohere-command-r-08-2024 | (진행중) | 0 | 21 | – | – | – | – (HTTP 500 `invalid_model_endpoint_authentication` — 백엔드 오류) |

### Findings (initial)
- **GitHub Models 카탈로그 ≠ 가용 모델**: 43종 catalog 중 일부는 inference 미배포. 사전 ping 없이는 식별 불가.
- **cohere-command-a 결과**: V4 가 V0 대비 prompt tokens 8.52% 절감, 품질은 86.5→85.4 (1.1 점 하락, judge=mock 기준). 사용자 측 추가 검증 필요.
- **mock judge 한계**: tier-2 점수가 결정론적이라 quality delta 의 통계적 유의성은 아직 평가 불가. Cross-vendor LLM judge 가 후속 과제.

### Validation
- `PYTHONPATH=. pytest -q` → **43 passed** (Round 6 변경 후 회귀 없음).
- 스모크 1: `runner --adapter github --model openai/gpt-4o-mini --max-cases 2` → 6/6 OK (12.3s).
- 스모크 2: wrapper 2 모델 dry run → gpt-4o-mini 6 OK, phi-4-mini hang → per-model timeout 추가로 해결.

### How to harvest final results (사용자용)
```bash
# 진행 상황
tail -f bench_real/runs/r6-all.log
ls bench_real/runs/lite-r6-all/

# 완료 후 최종 집계
PYTHONPATH=. python -m bench_real.aggregate \
  --runs-dir bench_real/runs/lite-r6-all \
  --out bench_real/runs/lite-r6-all/_aggregate.json

# 중단하려면
pkill -f "bench_real.run_all_github"
pkill -f "bench_real.runner"
# resume: 같은 명령 재실행 (--no-resume 미사용 시 기존 셀 skip)
```

### Out of scope (intentionally deferred)
- **reasoning 모델 6종** (o1/o3/o4/r1/phi-4-reasoning/mai-ds-r1): adapter 분기는 구현했으나 1차 run 에서 제외. `--include-reasoning` 으로 opt-in.
- **standard/deep tier** (V0..V5 × repeats=3): lite 결과 검증 후 결정 (~6배 시간).
- **cross-vendor LLM judge**: 호출량 2배 + rate-limit 위험. 1차 lite 완료 후 별도 라운드 권고.
- **vendor-direct API** (openai.com/anthropic.com/googleapis.com): 사용자 API 키 부재로 실행 불가. 키 확보 시 별도 라운드.
