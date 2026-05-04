## Recommendation

가장 먼저 개선할 것은 점수 자체보다 데이터셋 관리 방식이다. 현재 kpx 벤치마크는 재현성은 좋지만 정적 셋 중심이라 시간이 지날수록 contamination과 benchmark gaming에 취약해진다.

### Actions
1. `bench_real/tasks/`를 `public_dev`, `public_test`, `private_holdout` 개념으로 재편한다.
2. `bench_real.runner` 결과 행에 `benchmark_version`, `split`, `task_origin`, `created_at_cutoff`를 기록한다.
3. 월간 또는 분기별로 새 문제를 추가하고, 직전 private split은 일정 기간 후 public으로 승격한다.
4. 문서 headline은 `overall` 외에 `fresh holdout only`와 `public only`를 분리해 표기한다.
5. 중복·준중복 프롬프트를 포함한 contamination canary 셋을 별도 관리한다.

### Why this matters
- 최신성 없는 리더보드는 실제 개선보다 암기/노출 효과를 반영하기 쉽다.
- 공개 셋과 비공개 셋을 분리해야 prompt optimization이 진짜 일반화되는지 볼 수 있다.

### Source notes
- LiveBench: 주기적 갱신, 최신 문제 비공개 유지, 객관 채점 중심.
- SWE-bench Verified: human-filtered subset으로 신뢰 가능한 비교 환경 제공.