# Glossary — Claude Code Project Subagents

The domain model for reliable project-scoped custom subagents. A subagent file is a **Delegation Contract**: routing, capability, context, execution, and return are separate levers. The root virtue is **Delegation Reliability** — similar tasks reliably reach the intended worker, within the intended boundary, and produce a usable result.

## Architecture

### Delegation Contract

The complete behavioral contract formed by an agent's frontmatter, Markdown body, project-visible context, and runtime controls. It has four observable promises: the agent is selected for the right tasks, gets sufficient but bounded capability, finishes against a verifiable criterion, and returns what the parent needs.

_Avoid_: persona, bot profile, assistant definition

### Delegation Reliability

The repeatability of the contract rather than identical textual output. A reliable agent may take different valid paths on different runs, but should preserve the same task boundary, capability boundary, evidence standard, completion bar, and return shape.

_Avoid_: determinism, consistency alone

### Fresh-Context Tax

The cost paid when work is delegated: a new context must be initialized, task context must be transferred, the worker must rediscover project facts, and the parent receives a compressed result rather than shared state. Isolation must earn this cost through context savings, specialization, parallelism, or a stronger capability boundary.

_Avoid_: latency only, overhead only

### Context Handoff

The information that crosses from parent to worker through the delegation task plus worker-visible project context. A strong handoff contains task-specific facts the worker cannot reliably rediscover; durable policy remains in version-controlled worker-visible sources.

_Avoid_: prompt, instructions

### Return Contract

The explicit shape and scope of the worker's final result to the parent. It should contain the decision, evidence, changed artifacts, verification result, and unresolved risk the parent actually needs—not the full exploration trace.

_Avoid_: output format alone, summary

## Routing

### Routing Surface

The model-visible metadata used by the parent to decide whether a custom agent fits the task, dominated by the agent `description`. The body is not a substitute for this surface: a perfect worker prompt cannot help if the router never selects it.

_Avoid_: metadata, description text

### Trigger Set

The concrete classes of tasks that should delegate to an agent. Trigger language should resemble user requests, codebase terminology, and neighboring workflow language rather than generic expertise claims.

_Avoid_: keywords, synonyms

### Exclusion Boundary

A concise statement of a neighboring task that should not route to this agent, used only where real ambiguity exists. The positive route should remain primary; exclusions exist to separate adjacent workers, not to enumerate everything the agent does not do.

_Avoid_: negative prompt, blacklist

### Route Bleed

_Failure mode._ A description attracts tasks owned by another agent or the main conversation. Often caused by broad identity claims (“expert backend engineer”), overlapping trigger sets, or too many “proactive” use cases. Cure by partitioning responsibilities or merging indistinguishable agents.

_Avoid_: false positive only

### Route Starvation

_Failure mode._ Tasks that fit the agent repeatedly stay in the main conversation or route elsewhere. Causes include weak trigger language, competition with another agent, current-model delegation policy, unavailable agent discovery, or a description that describes expertise rather than when to delegate.

_Avoid_: false negative only

### Explicit Selection

A direct user or orchestrator reference to a specific subagent, bypassing the uncertainty of autonomous route choice. Use it in authoring tests to separate “is this worker good?” from “does the router choose this worker?”

_Avoid_: automatic delegation

## Capability

### Capability Surface

The actual operations exposed to the worker after Claude Code resolves available tools, allow/deny frontmatter, permissions, MCP servers, hooks, and runtime mode. The capability surface should be the smallest surface that can still satisfy the contract.

_Avoid_: tool list alone

### Capability Leak

_Failure mode._ The worker can take actions unrelated to its job. This increases ambiguity and blast radius even when the prompt says not to use the extra capability.

_Avoid_: tool sprawl

### Capability Gap

_Failure mode._ The worker's contract requires an operation its resolved capability surface cannot perform. A narrow surface is only good if the task remains completable.

_Avoid_: missing tool only

### Hard Boundary

A runtime restriction enforced outside natural-language compliance: tool absence, permissions, hooks, worktree isolation, sandboxing, or environment controls. Use hard boundaries for safety, destructive actions, or requirements that must not depend on prompt obedience.

