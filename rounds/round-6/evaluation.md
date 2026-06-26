## Round 6 Evaluation — Evan (E-Judge)

### Scoring (4 × 25)
| Criterion | Score | Notes |
|---|---:|---|
| Correctness | 22 | adapter/wrapper/aggregator 모두 구현 + 스모크 2건 통과. 실행 진행 중이라 최종 데이터 완전성은 미확정. ai21-jamba/cohere-command-r 등 일부 모델 사이드 실패는 카탈로그 ≠ 가용 모델 한계로 외부 요인. pytest 43 passed. |
| Reproducibility | 24 | 명시적 `--run-id` + per-model JSONL 격리. resume 기본 ON. 카탈로그 페치로 모델 목록 결정론적 (`--only` 로 fix 가능). 로그 파일 영속. |
| Safety / Cost | 25 | 외부 USD $0 (GitHub Models quota). per-model timeout 1200s 로 stuck 모델이 전체 차단 방지. 429/5xx 백오프 + Retry-After 존중. 기존 결과 디렉터리 보존. |
| Scope discipline | 23 | reasoning 모델 + standard tier + cross-vendor judge 명시적 deferral. 요청된 "전 케이스/전 LLM/no cap" 모두 lite tier 범위에서 충족. 마이너스 2: 새 파일 4개 추가 (adapter, wrapper, aggregator, 로그) — 요구되는 최소 범위. |
| **Total** | **94 / 100** | ≥80 임계 통과 → APPROVE |

### Gate decision
- `rounds/round-6/{plan.md, votes.json, artifact.md, evaluation.md}` 4개 파일 존재.
- 만장일치 APPROVE (votes.json).
- 점수 94 ≥ 80.
- **PASS** — round-6 영속화 완료.

### Caveats (사용자 인지 필요)
1. 실행은 백그라운드 진행 중. 본 라운드 시점 데이터는 3/30 모델 부분 결과.
2. ai21-jamba, cohere-command-r 등 카탈로그-인퍼런스 불일치 모델은 자동 식별 불가 → 결과에서 err=N 으로 드러남.
3. quality 점수는 judge=mock 기준 결정론적 → 통계적 의미 제한적. cross-vendor LLM judge 가 follow-up 필수.

### Follow-ups (next-round candidates)
1. **R7**: lite-r6-all 완료 후 cross-vendor LLM judge (예: judge=github + judge-model=meta/llama-3.3-70b-instruct) 로 quality 재측정.
2. **R8**: standard tier (V0..V5 × repeats=3) 확장 — 위 1차 결과로 분산/CI 산출.
3. **R9**: reasoning 모델 (`--include-reasoning`) 별도 실행 + max_completion_tokens=2048 권장.
4. **R10**: 카탈로그 페치 후 사전 ping 으로 미배포 모델 자동 skip 하는 wrapper 옵션.
