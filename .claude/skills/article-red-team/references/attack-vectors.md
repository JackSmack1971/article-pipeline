# Attack Vectors — Red Team Reference

## Logical Attack Taxonomy

| Attack | Definition | Example |
|--------|-----------|---------|
| Unstated Assumption | Thesis requires an undefended premise | "AI adoption improves productivity" assumes productivity is measurable and improvement is attributable |
| False Dichotomy | Only two options presented; more exist | "Either adopt AI or fall behind" — many companies selectively adopt with neutral outcomes |
| Scope Overreach | Evidence supports a narrower claim | Study of 50 companies cited to support claim about "enterprise-wide" behavior |
| Composition Fallacy | Component truth generalized to the whole | Individual components improve, therefore the system improves — often false in complex systems |
| Causal Overclaim | Correlation treated as directional causation | "Companies using X report higher revenue" — revenue growth may attract X adoption, not cause it |
| Cherry-Picked Timeframe | Data window chosen to flatter conclusion | "X grew 40% since 2021" — 2021 was a trough; relative to 2019 the growth is negligible |
| Survivorship Bias | Only successful cases studied | "Companies that adopted Y succeeded" — failed adopters are unrepresented in the dataset |
| CEO Revenue Conflation | Aggregate earnings-call figure attributed to a specific product category or deployment subset | "Microsoft's $37B AI revenue proves agentic adoption" — the figure covers all AI products (Copilot, Azure, infrastructure), not agentic deployments specifically. Any exec "run-rate" or "segment revenue" cited as evidence for a narrow claim requires checking what the figure actually covers. |

## Framing Vulnerability Taxonomy

| Vulnerability | Detection Question |
|---------------|-------------------|
| Metric manipulation | Which KPI was chosen, and does another KPI tell a different story? |
| Audience mismatch | Is the conclusion actionable for the stated audience, or only for a subset? |
| Temporal obsolescence | Is the conclusion based on a context that no longer exists? |
| False precision | Does the level of numerical specificity exceed the data's actual precision? |
| Anchoring bias | Does the framing of the thesis pre-dispose the reader toward one interpretation before the evidence is examined? |

## Threat Level Calibration

**LOW:** The counterargument is valid but doesn't change the article's practical utility.
A critical reader might note it; a practitioner reader would not.

**MEDIUM:** The counterargument identifies a gap the article should acknowledge. A skilled
reader in the field will notice the omission. A limitations section or a qualifying clause
in the conclusion resolves it.

**HIGH:** The counterargument, if raised by a critic, would undermine the article's core claim
in the eyes of the target audience. The thesis as stated cannot survive without addressing it.
Requires substantive revision — not just a disclaimer.

## Rules for the Red Team

1. Produce the strongest version of each attack — not a strawman.
2. Mark any empirical claim as `[RED TEAM ASSERTION — unverified]` if you cannot cite it.
3. Do not fabricate data or citations. Intellectual honesty is the constraint.
4. If no meaningful attack exists for a vector, state that explicitly — a clean bill of health
   on a vector is also a useful signal.
5. The threat level must be determined by how a well-informed critical reader of the target
   audience would respond — not by how persuasive the attack feels to you.

## Standing Heuristics (apply to every COMPLEX run)

These patterns recur across runs. Check each one explicitly before writing the threat assessment.

**Revenue/Financial Figure Scope:** Any executive revenue run-rate, segment revenue, or
earnings-call figure cited in the article as evidence for a specific deployment category
or product subset — check what the figure actually covers. Aggregate AI revenue (cloud
infrastructure + copilot + consumer) routinely gets cited as evidence of specific agentic
or enterprise adoption. If the article uses such a figure and the figure's actual scope
is broader than the claimed application: flag as CEO Revenue Conflation, threat level
at least MEDIUM.

**Governance Tension Self-Refutation:** If the article's thesis critiques concentration,
monopoly, or asymmetric control in a domain, check whether the primary examples cited
in favor of the thesis are themselves examples of the same concentration. (e.g., arguing
blockchain solves monopoly while relying on a single dominant chain as the evidence base.)
This is a self-refutation variant of Scope Overreach — flag if present.
