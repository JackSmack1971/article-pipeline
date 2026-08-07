# Markdown Style Rules — Article Draft Standard

All rules apply to `article_draft.md`. This file is the public-facing deliverable.
No YAML frontmatter. No HTML tags. No HTML comments. Pure Markdown only.

---

## Heading Rules

**H1:** Exactly one `#` heading. Placed at the very start of the document.
Contains the primary keyword or target entity. No other `#` headings anywhere in the draft.

**Sequence:** Headings must increment without skipping levels: H1 → H2 → H3.
Never jump from H2 to H4. Never use a heading purely to make text larger.

**Question phrasing:** At least 50% of all H2 and H3 headings must be phrased as
direct, explicit questions. This maps to conversational search intent and AI overview triggers.
- Acceptable: `## Why Does Partisan Accountability Diverge on Political Violence?`
- Not acceptable: `## Partisan Accountability Divergence`

**Keyword placement:** Include secondary keywords and related entities naturally within
H2 headings to strengthen semantic clustering. Do not keyword-stuff — one natural placement per heading.

---

## Paragraph Rules

**Max length:** 3–4 lines of text per paragraph. Hard limit. If a paragraph runs longer,
break it with a blank line. This is not aesthetic — it is extraction-critical for AI agents.

**First paragraph rule:** The first paragraph immediately after any heading must directly
and concisely answer the question posed by that heading. Target 40–60 words.
Do not begin with scene-setting, historical preamble, or meta-commentary.

**Blank lines:** Separate every paragraph with one completely blank line to generate proper
`<p>` elements. Never use two or more consecutive blank lines.

---

## Emphasis Rules

**Bold (`**`):** Apply only to primary entities, exact-match answers, and critical data points.
Never bold entire sentences or lengthy clauses — this dilutes semantic weight.
Maximum 1–2 bold instances per section (unchanged from existing pipeline rule).

**Italic (`*`):** Use for titles of works, technical terms on first introduction,
or subtle stress. Never use for decorative emphasis.

**Syntax:** Asterisks only — `**bold**` and `*italic*`. Never underscores.
Underscores cause parsing errors with intra-word emphasis.

---

## Citation Rules (Phrase Links)

All citations use inline phrase links. No footnote markers, no footnote block, no `[Source: ...]` text,
no `[^N]` syntax anywhere in `article_draft.md`.

**Format:** Wrap the natural phrase in prose that carries the claim:

```markdown
[meaningful anchor text](https://absolute-url)
```

**Examples:**

```markdown
❌ Wrong — naked URL:
The FEC recorded a $2.4 million gap. https://www.fec.gov/data/...

❌ Wrong — footnote marker:
The FEC recorded a $2.4 million gap[^1].

❌ Wrong — generic anchor:
The FEC recorded a [source](https://www.fec.gov/data/...) gap.

✅ Correct — phrase link wraps the finding:
[FEC filings show a $2.4 million contribution gap](https://www.fec.gov/data/...) between the two periods.

✅ Correct — anchor is the org name + action:
[Haun Ventures closed a $1 billion fund](https://doi.org/10.xxxx/xxxxx) focused on crypto infrastructure.
```

**Anchor text rules:**
- Must describe the claim or destination. Minimum 3 words.
- Never: "here", "source", "link", "read more", "this", bare numbers, "click here".
- Preferred: the specific finding, the org name + action, the document title fragment.

**URL rules:** Absolute `https://` always. DOI links (`https://doi.org/...`) preferred for academic sources.

**Source tier signaling:**

| Tier | Treatment |
|:-----|:---------|
| T1 | Phrase link, no marker. URL signals authority. |
| T2 | Phrase link, no marker. |
| T3 | Append `†` to anchor: `[finding from quality source†](url)` |
| `[BREAKING-UNVERIFIED]` | Phrase link + caveat: `*(Editorial note: Verify before publication.)*` |
| `[NAMED-ENTITY-UNVERIFIED]` | No link. Remove named entity. Use generic form. |
| `[QUOTE-UNVERIFIED]` | No link. Downgrade to paraphrase, strip quotation marks. |

**VERIFIED-UPDATED values:** Use the updated figure from `claims_for_drafting.md`.
Link to the verification source URL (not the original research source).

**No trailing citation block.** `article_draft.md` ends with the last content paragraph.

---

## Blockquote Rules

Use `>` exclusively for direct quotes from verifiable experts, official reports,
regulatory documents, or recognized industry publications.

**Attribution required:** The sentence immediately before or after the blockquote must
explicitly name the quoted entity, role, and date.

```markdown
Federal Election Commission Chair Dara Lindenbaum stated in her April 2026 testimony:

> The discrepancy in third-party bundling between the two organizations exceeds
> any threshold attributable to organizational size alone.
```

