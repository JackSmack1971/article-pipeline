# Audit Checklist — Full Severity-Tagged Rubric

## Severity Definitions

| Level | Meaning | Blocks Section? |
|-------|---------|-----------------|
| [CRITICAL] | Factual error, fabricated citation, unresolved CONFLICTING claim, silent conflict resolution | Yes — SECTION BLOCKED |
| [MAJOR] | Missing citation on factual claim, [Unverified] presented as fact, spec deviation > 30%, word budget > 30% over | Yes — SECTION BLOCKED |
| [MINOR] | Citation format non-standard, word budget 15–30% over, transition quality | No — SECTION PASS WITH NOTES |
| [STYLE] | Prohibited phrase, wrong emphasis type, passive construction | No — SECTION PASS WITH NOTES |

## Full Inline Checklist

### Factual Layer
- [ ] (CRITICAL) Claims map to research_context.md claim IDs
- [ ] (CRITICAL) No claims from [INSUFFICIENT] vectors stated as established fact
- [ ] (CRITICAL) VERIFIED-UPDATED values used (not original research_context.md figures)
- [ ] (MAJOR) [Unverified] claims labeled inline with `[Unverified]` marker
- [ ] (MAJOR) No fabricated or invented citations
- [ ] (MINOR) T3 citations marked `†` per fact-checker protocol

### Citation Layer
- [ ] (CRITICAL) Silent conflict resolution (one side adopted without disclosure)
- [ ] (MAJOR) Factual assertion without a phrase link `[anchor text](https://url)` in prose
- [ ] (MAJOR) Phrase link present but URL is relative (`/path/`) — must be absolute `https://`
- [ ] (MAJOR) Inline `[Source: ...]` text found in prose — must be converted to phrase link
- [ ] (MAJOR) Footnote marker `[^N]` found anywhere in document — banned; convert to phrase link
- [ ] (MAJOR) Footnote block found at document base — banned; remove entirely
- [ ] (MAJOR) Legislation/policy acronym without inline definition on first use
- [ ] (MINOR) T3 source phrase link anchor not marked `†` (correct form: `[anchor†](url)`)
- [ ] (MINOR) Anchor text is generic: "here", "source", "link", "this", bare number

### Markdown Compliance Layer (load `references/markdown-style.md` for full rules)
- [ ] (MAJOR) More than one H1 heading in document
- [ ] (MAJOR) Heading levels skip an increment (e.g., H2 → H4)
- [ ] (MAJOR) YAML frontmatter present in `article_draft.md`
- [ ] (MAJOR) Any HTML tag or comment in document body
- [ ] (MAJOR) Relative URL used in any link (`/path/` instead of `https://domain.com/path/`)
- [ ] (MAJOR) Footnote markers `[^N]` or footnote block found — phrase links are the citation system
- [ ] (STYLE) Fewer than 50% of H2/H3 headings phrased as questions
- [ ] (STYLE) Paragraph exceeds 4 lines without a blank line break
- [ ] (STYLE) First paragraph after heading exceeds 60 words or does not answer the heading
- [ ] (STYLE) Full sentence bolded (bold permitted only on entities, data, exact-match answers)
- [ ] (STYLE) Underscore emphasis used (`__` or `_`) instead of asterisks
- [ ] (STYLE) Unordered list uses `*` or `+` markers instead of `-`
- [ ] (STYLE) Blockquote used for content that is not an attributed expert/official quote
- [ ] (STYLE) Blockquote present without attribution sentence immediately before or after
- [ ] (STYLE) Code block missing language identifier after opening backticks
- [ ] (STYLE) Horizontal rule is not `---` or lacks blank lines before and after

### Conflict Handling Layer
- [ ] (CRITICAL) [CONFLICTING] claim handled differently than `conflict_decisions.json` specifies
- [ ] (MAJOR) "Remains contested" closing without identifying structural incompatibility axis
- [ ] (MINOR) Conflict presented but recommended handling (neutral/position) not clearly signaled to reader

### Style Guide Layer
- [ ] (MAJOR) Meta-narration ("In this article we will explore...")
- [ ] (STYLE) AI-tell phrases ("It's important to note", "It's worth mentioning", "Delving into")
- [ ] (STYLE) Rhetorical question as section opener
- [ ] (STYLE) Filler transitions ("Furthermore", "Moreover", "Additionally" without logical justification)
- [ ] (STYLE) Bold used for non-first-introduction terms
- [ ] (STYLE) Unattributed superlative ("the best", "revolutionary", "the most powerful")
- [ ] (STYLE) Bullet list for narrative content (bullets permitted only for 3+ parallel enumerations)

### Structural Layer
- [ ] (MAJOR) Section scope deviates materially from article_spec.md
- [ ] (MINOR) Word budget exceeded by 15–30%
- [ ] (MAJOR) Word budget exceeded by > 30%
- [ ] (MINOR) Topic sentence does not lead first paragraph

## Holistic-Only Checks

- [ ] (CRITICAL) Thesis not stated in introduction
- [ ] (MAJOR) Thesis not reflected or resolved in conclusion
- [ ] (CRITICAL) Item from conflict_register.md not addressed anywhere in draft
- [ ] (MAJOR) Single source > 30% of total citations
- [ ] (MAJOR) Any `[^N]` footnote marker found anywhere in document — must be converted to phrase link
- [ ] (MAJOR) Footnote block found at document base — must be removed
- [ ] (MAJOR) Phrase link spot-check: For any section citing multiple documents from the same
      organization, verify each phrase link URL leads to the specific document that contains the
      cited claim — not a different document from the same org. Right source family, wrong specific
      document is a MAJOR finding. Method: hover-check the URL against the attributed claim.
      The linked document must contain the specific figure, quote, or finding cited.
- [ ] (MINOR) Total word count outside 1,800–3,200 range
- [ ] (MINOR) Duplicate sentences between sections
- [ ] (STYLE) Abrupt section-to-section transition (no bridging sentence)
