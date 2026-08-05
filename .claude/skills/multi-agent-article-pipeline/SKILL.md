---
name: multi-agent-article-pipeline
description: >
  Orchestrates a full adversarial multi-agent article generation pipeline with eight skills:
  complexity triage, research dialectic, fact-check gate, streamed drafting with inline audit,
  red team validation, audience simulation, SEO optimization, and cross-run learning.
  Routes depth (SIMPLE/STANDARD/COMPLEX) based on scored triage. Triggers on: generate article,
  write article, research and write, multi-agent article, adversarial article, long-form content
  with research, fact-checked blog post, article pipeline, write with sources. Composes with
  article-complexity-triage, article-research-dialectic, article-fact-checker, article-qa-auditor,
  article-red-team, article-reader-simulation, article-seo-optimizer automatically. Do NOT
  trigger for short posts, social content, or tasks without research requirements.
---

# Multi-Agent Article Pipeline — v4

## Architecture

Eight skills, six personas, four human checkpoints. All inter-agent data passes through named
artifacts. No implicit context bleed between persona shifts.

**Always read before starting:** `CLAUDE.md` and
`article-qa-auditor/references/markdown-style.md` — they govern artifact,
prose, citation, and conflict-presentation standards.

**Load references on trigger:**
- `references/personas.md` — persona constitutions (load once)
- `references/pipeline-schemas.md` — JSON artifact schemas (reference as needed)

All named artifacts below are relative to the project artifact root
`.agents/artifacts/`. Resolve that root before every read/write; never create a
second copy in the current working directory. Run
`python scripts/validate_artifacts.py` before resuming an existing run and
after finalization.

---

## Step 0: Complexity Triage & Learning Ingestion

**Activate:** `article-complexity-triage` skill.

1. Triage skill reads `pipeline_learnings.md` and applies cross-run calibration.
2. Scores topic across novelty, contentiousness, scope.
3. Extracts or formulates thesis; halts for confirmation if `thesis_confidence = MEDIUM`.
4. Writes `pipeline_config.json` with all routing flags.
5. Display routing confirmation to user (format defined in triage skill).

**Proceed only after user confirms thesis (if MEDIUM) or triage completes (if HIGH).**

---

## Step 1: Research Phase

Read `pipeline_config.json.pipeline.adversarial_dialectic`.

**Activate:** `article-research-dialectic` skill.

### IF adversarial_dialectic = true (STANDARD or COMPLEX):

**→ Delegate to `article-advocate` subagent:** Phase 2a — thesis-supporting evidence.
Writes `advocate_context.md`. Capability-isolated: the subagent has no `Read` tool, so it
cannot see any prior-run artifact even if instructed to.

**→ Delegate to `article-skeptic` subagent:** Phase 2b — disconfirming evidence.
- Also has no `Read` tool. Pass only the extracted Source URL Index list (URLs only, no
  claims) from the advocate's output in its delegation prompt to avoid redundant retrieval —
  never pass `advocate_context.md` itself or any claim/confidence content from it.
- Writes `skeptic_evidence.md`.

**→ @synthesizer:** Phase 3 — conflict mapping.
- Writes `research_context.md`, `article_spec.md`, `conflict_register.md`.
- **KC-3 Check:** If any single source > 40% of total claims → HALT. Call
  `python scripts/pipeline_runner.py record-kc-event --code KC-3 --kc-status PASS|HALT --detail "<highest source share>" --artifact-root .agents/artifacts --json`
  either way, so the event is logged before any HALT is acted on.
- **KC-6 Check:** If > 50% of research vectors classified `[INSUFFICIENT]` → HALT. Call
  `python scripts/pipeline_runner.py record-kc-event --code KC-6 --kc-status PASS|HALT --detail "<insufficient vector count>" --artifact-root .agents/artifacts --json`
  either way.

### IF adversarial_dialectic = false (SIMPLE):

**→ @synthesizer:** Unified research pass.
- Writes `research_context.md`, `article_spec.md`. No `conflict_register.md`.

---

## Step 1.25: Research Summarization (All Depths)

