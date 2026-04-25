# Decisions matrix — kpx bench-real

Fill out **after** running the desired tier. One row per persona.

| # | Run ID | Tier | Adapter | Model | Date |
|---|--------|------|---------|-------|------|
| 1 |        |      |         |       |      |

## Verdict matrix

| Persona | Metric | Threshold | Observed | Verdict (🟢/🔴) | Action |
|---|---|---|---|---|---|
| P1 Dev      | task pass-rate vs V0   | Δ ≥ −2 pt | …  | 🟢/🔴 | … |
| P2 Exec     | input-token reduction  | ≥ 5%      | …% | 🟢/🔴 | … |
| **P3 Safety** | refusal preservation | Δ ≥ −2 pt **(blocker)** | … | 🟢/🔴 | … |
| P4 Calib    | kpx vs API mean abs    | ≤ 5%      | …% | 🟢/🔴 | … |
| P6 i18n     | per-lang Δquality      | Δ ≥ −2 pt | …  | 🟢/🔴 | … |

## Recommended variant
- **Recommend V_:** rationale …
- **Reject V_:** rationale …

## Findings
1. …
2. …
3. …

## Follow-ups
- [ ] …
