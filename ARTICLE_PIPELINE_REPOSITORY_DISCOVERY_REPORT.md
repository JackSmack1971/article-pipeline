# Article Pipeline Repository Discovery Report

**Repository:** `JackSmack1971/article-pipeline`  
**Branch inspected:** `main`  
**Snapshot inspected:** `4521479729c438fc7e8cb5fc1456ac636564c00a`  
**Mode:** Discovery / architecture analysis only  
**Repository changes made during discovery:** No existing files were modified. This report is the only new repository file created by the discovery pass.

---

## Executive Summary

This repository is best understood as **three systems occupying the same codebase**:

1. **A Claude Code–native article production pipeline** that takes a topic brief through complexity triage, adversarial research, synthesis, fact-checking, human approval, section-by-section drafting, QA, red-team challenge, reader simulation, SEO packaging, and cross-run learning.
2. **A control-plane laboratory** for moving important guarantees out of model instructions and into deterministic code, capability restrictions, state transitions, artifact validation, and hooks.
3. **An evaluation harness** that measures whether control-plane changes actually improve article quality, factual/citation integrity, reliability, cost, latency, and Qualified Publish Rate rather than merely making the prompts appear better.

It is **not** a conventional Python application, web service, package, or one-command article generator. There is no top-level executable that autonomously runs the whole pipeline from start to finish. The principal orchestrator is a **Claude Code session following project skills**, with selected work delegated to isolated subagents and selected invariants delegated to Python/shell code.

The architectural idea is sophisticated and internally coherent:

> **Use models for judgment; use deterministic mechanisms for guarantees.**

That principle appears repeatedly in `CLAUDE.md`, the control-plane improvement protocol, the pipeline state scripts, the validator, the artifact manifest, the isolated subagents, the unit tests, and the independent evaluation harness.

The repository's **current state is transitional**. The newest code has already implemented several hardening measures that older design documents still describe as proposals, while the committed example run under `.agents/artifacts/` was produced under an older schema. Recent merges also appear to have reconciled state/metadata/manifest files independently. As a result, the repo currently contains multiple generations of its own control-plane design at once.

The most important discovery is therefore not “this pipeline is broken” or “this pipeline is complete.” It is:

> **The repo is in the middle of a deliberate migration from prompt-enforced orchestration toward a hybrid, evidence-driven control plane. The newer mechanisms are materially stronger than the earlier design, but the migration has left contract drift between instructions, runtime state, historical artifacts, and executable enforcement.**

---

# 1. What This Repository Is

## 1.1 A Claude Code orchestration project, not a normal software product

The root `CLAUDE.md` explicitly defines the repository as both:

- the **implementation** of a Claude Code orchestration control plane; and
- the **active development environment** for that control plane.

That distinction explains the unusual repository layout. The important assets are not a normal `src/` package and application entrypoint. Instead, they are:

- `.claude/skills/` — procedural orchestration and specialist workflows;
- `.claude/agents/` — capability-isolated subagents;
- `.agents/artifacts/` — persisted output/state from an actual article run;
- `.agents/knowledge/` — retained cross-run lessons;
- `scripts/` — deterministic state, validation, integrity, and evaluation logic;
- `tests/` — regression tests for those deterministic contracts and evaluation rules;
- `evals/` — visible development corpus for matched experiments;
- `diagnostics/` — historical audits and implementation rationale;
- `docs-control-plane/` — a captured Claude Code documentation corpus;
- `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` — experimental method for modifying the control plane.

There is no root README, Python package manifest, dependency lock file, Makefile, or committed `.github/` workflow directory in the current snapshot.

This makes the repository primarily a **behavioral control system for Claude Code**, with Python acting as a policy/enforcement layer rather than as the complete application runtime.

## 1.2 A production workflow and an experiment platform in the same repo

The repository serves two distinct but connected purposes:

### Production-like article generation

The `multi-agent-article-pipeline` skill coordinates a full article lifecycle and persists every important handoff into named artifacts.

### Control-plane research

The repository also asks a meta-question:

> What combination of prompts, agents, state machines, validators, hooks, permissions, and independent graders produces better articles more reliably and efficiently?

The evaluation harness exists specifically so that answer is measured instead of assumed.

That dual purpose explains why the repo contains both article-generation artifacts and machinery for baseline/candidate experiments on the orchestration itself.

---

# 2. Who Is Involved

There are several different meanings of “who” in this repository.

## 2.1 Repository owner and human operator

The repository belongs to GitHub user `JackSmack1971`.

The human operator is intentionally kept in the workflow for decisions that are editorial rather than objectively computable. Examples include:

- confirming a medium-confidence thesis;
- approving or revising the article specification;
- deciding how conflicting evidence should be presented;
- deciding whether to address or merely acknowledge a red-team objection;
- deciding whether to polish reader-comprehension gaps;
- providing real author/publisher metadata rather than allowing the system to fabricate it.

This is an important design choice. The system does not attempt to turn all subjective decisions into automation.

## 2.2 The main Claude Code session

The main Claude session is the **actual workflow orchestrator**.

It:

- activates skills;
- reads and writes artifacts;
- delegates bounded work to custom subagents;
- presents human gates;
- invokes deterministic scripts;
- decides when semantic work is complete enough to move to the next scripted gate.

This is why the repository is not a standalone Python pipeline. Python owns important invariants, but the LLM session owns end-to-end semantic sequencing.

## 2.3 Capability-isolated custom subagents

Three custom subagents are committed under `.claude/agents/`:

### `article-advocate`

Purpose: find the strongest evidence supporting the thesis.