**→ @summarizer:** Immediately after @synthesizer writes artifacts, before fact-check gate.

Read `research_context.md` and `article_spec.md`. Write `research_context_summary.md`:

```markdown
# Research Context Summary

## Thesis
[single sentence]

## Confirmed Claims (CORROBORATED / UNCONTESTED)
[Max 15 claims — one line each with claim ID and source tier: ADV-1 (T1), SKP-3 (T2)]

## Contested Claims (CONFLICTING / WEAKENED)
[All CONFLICTING pairs — one line per conflict: C-1: ADV-2 vs SKP-4 — [axis]]

## Knowledge Gaps (INSUFFICIENT)
[List of vectors flagged insufficient]

## Source Inventory
[All unique sources cited, tier-tagged. Format: Tier | Author/Org | Domain]
```

**Purpose:** Downstream agents read `research_context_summary.md` as their default input.
They load the full `research_context.md` only when a specific claim ID or source needs
verification. This cuts context consumption by 60–80% for COMPLEX depth runs.

**@engineer reads `research_context_summary.md` first.** If a section requires a specific
claim's full evidence chain, @engineer reads only that claim's entry in `research_context.md`
rather than the full document.

---

## Step 1.5: Fact-Check Gate

Read `pipeline_config.json.pipeline.fact_check`.

**IF fact_check = true:**

**Activate:** `article-fact-checker` skill.

**→ @fact-checker:**
1. Extracts HIGH/MEDIUM confidence claims from `research_context.md`.
2. Verifies each via web search per verification protocol.
3. Writes `fact_check_report.md` and `dispute_register.md` (if disputes found).
4. If > 3 DISPUTED claims: surface `dispute_register.md` to user with inline note.

**@engineer MUST read `claims_for_drafting.md` before Step 3.** This is the compressed
claim lookup table produced in Step 1.75. It supersedes scanning `fact_check_report.md` directly.

---

## Step 1.75: Post-Fact-Check Compression

**→ @summarizer:** Runs immediately after `fact_check_report.md` is written.

Read `fact_check_report.md`. Write `claims_for_drafting.md` — a flat lookup table indexed
by section, for use by @engineer during drafting:

```markdown
# Claims for Drafting

| Claim ID | Final Value | Source URL | Suggested Anchor | Section | Status | PosteriorConfidence |
|:---------|:-----------|:-----------|:----------------|:--------|:-------|:-------------------|
| ADV-1 | 67% of respondents... | https://prri.org/... | PRRI survey found 67% of respondents | §Polling Gap | VERIFIED | HIGH (0.91) |
| ADV-5 | $2.4M gap | https://fec.gov/... | FEC filings show a $2.4M contribution gap | §FEC Analysis | VERIFIED-UPDATED (was $2.1M) | HIGH (0.95) |
| SKP-2 | Study found no causal link | https://doi.org/... | [study title†] found no causal link | §Limitations | VERIFIED | MEDIUM (0.74) |
| ADV-9 | [original claim] | URL-MISSING | — | §Rhetoric | UNVERIFIABLE | LOW (0.30) |
```

**PosteriorConfidence** is assigned by @fact-checker during Phase 2 verification:
- HIGH (0.80–1.00): Verified against T1/T2, no contradicting evidence
- MEDIUM (0.50–0.79): T3 accepted, single-source, or WEAKENED by skeptic evidence
- LOW (0.00–0.49): UNVERIFIABLE, `[BREAKING-UNVERIFIED]`, or DISPUTED/unresolved

@engineer uses PosteriorConfidence to calibrate inline hedging:
- HIGH: state the claim directly
- MEDIUM: qualify with source ("according to [source]") or note limitations
- LOW (UNVERIFIABLE): inline caveat mandatory — "*(Editorial note: Verify before publication.)*"
- LOW (DISPUTED): only include if retained per conflict_decisions.json; present as contested

