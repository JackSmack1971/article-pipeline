Claude Code Control Plane
=========================

Purpose
-------

This repository is both the implementation and the active development environment for a Claude Code orchestration control plane.

Optimize for:

* correctness and observable task success;

* evidence quality and reproducibility;

* deterministic enforcement where model judgment is not required;

* auditability and maintainability;

* lower tokens, tool calls, context use, latency, rework, and human intervention.

Prefer the simplest mechanism that preserves required guarantees. Additional agents, hooks, skills, rules, workflow states, or abstractions must address a concrete failure mode and justify their cost.
Policy model
------------

Treat prompt instructions as guidance and executable controls as enforcement.

If a guarantee must hold regardless of model judgment, enforce it with the appropriate deterministic mechanism: workflow code, permissions, hooks, sandboxing, schemas, or tests.

Do not claim a behavior is enforced because it appears in prose or configuration. Verify the executable path and realistic bypass paths.

If implementation, tests, documentation, and intended design disagree, surface the disagreement explicitly.
Sources of truth
----------------

For Claude Code platform semantics, use `docs-control-plane/claude-code-docs/AGENT_INDEX.md` and the captured first-party page. Check the current official source when freshness could affect the decision.

For current repository behavior, inspect executable code, settings, hooks, schemas, agent and skill definitions, and behavioral tests. Executable behavior outranks prose.

For intended behavior, use the explicit user requirement, `docs/ARCHITECTURE.md`, `orchestration/workflow.json`, relevant contracts, and `docs/AUDIT-COMPLIANCE.md`.

`scripts/workflow.py` is the deterministic workflow-state authority. Runtime state and evidence live under `.workflow/`.
Orchestration invariants
------------------------

The main Claude session owns end-to-end control flow unless an explicitly adopted project mechanism says otherwise.

Delegated agents perform bounded jobs and return bounded results. Role boundaries must be enforced in agent capabilities when practical, not only described in prompts.

Workers must not recursively orchestrate. Researchers gather evidence. Critics diagnose. Implementers execute one approved atomic task at a time. Verifiers independently assess evidence and do not silently repair failures.

Evidence must come from commands or observations that actually occurred. Relevant changes invalidate stale evidence.

A rejected workflow transition is repaired, not bypassed. Completion requires observable evidence, not a model assertion.

For non-trivial repository changes, invoke the project `workflow` skill.
Control-plane improvement
-------------------------

When the task audits, simplifies, benchmarks, or changes the control plane, read `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` before editing and follow the project control-plane-improvement skill if present.

Treat every control-plane change as an experiment:

* state the concrete failure mode or wasted resource;

* establish a baseline before the candidate change when feasible;

* test baseline and candidate in fresh, isolated Claude sessions when startup-loaded configuration is involved;

* hold model, effort, permissions, repository state, configuration sources, memory state, and resource limits constant unless the experiment intentionally varies them;

* use the same acceptance criteria for baseline and candidate;

* prefer outcome-based graders and independent verification;

* run enough trials to distinguish a real improvement from stochastic or infrastructure noise;

* test regressions, bypasses, false-success paths, and stale-evidence behavior;

* retain the change only when evidence shows net value and required guarantees remain intact.

Do not let the candidate control plane validate itself solely through its own changed instructions.

Do not inspect, modify, or optimize against held-out benchmark answers or hidden grader data. Do not weaken or rewrite a grader merely to make the candidate pass. If evaluator logic must change, report that separately and compare against the pre-change evaluator as well.

Deletion and simplification are first-class candidates. Do not preserve machinery merely because it already exists.

Native Claude Code orchestration features are candidate mechanisms, not authorities. Adopt or replace project mechanisms only when controlled evaluation shows a better tradeoff.
Change method
-------------

For behavior-changing work:

1. identify the invariant or observable behavior;

2. inspect the existing implementation and behavioral coverage;

3. add or update regression coverage;

4. make the smallest coherent change;

5. run focused checks while iterating;

6. after the final behavior-changing edit, run `make verify`;

7. inspect the final diff and working-tree status;

8. update affected contracts, architecture, compatibility, schema, manifest, or compliance documentation.

Use proportional judgment for small documentation-only changes.

If verification cannot run, report the exact environmental limitation. Never weaken a valid test, permission boundary, control, or gate merely to obtain a pass.
Change safety
-------------

Preserve unrelated working-tree changes.

Do not use destructive Git operations to solve local development problems.

Do not expose secrets or weaken protections around credentials or protected paths.

Treat `.workflow/` as runtime state; do not manually alter it to make a gate pass.

Do not commit transient runtime or benchmark data unless explicitly required.
Definition of done
------------------

A change is complete only when the requested observable behavior exists, relevant verification actually ran, failures are visible, evidence is current, deterministic gates still represent the guarantees they claim, implementation and documentation agree, and the final diff contains no unintended changes.

For a control-plane improvement, finish by answering:

> What behaviorally demonstrated or measured property improved over the baseline, what important guarantees remain intact, what did the improvement cost, and why is this the simplest mechanism that achieved the result?
