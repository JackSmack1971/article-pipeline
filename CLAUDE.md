Article Pipeline Control Plane
==============================

Purpose
-------

This repository is the implementation and active development environment for a Claude Code article-production control plane.

The product is not generic software-engineering orchestration. It is a research-to-publication pipeline for sourced long-form articles that routes work by topic complexity, uses adversarial research where warranted, verifies claims before drafting, audits prose during and after drafting, challenges complex articles after drafting, simulates the target reader, prepares SEO delivery artifacts, and learns from completed runs.

Optimize for:

* publishable article quality and factual/citation integrity;
* adversarial independence where it improves epistemic quality;
* faithful handling of user-approved thesis and conflict decisions;
* target-audience clarity, accessibility, and editorial coherence;
* deterministic artifact/state correctness where judgment is not required;
* lower tokens, searches, tool calls, latency, rework, and unnecessary human intervention.

Prefer the simplest mechanism that improves those outcomes while preserving required guarantees. Additional agents, skills, gates, counters, schemas, or abstractions must address a concrete article-pipeline failure mode and justify their cost.

Product contract
----------------

The canonical end-to-end procedure is `.claude/skills/multi-agent-article-pipeline/SKILL.md`.

`pipeline_config.json` routes each run as `SIMPLE`, `STANDARD`, or `COMPLEX`. Do not force maximum orchestration onto every article; depth is a product decision made by triage.

All run artifacts live under `.agents/artifacts/`. Do not create duplicate working copies elsewhere.

`scripts/pipeline_runner.py` owns deterministic stage transitions, gate/counter mutation, word-count synchronization, and finalization. `scripts/validate_artifacts.py` is the canonical persisted-artifact validator. `scripts/artifact_contract.py` defines shared artifact-contract logic.

`COMPLETE` may be entered only through runner finalization after the validator reports the run publishable. Never hand-edit `pipeline_state.json`, `artifact_manifest.json`, counters, or stage values to manufacture completion.

A `PUBLISHABLE` validator result proves the persisted artifact contract and configured publication blockers are clear. It does **not** by itself prove that the article is factually strong, well written, appropriately balanced, or useful to its target audience; those properties are established by the research, fact-check, QA, red-team, reader, and SEO stages and must be evaluated separately when improving the control plane.

Sources of truth
----------------

Use the narrowest authoritative source for the question at hand:

1. **User intent:** the topic brief, confirmed thesis, approval-gate responses, and `conflict_decisions.json` govern editorial intent.
2. **Pipeline orchestration:** `.claude/skills/multi-agent-article-pipeline/SKILL.md` governs stage order, routing, delegation, and handoffs.
3. **Artifact contracts:** `.claude/skills/multi-agent-article-pipeline/references/pipeline-schemas.md` plus `scripts/artifact_contract.py` govern persisted shapes and invariants.
4. **Deterministic state:** `scripts/pipeline_runner.py` and `scripts/validate_artifacts.py` govern transitions and persisted completion status.
5. **Stage-specific judgment:** the relevant article skill governs research, fact-checking, drafting/QA, red-team, reader simulation, or SEO behavior.
6. **Isolation-sensitive workers:** `.claude/agents/article-advocate.md`, `article-skeptic.md`, and `article-red-team.md` govern their bounded roles and capabilities.
7. **Current run state:** `.agents/artifacts/` records what actually happened; `.agents/knowledge/article-pipeline/` records cross-run learning.
8. **Claude Code semantics:** use `docs-control-plane/claude-code-docs/AGENT_INDEX.md` and the captured first-party page, checking current official documentation when freshness materially matters.

Executable behavior outranks prose for deterministic claims. Explicit user decisions outrank inferred editorial preferences. Surface disagreements instead of silently choosing whichever source is convenient.

Pipeline invariants
-------------------

The main Claude session owns end-to-end orchestration and artifact handoffs.

Use subagents only where isolation is part of the product value. The current isolation-sensitive roles are advocate, skeptic, and red team:

* advocate and skeptic research independently;
* skeptic may receive the advocate's Source URL Index only, never the advocate's claims, confidence judgments, or framing;
* red team receives only the thesis and conclusion, never the full draft;
* do not weaken these boundaries merely to save tokens or simplify delegation.

Other pipeline personas may run in the orchestrating context when they legitimately require shared artifacts.

