## Round 1 — Freshness / Contamination Control

### Goal
Reduce benchmark overfitting risk and make future benchmark claims harder to game.

### Local evidence
- Current benchmark layout is mostly static: fixed task JSON files in `bench_real/tasks/` and resumable JSONL outputs in `bench_real/runs/`.
- Existing plan emphasizes reproducibility and cost caps, but not explicit contamination control or rolling holdouts.

### External evidence
- LiveBench refreshes questions regularly and delays releasing the newest questions to reduce contamination.
- SWE-bench Verified improves reliability by human-filtering a smaller subset rather than trusting raw benchmark instances.

### Proposed change set
1. Split tasks into `public-dev`, `public-test`, and `private-holdout` partitions.
2. Add a rolling release cadence, for example monthly or quarterly, with archived benchmark versions.
3. Sample a small holdout from production-like prompts or recent internal prompt logs.
4. Add contamination canaries: near-duplicate prompts, public prompt variants, and post-cutoff tasks.
5. Report scores by benchmark version, not just a single aggregate headline.

### Cheap validation
- Confirm each run artifact records a benchmark version and split name.
- Confirm at least one private split is excluded from docs and committed task JSON.