Tools:

- `WebSearch`
- `Write`

Notably absent:

- `Read`

This means the advocate cannot inspect prior artifacts or prior context through the filesystem.

### `article-skeptic`

Purpose: find the strongest evidence that undermines, narrows, or complicates the thesis.

Tools:

- `WebSearch`
- `Write`

Again, there is no `Read` tool. The skeptic is allowed to receive only the advocate's flat Source URL Index, not the advocate's extracted claims or framing.

### `article-red-team`

Purpose: attack the finished thesis/conclusion after drafting.

Tool:

- `WebSearch`

It has neither `Read` nor `Write`. The parent is expected to pass only the thesis and conclusion into the delegation prompt, so the red team cannot inspect the full article body.

These are the repository's clearest examples of **real enforcement through capability design** rather than prose alone.

## 2.4 In-session specialist roles

Other roles are implemented primarily through skills or persona shifts in the main session rather than isolated subagents. They include:

- triage/routing;
- synthesizer;
- summarizer;
- fact-checker;
- engineer/drafter;
- QA auditor;
- reader simulator;
- SEO optimizer.

These roles need broader access to shared artifacts, so they remain more tightly coupled to the main session.

## 2.5 Deterministic runtime actors

Several Python/shell components act as non-model authorities:

- `scripts/pipeline_runner.py` — stage transitions, counters, halts, word-count synchronization, finalization;
- `scripts/validate_artifacts.py` — read-only publishability/artifact contract validation;
- `scripts/artifact_contract.py` — canonical word counting and manifest integrity rules;
- `scripts/write_artifact_manifest.py` — SHA-256/byte-size artifact manifest generation;
- `scripts/state_enforcer.sh` — hook-time state protection, backup, targeted validation, rollback;
- `scripts/enforce_artifact_contract.sh` — hook entrypoint delegating to `state_enforcer.sh`.

## 2.6 Independent evaluators

The evaluation subsystem deliberately separates the system being improved from the system judging the improvement.

Its actors include:

- baseline subject control plane;
- candidate subject control plane;
- independent claim/citation grader;
- blind editorial grader;
- deterministic validator/metric aggregator;
- experiment runner.

The intent is to prevent the candidate control plane from “grading itself into success.”

---

# 3. What the Repository Does

At a high level, it transforms a research-heavy article request into a structured, auditable article package.

The expected output is more than an article. Depending on route depth, the pipeline may produce:

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

The core product is therefore not just prose. It is an **evidence trail describing how the prose was created, challenged, verified, revised, and approved**.

---

# 4. End-to-End Workflow

The current orchestrator describes the pipeline in stages.

## 4.1 Step 0 — Complexity triage

`article-complexity-triage` scores the brief across:

- novelty — 35%;
- contentiousness — 40%;
- scope — 25%.

The composite score routes the article:

| Composite | Route | Main behavior |
|---|---|---|
| 1.0–2.4 | SIMPLE | unified research, no adversarial dialectic, no fact-check gate, no red team |
| 2.5–3.7 | STANDARD | advocate/skeptic research, fact-check, no red team |
| 3.8–5.0 | COMPLEX | advocate/skeptic research, fact-check, red team |

SEO remains enabled across the default routes.

The triage stage also:

- extracts/formulates a thesis;
- flags suspicious named entities, quotes, or unsupported brief assertions;
- reads prior pipeline learnings;
- applies accumulated calibration only after sufficient evidence;
- records available tools;
- records author metadata as an explicit nullable object in the **current** schema;
- chooses a token budget.

### Why this exists

The repo is explicitly trying to avoid two symmetric failures:

- spending complex-pipeline resources on a simple article;
- treating a contentious/fresh topic as if lightweight generation were sufficient.

This is cost/quality routing, not merely categorization.

## 4.2 Step 1 — Adversarial research dialectic

STANDARD and COMPLEX routes split research into two independent streams:

- advocate searches for supporting evidence;
- skeptic searches for disconfirming evidence.

The synthesizer then classifies resulting evidence as:

- `CORROBORATED`
- `UNCONTESTED`
- `CONFLICTING`
- `WEAKENED`
- `INSUFFICIENT`

For conflicts, it records whether the disagreement is:

- definitional;
- temporal;
- methodological;
- empirical;
- interpretive.

It then produces the research context, article specification, and conflict register.

### Why this exists

This is a direct defense against **confirmation bias and one-sided retrieval**.

The repo does not ask one model to “research both sides fairly” after it has already formed a narrative. It structurally gives two agents opposed objectives and isolates their working context.

That is one of the most important architectural decisions in the project.

## 4.3 Kill-condition checks during research

The pipeline defines explicit stop conditions, including:

- KC-3: one source accounts for more than 40% of extracted claims;
- KC-6: more than 50% of research vectors are insufficient.

### Why this exists

The system prefers visible failure over manufacturing a confident article from a weak evidence base.

## 4.4 Step 1.25 — Research compression

A summary artifact is generated after synthesis.

Instead of forcing downstream roles to repeatedly consume the full research context, they can use `research_context_summary.md` and only retrieve full claim detail when needed.

### Why this exists

This is explicit context-window economics. The skill claims a 60–80% context reduction for complex runs.

It also reduces accidental downstream exposure to irrelevant research detail.

## 4.5 Step 1.5 — Independent fact-check pass

The fact checker treats synthesized claims as **untrusted until re-verified**.

For eligible claims it performs fresh searches and assigns:

- VERIFIED;
- VERIFIED-UPDATED;
- UNVERIFIABLE;
- DISPUTED;
- OUTDATED.

