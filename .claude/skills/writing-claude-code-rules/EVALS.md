# Evaluating Claude Code Rules

Use an eval when a rule is important enough that wording or placement should be chosen from observed behavior rather than intuition.

## What to measure

Define one observable outcome per rule. Examples:

- generated handler calls the canonical validation helper;
- changed Python file is followed by the expected focused test command;
- new migration includes both `up` and `down` logic;
- untouched files outside the rule's `paths:` scope are not rewritten to the scoped convention.

Do not score “Claude mentioned the rule.” Score the resulting behavior.

## Build a representative task set

Use 6–12 tasks when practical:

1. 3–5 ordinary in-scope tasks;
2. 1–2 edge cases that historically caused mistakes;
3. 1–2 out-of-scope tasks to detect spillover;
4. at least one fresh-session task where the rule's activation timing matters.

Keep prompts natural. If the test prompt repeats the rule, you are measuring the prompt rather than the rule file.

## Compare variants

Prefer the smallest comparison that answers the question:

- placement A vs placement B (`CLAUDE.md` vs `paths:` rule);
- concise wording vs verbose wording;
- concrete rule vs emphasized concrete rule;
- one scoped file vs broad unscoped rule.

Use fresh sessions, the same Claude model/effort, the same repository state, and the same task prompts. Multiple runs matter for important rules because model behavior is stochastic.

For controlled one-shot CLI experiments, Claude Code exposes `-p`, `--model`, and `--setting-sources`. You can also exclude a specific instruction path with `claudeMdExcludes` in a temporary settings override. Verify the active context with `/context` or an `InstructionsLoaded` hook when testing interactive/lazy activation.

## Score three layers separately

### Delivery

Was the candidate instruction actually loaded for this task?

### Adherence

Given delivery, did Claude follow the intended behavior?

### Collateral effect

Did the rule cause irrelevant behavior outside its scope, extra work, verbosity, or conflicts?

A rule that raises adherence but creates large spillover may have lower instruction yield than a narrower alternative.

## Prefer decision thresholds over anecdotes

Example acceptance rule:

> Keep the candidate only if it improves in-scope adherence by at least 2 successful tasks out of 10, creates no new critical failures, and causes zero out-of-scope convention changes.

Choose thresholds based on the cost of failure. The point is to decide them before reading the outputs.

## Record the result

For rules that received explicit tuning, keep a short maintainer note outside loaded content when possible:

- behavior tested;
- variants compared;
- model/version/date;
- winning formulation;
- known gaps.

Do not turn the project rules themselves into an experiment log.
