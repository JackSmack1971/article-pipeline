# Triage Rubric — Dimension Scoring Guide

## Novelty (0.35 weight)

| Score | Criteria |
|-------|----------|
| 1 | Topic is fully settled. Established consensus, abundant primary literature, stable definitions. E.g., "How TCP/IP works." |
| 2 | Topic is well-covered but has recent updates. Core claims stable; periphery evolving. E.g., "State of remote work 2024." |
| 3 | Meaningful portion postdates 2023 or is rapidly evolving. Some primary sources unavailable. |
| 4 | Topic is primarily 2024–present or in a niche domain with sparse secondary literature. |
| 5 | Topic is cutting-edge (< 12 months), proprietary, or highly domain-specific with minimal public sourcing. |

## Contentiousness (0.40 weight)

| Score | Criteria |
|-------|----------|
| 1 | No credible disagreement. All relevant authorities concur. |
| 2 | Minor framing differences but no factual disputes among credible sources. |
| 3 | Documented disagreement on interpretation or methodology. Multiple defensible positions exist. |
| 4 | Active factual disputes. Studies contradict. Regulatory or political dimension present. |
| 5 | Deeply contested. Fundamental definitions disputed. High reputational/legal sensitivity. |

## Scope (0.25 weight)

| Score | Criteria |
|-------|----------|
| 1 | Single, tightly-bounded claim. 1–2 research vectors sufficient. |
| 2 | 2–3 distinct sub-topics. Manageable in 1,800–2,400 words. |
| 3 | 4–5 sub-topics. Requires explicit section hierarchy. 2,400–3,200 words. |
| 4 | 6–8 sub-topics or cross-domain synthesis. Risk of scope creep. |
| 5 | 9+ sub-topics or requires background explainers before the core argument. Consider splitting the brief. |

## Calibration Overrides (applied from pipeline_learnings.md)

When a `[CALIBRATION]` tag appears in pipeline_learnings.md, extract:
- `calibration.novelty_bias`: ±0.5 adjustment to novelty score
- `calibration.budget_kc1_topics`: list of topic keywords triggering budget bump

These are additive adjustments to raw scores before composite calculation.
