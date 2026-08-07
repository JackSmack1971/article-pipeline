---
name: article-seo-optimizer
description: >
  Generates complete SEO delivery package from a finished article draft: title variants,
  meta description, URL slug, primary and secondary keyword density analysis, JSON-LD
  structured data (Article, FAQPage, BreadcrumbList), internal link suggestions, and an
  on-page checklist. Writes seo_package.md. Triggers on: SEO optimization, article SEO,
  meta description, structured data, JSON-LD, keyword density, slug generation, on-page
  SEO, article distribution, article delivery SEO pass. Activates automatically at Step 6.5
  of the article generation pipeline when seo_pass is enabled in pipeline_config.json. Do NOT
  trigger for research, writing, auditing, or fact-checking tasks.
---

# Article SEO Optimizer

## Purpose

Transforms a completed `article_draft.md` into a distribution-ready artifact with all
on-page SEO elements correctly specified. @engineer writes prose; @seo-optimizer packages
it for publication.

## Pre-Execution Check

Read `pipeline_config.json`:
- If `pipeline.seo_pass` is `false`: Skip. Log `[SEO: SKIPPED — disabled by triage]`.
- Read `thesis` field for primary keyword extraction seed.

## Phase 1: Keyword Analysis

Read `article_draft.md` and `article_spec.md`.

1. Extract primary keyword: the core topic phrase that most precisely captures the article's
   subject. Derive from thesis + most frequent meaningful noun phrase in H2 headings.
2. Extract 3–5 secondary keywords: supporting terms from research vectors.
3. **Topic-title detection:** Check whether the primary keyword is identical or near-identical
   to the article's subject noun (e.g., "Agentic AI" in an article titled "Agentic AI: ...").
   If yes → set `is_topic_title: true`. This activates body-only density mode.
4. Count keyword density:
   - **Standard mode** (`is_topic_title: false`): `(occurrences / total_word_count) × 100`
   - **Body-only mode** (`is_topic_title: true`): Count occurrences in body paragraphs only.
     Exclude: H1, H2, H3 headings; YAML/metadata fields;
     image alt text; table headers. Formula: `(body_occurrences / body_word_count) × 100`
   - Body-only target range: 0.8%–1.5%. Flag if outside range.
   - Report both total density and body-only density in `seo_package.md` when `is_topic_title: true`.
     Total density is informational only; body-only density is the operative gate.
5. Check keyword in: Title H1, first 100 words of body, at least one H2, image alt text (if any),
   conclusion paragraph.

## Phase 2: Title & Meta Generation

Generate 3 title variants following constraints:
- Max 60 characters (renders fully in SERPs)
- Must contain primary keyword
- Must signal article's core finding or tension (not just topic)
- Variant types: (a) Data-led, (b) Outcome-led, (c) Contrarian/tension

Generate meta description:
- 150–160 characters exactly
- Contains primary keyword within first 60 characters
- States what the reader will learn or gain
- Ends with implicit or explicit call to action

Generate URL slug:
- Primary keyword in kebab-case
- Max 5 words
- No stop words, no dates

## Phase 3: Structured Data (JSON-LD)

Generate three JSON-LD blocks:

### Article / BlogPosting
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[selected title]",
  "description": "[meta description]",
  "keywords": "[primary], [secondary1], [secondary2]",
  "wordCount": [N],
  "datePublished": "[YYYY-MM-DD]",
  "author": {"@type": "Person", "name": "[from pipeline_config.json.pipeline.author.name, or '[TODO: author name]' if null]"},
  "publisher": {"@type": "Organization", "name": "[TODO: publisher]"}
}
```

### FAQPage (if article contains 2+ question-formatted subsections or Q&A patterns)
Extract question/answer pairs from article body. Minimum 2, maximum 5 pairs.

### BreadcrumbList
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "[TODO: site root]", "item": "[TODO: URL]"},
    {"@type": "ListItem", "position": 2, "name": "[category]", "item": "[TODO: category URL]"},
    {"@type": "ListItem", "position": 3, "name": "[article title]", "item": "[TODO: article URL]"}
  ]
}
```

Mark `[TODO:]` fields explicitly. Do not invent URLs.

## Phase 4: On-Page Checklist

Audit `article_draft.md` against the checklist in `references/seo-schema.md`.
Output pass/fail per item.

## External Link Audit
- Count live markdown hyperlinks `[text](URL)` in article body
- Minimum 3 external links required. If count < 3 → FAIL item 16.
- List all external domains linked. Flag any domain below T2 tier.

## E-E-A-T Audit
- Read `pipeline_config.json.pipeline.author` first. If explicitly `null`, item 17's Expertise
  signal is N/A (declared project convention), not FAIL — see `references/seo-schema.md`
  "Author state check."
- Score all four signals against `references/seo-schema.md` E-E-A-T Standards table.
- If all (applicable) signals PASS → confirm in `seo_package.md`
- If any FAIL → write "E-E-A-T Gaps" section specifying signal, current state, required edit.

## Phase 5: Write seo_package.md

```markdown
# SEO Package — [Article Title]

## Recommended Title
[best of 3 variants, clearly marked]

## Title Variants
1. [Data-led]
2. [Outcome-led]
3. [Contrarian]

## Meta Description
[150–160 char string]

## URL Slug
[kebab-case slug]

## Keyword Analysis
- Primary: "[keyword]" | Density: [N]% | Status: [IN RANGE|FLAG]
- Secondary: [list]
- Keyword placement: [pass/fail per location]

## JSON-LD Blocks
[Article block]
[FAQPage block if applicable]
[BreadcrumbList block]

## On-Page Checklist
[pass/fail table]

## Internal Link Opportunities
[3–5 suggested anchor texts and target descriptions — no invented URLs]
```

---
> References: `references/seo-schema.md`
