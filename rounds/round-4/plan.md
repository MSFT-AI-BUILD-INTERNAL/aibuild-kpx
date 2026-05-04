## Round 4 — Reproducibility / Cost / Statistical Reporting

### Goal
점수 해석을 더 엄격하게 만들고, 비용 대비 신뢰도를 높인다.

### Local evidence
- runner는 seed, cap-usd, resume를 지원한다.
- 현재 README와 결과 요약은 headline mean 위주이며 분산, CI, judge variance, model routing effect는 드러나지 않는다.

### External evidence
- OpenAI evals는 run-level usage와 criteria results를 함께 남긴다.
- lm-evaluation-harness는 caching, integrity checks, sample logging, result visualization을 강조한다.
- Anthropic은 complexity를 증명 가능한 개선이 있을 때만 늘리라고 권고한다.

### Proposed change set
1. 모든 headline metric에 bootstrap CI 또는 standard error를 붙인다.
2. run manifest에 commit SHA, task version, adapter version, pricing table version을 남긴다.
3. cached / uncached token usage를 분리해 prompt caching 효과를 독립적으로 본다.
4. 소규모 smoke, standard, deep 외에 regression gate tier를 추가한다.
5. 실험 비교는 mean뿐 아니라 cost-normalized gain, variance-normalized gain으로 정렬한다.

### Cheap validation
- 결과 JSONL 한 개에서 summary script가 CI와 run manifest를 생성하는지 확인.