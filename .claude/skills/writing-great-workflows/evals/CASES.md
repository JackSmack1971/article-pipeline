# Eval Cases — `writing-great-workflows`

These cases test decisions, not just whether the skill can emit JavaScript. A strong run should refuse unnecessary orchestration, choose a topology from dependencies, define a verifier, and surface version-sensitive assumptions.

## Case 1 — Unnecessary workflow

**Prompt:** “Use a dynamic workflow to rename one private helper in one file and update its two call sites.”

**Expected behavior:** Recommend a normal Claude Code turn or small subagent, not a workflow. Explain that there is no orchestration decision worth moving into code.

## Case 2 — Read-only fan-out

**Prompt:** “Audit 180 route handlers for missing authorization and report only confirmed issues.”

**Expected behavior:** Fan-out by independent route/file, structured candidate findings, independent verification against code, bounded pilot slice first, explicit null/unverified handling.

## Case 3 — Conflicting writes

**Prompt:** “Migrate 60 components in parallel; they all edit the same shared theme file.”

**Expected behavior:** Identify false parallelism. Isolate per-component work or serialize the shared-file phase; do not blindly run one writer per component against shared mutable state.

## Case 4 — Open-ended repair loop

**Prompt:** “Keep asking agents to fix TypeScript until everything is perfect.”

**Expected behavior:** Replace vague infinity with an authoritative checker, semantic progress fingerprint, hard maximum rounds, and an explicit stalled state.

## Case 5 — Majority-vote trap

**Prompt:** “Run 15 identical security reviewers and accept anything 8 of them vote for.”

**Expected behavior:** Flag verification gap and correlated errors. Prefer role/evidence diversity plus deterministic or independent verification. Require evidence that 15 agents outperform a smaller topology before paying the cost.

## Case 6 — Node substrate mismatch

**Prompt:** “Write a workflow that imports `node:fs`, scans the repo directly, and uses `child_process.exec` for tests.”

**Expected behavior:** Reject direct workflow I/O and delegate reads/shell/test execution to agents. Do not claim a Node syntax check validates Claude's runtime.

## Case 7 — Resume hazard

**Prompt:** “Launch 100 agents that each publish an external side effect; I may pause halfway and resume later.”

**Expected behavior:** Surface same-session resume and start-order replay behavior; redesign side effects to be idempotent/check-before-write or split into a verified collection stage plus controlled commit stage.

## Case 8 — Empirical optimization

**Prompt:** “Our 12-agent review workflow feels expensive. Make it better.”

**Expected behavior:** Establish baseline metrics, pilot representative cases, ablate width/verifier/schema/model choices, compare success and false-positive rate against a smaller or single-agent baseline, and keep only measured gains.

## Suggested grader dimensions

Score 0-2 each:

1. **Abstraction choice** — chooses workflow only when orchestration shape warrants it.
2. **Dependency reasoning** — distinguishes true from false parallelism.
3. **Contracts** — uses structured outputs where control flow depends on model results.
4. **Verification** — closes the verification gap with evidence, not confidence alone.
5. **Boundedness** — explicit caps and semantic stop conditions.
6. **Replay safety** — accounts for interruption and duplicate execution.
7. **Runtime grounding** — distinguishes current docs from community observations.
8. **Empiricism** — proposes measurable baseline/evals/ablations.
9. **JavaScript clarity** — readable state, null handling, stable ordering, minimal mutation.
10. **Economics** — treats tokens/latency as first-class outcome dimensions.

A passing workflow-design response should score at least 16/20 and must not score 0 on Runtime grounding, Verification, or Boundedness.
