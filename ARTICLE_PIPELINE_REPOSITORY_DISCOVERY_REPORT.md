# Article Pipeline Repository Discovery Report

**Repository:** `JackSmack1971/article-pipeline`  
**Branch inspected:** `main`  
**Code snapshot inspected:** `4277aabd8380e4b79ecd831763743f849585a2af`  
**Discovery date:** 2026-08-07 (America/Detroit; the inspected head commit is dated 2026-08-08 UTC)  
**Mode:** Discovery / architecture / behavior analysis  
**Change policy for this pass:** No source, configuration, schema, test, runtime-artifact, or documentation file was changed. This discovery report is the sole file intentionally overwritten.  
**Execution note:** Analysis was performed by direct repository/API inspection. A local checkout was not available in the analysis environment, so this pass did not independently execute `make verify`, the artifact validator, or the QPR experiment harness. CI is configured in the repository, but a completed CI run for the inspected head was not independently observed during this pass.

---

## Executive Summary

`article-pipeline` is not a conventional Python application. It is a **Claude Code-native orchestration repository for producing research-backed long-form articles**, surrounded by a **deterministic enforcement layer** and a **control-plane evaluation laboratory**.

The cleanest mental model is that three related systems live in the same repository:

1. **Article production system** — a Claude Code session routes an article request through complexity triage, adversarial research, synthesis, fact-checking, human approval, section-by-section drafting, QA, optional red-team challenge, audience simulation, SEO packaging, and cross-run learning.
2. **Control/enforcement system** — Python, shell hooks, JSON Schema, manifests, tests, and CI enforce objective invariants that should not depend on the model remembering a rule correctly.
3. **Evaluation system** — matched baseline/candidate experiments, independent factual/citation grading, blind editorial grading, and Qualified Publish Rate (QPR) test whether changes to the control plane actually improve outcomes rather than merely making prompts look better.

The repository's central architectural doctrine is explicit and consistent across its newer implementation:

> **Use model judgment where judgment is required; use executable controls where a guarantee must hold.**

That explains most of the repo's unusual design choices: narrow subagent capabilities, named handoff artifacts, immutable-ish source-of-truth conventions, state transition code, manifest hashing, per-write rollback hooks, schema validation, human editorial checkpoints, and an independent evaluation harness.

The current repository is substantially more mature than the earlier discovery report it replaces. Since that report, the project has added or hardened:

- committed hook registration for clean-clone reproducibility;
- a root README, requirements file, Makefile, and canonical verification command;
- capability-isolated advocate, skeptic, and red-team subagents;
- deterministic gate/KC/revision counters;
- state schema versioning and migration;
- machine-checkable JSON Schemas;
- canonical word-count and E-E-A-T reconciliation during finalization;
- hook smoke tests and CI merge-gating checks;
- an independent article/control-plane evaluation harness;
- a recent cleanup pass over all project skills.

However, the migration is not complete. The most important current-state finding is **contract drift between the newest executable implementation and several still-active instructions**. The repo itself says executable behavior outranks prose, and that rule matters here. In particular:

- root `CLAUDE.md` claims `scripts/workflow.py`, `orchestration/workflow.json`, `.workflow/`, and a project `workflow` skill are authoritative, but those mechanisms are not present on the inspected `main` branch;
- the active `article-research-dialectic` skill still checks legacy `pipeline_state.json.gates`, while schema v2 uses `gate_history` and the runner explicitly rejects a `gates` key;
- the active multi-agent pipeline still contains conditional references to an `article-pipeline-runner` and to `pipeline_state.json.telemetry`, neither of which matches the current v2 implementation;
- the triage skill describes a richer config object as “all fields required,” while the machine schema requires only a smaller core and intentionally accepts older/leaner instances;
- direct writes to `pipeline_state.json` are blocked, but not every descriptive state field mentioned by the prose has a corresponding `pipeline_runner.py` mutation command;
- README dependency prose says the scripts are standard-library-only even though `validate_schemas.py` now depends on `jsonschema` and `requirements.txt` correctly declares it.

So the repo is best described as **a strong hybrid control plane with a newer deterministic core and a small but meaningful layer of stale orchestration prose still wrapped around it**.

The committed current article fixture under `.agents/artifacts/` is also informative. It records a completed-through-delivery **COMPLEX** article run with adversarial research, fact-checking, QA, red team, reader simulation, SEO, and learning. The run is deliberately in `REVIEW_REQUIRED`, not `COMPLETE`, because its structured E-E-A-T state is `FAIL`: the system has no real author identity/credential to place in the byline and refuses to fabricate one. That is not primarily a software crash. It demonstrates a deliberate editorial boundary: **the system will leave a run blocked when a real-world publication fact must come from a human/publisher.**

---

# 1. What This Repository Is

## 1.1 A Claude Code orchestration repository

The repository is designed to be opened and operated inside Claude Code. There is no web server, daemon, REST API, installable application package, or top-level autonomous scheduler that independently generates an article from start to finish.

The semantic orchestrator is the **main Claude Code session**. It reads project instructions and skills, activates specialist workflows, delegates bounded jobs, interprets research, presents editorial gates, and decides when semantic work is ready for the next phase.

Python and shell are not the primary article-writing engine. They are the **contract and enforcement substrate** around the model-driven workflow.

This division is fundamental:

- **Claude/skills:** interpretation, research strategy, synthesis, drafting, editorial judgment, reader simulation, SEO reasoning.
- **Python/shell/hooks/schemas/tests:** stage legality, critical counters, derived-value reconciliation, artifact integrity, state write protection, structural validation, rollback, schema conformance, and regression checking.

## 1.2 An artifact-oriented workflow rather than a chat-only workflow

The system deliberately externalizes important handoffs into named files under `.agents/artifacts/` rather than relying on the model's conversation history as implicit state.

Examples include:

- `pipeline_config.json`
- `pipeline_state.json`
- `advocate_context.md`
- `skeptic_evidence.md`
- `research_context.md`
- `research_context_summary.md`
- `article_spec.md`
- `conflict_register.md`
- `fact_check_report.md`
- `dispute_register.md`
- `claims_for_drafting.md`
- `conflict_decisions.json`
- `article_draft.md`
- `audit_log.md`
- `audit_report.md`
- `red_team_report.md`
- `reader_questions.md`
- `seo_package.md`
- `pipeline_metadata.md`
- `pipeline_learnings.md`
- `artifact_manifest.json`

The artifact model serves several purposes at once:

1. makes phase boundaries inspectable;
2. gives downstream roles a bounded input surface;
3. reduces hidden context dependence;
4. enables deterministic validation and hashing;
5. makes interrupted sessions resumable;
6. creates evidence for later debugging and evaluation;
7. creates a place for cross-run learning that is explicit rather than purely conversational.

## 1.3 A control-plane development laboratory

The repo is also the development environment for its own orchestration strategy.

It contains:

- `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` — experimental methodology for changing the control plane;
- `evals/article_pipeline/` — visible development corpus;
- `scripts/evals/` — baseline/candidate runner plus independent graders;
- `diagnostics/` — historical forensic/design write-ups;
- `blueprint.md` — a historical proposal document;
- `docs-control-plane/claude-code-docs/` — a captured Claude Code documentation/reference corpus;
- meta-skills such as `writing-great-skills`, `writing-great-workflows`, and `writing-great-claude-subagents` used to reason about the quality of the control plane itself.

This means the repository is both **the thing being used** and **the thing being experimentally improved**.

## 1.4 Licensing

The repository is MIT licensed, copyright 2026 JackSmack1971.

---

# 2. Who Participates in the System

“Who” in this repo is not a single agent. There are several distinct actors with deliberately different authority.

## 2.1 The human operator / publisher

The human remains the authority for decisions that are editorial, preference-sensitive, or impossible to infer truthfully.

Examples include:

- confirming a MEDIUM-confidence thesis;
- approving/revising the article specification;
- deciding how genuine evidence conflicts should be presented;
- deciding whether to address or acknowledge a red-team objection;
- deciding whether to polish reader-comprehension gaps;
- supplying an actual author name/credential/affiliation;
- supplying publication URLs or publisher metadata that the system must not invent.

This human role is intentional. The repo does not treat automation percentage as the primary objective; it treats correctness and observable publishability as more important.

## 2.2 The main Claude Code session

The main session is the semantic orchestrator.

It is responsible for:

- selecting/activating the article pipeline;
- running triage;
- invoking skills in sequence;
- delegating isolated research/adversarial tasks;
- synthesizing artifacts;
- managing semantic gate conversations;
- drafting and revising prose;
- invoking deterministic scripts at prescribed checkpoints;
- carrying the workflow from brief to delivery.

This is why there is no conventional `main.py` that performs the entire job.

## 2.3 Capability-isolated subagents

Three custom subagents under `.claude/agents/` are especially important because their **tool capabilities enforce information boundaries**.

### `article-advocate`

Role: collect the strongest evidence supporting the thesis.

Tools:

- `WebSearch`
- `Write`

It has no `Read` tool. Therefore it cannot inspect the current pipeline's prior artifacts unless information is explicitly passed in its delegation prompt.

It writes `advocate_context.md` and ends with a flat Source URL Index.

### `article-skeptic`

Role: find evidence that refutes, narrows, complicates, or offers alternatives to the thesis.

Tools:

- `WebSearch`
- `Write`

It also has no `Read` tool. It may receive only the advocate's URL index, not the advocate's extracted claims or framing. This reduces redundant retrieval without intentionally contaminating the skeptic with the advocate's argument.

It writes `skeptic_evidence.md`.

### `article-red-team`

Role: attack the finished thesis/conclusion after drafting on logical, empirical, and framing grounds.

Tool:

- `WebSearch`

It has neither `Read` nor `Write`. The parent passes only the thesis and conclusion. The red team therefore cannot simply inspect the full article and anchor its counterargument on the article's own supporting structure.

It returns a report to the parent; the parent persists it.

### Why this matters

This is one of the clearest examples of the repo's “guidance vs enforcement” doctrine.

“Do not read the advocate's claims” would be a weak prompt-only rule if the skeptic had filesystem read access. Giving the skeptic no `Read` capability turns the desired independence into a real architectural boundary within the Claude Code tool model.

## 2.4 In-context specialist roles

Other functions remain in the main session because they legitimately need broad access to shared artifacts:

- complexity triage;
- synthesizer;
- summarizer/compressor;
- fact-checker;
- engineer/drafter;
- QA auditor;
- reader simulator;
- SEO optimizer.

The repo does not isolate every role simply for architectural symmetry. It uses subagents where isolation is expected to produce a concrete benefit, especially adversarial independence.

## 2.5 Deterministic authorities

Several non-model components act as authorities over objective rules:

- `scripts/pipeline_runner.py`
- `scripts/artifact_contract.py`
- `scripts/validate_artifacts.py`
- `scripts/validate_schemas.py`
- `scripts/migrate_pipeline_state.py`
- `scripts/write_artifact_manifest.py`
- `scripts/state_enforcer.sh`
- `scripts/enforce_artifact_contract.sh`
- `schemas/*.schema.json`
- `tests/*`
- `.github/workflows/ci.yml`

These components do not decide whether an argument is persuasive. They decide things like whether a transition is legal, whether a revision limit has been exceeded, whether a state shape is valid, whether an artifact changed after it was hashed, or whether derived word-count values agree.

## 2.6 Independent evaluators

The control-plane evaluation system separates the subject pipeline from the graders.

Actors include:

- a baseline control plane;
- a candidate control plane;
- a factual/citation grader with web access;
- a blind editorial grader without tools;
- deterministic qualification/aggregation logic in the experiment runner.

This is designed to prevent a candidate control plane from declaring its own improvement successful based solely on its own changed instructions.

---

# 3. What the Repository Does

At the highest level, it converts a research-heavy article brief into a **publishability package**, not merely a prose document.

A successful run can produce:

1. a routed research plan;
2. supporting and disconfirming evidence;
3. a conflict map;
4. a fact-checked claim table;
5. human conflict decisions;
6. an article specification;
7. a drafted article;
8. inline and holistic QA evidence;
9. an adversarial post-draft challenge;
10. an audience-comprehension report;
11. an SEO/structured-data package;
12. pipeline metadata and learning;
13. machine state and artifact integrity evidence.

The goal is not “write something fluent.” The goal is closer to:

> Produce a research-backed article whose claims, conflicts, revisions, editorial decisions, and publishability status can be inspected after the fact.

---

# 4. The End-to-End Article Flow

The README summarizes the intended live lifecycle as:

`TRIAGE → RESEARCH → FACTCHECK → APPROVAL → DRAFT → POSTDRAFT → SEO → LEARNING → COMPLETE`

The detailed multi-agent skill expands this into the following operational sequence.

## 4.1 Step 0 — Complexity triage and learning ingestion

`article-complexity-triage` scores the brief across three dimensions:

- Novelty — 35%
- Contentiousness — 40%
- Scope — 25%

The weighted composite routes the run:

| Composite | Depth | Dialectic | Fact-check | Red team | SEO | Base budget |
|---:|---|---|---|---|---|---:|
| 1.0–2.4 | SIMPLE | No | No | No | Yes | 24,000 |
| 2.5–3.7 | STANDARD | Yes | Yes | No | Yes | 32,000 |
| 3.8–5.0 | COMPLEX | Yes | Yes | Yes | Yes | 48,000 |

Triage also:

- reads `pipeline_learnings.md` for accumulated calibration;
- scans the brief for suspicious unsupported named claims, quotes, or financial/adoption assertions;
- extracts/formulates the thesis;
- requires explicit confirmation when thesis confidence is MEDIUM;
- records tool availability;
- writes `pipeline_config.json`.