It also contains special checks for structurally mismatched social-platform citations.

### Why this exists

Research synthesis and final factual verification are treated as separate epistemic jobs.

A claim being present in the research artifact is not considered sufficient proof that the claim should appear as settled fact in the article.

## 4.6 Step 1.75 — Claim compression for drafting

The fact-check output is compressed into `claims_for_drafting.md`.

Each claim carries a final value, source URL, section mapping, status, and posterior confidence.

Drafting rules use confidence to determine whether prose may state a claim directly or must qualify/caveat it.

### Why this exists

This prevents the drafter from repeatedly re-interpreting a long fact-check report and creates a single compact lookup table for the values that should actually enter prose.

It also intentionally establishes precedence: where the earlier `article_spec.md` and later fact-check results disagree about a claim's status, the fact-check-derived drafting table wins.

## 4.7 Step 1.8 — Visual candidates

The specification can mark quantitative/process-heavy sections as visual candidates.

If code execution is unavailable, the pipeline degrades explicitly to placeholders rather than pretending an asset was generated.

### Why this exists

Tool degradation is made observable rather than silently changing the article package.

## 4.8 Step 2 — Human approval gate

The user reviews:

- the article specification;
- conflicts;
- disputes.

Conflicts can be handled by:

- neutral presentation;
- explicit author position;
- unresolved/contested framing.

The decision is persisted in `conflict_decisions.json`, which is authoritative for drafting.

### Why this exists

Conflict handling is an editorial/value judgment. The system does not silently convert ambiguity into a model-selected editorial stance.

## 4.9 Step 3 — Streamed drafting and inline QA

The drafter writes one section at a time.

QA audits each section before the next section advances.

Checks include:

- factual claim traceability;
- correct use of fact-check updates;
- citation integrity;
- conflict handling;
- qualification of uncertain claims;
- style/Markdown rules;
- structural requirements;
- visual placeholders where required.

Consecutive blocked audits are counted by deterministic code.

There is also a same-section retry kill condition and a mid-draft utilization kill condition.

### Why this exists

The pipeline is designed to catch drift close to where it is introduced rather than waiting until a fully formed article has accumulated many compounding errors.

## 4.10 Holistic audit

After per-section approval, QA evaluates the article as a whole for:

- thesis/conclusion alignment;
- narrative arc;
- cross-section consistency;
- citation concentration;
- conflict coverage;
- publication Markdown standards.

### Why this exists

A document can have locally correct sections that still fail globally. Holistic auditing handles system-level editorial properties that section checks cannot.

## 4.11 Step 4 — Red team for COMPLEX routes

The red-team subagent receives only:

- thesis;
- conclusion.

It attacks:

- unstated assumptions;
- false dichotomies;
- scope overreach;
- causal overclaims;
- empirical weaknesses;
- misleading framing.

The user decides whether to accept, address, or acknowledge the critique.

### Why this exists

The red team is intended to challenge the finished argument **without being anchored on the article's own evidence selection and rhetorical scaffolding**.

## 4.12 Step 5 — Reader simulation

A reader persona based on the target audience scans the article for:

- jargon;
- assumed knowledge;
- logical leaps;
- evidence opacity;
- engagement friction.

If the user chooses “polish,” only the highest-priority comprehension problems are targeted.

### Why this exists

The repo distinguishes expert correctness from audience accessibility.

## 4.13 Step 6.5 — SEO packaging

The SEO skill produces:

- title variants;
- meta description;
- slug;
- keyword-density analysis;
- JSON-LD;
- FAQ schema when applicable;
- Breadcrumb schema;
- on-page checklist;
- internal-link opportunities;
- E-E-A-T analysis.

### Why this exists

The final deliverable is intended to be publication/distribution-ready, not just editorially complete.

## 4.14 Step 7 — Cross-run learning and finalization

The run writes structured learnings that later triage passes may ingest.

The final deterministic step is `pipeline_runner.py finalize`, which:

1. recalculates the canonical draft word count;
2. synchronizes state and metadata;
3. regenerates the artifact manifest;
4. validates the artifact set;
5. writes `COMPLETE` only if the validator reports no errors/blockers.

### Why this exists

The model is not allowed to assert completion merely because it believes the work is done.

Completion is intended to be an observable state backed by persisted artifacts and validation.

---

# 5. How the System Is Implemented

## 5.1 Artifact-mediated orchestration

The pipeline treats files as explicit messages between stages.

Conceptually:

```text
User brief
   |
   v
TRIAGE ------------------------> pipeline_config.json
   |
   v
ADVOCATE ---> advocate_context.md ---\
                                      \
                                       > SYNTHESIS ---> research_context.md
                                      /                 article_spec.md
SKEPTIC ----> skeptic_evidence.md ----/                  conflict_register.md
                                                         |
                                                         v
                                                  research summary
                                                         |
                                                         v
                                                   FACT CHECK
                                                         |
                                            fact_check_report.md
                                            claims_for_drafting.md
                                                         |
                                                         v
                                                HUMAN APPROVAL
                                                         |
                                             conflict_decisions.json
                                                         |
                                                         v
                                                  DRAFT <-> QA
                                                         |
                                                   holistic QA
                                                         |
                                         red team / reader simulation
                                                         |
                                                         v
                                                       SEO
                                                         |
                                                         v
                                                   FINAL VALIDATE
                                                         |
                                              COMPLETE / REVIEW_REQUIRED
```

This approach is intentionally more verbose on disk than an implicit chat-only pipeline.

The benefit is traceability, resumability, and debuggability.

