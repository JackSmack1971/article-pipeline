# Glossary — Writing Great Dynamic Workflows

A dynamic workflow turns multi-agent orchestration into inspectable code. The root virtue is **Controlled Scaling**: increase breadth, depth, and autonomy only where independence, verification, and value justify them.

**Bold terms** in definitions are themselves defined here.

## Controlled Scaling

The property of adding agentic compute only where it produces measured value under a bounded cost and risk envelope. It rejects “more agents” as a default. A workflow is controlled when its width, depth, stop conditions, verification, and replay behavior are explicit.

_Avoid_: maximum parallelism, swarm size, agent count as quality

## Plan in Code

The defining workflow move: branching, loops, fan-out, and intermediate state live in the JavaScript runtime instead of being recreated by Claude turn by turn. Agents still exercise judgment inside their assigned work units; the script determines the orchestration shape.

_Avoid_: prompt chain as prose, hidden orchestration

## Orchestration Shape

The dependency structure the script executes: **Chain**, **Fan-out / Fan-in**, **Propose / Verify**, **Evaluator / Optimizer**, or **Saturation Loop**. Choose shape from the dependency graph, not from stylistic preference.

_Avoid_: architecture for its own sake

## Independence Graph

A map of what each work unit reads, writes, returns, and depends on. It determines which edges may safely run in parallel. Parallel tasks that mutate the same state without isolation are not independent even if their prompts look unrelated.

_Avoid_: task list, superficial decomposition

## Work Unit

One agent invocation with a bounded objective, defined inputs, output contract, and inspectable label. Good work units are large enough to amortize agent startup and small enough to verify, replay, and attribute.

_Avoid_: agent role, persona

## Structured Contract

A schema-defined hand-off between an agent and downstream code. It turns model output into fields that control flow can consume without reparsing prose. Contracts should make required information explicit and keep optionality deliberate.

_Avoid_: format suggestion, JSON-ish prose

## Cost Envelope

The planned upper bound on agent count, rounds, expensive stages, and acceptable token/time spend for a workflow. It includes a **Pilot Slice** used to test the topology before scaling.

_Avoid_: budget guess, unlimited until done

## Pilot Slice

The smallest representative subset that exercises the same orchestration shape as the intended run. A pilot should be large enough to expose coordination and verification failures but cheap enough to throw away.

_Avoid_: toy example with different topology

## Verification Gap

The difference between generating at least one correct candidate and reliably identifying it. Parallel sampling often widens the candidate set faster than it improves selection. A workflow closes the gap with an **Oracle**, not merely more votes.

_Avoid_: consensus equals truth

## Oracle

Evidence capable of discriminating correct from plausible-but-wrong results. Strong oracles are executable tests, known-good implementations, invariants, or direct evidence. An LLM verifier can be useful when it independently inspects the underlying artifact, but is weaker when it only rereads another model's conclusion.

_Avoid_: reviewer count, confidence score

## Diversity

Meaningful variation in evidence, role, criteria, or reasoning path across parallel agents. Repeating the same prompt several times may increase sampling but can preserve correlated errors. Diversity earns cost only when the aggregation stage can exploit it.

_Avoid_: decorative personas

## Saturation Loop

An iterative search that stops when a measurable round contributes no new information (or after a hard maximum). The semantic stop condition is the point; “repeat until good” is not a saturation loop.

_Avoid_: infinite refinement, vibes-based done

## Progress Test

A stable comparison between rounds that can detect improvement, stalling, or regression. Examples: remaining error set, failing test identifiers, count of novel findings, or objective metric. A hard round cap is a safety bound; a progress test is the semantic stopping rule.

_Avoid_: round counter alone

## Replay Frontier

The first unfinished agent in start order during workflow resume. Cached reuse stops there; agents started later rerun even if they had completed. Designs with expensive side effects should assume work beyond the frontier may execute again.

_Avoid_: exactly-once assumption

## Replay-Safe

A work unit whose re-execution does not corrupt state or invalidate the workflow. Replay safety can come from idempotent operations, isolated workspaces, verification before mutation, stable identifiers, or explicit checks for already-applied state.

_Avoid_: “probably won't rerun”

## Substrate Mismatch

Assuming the workflow file is an ordinary Node.js program. Claude's workflow runtime is a purpose-built JavaScript environment with injected orchestration primitives and runtime constraints. A Node parser, package import, filesystem API, or shell call is not authoritative merely because it is valid JavaScript elsewhere.

_Avoid_: Node equivalence, syntax-check = runtime-check

## Contract Drift

A failure mode where an agent prompt, schema, and downstream code no longer agree about what a stage returns. It often appears after incremental edits where one side changes but the other does not.

_Avoid_: permissive parsing as a cure

## Accidental Serialism

Independent work runs sequentially because the script awaits each work unit before starting the next. This spends latency without buying correctness. Fix it only when the **Independence Graph** proves the work can safely overlap.

_Avoid_: blanket no-await-in-loop rule

## False Parallelism

Work is launched concurrently even though agents contend on the same files, mutable state, or prerequisite. It often creates merge conflicts, duplicated effort, or nondeterministic end state.

_Avoid_: fan-out by default

## Version Sediment

Old workflow facts copied forward after Claude Code behavior changes. Dynamic workflows have changed trigger behavior, save semantics, defaults, UI behavior, and distribution support across versions. Store dated implementation facts in evidence/reference material and re-check them before turning them into hard rules.

_Avoid_: folklore, issue-thread API documentation
