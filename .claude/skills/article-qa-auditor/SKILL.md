---
name: article-qa-auditor
description: >
  Audits article drafts for factual accuracy, citation integrity, style guide compliance,
  conflict traceability, source tier quality, and fact-check report adherence. Operates in
  two modes: inline (per-section during drafting, enforces KC-5 mid-draft token check) and
  holistic (full-document final review). Also serves as the drafting execution engine
  (@engineer) when paired with approved research artifacts. Triggers on: audit article,
  QA draft, fact-check and style-check, editorial audit, review article for compliance,
  draft article from spec, inline audit section, holistic audit. Activates automatically
  at Step 3 of multi-agent-article-pipeline. Do NOT trigger for grammar-only proofreading,
  SEO optimization, or tasks without a research context artifact.
---

# Article QA Auditor — v4

## Modes

**Inline mode:** Activated after @engineer writes each section. Audits that section only.
**Holistic mode:** Activated after all sections pass inline. Full-document review.

---

## Inline Audit Protocol

### Audit Checklist (per section)

Load `references/audit-checklist.md` for the full rubric. Key checks:

**Factual Accuracy**
- [ ] Every factual claim maps to a claim ID in `research_context.md`
- [ ] Statistical values match `fact_check_report.md` VERIFIED-UPDATED entries (not originals)
- [ ] No claims from [INSUFFICIENT] vectors presented as established fact
- [ ] No `[Unverified]` claims without explicit `[Unverified]` label in prose

**Citation Integrity**
- [ ] Every factual assertion is cited using a phrase link: `[meaningful anchor text](https://absolute-url)`.
      The anchor text must be the natural phrase in prose that carries the claim — not a naked URL,
      not `[Source]`, not `[1]`. If no URL is available for a source, flag `[URL-MISSING]`.
- [ ] All phrase link URLs are absolute (`https://`) — no relative paths (`[MAJOR]`).
- [ ] Anchor text is meaningful and descriptive — generic anchors like "here", "this study",
      "source", or bare numbers are `[STYLE]`.
- [ ] PosteriorConfidence qualifiers correctly applied per `claims_for_drafting.md`:
      MEDIUM claims include source attribution qualifier ("according to [source]" or equivalent).
      LOW/UNVERIFIABLE claims carry inline caveat. Missing qualifier on MEDIUM or LOW → `[MAJOR]`.
- [ ] Legislation/policy acronyms have mandatory inline definition on first use
- [ ] T3 citations marked `†` with documented T1/T2 re-search attempt

**Conflict Handling**
- [ ] [CONFLICTING] claims handled per `conflict_decisions.json` (not improvised)
- [ ] Sections closing with "remains contested" must identify the structural incompatibility axis
- [ ] No silent conflict resolution (one side adopted without disclosure)
- [ ] Unfalsifiable conclusion check: Does any section make a causal claim that the article's own
      evidentiary standard would reject if applied to an opponent? (e.g., "rhetoric X caused violence Y"
      when the thesis argues that such causal claims are applied asymmetrically and lack evidentiary
      basis) If yes → `[MAJOR]` — either add an explicit logical-consistency caveat or revise the
      causal framing to correlation + pattern before advancing.

**Style Guide Compliance**
- [ ] No prohibited patterns (meta-narration, AI-tell phrases, rhetorical questions as openers)
- [ ] Bold used for key terms on first introduction only
- [ ] No unattributed superlatives

**Structural**
- [ ] Section matches spec scope and word budget (±15% tolerance)
- [ ] Topic sentence leads the first paragraph
- [ ] Section contains ≥ 1 H3 subsection unless spec word budget for this section is < 300 words.
      Absence of H3 in a full-length section → `[MAJOR]`.
- [ ] If `article_spec.md` marks this section `[VIZ-CANDIDATE]`, the image placeholder block
      must appear immediately after the data claim that motivated the flag:
      `![Chart: [one-sentence takeaway] — [Source, Year]]([filename].webp)`
      Missing placeholder in a VIZ-CANDIDATE section → `[MAJOR]`.

### Verdict

```
SECTION PASS — all checks clear
SECTION PASS WITH NOTES — [MINOR]/[STYLE] findings only; @engineer may note and advance
SECTION BLOCKED — one or more [CRITICAL]/[MAJOR] findings; @engineer must revise before advancing
```

**KC-5 Check (mid-draft):** After issuing verdict, check cumulative telemetry footer.
If `utilization > 85%` and sections remain → output KC-5 diagnostic dump. Pipeline halts.

Append findings to `audit_log.md` — **delta-only format:**

```markdown
## Section [N] — [Title] — SECTION PASS
> Clean pass. No findings.

## Section [N] — [Title] — SECTION PASS WITH NOTES
> Notes: [MINOR/STYLE findings only, one line each]

## Section [N] — [Title] — SECTION BLOCKED
### Findings (full detail required)
- [CRITICAL|MAJOR] [finding description] | Claim ref: [ADV/SKP ID if applicable]
- [repeat per blocking finding]
### Required action: [one sentence specifying the minimum revision]
```

PASS sections: one-line verdict only. Full findings blocks only for BLOCKED and PASS WITH NOTES.
This reduces `audit_log.md` size by ~70% on clean runs without losing traceability.

---

## Holistic Audit Protocol

Read complete `article_draft.md` after all sections pass inline.

**SIMPLE depth:** Run Mini-Audit protocol (see below) instead of full holistic.
**STANDARD/COMPLEX depth:** Run full holistic checklist.

### Holistic Checklist

