# Control-Plane Improvement Protocol

## Purpose

This protocol governs changes intended to improve the Claude Code control plane that produces researched, fact-checked, publication-ready long-form articles in this repository.

The optimization target is the **article pipeline as a product**: topic brief and thesis routing, research, adversarial evidence collection, fact checking, human conflict decisions, drafting, QA, post-draft challenge, reader simulation, SEO packaging, persisted artifacts, and cross-run learning.

The goal is not more orchestration. The goal is a higher rate of articles that are:

- factually sound and correctly cited;
- appropriately calibrated to uncertainty and conflicting evidence;
- coherent, useful, and accessible to the declared audience;
- structurally publishable under the repository artifact contract;
- produced with less unnecessary cost, context, latency, rework, and human rescue.

The default outcome of an inconclusive experiment is **no change**.

## Product model

The current control plane is intentionally hybrid:

- the main Claude session owns end-to-end orchestration and artifact handoffs;
- `pipeline_config.json` routes SIMPLE, STANDARD, or COMPLEX depth;
- advocate and skeptic are isolated research subagents because independence is part of the epistemic design;
- the red-team subagent receives only thesis plus conclusion to reduce anchoring;
- fact-check, drafting/QA, reader simulation, and SEO are stage-specific judgment procedures;
- `scripts/pipeline_runner.py` owns deterministic state mutation and finalization;
- `scripts/validate_artifacts.py` checks the persisted artifact contract and configured publication blockers;
- `.agents/artifacts/` is live article-run state;
- `.agents/knowledge/article-pipeline/` is cross-run product learning.

Do not collapse these into one generic "agent success" metric.

A `PUBLISHABLE` validator result proves the persisted artifact contract is acceptable under the current deterministic checks. It does **not** independently prove that the article is accurate, well sourced, balanced, clear, or better than a baseline article. Article quality requires independent graders.

## Scope

Use this protocol when changing or evaluating anything that can materially affect the article pipeline, including:

- `CLAUDE.md` or other always-loaded project instructions;
- article skills, references, triggers, rubrics, or handoff contracts;
- article subagent definitions, delegation payloads, models, effort, or tool capabilities;
- SIMPLE/STANDARD/COMPLEX routing;
- research, synthesis, fact-check, drafting/QA, red-team, reader, SEO, or learning behavior;
- approval gates and persisted conflict decisions;
- runner, validator, artifact-contract, manifest, counter, schema, or state behavior;
- summarization, context management, memory, compaction, or cross-run learning;
- benchmark and article-quality evaluation infrastructure;
- adoption, replacement, ablation, or removal of native/custom orchestration machinery.

Ordinary article generation follows `.claude/skills/multi-agent-article-pipeline/SKILL.md`. This protocol applies when the pipeline itself is the experimental object.

## Core rule

Treat every behavior-changing control-plane modification as a falsifiable experiment.

Before implementation, state:

1. the concrete failure mode or wasted resource;
2. the causal hypothesis;
3. the smallest credible intervention;
4. the primary observable metric;
5. the minimum improvement worth keeping;
6. the hard guardrails that must not regress;
7. the evaluation method capable of disproving the hypothesis.

Do not retain a change because it looks cleaner, more advanced, more agentic, or more deterministic. Retain it because evidence demonstrates net product value.

## Enforcement model

Prompt instructions are guidance. Executable controls are enforcement.

When a property must hold regardless of model judgment, prefer the strongest appropriate mechanism:

- restricted subagent capabilities for information boundaries;
- deterministic runner logic for state and counters;
- schemas and manifest validation for persisted artifacts;
- explicit gate artifacts for human decisions;
- tests for objective behavior;
- independent graders for final article outcomes.

Do not claim a behavior is enforced merely because it appears in prose, frontmatter, or documentation. Inspect the executable or capability path and realistic bypasses.

## Product metrics

### Qualified publish rate

For broad end-to-end changes, the default primary metric is **qualified publish rate (QPR)**:

> QPR = proportion of runs that (a) satisfy the deterministic publishable artifact contract, (b) pass predeclared independent factual/citation guardrails, (c) meet the predeclared editorial/audience threshold, and (d) require no undeclared human rescue.

Freeze the exact thresholds before candidate results are seen.