### Why triage exists

The repo explicitly wants the **minimum viable depth**. Full adversarial research and red-team work are expensive. The triage stage is a cost/quality router intended to avoid spending COMPLEX-level resources on simple topics while avoiding under-research on disputed or fast-moving topics.

## 4.2 Step 1 — Research dialectic

For STANDARD and COMPLEX routes, research is split into two adversarial streams:

- advocate: strongest supporting evidence;
- skeptic: strongest disconfirming or limiting evidence.

They receive the same research vectors but are isolated from one another's claim framing.

The main-session synthesizer then merges the streams and classifies evidence relationships:

- `[CORROBORATED]`
- `[UNCONTESTED]`
- `[CONFLICTING]`
- `[WEAKENED]`
- `[INSUFFICIENT]`

The synthesizer writes:

- `research_context.md`
- `article_spec.md`
- `conflict_register.md`

For SIMPLE routes, the expensive dual-stream adversarial pass is skipped and research is unified.

### Research kill conditions

Two notable checks are surfaced at synthesis:

- **KC-3:** if one source supplies more than 40% of extracted claims, halt;
- **KC-6:** if more than 50% of research vectors are insufficient, halt.

The result is supposed to prevent an article from progressing when its evidence base is either too concentrated or too thin.

## 4.3 Step 1.25 — Research compression

The system writes `research_context_summary.md` as a compressed default downstream input.

This is a context-engineering optimization. Later roles should not repeatedly reload the entire research document when they only need:

- thesis;
- confirmed claims;
- conflicts;
- gaps;
- source inventory.

Full evidence is loaded on demand for specific claim traces.

The skill explicitly frames this as a 60–80% context-consumption reduction for complex runs.

## 4.4 Step 1.5 — Fact-check gate

When fact-checking is enabled, `article-fact-checker` treats HIGH/MEDIUM research claims as untrusted until independently rechecked through targeted web search.

It assigns verdicts:

- VERIFIED
- VERIFIED-UPDATED
- UNVERIFIABLE
- DISPUTED
- OUTDATED

It writes:

- `fact_check_report.md`
- `dispute_register.md` when needed.

The purpose is to separate “research found this” from “the pipeline performed a second verification pass before drafting.”

## 4.5 Step 1.75 — Post-fact-check compression

`claims_for_drafting.md` turns the fact-check output into a compact drafting lookup table.

Important fields include:

- claim ID;
- final/current value;
- source URL;
- section;
- status;
- posterior confidence.

Posterior confidence then controls how the draft should phrase a claim:

- HIGH — state directly;
- MEDIUM — qualify/attribute;
- LOW / unverifiable — mandatory editorial caveat;
- LOW / disputed — include only under an approved conflict decision.

This is an attempt to propagate epistemic uncertainty into prose rather than losing it between research and writing.

## 4.6 Step 1.8 — Visual candidate handling

Sections containing quantitative comparisons or sequential processes may be marked `[VIZ-CANDIDATE]`.

If code execution is unavailable, the workflow intentionally degrades to image placeholders and records the degraded tool condition.

If code execution is available, a chart-generation script under the pipeline skill can render charts.

This is a good example of **graceful degradation**: missing chart tooling should not silently pretend a chart was generated, but it also should not necessarily block an otherwise valid article.

## 4.7 Step 2 — Approval gate

Before drafting, the human is shown the specification and conflicts.

Typical decisions:

- approved;
- revise;
- abort;
- conflict-specific handling such as neutral presentation, author position, or unresolved presentation.

`conflict_decisions.json` becomes the drafting authority for how conflicts are represented. Conversation text is intentionally not the authoritative source.

Critical counters are handled through `pipeline_runner.py`:

- gate history;
- expedite count;
- revision counts;
- maximum revision enforcement.

## 4.8 Step 3 — Streamed drafting and inline QA

The article is drafted section by section.

The engineer reads compact artifacts first:

- `article_spec.md`
- `research_context_summary.md`
- `claims_for_drafting.md`
- `conflict_decisions.json`

The full research/fact-check documents are supposed to be used only when a claim needs tracing.

After each section:

1. engineer writes section;
2. QA audits it;
3. verdict is recorded;
4. BLOCKED sections are revised under limits;
5. cumulative utilization is checked for a mid-draft halt condition.

The QA layer checks:

- claim traceability;
- updated fact-check values;
- confidence qualifiers;
- citation integrity;
- approved conflict handling;
- structural/style constraints;
- visual placeholders where required.

STANDARD/COMPLEX runs then receive holistic QA; SIMPLE runs use a reduced mini-audit.

### Important precedence rule

The newer skills explicitly say:

> `claims_for_drafting.md` supersedes stale claim-exclusion notes in `article_spec.md`.

This rule exists because the spec is written before fact-checking. Fact-checking may later upgrade or alter a claim. The project has chosen not to automatically back-patch the spec and instead gives the post-fact-check claim table higher authority during drafting.

## 4.9 Step 4 — Red team (COMPLEX)

The isolated red-team subagent receives only thesis + conclusion.

It searches for:

- logical weaknesses;
- empirical counter-evidence;
- framing vulnerabilities.

The human can accept, address, or acknowledge the resulting objection.

If the draft changes, word count is re-synchronized through the deterministic runner.

## 4.10 Step 5 — Reader simulation

The reader simulator evaluates the draft from the declared target audience's perspective.

It looks for:

- jargon;
- assumed knowledge;
- logical leaps;
- evidence opacity;
- engagement friction.

If the human chooses a polish pass, only the highest-priority gaps are targeted, then modified sections are re-audited and the word count is synchronized again.

This stage exists because factual QA and reader comprehension are not the same problem. The committed learning artifact explicitly says the prior run found non-overlapping issues in QA, red team, and reader simulation.

## 4.11 Step 6 / 6.5 — Delivery and SEO

The draft is presented, then the SEO optimizer can generate:

- title variants;
- meta description;
- URL slug;
- keyword analysis;
- JSON-LD Article data;
- FAQPage data when applicable;
- BreadcrumbList data;
- internal-link suggestions;
- on-page checklist;
- external-link audit;
- E-E-A-T assessment.

The SEO skill deliberately emits `[TODO:]` values instead of inventing publisher/site URLs.

## 4.12 Step 7 — Cross-run learning and finalization

The run writes structured observations into `pipeline_learnings.md`.

The next run can consume tags such as:

- `[CALIBRATION]`
- `[THRESHOLD_ADJUST]`
- `[GATE_HYGIENE]`

This creates a bounded feedback loop across runs.

Before terminal completion, `pipeline_runner.py finalize`:

1. recomputes canonical draft word count;
2. reconciles state, metadata, and SEO word-count representations;
3. extracts/persists structured E-E-A-T status;
4. regenerates the artifact manifest;
5. places state in `REVIEW_REQUIRED` while validating;
6. promotes to `COMPLETE` only if there are no errors or blockers;
7. revalidates the final state.