Include all claims with verdict VERIFIED, VERIFIED-UPDATED, UNVERIFIABLE, and DISPUTED.
Exclude OUTDATED claims (those must not appear in draft per dispute_register.md).
One row per claim. No full evidence chains. @qa verifies PosteriorConfidence qualifiers
are correctly applied; absence of qualifier on MEDIUM/LOW claim → `[MAJOR]`.

---

## Step 1.8: VIZ Chart Generation

Read `pipeline_config.json.pipeline.tool_availability.code_execution`.

**IF `code_execution: false`:**
For each `[VIZ-CANDIDATE]` section in `article_spec.md`:
- Update the Visual Assets entry: `Visual: [PLACEHOLDER-ONLY] [filename].webp`
- Log to `pipeline_metadata.md`: `[TOOL-UNAVAILABLE: code_execution] VIZ-CANDIDATE "[section]" → placeholder only`
- @engineer writes the placeholder block inline; production toolchain generates the actual asset.
Do not attempt script execution. Proceed to Step 2.

**IF `code_execution: true`:**
Read `article_spec.md` Visual Assets section. For each `[VIZ-CANDIDATE]` section:

```bash
python3 .claude/skills/multi-agent-article-pipeline/scripts/generate_chart.py \
  --spec ".agents/artifacts/charts/[candidate-spec].json" \
  --output ".agents/artifacts/charts"
```

Script generates a matplotlib chart and saves under `.agents/artifacts/charts/`. Update the VIZ-CANDIDATE
placeholder in `article_spec.md` to reference the actual generated file path.
Log chart generation results (success/failure) to `pipeline_metadata.md`.

---

## Step 2: Approval Gate — ⛔ HALT

> **If `article-pipeline-runner` is active:** Gate is managed by the runner's Step 3 protocol.
> Runner handles `conflict_decisions.json` write and state update. Skip manual gate text below.

**Manual gate (no runner):** Present to user:
- `article_spec.md` — section hierarchy, token budget, target audience.
- `conflict_register.md` — (STANDARD/COMPLEX) conflicts requiring decision.
- `dispute_register.md` — (if populated) verified disputes from fact-check gate.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ APPROVAL GATE — Pipeline Paused
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Depth: [SIMPLE|STANDARD|COMPLEX]
Sections: [N] | Conflicts: [N] | Fact Disputes: [N]
Token Budget: [N] tokens

Conflict handling required for each [CONFLICTING] item:
  (a) Present both positions neutrally.
  (b) Author takes position — specify: advocate or skeptic.
  (c) Flag as unresolved ("remains contested").

Actions:
  ✅ "approved" — conflicts default to (a) if not individually specified.
  ✏️ "revise: <feedback>" — amend spec. Max 3 cycles.
  ❌ "abort" — terminate pipeline.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

On any response, call
`python scripts/pipeline_runner.py record-gate --gate APPROVAL --decision <approved|expedite|revise|abort> --artifact-root .agents/artifacts --json`
first — it owns `gate_history` and `gate_expedite_count` (the JSON's `warning` field fires the
KC-2 tightening note once `gate_expedite_count >= 2`).

On `revise`: before amending the spec, call
`python scripts/pipeline_runner.py increment-revision --gate APPROVAL --artifact-root .agents/artifacts --json`.
If it returns `status: HALT_REQUIRED`, do not attempt a 4th revision — HALT and escalate
instead. Only amend `article_spec.md` after a `RECORDED` result.

On `approved`: write `conflict_decisions.json` (schema in `references/pipeline-schemas.md`).
Record each conflict with: id, handling decision (neutral/author_position/unresolved), position if applicable.
**This JSON is the authoritative source for @engineer — not the free-text conversation.**

KC-2 Check: third non-substantive consecutive revision → HALT.

---

## Step 3: Streamed Drafting + Inline Audit

**@engineer** reads: `article_spec.md`, `research_context_summary.md`,
`claims_for_drafting.md`, `conflict_decisions.json`.
Full `research_context.md` and `fact_check_report.md` available on-demand for claim traces only.

**Precedence rule:** `claims_for_drafting.md` supersedes `article_spec.md`'s Key Claims
exclusion notes on any conflict (e.g., a claim marked excluded at spec-approval time that
fact-check later upgraded). `article_spec.md` is written once, before FACTCHECK runs, and is
never back-patched — treat it as stale on claim status wherever the two disagree.

