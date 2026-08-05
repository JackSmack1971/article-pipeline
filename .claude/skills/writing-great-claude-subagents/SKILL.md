---
name: writing-great-claude-subagents
description: Reference for designing and editing reliable Claude Code project-scoped custom subagents in .claude/agents/.
disable-model-invocation: true
---

A project subagent file is a **delegation contract**. The parent conversation decides _when_ to delegate, Claude Code constrains _what the worker can do_, and a fresh context decides _how_ to do the work. The root virtue is **delegation reliability**: the same kinds of tasks reach the same worker, inside the intended capability boundary, and return an outcome the parent can use.

**Bold terms** are defined in [`GLOSSARY.md`](GLOSSARY.md). For version-sensitive Claude Code mechanics and the current frontmatter surface, consult [`REFERENCE.md`](REFERENCE.md). For empirical validation, use [`EVALS.md`](EVALS.md).

## First decision: should this be a subagent?

A subagent pays a **fresh-context tax**: startup, delegation, a separate context window, and a compressed return to the parent. Pay that tax only when isolation earns it.

Prefer a project subagent when at least one is true:

- **Context isolation** is the point: exploration, logs, search results, or implementation detail would otherwise crowd the main conversation.
- A repeatable task needs a distinct **capability surface**: narrower tools, a different model, worktree isolation, scoped MCP, hooks, or a dedicated permission mode.
- The task is self-contained enough to finish behind a **return contract**, rather than requiring frequent back-and-forth with the parent.
- The same project repeatedly needs the same worker role and the definition belongs in version control.

Prefer the main conversation or a skill when the work depends heavily on conversational state, needs rapid interactive steering, is a short one-off, or only needs reusable instructions without context isolation. A skill teaches the current context; a subagent creates a new one.

## Two control planes

Treat frontmatter and body as different control planes. Mixing their jobs makes agents harder to reason about.

### Frontmatter is the routing and capability plane

Use it for machine-interpreted configuration:

- `name` — stable identity.
- `description` — the parent-facing **routing surface**.
- `tools` / `disallowedTools` — capability selection.
- `model` / `effort` / `maxTurns` — cost and reasoning envelope.
- `permissionMode`, `hooks`, `isolation` — enforcement and execution boundary.
- `skills`, `mcpServers`, `memory` — deliberate context or capability injection.
- `background`, `color`, `initialPrompt` — runtime/UI behavior where needed.

Do not explain these settings again in the body unless the subagent itself must reason about their consequence. Keep each meaning in a **single source of truth**.

### The Markdown body is the worker-facing system prompt

The body should tell a fresh worker how to perform the role. It is **soft steering**, not enforcement. Put behavior here; put hard capability boundaries in frontmatter, permissions, hooks, or the environment.

A strong body usually needs only five things:

1. **Role and scope** — what class of problem this worker owns.
2. **Operating method** — heuristics or phases that materially change its work.
3. **Evidence standard** — what it must inspect, test, cite, or verify before concluding.
4. **Completion criterion** — a checkable condition for being done.
5. **Return contract** — the compact result the parent needs back.

If a sentence does not change execution, delete it.

## Writing the description

The description is not a miniature system prompt. It is a routing rule exposed to the parent model.

Write it around the **trigger set**:

- Name the concrete tasks that should route here: “Use for migration risk analysis across database schema changes,” not “Expert database architect.”
- Use the vocabulary users and project docs actually contain. Stable shared language gives the router a sharper match.
- Distinguish neighboring agents by task boundary, not by seniority or personality.
- Add an **exclusion boundary** only when adjacent routes are genuinely confusable: “Use for read-only diagnosis; implementation belongs to `backend-implementer`.”
- Keep identity, process detail, output format, and tool policy out of the description unless they affect routing.

Treat automatic delegation as a model behavior to test, not a guarantee to infer from prose. Use explicit invocation when deterministic selection matters; test autonomous routing separately in [`EVALS.md`](EVALS.md).

### Route overlap is architecture debt

If two agents plausibly match the same prompt, changing wording alone may not fix the design. Either sharpen the task boundary or merge them. A collection of agents should partition work more than it duplicates it.

## Capability surface

Every enabled tool adds both power and ambiguity. Start with the smallest surface that can complete the task, then add capabilities only when an observed failure requires them.

- Use an allowlist (`tools`) when the worker has a narrow job.
- Use `disallowedTools` when it mostly needs the inherited tool set but a few capabilities are inappropriate.
- Prefer read-only workers for diagnosis, review, research, and planning unless edits are intrinsic to the job.
- Use `isolation: worktree` when independent code changes are the point and repository isolation materially reduces collision risk.
- Scope MCP servers to the subagent when their tools are useful only there; this keeps irrelevant tool descriptions out of the parent context.
- Preload skills only when their full content is needed on most invocations. Preloading is context, not a permission boundary.
- Use hooks and permissions for enforceable gates. A sentence such as “never modify production” is not a substitute for preventing the relevant action.

A **capability leak** is a worker receiving power it does not need. A **capability gap** is a worker unable to complete its own contract. Optimize for the narrow band between them.

## Writing for a fresh context

Custom subagents do not inherit the parent transcript. Write the body so it works without hidden conversational assumptions.

- State durable task rules in the agent body, a preloaded skill, or project instructions—not in the parent conversation you hope will be remembered.
- Instruct the worker to discover task-specific facts from the repository or delegation message rather than presuming them.
- When a project fact is critical and easy to miss, make the worker verify it from a source of truth.
- Avoid references like “continue the approach we discussed,” “use the files above,” or “follow my earlier constraints.” Those are **context assumptions**.
- Keep the return compact. The point of isolation is lost when the subagent floods the parent with everything it saw.

