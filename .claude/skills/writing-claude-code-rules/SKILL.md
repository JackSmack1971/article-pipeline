---
name: writing-claude-code-rules
description: Design, audit, and refactor Claude Code project instructions and .claude/rules files for high adherence with minimal context cost.
disable-model-invocation: true
---

A Claude Code rule earns its place by changing behavior **at the narrowest reliable scope**. The root virtue is **instruction yield**: useful behavioral change per token placed into Claude's context.

**Bold terms** are defined in [`GLOSSARY.md`](GLOSSARY.md). Evidence behind the recommendations is summarized in [`EVIDENCE.md`](EVIDENCE.md). For controlled comparisons, use [`EVALS.md`](EVALS.md).

## 1. Inventory before editing

Before proposing a rule, inspect the instruction surface that can already affect the target files:

- project and ancestor `CLAUDE.md` / `CLAUDE.local.md`
- project and ancestor `.claude/rules/**/*.md`
- relevant nested `CLAUDE.md` or nested `.claude/rules/` near the target subtree
- project settings that can exclude memory (`claudeMdExcludes`) or enforce behavior through permissions/hooks
- existing skills when the requested content is procedural rather than persistent

Build a **rule map**: file -> scope -> activation -> topic. Identify overlaps and contradictions before adding anything.

**Completion criterion:** every existing instruction source that can plausibly govern the requested files is accounted for, and every overlap has an explicit disposition: keep, merge, narrow, move, or delete.

## 2. Route the instruction to the right mechanism

Use the cheapest mechanism that matches the behavior:

- **Project `CLAUDE.md`** — facts and conventions Claude should carry in essentially every session in this project.
- **Unscoped `.claude/rules/*.md`** — always-on project instructions that deserve their own topical file for maintainability. This is an organizational split, not a context-saving split.
- **Path-scoped `.claude/rules/*.md`** — conventions that apply only while Claude is working with a stable file set. Add YAML `paths:` frontmatter.
- **Skill** — task-specific reference or a multi-step workflow that should load on demand.
- **Hook / permission / setting** — a guarantee, lifecycle action, security boundary, or deterministic enforcement. Rules are guidance, not enforcement.

A rule is the wrong tool if its core meaning is “when asked to do task X, perform steps A→B→C.” That is a **procedure**, so put it in a skill. A rule is also the wrong tool for “this action must never occur regardless of model judgment.” That needs an **enforcement boundary**.

**Completion criterion:** each candidate instruction has exactly one authoritative home, chosen by load timing and enforcement need rather than by convenience.

## 3. Choose scope by semantic locality

For each rule, ask: “For exactly which files is this instruction true?” Use the smallest **scope envelope** that covers those files without surprising spillover.

Prefer `paths:` when the rule is genuinely tied to a file type, directory, or cross-cutting glob. Example:

```markdown
---
paths:
  - "src/api/**/*.ts"
  - "tests/api/**/*.test.ts"
---

# API boundaries

- Validate external input with the schemas in `src/api/schema/` before calling domain services.
- Return failures through `toApiError()` so handlers share one error envelope.
- After changing a handler, run the nearest API test file before broadening test scope.
```

Rules without `paths:` are always-on. Splitting one large always-on file into five unscoped rule files improves maintainability, but it does not reduce their combined context cost.

Treat path activation as **read-triggered context**, not a hard filesystem policy. If an instruction faces an **activation gap** — it must govern a brand-new file before Claude has read any matching file — do not rely on path scoping alone; keep the minimum necessary breadcrumb always-on or enforce the behavior mechanically.

**Completion criterion:** every path-scoped rule has globs that match all intended files, exclude known non-targets, and are not being used as a substitute for a task trigger or security boundary.

## 4. Write for signal density

A project rule should read like a terse engineering constraint sheet, not documentation.

For each line, require a **behavioral delta**: removing it would make a relevant Claude Code mistake more likely. Cut material Claude can cheaply infer from source, standard language conventions, generated directory tours, dependency inventories, generic advice, tutorials, and rationale that does not change the decision.

Write instructions with these forms:

- **Atomic** — one behavior per bullet.
- Concrete — name the command, path, helper, invariant, or observable result.
- **Verifiable** — prefer “run `pnpm test api -- <file>`” over “test thoroughly.”
- **Positive target** — tell Claude what pattern to produce. When a prohibition is necessary, pair it with the replacement behavior.
- **Local rationale when useful** — a short reason can improve generalization when the rule has edge cases; keep it on the same bullet as the behavior.
- **Exemplar pointer** — point to a stable in-repo example when the code itself demonstrates the pattern better than prose.