## 5.2 `pipeline_config.json` vs. `pipeline_state.json`

The design distinguishes:

- **configuration:** what route and capabilities this run should use;
- **state:** what actually happened and where the run currently is.

That split is conceptually sound.

The current repository, however, is in the middle of changing the exact state schema, discussed later in this report.

## 5.3 Deterministic state transitions

`pipeline_runner.py` defines legal stage transitions and explicitly forbids normal `advance()` calls from entering COMPLETE.

COMPLETE is reserved for `finalize()`.

This is exactly aligned with the root policy that objective guarantees should move out of prose and into code.

## 5.4 Canonical word counting

`artifact_contract.py` defines one canonical Markdown word-count function.

`sync_word_count()` applies that count to:

- `pipeline_state.json.draft.word_count`;
- the “Final word count” line in `pipeline_metadata.md`.

This was introduced because historical post-draft edits could leave independent word-count fields inconsistent.

## 5.5 Artifact integrity manifest

The manifest stores for every artifact except itself:

- SHA-256 hash;
- byte length.

The validator compares the persisted manifest with the current artifact tree.

This makes post-finalization edits visible.

It is an integrity/checkpoint mechanism, not a signed security boundary.

## 5.6 Read-only validation

`validate_artifacts.py` checks:

- required artifacts;
- route-dependent artifacts;
- stage-dependent artifacts;
- state references;
- word-count consistency;
- manifest integrity;
- selected editorial/tool-degradation conditions.

The status model is roughly:

- invalid/incomplete state;
- review required;
- publishable.

## 5.7 Hook-time protection

`state_enforcer.sh` implements a stronger layer around state/artifact mutation:

- SessionStart validation;
- direct state-file Write/Edit denial;
- Bash command guard for state mutation;
- artifact backups;
- post-write structural validation;
- targeted artifact-contract validation;
- rollback on implicated errors.

The diagnostic document explains that these hooks were tested with synthesized hook payloads.

However, the actual hook configuration file named by that design, `.claude/settings.local.json`, is **not present in the current `main` tree**.

Therefore:

> The hook implementation exists in the repo, but a clean checkout of the committed repository does not contain the configuration required to activate it.

A developer may have a local settings file that activates the hooks; this discovery pass cannot infer local uncommitted configuration. The important repository-level fact is that activation is not reproducible from committed files alone.

## 5.8 Unit tests

The current unit suite directly tests important deterministic contracts, including:

- only finalization can produce COMPLETE;
- illegal transitions are rejected;
- word counts are synchronized;
- a fourth approval revision is refused;
- repeated gate expedites are tracked;
- kill conditions return halt signals;
- blocked-audit counters reset/pass correctly;
- manifest drift is detected;
- tool degradation can remain review-only;
- skip-manifest mode does not disable unrelated required-artifact checks;
- evaluator hard guardrails;
- isolation leakage detection for skeptic/red-team delegation;
- QPR qualification and regression rejection.

There is no committed `.github/` workflow directory in the inspected snapshot, so these tests are not visibly wired to GitHub Actions in the repository itself.

---

# 6. The Evaluation System

The repository does not merely contain tests for helper functions. It contains an **experimental evaluation framework for the article pipeline itself**.

## 6.1 Matched baseline/candidate runs

`scripts/evals/qpr_runner.py` runs the same brief against baseline and candidate Git refs in fresh detached worktrees.

Pair order is randomized.

This is designed to reduce ordering and environment bias.

## 6.2 Subject/evaluator separation

Subject worktrees are scrubbed of:

- evaluation code;
- prior run artifacts;
- prior article-pipeline knowledge by default.

Independent graders run separately in Claude Code `--bare` mode.

This prevents the candidate pipeline from directly altering the grader instructions used to judge it.

## 6.3 Independent claim/citation grading

The factual grader independently audits material claims and citation URLs rather than trusting the pipeline's own fact-check artifacts.

That distinction is crucial: the article pipeline's internal fact checker is part of the subject being evaluated.

## 6.4 Blind editorial grading

The editorial grader sees the final article and brief/audience without being told whether it came from baseline or candidate.

## 6.5 Qualified Publish Rate

The evaluation harness defines a successful article more strictly than “the model returned a document.”

A run qualifies only when it satisfies requirements such as:

- deterministic validator says PUBLISHABLE;
- high factual claim precision;
- high citation-support rate;
- no missing material citations;
- editorial score thresholds;
- no fabricated/mismatched citation;
- no outdated claim presented as current fact;
- no fatal editorial defect;
- isolation guardrails remain intact;
- expected route depth is respected;
- no undeclared human rescue was required.

The harness also reports operational QPR so infrastructure failures cannot be hidden by excluding them from the quality denominator.

## 6.6 Why this subsystem exists

This is the natural extension of the repo's central philosophy.

If “model judgment is not enforcement,” then “the model saying the new workflow is better” is not evaluation either.

The repo therefore attempts to make control-plane improvement falsifiable.

---

# 7. Why the Repository Is Designed This Way

The current architecture can be traced to several recurring failure modes.

## 7.1 Hallucination and confirmation bias

**Mechanism:** advocate/skeptic split, independent fact check, independent eval grader.

**Reason:** one model researching a thesis can anchor on its first framing and selectively accumulate supporting evidence.

## 7.2 Context contamination

**Mechanism:** no-Read advocate/skeptic/red-team subagents, artifact handoffs, compressed summaries.

**Reason:** adversarial roles are less useful if they inherit the argument they are supposed to independently challenge.

## 7.3 Model arithmetic/state mistakes

