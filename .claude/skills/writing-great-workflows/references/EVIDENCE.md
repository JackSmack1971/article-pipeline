# Evidence Basis — Claude Code Dynamic Workflows

**Research snapshot:** 2026-08-03

This file is deliberately dated. Dynamic workflows are a fast-moving Claude Code feature. Treat the official runtime documentation as the source of truth for current mechanics and the empirical literature as evidence about design choices, not as an API specification.

## Evidence tiers

- **Tier A — current documented mechanism:** official Claude Code / Anthropic documentation describing current product behavior.
- **Tier B — Anthropic empirical engineering:** measured or field-tested findings published by Anthropic; strong design evidence but often domain-specific.
- **Tier C — external empirical research:** benchmark or controlled-study evidence; useful for challenging assumptions, but transfer to Claude Code workflows is not automatic.
- **Tier D — language/specification guidance:** JavaScript / JSON Schema semantics that apply where the workflow runtime follows standard JavaScript behavior.
- **Observed field report:** GitHub issue or practitioner report. Use to generate hypotheses and regression tests, never as the sole basis for a hard API rule.

## Current documented mechanism (Tier A)

### A1. A workflow moves the plan into code

The official docs distinguish workflows from subagents, skills, and agent teams by who owns the plan. A workflow runtime executes a JavaScript script, keeps intermediate results in script variables, and makes orchestration repeatable. This is the core architectural fact the skill should preserve.

Source: https://code.claude.com/docs/en/workflows

### A2. The runtime is deliberately constrained

Current docs state:

- dynamic workflows require Claude Code v2.1.154+;
- the body is plain JavaScript with top-level `await`;
- `agent()` spawns a subagent and `pipeline()` runs one per item;
- `agent()` can return `null` on stop or unrecoverable API error;
- the workflow script itself has no direct filesystem or shell access; agents do I/O;
- up to 16 agents may run concurrently (fewer on CPU-constrained machines);
- a run can spawn at most 1,000 agents;
- arbitrary mid-run user input is unavailable except permission prompts.

Source: https://code.claude.com/docs/en/workflows

### A3. Resume is start-order-sensitive, not exactly-once

Current docs describe resume as replaying cached results until the first unfinished agent in start order. Agents started after that frontier rerun even if they had already finished. Resume only works in the same Claude Code session; a new session starts fresh.

Design implication: side-effecting work after the replay frontier should be replay-safe, and giant individual agents are expensive interruption points.

Source: https://code.claude.com/docs/en/workflows

### A4. Cost is an explicit product concern

Current docs recommend piloting a small slice before a large run. Claude Code warns when a workflow exceeds an agent-count/token projection threshold and supports size guidelines (`small`, `medium`, `large`, `unrestricted`) as advice rather than hard caps. As of v2.1.219 the documented default is `medium`.

Source: https://code.claude.com/docs/en/workflows

### A5. Workflows are now distributable

Current docs support project and personal saved workflows, hierarchical `.claude/workflows/` resolution, and plugin-packaged workflows with namespace-qualified commands. This is a useful example of why old community claims must be revalidated against the installed/current version.

Source: https://code.claude.com/docs/en/workflows

### A6. Skills, subagents, teams, and workflows are different control surfaces

Skills supply reusable procedural knowledge. Subagents provide isolated worker contexts. Agent teams provide peer sessions that communicate and coordinate. Workflows move control flow into a script. Choosing among them is part of workflow design, not a prelude to it.

Sources:
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/agent-teams

## Anthropic empirical engineering (Tier B)

### B1. Multi-agent gains can be very large on breadth-first work — and very expensive

Anthropic reported that its multi-agent research system (Opus 4 lead, Sonnet 4 subagents) outperformed single-agent Opus 4 by 90.2% on an internal research evaluation. In the same article, token use explained 80% of BrowseComp performance variance in their analysis; multi-agent systems used roughly 15× the tokens of chat interactions. Anthropic explicitly cautioned that domains with shared context and many dependencies — including many coding tasks — are a poorer fit.

The same report gives practical orchestration lessons: define clear subagent objectives/output/boundaries, scale effort to task complexity, parallelize genuinely independent searches, add guardrails, trace behavior, and evaluate outcomes rather than requiring a single prescribed trajectory.

Source: https://www.anthropic.com/engineering/multi-agent-research-system

### B2. Simple composable patterns are the default

Anthropic's “Building effective agents” article distinguishes predefined workflows from model-directed agents and recommends the simplest architecture that works. It describes prompt chaining, routing, parallelization (sectioning/voting), orchestrator-workers, and evaluator-optimizer as common composable patterns. It explicitly frames cost/latency as trade-offs for added performance.

Source: https://www.anthropic.com/engineering/building-effective-agents

### B3. Long-running coding autonomy depends on the verifier and environment

Anthropic's 2026 compiler experiment used 16 parallel agents across nearly 2,000 Claude Code sessions and about $20,000 in API cost to produce a roughly 100,000-line Rust C compiler capable of building Linux 6.9 on multiple architectures. The author attributes much of the enabling work to high-quality tests, isolation, synchronization, concise feedback, progress visibility, and specialization. The article stresses that a weak verifier lets autonomous agents optimize the wrong problem.

Source: https://www.anthropic.com/engineering/building-c-compiler

## External empirical research (Tier C)

These are research papers/preprints, not Claude Code product specifications. Use them to pressure-test architecture choices.

### C1. Parallel scaling exposes a verification gap

