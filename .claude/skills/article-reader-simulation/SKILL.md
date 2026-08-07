---
name: article-reader-simulation
description: >
  Simulates a declared target audience reading an article or document, surfacing comprehension
  gaps, undefined jargon, assumed knowledge, and accessibility issues. Produces a prioritized
  gap report and accessibility rating. Pre-scans for parenthetical definitions before flagging
  terms as gaps — avoids false positives on already-defined terminology. Usable standalone on
  any document. Triggers on: simulate the reader, how will my audience read this, accessibility
  check, comprehension gaps, reader perspective, is this too technical, audience simulation,
  reader questions. Activates automatically at Step 5 of multi-agent-article-pipeline. Do NOT
  trigger for factual accuracy checking, grammar review, or SEO analysis.
---

# Article Reader Simulation — v4

## Purpose

@reader reads `article_draft.md` from the declared target audience's perspective and surfaces
every point where the audience would stop, question, or disengage. The goal is not to produce
a perfect article — it is to surface the gaps @engineer can still fix.

## Pre-Execution: Audience Calibration

Read `article_spec.md` — extract:
- `Target Audience:` field — who they are and what they already know
- `Pipeline Depth:` field — sets simulation rigor (SIMPLE = casual reader; COMPLEX = expert critical reader)

Calibrate your persona to that audience. You are not reading as an editor or expert. If you
find yourself thinking "I understand what they mean," your persona has drifted — an expert
reader is not the target.

## Phase 1: Pre-Scan

Before flagging any term, perform a pre-scan of the full article:
- Build a **Defined Terms Index**: every term that has a parenthetical definition `(term: definition)`
  or an inline explanation within the same sentence of first use.
- Terms in the Defined Terms Index are downgraded from `[GAP]` to `[NOTED]` — they cannot be
  flagged as assumed knowledge gaps.

This prevents false positives on terminology the author has already handled.

## Phase 2: Section-by-Section Simulation

Read each section of `article_draft.md` as the target audience. At each major concept introduction, apply these tests:

**Jargon & Acronym Test**
- Is this term used without definition and absent from the Defined Terms Index?
- If yes → flag as `[GAP: JARGON]`

**Assumed Knowledge Test**
- Does understanding this sentence require background the target audience likely lacks?
- If yes → flag as `[GAP: ASSUMED KNOWLEDGE]`

**Logical Leap Test**
- Does the argument skip a step that the audience would need explained?
- If yes → flag as `[GAP: LOGICAL LEAP]`

**Evidence Accessibility Test**
- Is a data point or claim cited in a way the audience could not verify or contextualize?
- If yes → flag as `[GAP: EVIDENCE OPACITY]`

**Engagement Friction Test**
- Is there a point where the audience's attention would likely drop due to density, length,
  or structural monotony? (Only flag if a full paragraph or section is affected — not individual sentences.)
- If yes → flag as `[GAP: ENGAGEMENT RISK]`

Format each finding:

```markdown
### Gap [N] — [GAP TYPE]
- Location: Section [title], paragraph [N]
- Trigger: "[exact phrase or sentence that caused the flag]"
- Audience Question: "What question would they ask here?"
- Priority: [HIGH | MEDIUM | LOW]
- Suggested Fix: [one sentence describing the minimal edit that resolves this]
```

**Priority assignment:**
- HIGH: Would cause the reader to stop trusting the article or abandon it
- MEDIUM: Would cause confusion but reader likely continues
- LOW: Minor friction; reader proceeds with mild uncertainty

## Phase 3: Accessibility Rating

After completing all sections, issue an overall rating:

| Rating | Criteria |
|--------|----------|
| `ACCESSIBLE` | ≤ 2 HIGH priority gaps; audience can follow the full argument |
| `MOSTLY ACCESSIBLE` | 3–5 HIGH gaps or ≥ 8 MEDIUM gaps; argument mostly followable with effort |
| `INACCESSIBLE TO TARGET AUDIENCE` | > 5 HIGH gaps; argument requires domain expertise the audience lacks |

## Phase 4: Write reader_questions.md

```markdown
# Reader Simulation Report

## Target Audience
[from article_spec.md]

## Defined Terms Index
[terms confirmed as pre-defined — excluded from gap count]

## Accessibility Rating
[ACCESSIBLE | MOSTLY ACCESSIBLE | INACCESSIBLE TO TARGET AUDIENCE]

## Gap Summary
- Total gaps: [N]
- HIGH: [N] | MEDIUM: [N] | LOW: [N]

## Priority Gaps (HIGH only — for "polish" pass)
[Top 3 HIGH gaps with full detail]

## Full Gap Register
[All findings in order of appearance]
```

**Polish pass scope:** If user selects "polish," @engineer addresses the top 3 HIGH priority
gaps only. @qa inline-audits only the modified sections.

---
> References: `references/reader-personas.md`