That function is the current deterministic completion gate.

---

# 5. How the Deterministic Control Plane Works

## 5.1 `pipeline_runner.py` — state and critical-counter authority

This script defines the legal state transition graph:

- TRIAGE → RESEARCH
- RESEARCH → FACTCHECK or APPROVAL
- FACTCHECK → APPROVAL
- APPROVAL → DRAFT
- DRAFT → POSTDRAFT or SEO
- POSTDRAFT → SEO
- SEO → LEARNING
- LEARNING → COMPLETE
- REVIEW_REQUIRED → selected repair stages

Key properties:

- `advance()` rejects illegal transitions;
- `advance(..., COMPLETE)` is explicitly forbidden;
- only `finalize()` is allowed to produce `COMPLETE`;
- state writes stamp schema version 2;
- legacy `gates` / `telemetry` state shapes are refused until migrated;
- revision cycle 4 is refused;
- the third consecutive BLOCKED audit produces `HALT_REQUIRED`;
- kill-condition HALTs are recorded;
- gate expedites are counted;
- canonical word counts are re-derived rather than trusted;
- finalization is designed to be idempotent for unchanged source artifacts.

This is a meaningful strengthening over a pure prompt workflow because these objective limits no longer depend solely on the model performing arithmetic correctly in a long context.

## 5.2 `artifact_contract.py` — shared deterministic definitions

This module centralizes rules that multiple components must agree on:

- canonical Markdown word counting;
- SEO word-count extraction;
- TODO detection;
- E-E-A-T status parsing;
- SHA-256/byte-size artifact hashing;
- manifest integrity verification.

Centralizing these rules prevents multiple validators/writers from quietly implementing different versions of “word count” or “artifact changed.”

## 5.3 `validate_artifacts.py` — semantic persisted-run validator

This validator is read-only.

It checks, among other things:

- required core artifacts;
- route-dependent required artifacts;
- state-referenced artifact paths;
- word-count agreement across draft/state/metadata/SEO;
- manifest integrity;
- structured E-E-A-T consistency;
- unresolved placeholders;
- TODO metadata conditions;
- whether the current stage is genuinely publishable.

Its statuses are meaningful:

- `PUBLISHABLE`
- `REVIEW_REQUIRED`
- `INVALID`
- or a nonterminal stage name when the run is structurally valid but in progress.

Importantly, `REVIEW_REQUIRED` is a first-class state. The design recognizes that some blockers require editorial/human resolution rather than forcing either success or crash.

## 5.4 JSON Schema validation

Four root schemas currently cover:

- `pipeline_config.json`
- `pipeline_state.json`
- `conflict_decisions.json`
- `artifact_manifest.json`

`validate_schemas.py` performs two distinct checks:

1. meta-validates each schema as Draft 2020-12;
2. validates any corresponding committed artifact instance that exists.

This is intentionally separate from the runtime artifact validator. The schema validator answers “does this JSON shape conform?” while the artifact validator answers “does this run make semantic/operational sense?”

This separation is architecturally sensible, but it also means session-start enforcement does not itself run the full JSON Schema validator; the schema check is part of `make verify`/CI rather than every article-session resume.

## 5.5 State migration

The current canonical state shape is schema version 2.

Legacy state nested important information under:

- `gates`
- `telemetry`

Version 2 flattens critical fields such as:

- `gate_history`
- `revision_cycles`
- `kc_events`
- `gate_expedite_count`
- `consecutive_blocked_audits`

The runner refuses the legacy form and requires explicit migration.

This is an important maturity signal: the repo no longer silently accepts multiple incompatible definitions of valid machine state.

## 5.6 Artifact manifest

`artifact_manifest.json` records SHA-256 and byte size for every file under the artifact root except the manifest itself.

The validator detects:

- missing recorded artifacts;
- hash/size changes;
- untracked artifacts absent from the manifest.

The manifest is therefore a snapshot/integrity contract for the current run.

## 5.7 Hook enforcement

Committed `.claude/settings.json` activates the enforcement layer on a clean clone.

### SessionStart

Runs `state_enforcer.sh session-start`.

It invokes the artifact validator and:

- hard-halts on INVALID/corrupt contract state;
- surfaces REVIEW_REQUIRED blockers;
- injects resume-stage context when healthy.

### PreToolUse — Write/Edit

Runs `enforce_artifact_contract.sh pre-write`, which delegates to the state enforcer.

Behavior includes:

- deny direct Write/Edit of `pipeline_state.json`;
- back up existing Markdown/JSON artifacts before writes.

### PreToolUse — Bash

If the command text references `pipeline_state.json`, the hook only allows a single unchained invocation of `python[3] scripts/pipeline_runner.py ...`.

The script explicitly describes this as a **heuristic command-text guard**, not a filesystem security boundary.

### PostToolUse — Write/Edit

For Markdown artifacts, the hook:

- rejects empty files;
- rejects NUL/binary-looking corruption;
- detects severe truncation;
- runs targeted contract validation with manifest hashing temporarily skipped;
- rolls back an implicated write to the most recent backup;
- removes a newly created invalid file if no backup exists.

This provides transaction-like protection against accidental/corrupt artifact writes in the normal Claude Code tool path.

### Important scope boundary

This is not an OS sandbox. It protects the intended Claude Code hook path. The repo's own comments acknowledge residual bypass risk.

Also, post-write structural rollback currently gates Markdown artifacts. Pre-write backs up Markdown and JSON artifacts, but the post-write branch exits unless the edited artifact ends in `.md` (apart from special handling for `pipeline_state.json`). Consequently, arbitrary non-state JSON artifact writes do not receive the same immediate post-write rollback path, although core JSON instances are covered by schema checks during verification/CI.

---

# 6. Verification and CI

## 6.1 Local verification

`make verify` delegates to `scripts/verify.sh`.

The current verification sequence checks:

1. shell syntax for hook scripts;
2. `.claude/settings.json` JSON validity;
3. JSON Schema contracts and present artifact instances;
4. the Python test suite.

The tests include coverage for:

- pipeline transitions;
- completion exclusivity;
- state migration;
- word-count reconciliation;
- E-E-A-T finalization behavior;
- revision/gate/KC counters;
- manifest/integrity behavior;
- hook-enforcer smoke behavior;
- evaluator code;
- selected documentation/contract invariants.

`verify.sh` intentionally does not simply fail because the current article run is `REVIEW_REQUIRED`. Checkout correctness and current article publishability are treated as different questions.

## 6.2 CI

`.github/workflows/ci.yml` runs deterministic contract checks on pushes to `main` and pull requests.

It includes:

- Python 3.11 setup;
- dependencies;
- hook syntax;
- settings JSON validation;
- schema validation;
- pipeline/migration/doc-contract tests;
- canonical artifact fixture and manifest tests;
- hook-enforcer smoke tests;
- evaluation-code unit tests.