General AgentBench (2026) evaluates general agents across search, coding, reasoning, and tool use. The authors report that parallel sampling raises the probability a correct trajectory exists, but agents often fail to identify it; sequential scaling also saturates or degrades after a context ceiling. This directly motivates a separate verification design rather than treating fan-out as self-validating.

Source: https://arxiv.org/abs/2602.18998

### C2. Fixed multi-agent systems often fail to beat a matched single-agent baseline

BenchAgent (2026 preprint) normalizes tool access, usage accounting, and answer contracts across several workflows. Under its substrate-internal evaluation, at most one of six tested fixed/evolving multi-agent systems exceeded the matched single-agent anchor on benchmark-balanced average accuracy; five were both less accurate and more expensive. A separate Claude-Code-style runtime workflow performed strongly on a GAIA snapshot, reinforcing that topology/substrate fit matters more than agent count alone.

Source: https://arxiv.org/abs/2606.05670

### C3. Diversity can matter more than debate structure

A controlled multi-agent debate study (2025 preprint) found intrinsic reasoning strength and group diversity were dominant factors, while majority pressure could suppress independent correction. This argues for differentiated evidence/criteria and an oracle, not decorative personas or blind majority voting.

Source: https://arxiv.org/abs/2511.07784

### C4. Procedural skills plus live grounding can reduce cost

DataFlow-Harness (2026 technical report) combined skills, MCP grounding, and typed incremental pipeline construction. On a 12-task data-engineering benchmark it reported a 93.3% observed end-to-end pass rate, 72.5% lower monetary cost and 49.9% lower generation latency than Vanilla Claude Code, while remaining within 0.9 percentage points of a context-aware baseline. The paper reports skills were particularly useful where construction depended on implicit procedural knowledge.

This is not a dynamic-workflow benchmark, but it supports a core design choice for this skill: encode durable procedural expertise in the skill while grounding runtime facts in live/current interfaces.

Source: https://arxiv.org/abs/2607.16617

## JavaScript and schema guidance (Tier D)

### D1. Prefer `const` when a binding is not reassigned

MDN notes that many style guides, including MDN's, recommend `const` over `let` when the binding is not reassigned. This is a clarity tool, not immutability: object contents can still change.

Source: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const

### D2. Parallelize independent async work; preserve sequential dependencies

MDN documents `Promise.all()` as a concurrency combinator that preserves result order and fails fast. ESLint's `no-await-in-loop` explains why awaiting independent operations in a loop can accidentally serialize them, while explicitly documenting cases where sequential awaiting is correct. In Claude workflows, runtime-native orchestration primitives should take precedence when they express the same intent because they carry product-specific observability/replay semantics.

Sources:
- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all
- https://eslint.org/docs/latest/rules/no-await-in-loop

### D3. Use nullish defaults and optional access deliberately

Optional chaining short-circuits on `null`/`undefined`. Nullish coalescing (`??`) applies a default only to those nullish values, preserving valid falsy values such as `0` and `false`.

Sources:
- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining
- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing

### D4. JSON Schema is an executable structural contract

JSON Schema Draft 2020-12 defines structural validation vocabulary including object `required` properties. Workflow schemas should use required fields for values downstream code depends on, while remembering that structural validity is not semantic correctness.

Source: https://json-schema.org/draft/2020-12/json-schema-validation

## Conflicting evidence and how the skill resolves it

### “Parallelize more” vs “more agents usually do not help”

There is no universal contradiction. Anthropic's strongest multi-agent results are on breadth-first research with genuinely separable directions and high information volume. General-agent benchmarks find weak gains when candidate selection/verification is poor or when tasks share context and dependencies. The skill therefore requires an **Independence Graph**, **Cost Envelope**, and **Oracle** before scaling.

### Voting as a quality pattern vs majority pressure

Anthropic's general agent-pattern guidance lists voting as a useful form of parallelization, while controlled debate research shows majority pressure can suppress correction. The skill treats voting as a hypothesis to evaluate, not a universal verifier. Deterministic evidence and independent verification outrank consensus.

### Generic JavaScript concurrency vs workflow-native orchestration

Standard JS guidance says independent async work should not be accidentally serialized. Claude's workflow runtime adds tracking, caps, and resume semantics around agent orchestration. The skill therefore adopts the JavaScript principle (parallelize independence) without assuming generic `Promise.all()` is always the best substrate-specific expression.

## Field reports: useful, not authoritative

- GitHub issue #79127 reports lost completed work after resuming a large fan-out in a way consistent with the currently documented start-order replay frontier. Because the docs now specify the behavior, the docs are the rule and the issue is corroboration only.
  https://github.com/anthropics/claude-code/issues/79127
- GitHub issue #66032 requested plugin distribution for workflows. Current official docs now support plugin-packaged workflows, so this issue demonstrates **Version Sediment**: a once-valid limitation can become false while remaining easy to rediscover.
  https://github.com/anthropics/claude-code/issues/66032

## Design conclusions carried into the skill

1. **Topology before code.** The dependency graph selects the pattern.
2. **Parallelism by independence.** Width is not a quality metric.
3. **Typed hand-offs.** Structured contracts reduce coordination ambiguity.
4. **Verification is architecture.** Fan-out without a discriminating oracle widens the verification gap.
5. **Bound both cost and loops.** Pilot small, then scale only on measured gains.
6. **Replay is part of correctness.** Side effects must tolerate reruns beyond the replay frontier.
7. **Runtime facts are dated.** Revalidate product mechanics before turning them into hard skill rules.
8. **Evaluate end state.** A different valid trajectory is not a failure; an elaborate trace is not a success.