_Avoid_: instruction, warning

### Soft Steering

Natural-language behavior in the agent body. It is appropriate for method, prioritization, evidence, style, and judgment. It is not enforcement.

_Avoid_: policy enforcement

### Prompt Enforcement

_Failure mode._ Treating soft steering as though it were a hard boundary. “Never deploy,” “do not edit,” or “only read” can guide behavior, but if violation matters, capability controls must make the undesired action unavailable or intercept it.

_Avoid_: guardrail

## Context

### Preload Tax

Recurring context consumed every time a preloaded skill, MCP tool description, or other always-present material is injected into a worker. Preloads are justified by frequent need, not mere possible relevance.

_Avoid_: token cost alone

### Context Assumption

_Failure mode._ Worker instructions depend on parent transcript state that is not part of the worker's fresh context. Symptoms include “as discussed above,” invisible earlier constraints, or a worker that succeeds only after unusually detailed delegation messages.

_Avoid_: missing context

### Project Truth

A repository-visible source that the worker can inspect and that should outrank mutable recollection: code, tests, schemas, configuration, ADRs, or version-controlled instructions. Good prompts make workers verify important task facts against project truth.

_Avoid_: context file

### Memory Sediment

_Failure mode._ Persistent agent memory accumulates old observations, one-off workarounds, or duplicated policy until stale notes compete with current project truth. Cure with a clear memory purpose and active pruning.

_Avoid_: memory bloat

### Replica Drift

_Failure mode._ One behavioral rule is independently copied into several control surfaces—agent body, skill, `CLAUDE.md`, hook output, documentation—and diverges over time. Keep one authoritative source and use pointers where possible.

_Avoid_: duplication only

## Execution and completion

### Evidence Standard

The evidence a worker must obtain before it can make or return a claim: files inspected, tests executed, logs read, documentation checked, or source locations cited. It converts vague diligence into a checkable expectation.

_Avoid_: be thorough

### Completion Criterion

The observable condition that makes the delegated task done. Strong criteria describe verified state (“targeted tests pass and no new diagnostics remain”) rather than activity (“review the code carefully”).

_Avoid_: stopping rule alone

### Verification Contract

The set of checks that prove the agent's claimed outcome. It may include tests, lint/type checks, command output, source citations, diff inspection, or explicit uncertainty where verification is impossible.

_Avoid_: self-check

### Return Flood

_Failure mode._ The worker returns so much raw exploration that the parent pays the context cost the subagent was meant to avoid. The cure is a return contract that separates evidence needed for the decision from disposable working detail.

_Avoid_: verbosity alone

### Nesting Explosion

_Failure mode._ A subagent recursively delegates without a bounded decomposition need, multiplying coordination cost and making responsibility opaque. Nesting is justified when workers own separable subproblems with explicit return contracts, not as a generic “more agents is better” strategy.

_Avoid_: parallelism

## Files and scope

### Project Agent Tree

All `.claude/agents/` definitions Claude Code discovers for the current project path, including recursively scanned subfolders and nested project directories discovered on the path toward the repository root. Human folder organization does not change a project agent's identity; `name` does.

_Avoid_: agents directory only

### Shadowing

_Failure mode._ More than one discovered definition declares the same agent name, so a higher-priority or nearer definition wins. Within the same scope tree, duplicate resolution may rely on filesystem read order rather than a semantic rule. Prevent shadowing with globally unique project-agent names and diagnostics.

_Avoid_: override alone

### Frontmatter Fragility

_Failure mode._ An agent relies on YAML that is technically clever, ambiguous, or only accidentally accepted by a particular Claude Code parser version. Conservative scalars, explicit lists, and post-upgrade load checks reduce this risk.

_Avoid_: invalid YAML only

### Schema Drift

The change over time in supported frontmatter fields, defaults, model behavior, discovery rules, or system prompt behavior. Because Claude Code evolves quickly, stable authoring principles belong in `SKILL.md`; volatile mechanics belong in the dated `REFERENCE.md` and should be re-verified after upgrades.

_Avoid_: version change
