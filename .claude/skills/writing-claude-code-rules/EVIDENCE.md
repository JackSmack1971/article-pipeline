# Evidence Base — Claude Code Project Rules

This file separates **documented Claude Code mechanics**, **Anthropic prompting guidance**, and **general empirical LLM evidence**. Recommendations in the skill prefer current primary Claude Code documentation when available. General LLM studies support design intuitions but should not be treated as measurements of current Claude Code models unless the study tested them directly.

## Evidence grades

- **A — Product primary source:** current Anthropic / Claude Code documentation describing runtime behavior or official recommendations.
- **B — Model primary guidance:** current Anthropic prompting documentation for Claude models; applicable to instruction writing but not specific to `.claude/rules/` transport.
- **C — Peer-reviewed empirical research:** controlled LLM studies; useful for mechanism and risk, but model/task transfer must be treated cautiously.
- **D — Historical / practitioner evidence:** useful for hypotheses and regressions, never the sole basis for a hard rule.

## Claims used by the skill

### 1. Project instructions are context, not hard enforcement — Grade A

Claude Code's memory documentation states that CLAUDE.md-style instructions are context rather than enforced configuration. The debugging guide recommends permissions/hooks for guarantees and security boundaries. Therefore this skill routes deterministic constraints away from prose rules.

Sources:
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/debug-your-config

### 2. Specific, concise, structured instructions have better adherence — Grade A

Claude Code recommends specific, concise, well-structured project instructions; it explicitly recommends Markdown headers/bullets and concrete, verifiable wording. It targets under ~200 lines per CLAUDE.md and states that longer files consume more context and reduce adherence.

Source:
- https://code.claude.com/docs/en/memory

### 3. Unscoped rules are always-on; path rules load conditionally — Grade A

All Markdown files in `.claude/rules/` are discovered recursively. Rules without `paths:` load at launch. Path-scoped rules apply when Claude works with matching files and are triggered when Claude reads a matching file, not on every tool use.

Source:
- https://code.claude.com/docs/en/memory

### 4. Splitting into unscoped rule files is organizational, not a context optimization — Grade A

Because unscoped `.claude/rules/*.md` load at launch, dividing one always-on document into multiple unscoped files does not by itself remove their content from the context window. Conditional `paths:` or on-demand skills are the mechanisms that reduce irrelevant persistent context.

Sources:
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/features-overview

### 5. Imports do not reduce startup context — Grade A

Claude Code expands `@` imports into context at launch. The docs explicitly say imports can improve organization but do not reduce context. Therefore the skill never recommends imports as token optimization.

Source:
- https://code.claude.com/docs/en/memory

### 6. Project/user instruction layers are additive; load order is not deterministic conflict resolution — Grade A

The memory docs describe broad-to-specific load order and note that user rules load before project rules. The Agent SDK docs clarify the crucial semantic point: all instruction levels are additive and there is no hard precedence rule; if instructions conflict, the outcome depends on Claude's interpretation. This is not a contradiction once load order is distinguished from enforcement precedence.

Sources:
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/agent-sdk/claude-code-features

### 7. `claudeMdExcludes` is the correct way to remove irrelevant ancestor/project memory — Grade A

Claude Code supports glob or absolute-path exclusions for CLAUDE.md and rule files. Managed policy instructions cannot be excluded. This supports deleting/excluding irrelevant instructions instead of counter-prompting them.

Sources:
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/memory

### 8. Skills are the right home for on-demand reference and procedures — Grade A

Claude Code's extension overview contrasts always-loaded project instructions, conditionally loaded rules, and on-demand skills. The skill documentation says full skill content loads when invoked/relevant and recommends keeping skill bodies concise once loaded.

Sources:
- https://code.claude.com/docs/en/features-overview
- https://code.claude.com/docs/en/skills

### 9. Delivery can be observed separately from adherence — Grade A

Claude Code provides `/context` to see what occupies the context window and `/memory` to inspect instruction locations. It also documents an `InstructionsLoaded` hook for logging which instruction files load, when, and why. Therefore debugging should verify delivery before rewriting instructions.

Sources:
- https://code.claude.com/docs/en/debug-your-config
- https://code.claude.com/docs/en/memory

### 10. Clear/direct wording, context, examples, and positive output descriptions are supported Claude prompting practices — Grade B

Anthropic's current prompting guide recommends explicit instructions, sequential bullets/steps when order matters, concise context/motivation when it improves generalization, and well-chosen examples. It also recommends describing the desired behavior rather than only the forbidden format in output-control cases. The skill applies these principles selectively to rule writing while preferring Claude Code's native Markdown guidance over importing complex API-prompt structure wholesale.

Sources:
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview

### 11. Longer context can reduce information use even when it fits — Grade C

Liu et al. found position-dependent degradation in long-context retrieval/QA, with important information in the middle often used less reliably. Du et al. later found performance degradation as context length increased even under perfect retrieval conditions across several models and tasks. These papers do not prove a specific failure curve for current Claude Code; they support the conservative practice of minimizing irrelevant always-on instructions.

Sources:
- https://aclanthology.org/2024.tacl-1.9/
- https://aclanthology.org/2025.findings-emnlp.1264/

### 12. Prompt sensitivity exists, but measurement methodology matters — Grade C

Research on prompt sensitivity finds meaningful performance variation across prompt formulations, while later work also shows that some reported sensitivity is inflated by evaluation artifacts. The implication is not “find magic wording”; it is to test important rules against behaviorally meaningful success criteria.

Sources:
- https://aclanthology.org/2024.findings-emnlp.108/
- https://aclanthology.org/2025.emnlp-main.1006/

### 13. Historical Claude Code guidance treated lexical emphasis as an empirical tuning tool — Grade D/A-historical

Anthropic's 2025 Claude Code best-practices article reported that teams sometimes improved adherence by tuning CLAUDE.md wording and adding emphasis such as `IMPORTANT` or `YOU MUST`. Current model guidance also warns against blanket over-prompting on newer models. The skill therefore treats emphasis as a testable escalation, not a default style.

Sources:
- https://www.anthropic.com/engineering/claude-code-best-practices
- https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

## Open questions / product-version risks

- Path-scoped rules are explicitly read-triggered. Exact edge behavior around brand-new files, unusual IDE workflows, or non-Read tool paths may vary by Claude Code version. Treat “activation gap” as a conservative design inference, not a documented guarantee that creation will fail.
- Claude Code's rules/glob implementation has changed across recent 2.1.x releases. Keep syntax simple and re-check current docs after major upgrades.
- Anthropic's ~200-line recommendation is guidance for each `CLAUDE.md`, not a published hard limit for total `.claude/rules/` content. This skill generalizes the same context-budget logic to the combined always-on surface; that generalization is reasoned, not an Anthropic numeric rule.
- No public study located here directly measures adherence as a function of `.claude/rules/` Markdown formatting on the latest Claude Code model stack. That gap is why [`EVALS.md`](EVALS.md) treats local behavioral evaluation as the final authority.
