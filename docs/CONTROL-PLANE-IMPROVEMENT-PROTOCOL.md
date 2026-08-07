# Control-Plane Improvement Protocol

## Purpose

This protocol governs changes intended to improve the Claude Code orchestration control plane.

Its purpose is not to make the control plane more elaborate. Its purpose is to make the system measurably better at completing real engineering work while preserving required guarantees.

A control-plane change is justified only when it improves an observable property, removes unnecessary machinery without meaningful regression, or closes a demonstrated correctness, safety, evidence, or efficiency gap.

The default outcome of an inconclusive experiment is **no change**.

## Scope

Use this protocol when changing or evaluating any mechanism that can materially affect Claude Code behavior, including:

- `CLAUDE.md` and scoped rules;
- skills and custom commands;
- subagent definitions, delegation policy, models, effort, or tool capabilities;
- hooks, permissions, sandboxing, or protected-path policy;
- workflow states, transitions, evidence rules, schemas, or templates;
- `scripts/workflow.py` or other deterministic orchestration logic;
- context-management, memory, compaction, or handoff mechanisms;
- verification, audit, completion, or stale-evidence behavior;
- benchmark or evaluation infrastructure;
- adoption, replacement, or removal of native Claude Code features;
- orchestration complexity, including adding or deleting agents, states, hooks, rules, or abstraction layers.

Ordinary product or repository changes are governed by the normal workflow. This protocol applies when the control plane itself is the experimental object.

## Core principle

Treat every control-plane modification as a falsifiable experiment.

Before implementation, state:

1. the concrete failure mode or wasted resource;
2. the causal hypothesis for why it occurs;
3. the smallest candidate intervention expected to change it;
4. the observable primary metric;
5. the minimum improvement worth keeping;
6. the guarantees that must not regress;
7. the evaluation method that can disprove the hypothesis.

Do not retain a change because it appears cleaner, more advanced, more agentic, more deterministic, or more elegant. Retain it because evidence demonstrates net value.

## Authority and enforcement

Prompt instructions are guidance. Executable controls are enforcement.

When a property must hold regardless of model judgment, prefer a deterministic mechanism such as:

- permission rules;
- hooks;
- restricted tool capabilities;
- sandboxing or worktree isolation;
- schemas;
- deterministic workflow transitions;
- tests or external graders.

Do not claim that a behavior is enforced merely because it appears in prose, agent instructions, configuration, or documentation.

Test the actual executable path and realistic bypass paths.

## Improvement objectives

Control-plane improvements may target one or more of the following dimensions.

### Correctness

- task success;
- implementation correctness;
- adherence to explicit requirements;
- correct workflow-state transitions;
- accurate evidence association;
- absence of false completion.

### Reliability

- success rate across repeated trials;
- lower variance across trials;
- fewer retries or recoveries;
- robust behavior under alternate valid task paths;
- robust behavior after context pressure or session boundaries.

### Safety and integrity

- resistance to bypass;
- preservation of permission and protected-path boundaries;
- correct rejection of invalid transitions;
- stale-evidence invalidation;
- grader and benchmark integrity;
- failure visibility rather than concealment.

### Efficiency

- total cost;
- input and output tokens;
- always-loaded context;
- tool calls;
- agent invocations;
- wall-clock latency;
- model/API duration where available;
- retries and rework;
- human interventions.

### Simplicity and maintainability

- fewer active mechanisms;
- fewer workflow states or transitions;
- fewer deterministic branches;
- fewer hooks, agents, skills, rules, or duplicated policies;
- smaller always-loaded instruction surface;
- clearer ownership and source-of-truth boundaries;
- reduced failure surface without loss of guarantees.

No single scalar score replaces these dimensions. Each experiment must declare a primary metric and guardrails.

## Non-goals

This protocol does not optimize for:

- novelty;
- maximum agent count;
- architectural sophistication;
- prompt length;
- benchmark score at any cost;
- passing visible tests through grader-specific tricks;
- replacing deterministic guarantees with model judgment merely to simplify code;
- preserving existing machinery because it already exists.