Prefer:

```markdown
- Store money as integer cents in domain and persistence layers; convert decimal input only at system boundaries to avoid floating-point drift.
```

Over:

```markdown
- Be careful with money values. Do not use floating point numbers because they can be inaccurate. We have had bugs with this before, so make sure you use the correct representation throughout the application.
```

Use Markdown headings and bullets to create visible groups. Do not add XML merely because XML is useful in complex API prompts; Claude Code's own memory guidance specifically recommends Markdown structure for `CLAUDE.md` and rules.

**Completion criterion:** every surviving sentence changes a decision, names enough context to act correctly, and belongs to exactly one topic group.

## 5. Control conflicts and duplication

Claude Code concatenates instruction sources; closer/more-specific sources may be read later, but conflicting behavioral instructions are not a deterministic override system. Do not design a ruleset that depends on “the lower file will win.”

For each concept, maintain a **single source of truth**. If a broad rule and a narrow rule differ, either:

1. rewrite the broad rule so the scopes no longer conflict, or
2. state the exception explicitly in the narrow rule and make the broad rule point to that exception without repeating its contents.

Avoid copying the same coding convention into root `CLAUDE.md`, a language rule, and a package rule. Repetition spends tokens and turns later edits into drift.

Use `claudeMdExcludes` in large monorepos when ancestor or sibling-team instruction files are irrelevant to the current work; do not “counter-prompt” irrelevant rules with more rules.

**Completion criterion:** no behavior is specified independently in two active files, and no intended outcome depends on undocumented conflict resolution.

## 6. Budget always-on context aggressively

Treat every unscoped rule as a recurring **context tax**. Anthropic recommends keeping each `CLAUDE.md` under roughly 200 lines because longer instruction files consume context and reduce adherence; use the same discipline for the combined always-on project instruction surface.

The 200-line figure is a target, not a magic threshold. Optimize the total always-on set for **signal density**, then move conditional material behind `paths:` or skills.

Escalation order when the instruction surface grows:

1. delete **no-op** or derivable content;
2. merge duplicates;
3. narrow file scopes with `paths:`;
4. move task procedures/reference to skills;
5. use nested project instructions only when directory locality is genuinely clearer than a path rule.

Do not use `@imports` as a context optimization: imports improve organization but are expanded into context at launch.

**Completion criterion:** the always-on set contains only project-wide behavioral constraints and high-frequency facts, with conditional and procedural content moved out.

## 7. Validate loading before blaming wording

When a rule “doesn't work,” separate **delivery failure** from **adherence failure**.

- Use `/context` to confirm the file is actually present in the session context.
- Use `/memory` to inspect instruction locations and edit them.
- For path-scoped or lazy-loaded instruction debugging, use the `InstructionsLoaded` hook when available to record what loaded, when, and why.
- Check glob syntax and `claudeMdExcludes` before rewriting the prose.

If the file did not load, fix scope/discovery. If it loaded and the behavior still failed, fix specificity, conflict, or context load.

**Completion criterion:** every reported failure is classified as delivery, conflict, ambiguity, overload, or true model variance before the rule is changed.

## 8. Treat emphasis and formatting as hypotheses

Do not cargo-cult `IMPORTANT`, `MUST`, duplicated warnings, XML wrappers, or elaborate templates. Current Claude prompting guidance favors clear, explicit instructions and says context/motivation can help; historical Claude Code guidance noted that emphasis sometimes improved adherence. Newer Claude models are also more literal and may overreact to blanket prompting.

Apply **emphasis escalation**: add emphasis only after a normal concrete instruction fails a representative evaluation. Prefer improving scope, specificity, and verification first.

When reliability matters, run an **A/B rule eval** using [`EVALS.md`](EVALS.md). Judge behavior on representative tasks, not how persuasive the prose looks to a human.

**Completion criterion:** every `IMPORTANT`/`MUST`/duplicated-warning marker in the changed rule either predates a failed representative eval in EVALS.md or has been removed/downgraded to a plain instruction.

## 9. Produce the smallest coherent change

When writing or refactoring rules:

1. show the rule map and the placement decision;
2. edit only the authoritative files;
3. delete displaced duplicates in the same change;
4. preserve unrelated project policy;
5. report expected load behavior: always-on vs path-triggered;
6. name any unresolved conflict, activation edge case, or enforcement gap.

A successful rules change is smaller than the instruction debt it replaces.

**Completion criterion:** the diff touches only the authoritative files identified in the rule map, no displaced duplicate remains in a non-authoritative file, and the report states always-on vs path-triggered load plus any unresolved conflict or activation gap.
