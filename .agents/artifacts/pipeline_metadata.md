# Pipeline Metadata

## Run Summary
- Topic: Cognitive/epistemic warfare — distinguishing individual-level cognitive targeting from institutional-level epistemic targeting
- Depth: COMPLEX (composite score 4.65; novelty 4, contentiousness 5, scope 5)
- Publish date: 2026-08-08
- Author: none declared (project convention — see `CLAUDE.md` Author section)
- Final word count: 3,373 words (canonical Markdown-token count)

## Phases Completed
TRIAGE → RESEARCH (advocate/skeptic dialectic) → FACTCHECK → APPROVAL (human gate) → DRAFT (9 sections, inline QA) → POSTDRAFT (red team + reader simulation) → SEO → LEARNING. All phases configured for COMPLEX depth (`adversarial_dialectic`, `fact_check`, `red_team`, `seo_pass`, `draft_in_phases` all `true`) completed.

This run resumed mid-pipeline: session state (`pipeline_state.json`) showed the APPROVAL gate already recorded as `approved` (with `conflict_decisions.json` written) but `stage` had not advanced to `DRAFT` before the prior session ended. Resumed per user confirmation directly into Step 3 drafting rather than re-running TRIAGE or APPROVAL.

## Revision Cycles
- TRIAGE_THESIS_CONFIRM gate: 1 cycle (`rephrase`, then confirmed) — within the 3-cycle limit.
- APPROVAL gate: 0 revision cycles (`approved` on first presentation, in the prior session).
- Inline drafting: 0 `BLOCKED` verdicts across all 12 recorded audit verdicts (9 initial sections + 3 post-red-team + none required post-reader-sim beyond the 3 already counted in post-red-team — see Audit Log detail below). `consecutive_blocked_audits` remained 0 throughout.
- Holistic audit: 1 pass, verdict PASS, no revision cycle needed.

## KC (Kill Condition) Events
- KC-3 (source diversity): PASS — max single-source share ~8% (cetas.turing.ac.uk / act.nato.int variants, ≤4 of 48 research-phase claims).
- KC-6 (contradiction resolution): PASS — 0/7 research vectors classified INSUFFICIENT on either advocate or skeptic stream.
- KC-5 (token budget mid-draft): not triggered.
- No HALT events this run.

## Gates Expedited
None. `gate_expedite_count`: 0.

## Token / Budget Notes
- Configured token budget: 48,000 (`pipeline_config.json`).
- No KC-5 mid-draft budget halt triggered; drafting completed in a single continuous pass across all 9 sections plus the post-red-team and post-reader-sim polish passes.

## Tool Degradation
- `code_execution`: unavailable this session (`pipeline_config.json.pipeline.tool_availability.code_execution: false`). No VIZ-CANDIDATE sections were flagged in `article_spec.md` (evidentiary base is doctrinal/legal/philosophical, not quantitative), so this had no downstream effect on the draft.
- `web_search`: available throughout; used for original research (advocate/skeptic streams), fact-check, and independent verification of the two red-team-flagged claims before incorporation.

## Material Gate Decisions
- **APPROVAL**: approved. All 4 conflicts (C-1, C-2, C-4: neutral; C-3: unresolved) defaulted per `conflict_decisions.json`, since no conflict-specific handling was individually specified by the user at that gate.
- **Red Team (Step 4)**: `address`. Threat level MEDIUM. Two empirical claims from the red-team report were independently web-verified before incorporation; one attribution (Chile neurorights redundancy critique) was corrected from the red team's own draft attribution ("Bublitz and others") to the verified source (Pablo Contreras / Stanford Law School analysis) rather than repeated uncritically. See `red_team_report.md` "Resolution" section.
- **Reader Simulation (Step 5)**: `polish`. Accessibility rating ACCESSIBLE (1 HIGH, 3 MEDIUM, 2 LOW gaps). Top 3 gaps addressed: removed an unresolved `†` citation-tier symbol with no reader-facing meaning, defined GDPR on first use, and clarified the stakes of the UN Charter "prohibited force" threshold.

## Conflict Resolution Summary (from `conflict_register.md` / `conflict_decisions.json`)
| ID | Axis | Handling | Where addressed |
|---|---|---|---|
| C-1 | Definitional/Interpretive | Neutral | "What Is Cognitive Warfare, and Is It a Coherent Doctrine?" |
| C-2 | Interpretive/Normative | Neutral | "Is Epistemic Security a Neutral Framework or a New Site of Power?" |
| C-3 | Interpretive (internal logical vulnerability) | Unresolved (flagged explicitly) | "Is Epistemic Security a Neutral Framework or a New Site of Power?" §"An Unresolved Tension, Not a Resolved One"; revisited in the conclusion |
| C-4 | Empirical/Methodological | Neutral | "Is Chile's Neurorights Model a Precedent Worth Following?" |

## Red Team Rating
MEDIUM threat level. See `red_team_report.md` for full attack-vector breakdown and resolution.

## Reader Simulation Rating
ACCESSIBLE (post-polish). See `reader_questions.md` for full gap register.

## Artifacts Written This Run
`pipeline_config.json` (pre-existing), `article_spec.md` (pre-existing), `conflict_register.md` (pre-existing), `conflict_decisions.json` (pre-existing), `article_draft.md`, `audit_log.md`, `audit_report.md`, `red_team_report.md`, `reader_questions.md`, `seo_package.md`, `pipeline_metadata.md` (this file).