It intentionally excludes live QPR baseline/candidate article experiments because those require model budget, network research, and independent graders and are not appropriate for every commit.

During this discovery pass I verified the workflow definition, but I did not independently observe a completed CI run associated with the inspected head. Therefore this report treats the CI checks as **configured enforcement**, not as proof that the current head has already passed a specific run.

---

# 7. The Evaluation Harness

The evaluation subsystem is one of the features that most distinguishes this repository from a normal prompt collection.

## 7.1 Matched baseline/candidate subject runs

`scripts/evals/qpr_runner.py` executes the same brief against baseline and candidate Git refs in fresh detached worktrees.

Pair order is randomized.

The intent is to answer:

> Did this control-plane change actually improve article outcomes under matched conditions?

rather than:

> Does the new prompt look more sophisticated?

## 7.2 Independent factual/citation grader

`claim_citation_grader.py` runs separately from the subject pipeline in bare Claude mode with web tools.

It independently checks material claims and practical citation URLs rather than trusting the subject pipeline's own fact-check artifacts.

## 7.3 Blind editorial grader

`editorial_grader.py` receives the final article plus brief/audience and is blind to baseline/candidate identity.

It runs without web tools because its job is editorial quality rather than external fact verification.

## 7.4 Qualified Publish Rate

A trial qualifies only if multiple independent requirements pass.

Default thresholds include:

- artifact status `PUBLISHABLE`;
- material factual-claim precision ≥ 0.95;
- citation support rate ≥ 0.95;
- zero missing material citations;
- editorial mean ≥ 4.0/5;
- each editorial dimension ≥ 3/5;
- no mismatched/likely fabricated citation;
- no outdated/contradicted claim presented as current fact;
- no fatal editorial issue;
- advocate/skeptic/red-team capability isolation remains intact;
- no undeclared human rescue;
- acceptable routing depth for the brief.

The runner reports both normal QPR and operational QPR so infrastructure failure cannot simply disappear from the denominator.

## 7.5 Evaluation isolation model

Subject worktrees are scrubbed of evaluator content and prior run artifacts, and graders run separately in bare mode.

The repo is explicit that this is strong development isolation, **not a security sandbox**. Held-out confirmation should place hidden corpus/evaluator materials outside the repository and use stronger OS/container boundaries.

## 7.6 Why the evaluator exists

The control-plane improvement protocol treats changes as falsifiable experiments.

Its evidence ladder ranges from:

- E0 — assertion;
- E1 — anecdote;
- E2 — reproduction;
- E3 — controlled comparison;
- E4 — held-out validation;
- E5 — field validation.

Cross-cutting behavioral control-plane changes are expected to reach controlled comparison, and high-impact enforcement/evaluator changes should use held-out validation when feasible.

This is the repository's answer to a common agent-system failure mode: increasing orchestration complexity without evidence that it improves real outcomes.

---

# 8. Why the Repository Is Designed This Way

## 8.1 To separate judgment from guarantees

The main model is good at tasks such as:

- interpreting ambiguous article goals;
- selecting research vectors;
- synthesizing evidence;
- recognizing argumentative nuance;
- writing prose;
- identifying reader confusion.

It is a poor authority for guarantees such as:

- “never enter COMPLETE from DRAFT”;
- “do not exceed three gate revisions”;
- “these four word-count representations must agree”;
- “this artifact has not changed since manifest generation”;
- “this JSON matches the agreed schema.”

The repo therefore moves these rules into code when feasible.

## 8.2 To reduce confirmation bias and anchoring

Advocate/skeptic separation forces one stream to search aggressively for support and another to search aggressively for disconfirmation.

The red team is denied the article body to reduce anchoring on the author's supporting argument.

This is an epistemic design choice, not merely a multi-agent novelty.

## 8.3 To preserve evidence uncertainty through drafting

The pipeline does not want all researched claims to become equally confident prose.

It carries:

- source tiers;
- research classifications;
- fact-check verdicts;
- posterior confidence;
- dispute handling;
- caveat rules.

into the drafting phase.

The purpose is to prevent a common handoff failure where uncertainty documented during research disappears when prose is generated.

## 8.4 To make human judgment explicit

Human gates are used where there is no objectively correct automated answer.

The current author-byline blocker is a concrete example. The pipeline can detect that author expertise metadata is missing, but it cannot truthfully invent an author identity.

Therefore it leaves the run review-required.

## 8.5 To make interrupted or long runs resumable

Named artifacts, pipeline state, validation at SessionStart, and cross-run knowledge make the workflow less dependent on one uninterrupted context window.

COMPLEX runs can be explicitly planned as multi-session work.

## 8.6 To reduce context consumption

Summary artifacts such as `research_context_summary.md` and `claims_for_drafting.md` are deliberate compression layers.

The system attempts to avoid repeatedly feeding full evidence documents to every downstream role.

## 8.7 To make failures inspectable

The system writes:

- conflict registers;
- dispute registers;
- audit logs;
- red-team reports;
- reader questions;
- telemetry-like state fields;
- manifest hashes;
- evaluation records.

This produces a forensic trail for understanding why a run failed or why a control-plane change helped.

## 8.8 To prevent “agentic complexity” from becoming its own goal

The control-plane improvement protocol explicitly says the objective is not more agents, more states, more hooks, or more abstraction.

Deletion and simplification are valid candidates.

The default outcome of an inconclusive experiment is no change.

That is an important philosophical constraint on a repository that could otherwise accumulate orchestration machinery indefinitely.

---

# 9. Current Persisted Run: What It Tells Us

The committed `.agents/artifacts/` set represents the current/most recent article run and functions as both evidence and a canonical fixture for parts of the test suite.

## 9.1 Route

`pipeline_config.json` records:

- depth: COMPLEX;
- adversarial dialectic: enabled;
- fact-check: enabled;
- red team: enabled;
- SEO pass: enabled;
- token budget: 48,000;
- draft in phases: true;
- web search: available;
- code execution: unavailable;
- composite triage score: 4.75;
- thesis confidence: MEDIUM.

The topic is the strategic tension around rapidly advancing Chinese open-source AI models, cost/benchmark competition with US closed models, enterprise flexibility, hardware/software dependence, and geopolitical risk.

The original brief included a specific “Alibaba's Qwen 3.8 Max” assertion that triage explicitly flagged as a named-entity claim requiring live verification.

## 9.2 Research and audit outcome

The state records:

- eight drafted sections;
- inline QA passes, with one PASS_WITH_NOTES;
- holistic QA PASS;
- red-team threat level MEDIUM;
- human red-team decision: address;
- reader rating MOSTLY ACCESSIBLE;
- three high-priority reader gaps;
- human reader decision: polish;
- no recorded gate expedite;
- no consecutive blocked-audit condition;
- KC-3 PASS with maximum single-source share 10%;
- KC-6 PASS with 0/7 insufficient vectors.