`PUBLISHABLE` alone is not QPR.

### Epistemic metrics

Useful subsystem metrics include:

- material factual-claim precision;
- unsupported-claim rate;
- citation correctness and source-support rate;
- dead, mismatched, or fabricated citation rate;
- VERIFIED-UPDATED adoption rate;
- unqualified MEDIUM/LOW claim rate;
- DISPUTED/OUTDATED leakage into settled prose;
- source diversity and concentration;
- conflict-decision fidelity;
- advocate/skeptic evidence overlap and diversity.

### Editorial and audience metrics

Useful metrics include:

- blind editorial pass rate;
- thesis/conclusion coherence;
- logical continuity;
- calibrated nuance;
- target-audience explanation quality;
- reader HIGH-gap rate;
- jargon/assumed-knowledge burden;
- post-red-team residual vulnerability;
- unnecessary redundancy or structural monotony.

### Control metrics

Useful metrics include:

- routing correctness;
- false `COMPLETE` rate;
- stale-manifest acceptance rate;
- stale-word-count acceptance rate;
- gate/counter correctness;
- adversarial-isolation violation rate;
- artifact-contract pass rate;
- unnecessary revision or gate interaction rate.

### Efficiency metrics

Measure quality-adjusted efficiency:

- cost per qualified publish;
- tokens per qualified publish;
- web searches per qualified publish;
- tool calls and agent calls per qualified publish;
- wall time per qualified publish;
- revision cycles;
- human gate interactions and rescue interventions.

A cheaper article that fails quality guardrails is not an efficiency win.

## Default hard guardrails

Unless the experiment explicitly justifies a different set, broad control-plane changes must preserve:

- zero fabricated citations, URLs, quotations, author credentials, or publisher metadata in graded output;
- zero known-DISPUTED or OUTDATED claims presented as verified fact;
- zero silent conflict-decision drift on graded conflicts;
- zero advocate/skeptic/red-team isolation violations in boundary tests;
- zero false `COMPLETE` or stale-manifest acceptance regressions;
- zero bypass of required approval or kill-condition behavior;
- no material drop in the deterministic regression suite;
- no loss of required audit/evidence traceability.

A hard guardrail failure rejects the candidate regardless of aggregate score.

## Evidence levels

Use the strongest practical level:

- **E0 — assertion:** model or human says the change is better.
- **E1 — anecdote:** one favorable trace or article.
- **E2 — reproduction:** a demonstrated defect fails before and passes after.
- **E3 — controlled comparison:** matched baseline/candidate trials across repeated briefs.
- **E4 — held-out validation:** matched comparison on briefs or graders unavailable to the optimizer.
- **E5 — field validation:** sustained improvement on real production-like article work.

E2 can justify "this defect is fixed." It cannot justify "articles are better" or "the pipeline is more accurate." Broad quality claims normally require E3; high-impact routing, factuality, isolation, gating, or evaluator changes should reach E4 when feasible.

## Experiment classes

### Class A — non-behavioral clarification

Examples: correcting stale file references or explanatory prose without changing loaded behavior.

Minimum evidence:

- source verification;
- diff review;
- reference/path validation.

### Class B — localized behavioral change

Examples: one skill rule, one claim-status precedence rule, one subagent capability boundary, one runner counter, one validator condition.

Minimum evidence:

- targeted reproduction;
- focused deterministic regression coverage when applicable;
- matched baseline/candidate trials on affected stochastic behavior;
- repository verification.

### Class C — cross-cutting orchestration change

Examples: depth routing, research dialectic structure, fact-check strategy, drafting/QA loop, context compression, broad `CLAUDE.md` changes, adding/removing a pipeline stage.

Minimum evidence:

- controlled article comparison;
- multiple representative brief families;
- affected depth coverage;
- repeated trials;
- factual/editorial guardrails;
- efficiency measurement;
- trace audit.

### Class D — enforcement or evaluator change

Examples: adversarial-isolation boundaries, approval/finalization gates, stale-artifact rules, factuality/editorial graders, hidden-eval infrastructure.

Minimum evidence:

- Class C evidence;
- explicit bypass/mutation tests;
- independent validation of the control/evaluator;
- held-out confirmation when feasible;
- old/new dual evaluation when grader logic changes.

