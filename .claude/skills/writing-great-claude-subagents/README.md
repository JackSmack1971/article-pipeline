# writing-great-claude-subagents

A reference skill for designing, editing, and empirically validating Claude Code project-scoped custom subagents under `.claude/agents/`.

## Files

- `SKILL.md` — stable authoring principles and failure modes.
- `GLOSSARY.md` — domain vocabulary for reasoning about routing, context, capability, and completion.
- `REFERENCE.md` — dated Claude Code mechanics, supported fields, evidence classification, and research sources.
- `EVALS.md` — practical protocol for discovery, routing, boundary, outcome, and regression tests.

## Install

Copy this directory into a project as:

```text
.claude/skills/writing-great-claude-subagents/
```

The skill is intentionally user-invoked (`disable-model-invocation: true`) so its description does not compete for model context on every turn. Invoke it when creating, reviewing, or refactoring `.claude/agents/*.md` files.

## Design choice

Stable guidance is separated from volatile product behavior. `SKILL.md` should change slowly; `REFERENCE.md` is explicitly dated and should be refreshed after significant Claude Code releases or model-routing changes.