**Mechanism:** deterministic gate counters, revision limits, audit circuit breakers, legal stage transitions.

**Reason:** a long-running model session should not be expected to reliably remember and increment workflow counters by hand.

## 7.4 Stale derived state

**Mechanism:** canonical word count, synchronization command, manifest hashes.

**Reason:** post-draft revisions previously changed the article without consistently updating dependent metadata.

## 7.5 False completion

**Mechanism:** only `finalize()` can enter COMPLETE; validator must pass.

**Reason:** “I think this is finished” is not sufficient evidence that required artifacts and checks are actually satisfied.

## 7.6 Over-processing

**Mechanism:** SIMPLE/STANDARD/COMPLEX routing.

**Reason:** full adversarial research and red-teaming are expensive and unnecessary for every topic.

## 7.7 Token/context pressure

**Mechanism:** research summaries, claim lookup tables, selective full-context reads, optional session split.

**Reason:** large context can reduce efficiency and can itself become a reliability problem.

## 7.8 Editorial over-automation

**Mechanism:** explicit human gates.

**Reason:** evidence can be computed and categorized, but how an author wishes to represent a genuine conflict is an editorial choice.

## 7.9 Self-congratulatory control-plane changes

**Mechanism:** matched baseline/candidate experiments, independent graders, QPR, guardrails, held-out guidance.

**Reason:** adding agents/hooks/prompts can make a system feel more sophisticated while making real performance worse.

---

# 8. What Is Strong in the Current State

## 8.1 The guidance/enforcement distinction is unusually explicit

The repository repeatedly states that instructions are guidance and executable controls are enforcement.

More importantly, several important properties have actually moved into code.

## 8.2 Adversarial isolation is real for the three custom subagents

The skeptic does not merely promise not to read advocate output. It lacks a Read tool.

The red team cannot merely be told “ignore the full draft.” It lacks a Read tool and is supposed to receive only a narrow prompt payload.

The test suite also contains dynamic leakage checks that inspect delegation prompts.

This is a strong design.

## 8.3 Completion has a deterministic authority

`finalize()` and `validate_artifacts.py` give the project a concrete definition of completion.

That is better than relying on a narrative final response from the model.

## 8.4 The artifact model creates an audit trail

The pipeline can explain not only what it wrote, but:

- what research supported it;
- what research challenged it;
- where sources conflicted;
- what the human decided;
- what fact checking changed;
- what QA found;
- what the red team attacked;
- what readers might not understand;
- what SEO packaging remains unresolved.

## 8.5 The project has explicit failure paths

Kill conditions make “stop and surface the problem” a first-class outcome.

That is healthier than always attempting to force a final article out of insufficient evidence or exhausted context.

## 8.6 Evaluation is independent of the subject pipeline

The development harness takes the important step of using separate graders and scrubbed subject worktrees.

It even explicitly warns that this is development isolation, not a security sandbox, and recommends stronger isolation for held-out confirmation.

## 8.7 The system is evidence-driven about its own evolution

The control-plane improvement protocol treats deletion/simplification as valid improvements and says inconclusive experiments should result in no change.

That is a useful counterweight to agent/control-plane complexity creep.

---

# 9. Current-State Contract Drift and Inconsistencies

This section is the most important discovery section because it describes the repo **as it exists now**, not merely as intended.

## 9.1 Root control-plane policy references authorities that are not present

`CLAUDE.md` names items such as:

- `docs/ARCHITECTURE.md`;
- `orchestration/workflow.json`;
- `scripts/workflow.py`;
- `AGENTS.md`;
- `make verify`;
- `.workflow/` runtime state.

Those paths/mechanisms are not present in the current repository snapshot.

The control-plane improvement protocol also refers generically to `scripts/workflow.py` and `.workflow/experiments/`.

### Interpretation

The root policy appears to have been generalized from or aligned with a broader control-plane architecture that this repository does not currently contain in full.

For this repository, the effective article-state authority is actually `scripts/pipeline_runner.py` plus `scripts/validate_artifacts.py`.

## 9.2 `blueprint.md` is now historical, not a current implementation plan

The blueprint labels itself “proposal, not yet implemented,” but several of its key proposals are already present on `main`, including:

- canonical word-count synchronization;
- isolated advocate/skeptic/red-team subagents;
- deterministic gate/KC/audit counters;
- explicit claim-precedence guidance;
- nullable author metadata in the current triage schema.

### Interpretation

The blueprint is valuable as causal history — it explains **why** later hardening happened — but it should not be treated as current-state truth.

## 9.3 The orchestrator references an `article-pipeline-runner` that is not in the repo

The main skill contains conditional language such as:

> If `article-pipeline-runner` is active...

No matching mechanism was found in the current repository search.

### Interpretation

This may refer to an external/user-level mechanism or a removed earlier component. In the committed repo alone, this branch of the documentation is unresolved.

## 9.4 `pipeline_state.json` currently has two generations of schema

The checked-in completed run uses a legacy shape with data such as:

- `gates: [...]`;
- `telemetry.revision_cycles`;
- `telemetry.kc_events`;
- `telemetry.gate_expedite_count`;
- `telemetry.consecutive_blocked_audits`.

The current `pipeline_runner.py`, however, writes newer fields at the top level:

- `gate_history`;
- `revision_cycles`;
- `kc_events`;
- `gate_expedite_count`;
- `consecutive_blocked_audits`.

The current orchestrator still tells the learning step to read the `pipeline_state.json.telemetry` block.

### Interpretation

There is no single formal state schema/migration layer binding the old artifact shape to the new runner behavior.

