---
name: article-complexity-triage
description: >
  Scores an article topic brief across novelty, contentiousness, and scope dimensions
  to route the pipeline to SIMPLE, STANDARD, or COMPLEX depth. Reads pipeline_learnings.md
  to apply cross-run calibration before scoring. Writes pipeline_config.json with all
  routing flags, token budget, and thesis confidence level. Triggers on: complexity triage,
  pipeline routing, topic scoring, depth classification, article pipeline start. Required
  first step before any article generation pipeline run. Do NOT use standalone for research,
  writing, auditing, or SEO tasks.
---

# Article Complexity Triage

## Purpose

Routes each pipeline run to the minimum viable depth that produces a credible, defensible
article. Over-routing wastes tokens; under-routing produces thin output. Scoring is
deterministic — every field has an explicit rubric with numeric thresholds.

## Step 0: Pre-Triage Learning Ingestion

Before scoring, read `pipeline_learnings.md` (project file):

**[CALIBRATION] entries** — override default dimension weights:
- Scan for `novelty_bias` values. Apply additive adjustment to novelty raw score before composite calculation.
- Scan for `budget_kc1_topics` — if current brief matches listed keywords, apply +8k budget ceiling.

**[THRESHOLD_ADJUST] entries** — auto-adjust routing thresholds:
- Require ≥ 3 matching entries before applying any adjustment.
- Supported adjustments (read from accumulated entries):
  - `COMPLEX base budget +N` → add N to 48,000 base for this run
  - `STANDARD base budget -N` → subtract N from 32,000 base (floor: 24,000)
  - `COMPLEX depth threshold -N` → lower COMPLEX floor from 3.8 to (3.8 - N)
  - `novelty_bias +N for similar topics` → add N to novelty raw score if topic matches
- Log applied adjustments to triage confirmation output.

**[GATE_HYGIENE] entries** — inform thesis confidence rating:
- If cumulative_expedites ≥ 5 across last 3 runs: set `thesis_confidence` one level more
  conservative (HIGH → MEDIUM threshold requires composite ≥ 3.5 instead of 4.0).

If no learnings exist or file is empty, proceed with all defaults.

## Step 1: Thesis Extraction and Brief Credibility Scan

From the topic brief, extract or formulate:

```markdown
Proposed Thesis: [one declarative sentence asserting a specific position]
Confidence: [HIGH | MEDIUM]
```

- **HIGH:** Topic is factual, bounded, and well-attested. Concurrent research allowed.
- **MEDIUM:** Topic is contested, rapidly evolving, or requires definitional setup.
  HALT before research. Present thesis to user for confirmation before proceeding.

### Brief Credibility Scan (runs before Dimension Scoring)

Before scoring, inspect the user-supplied topic brief for zero-evidence claims. These are
claims that appear to be factual assertions but have no obvious primary source basis and
are likely user belief, hearsay, or forward-looking speculation stated as fact.

Flag any phrase in the brief matching these patterns:
- Revenue or financial figures attributed to a specific product or deployment category
  (e.g., *"GPT-5.5 doubled Codex revenue in days"*) — earnings-call aggregates are routinely
  misattributed to subsets
- Named company adoption claims with no widely-reported sourcing
  (e.g., *"Bridgewater is using [tool]"*)
- Direct quotes attributed to a named executive or institution that cannot be
  immediately recognized as publicly documented

For each flagged phrase, output:
```markdown
[BRIEF-FLAG] "[exact phrase from brief]"
Risk: [revenue-conflation | named-entity-unverified | quote-unverified]
Recommendation: [verify at research gate | remove from thesis | use as research vector only]
```

**Disposition options:**
- `verify at research gate` — keep in brief; @advocate must produce T1/T2 source or flag INSUFFICIENT
- `remove from thesis` — do not build the spec around this claim; treat as a question to investigate
- `use as research vector only` — reframe as a research question rather than an asserted fact

Display BRIEF-FLAGS in the triage confirmation. User may override any recommendation
before research begins. If overridden, log the override in `pipeline_state.json.gate_history`.

## Step 2: Dimension Scoring

Score each dimension 1–5 using the rubric in `references/triage-rubric.md`.

| Dimension | Score | Criteria Summary |
|-----------|-------|-----------------|
| Novelty | 1–5 | How much of the topic postdates 2023 or is domain-niche? |
| Contentiousness | 1–5 | How much do credible sources disagree on facts or interpretation? |
| Scope | 1–5 | How many distinct sub-topics must be covered for adequate treatment? |

