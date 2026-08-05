# SEO Schema — On-Page Checklist & Standards

## On-Page Checklist (Scored Pass/Fail)

| # | Check | Criteria |
|---|-------|----------|
| 1 | Title length | ≤ 60 characters |
| 2 | Primary keyword in title | Must appear verbatim or as close variant |
| 3 | Meta description length | 150–160 characters |
| 4 | Primary keyword in meta | Within first 60 characters of meta |
| 5 | H1 uniqueness | Exactly one H1; matches or close-matches title |
| 6 | Keyword in intro | Primary keyword within first 100 words |
| 7 | Keyword in at least one H2 | Verbatim or semantically equivalent |
| 8 | No keyword stuffing | Density < 2.0% |
| 9 | Article word count | ≥ 1,800 words (flags if below) |
| 10 | Source Appendix present | Must exist and contain ≥ 3 citations |
| 11 | Internal link suggestions | ≥ 3 identified (actual URLs not required) |
| 12 | Image alt text fields | Populated if images referenced; `[TODO]` if none |
| 13 | No orphan H3s | Every H3 must have a parent H2 |
| 14 | FAQ schema eligible | ≥ 2 question patterns found in body |
| 15 | Structured data complete | All non-TODO JSON-LD fields populated |
| 16 | External hyperlinks in body | ≥ 3 live markdown links `[text](URL)` in article body — zero external links = FAIL |
| 17 | E-E-A-T block present | Author credentials, expertise signal, and at least one primary-source date within body — see E-E-A-T standards below. N/A (not FAIL) if `pipeline_config.json.pipeline.author` is explicitly `null` |

## Keyword Density Standards

- **Standard mode (is_topic_title: false):**
  - Primary keyword: 0.8%–1.5% total. Flag if outside range. CRITICAL if > 2.5%.
  - This is the operative gate for most articles.

- **Body-only mode (is_topic_title: true):**
  - Primary keyword: 0.8%–1.5% of body words only (headings, phrase link URLs, alt text excluded).
  - Total density is informational — may legitimately exceed 1.5% due to structural inflation.
  - CRITICAL threshold applies to body-only density only: body-only > 2.5% = CRITICAL.
  - Total density > 2.5% is NOT a CRITICAL flag in body-only mode; document it, do not block.
  - Both figures must appear in `seo_package.md`:
    `Primary keyword density — total: N% | body-only: N% | operative gate: body-only`

- **Secondary keywords:** 0.3%–0.8% each (total); no secondary exceeds primary body-only density.
- **Forbidden:** Keyword repetition in consecutive sentences; keyword in every heading.

## Title Variant Formulas

| Type | Formula |
|------|---------|
| Data-led | `[Stat or Finding]: [What It Means for X]` |
| Outcome-led | `How [X] [Achieves/Prevents/Changes] [Y]` |
| Contrarian | `Why [Common Belief] Is [Wrong/Incomplete/Overstated]` |

## Slug Construction Rules

1. Extract primary keyword phrase.
2. Remove stop words (the, a, an, of, in, for, to, and, or, but).
3. Convert to lowercase kebab-case.
4. Maximum 5 tokens after stop word removal.
5. No dates, no version numbers, no brand names unless they are the primary keyword.

## JSON-LD Validation Notes

- `datePublished`: Use ISO 8601 format. If unknown, mark `[TODO: publication date]`.
- `author`: If multi-author, use `@type: "Organization"` for the publisher field instead.
- `FAQPage`: Only generate if 2+ distinct question-answer pairs can be extracted from body text. Do not fabricate Q&A pairs.
- `wordCount`: Use the pipeline's canonical Markdown-token count from
  `scripts/artifact_contract.py`; do not substitute a separate body-only count.

## E-E-A-T Standards (Experience, Expertise, Authoritativeness, Trustworthiness)

Google's quality rater guidelines score content on four signals. For each, check whether
the article satisfies the minimum threshold and note what's present vs. missing.

| Signal | Minimum Standard | How to Surface It |
|--------|-----------------|------------------|
| **Experience** | First-hand or original research present | FEC data queries, original data analysis, named primary sources with dates |
| **Expertise** | Author credentials visible near byline | Name + title/affiliation OR "X years covering Y" — not anonymous byline |
| **Authoritativeness** | ≥ 3 phrase links to T1/T2 sources visible in body prose | Phrase link anchor text must name the org or finding; URL must be absolute and resolve to the correct document |
| **Trustworthiness** | No unattributed claims; corrections process implied | Source Appendix complete; no `[Unverified]` claims without label |

**Author state check (do this first):** Read `pipeline_config.json.pipeline.author`.
- **Populated** (`name` set): score the Expertise signal normally against the criteria below.
- **Explicitly `null`:** this is a declared project convention, not a rediscovered gap. Score
  item 17 as **N/A** rather than FAIL — evaluate only the other three E-E-A-T signals
  (Experience, Authoritativeness, Trustworthiness) for pass/fail. Note the author state as
  "no author declared by project convention" in `seo_package.md`, once, without treating it as
  a blocking gap or prompting the user about it.

**Checklist item 17 PASS criteria (all required, only when `author` is populated):**
- [ ] Author name and at least one credential appears in byline or first paragraph
- [ ] ≥ 3 phrase links in body prose link to T1/T2 sources with absolute URLs
- [ ] ≥ 1 phrase link points to a T1 primary source (gov site, official filing, peer-reviewed DOI)
- [ ] No footnote block present — phrase links are the citation system; trailing footnote block = fail

**If checklist item 17 FAILS** (author populated but criteria unmet): Add to `seo_package.md`
under a dedicated "E-E-A-T Gaps" section specifying exactly which signals are absent and the
minimum edit to resolve each. Do not mark the article as distribution-ready until the author
reviews the E-E-A-T gap list.
