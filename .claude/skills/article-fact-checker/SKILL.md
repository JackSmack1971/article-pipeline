---
name: article-fact-checker
description: >
  Verifies atomic claims in research artifacts against live sources before article drafting
  begins. Operating as @fact-checker persona, queries web search for each HIGH and MEDIUM
  confidence claim in research_context.md, assigns a verification verdict, clears [Unverified]
  flags or escalates to [DISPUTED], and writes fact_check_report.md. Triggers on: fact check
  gate, pre-draft verification, source validation, verify research claims.
  Activates automatically at Step 1.5 of the article generation pipeline when fact_check is
  enabled in pipeline_config.json. Do NOT trigger for writing, auditing, SEO, or post-draft
  tasks.
---

# Article Fact-Checker

## Purpose

Closes the epistemic gap between research synthesis and drafting. @synthesizer produces
`research_context.md` from searched artifacts but cannot re-verify every claim inline.
@fact-checker does exactly that: treats every HIGH/MEDIUM confidence claim as untrusted
until confirmed by a secondary web lookup.

## Pre-Execution Check

Read `pipeline_config.json`:
- If `pipeline.fact_check` is `false`: Skip entirely. Log `[FACT_CHECK: SKIPPED — disabled by triage]`.
- If `pipeline.fact_check` is `true`: Execute full protocol below.

## Phase 1: Claim Extraction

Read `research_context.md`. Extract all claims where:
- Confidence = HIGH or MEDIUM (LOW confidence claims are already flagged [Unverified] and go to @qa)
- Classification = `[CORROBORATED]`, `[UNCONTESTED]`, or `[WEAKENED]`
- Skip `[CONFLICTING]` claims — these are handled by human resolution at the Approval Gate
- Skip `[INSUFFICIENT]` claims — these are knowledge gap flags, not verifiable claims

Build a claim verification queue:

```markdown
## Verification Queue
- VQ-1: [ADV/SKP ID] "[claim statement]" | Source: [URL] | Priority: [HIGH|MEDIUM]
- VQ-2: ...
```

**Queue limits:** MAX 40 claims. If `research_context.md` contains > 40 eligible claims,
prioritize: (1) claims cited in the introduction/conclusion sections of `article_spec.md`,
(2) claims with HIGH confidence, (3) claims from single-source vectors.

## Phase 2: Verification Passes

Before searching, consult `references/verification-protocol.md` for source-tier weights
(T1–T4), the search-query pattern for this claim's type, and the freshness threshold that
applies.

For each claim in the queue:

1. Execute a targeted web search: query = `[claim core assertion] site:authoritative OR [source domain]`
2. **Social post platform verification (runs before tier assignment):** check the source URL
   domain against the attributed platform per `references/verification-protocol.md` (Social
   post claims). Domain mismatch → verdict `[DISPUTED]` immediately, flag `[PLATFORM-MISMATCH]`.
3. Assign verdict:

| Verdict | Criteria |
|---------|----------|
| `[VERIFIED]` | Secondary source corroborates the claim within acceptable variation (±10% for statistics). |
| `[VERIFIED-UPDATED]` | Claim is correct but a more recent figure/finding supersedes it. Include updated value. |
| `[UNVERIFIABLE]` | No secondary source found after 2 search attempts. Claim stands but flagged. |
| `[DISPUTED]` | Secondary source directly contradicts the claim. Requires human decision. |
| `[OUTDATED]` | Claim was accurate historically but is no longer current. Must be updated or cut. |

4. For `[DISPUTED]` and `[OUTDATED]`: escalate to `dispute_register.md` (see Phase 3).

```markdown
### VQ-[N]: [ADV/SKP ID]
- Claim: "[statement]"
- Original Source: [URL]
- Search Query Used: "[query]"
- Verification Source: [URL, Date]
- Verdict: [VERIFIED|VERIFIED-UPDATED|UNVERIFIABLE|DISPUTED|OUTDATED]
- Notes: [updated value if VERIFIED-UPDATED; contradiction if DISPUTED]
```

## Phase 3: Dispute Register

For every `[DISPUTED]` or `[OUTDATED]` finding, append to `dispute_register.md`:

```markdown
## Dispute DR-[N]
- Claim ID: [ADV/SKP ID]
- Original Claim: "[statement]"
- Conflicting Evidence: "[counter-statement]" [Source URL, Date]
- Type: [DISPUTED | OUTDATED]
- Recommended Action: [update claim | remove claim | present both | flag for human]
```

If `dispute_register.md` contains > 3 DISPUTED entries: surface to user before Approval Gate
with a warning block. This does not halt the pipeline but informs the spec review.

## Phase 4: Write fact_check_report.md

```markdown
# Fact-Check Report

## Summary
- Claims verified: [N]
- Verified: [N] | Verified-Updated: [N] | Unverifiable: [N]
- Disputed: [N] | Outdated: [N]
- Dispute register: [attached if N > 0]

## Updated Claims
[List of VERIFIED-UPDATED entries with new values — @engineer MUST use these, not the originals]

## Unverifiable Claims
[List — @qa will flag these [Unverified] in audit if they appear without qualification]

## Verification Log
[Full VQ table]
```

**Critical output rule:** @engineer reads `fact_check_report.md` before drafting. Claims
marked `[VERIFIED-UPDATED]` in the report supersede the original `research_context.md` values.
Claims marked `[DISPUTED]` with "remove" recommendation must not appear in the draft.

---
> References: `references/verification-protocol.md`