New runs using the current runner will progressively create a different shape than the checked-in historical run.

## 9.5 The current schema documentation does not fully define `pipeline_state.json`

`pipeline-schemas.md` gives concrete examples for `pipeline_config.json` and `conflict_decisions.json`, and it describes the persisted run contract, but it does not provide a full canonical `pipeline_state.json` schema matching current code.

### Interpretation

State evolution is being managed through implementation convention and tests rather than explicit schema versioning/migration.

## 9.6 The checked-in run predates the current config contract

The sample `pipeline_config.json` is a COMPLEX run from August 3, 2026.

It contains route flags, topic/thesis, scores, budget, and tool availability, but it does **not** contain current fields such as:

- `word_count_method`;
- the always-present `author` object now required by current triage guidance.

### Interpretation

The checked-in run is best treated as a historical execution snapshot, not as a canonical current-format fixture.

## 9.7 The checked-in artifact manifest is stale relative to current files

The committed `artifact_manifest.json` records:

- `pipeline_state.json` — 2,822 bytes;
- `pipeline_metadata.md` — 2,754 bytes.

The current repository tree reports:

- `pipeline_state.json` — 2,715 bytes;
- `pipeline_metadata.md` — 2,714 bytes.

Because byte size is part of the manifest contract, these differences alone guarantee a manifest mismatch under the current verifier.

### Interpretation

The committed run says `stage: COMPLETE`, but the artifact set as presently committed does not satisfy the current manifest-integrity contract without regenerating the manifest.

Recent merge history shows conflicts specifically involving `artifact_manifest.json`, `pipeline_state.json`, and `pipeline_metadata.md`, which is consistent with this drift. That history is suggestive, though this report does not claim the merge is definitively the only cause.

## 9.8 Word-count synchronization stops short of SEO-derived metadata

The current state and pipeline metadata both say the final draft is **2,291 words**.

The checked-in `seo_package.md` still says **2,151 words** in:

- Article JSON-LD `wordCount`;
- the on-page word-count checklist.

`sync_word_count()` intentionally synchronizes only:

- article draft -> state;
- article draft -> pipeline metadata.

It does not update `seo_package.md`.

### Interpretation

The original three-way word-count drift was addressed, but a fourth derived representation now remains stale after post-SEO/post-draft revision.

## 9.9 The E-E-A-T blocker has a wording/validator mismatch

The current validator's blocking regex looks for the term `FAILED` near `E-E-A-T`.

The checked-in SEO artifact uses:

> `FAIL — see E-E-A-T Gaps below`

and later states that the article should not be considered distribution-ready until a byline is added.

The unit test for this condition also uses the exact text `E-E-A-T: FAILED`.

### Interpretation

The semantic artifact says the E-E-A-T requirement failed, but the deterministic validator's regex is narrower than the producer's current wording.

This creates a false-negative path for a condition the validator is intended to treat as blocking.

The newer SEO skill changes author-null behavior so a deliberately null project author becomes N/A rather than FAIL, but the checked-in run predates that rule.

## 9.10 QA contains a citation-policy contradiction

The holistic QA checklist says:

> Source Appendix present and complete

The Markdown style authority explicitly bans:

- footnote blocks;
- trailing citation blocks;
- a Source Appendix pattern at the document end.

The checked-in SEO package itself recognizes this and treats its Source Appendix check as N/A because phrase-linked citations are the project standard.

### Interpretation

At least one QA checklist item is stale relative to the newer Markdown citation policy.

## 9.11 Hook implementation exists, but hook activation is not committed

`diagnostics/002-state-verification-layer.md` says the hook configuration was delivered in `.claude/settings.local.json`.

The current `main` tree does not contain that file.

### Interpretation

The scripts are present, tested, and documented, but a clean clone cannot reproduce the full hook-enforced behavior from versioned repository state alone.

This is especially important because the hooks are what turn several mutation rules from “call this script” into an automatic control around tool use.

## 9.12 Skill-layer capability restriction remains weaker than subagent restriction

The three custom subagents have explicit tool allowlists.

Most workflow skills run inside the main session and therefore rely on ambient permissions plus procedural instructions.

### Interpretation

Role boundaries are strongest where custom subagents are used. They are softer where a persona is implemented as an in-session skill.

This may be appropriate for roles that genuinely need broad artifact access, but it means the overall system has mixed enforcement strength depending on the stage.

## 9.13 There is no repository-visible CI pipeline

Tests are present and meaningful, but `.github/` is absent in the current tree.

### Interpretation

The repository has testability without a committed GitHub Actions enforcement path.

Verification therefore depends on local/manual/evaluator execution unless another external CI mechanism exists outside the repo.

---

# 10. Current Checked-In Run: What It Tells Us

The `.agents/artifacts/` directory is especially useful because it demonstrates how the system behaves in practice.

## 10.1 Route

The run was classified COMPLEX:

- adversarial dialectic: enabled;
- fact-check: enabled;
- red team: enabled;
- SEO: enabled;
- code execution: unavailable;
- web search: available.

The topic concerns Qwen3.8-Max and the strategic implications of competitive Chinese open-weight AI models.

## 10.2 Human interaction

The thesis confidence was MEDIUM and was confirmed.

The approval gate was approved without spec revisions.

The red team returned MEDIUM threat and the user chose to address the issue.

The reader simulation returned MOSTLY ACCESSIBLE and the user chose to polish the article.

## 10.3 QA behavior

The state records eight sections with:

- seven PASS;
- one PASS WITH NOTES;
- no blocked sections;
- holistic PASS.