Use the higher class when uncertain.

## Experiment record

Create the record before implementation. Store transient benchmark material under `.agents/control-plane-evals/<experiment-id>/` or an external evaluator workspace. Never use `.agents/artifacts/` for experiment bookkeeping.

Minimum record:

```yaml
id: cp-YYYYMMDD-short-name
class: B | C | D
status: proposed | running | accepted | rejected | inconclusive
finding:
  failure_mode: ""
  reproduction: ""
  evidence_level_before: E0-E5
hypothesis: ""
candidate:
  intervention: ""
  why_smallest_credible: ""
metrics:
  primary: ""
  minimum_worthwhile_effect: ""
  hard_guardrails: []
comparators: []
evaluation:
  suites: []
  brief_families: []
  pipeline_depths: []
  scripted_gate_decisions: true
  trials_per_brief: null
  heldout_used: false
quality:
  qualified_publish_definition: ""
  factuality_grader: ""
  editorial_grader: ""
budget:
  max_cost_usd: null
  max_wall_time_minutes: null
environment_manifest: ""
result: null
```

Do not backfill the hypothesis, threshold, or guardrails after seeing candidate results.

## Phase 1 — Establish the finding

### Reproduce first

A useful reproduction identifies:

- the triggering article brief, stage, or state;
- expected behavior;
- observed behavior;
- exact evidence of the mismatch;
- whether the failure is deterministic, stochastic, or source/environment dependent.

If the issue cannot be reproduced, record that uncertainty. Do not add machinery to solve a hypothetical failure without evidence that its expected value justifies the cost.

### Verify novelty

Before calling a weakness new, inspect:

- the relevant article skill and references;
- `scripts/pipeline_runner.py`, `scripts/validate_artifacts.py`, and `scripts/artifact_contract.py` when deterministic behavior is involved;
- existing tests;
- completed/failed `.agents/artifacts/` evidence when relevant;
- `pipeline_learnings.md` and `.agents/knowledge/article-pipeline/` for already-known recurring issues;
- relevant subagent definitions and capability boundaries;
- current first-party Claude Code semantics when version-sensitive.

A missing prose statement is not a finding if the behavior is already adequately enforced elsewhere.

### Place the control correctly

Use this default mapping:

| Failure type | Preferred control |
| --- | --- |
| Always-on article-pipeline invariant | concise `CLAUDE.md` policy |
| Conditional stage/editorial procedure | owning skill/reference |
| Complexity/depth routing error | triage skill or deterministic routing code if objective |
| Product-critical independent perspective | isolated subagent + bounded delegation payload |
| Must-not-see / must-not-do behavior | capability/deterministic restriction, not prose alone |
| Deterministic stage/counter mutation | `scripts/pipeline_runner.py` |
| Persisted artifact consistency | artifact contract / validator / manifest code |
| Human editorial choice | explicit gate + persisted decision artifact |
| Claim-verification policy | fact-check skill + QA; deterministic checks where objective |
| Publication-contract fact | `scripts/validate_artifacts.py` |
| Cross-run calibration | pipeline learning/knowledge only when justified and benchmark-safe |

Use this as a default, not a substitute for evidence.

## Phase 2 — Predeclare the experiment

Write the hypothesis in this form:

> Because `<cause>`, the current article pipeline produces `<failure or waste>`. Changing `<specific mechanism>` should improve `<primary metric>` by at least `<minimum worthwhile effect>` while preserving `<hard guardrails>`.

Choose one primary metric. Use QPR for broad end-to-end changes; use the narrowest direct metric for subsystem changes.

Examples of worthwhile effects:

- eliminate a deterministic state/publication bypass;
- improve QPR by at least 5 percentage points;
- reduce unsupported factual claims by at least 25% without accessibility regression;
- reduce median cost per qualified publish by at least 15% with no meaningful quality regression;
- remove one orchestration layer while preserving QPR within a predeclared non-inferiority margin.

The threshold must exist before candidate results.

## Phase 3 — Freeze the baseline

Record at least:

- git commit and dirty-tree diff;
- Claude Code version;
- model and effort;
- permission mode and relevant command flags;
- project/user/managed settings that affect the run;
- enabled MCP servers/plugins and relevant external tools;
- relevant environment variables;
- auto-memory state and configuration isolation;
- OS/architecture and meaningful CPU/memory limits;
- timeout and network policy;
- evaluator commit/version;
- article brief set/version and target audiences;
- scripted human gate decisions;
- selected depth/route for each brief;
- live-web retrieval window;
- `.agents/knowledge/article-pipeline/` state if learning is enabled.

Baseline and candidate use matched conditions unless a named condition is the experimental variable.

### Fresh processes

Run serious trials in fresh Claude Code processes. Do not validate startup-loaded instruction changes only in the session that edited them.

### Isolate persistent state

Unless memory/learning is the variable, isolate or disable:

- auto memory;
- prior transcripts;
- prior article artifacts;
- benchmark outputs;
- generated files from earlier trials;
- local settings that differ between arms;
- cross-run article knowledge not intentionally shared by both arms.

Keep evaluator data outside the subject-readable environment.

## Phase 4 — Evaluation suites

Do not use one benchmark for everything.

### Deterministic regression suite

Cover objective pipeline behavior, including:

- legal/illegal stage transitions;
- gate and revision counters;
- kill-condition recording;
- word-count synchronization;
- manifest freshness;
- required artifacts by route;
- `COMPLETE`/`REVIEW_REQUIRED` finalization;
- tool-degraded/optional-metadata conditions;
- structurally inspectable capability boundaries.

Every material deterministic bug should become regression coverage after it is fixed.

### Article capability suite

Maintain realistic briefs across:

- SIMPLE, STANDARD, and COMPLEX depth;
- low/high contentiousness;
- evergreen/time-sensitive facts;
- source-rich/source-scarce topics;
- genuine contradictory evidence;
- quantitative/data-heavy topics;
- policy/legislation or acronym-heavy technical topics;
- broad and expert audiences;
- briefs where good research should weaken the initial thesis.

Do not claim a broad pipeline improvement from one topic.

### Epistemic/adversarial integrity suite

Include deliberately diagnostic cases:

- plausible false statistic;
- stale value with an authoritative newer value;
- real citation that does not support the wording;
- social-platform attribution/URL mismatch;
- single-source evidence that should remain qualified;
- contradictory authoritative sources requiring conflict handling;
- low-evidence vector that should stay insufficient;
- OUTDATED/DISPUTED claim that must not appear as settled fact;
- tempting fabricated-citation or fabricated-quote opportunity;
- skeptic delegation that must not receive advocate claims/framing;
- red-team delegation that must not receive the full draft;
- post-draft edit that should invalidate dependent count/manifest state;
- unresolved blocker that must prevent `COMPLETE`.

### Editorial/audience suite

Use blind grading for:

- thesis clarity;
- logical coherence;
- calibration and nuance;
- explanation quality for the declared audience;
- jargon/assumed knowledge;
- redundancy and structural monotony;
- conclusion strength relative to evidence;
- treatment of material counterevidence;
- usefulness/actionability where appropriate;
- publication-ready prose quality.

Do not use the pipeline's own reader, QA, or red-team rating as the sole evidence that the same dimension improved.

### SEO/delivery suite

When relevant, test objective package properties:

- title/meta/slug constraints;
- structured-data validity;
- external-link integrity;
- author-null behavior without fabrication;
- required TODO behavior for unknown site/publisher URLs;
- consistency with the final article.

Do not claim search-ranking improvement without downstream ranking evidence.

### Efficiency suite

Use representative briefs at each affected depth. Measure cost, searches, tokens, tool calls, agent calls, latency, revisions, and human interactions **per qualified publish**.

### Held-out suite

For high-impact experiments:

- keep some briefs outside the candidate-readable checkout;
- keep hidden factual traps/reference facts/grader logic outside subject tool access;
- do not expose prior held-out outputs or grader rationales to the optimizer;
- group near-duplicate topic families in the same partition;
- refresh cases when contamination is suspected.

Held-out briefs should resemble real publication work, not arbitrary puzzles.

## Phase 5 — Validate briefs and graders

A benchmark can be wrong.

Before trusting a brief:

1. make the topic, audience, time horizon, and constraints explicit;
2. confirm both arms can research it with the available tools;
3. identify hidden factual/conflict conditions without exposing them to the subject;
4. verify known good deterministic fixtures pass;
5. verify intentionally bad examples fail the relevant graders;
6. ensure alternate valid theses/structures are not rejected accidentally;
7. distinguish subject failure from source volatility and infrastructure failure;
8. inspect grader edge cases and timeouts.

### Layered article grading

Use separate layers.

**Layer A — deterministic contract**

Use repository code for state, artifact integrity, manifests, required outputs, and publication blockers.

**Layer B — independent claim/citation integrity**

Extract material factual claims from the final draft and verify a complete or predeclared sample. Check:

- cited URL/source identity;
- whether the source supports the wording;
- current value/date for the declared time horizon;
- VERIFIED-UPDATED/DISPUTED/OUTDATED handling;
- calibration of uncertainty.

The pipeline's own `fact_check_report.md` is evidence about its process, not an independent grader of itself.

**Layer C — blind editorial/audience quality**

Use a rubric-driven model grader, calibrated human review, or both. Grade against the declared brief/audience, not generic style preference.

**Layer D — route-specific quality**

Apply only when relevant: adversarial resilience, reader accessibility, SEO package correctness.

Model graders must be blind to baseline/candidate identity and internal pipeline scores when possible. Allow `unknown` or `insufficient evidence` instead of forced confidence.

## Phase 6 — Choose the smallest credible candidate

Before adding machinery, ask:

1. Can conflicting/redundant instructions be deleted?
2. Can an existing deterministic control be tightened?
3. Can the current route be corrected without another stage/agent?
4. Can a conditional procedure move out of always-loaded context?
5. Can native Claude Code behavior replace custom machinery with equal or stronger guarantees?
6. Can a prose prohibition become a capability boundary where it truly must hold?

When multiple candidates are plausible, use an ablation ladder:

1. current baseline;
2. baseline minus the suspected unnecessary mechanism;
3. smallest replacement;
4. larger redesign only if necessary.

This improves causal attribution.

## Phase 7 — Implement without contaminating the experiment

- Preserve unrelated working-tree changes.
- Add/update deterministic coverage for objective behavior changes.
- Do not modify benchmark expectations to fit the candidate.
- Keep the candidate coherent and minimal.
- Record unplanned experimental variables.
- Separate subject and evaluator changes into different commits/experiments when possible.
- Do not write benchmark hints or held-out information into `.agents/knowledge/article-pipeline/`.
- Do not use `.agents/artifacts/` for evaluation bookkeeping.

After the final behavior-changing edit, run deterministic verification required by `CLAUDE.md`. If the claim is that generated articles improve, run the article evaluation appropriate to the experiment class; unit tests cannot prove article quality.

## Phase 8 — Run the comparison

### Match conditions

Baseline and candidate use the same:

- article brief and target audience;
- model/effort and Claude Code version;
- permissions and external tools;
- resource limits and timeout;
- evaluator and network policy;
- initial repository/artifact state;
- memory policy;
- experimental budget.

Freeze or script thesis/approval/postdraft human decisions unless gate behavior itself is the variable. Different human choices can dominate the outcome and destroy causal attribution.

Live web research is time-varying. Interleave baseline/candidate runs tightly, record retrieval timestamps, and where practical retain an evaluator-side source snapshot or reference pack. Do not interpret a source that appeared between arms as an orchestration improvement.

### Repeat trials

Agent behavior is stochastic.

Starting guidance:

- deterministic boundary reproduction: repeat enough to characterize the bypass/fix;
- Class B stochastic changes: at least 3 trials per targeted brief when cost permits;
- Class C/D: normally at least 5 trials per key brief family, with coverage across affected depths and more trials near the decision threshold.

These are starting points, not magic numbers.

### Pair and randomize

Run both arms on the same brief set. Interleave runs and randomize arm order when time-of-day or service-load effects could matter.

For high-impact experiments, include a negative-control brief/fixture when practical. Unexplained movement in an unrelated control can indicate harness drift or contamination.

### Capture every trial

Record:

- brief ID/family, audience, and time horizon;
- arm identity;
- selected depth and route flags;
- scripted/actual gate decisions;
- environment-manifest digest;
- timestamps/retrieval window;
- finalization and validator result;
- final article plus route-relevant delivery artifacts;
- independent factual/citation grader output;
- independent editorial/audience grader output;
- route-specific grader output;
- transcript/trace reference;
- cost/tokens/tool/search/agent counts when available;
- revision and human-intervention counts;
- infrastructure/source-volatility classification;
- failure category.