**Composite score** = (Novelty × 0.35) + (Contentiousness × 0.40) + (Scope × 0.25)

## Step 3: Routing Decision

| Composite Score | Depth | Adversarial Dialectic | Red Team | Fact Check | SEO Pass | Token Budget |
|-----------------|-------|-----------------------|----------|------------|----------|--------------|
| 1.0 – 2.4 | SIMPLE | false | false | false | true | 24,000 |
| 2.5 – 3.7 | STANDARD | true | false | true | true | 32,000 |
| 3.8 – 5.0 | COMPLEX | true | true | true | true | 48,000 |

Token budget increases 8k if pipeline_learnings.md contains a KC-1 entry for similar topics.

**COMPLEX session budget note:** When Red Team and SEO audit gate are both active, pipeline
execution requires ≥10,000 session tokens. If the session environment caps below that, note
it in the triage confirmation and recommend a two-session split: spec approval in session 1,
drafting through delivery in session 2.

## Step 4: Write pipeline_config.json

```json
{
  "pipeline": {
    "depth": "SIMPLE|STANDARD|COMPLEX",
    "adversarial_dialectic": true,
    "red_team": false,
    "fact_check": true,
    "seo_pass": true,
    "token_budget": 32000,
    "draft_in_phases": false,
    "tool_availability": {
      "code_execution": true,
      "web_search": true
    },
    "topic_brief": "<verbatim user input>",
    "thesis": "<extracted thesis>",
    "thesis_confidence": "HIGH|MEDIUM",
    "novelty_score": 3,
    "contentiousness_score": 4,
    "scope_score": 2,
    "composite_score": 3.1,
    "budget_adjusted": false,
    "budget_adjustment_reason": null,
    "word_count_method": "canonical_markdown_tokens",
    "routed_at": "<ISO timestamp>",
    "author": {
      "name": null,
      "credential": null,
      "affiliation": null
    }
  }
}
```

**`author` rule:**
- Always write this object — never omit it.
- If `CLAUDE.md` declares a project-level default author (a short `## Author` section with
  name/credential/affiliation), populate all three fields from it.
- Otherwise write all three fields as explicit `null`. This is a legitimate, declared state —
  `article-seo-optimizer`'s E-E-A-T audit treats it as "no author by project convention," not
  a rediscovered gap, and will not prompt the user about it.

**`draft_in_phases` rule:**
- `false` for SIMPLE and STANDARD — single session always sufficient.
- `true` automatically for COMPLEX when `red_team: true` AND `seo_pass: true`.
- May be overridden to `false` by user at triage confirmation if they prefer single-session.
- When `true`: triage confirmation explicitly states the two-session plan. Runner enforces split.

**`tool_availability` rule:**
- Triage attempts to detect environment capabilities before writing. If detection is not
  possible, default both to `true` and note `[ASSUMED]` in triage confirmation.
- `code_execution: false` → runner marks all VIZ-CANDIDATEs as `[PLACEHOLDER-ONLY]` at Step 1.8.
- `web_search: false` → fact-check gate auto-disabled regardless of `fact_check` flag;
  runner logs `[TOOL-UNAVAILABLE: web_search — fact_check disabled]` to `pipeline_metadata.md`.

All fields required. No partial writes.

## Step 5: Confirm to User

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔀 COMPLEXITY TRIAGE — Routing Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Depth:               [SIMPLE|STANDARD|COMPLEX]
Composite Score:     [N.N] (Novelty: N | Contention: N | Scope: N)
Thesis:              [one sentence]
Thesis Confidence:   [HIGH → proceeding | MEDIUM → awaiting confirmation]
Adversarial Dialectic: [enabled|disabled]
Fact-Check Gate:     [enabled|disabled]
Red Team:            [enabled|disabled]
Token Budget:        [N] tokens
Learning Calibration: [applied|none]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If `thesis_confidence` is MEDIUM, display:

```
⚠️ THESIS CONFIDENCE: MEDIUM
Proposed thesis: "[thesis]"
Confirm, rephrase, or provide alternative:
  ✅ "confirmed" — proceed with this thesis
  ✏️ "rephrase: <new thesis>" — update and proceed
```

Proceed only on explicit user confirmation.

---
> References: `references/triage-rubric.md`
