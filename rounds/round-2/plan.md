## Round 2 — Graders / Rubrics / Judge Reliability

### Goal
품질 판정을 더 세분화하고 judge drift를 줄인다.

### Local evidence
- `bench_real/runner.py`는 tier-2 judge를 확률 샘플링으로만 호출한다.
- `bench_real/views/p3_safety_audit.py`는 안전성의 요약값은 제공하지만 judge disagreement나 세부 failure reason은 남기지 않는다.

### External evidence
- OpenAI evals는 task schema와 testing criteria를 명시적으로 분리한다.
- Vertex AI Gen AI Evaluation은 prompt별 adaptive rubric을 권장하고 pass/fail reason을 남긴다.
- Anthropic evaluator-optimizer 패턴은 평가 기준이 명확할수록 반복 개선 가치가 높다고 본다.

### Proposed change set
1. task별 고정 rubric과 sample별 adaptive rubric을 함께 저장한다.
2. LLM judge 결과를 단일 점수 대신 criterion-level pass/fail로 보존한다.
3. judge model 2개 교차평가 또는 same-judge n=2 재시도로 disagreement rate를 측정한다.
4. quality headline 옆에 confidence interval과 disagreement rate를 같이 표기한다.
5. `failed cases` 뷰를 추가해 왜 졌는지 바로 읽을 수 있게 한다.

### Cheap validation
- 한 run에서 10개 샘플만 추출해 rubric JSON과 judge reason이 모두 생성되는지 확인.