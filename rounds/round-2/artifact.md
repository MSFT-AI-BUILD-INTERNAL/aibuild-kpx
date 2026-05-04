## Recommendation

현재 벤치마크는 `rule_based + optional llm_judge` 구조라 가볍고 실용적이지만, 개선 루프를 돌릴 때 어디서 성능이 무너졌는지 보기가 어렵다. 다음 단계는 judge를 더 자주 쓰는 것이 아니라, judge 결과를 더 잘 구조화하는 것이다.

### Actions
1. 각 샘플에 대해 `rubric.json` 또는 JSON column 형태로 세부 기준을 저장한다.
2. LLM judge 출력은 총점만 두지 말고 `criterion`, `pass`, `reason`, `evidence_span`으로 저장한다.
3. 품질 뷰에는 `mean`, `95% CI`, `judge disagreement`, `unjudgeable rate`를 함께 표시한다.
4. safety와 translation은 deterministic metric과 LLM judge를 모두 실행해 상충 사례를 따로 모은다.
5. `bench_real/views/`에 failure gallery를 추가해 대표 실패 사례를 바로 열람 가능하게 한다.

### Why this matters
- 점수만 있으면 개선 우선순위를 정하기 어렵다.
- criterion-level 저장은 prompt 변경이 무엇을 악화시켰는지 빠르게 드러낸다.

### Source notes
- OpenAI evals: task schema와 testing criteria 분리.
- Vertex AI Evaluation: adaptive rubric + pass/fail reason.
- Anthropic: evaluator-optimizer는 명확한 평가 기준이 있을 때 효과적.