## Experimental separation

For meaningful experiments, separate these roles conceptually and, when practical, operationally.

### Optimizer

Finds weaknesses, proposes changes, and implements the candidate.

### Subject

The baseline or candidate control plane being evaluated.

### Evaluator

Runs the task, captures outcomes and traces, applies graders, and computes metrics.

### Auditor

Inspects anomalous traces, grader behavior, bypasses, and whether the experiment actually tested the stated hypothesis.

The optimizer must not be the sole judge of whether its own change succeeded.

For high-risk or benchmark-sensitive experiments, the candidate subject must not have read access to held-out task answers, hidden grader logic, or prior held-out transcripts.

## Evidence levels

Use the strongest practical level.

- **E0 — assertion:** model or human claims a change is better.
- **E1 — anecdote:** one favorable trace or manual example.
- **E2 — reproduction:** demonstrated failure before and successful targeted reproduction after.
- **E3 — controlled comparison:** baseline and candidate evaluated under matched conditions across repeated trials.
- **E4 — held-out validation:** controlled comparison on tasks or graders not available to the optimizer.
- **E5 — field validation:** sustained improvement in real usage or production-like workloads.

Anecdotal success is useful for hypothesis generation, not broad retention decisions.

Behavior-changing control-plane changes should normally reach E3. Changes to high-impact enforcement, general orchestration, or evaluation infrastructure should reach E4 when feasible.

## Experiment classes

Classify the experiment before work begins.

### Class A — documentation or non-behavioral clarification

Examples: correcting prose without changing loaded instructions or executable behavior.

Minimum evidence:

- source verification;
- diff review;
- relevant documentation checks.

### Class B — localized behavioral change

Examples: one skill trigger, one agent capability boundary, one hook condition, one workflow transition.

Minimum evidence:

- targeted reproduction;
- focused regression coverage;
- matched baseline/candidate trials on affected tasks;
- repository verification.

### Class C — cross-cutting orchestration change

Examples: delegation strategy, planning model, workflow topology, context strategy, broad `CLAUDE.md` changes, native-feature replacement.

Minimum evidence:

- controlled baseline/candidate comparison;
- multiple representative tasks;
- repeated trials;
- regression and adversarial suites;
- efficiency measurement;
- trace audit;
- repository verification.

### Class D — enforcement or evaluator change

Examples: permission boundaries, completion gates, stale-evidence rules, grader logic, benchmark harness, hidden-eval infrastructure.

Minimum evidence:

- everything required for Class C;
- explicit bypass or mutation tests;
- independent validation of the evaluator/control;
- held-out evaluation when feasible;
- dual evaluation when grader logic changes.

Use the higher class when uncertain.

## Required experiment record

Create an experiment record before implementation. Store transient run artifacts under `.workflow/experiments/<experiment-id>/` unless the repository defines another runtime location.

The record must contain at least:

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
  guardrails: []
comparators: []
evaluation:
  suites: []
  trials_per_task: null
  order_strategy: ""
  isolation_strategy: ""
  heldout_used: false
budget:
  max_cost_usd: null
  max_wall_time_minutes: null