**Activate:** `article-qa-auditor` skill (inline mode).

**SIMPLE depth:** After all sections pass inline, run Mini-Audit (not full holistic).
**STANDARD/COMPLEX depth:** Run full holistic after all sections pass inline.

Loop per section:
```
@engineer writes section → yields
@qa audits section (inline mode) → verdict to audit_log.md
Call `python scripts/pipeline_runner.py record-audit-verdict --verdict <PASS|PASS_WITH_NOTES|BLOCKED>
  --artifact-root .agents/artifacts --json` — it owns `consecutive_blocked_audits` (resets on
  any non-BLOCKED verdict) and returns `status: HALT_REQUIRED` on the 3rd consecutive BLOCKED
  verdict across the whole run (the "3 consecutive BLOCKED audits" circuit breaker).

SECTION PASS or PASS WITH NOTES → advance
SECTION BLOCKED →
  REVISION_COUNT += 1
  IF REVISION_COUNT ≥ 2 → KC-4: HALT
  ELSE → @engineer revises → re-audit
```

**KC-5 Check (mid-draft):** After each section, check cumulative telemetry. If utilization
> 85% and sections remain → HALT. Do not wait for KC-1 (which only fires pre-draft). Log the
outcome with
`python scripts/pipeline_runner.py record-kc-event --code KC-5 --kc-status PASS|HALT --detail "<utilization%>" --artifact-root .agents/artifacts --json`.

> **KC-5 Calibration Note:** COMPLEX runs with Red Team + SEO audit gate both active
> consume significantly more session budget than STANDARD runs. If `pipeline_learnings.md`
> shows KC-5 triggers on similar topics, the triage skill auto-applies a +8k content budget
> adjustment. Operationally, budget ≥10k session tokens before starting Step 1 on COMPLEX
> routes. If the environment caps below that, consider splitting the run at the Approval Gate:
> approve spec in session 1, execute drafting → delivery in session 2 with fresh context.

After all sections pass:
- **@qa final holistic mode:** cross-section coherence, narrative arc, source diversity
  (>30% single source = CRITICAL finding), thesis-conclusion alignment.
- Writes `audit_report.md`.
- If holistic verdict = FAIL: one revision cycle on CRITICAL/MAJOR sections only, then re-audit.

---

## Step 4: Red Team (COMPLEX only)

Read `pipeline_config.json.pipeline.red_team`.

**IF red_team = true:**

**Activate:** `article-red-team` skill, which delegates to the `article-red-team` subagent.

**→ Delegate to `article-red-team` subagent:** Pass ONLY thesis statement + conclusion
section in the delegation prompt (no full draft — anchoring prevention). The subagent has no
`Read` tool, so this is capability-enforced, not just an instruction. It has no `Write` tool
either — it returns the report as its final message; the orchestrator writes it verbatim to
`red_team_report.md`.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Red Team Report — Threat Level: [LOW|MEDIUM|HIGH]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ "accept" — proceed as-is.
  ✏️ "address" — @engineer adds/modifies to respond.
  📝 "acknowledge" — add limitations paragraph only.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If "address": @engineer revises → @qa re-audits affected sections only, then run
`python scripts/pipeline_runner.py sync-word-count --artifact-root .agents/artifacts --json`
to reconcile `pipeline_state.json` and `pipeline_metadata.md` with the revised draft.

---

## Step 5: Reader Simulation

**Activate:** `article-reader-simulation` skill.

**→ @reader:** Reads `article_draft.md` from declared target audience perspective.
Writes `reader_questions.md`.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reader Simulation — Rating: [ACCESSIBLE|MOSTLY ACCESSIBLE|INACCESSIBLE]
Comprehension Gaps: [N]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ "ship" — accept as-is.
  ✏️ "polish" — address top 3 priority gaps.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If "polish": @engineer addresses gaps → @qa inline-audits modified sections, then run
