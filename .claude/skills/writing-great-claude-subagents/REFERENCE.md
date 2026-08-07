# Claude Code project-subagent reference

**Research date:** 2026-08-03  
**Claude Code release baseline:** v2.1.220 (released 2026-07-25)  
**Scope:** project-scoped custom subagents stored under `.claude/agents/`

This file intentionally contains version-sensitive facts. Re-check the official documentation after meaningful Claude Code upgrades. The stable authoring principles live in [`SKILL.md`](SKILL.md).

## Evidence legend

- **[DOC]** Current official Claude Code / Anthropic documentation.
- **[SPEC]** Language or format specification.
- **[FIELD]** Reproducible or detailed public issue report; useful evidence, not a product guarantee.
- **[INFERENCE]** Recommendation derived from the documented mechanics plus prompting/evaluation research.

## Current discovery and precedence

**[DOC]** Claude Code currently recognizes custom subagents from several scopes, with precedence: managed settings, `--agents` session definitions, project `.claude/agents/`, user `~/.claude/agents/`, then plugin agents.

**[DOC]** Project agents are discovered by walking upward from the current working directory toward the repository root and scanning every `.claude/agents/` encountered. Directories supplied through `--add-dir` are also scanned for `.claude/agents/`.

**[DOC]** Project and user agent directories are scanned recursively. Subfolders are organizational only; for project/user agents, the frontmatter `name` defines identity.

**[DOC]** If nested project directories define the same `name`, the definition closest to the working directory wins (documented since v2.1.178). If two files in the same scope tree define the same `name`, only one loads and the choice is filesystem read order rather than a documented semantic precedence. `/doctor` reports duplicate names.

**Authoring consequence [INFERENCE]:** Treat agent names as a repository-wide namespace. Nested overrides should be intentional and rare; accidental same-name files create hidden behavior changes based on launch directory.

## Live reload

**[DOC]** Claude Code watches existing `.claude/agents/` and `~/.claude/agents/` directories and normally picks up edits within seconds for the next delegation.

Two documented exceptions require a restart:

1. The `agents` directory itself did not exist when the session started and is created for the first time during that session.
2. The session started with `--disable-slash-commands`, which also disables these directory watchers.

**Authoring consequence [INFERENCE]:** When an agent appears “missing” immediately after first creation, distinguish discovery/watcher state from prompt quality before rewriting the description.

## Frontmatter surface

Only `name` and `description` are currently required.