invariants: []
environment_manifest: ""
result: null
```

Do not backfill the hypothesis or success threshold after seeing candidate results.

## Phase 1 — Establish the finding

### 1.1 Reproduce before redesigning

Convert the suspected weakness into a concrete reproduction whenever feasible.

A useful reproduction identifies:

- triggering task or state;
- expected behavior;
- observed behavior;
- exact evidence of the mismatch;
- whether the failure is deterministic, intermittent, or environment-dependent.

If the issue cannot be reproduced, record that uncertainty. Do not invent architecture to solve a hypothetical failure without evidence that its expected value justifies the cost.

### 1.2 Verify novelty

Before calling a weakness new, inspect:

- current implementation;
- tests;
- workflow contracts;
- hooks and permissions;
- relevant rules, skills, and agent definitions;
- audit behavior;
- current first-party Claude Code semantics when version-sensitive.

A missing prose statement is not a finding if executable behavior already enforces the property adequately.

### 1.3 Identify the control type

Classify the failure before choosing a mechanism:

| Failure type | Preferred control |
| --- | --- |
| Always-on project fact or invariant | concise `CLAUDE.md` policy |
| Path-specific instruction | scoped rule |
| Conditional multi-step procedure | skill |
| Agent specialization | agent definition |
| Must-not-happen tool behavior | permission / capability restriction / hook |
| Deterministic state transition | workflow code / schema |
| Completion fact | executable verification / grader |
| Repeated cross-session learning | memory only if benchmark contamination is not a concern |

Use this mapping as a default, not a substitute for measurement.

## Phase 2 — Form the experimental contract

Before editing, write a falsifiable hypothesis in this form:

> Because `<cause>`, the current control plane produces `<failure or waste>`. Changing `<specific mechanism>` should improve `<primary observable metric>` by at least `<minimum worthwhile effect>` while preserving `<guardrails>`.

### 2.1 Choose one primary metric

The primary metric should directly measure the targeted property.

Examples:

- proportion of tasks ending in externally verified success;
- false-success rate;
- stale-evidence bypass rate;
- number of required human interventions;
- median cost among successful trials;
- median tool calls among successful trials;
- success rate under a fixed cost budget;
- always-loaded context tokens;
- number of active orchestration mechanisms removed under a non-inferiority constraint.

Do not choose a proxy when the outcome can be measured directly.

### 2.2 Declare a minimum worthwhile effect

Specify how much improvement is worth the complexity and migration cost.

Examples:

- eliminate a known deterministic bypass;
- improve verified task success by at least 5 percentage points on the targeted capability suite;
- reduce median cost per successful task by at least 15% with no meaningful success regression;
- remove one orchestration layer while keeping success within a declared non-inferiority margin.

The threshold must be chosen before candidate results are known.

### 2.3 Declare guardrails

Guardrails are properties that must remain within bounds even if the primary metric improves.

Common guardrails:

- zero protected-path or permission-boundary violations;
- zero false-success regressions on the relevant suite;
- regression suite remains above its required threshold;
- no material increase in cost or latency beyond the declared budget;
- no new unrecoverable workflow states;
- no loss of required audit evidence.

A hard guardrail failure rejects the candidate regardless of aggregate score.

## Phase 3 — Freeze the baseline

Before the candidate change, capture a baseline manifest.

At minimum record:

- git commit and dirty-tree diff;
- Claude Code version;
- model identifier;
- effort level;
- permission mode;
- command-line flags;
- project, local, user, and managed setting sources that affect the run;
- enabled hooks;
- enabled MCP servers and plugins;
- relevant environment variables;
- auto-memory state;
- `CLAUDE_CONFIG_DIR` or equivalent configuration isolation;
- OS and architecture;
- CPU and memory allocation/limits when relevant;
- concurrency;
- per-task timeout;
- network/egress constraints;
- benchmark task-set version;
- grader version;
- evaluator commit or digest.

Baseline and candidate must use matched settings unless the experiment explicitly changes one of them.

### 3.1 Use fresh processes

Run each serious benchmark trial in a fresh Claude Code process.

Do not validate startup-loaded instruction changes only inside the session that edited them.

For automated experiments, prefer non-interactive fresh invocations with structured output and explicit model/effort/settings rather than inherited interactive state.

### 3.2 Isolate persistent state

Unless persistent memory is the experimental variable:

- disable auto memory during benchmark trials; or
- give every trial an isolated, empty memory/config directory.

Prevent previous trials from leaking state through:

- auto memory;
- transcripts;
- caches when they change behavior;
- git history created by prior trials;
- shared worktrees;
- generated files;
- local settings;
- prior benchmark output.

### 3.3 Keep authentication separate from experimental state

If configuration isolation is used, provide credentials through a controlled mechanism without copying unrelated user configuration into the trial environment.

## Phase 4 — Build or select the evaluation suite

Do not evaluate every change with one undifferentiated benchmark.

Maintain distinct suites.

### 4.1 Regression suite

Purpose: prove that behavior already considered reliable remains reliable.

Characteristics:

- expected pass rate near 100%;
- stable, unambiguous tasks;
- deterministic graders where practical;
- every material production/control-plane failure should graduate into this suite once fixed.

### 4.2 Capability suite

Purpose: create headroom for measurable improvement.

Characteristics:

- contains tasks the current control plane sometimes fails;
- spans the behaviors the control plane is expected to improve;
- should not be permanently saturated;
- successful mature cases can graduate to regression coverage.

### 4.3 Adversarial integrity suite

Purpose: test false-success and bypass behavior.

Include cases such as:

- attempting an invalid workflow transition;
- modifying relevant files after evidence is captured;
- attempting to reuse stale evidence;
- verifier encountering a failing test;
- agent attempting a prohibited write;
- implementation that prints success while leaving the outcome incorrect;
- alternate command/path that bypasses the intended hook;
- malformed or partial evidence;
- interrupted or timed-out execution;
- intentionally misleading but plausible model assertions.

For deterministic controls, include mutation-style tests that deliberately try to cross the boundary.

### 4.4 Efficiency suite

Purpose: measure overhead on tasks that do not need maximum orchestration.

Include easy, medium, and complex tasks. A control plane that helps only hard tasks but taxes every easy task may be a net regression.

Measure successful-task cost rather than raw cost alone whenever possible.

### 4.5 Held-out suite

Purpose: detect overfitting, benchmark gaming, and optimizer-specific tuning.

For major experiments:

- keep some tasks outside the candidate-readable checkout;
- keep hidden grader data outside the candidate's tool-accessible environment;
- do not expose previous held-out transcripts to the optimizer;
- rotate or refresh held-out tasks when contamination is suspected.

The held-out suite should test the same capability distribution as the visible development suite without reusing exact answers. Split by task family when near-duplicates could leak the solution pattern across partitions.

### 4.6 Development versus confirmatory evaluation

Use visible development tasks for iteration. Use held-out tasks for confirmation, not hill-climbing.

Before the confirmatory run:

- freeze the candidate commit;
- freeze grader and harness versions;
- freeze success thresholds and analysis rules;
- record the experiment manifest.

If the candidate is changed because of a held-out result, that held-out observation has become development information. Do not present a second run on the same exposed cases as independent confirmation; use fresh held-out cases or label the result as iterative development evidence.

For model-based graders, hide baseline/candidate identity and implementation details when they are not needed for grading.

## Phase 5 — Validate tasks and graders

A benchmark is itself software and can be wrong.

Before trusting a task:

1. ensure the task statement contains the information needed to satisfy the grader;
2. produce or retain a known reference solution when practical;
3. verify the reference solution passes;
4. verify an intentionally bad solution fails;
5. check that alternate valid solutions are not accidentally rejected;
6. distinguish agent failure from infrastructure failure;
7. inspect grader edge cases and timeouts.

Prefer grading outcomes over requiring one exact trajectory.

Use deterministic graders for objective properties. Use model-based graders only where deterministic grading cannot capture the desired quality, and calibrate those graders against human judgment or fixed reference cases.

Model graders should be narrow, rubric-driven, and allowed to return `unknown` or `insufficient evidence` rather than invent confidence.

## Phase 6 — Choose the smallest credible candidate

Generate at least one deletion or simplification candidate when relevant.

Before adding a mechanism, ask:

1. Can the failure be solved by deleting conflicting instructions or redundant machinery?
2. Can an existing deterministic control be tightened?
3. Can existing behavior be routed correctly rather than adding another agent/state?
4. Can a conditional procedure move out of always-loaded context?
5. Can a native Claude Code capability replace custom machinery with equal or stronger guarantees?
6. Can a prompt rule be converted into a capability boundary if it must always hold?

If multiple candidates are plausible, prefer an ablation ladder instead of changing several mechanisms at once.

Example:

1. baseline;
2. baseline minus suspected unnecessary mechanism;
3. smallest replacement;
4. larger redesign only if the smaller candidate fails.

This makes causal attribution possible.

## Phase 7 — Implement without contaminating the experiment

- Preserve unrelated working-tree changes.
- Add or update behavioral coverage for the targeted invariant.
- Do not modify benchmark expectations merely to match the candidate.
- Keep candidate changes coherent and minimal.
- Record any unplanned experimental variable introduced during implementation.
- If the candidate requires changing both the subject and evaluator, split those into separate commits or experiments when possible.

After the final behavior-changing edit, run repository verification required by `CLAUDE.md`.

## Phase 8 — Run the comparison

### 8.1 Match conditions

Baseline and candidate must use the same experimental budget and the same:

- task inputs;
- model and effort;
- Claude Code version;
- permissions;
- external tools;
- resource limits;
- timeout;
- evaluator;
- network policy;
- initial repository state;
- memory policy.

Any intentional difference must be named as an experimental variable. If the candidate intentionally changes resource consumption, evaluate both quality under a matched resource budget and efficiency at comparable achieved quality when practical.

Stop a run early when a predeclared hard invariant is violated and continuing cannot add useful diagnostic evidence. Record the early stop rather than silently dropping the trial.

### 8.2 Repeat trials

Agent behavior is stochastic. Do not infer broad improvement from one run.

Default trial guidance:

- deterministic enforcement reproductions: repeat until bypass behavior is convincingly characterized;
- localized Class B changes: at least 3 trials per stochastic targeted task when cost permits;
- Class C/D changes: normally at least 5 trials per key stochastic task, with more trials when observed differences are small or variance is high.

These are starting points, not magic numbers. Increase trials when the decision is near the threshold.

### 8.3 Pair and randomize

Run baseline and candidate on the same task set.

When service load or time-of-day effects could matter:

- interleave baseline and candidate runs;
- randomize which one runs first per task;
- spread trials across more than one time window when practical.

Do not run all baseline trials under one environment condition and all candidate trials under another if those conditions may differ.

For high-impact experiments, include at least one unrelated negative-control task family when practical. A candidate targeted at delegation, for example, should not mysteriously improve an unrelated deterministic permission test; unexplained movement can indicate harness drift or contamination.

### 8.4 Capture complete trial data

For every trial, preserve enough information to reconstruct the result:

- task ID and variant;
- baseline/candidate identity;
- environment manifest digest;
- start/end timestamps;
- exit status;
- final repository or environment outcome;
- grader outputs;
- tool/agent trace or transcript reference;
- cost and token metadata when available;
- wall time;
- tool-call count;
- agent invocation count;
- human intervention count;
- infrastructure-error classification;
- failure classification.

Never count an infrastructure failure as evidence of agent capability without labeling it separately.

## Phase 9 — Grade outcomes independently

Prefer this order of evidence:

1. final external state;
2. deterministic tests or assertions;
3. static analysis or schema checks;
4. transcript-derived evidence;
5. model judgment;
6. subject's own claim.

A statement such as "all tests pass" is not evidence if the tests did not run or their outputs are unavailable.

### 9.1 False-success metric

Track false success explicitly:

> false success = subject reports or transitions to completion while an authoritative grader says the task is incomplete or invalid.

False-success rate is a first-class control-plane metric and should normally be a hard guardrail.

### 9.2 Evidence freshness metric

For workflows that cache evidence, test whether evidence remains valid after relevant state changes.

The grader should distinguish:

- current valid evidence;
- stale evidence correctly invalidated;
- stale evidence incorrectly accepted;
- evidence that cannot be tied to an actual command or result.

## Phase 10 — Inspect traces

Aggregate scores are insufficient.

Inspect:

- every unexpected guardrail violation;
- every infrastructure error;
- every baseline/candidate disagreement on a targeted reproduction;
- representative successes;
- representative failures;
- unusually cheap or expensive runs;
- suspiciously perfect held-out performance.

Ask whether the candidate improved the intended mechanism or merely discovered a shortcut in the grader.

For major experiments, an auditor who did not implement the candidate should review a sample when practical.

## Phase 11 — Analyze effect and uncertainty

Report both absolute performance and change from baseline.

At minimum report:

- task/trial counts;
- success rate or primary metric for baseline;
- success rate or primary metric for candidate;
- absolute and relative delta where meaningful;
- variation across trials;
- infrastructure-error rate;
- guardrail results;
- efficiency deltas;
- observed outliers.

Do not report excessive decimal precision unsupported by the sample size.

For larger experiments, use an appropriate uncertainty estimate such as paired bootstrap confidence intervals, a paired binary test, or another method suited to the metric. Pair by task whenever baseline and candidate see the same cases.

Statistical significance is not a substitute for practical significance. A tiny but significant gain may not justify added complexity.

## Retention decision

Classify the result as **accept**, **reject**, or **inconclusive**.

### Accept

Accept only when all are true:

- the targeted failure or waste is demonstrably improved;
- the primary metric meets the predeclared minimum worthwhile effect, or a deterministic defect is eliminated;
- all hard guardrails pass;
- important regressions are absent;
- efficiency is within the declared budget;
- the mechanism is the simplest credible intervention demonstrated to work;
- evidence is strong enough for the experiment class.

### Reject

Reject when any are true:

- the targeted effect does not reproduce;
- a hard guarantee regresses;
- the candidate relies on benchmark-specific behavior rather than solving the underlying problem;
- cost or complexity exceeds the declared budget without sufficient benefit;
- the observed gain disappears under matched or repeated trials;
- the evaluator cannot distinguish true improvement from contamination.

### Inconclusive

Mark inconclusive when:

- observed effects are within noise;
- trial count is inadequate for the effect size;
- environment drift compromised comparability;
- grader validity is uncertain;
- results conflict across suites without an explained tradeoff.

The default action for an inconclusive additive change is revert or do not merge.

A simplification may be retained under a predeclared non-inferiority rule if quality remains within tolerance and complexity or cost is measurably reduced.

## Special protocol: simplification and deletion

Complexity is a recurring tax and must periodically re-earn its existence.

For an existing mechanism, run an ablation:

> current control plane vs. current control plane minus the mechanism

Delete the mechanism when:

- required guarantees remain intact;
- primary quality metrics stay within the declared non-inferiority margin;
- complexity, context, cost, latency, or maintenance burden improves materially.

Examples of ablation targets:

- agent roles;
- workflow states;
- hooks;
- duplicated rules;
- always-loaded instructions;
- planner or verifier passes;
- custom machinery now duplicated by native Claude Code capabilities.

Do not assume a mechanism remains valuable because it was valuable for an older model or earlier Claude Code version.

## Special protocol: changes to enforcement

When modifying a deterministic safety or correctness boundary:

1. define the protected invariant;
2. enumerate known entry points and alternate paths;
3. add positive tests for allowed behavior;
4. add negative tests for blocked behavior;
5. add bypass attempts using alternate commands/tools/paths;
6. test error and timeout behavior;
7. confirm failure is visible to the main session;
8. confirm the control cannot be silently bypassed by changing runtime state that should be protected.

Never weaken a valid boundary solely to improve benchmark completion rate.

## Special protocol: changes to evaluators or benchmarks

Evaluator changes are high-risk because they can manufacture apparent progress.

When modifying a grader, task, or harness:

- preserve the pre-change evaluator;
- validate reference good and bad cases against both versions;
- report candidate performance under the old evaluator and new evaluator where meaningful;
- explain every score change caused by the grader rather than the subject;
- do not retroactively redefine success because the candidate found an inconvenient valid path;
- do revise an evaluator when evidence shows it is genuinely wrong, ambiguous, brittle, or gameable.

A grader fix and a subject improvement should be reported as separate effects.

## Special protocol: self-modifying instructions and configuration

When the candidate changes startup-loaded behavior such as root `CLAUDE.md`, settings, permissions, or other startup configuration:

- the editing session is not a valid candidate trial;
- launch fresh baseline and candidate processes from clean states;
- verify which instructions and settings actually loaded;
- avoid inherited personal configuration unless intentionally part of the product environment.

When benchmarking configuration selection itself, include the active configuration sources in the evidence.

## Special protocol: model or Claude Code upgrades

Do not attribute a model or platform upgrade to a control-plane change.

When the model or Claude Code version changes materially:

1. establish a new baseline on the unchanged control plane;
2. rerun critical regression and capability suites;
3. rerun selected ablations of expensive orchestration components;
4. remove scaffolding that no longer provides measurable lift;
5. record any semantic changes to native tools, agents, hooks, skills, or configuration that invalidate prior assumptions.

Model upgrades are opportunities to simplify the harness.

## Benchmark integrity and anti-gaming rules

The optimizer must not:

- read held-out expected answers;
- read hidden grader logic when the evaluator can isolate it;
- search for benchmark answer keys;
- use prior held-out transcripts as hints;
- modify evaluator data during subject execution;
- treat benchmark identity discovery as task progress;
- weaken a grader merely to obtain a better candidate score.

For serious held-out evaluations, prefer an evaluator architecture where:

- the subject receives only the task and production-equivalent tools;
- hidden tasks/graders live outside the subject-readable filesystem;
- grading occurs after subject execution;
- evaluator credentials and control files are not available to the subject;
- trial artifacts are copied out after the run rather than exposed in advance.

Treat suspicious benchmark-aware behavior as contamination and invalidate affected trials unless the benchmark explicitly intends to measure that behavior.

## Failure taxonomy

Classify failures rather than collapsing everything into pass/fail.

Recommended categories:

- `subject_reasoning` — incorrect decision or plan;
- `subject_execution` — correct intent, failed implementation/action;
- `verification` — failed to verify or interpreted evidence incorrectly;
- `false_success` — claimed completion despite failed outcome;
- `orchestration` — delegation/state/control-flow failure;
- `permission_or_hook` — enforcement misbehavior;
- `context_or_memory` — stale, missing, or contaminated context;
- `grader` — evaluation defect;
- `task_spec` — ambiguous or invalid task;
- `infrastructure` — resource, service, network, sandbox, or harness failure;
- `timeout` — budget exhausted without classification above;
- `contamination` — benchmark/evaluator information leaked to the subject.

Track whether the candidate changes the distribution of failure categories, not only the aggregate success rate.

## Efficiency accounting

For each successful trial, capture when available:

- total cost;
- input tokens;
- output tokens;
- cache usage if exposed;
- tool calls;
- agent calls;
- wall time;
- verification commands;
- retries;
- human interventions.

For control-plane comparisons, report at least:

- success rate;
- median cost per successful task;
- median wall time per successful task;
- median tool calls per successful task;
- human intervention rate.

If a candidate increases success by spending substantially more, state the tradeoff directly.

## Complexity accounting

Every additive candidate must declare its complexity cost.

Useful proxies include change in:

- always-loaded instruction lines or estimated tokens;
- number of active agents;
- number of active hooks;
- number of skills/rules loaded for the affected task;
- workflow states and transitions;
- deterministic branches;
- configuration surfaces;
- schemas or persisted runtime objects;
- new dependencies;
- tests required to defend the mechanism.

These are proxies, not a universal complexity score. Use them to make hidden orchestration tax visible.

## Continuous eval maintenance

The evaluation suite is a product, not a one-time artifact.

After an accepted fix:

- add the original failure as regression coverage when practical;
- add a nearby negative/alternate case to prevent overfitting;
- preserve the causal reproduction;
- retire redundant cases only when equivalent coverage remains.

When a capability suite saturates:

- promote stable tasks to regression;
- add harder or more realistic variants;
- test longer-horizon and cross-cutting work;
- avoid making tasks obscure merely for difficulty.

Periodically audit the suite for:

- ambiguity;
- leaked answers;
- stale assumptions;
- invalid environment requirements;
- grader brittleness;
- duplicate tasks;
- missing negative cases;
- mismatch with real repository work.

## Recommended comparator set

Use the smallest comparator set that answers the causal question.

Possible comparators:

- `current` — current committed control plane;
- `candidate` — proposed change;
- `ablation` — current minus the mechanism under question;
- `native` — simpler/native Claude Code mechanism when relevant;
- `bare` — reduced control-plane baseline when useful for measuring total harness lift.

Do not compare against `bare` merely for a dramatic score if production never operates that way. Comparators must answer a real design question.

## Required closeout

Every completed experiment must produce a concise report.

### Finding

What concrete failure mode or wasted resource was observed?

### Baseline

What happened before the change, under what environment, and with what confidence?

### Hypothesis

Why should the candidate affect the targeted metric?

### Candidate

What changed, and why was it the smallest credible intervention?

### Evaluation

What tasks, graders, trials, environment controls, comparators, and budgets were used?

### Results

Report the primary metric, guardrails, efficiency, failure categories, and uncertainty.

### Trace audit

What did representative successes/failures show? Was there evidence of grader gaming, contamination, or an alternate explanation?

### Decision

`accepted`, `rejected`, or `inconclusive`.

### Simplicity

What machinery was added, removed, or made unnecessary?

### Guarantees

Which important guarantees remain intact, and what evidence demonstrates that?

Finish with:

> What measurable or behaviorally demonstrated property is better than the baseline, what important guarantees remain intact, what did the improvement cost, and why is this the simplest mechanism that achieved the result?

## Minimum acceptance checklist

Before retaining a behavior-changing control-plane improvement, verify all applicable items:

- [ ] The failure or waste was concretely reproduced.
- [ ] Existing repository behavior was inspected before claiming novelty.
- [ ] The experiment class was declared.
- [ ] The causal hypothesis was written before implementation.
- [ ] One primary metric was declared.
- [ ] A minimum worthwhile effect or non-inferiority margin was declared.
- [ ] Hard guardrails were declared.
- [ ] Baseline environment and configuration were captured.
- [ ] Baseline and candidate ran in fresh, matched processes.
- [ ] Persistent state and auto memory were isolated or intentionally controlled.
- [ ] Regression coverage exists for the targeted behavior.
- [ ] Capability coverage has enough headroom to measure improvement when applicable.
- [ ] Adversarial/bypass paths were tested when relevant.
- [ ] Trials were repeated for stochastic behavior.
- [ ] Infrastructure failures were separated from subject failures.
- [ ] Complete outcomes and grader evidence were captured.
- [ ] Representative traces were inspected.
- [ ] Efficiency deltas were measured for Class C/D changes.
- [ ] Held-out validation was used for high-impact changes when feasible.
- [ ] The evaluator was not silently changed to favor the candidate.
- [ ] Repository-level verification passed after the final edit.
- [ ] The final diff contains no unintended changes.
- [ ] The result was classified as accepted, rejected, or inconclusive.
- [ ] Accepted fixes produced durable regression coverage.
- [ ] The final report answers the required closeout question.

## Default posture

The control plane should become stronger by becoming more empirically justified, not merely larger.

Every mechanism is provisional.

Every guarantee should live at the strongest appropriate enforcement layer.

Every important failure should become reproducible.

Every retained change should improve a measured outcome or remove cost without meaningful regression.

Every major model or platform improvement should trigger fresh ablation pressure against old scaffolding.

When evidence does not distinguish a more complex design from a simpler one, choose the simpler design.