**Multi-paragraph quotes:** Every blank line inside a blockquote must contain the `>` character
to prevent the quote from breaking into separate blocks.

**What blockquotes are NOT for:** Callout boxes, visual emphasis, summarizing your own argument,
or any content that is not an attributed direct quote. Use prose for all of these.

---

## List Rules

**Marker:** Hyphens only (`-`). Never asterisks (`*`) or plus signs (`+`) for unordered lists.
This distinguishes list items from emphasis markers in raw source.

**Parallel structure:** Every item in a list must begin with the same part of speech
(all action verbs, all nouns, all past participles). Mixed structure fails NLP parsing.

**Atomic items:** If a list item requires more than one sentence, it must become a subheading.
Lists are for enumeration, not exposition.

**Narrative content:** Do not use lists for narrative text or flowing argument.
Lists are permitted only for 3+ parallel, genuinely enumerable items.

---

## Link Rules

**Anchor text:** Must explicitly describe the destination entity or page.
Never use "click here," "read more," "this article," or "here."
- Correct: `[FEC's individual contribution database](https://www.fec.gov/...)`
- Wrong: `[click here](https://www.fec.gov/...)`

**Placement:** Embed links contextually within paragraph prose.
Do not dump lists of related links at the document end.

**Absolute URLs only:** Always `https://domain.com/full/path/`.
Never relative paths (`/path/`). Markdown files are syndicated and extracted raw by AI agents;
relative links break immediately upon extraction.

---

## Image Rules

**Alt text:** Accurately and explicitly describe the image's specific content and function.
Format for VIZ-CANDIDATE placeholders: `![Chart: one-sentence takeaway — Source, Year](hyphenated-filename.webp)`

**Decorative images:** Use empty brackets `![]` so screen readers skip them.

**Filename format:** Hyphen-separated, descriptive, lowercase:
`actblue-donation-gap-q1-2026.webp` — never `IMG002.jpg` or `chart1.png`.

**File format:** Link to WebP or AVIF. Never JPG or PNG for new image references.

---

## Table Rules

**Use for:** Comparative data, pricing tiers, feature breakdowns, scoring matrices.
Never use descriptive paragraphs where a table would convey the same information more clearly.

**Headers:** All column headers must be explicit and keyword-rich. No blank header cells.

**Alignment:** Define alignment with colon syntax in the separator row.
Right-align all numerical data and pricing: `---:`. Left-align text: `:---`. Center for labels: `:---:`.

**Cell content:** Concise and factual. No full paragraphs in cells.
Use inline code (`` ` ``) or bold (`**`) for technical terms or winning features within cells.

**No merged cells:** Pure Markdown does not support `colspan` or `rowspan`.
Never attempt them — they break all parsers.

---

## Code Block Rules

**Fenced blocks:** Always append a language identifier immediately after the opening backticks.
```python
# correct
```
``` 
# wrong — no language specified
```

Supported identifiers: `python`, `javascript`, `typescript`, `bash`, `json`, `sql`, `markdown`, `yaml`, `html`, `css`.

**Inline code:** Use single backticks for any technical entity embedded in prose:
variable names, file paths, API endpoints, CLI commands, keyboard shortcuts, field names.
This flags the term as a technical entity and prevents search parsers from treating it as prose.

---

## Horizontal Rule Rules

**Use for:** Thematic breaks only — shifts in narrative, section separators where a heading
would be semantically wrong, or preventing context bleeding in long-form content.

**Syntax:** Three hyphens only: `---`. Never `***` or `___`.

**Spacing:** Always preceded and followed by a completely blank line.

**Prohibited use:** Never use for visual decoration, faux borders, or separating list items.

---

## Prohibited Patterns (new — supersede any conflicting checklist items)

| Pattern | Prohibition |
|:--------|:-----------|
| YAML frontmatter in `article_draft.md` | Banned. Delivery metadata goes to `pipeline_metadata.md`. |
| HTML tags of any kind | Banned. `<div>`, `<span>`, `<!-- ... -->` all prohibited. |
| Inline `[Source: ...]` citation | Banned. Use phrase links `[text](url)`. |
| Footnote markers `[^N]` in prose | Banned. No footnote system. |
| Footnote block at document base | Banned. No trailing citation block. |
| Relative URLs | Banned. Always absolute `https://`. |
| Underscore emphasis (`__bold__`) | Banned. Use `**bold**`. |
| Blockquote for non-attributed content | Banned. Attribution sentence required. |
| List markers `*` or `+` | Banned. Use `-`. |
| Code blocks without language ID | Banned. |
| Heading levels skipped | Banned. Sequential increment only. |
| Multiple H1 headings | Banned. Exactly one. |