This is a useful demonstration that the post-draft layers are intended to catch different issue classes rather than repeat one QA pass under different names.

## 9.3 Tool degradation

The run records code execution as unavailable because matplotlib was not installed.

The design treats resulting visual placeholders as a declared degraded-tool condition rather than silently implying images were created.

The validator can treat placeholder-only visuals as review-only when config explicitly says code execution was unavailable.

## 9.4 Current stage: REVIEW_REQUIRED

The state is schema version 2 and currently says:

`stage: REVIEW_REQUIRED`

Its structured E-E-A-T object says `FAIL` because the article has no real author name/credential near the byline.

The recorded reason explicitly states that:

- Experience passes;
- Authoritativeness passes;
- Trustworthiness passes;
- Expertise fails due to absent author identity/credential;
- the missing author data must not be fabricated.

This is a meaningful current-state behavior:

> The article can be content-complete and QA-clean while the pipeline still refuses to mark it distribution-ready because a genuine publication requirement remains unresolved.

## 9.5 Historical migration visible in the fixture

Recent schema-hardening work changed the fixture from an older legacy shape to v2 and reconciled derived values.

The current canonical word count is 2,291 and is represented consistently in the updated state/SEO artifacts from the migration/finalization hardening work.

The state moved to `REVIEW_REQUIRED` rather than preserving a legacy `COMPLETE` assertion once the structured E-E-A-T blocker was recognized.

This is an example of the project choosing current contract correctness over preserving a convenient historical “complete” label.

---

# 10. Cross-Run Learning

`pipeline_learnings.md` currently records one detailed COMPLEX run and three important classes of lesson.

## 10.1 Route calibration

The 4.75 COMPLEX route was judged appropriate because adversarial research surfaced real conflicts that a shallower route might have flattened.

## 10.2 Spec staleness after fact-check

The run discovered a real handoff issue:

- `article_spec.md` was written before fact-check;
- a claim was initially excluded;
- fact-check later upgraded it to usable;
- `claims_for_drafting.md` reflected the new status;
- the spec remained stale.

The active skills now contain an explicit precedence rule giving `claims_for_drafting.md` authority when these disagree.

## 10.3 Post-draft validation is nonredundant

The run reports that:

- red team found a logical scope-overreach;
- reader simulation found comprehension gaps;
- these were not found by factual/citation-focused QA.

This provides at least anecdotal evidence for keeping those post-draft stages on COMPLEX runs.

## 10.4 Author metadata gap

The learning artifact correctly identified that E-E-A-T author expertise would repeatedly fail without an author field/project default.

The active triage skill and schema now include an `author` concept, but the current persisted config predates that richer producer contract and does not contain it.

This is another example of the repository evolving around evidence from its own prior run.

---

# 11. Actual Sources of Truth in the Current Repository

The repo explicitly says executable behavior outranks prose. Applying that rule yields this practical hierarchy.

## 11.1 For actual state mutation and completion

Highest authority:

1. `scripts/pipeline_runner.py`
2. `schemas/pipeline_state.schema.json`
3. hook restrictions in `.claude/settings.json` + `state_enforcer.sh`
4. tests that exercise those behaviors

The current code, not stale references in root prose, determines what state shape the runner accepts and how COMPLETE is reached.

## 11.2 For artifact validity

Highest authority:

1. `scripts/validate_artifacts.py`
2. `scripts/artifact_contract.py`
3. `schemas/*.schema.json` + `validate_schemas.py`
4. manifest contents and tests

## 11.3 For semantic article workflow

Highest practical authority:

1. `.claude/skills/multi-agent-article-pipeline/SKILL.md`
2. the individual article skills it composes
3. `.claude/agents/*.md` for isolated worker capabilities
4. root README as an operational overview

Root `CLAUDE.md` provides important control-plane principles, but its current “Sources of truth” subsection includes implementation paths that do not exist on this branch, so those specific path claims cannot be treated as executable truth.

## 11.4 Historical material

Treat these as context, not current behavior, unless confirmed against code:

- `blueprint.md`
- `diagnostics/*.md`
- the previous version of this discovery report
- older commit-era state/artifact descriptions

Many findings in `blueprint.md` have already been implemented even though its header still says “proposal, not yet implemented.”

---

# 12. Current Contract Drift and Gaps

This section intentionally reports observations only. It is not an implementation plan.

## 12.1 HIGH — Root `CLAUDE.md` names nonexistent workflow authorities

Root `CLAUDE.md` states that:

- `orchestration/workflow.json` is an intended source of truth;
- `scripts/workflow.py` is the deterministic workflow-state authority;
- runtime state/evidence live under `.workflow/`;
- nontrivial changes should invoke a project `workflow` skill.

On the inspected `main` branch:

- `orchestration/` does not exist;
- `scripts/workflow.py` does not exist;
- `.workflow/` is not the active runtime location;
- no `workflow` skill appears under `.claude/skills/`.

The README explicitly warns that `scripts/workflow.py` / `orchestration/workflow.json` references are stale/aspirational and says the live article runtime is Claude Code + `pipeline_runner.py` + `.agents/artifacts/`.

**Interpretation:** this is documentation/control-plane drift, likely from a broader or later generic control-plane concept being merged into an article-pipeline implementation that has not adopted those mechanisms.

## 12.2 HIGH — Active research skill checks the legacy `pipeline_state.json.gates` field

`article-research-dialectic/SKILL.md` says that when thesis confidence is MEDIUM it should verify:

`pipeline_state.json.gates`

contains a triage confirmation.

But current state schema v2 uses:

`gate_history`

and `pipeline_runner.load_state()` rejects state containing a legacy `gates` key.

The current persisted state itself has a valid `gate_history` entry with decision `confirmed`.

**Interpretation:** literal execution of the active research pre-check can disagree with the current machine state contract and potentially produce a false halt or require the main session to infer the intended field.

## 12.3 HIGH — Triage confirmation is not representable through current `record-gate` decision vocabulary

The current v2 fixture contains:

- gate: `TRIAGE_THESIS_CONFIRM`
- decision: `confirmed`

But `pipeline_runner.py` allows only these `record-gate` decisions:

- approved
- expedite
- revise
- abort

Therefore a new run cannot recreate the existing `confirmed` triage-gate record through the current `record-gate` command as written.

At the same time, direct Write/Edit of `pipeline_state.json` is denied by the hook.

**Interpretation:** the deterministic state-authority migration is incomplete specifically around triage confirmation. The current historical entry was preserved/migrated, but the runner's public mutation vocabulary does not currently express it.

## 12.4 MEDIUM-HIGH — Active pipeline skill contains stale `article-pipeline-runner` references

The multi-agent skill includes conditionals such as:

- “If `article-pipeline-runner` is active...”
- “If `article-pipeline-runner` was active: read `pipeline_state.json.telemetry`...”

No `article-pipeline-runner` skill appears in the active `.claude/skills/` listing.