## 10.4 Post-draft revisions

The red-team response revised the conclusion.

Reader polish revised three sections.

This historical run is the exact kind of workflow that exposed the original word-count synchronization problem: the article changed after initial drafting.

## 10.5 Tool degradation

Because code execution was unavailable, the run retained visual placeholders rather than generated chart files.

This is explicitly logged instead of hidden.

## 10.6 Learning

The run wrote pipeline learnings and knowledge artifacts, including observations that later informed architecture changes.

### Overall interpretation of the sample run

The artifact set is valuable as a **forensic trace of a real complex run**, but it should not be used as an unquestioned golden fixture for current schemas because the control plane changed after it was produced.

---

# 11. Development History Implied by the Repo

The current structure suggests a recognizable evolution.

## Phase A — Prompt/skill-first article pipeline

The initial system appears to have relied heavily on detailed skills and persona instructions.

The pipeline already had a thoughtful article methodology, but some workflow invariants were model-maintained.

## Phase B — Failures exposed by a real run

The historical blueprint and run artifacts identified concrete problems, including:

- stale word counts after post-draft revisions;
- adversarial roles relying too much on instruction-level isolation;
- counters/limits maintained by the model;
- stale spec claim status after fact-check updates;
- an unsatisfiable author/SEO condition.

## Phase C — Deterministic hardening

Current `main` now contains:

- isolated subagents;
- word-count sync;
- deterministic gate/KC/audit counters;
- finalization gate;
- manifest integrity;
- state-enforcement hooks/scripts;
- regression tests.

## Phase D — Evaluation hardening

Recent commits add:

- independent claim/citation grading;
- blind editorial grading;
- matched experiment corpus;
- QPR runner;
- isolation leakage tests;
- guardrail-aware recommendation logic.

### Interpretation

The repository is evolving from:

> “a sophisticated prompt workflow”

into:

> “a hybrid orchestration system whose important invariants are measured and increasingly executable.”

That evolution explains why the current repo contains both mature ideas and transitional seams.

---

# 12. Source-of-Truth Hierarchy in Practice

The repo's stated policy is that executable behavior outranks prose.

For this repository specifically, the practical hierarchy is approximately:

## Level 1 — Strongest executable authority

- custom subagent tool allowlists;
- `pipeline_runner.py` transition/counter/finalization logic;
- `validate_artifacts.py`;
- `artifact_contract.py`;
- manifest verification;
- unit/evaluator hard guardrails.

## Level 2 — Executable only if project/local configuration activates it

- `state_enforcer.sh` hook behavior.

The implementation is versioned, but the committed hook registration is absent.

## Level 3 — Procedural orchestration

- `multi-agent-article-pipeline/SKILL.md`;
- specialist skills;
- Markdown/style references;
- persona/reference documents.

These strongly guide model behavior but do not automatically enforce every rule.

## Level 4 — Historical/design rationale

- `blueprint.md`;
- diagnostics describing previous phases;
- old persisted run schemas/artifacts.

These explain intent and evolution but should not override newer executable code.

This hierarchy matters when documents conflict.

---

# 13. What the Repository Is Not

Clarifying what this repo is **not** helps avoid incorrect assumptions.

It is not currently:

- a hosted article-generation service;
- a REST API;
- a Python package intended for installation;
- a single CLI that executes the complete editorial pipeline;
- a generic multi-agent framework independent of Claude Code;
- a fully deterministic workflow engine;
- a fully autonomous publisher;
- a security sandbox;
- a schema-stable production release.

It is a **Claude Code–specific, artifact-centric orchestration system with deterministic support/enforcement components and a serious experimental evaluation layer**.

---

# 14. Maturity Assessment

## 14.1 Editorial methodology: High sophistication

The research/fact-check/conflict/QA/red-team/reader/SEO sequence is unusually explicit.

The system has thought carefully about epistemic failure, audience fit, and traceability.

## 14.2 Deterministic workflow enforcement: Medium-to-high, still expanding

Key counters, transitions, completion checks, word count, and artifact integrity are now coded.

However, the full workflow is still LLM-orchestrated, and hook activation is not reproducible from committed config alone.

## 14.3 State/schema stability: Transitional

The biggest structural weakness in the current snapshot is state/config/artifact schema drift across generations.

## 14.4 Test quality: Good for current deterministic components

The tests target meaningful failure modes rather than superficial coverage.

There is, however, no visible CI wiring in the committed repo.

## 14.5 Evaluation methodology: Strong and unusually rigorous for an agent workflow

Matched worktrees, bare independent graders, QPR, operational QPR, hard guardrails, and held-out guidance show serious attention to experimental validity.

## 14.6 Packaging/reproducibility: Moderate

A knowledgeable Claude Code user can understand the system, but a fresh clone does not expose a simple root entrypoint or all runtime hook configuration.

The absence of a root README also means the intended startup path must be inferred from `CLAUDE.md` and skill metadata.

## 14.7 Documentation consistency: Rich but drifted

There is substantial documentation, but some of it belongs to different generations of the design.

The repository's own policy correctly says these disagreements should be surfaced rather than silently reconciled.

---

# 15. The Central Architectural Tradeoff

The repo makes a deliberate tradeoff:

### It accepts more artifacts, stages, and explicit control machinery...

in exchange for:

- traceability;
- stronger evidence discipline;
- resumability;
- isolated adversarial roles;
- deterministic completion criteria;
- measurable control-plane experiments.

The risk is **control-plane entropy**: each new stage, counter, schema field, hook, and artifact creates another synchronization boundary.

