# Glossary — Building Great Skills

The domain model for what makes a skill great. A skill exists to wrangle determinism out of a stochastic system; the root virtue is **Predictability**, and every term below is a lever on it. This is the disclosed reference for [`writing-great-skills`](SKILL.md).

The terms are grouped by axis: **Invocation** (how a skill is reached), **Information Hierarchy** (how its content is arranged), **Steering** (how the agent's runtime behaviour is shaped), and **Pruning** (how it is kept lean). Each **failure mode** lives beside the lever that cures it, tagged _failure mode_.

**Bold terms** in any definition are themselves defined in this glossary; find them by their heading.

## Predictability

Stability of desired behavioral properties across repeated runs and task-preserving variations of the input. Measure it over representative tasks using perturbations such as paraphrase, ordering, formatting, irrelevant context, and sampling variation. Predictability concerns stability of the required behavior, not identical generated text.

_Avoid_: consistency, reliability, robustness, output-determinism

## Invocation

How a skill is reached — and the two loads you pay for the choice.

### Model-Invoked

A capability made available for autonomous model selection by the surrounding runtime, typically through visible metadata such as a name, description, schema, or retrieved representation. Visibility makes invocation possible but does not guarantee reliable selection; measure invocation precision and recall empirically.

_Avoid_: ability, tool, capability

### User-Invoked

A capability whose activation requires an explicit human action and which is excluded from autonomous model selection by the runtime. This trades model-side discovery overhead for human-side discovery and selection effort.

_Avoid_: procedure, workflow, command

### Description

Natural-language metadata used by a model or routing system to infer the purpose, applicability, and use of a capability. Effective descriptions contain discriminative cues that distinguish the capability from alternatives. Evaluate descriptions through invocation precision, recall, and downstream task success.

_Avoid_: frontmatter, summary

### Context Pointer

A compact cue used to decide whether and where to retrieve additional instructions or reference material. Its quality is measured by retrieval/invocation precision and recall. For required information, compare pointer-based retrieval against inlining rather than assuming either is universally superior.

_Avoid_: link, reference, import

### Context Load

The performance and resource burden imposed by material active in the model's context. It depends on amount, relevance, position, redundancy, similarity among competing items, and number of active behavioral constraints—not token count alone.

_Avoid_: token cost, context bloat

### Cognitive Load

Human effort required to discover, remember, distinguish, select, and invoke available capabilities. Measure it where relevant using selection errors, task time, recall, abandonment, or validated subjective workload measures.

_Avoid_: human index, burden, overhead

### Router

An index, classifier, retriever, or human-facing guide that reduces a larger capability set to a smaller set of relevant candidates before final selection. Evaluate it by routing accuracy, selection effort, and end-to-end success.

_Avoid_: dispatcher, menu, registry, index, router procedure

### Granularity

The scope assigned to each capability or instruction module. Choose granularity by balancing routing ambiguity, active context/constraint load, human discoverability, reuse, and the benefits or costs of task decomposition. Determine the optimum empirically for representative tasks.

_Avoid_: chunking, modularity

## Information Hierarchy

How a skill's content is arranged, and how far down the ladder each piece sits.

### Information Hierarchy

Arrangement of context so information needed for the current decision or action is salient, while conditional or lower-priority material is retrieved or presented only when useful. The hierarchy should be validated against alternatives because optimal ordering varies by model and task.

_Avoid_: structure, organization, layout

### Steps

Explicitly ordered subgoals used when decomposing a task improves reliability, observability, or tool coordination. Each step should have a success condition. Use decomposition when validated against a simpler end-to-end formulation.

_Avoid_: workflow, instructions, choreography

### Reference

Nonprocedural information that may be required to perform or evaluate a task, such as definitions, facts, examples, schemas, or constraints. Include or retrieve it according to demonstrated relevance rather than by default.

_Avoid_: supporting material, docs, background

### External Reference

Authoritative task information stored outside the active skill prompt and retrieved when needed. Its quality depends on source authority, retrieval accuracy, freshness, and preservation of task-critical detail.

_Avoid_: doc, resource, knowledge base

### Progressive Disclosure

Present or retrieve information when it becomes relevant rather than keeping all potentially useful information active at once. It is beneficial when it lowers distraction or selection burden without hiding information needed for correct action.

_Avoid_: lazy loading, chunking

### Co-location

Placing information that must be jointly interpreted near enough that the model is likely to consider it together. Use co-location as a default heuristic, but test alternative arrangements for important behaviors because positional effects are model- and task-dependent.

_Avoid_: grouping, clustering, cohesion

### Sprawl

Excess active material whose inclusion measurably harms retrieval, instruction adherence, selection, latency, maintainability, or cost. Sprawl is relative to task and model; diagnose it through ablation or context-scaling tests rather than line count.

_Avoid_: bloat, length, size, verbosity

## Steering

The levers that shape the agent's runtime behaviour toward **Predictability**.

### Branch

A conditionally applicable task path requiring materially different instructions, tools, evidence, or success criteria. A branch justifies separate context when it can be reliably identified and the separation improves end-to-end performance.

_Avoid_: path, case, fork

### Leading Word

A compact semantic cue intended to bias behavior toward a pretrained concept or pattern. Because cue effects vary by model and task, a leading word earns its place only when ablation shows that it improves the target behavior relative to a literal instruction or no cue.

_Avoid_: keyword, term, motif

### Completion Criterion

An explicit condition whose satisfaction determines whether a task or step is complete. Strong criteria are understandable, sufficiently demanding, and independently verifiable. When possible, decompose them into individually checkable constraints or rubric items.

_Avoid_: done condition, exit condition, stopping rule

### Legwork

Observable task-relevant activity undertaken before declaring completion, such as searches, file inspections, tool calls, tests, evidence collection, or coverage of required cases. Operationalize legwork through observable actions or coverage measures rather than inferred internal effort.

_Avoid_: scope, effort, diligence, coverage

### Post-Completion Steps

Planned actions that follow the current step. Their visibility may affect current-step behavior through planning or instruction competition, but the direction and magnitude of the effect are task-dependent and should be tested.

_Avoid_: horizon, fog of war, lookahead

### Premature Completion

Terminating a task or step while one or more stated completion criteria remain unsatisfied. Diagnose it behaviorally. Possible causes include ambiguous criteria, planning failures, instruction competition, insufficient search, context limitations, or tool failures; causal attribution requires experiment.

_Avoid_: premature closure, the rush, rushing, shortcutting

### Negative Constraint

An instruction specifying behavior, content, or conditions to exclude. LLMs can be less reliable on some forms of linguistic negation, but explicit negative constraints can also improve performance. Prefer an equivalent positive specification when it is clearer; retain explicit exclusions when the exclusion itself is important, and compare formulations empirically.

_Avoid_: ironic rebound, don't-prompting, the pink elephant

## Pruning

Keeping a skill lean — each remedy paired with the failure it cures.

### Single Source of Truth

A maintenance principle under which one location is authoritative for a behavioral rule or fact. Other occurrences should reference or derive from it where possible. Deliberate redundant presentation is permitted when needed for runtime robustness, provided the authoritative source remains unambiguous.

_Avoid_: home, canonical location

### Duplication

Repeated expression of substantively equivalent information. It creates maintenance and context costs and can create inconsistencies, but deliberate repetition may improve salience or robustness. Treat duplication as harmful when it adds no measured benefit, creates divergence risk, or distorts instruction priority.

_Avoid_: repetition, redundancy

### Relevance

The expected contribution of an instruction or reference item to successful performance on the current task distribution. Irrelevant context can distract models even when superficially related. Evaluate relevance through retrieval quality, ablation, or measured downstream contribution.

_Avoid_: load-bearing, staleness, freshness

### Sediment

Instructions or reference material retained after their measurable contribution has disappeared or their assumptions have become stale. Detect it through periodic freshness review, behavioral regression tests, and ablation rather than age alone.

_Avoid_: accretion, bloat, cruft, rot

### No-Op

An instruction whose removal or modification does not materially worsen the target behavioral metrics over a representative evaluation set. Determine no-op status by controlled ablation with repeated trials and uncertainty estimates, not by judging whether the instruction sounds useful.

_Avoid_: redundant instruction, restating the obvious, belaboring