The best worker prompt says enough to create a reliable local policy, then relies on tools and project evidence for the rest.

## Prompt structure

Formatting is a steering aid, not the behavior itself. Use the lightest structure that makes instruction classes obvious.

A dependable default:

```markdown
You are the project's <role>. Own <bounded class of tasks>.

## Scope
- Handle ...
- Hand off ...

## Method
1. Inspect ...
2. Determine ...
3. Act ...

## Verification
Before finishing, verify ...

## Return
Return: <small, explicit result contract>.
```

Prefer normal Markdown headings and bullets for short agents. Use XML only when the prompt mixes large examples, variable data, or instruction classes that benefit from stronger delimiters. Examples are expensive: add a few canonical, diverse examples only when an eval shows that prose rules leave a recurring ambiguity.

Avoid ceremonial sections with no behavioral effect. “Principles,” “mindset,” “mission,” and long persona prose are common **prompt sediment** unless they change decisions you can observe.

## Frontmatter formatting

YAML is configuration, so optimize for parser robustness and reviewability rather than clever compactness.

- Use a lowercase hyphenated `name`, unique across the project agent tree.
- Keep one field per line and use one canonical field order across the repository.
- Prefer YAML sequences for multi-value fields when values become nontrivial.
- Quote scalars that could be parsed ambiguously.
- For a complex or multiline `description` containing colons, quotes, examples, or markup, prefer a block scalar (`>-` for folded prose or `|-` when line breaks matter).
- Do not rely on filename or folder path as identity; `name` is the identity for project agents.
- Treat undocumented formatting accepted by one Claude Code version as unstable until validated after upgrades.

A useful project convention is:

```yaml
---
name: migration-reviewer
description: >-
  Use for read-only review of database migration safety, rollback risk,
  locking behavior, and backward compatibility. Use after a migration is
  drafted and before merge; implementation belongs to migration-implementer.
tools:
  - Read
  - Grep
  - Glob
  - Bash
model: sonnet
effort: medium
permissionMode: default
maxTurns: 12
---
```

Field order has no YAML semantics; the convention exists to make diffs predictable.

## Project scope and naming

Project agents are repository architecture, not personal aliases. Commit them and design the namespace deliberately.

- Keep every project-agent `name` unique, even when files are organized into subfolders.
- In monorepos, remember that Claude Code can discover multiple nested `.claude/agents/` directories. A nearer definition can **shadow** a farther one with the same name.
- Use subfolders for human organization only; do not encode routing semantics that depend on the folder path.
- Choose names that describe a stable job (`api-contract-reviewer`) rather than a temporary project phase (`phase-2-agent`).
- If two roles differ only by prompt wording but share route, tools, and output, question whether they should be one agent.

## Context additions

Context is a budget. Every preload should earn its place.

- `skills`: preload when the agent needs the full skill on most runs. If it is only occasionally relevant, let the agent invoke the skill when needed.
- `mcpServers`: scope specialized servers to the worker that uses them.
- `memory`: reserve persistent memory for facts learned across runs. Durable policy belongs in version-controlled instructions, not mutable memory.
- `CLAUDE.md`: custom agents receive project instructions, but critical worker-specific behavior still belongs close to the worker so its contract remains inspectable.

A **preload tax** is recurring context paid on every invocation. A **memory sediment** problem is mutable history accumulating until old observations compete with current truth. Both are cured by pruning.

## Verification is part of authoring

A valid-looking agent file is not a finished agent. Finish only when the contract has been exercised.

1. **Load check** — Claude Code recognizes the file and reports no duplicate/parse problem.
2. **Explicit-run check** — explicitly invoke the agent on a representative task; verify prompt, tools, and return contract.
3. **Routing check** — test should-route and should-not-route prompts across repeated trials.
4. **Boundary check** — prove denied capabilities are denied and required capabilities work.
5. **Outcome check** — grade the task result, not only whether Claude happened to use the expected sequence of tools.
6. **Regression check** — keep representative failures as permanent tests when editing the description or body.

Use [`EVALS.md`](EVALS.md) for the full protocol. The completion criterion for editing an agent is not “the Markdown looks good”; it is “the intended route, boundary, outcome, and return all pass their checks.”

## Failure modes

- **Route bleed** — the description attracts neighboring tasks. Cure the task boundary, not the persona prose.
- **Route starvation** — appropriate tasks rarely delegate. Sharpen trigger language, test with the current model/version, and use explicit invocation where certainty matters.
- **Shadowing** — a same-named definition elsewhere in the discovered project tree silently wins by scope/nearest-directory rules or filesystem read order. Keep names unique and run diagnostics.
- **Context assumption** — the body depends on parent conversation history the worker never receives. Move durable facts into worker-visible sources.
- **Capability sprawl** — the worker has tools it never needs. Remove them until the smallest complete surface remains.
- **Prompt enforcement** — a prose prohibition is mistaken for a hard control. Move enforcement to tools, permissions, hooks, isolation, or the environment.
- **Return flood** — the worker returns the exploration it was created to isolate. Write a narrow return contract.
- **Frontmatter fragility** — complex YAML happens to parse on one version and fails on another. Prefer conservative YAML and validate after upgrades.
- **Preload bloat** — skills or MCP descriptions are injected “just in case.” Load them only on branches that earn the context.
- **Memory sediment** — stale learned notes become competing policy. Keep durable policy version-controlled and prune memory.
- **Nesting explosion** — workers spawn workers without a clear orchestration need. Give nesting a bounded purpose, depth, and completion criterion.
- **Replica drift** — the same rule exists in `CLAUDE.md`, a skill, the agent body, and a hook message. Pick one source of truth and point to it from the others.
