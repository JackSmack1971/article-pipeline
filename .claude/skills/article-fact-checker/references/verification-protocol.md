# Verification Protocol — Source Tier & Search Strategy

## Source Tier Hierarchy

| Tier | Source Type | Weight |
|------|-------------|--------|
| T1 | Primary sources: peer-reviewed papers, official regulatory filings, government datasets, company IR releases | Highest — confirms without needing further verification |
| T2 | Authoritative secondary: recognized experts quoted in institutional publications, established industry reports (Gartner, McKinsey, Forrester) | Strong — corroborates T1 or stands alone for non-scientific claims |
| T3 | Quality journalism: Reuters, AP, NYT, FT, Bloomberg, WSJ (with byline and date) | Acceptable — must have clear T1/T2 cited within the article |
| T4 | Blogs, forum posts, opinion pieces, undated pages | Never sufficient for verification. Counts as [UNVERIFIABLE] regardless of content. |

## Search Strategy by Claim Type

**Statistical claims** (percentages, dollar figures, counts):
- Query: `"[exact figure]" [source org] [year]` OR `[topic] statistics [year] site:[known data org]`
- Accept if within ±10% of original. Flag VERIFIED-UPDATED with exact figure if outside range.

**Causal claims** ("X causes Y", "X led to Z"):
- Query: `[X] [Y] study OR research OR evidence [year range]`
- Require T1 or T2 corroboration. T3 alone insufficient for causal claims.

**Attribution claims** (statements attributed to a person or org):
- Query: `"[attributed person/org]" "[key phrase from claim]"`
- Verify against primary source (speech, press release, official statement).
- If misquoted or out of context: DISPUTED regardless of T-tier of the original source.

**Social post claims** (quotes or statements sourced from social media):
- Before any other verification: check URL domain against attributed platform.
  `x.com` or `twitter.com` = X/Twitter. `linkedin.com` = LinkedIn. `bsky.app` = Bluesky.
  Domain mismatch → `[PLATFORM-MISMATCH]` → DISPUTED immediately.
- Verify the post exists at the URL (not deleted, not a quote-post misattribution).
- Verify the attributed account is the verified/official account of the named person or org.
- Social posts that cannot be located at the cited URL after one search attempt → UNVERIFIABLE.

**Trend/directional claims** ("X is growing", "adoption is declining"):
- Query: `[X] trend [year] data OR report`
- OUTDATED if the trend has materially reversed since the original research date.

## Freshness Policy

| Claim Type | Max Age Before OUTDATED Flag |
|------------|------------------------------|
| Regulatory / legal status | 6 months |
| Software version / API specs | 3 months |
| Market share / adoption rates | 12 months |
| Academic findings | 36 months (flag if contradicted by newer meta-analysis) |
| Historical facts | No expiry |

## T3 Citation Acceptance Protocol

A T3 source may be accepted ONLY if:
1. A re-search attempt for T1/T2 corroboration was made and documented.
2. The T3 source itself explicitly cites a T1/T2 within the article text.
3. The accepted T3 citation is marked `†` in `fact_check_report.md` with the documented re-search note.

If these conditions are not met, verdict = `[UNVERIFIABLE]`.