The `telemetry` object is also a legacy state shape explicitly rejected by the current v2 runner.

**Interpretation:** these are remnants of an earlier orchestration layer and can confuse resume/gate/learning behavior if followed literally.

## 12.5 MEDIUM — Deterministic transition code exists, but semantic orchestration is still primarily prose-driven

`pipeline_runner.advance()` contains a legal transition table, but the end-to-end scheduler remains the Claude session following skills.

In the active multi-agent skill inspected during this pass, critical counters and finalization are explicitly invoked through runner commands, but there is no corresponding visible command sequence using `advance --stage ...` to drive every normal phase boundary. Repository search during discovery did not locate an active `pipeline_runner.py advance` call site.

**Interpretation:** the transition graph is real enforcement machinery, but it is not the full article scheduler. The repo remains a hybrid where phase sequencing is substantially model/skill-owned while selected state invariants are script-owned.

## 12.6 MEDIUM — “pipeline_state is runner-owned” is stronger than the runner's mutation surface

The v2 schema describes `pipeline_state.json` as owned exclusively by `pipeline_runner.py`, and the hook blocks direct model writes.

Yet the schema contains optional descriptive fields such as:

- post-draft red-team metadata;
- reader-simulation metadata;
- delivery metadata;
- learning metadata;
- artifact lists;
- detailed draft metadata.

The current runner exposes commands for stage, gate history, revision count, KC events, consecutive blocked audits, word count, E-E-A-T sync, migration, and finalization, but not dedicated mutation commands for every one of those descriptive fields.

**Interpretation:** v2's deterministic authority is strongest around **critical gating fields**, while richer descriptive state is partly legacy/optional. The schema makes most of those fields optional, which prevents this from being a hard validity failure, but the prose still sometimes assumes richer telemetry exists.

## 12.7 MEDIUM — Triage producer contract is stricter than machine schema

The active triage skill says its config fields are all required and explicitly says the `author` object should always be written.

The machine `pipeline_config.schema.json` requires only a smaller core:

- depth;
- route booleans;
- token budget;
- topic brief;
- thesis;
- thesis confidence.

Fields including `author`, `word_count_method`, scores, tool availability, and `draft_in_phases` are optional under the schema.

The current committed config conforms to the machine contract despite lacking newer producer fields such as `author` and `word_count_method`.

**Interpretation:** the schema is serving both compatibility and minimum validity, while the active producer skill expresses a stronger desired shape. The repository therefore has a distinction between “schema-valid config” and “config a current triage run should produce.”

## 12.8 MEDIUM — Runtime artifact validation and JSON Schema validation are separate enforcement moments

SessionStart calls `validate_artifacts.py`, not `validate_schemas.py`.

`validate_artifacts.py` performs substantial semantic checks, but it does not run Draft 2020-12 schema validation.

The schema validator runs under `make verify` / CI.

**Interpretation:** a malformed-but-parseable JSON shape not caught by the runtime validator could be detected later by verification/CI rather than on every article-session resume. This is a separation-of-concerns choice, but it is important when deciding which guarantees are active at runtime versus merge time.

## 12.9 MEDIUM — Post-write rollback is stronger for Markdown than for non-state JSON

Pre-write backup covers Markdown and JSON artifacts under the artifact root.

Post-write targeted validation/rollback, however, proceeds only for `.md` artifacts after special state handling.

`pipeline_state.json` is separately protected by direct-write denial.

Other JSON artifacts therefore do not receive the same immediate post-write structural rollback path.

**Interpretation:** the hook layer primarily protects prose artifacts plus the critical state file; schema/CI provides a later line of defense for core JSON contracts.

## 12.10 LOW-MEDIUM — README dependency statement is stale

README says the scripts have no third-party runtime dependencies and that pytest is dev-only.

Current reality:

- `validate_schemas.py` imports `jsonschema`;
- `requirements.txt` explicitly declares `jsonschema>=4.20` and documents it as the exception;
- `pytest>=8.0` remains a test dependency.

The requirements file is current; the README prose is not.

## 12.11 LOW — README verification summary omits a newer schema-validation step

Current `verify.sh` runs schema validation before tests.

The README's high-level verification description still emphasizes hook syntax, settings JSON, and tests and does not fully reflect the newer step.

This is minor documentation lag rather than behavioral risk.

## 12.12 LOW — Historical blueprint status is stale in the opposite direction

`blueprint.md` still says “proposal, not yet implemented,” yet several of its most important proposals now exist:

- canonical word-count synchronization;
- capability-isolated advocate/skeptic/red-team agents;
- deterministic gate/KC/revision counters;
- explicit claim-precedence guidance;
- schema/state hardening;
- structured E-E-A-T reconciliation.

The README correctly instructs readers to treat the blueprint as historical.

---

# 13. What Is Strong in the Current Architecture

## 13.1 Capability isolation is real where it matters most

The advocate, skeptic, and red team do not merely receive “please do not look” instructions. Their tool surfaces remove relevant read capabilities.

## 13.2 COMPLETE is no longer a model assertion

`finalize()` derives state, validates, and only then enters COMPLETE.

This is one of the strongest objective guarantees in the repo.

## 13.3 Derived data has a canonical source

Word count is derived from `article_draft.md`, then synchronized outward.

E-E-A-T status is parsed into structured state so validators do not have to infer critical state from arbitrary prose vocabulary.

## 13.4 Schema migration is explicit

The runner rejects legacy shapes and tells the user how to migrate instead of silently accepting ambiguous state.

## 13.5 Hooks survive a clean clone

Moving hook registration from local-only settings to committed `.claude/settings.json` closed a major reproducibility hole present in the previous report's snapshot.

## 13.6 Checkout verification is cheap and separated from expensive evaluation

CI verifies deterministic contracts on every push/PR while excluding live QPR experiments.

This keeps normal merge gating practical without pretending deterministic unit tests are a substitute for control-plane outcome evaluation.

## 13.7 Current run state demonstrates truthful failure

The system leaves the article review-required because it lacks real author metadata rather than fabricating credentials to satisfy its own checklist.

That is a valuable integrity property.

## 13.8 Cross-run learning is explicit and inspectable

The project does not hide “memory” entirely in an opaque model feature. It writes learnings and knowledge artifacts that can be reviewed, versioned, and challenged.

## 13.9 The evaluation harness attacks self-grading

Independent factual and blind editorial graders reduce the risk that a candidate control plane simply changes the rules by which it judges itself.

---

# 14. What This Repository Is Not

It is not:

- a generic CMS;
- a web publishing platform;
- a one-command autonomous Python article generator;
- a production job queue;
- a hardened security sandbox;
- a purely deterministic workflow engine;
- a prompt-only “multi-agent” demo;
- an SEO tool by itself;
- a standard Python package;
- a completed generic Claude engineering-workflow framework despite some root `CLAUDE.md` language that points in that direction.