| Field | Current documented meaning | Authoring note |
|---|---|---|
| `name` | Lowercase letters and hyphens; unique identifier; `:` reserved for plugin-scoped identifiers | Keep unique across project tree. Filename need not match, but matching reduces human error. |
| `description` | When Claude should delegate to this subagent | Write task triggers and boundaries, not full worker instructions. |
| `tools` | Allowlist of tools; if omitted, inherits every tool available to subagents | Prefer minimum viable surface for narrow workers. |
| `disallowedTools` | Denylist removed from inherited/specified tools | Useful when inheritance is mostly correct. |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, full model ID, or `inherit`; default `inherit` | Pin only when cost/capability behavior is part of the contract. |
| `permissionMode` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` alias | Affects permission behavior; do not infer safety solely from prompt wording. |
| `maxTurns` | Maximum agentic turns | Use as a resource/stopping bound, not as a replacement for a completion criterion. |
| `skills` | Skills preloaded in full at startup | Full content is injected; this is context, not a skill allowlist. |
| `mcpServers` | Existing server names or inline server definitions scoped to the worker | Useful to isolate specialized tool descriptions from parent context. |
| `hooks` | Lifecycle hooks scoped to this subagent | Verify in your target version/platform if relied on for enforcement. |
| `memory` | Persistent memory: `user`, `project`, or `local` | Use for learned cross-run state, not immutable policy. |
| `background` | `true` forces background execution; when unset Claude chooses | Current docs note background is the default choice as of v2.1.198. |
| `effort` | Worker effort override | Available levels depend on model. |
| `isolation` | `worktree` for a temporary isolated git worktree | Strong fit for independent modifying workers. |
| `color` | UI/transcript color | Cosmetic. |
| `initialPrompt` | First user turn when the agent runs as the main session agent | Relevant to `--agent` / `agent` setting more than ordinary delegation. |

**[DOC]** Model resolution can also be overridden per invocation and by environment configuration; therefore the frontmatter `model` is not always the final model if a higher-priority override exists.

## What a custom subagent starts with

**[DOC]** A custom subagent runs in a fresh context. It does not inherit the parent conversation transcript, files already read in that transcript, or skills already invoked there.

Current official documentation says a custom subagent gets:

- its own Markdown body as system prompt plus basic environment details;
- the delegation task from the parent;
- the applicable `CLAUDE.md` hierarchy and a git-status snapshot (unlike built-in Explore/Plan, which intentionally skip those);
- any explicitly preloaded skills;
- configured agent memory when `memory` is enabled;
- its resolved tools/MCP servers and runtime controls.

**[DOC]** The worker starts in the parent conversation's current working directory. Shell `cd` state does not persist between shell tool calls. `isolation: worktree` changes where repository-modifying shell work occurs.

**Authoring consequence [INFERENCE]:** Write the body as a local system policy for a worker that can inspect the project but cannot see the conversation that motivated the delegation.

## Description vs. body

**[DOC]** Claude Code explicitly says it uses the subagent `description` to decide when to delegate. The Markdown body becomes the subagent's system prompt.

This gives a useful separation:

- **Description:** parent-facing router contract — _when should this worker be selected?_
- **Body:** worker-facing execution contract — _how should this worker perform once selected?_

**[INFERENCE]** Do not spend description tokens on detailed process unless the process itself distinguishes this agent from a neighbor. Do not hide routing boundaries only in the body because the router must choose the worker before the body can help.

## Skills, MCP, and memory

**[DOC] Skills.** The `skills` field preloads the full content of listed skills into the worker at startup. It does not prohibit the worker from invoking other available skills through the Skill tool. Skills marked `disable-model-invocation: true` cannot be preloaded automatically as model-invoked content.

**[DOC] MCP.** `mcpServers` can reference existing servers or define servers inline for the subagent. This allows a specialized worker to carry tool definitions that the parent does not need.

**[DOC] Memory.** `memory: user|project|local` enables persistent agent memory. Current docs recommend `project` as a common default for project-specific learning. Agent memory is separate from the main session's auto-memory behavior.

**[INFERENCE]** Use version control for durable rules and memory for learned, revisable observations. Otherwise mutable memory becomes an unreviewed policy layer.

## Hooks and permissions: documented behavior vs. field evidence

**[DOC]** Current Claude Code docs support frontmatter `hooks`, project-level `SubagentStart` / `SubagentStop` hooks, and permission controls that can restrict the Agent tool or specific agent names.

**[FIELD]** Public GitHub reports in 2026 documented cases where `PreToolUse` / `PostToolUse` or subagent lifecycle hooks did not fire as expected in particular Claude Code versions/platforms (for example v2.1.76). Some older reports conflict with today's docs, and several were later closed or may have been fixed.

**Authoring consequence [INFERENCE]:** If a hook is a security, compliance, deployment, or destructive-action gate, test the exact hook path on the exact Claude Code version/platform you ship. Documentation establishes intended/current behavior; a passing local integration test establishes your operational behavior.

## Nested subagents

**[DOC]** Current Claude Code docs allow subagents to spawn subagents while the configured depth permits it. The documented default supports multiple nested layers, with environment variables controlling maximum spawn depth, session subagent count, and concurrent subagent count.

**[INFERENCE]** Nest only where decomposition is structural: a worker owns an orchestration task and child workers own disjoint subproblems. Do not grant `Agent` merely because it is available; it expands both capability and coordination state.

## Automatic delegation caveat

**[DOC]** Official docs describe automatic delegation based on the task, description, and context, and their examples still use phrasing such as “Use proactively.” They also support explicit invocation / mentions when a specific worker should be used.

**[FIELD]** A current open issue against v2.1.219 reports that an Opus 5 system-prompt section can tell the model not to call the Agent tool unless the user requested it, potentially suppressing autonomous delegation despite project descriptions. This is a report, not an official contract, but it is recent enough to matter.

**Authoring consequence [INFERENCE]:** Keep automatic-routing evals separate from explicit-invocation evals. A worker may be excellent even when current model-level policy makes autonomous delegation conservative. For workflows where the exact worker is mandatory, invoke it explicitly rather than encoding operational certainty as a hope in the description.

## YAML formatting

**[SPEC]** YAML plain scalars have syntactic sensitivities around `:` and other indicators; block scalar styles provide explicit multiline behavior. `|` preserves line breaks; `>` folds most line breaks into spaces.

**[FIELD]** A Claude Code issue report describes complex agent descriptions that stopped parsing under a stricter 2.1.x frontmatter parser until rewritten as YAML block scalars. Historical parser issues also show that “valid-looking” frontmatter may fail discovery.

Recommended robust style [INFERENCE]:

```yaml
---
name: release-risk-reviewer
description: >-
  Use for read-only release risk review before production deployment. Inspect
  code changes, migration compatibility, rollout dependencies, and rollback
  readiness. Implementation and deployment belong to other workers.