The current repository demonstrates both sides of this tradeoff:

- the extra machinery has caught and prevented real failure modes;
- the machinery itself now has version drift that must be treated as a first-class system concern.

This is likely why the root policy and improvement protocol repeatedly emphasize simplicity and deleting mechanisms that do not earn their cost.

---

# 16. Current-State Mental Model

The simplest accurate mental model is:

> **A Claude session acts as an editorial operating system. Skills are its procedures. Isolated subagents are specialist processes. Artifacts are the IPC/state files. Python scripts are kernel-like invariants. The validator is the completion gate. The evaluation harness is the external benchmark lab.**

That analogy explains most of the repository.

The main session is flexible and semantic.

The subagents isolate certain adversarial jobs.

The artifact tree externalizes memory.

The Python layer prevents a subset of state/integrity mistakes.

The evaluator judges whether changing that whole control plane actually improves outcomes.

---

# 17. Discovery Conclusions

## What is it?

A Claude Code–native, multi-stage article generation and editorial assurance control plane, combined with an experimental framework for improving that control plane.

## What does it do?

It routes article requests by complexity, gathers adversarial evidence, synthesizes conflicts, re-verifies factual claims, pauses for human editorial decisions, drafts and audits incrementally, red-teams complex arguments, simulates target readers, packages SEO, persists a detailed provenance trail, and validates final artifacts.

It also runs matched experiments to determine whether changes to that system improve qualified article outcomes.

## How does it do it?

Through a hybrid architecture:

- Claude skills for semantic procedures;
- three capability-isolated subagents for adversarial independence;
- named Markdown/JSON artifacts for handoffs and state;
- Python for state transitions, counters, canonical calculations, validation, manifests, and eval metrics;
- shell hooks for mutation-time enforcement/rollback when locally configured;
- human gates for subjective editorial decisions;
- independent graders for control-plane evaluation.

## Why does it do it this way?

Because the repository is explicitly designed around the belief that:

- research agents can anchor and hallucinate;
- model assertions are not proof;
- objective invariants should not depend on memory/prompt compliance;
- difficult articles need adversarial evidence and explicit conflict treatment;
- human editorial judgment should remain human where appropriate;
- context/token costs must be managed;
- orchestration changes should be retained only when controlled evidence shows net benefit.

## Why is it in its current state?

Because it is actively migrating from an instruction-heavy first implementation toward a more deterministic and experimentally validated control plane.

The historical run and blueprint exposed real failure modes. Newer commits responded by adding isolated agents, deterministic counters, state guards, artifact validation, and a rigorous evaluator.

That work happened quickly enough that the repository currently contains:

- old run artifacts;
- newer state code;
- partially stale orchestration prose;
- historical proposals that are now implemented;
- hook code whose activation file is not committed;
- a manifest that no longer matches the current checked-in artifact files;
- derived SEO metadata that predates the final synchronized draft count.

The current repo should therefore be viewed as an **advanced experimental system in active consolidation**, not a finished, schema-stable product.

---

# 18. High-Signal Findings to Carry Into Any Future Phase

This discovery phase does not modify or redesign the system, but the following facts are the most important context for any later work:

1. **Do not mistake `pipeline_runner.py` for the full orchestrator.** It is a deterministic state helper/finalizer; Claude Code skills remain the workflow engine.
2. **Treat the three custom subagent tool allowlists as real enforcement and the skill instructions as softer controls.**
3. **Treat current executable code as newer than the August 3 sample artifacts.**
4. **Do not use `blueprint.md` as an implementation-status source without checking current code.** Many proposals are already implemented.
5. **Resolve state-schema generation before reasoning about telemetry.** Legacy artifacts nest it; current code writes several fields at top level.
6. **The current committed artifact manifest is stale against the current artifact files.**
7. **SEO-derived word count is stale relative to final state/metadata.**
8. **The E-E-A-T validator and producer wording do not currently align exactly.**
9. **The QA Source Appendix requirement conflicts with the current phrase-link/no-trailing-citation style authority.**
10. **Hook enforcement scripts are committed; hook registration is not.** Repository-level enforcement therefore differs from the documented locally tested configuration.
11. **The evaluator is a major architectural subsystem, not auxiliary test code.** It defines how future control-plane changes are supposed to earn their place.
12. **The repo's intended direction is simplification through evidence, not unconditional accumulation of more agents/rules/hooks.**

---

# 19. Final Characterization

If this repository had to be described in one paragraph:

> `article-pipeline` is a Claude Code–centric editorial control plane that turns research-heavy article briefs into evidence-backed, conflict-aware, fact-checked, audited, adversarially challenged, audience-tested, SEO-packaged deliverables while persisting the entire reasoning/evidence workflow as artifacts. It deliberately assigns subjective judgment to models/humans and objective workflow guarantees to deterministic code. In parallel, it contains a matched experimental evaluator designed to prove whether changes to that control plane improve real publication quality. The current `main` branch is a transitional snapshot: newer hardening mechanisms are present, but historical artifacts and several documents still reflect earlier schemas and enforcement assumptions.

---

## Discovery Scope Notes

This report was produced from static inspection of the repository contents, current `main` metadata, current file contents, and recent commit history through GitHub.

No existing repository file was edited or deleted. No branch was created. No test suite or article-generation run was executed during this discovery pass. The report intentionally distinguishes:

- **observed current implementation**;
- **historical artifacts/design rationale**;
- **inferences about why the current state evolved**.

Where the repository itself contains disagreement between implementation, documentation, and persisted artifacts, the disagreement is reported rather than silently normalized.