Never count an infrastructure failure as subject capability evidence without labeling it separately.

## Phase 9 — Grade independently

Prefer this evidence order:

1. final article/delivery artifacts;
2. independent claim/citation verification;
3. deterministic artifact/state validation;
4. blind editorial/audience grading;
5. trace evidence about process/isolation;
6. pipeline-generated QA/red-team/reader/SEO judgments;
7. the subject's own assertion of readiness.

Internal pipeline reports are useful product artifacts, not independent proof that the pipeline improved itself.

### False success

Track two forms.

**Contract false success:** run reaches or claims `COMPLETE` while the authoritative artifact validator says invalid/review-required.

**Qualified false success:** pipeline delivers the article as publication-ready while an independent grader finds a predeclared hard factual/citation/integrity violation.

Do not treat ordinary editorial preference disagreement as false success.

### Evidence freshness

Test whether persisted evidence remains valid after relevant changes:

- current valid evidence;
- stale evidence correctly invalidated;
- stale evidence incorrectly accepted;
- evidence not traceable to actual research, verification, user decision, or command output.

## Phase 10 — Inspect traces and analyze uncertainty

Aggregate scores are insufficient. Inspect:

- every hard-guardrail violation;
- every infrastructure/source-volatility error;
- baseline/candidate disagreements on targeted reproductions;
- representative successes/failures;
- unusually cheap/expensive runs;
- suspiciously perfect held-out performance.

Ask whether the candidate improved the intended mechanism or merely discovered a grader shortcut.

Report at minimum:

- brief/trial counts and depth coverage;
- baseline/candidate primary metric;
- absolute/relative delta where meaningful;
- variation across trials;
- hard-guardrail results;
- infrastructure/source-volatility rate;
- efficiency deltas;
- failure-category shifts;
- meaningful outliers.

For larger experiments, use paired uncertainty analysis appropriate to the metric, such as paired bootstrap intervals or paired binary tests. Pair by brief.

Statistical significance does not replace practical significance. Tiny gains do not justify large orchestration taxes.

## Retention decision

### Accept

Accept only when:

- the targeted failure/waste is demonstrably improved;
- the primary metric meets the predeclared threshold or a deterministic defect is eliminated;
- every hard guardrail passes;
- important regressions are absent;
- efficiency remains inside the declared budget;
- evidence strength matches the experiment class;
- the intervention is the simplest credible mechanism shown to work.

### Reject

Reject when:

- the finding does not reproduce;
- any hard guarantee regresses;
- gains depend on benchmark-specific gaming;
- cost/complexity exceeds the declared tradeoff;
- improvement disappears under matched repeated trials;
- evaluator contamination prevents causal interpretation.

### Inconclusive

Use when:

- effects are within noise;
- trial count is inadequate;
- live-web or environment drift compromises comparability;
- grader validity is uncertain;
- suite results conflict without a predeclared acceptable tradeoff.

The default action for an inconclusive additive change is revert/do not merge.

A simplification may be retained under a predeclared non-inferiority rule if quality stays within tolerance and cost/complexity falls materially.

## Special protocol — simplification and ablation

Complexity must periodically re-earn its existence.

Compare:

> current control plane vs. current control plane minus the mechanism

Useful ablation targets include:

- research summarization passes;
- duplicated persona/rubric text;
- always-loaded instructions;
- extra QA/revision loops;
- red-team or reader-simulation scope on depths where it may not earn its cost;
- custom orchestration duplicated by improved native Claude Code behavior.

Do not casually ablate factuality, human-decision, publication, or adversarial-isolation controls. If one is tested for removal, the non-inferiority suite must directly exercise the failure mode it prevents.

Delete a mechanism when required guarantees remain intact, quality stays within the declared non-inferiority margin, and complexity/context/cost/latency improves materially.

## Special protocol — enforcement changes

When modifying a deterministic or capability boundary:

1. define the protected invariant;
2. enumerate entry and bypass paths;
3. add positive tests for allowed behavior;
4. add negative tests for blocked behavior;
5. test alternate commands/tools/paths;
6. test errors/timeouts;
7. confirm failure is visible to the orchestrator;
8. confirm protected runtime state cannot be silently mutated around the control.

Never weaken a valid factuality, isolation, gate, or publication boundary solely to improve completion rate or lower cost.

## Special protocol — evaluator changes

Evaluator changes can manufacture apparent progress.

When changing a grader, brief, or harness:

- preserve the pre-change evaluator;
- validate known good/bad anchors against old and new versions;
- report candidate performance under both where meaningful;
- separate score movement caused by grader changes from subject changes;
- do not retroactively redefine success because the candidate found an inconvenient path;
- do fix an evaluator when evidence shows it is wrong, ambiguous, brittle, or gameable.

A grader fix and a control-plane improvement are separate effects.

## Special protocol — self-modifying instructions/configuration

When changing startup-loaded behavior such as root `CLAUDE.md`, settings, model routing, or agent definitions:

- the editing session is not a valid candidate trial;
- launch fresh baseline and candidate processes;
- verify which configuration actually loaded;
- isolate personal configuration and prior article memory unless intentionally present in both arms.

## Special protocol — model or Claude Code upgrades

Do not attribute a platform/model upgrade to the control plane.

After a material upgrade:

1. establish a new baseline on unchanged control-plane code;
2. rerun critical deterministic and article capability suites;
3. rerun selected ablations of expensive scaffolding;
4. remove machinery that no longer provides measurable lift;
5. update assumptions about skills, agents, capabilities, tools, or configuration when native semantics changed.

Model upgrades are opportunities to simplify the harness.

## Benchmark integrity

The optimizer must not:

- read held-out expected facts/answers;
- read hidden grader logic when it can be isolated;
- search for benchmark answer keys;
- use prior held-out outputs/rationales as hints;
- modify evaluator data during subject execution;
- treat benchmark identity discovery as article progress;
- weaken a grader merely to raise candidate score.

For serious held-out evaluation:

- subject receives only the article brief, declared audience/gate inputs, and production-equivalent tools;
- hidden briefs/factual traps/reference facts/graders live outside subject-readable storage;
- grading occurs after subject execution;
- evaluator credentials/control files are unavailable to the subject;
- artifacts are copied out after the run rather than exposed in advance.

Treat suspicious benchmark-aware behavior as contamination.

## Failure taxonomy

Classify failures rather than collapsing everything into pass/fail:

- `routing` — wrong depth/stage for the brief;
- `research_coverage` — important vector missed or evidence too weak/narrow;
- `research_independence` — advocate/skeptic anchoring or information-boundary failure;
- `claim_verification` — false/stale/mismatched claim not corrected or calibrated;
- `citation_integrity` — citation missing, fabricated, dead, wrong, or non-supporting;
- `conflict_fidelity` — research conflict or user decision mishandled;
- `drafting` — prose/structure failure despite adequate evidence;
- `qa` — material defect missed or valid prose repeatedly blocked;
- `red_team` — material vulnerability missed or repair worsened article;
- `reader_accessibility` — audience mismatch, jargon, or logical-gap failure;
- `seo_delivery` — objective package defect or fabricated metadata;
- `artifact_state` — state/count/manifest/contract inconsistency;
- `false_success` — contract or qualified false success;
- `orchestration` — delegation/control-flow failure not covered above;
- `context_or_memory` — stale/missing/contaminated context or cross-run knowledge;
- `grader` — evaluation defect;
- `brief_spec` — ambiguous/invalid benchmark brief;
- `source_volatility` — live-web source changed materially between matched runs;
- `infrastructure` — service/network/sandbox/harness failure;
- `timeout` — budget exhausted without a more specific cause;
- `contamination` — held-out/evaluator information leaked to the subject.

Track failure-distribution shifts as well as aggregate QPR.

## Complexity accounting

Every additive candidate declares its complexity cost. Useful proxies:

- always-loaded instruction lines/tokens;
- active agents;
- skills/references loaded by the affected route;
- stages, gates, counters, and transitions;
- deterministic branches;
- schemas/persisted objects;
- dependencies;
- regression tests needed to defend the mechanism.

These are not a universal complexity score. They expose hidden orchestration tax.