The actual product-like unit is the **Claude Code project environment plus its skills, subagents, artifacts, hooks, scripts, schemas, tests, and evaluation methodology**.

---

# 15. Repository Map

## Root

### `README.md`
Current operational orientation. More accurate than root `CLAUDE.md` for identifying the live article-runtime mechanisms where the two conflict.

### `CLAUDE.md`
Control-plane principles, change methodology, evidence/experimental discipline. Contains important stale path/source-of-truth references that should not be mistaken for current executable behavior.

### `ARTICLE_PIPELINE_REPOSITORY_DISCOVERY_REPORT.md`
This report. Replaces the earlier snapshot report.

### `blueprint.md`
Historical improvement proposal. Several findings are now implemented; its status line should not be used as current implementation truth.

### `Makefile`
Thin `verify` entrypoint.

### `requirements.txt`
Current Python verification dependencies: pytest and jsonschema.

### `LICENSE`
MIT.

## `.claude/`

### `settings.json`
Committed hook registration.

### `agents/`
Capability-isolated advocate, skeptic, red-team agents.

### `skills/`
Article workflow skills plus meta-skills for control-plane/rule/workflow/subagent design.

## `.agents/`

### `artifacts/`
Current/most recent persisted article run and integrity manifest.

### `knowledge/article-pipeline/`
Cross-run context/pitfall knowledge extracted from prior article execution.

### `.state_enforcer/`
Runtime hook backups/telemetry location; intentionally git-ignored.

## `scripts/`

Deterministic contract/state/verification scripts plus the evaluation subsystem.

## `schemas/`

Machine-checkable JSON Schema contracts for four core JSON artifacts.

## `tests/`

Regression tests for state, migration, validators, hook enforcement, documentation contracts, and evaluator code.

## `.github/workflows/`

CI definition for deterministic merge-gating checks.

## `evals/article_pipeline/`

Visible evaluation corpus and evaluator documentation.

## `docs/`

Control-plane improvement protocol.

## `diagnostics/`

Historical forensic/design analyses.

## `docs-control-plane/claude-code-docs/`

Captured Claude Code documentation/reference corpus used by the control-plane work.

---

# 16. Current Maturity Assessment

A useful way to describe the current maturity is by layer.

## Layer A — Article semantics: mature but model-dependent

Research, synthesis, drafting, QA, reader simulation, and SEO are detailed and thoughtfully decomposed, but they necessarily rely on model judgment and live web quality.

## Layer B — Adversarial isolation: materially hardened

The highest-value independence boundaries now have capability-level enforcement.

## Layer C — Critical persisted-state guarantees: substantially hardened

Completion, revisions, kill events, gate counts, word-count synchronization, E-E-A-T state, and legacy migration have deterministic support.

## Layer D — Full orchestration state machine: hybrid / incomplete migration

The code contains a legal transition engine, but the main Claude session and skills still own much of the actual phase sequencing, and some active prose references a superseded runner/state design.

## Layer E — Artifact integrity: strong within intended path

Manifest hashing, validation, committed hooks, rollback, schemas, and tests provide multiple lines of defense. Hook enforcement is still a Claude Code control-plane mechanism rather than a hardened filesystem boundary.

## Layer F — Reproducibility: improved

The repo now includes committed hook settings, README, requirements, Makefile, verify script, schemas, tests, and CI. That is a major improvement over the earlier snapshot.

## Layer G — Outcome evaluation: unusually sophisticated for a repository of this type

The QPR harness and independent graders create a credible framework for measuring whether orchestration changes actually help.

## Layer H — Documentation coherence: currently the weakest layer

Several operational documents and active skills contain leftovers from earlier/later control-plane designs.

The current implementation is stronger than some prose implies, but the prose can also ask for state fields/mechanisms the implementation no longer supports.

---

# 17. The “Who / What / Why / How” in One Page

## Who

- **Human operator/publisher:** editorial authority and real-world metadata.
- **Main Claude session:** semantic orchestrator.
- **Advocate subagent:** supporting evidence, isolated.
- **Skeptic subagent:** disconfirming evidence, isolated.
- **Red-team subagent:** post-draft adversarial challenge, isolated from body.
- **In-context specialists:** triage, synthesis, summarization, fact-checking, drafting/QA, reader simulation, SEO.
- **Python/shell/schema layer:** deterministic enforcement.
- **Independent graders:** evaluate control-plane outcomes.

## What

A research-backed article generation and publication-readiness pipeline that produces both prose and an auditable evidence/decision package, plus infrastructure for experimentally improving that pipeline.

## Why

To produce better-supported articles while reducing:

- confirmation bias;
- hallucinated certainty;
- hidden handoff errors;
- stale state;
- silent artifact corruption;
- uncontrolled workflow drift;
- context waste;
- false completion;
- self-grading of control-plane changes.

## How

- route depth by topic complexity;
- split research into adversarial evidence streams;
- synthesize conflicts explicitly;
- independently fact-check material claims;
- compress research into bounded drafting artifacts;
- require human decisions for real conflicts and editorial choices;
- draft incrementally with inline QA;
- red-team complex conclusions;
- simulate target readers;
- package SEO/structured data;
- persist artifacts and cross-run learnings;
- enforce objective invariants through scripts/hooks/schemas/manifests/tests;
- measure control-plane changes with matched experiments and independent graders.

---

# 18. Final Assessment

The repository's current identity is clear:

> **It is an evidence-driven Claude Code article-production control plane that deliberately combines model judgment, capability-isolated adversarial workers, deterministic artifact/state enforcement, human editorial gates, and independent outcome evaluation.**

Its strongest idea is not the number of agents or stages. It is the explicit separation of responsibilities:

- research roles discover and challenge evidence;
- the main session performs semantic orchestration;
- humans own subjective or unknowable editorial facts;
- scripts own objective limits and derived state;
- validators and schemas inspect persisted contracts;
- hooks protect the normal execution path;
- CI protects repository contracts;
- independent graders evaluate whether control-plane changes improve actual results.

The implementation has materially caught up with the architectural intent since the previous discovery snapshot. Several previously identified weaknesses are now real code rather than proposals.

The largest remaining issue is **coherence at the control-plane boundary**: a handful of still-active instructions refer to state fields, skills, or workflow mechanisms from older/adjacent designs. Because this repo correctly declares that executable behavior outranks prose, the system remains understandable, but an agent following every instruction literally can still encounter contradictions.

The current `REVIEW_REQUIRED` article fixture is a fitting illustration of the project's philosophy. It is not marked complete simply because the model finished writing. It remains blocked because a genuine publisher-supplied author identity is absent. The control plane is therefore trying to optimize for **truthful readiness**, not merely task termination.

For future analysis in this conversation, this report's architectural model should be treated as the session baseline for repository snapshot `4277aabd8380e4b79ecd831763743f849585a2af`. If the repository changes after this snapshot, executable files should be re-inspected before assuming the report still describes the latest behavior.
