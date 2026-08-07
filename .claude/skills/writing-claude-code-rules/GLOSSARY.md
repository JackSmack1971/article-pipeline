# Glossary — Claude Code Project Rules

This glossary supplies the domain model used by [`SKILL.md`](SKILL.md). The organizing principle is **Instruction Yield**: useful behavioral change per token and per activation.

## Placement

### Instruction Yield

The behavioral value produced by an instruction relative to the context it consumes and the situations in which it is active. A concise path-scoped rule with a strong behavioral effect has high instruction yield; a generic always-on paragraph Claude could infer from the codebase has low yield.

Instruction yield combines three questions: does the instruction change behavior, does it load only when useful, and is its wording compact enough to preserve attention for the task itself?

### Behavioral Delta

The difference in Claude's likely behavior caused by an instruction. The practical deletion test is: if this sentence disappears, does a relevant mistake become more likely? If not, the sentence is probably derivable, decorative, or a **no-op**.

### Rule Map

An inventory of all instruction files capable of affecting a target: location, activation timing, scope, and topic. Its purpose is to expose conflicts and duplication before editing. It is not a directory listing; only instruction-bearing artifacts belong on it.

### Procedure

A repeatable task sequence whose value appears only when a particular workflow is requested. Procedures belong in skills rather than always-on rules because their steps need not occupy context during unrelated work.

### Enforcement Boundary

A behavior that must hold independent of model interpretation. Permissions, hooks, sandboxing, and deterministic scripts create enforcement boundaries. `CLAUDE.md` and rule files do not; they influence behavior probabilistically.

## Scope

### Scope Envelope

The smallest stable set of files for which a rule is true. A good `paths:` list approximates this envelope closely: broad enough to catch every intended file, narrow enough not to inject irrelevant guidance elsewhere.

### Semantic Locality

The degree to which a rule's meaning naturally belongs to a code region. “Every database migration is reversible” has strong locality to migration files. “Use pnpm for this repository” has project-wide locality. Scope should follow semantic locality, not the author's preference for tidy folders.

### Context Tax

The recurring token and attention cost of content loaded even when irrelevant. Unscoped `.claude/rules/*.md` files pay the same kind of recurring tax as root project instructions. Splitting them into more files changes maintenance structure, not the total tax.

### Read-Triggered Context

Instructions whose activation is caused by Claude reading a matching file. Path-scoped rules and nested instruction files can enter context lazily. This is useful for conditional guidance but is not equivalent to a pre-write policy gate.

### Activation Gap

A situation where an instruction is semantically relevant before the event that would cause Claude Code to load it. Creating a brand-new file in a path-scoped area is the clearest example: if no matching file has yet been read, the conditional rule should not be treated as guaranteed guidance. The remedy is a minimal always-on breadcrumb or mechanical enforcement when required.

### Spillover

A rule entering context for files where its guidance is not true or useful. Over-broad globs create spillover, which lowers instruction yield and can introduce accidental conflicts.

## Writing

### Signal Density

The proportion of a rule file that materially changes decisions. Concrete invariants, commands, and project-specific exceptions are signal. Generic engineering advice, tutorials, dependency lists, and codebase facts Claude can cheaply inspect are usually noise.

### Atomic Rule

One instruction that governs one observable behavior. Atomicity makes conflicts easier to detect and edits easier to reason about. A bullet that specifies naming, testing, error handling, and architecture simultaneously is not atomic.

### Verifiable Rule

A rule whose success can be observed from code, command output, or a concrete action. “Use `ruff check` on touched Python files” is verifiable. “Keep code clean” is not.

### Positive Target

A description of the behavior Claude should produce, rather than only naming the behavior to avoid. A hard prohibition can still be appropriate, but it is stronger when paired with the replacement pattern: “Use `Result<T, E>` for recoverable failures; exceptions are reserved for invariant violations.”

### Local Rationale

A short explanation colocated with a rule when the reason helps Claude generalize to edge cases. Rationale should pay rent by changing interpretation; historical background that does not affect decisions is documentation, not a rule.

### Exemplar Pointer

A stable path to existing code that demonstrates the desired pattern. It often carries more useful detail than reproducing a long example in an always-loaded instruction file. The exemplar must be maintained enough that it does not become a stale authority.

### No-Op

An instruction that fails the behavioral-delta test because Claude already does it by default or can infer it immediately from the repository. No-ops consume context without buying reliability.

## Interaction

### Single Source of Truth

A state where one active instruction location owns each behavioral rule. Other files may point to that location or define a narrower exception, but they do not independently restate the same meaning.

### Conflict Surface

The set of active instructions that speak to the same behavior. A large conflict surface increases the chance that Claude receives contradictory guidance. Load order may influence attention, but it is not deterministic configuration precedence.

### Counter-Prompting

Adding a new rule whose purpose is to cancel an irrelevant or stale rule that should instead be removed, narrowed, or excluded. Counter-prompting compounds context tax and makes the ruleset harder to reason about.

### Delivery Failure

The rule was not in context when needed: wrong location, unmatched `paths:`, invalid glob, exclusion, disabled setting source, or lazy activation that never fired. Fix discovery or activation rather than prose.

### Adherence Failure

The rule was present but Claude did not follow it. Common causes are ambiguity, conflict, excess context, weak behavioral delta, or ordinary model variance. Confirm delivery before diagnosing adherence.

### Emphasis Escalation

Adding stronger lexical emphasis such as `IMPORTANT` or `MUST` only after a concrete, well-scoped rule has failed representative evaluation. Emphasis is an empirical tuning move, not a default formatting style.

## Maintenance

### Instruction Debt

The accumulated cost of stale, duplicated, overly broad, or procedural content living in persistent instructions. A good refactor deletes more instruction debt than it adds.

### Rule Drift

The mismatch that appears when code conventions change but instruction files do not. Drift is especially dangerous for exemplar pointers and duplicated rules because they can continue sounding authoritative after the repository has moved on.

### Scope Drift

A change in repository layout that makes a previously accurate `paths:` pattern too broad, too narrow, or dead. Path-scoped rules need periodic validation when directories are renamed or packages split.