## Continuous evaluation maintenance

After an accepted fix:

- add the original failure as deterministic regression or benchmark coverage when practical;
- add a nearby negative/alternate case;
- preserve the causal reproduction;
- retire redundant cases only when equivalent coverage remains.

When capability cases saturate:

- promote mature cases to regression/anchors;
- add harder realistic briefs;
- expand contentiousness, source scarcity, freshness, audience, and domain coverage;
- do not create arbitrary obscurity solely for difficulty.

Periodically audit the suite for ambiguity, leakage, stale assumptions, grader brittleness, duplicates, missing negative cases, and mismatch with real article-production work.

## Comparator set

Use the smallest set that answers the causal question:

- `current` — current committed article control plane;
- `candidate` — proposed change;
- `ablation` — current minus the mechanism under question;
- `native` — simpler native Claude Code mechanism when relevant;
- `bare` — reduced article pipeline when useful for measuring total orchestration lift.

Do not use a dramatic but irrelevant comparator. Comparators must answer a real design question.

## Required closeout

Every completed experiment reports:

### Finding

What concrete article-pipeline failure mode or wasted resource was observed?

### Baseline

What happened before the change, under what environment, and with what evidence level?

### Hypothesis

Why should the candidate affect the chosen metric?

### Candidate

What changed, and why was it the smallest credible intervention?

### Evaluation

What briefs, depths, gate decisions, graders, trials, environment controls, comparators, and budgets were used?

### Results

Report QPR or the declared primary metric, hard guardrails, efficiency, failure categories, and uncertainty.

### Trace audit

What did representative successes/failures show? Was there grader gaming, contamination, source volatility, or another explanation?

### Decision

`accepted`, `rejected`, or `inconclusive`.

### Simplicity

What machinery was added, removed, or made unnecessary?

### Guarantees

Which factual/editorial/control-plane guarantees remain intact, and what evidence demonstrates that?

Finish with:

> What measurable article-pipeline property is better than the baseline, what factual/editorial and control-plane guarantees remain intact, what did the improvement cost, and why is this the simplest mechanism that achieved the result?

## Minimum acceptance checklist

- [ ] The failure/waste was concretely reproduced or benchmarked.
- [ ] Existing behavior and prior pipeline learnings were inspected before claiming novelty.
- [ ] Experiment class was declared.
- [ ] Hypothesis was written before implementation.
- [ ] One primary metric was declared.
- [ ] Minimum worthwhile effect/non-inferiority margin was declared.
- [ ] Hard guardrails were declared.
- [ ] Baseline environment, article briefs, gate decisions, and learning state were captured.
- [ ] Baseline/candidate ran in fresh matched processes when stochastic behavior mattered.
- [ ] Persistent state and benchmark contamination were controlled.
- [ ] Deterministic regression coverage exists for objective changed behavior.
- [ ] Article capability coverage has headroom when a quality claim is made.
- [ ] Adversarial/bypass cases were tested when relevant.
- [ ] Trials were repeated for stochastic behavior.
- [ ] Source volatility/infrastructure failures were separated from subject failures.
- [ ] Final article/delivery artifacts and independent grader evidence were captured.
- [ ] Representative traces were inspected.
- [ ] Efficiency deltas were measured for Class C/D changes.
- [ ] Held-out validation was used for high-impact changes when feasible.
- [ ] Evaluator changes were not silently conflated with subject improvements.
- [ ] Deterministic repository verification passed after the final edit.
- [ ] Final diff contains no unintended article artifacts or benchmark leakage.
- [ ] Result was classified accepted/rejected/inconclusive.
- [ ] Accepted fixes produced durable regression/benchmark coverage when practical.
- [ ] Final report answers the required closeout question.

## Default posture

The article control plane should become stronger by producing better qualified articles more reliably, not by accumulating orchestration.

Every mechanism is provisional.

Every guarantee belongs at the strongest appropriate control layer.

Every important article-pipeline failure should become reproducible or benchmarkable.

Every retained change should improve a measured article/control outcome or remove cost without meaningful factual, editorial, or integrity regression.

Every major model/platform improvement should trigger fresh ablation pressure against old scaffolding.

When evidence does not distinguish a more complex design from a simpler one, choose the simpler design.
