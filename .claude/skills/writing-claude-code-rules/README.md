# writing-claude-code-rules

A user-invoked Claude Code skill for designing, auditing, and refactoring project-scoped `CLAUDE.md` and `.claude/rules/` instruction files.

Install by copying this directory to:

```text
.claude/skills/writing-claude-code-rules/
```

Invoke with:

```text
/writing-claude-code-rules
```

The skill is deliberately `disable-model-invocation: true`, so its description consumes no session context until you invoke it.