tools:
  - Read
  - Grep
  - Glob
  - Bash
model: sonnet
permissionMode: default
maxTurns: 10
---
```

Use `>-` for a prose description where newlines are only source formatting. Use `|-` when preserved line breaks are intentionally part of the scalar. Prefer explicit lists once a collection is more than a tiny one-liner.

## Prompt-format research translated to subagents

Anthropic's current prompting guidance and context-engineering research supports several design choices:

- **[DOC]** Clear, direct instructions outperform vague prompting; current models often need less aggressive “MUST/ALWAYS” language than older prompt recipes.
- **[DOC]** Structured delimiters help when prompts mix instructions, context, examples, and variable inputs; Markdown headings are sufficient when the structure is already obvious.
- **[DOC]** Examples are a strong steering mechanism; Anthropic recommends a small set of relevant, diverse examples rather than a laundry list.
- **[DOC]** Context is finite and high-signal context generally beats indiscriminate accumulation.
- **[DOC]** Tool sets should be designed deliberately; agents work best with tools whose purpose and boundaries are clear.
- **[INFERENCE]** Therefore, start with a short worker contract and add sections/examples only in response to measured failure modes. Complexity should be earned by eval evidence.

## Empirical authoring loop

Anthropic's prompt-engineering docs say to define success criteria and a way to test them before iterating on prompts. Its agent-eval guidance emphasizes multiple trials, outcome grading, transcript inspection, and separate capability vs. regression suites.

Translate that into subagent authoring:

1. Specify route, capability, outcome, and return success criteria.
2. Write the smallest agent that should satisfy them.
3. Test explicit invocation first.
4. Test autonomous routing independently, with positive and negative examples.
5. Grade outcomes with deterministic checks where possible; inspect transcripts for routing/tool failures.
6. Run multiple trials because the agent is stochastic.
7. Promote every meaningful bug into a regression case.

See [`EVALS.md`](EVALS.md) for a practical harness-independent protocol.

## Primary sources

1. Claude Code — Create custom subagents: https://code.claude.com/docs/en/sub-agents
2. Claude Code — Extend Claude with skills: https://code.claude.com/docs/en/skills
3. Claude Code — How Claude remembers your project: https://code.claude.com/docs/en/memory
4. Claude Code — Debug your configuration: https://code.claude.com/docs/en/debug-your-config
5. Claude Code — Configure permissions: https://code.claude.com/docs/en/permissions
6. Claude Code — Orchestrate teams of Claude Code sessions: https://code.claude.com/docs/en/agent-teams
7. Claude Code — Explore the .claude directory: https://code.claude.com/docs/en/claude-directory
8. Anthropic — Prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
9. Anthropic — Prompt engineering overview: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview
10. Anthropic Engineering — Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
11. Anthropic Engineering — Demystifying evals for AI agents: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
12. Anthropic Engineering — Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
13. YAML 1.2.2 specification: https://yaml.org/spec/1.2.2/
14. Claude Code changelog feed: https://github.com/anthropics/claude-code/blob/main/feed.xml

## Field evidence / conflict sources

15. GitHub issue #11205 — complex description/frontmatter parsing field report: https://github.com/anthropics/claude-code/issues/11205
16. GitHub issue #34692 — reported subagent tool-hook gap on v2.1.76: https://github.com/anthropics/claude-code/issues/34692
17. GitHub issue #80988 — reported Opus 5 delegation suppression in v2.1.219: https://github.com/anthropics/claude-code/issues/80988
18. GitHub issue #8501 — historical documentation/frontmatter inconsistencies: https://github.com/anthropics/claude-code/issues/8501