Fact-check outputs govern claim status at drafting time. `claims_for_drafting.md` supersedes stale claim-status notes in `article_spec.md` when they disagree.

Do not fabricate sources, URLs, quotations, author credentials, publisher metadata, dates, or missing evidence. Preserve explicit uncertainty and `[TODO:]`/review states where the contract permits them.

Do not silently resolve research conflicts. Implement `conflict_decisions.json` exactly, including neutral presentation and unresolved status.

Evidence recorded in artifacts must correspond to research, verification, audit, or user decisions that actually occurred. Relevant edits must not leave dependent state, counts, manifests, or completion evidence falsely current.

A failed kill condition, blocked audit, invalid transition, or publication blocker is repaired or surfaced; it is never bypassed.

Control-plane improvement
-------------------------

When auditing, simplifying, benchmarking, or changing the article control plane, read `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` before editing.

Treat the article pipeline as the product under test. Code tests alone are not sufficient evidence for a change intended to improve article quality or orchestration quality.

For behavioral experiments:

* reproduce the concrete article-pipeline failure or waste first;
* compare baseline and candidate in fresh, isolated Claude sessions when loaded instructions, skills, agents, model behavior, or persistent memory can affect the result;
* use matched article briefs and matched environment/budget conditions;
* evaluate across the pipeline depths and content conditions the change can affect;
* measure externally graded article outcomes, not only whether the subject says it succeeded;
* retain deterministic tests for state, artifact, and capability boundaries;
* keep benchmark/eval outputs outside `.agents/artifacts/` so experiments cannot corrupt a real article run;
* do not train against held-out answers, hidden grader logic, or prior held-out transcripts;
* include deletion/ablation candidates when existing scaffolding may no longer earn its cost.

The default top-level article metric is **qualified publish rate**: the proportion of runs that satisfy the deterministic artifact contract **and** independently meet the experiment's factual/editorial quality thresholds without an undeclared human rescue. Use a narrower primary metric when the change targets one subsystem.

Hard guardrails normally include no fabricated citations or metadata, no known-disputed/outdated claim presented as verified fact, no silent conflict-resolution drift, no adversarial-isolation violation, no false `COMPLETE`, and no bypass of required human gates.

Change method
-------------

For behavior-changing control-plane work:

1. identify the article outcome, invariant, or wasted resource being changed;
2. inspect the relevant skill/agent/script plus existing tests and completed-run evidence;
3. add or update deterministic regression coverage where objective behavior changes;
4. make the smallest coherent intervention at the strongest appropriate control layer;
5. run focused unit tests while iterating;
6. if the change can alter generated articles, run the evaluation required by the improvement protocol rather than treating unit tests as proof of quality;
7. inspect the final diff and verify that article artifacts or learned knowledge were not unintentionally changed;
8. update affected skill contracts, schemas, agent definitions, and documentation together.

Do not refactor unrelated pipeline machinery merely to satisfy stylistic preference.

Verification
------------

For repository code changes, run:

    python3 -m unittest discover -s tests -p 'test_*.py'

When the current `.agents/artifacts/` run is relevant to the change, also run:

    python3 scripts/validate_artifacts.py --artifact-root .agents/artifacts --json

Do not treat validation of one existing article as evidence that a general orchestration change improves future articles.

If required verification or an article benchmark cannot run, report the exact limitation and reduce the claimed evidence level accordingly.

Change safety
-------------

Preserve unrelated working-tree changes.

Do not use destructive Git operations to solve local development problems.

Do not expose secrets or weaken credential protections.

Treat `.agents/artifacts/` as live article-run state. Do not manually edit it to make a gate, validator, or benchmark pass unless the task explicitly concerns that artifact and the edit is part of the tested production path.

Treat `.agents/knowledge/article-pipeline/` as cross-run product memory. Do not write benchmark-specific hints, held-out answers, or one-off experimental artifacts into it.

Do not commit transient benchmark/evaluation output unless explicitly required.

Definition of done
------------------

A control-plane change is complete only when the requested behavior exists, relevant deterministic verification actually ran, failures are visible, affected contracts agree, the final diff contains no unintended changes, and the evidence level matches the strength of the claim being made.

For a control-plane improvement, finish by answering:

> What measurable article-pipeline property improved over the baseline, what factual/editorial and control-plane guarantees remained intact, what did the improvement cost, and why is this the simplest mechanism that achieved the result?