**Narrative Arc**
- [ ] Thesis stated explicitly in introduction
- [ ] Thesis reflected or resolved in conclusion
- [ ] Section sequence builds logically (no orphaned arguments)

**Cross-Section Coherence**
- [ ] No contradictory claims between sections
- [ ] No repeated identical sentences or paragraphs
- [ ] Transitions between sections are explicit (no abrupt topic jumps)

**Aggregate Citation Metrics**
- [ ] Source diversity: no single source > 30% of total citations
- [ ] Minimum 5 distinct sources for STANDARD/COMPLEX depth articles
- [ ] Source Appendix present and complete

**Word Count**
- [ ] Total within 1,800–3,200 words (or spec override)
- [ ] No section > 30% over its spec word budget

**Conflict Resolution Audit**
- [ ] Every item in `conflict_register.md` is addressed in the draft
- [ ] No new conflicts introduced in prose that weren't in the register

### Publication Readiness Gate (run before holistic verdict)

**Markdown Compliance** — load `references/markdown-style.md` before scoring:
- [ ] Exactly one H1 at document start; no other H1 anywhere (`[MAJOR]`)
- [ ] Heading levels sequential — no skipped increments (`[MAJOR]`)
- [ ] ≥ 50% of H2 and H3 headings phrased as direct questions (`[STYLE]`)
- [ ] No YAML frontmatter in `article_draft.md` body (`[MAJOR]`) — delivery metadata lives in `pipeline_metadata.md`
- [ ] No HTML of any kind — no tags, no `<!-- -->` comments (`[MAJOR]`)
- [ ] All paragraphs ≤ 4 lines; blank line between every paragraph (`[STYLE]`)
- [ ] First paragraph after each heading ≤ 60 words and directly answers the heading (`[STYLE]`)
- [ ] Bold (`**`) used only on entities, data points, exact-match answers — never full sentences (`[STYLE]`)
- [ ] All emphasis uses asterisks — no underscores (`[STYLE]`)
- [ ] Unordered lists use hyphens (`-`) only — no asterisks or plus signs (`[STYLE]`)
- [ ] All links use absolute URLs (`https://`) — no relative paths (`[MAJOR]`)
- [ ] Blockquotes used only for attributed expert/official quotes with named source (`[STYLE]`)
- [ ] Phrase links used for citations — no `[^N]` footnote markers, no footnote block at document base (`[MAJOR]`)
- [ ] All phrase link URLs are absolute `https://` — no relative paths (`[MAJOR]`)
- [ ] ≥ 1 H3 per H2 section with word budget ≥ 300 words (`[MAJOR]`)

**Structure & SEO**
- [ ] Table of Contents present for articles ≥ 1,800 words (`[STYLE]`)
- [ ] Data-heavy sections have VIZ-CANDIDATE image placeholder with descriptive alt text and
      hyphenated WebP filename: `![Chart: takeaway — Source, Year](hyphenated-name.webp)` (`[STYLE]`)
- [ ] Key evidentiary claims bolded — 1–2 per section maximum (`[STYLE]`)
- [ ] Publish date visible near byline in body text (`[STYLE]`)
- [ ] Pipeline metadata (conflicts, red team rating, reader rating) in `pipeline_metadata.md` artifact
      — not embedded anywhere in `article_draft.md` body (`[STYLE]`)

All Publication Readiness Gate failures are `[STYLE]` or `[MAJOR]` as marked.
`[MAJOR]` items block delivery. `[STYLE]` items listed in "Publication Checklist" section of
`audit_report.md` for the polish pass.

### Holistic Verdict

```
PASS — article is ready for validation phases
FAIL — [list CRITICAL/MAJOR findings with section references]
```

On FAIL: one revision cycle targeting CRITICAL/MAJOR sections only. Maximum 1 full-document cycle.

Write `audit_report.md`.

---

## Mini-Audit Protocol (SIMPLE depth only)

Replaces full holistic audit for SIMPLE runs. Three checks, no narrative arc analysis.

Read `article_draft.md`:
- [ ] At least one phrase link `[text](https://url)` present per factual section → FAIL if none
- [ ] No prohibited patterns: `[TODO]`, `[TBD]`, `[INSERT]`, `[Source: `, `[^` → FAIL if found
- [ ] Total word count within 1,200–2,400 range → FAIL if outside

Verdict: `MINI-PASS` or `MINI-FAIL: [failing check]`

Write one-paragraph `audit_report.md`:
```markdown
# Mini-Audit Report (SIMPLE)
Verdict: MINI-PASS / MINI-FAIL
[Failing check description if applicable]
Word count: [N] | Phrase links: [N] | Prohibited patterns: none / [list]
```

`MINI-FAIL` triggers one targeted correction cycle. No second cycle.

---

## @engineer Drafting Mode

When activated as drafting engine with an approved spec:

1. Read `article_spec.md` and `claims_for_drafting.md` (primary claim lookup). 
   Read `fact_check_report.md` only if a specific claim's full verification trace is needed.
   **Precedence rule:** `claims_for_drafting.md` supersedes `article_spec.md`'s Key Claims
   exclusion notes on any conflict — `article_spec.md` is written before FACTCHECK runs and is
   never back-patched, so it can go stale on claim status.
2. Read `CLAUDE.md` and `references/markdown-style.md` for the active project rules.
3. Draft section by section. Yield after each for inline audit.
4. On VERIFIED-UPDATED claims: use the value from `claims_for_drafting.md` column "Final Value" — this already reflects fact-check corrections.
5. On CONFLICTING claims: implement exactly as specified in `conflict_decisions.json`.

---
> References: `references/audit-checklist.md`, `references/markdown-style.md`
