# writing-great-workflows

A Claude Code skill for designing, writing, reviewing, and empirically improving dynamic workflow files (`.claude/workflows/*.js`). It is modeled after the supplied `writing-great-skills` reference: a compact top-level skill, a domain glossary, and progressively disclosed supporting material.

## Install

Copy this directory to a Claude Code skill location, for example:

```text
~/.claude/skills/writing-great-workflows/
```

or:

```text
.claude/skills/writing-great-workflows/
```

The supplied skill is user-invoked (`disable-model-invocation: true`) to match the reference skill's invocation strategy. If you want Claude to discover it automatically, remove that field and rewrite the description as a model-facing trigger description.

## Contents

- `SKILL.md` — core workflow-design reference.
- `GLOSSARY.md` — controlled-scaling domain model.
- `references/EVIDENCE.md` — dated research and runtime evidence.
- `references/JAVASCRIPT.md` — JavaScript conventions for the workflow substrate.
- `templates/` — two conservative documented-primitive examples.
- `evals/CASES.md` — behavior-oriented evaluation cases.
- `scripts/lint-workflow.mjs` — advisory text-level hazard detector.

## Design stance

The skill does not teach “how to spawn the most agents.” It teaches when moving the plan into code is worthwhile, which work can genuinely run independently, how to close the verification gap, how to bound cost and replay hazards, and how to prove the workflow beats a simpler baseline.