`python scripts/pipeline_runner.py sync-word-count --artifact-root .agents/artifacts --json`
to reconcile `pipeline_state.json` and `pipeline_metadata.md` with the revised draft.

---

## Step 6: Delivery

Present final `article_draft.md`.

---

## Step 6.5: SEO Pass

Read `pipeline_config.json.pipeline.seo_pass`.

**IF seo_pass = true:**

**Activate:** `article-seo-optimizer` skill.

Generates `seo_package.md` with title variants, meta description, slug, keyword analysis,
JSON-LD blocks, and on-page checklist. Present to user alongside final article.

---

## Step 7: Cross-Run Learning

**→ @qa** appends structured entry to `pipeline_learnings.md`.

Before finalizing the run, use
`python scripts/pipeline_runner.py finalize --artifact-root .agents/artifacts --json`.
It re-syncs the canonical word count (`article_draft.md` → `pipeline_state.json` →
`pipeline_metadata.md`), regenerates `artifact_manifest.json`, validates the run, and persists
`COMPLETE` only when the result is `PUBLISHABLE`. Expected
`OPTIONAL_METADATA` or `TOOL_DEGRADED` conditions remain review-only; do not
turn them into blockers by scanning for TODO or placeholder text generically.

If `article-pipeline-runner` was active: read `pipeline_state.json.telemetry` block first —
use its quantitative values directly rather than estimating.

```markdown
## Run: [ISO Date] — [Topic Title]
### Depth: [SIMPLE|STANDARD|COMPLEX] | Composite Score: [N.N]

### Quantitative Telemetry
| Metric | Value |
|:-------|------:|
| Stages completed | [N] / [total for depth] |
| Total revision cycles | [N] |
| KC triggers | [N] — [list conditions or "none"] |
| Gates expedited | [N] — [list which or "none"] |
| Artifact warnings | [N] — [list files or "none"] |
| Sessions used | [1 or 2] |
| Phase split | [yes/no] |
| Research context size | [estimated lines] |
| Summary compression ratio | [research_context_summary lines / research_context lines]% |

### Stage Timing Estimates (token-equivalent)
- Research: [light/moderate/heavy]
- Fact-check: [N claims verified, N disputed]
- Drafting: [N sections, N inline blocks]
- QA holistic: [pass/fail + cycles]
- Red team: [N/A | LOW | MEDIUM | HIGH]
- Reader sim: [N gaps, rating]
- SEO: [keyword density, E-E-A-T pass/fail]

### Lessons
- [What worked]
- [What to change next run]

### Calibration
[CALIBRATION] novelty_bias: [±N if applicable] | budget_kc1_topics: [topic keywords if KC-1 fired]

### Threshold Adjustment
[THRESHOLD_ADJUST] trigger: [condition] | adjustment: [what changes] | magnitude: [value]

Examples of valid THRESHOLD_ADJUST entries:
- `trigger: KC-5 fired ≥ 3 consecutive COMPLEX runs | adjustment: COMPLEX base budget | magnitude: +4000`
- `trigger: STANDARD ran 5+ runs with zero KC triggers | adjustment: STANDARD base budget | magnitude: -4000`
- `trigger: KC-6 fired on novelty=5 topic | adjustment: novelty_bias for similar topics | magnitude: +0.5`
- `trigger: reader_rating=INACCESSIBLE correlated with contentiousness ≥ 4 | adjustment: COMPLEX depth threshold | magnitude: -0.2`

Write `[THRESHOLD_ADJUST] none` if no pattern is strong enough to justify adjustment.
Require ≥ 3 data points before writing any non-none THRESHOLD_ADJUST entry.

### Gate Hygiene
[GATE_HYGIENE] expedited_this_run: [N] | cumulative_expedites: [N across all runs]
[GATE_HYGIENE] note: [qualitative observation about gate quality this run]
```

The `[CALIBRATION]` tag is required. `[THRESHOLD_ADJUST]` and `[GATE_HYGIENE]` are required.
Write `none` for any tag with no data.

---
> References: `references/personas.md`, `references/pipeline-schemas.md`
