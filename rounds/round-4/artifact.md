## Recommendation

현재 kpx 벤치마크는 재현 가능한 편이지만, 리더보드 해석은 아직 평균 중심이다. 다음 단계는 더 많은 실험이 아니라, 같은 실험을 더 엄격하게 읽는 것이다.

### Actions
1. 모든 summary에 `mean`, `95% CI`, `n`, `variance`, `judge_n`를 표시한다.
2. run manifest에 `git_sha`, `benchmark_version`, `adapter`, `judge_adapter`, `pricing_version`, `seed`를 저장한다.
3. pricing table 변경 시 과거 결과와 직접 비교하지 않도록 version을 분리한다.
4. regression gate tier를 만들어 PR 레벨에서 빠른 회귀 감지용 최소 셋을 항상 실행한다.
5. `cost_per_quality_point`와 `quality_per_1k_tokens_saved`를 추가해 비용-효율 관점의 ranking을 제공한다.

### Why this matters
- 작은 delta는 분산과 비용을 같이 봐야 의미가 있다.
- 운영 환경에서는 최고 점수보다 비용당 개선량이 더 중요할 수 있다.

### Source notes
- OpenAI evals: usage와 criteria 결과를 함께 제공.
- lm-evaluation-harness: integrity check, log_samples, caching, visualization 지원.
- Anthropic: 복잡도는 측정 가능한 개선이 있을 때만 추가.