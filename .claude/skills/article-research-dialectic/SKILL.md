---
name: article-research-dialectic
description: >
  Executes adversarial research for article generation: declares a falsifiable thesis,
  runs @advocate (supporting evidence) and @skeptic (disconfirming evidence) streams,
  then synthesizes into a conflict-mapped research context and article specification.
  @skeptic may access source URLs (not claims) from advocate output to prevent redundant
  retrieval while preserving anchoring isolation. Enforces KC-3 and KC-6 kill conditions.
  Triggers on: adversarial research (advocate/skeptic evidence gathering), thesis-based
  research, generate article spec. Activates automatically at Step 1 of
  multi-agent-article-pipeline. Do NOT trigger for writing, auditing, SEO, triage, or
  fact-checking tasks.
---

# Article Research Dialectic — v4

## Pre-Execution Check

Read `pipeline_config.json`:
- `adversarial_dialectic = false` (SIMPLE): Skip Phase 2a/2b. Execute Phase 3 only with unified research pass.
- `adversarial_dialectic = true` (STANDARD/COMPLEX): Execute full three-phase protocol.
- `thesis` and `thesis_confidence` fields are pre-populated by triage — use these directly.

## Phase 1: Research Vector Decomposition

Given the thesis (from `pipeline_config.json.pipeline.thesis`), decompose into 3–7 research vectors.
Each vector = one knowledge gap or claim that the article must address.

```markdown
## Research Vectors
1. [Vector Name]: [1-sentence scope] | Priority: [HIGH|MEDIUM|LOW]
2. ...
```

Both @advocate and @skeptic receive identical vectors.

**Thesis Confidence = HIGH:** Proceed directly to Phase 2a and 2b.
**Thesis Confidence = MEDIUM:** Verify `pipeline_state.json.gates` contains a triage-stage
`confirm` entry for this thesis before proceeding; if absent, halt and return to the triage
gate.

## Phase 2a: @advocate Evidence Gathering

**Delegate to the `article-advocate` subagent** rather than operating as @advocate in this
context. Pass the thesis and the full research vector list in the delegation prompt — the
subagent starts with no context of its own and has no `Read` tool, so it cannot see anything
you don't hand it directly. The isolation is capability-enforced: the subagent literally has
no path to any prior-run artifact, not just an instruction not to look.

Also include the full text of the **Direct Quote Attribution Protocol** and
**Breaking-News Freshness Protocol** (below, under Research Quality Gate) verbatim in the
delegation prompt. The subagent has no `Read` tool and cannot retrieve them itself — if you
omit this text, the subagent has no way to apply the gate.

The subagent gathers SUPPORTING evidence per vector (source priority: Primary > Authoritative
secondary > Empirical data; minimum 3 sources per vector, `[INSUFFICIENT DATA]` if unmet) and
writes `.agents/artifacts/advocate_context.md` itself, ending with a **Source URL Index**
section (flat URL list only, no claims or metadata) — this index is the only part of its
output the skeptic subagent may see. See `.claude/agents/article-advocate.md` for its full
operating method and output format.

## Research Quality Gate (applies to both Phase 2a and 2b)

### Direct Quote Attribution Protocol

For any claim extracted as a direct quoted statement (text in quotation marks attributed
to a named person or organization):

1. Verify the quote exists in a primary or secondary source — do not accept paraphrases
   presented as quotes. If the exact wording cannot be confirmed in a source:
   → Downgrade to `[PARAPHRASE]` classification and strip quotation marks.
   → Flag `[QUOTE-UNVERIFIED]` in the evidence artifact.
2. Verify the attributed speaker is the actual originator. Re-posts, aggregators, and
   "as reported by" citations do not count as attribution verification.
3. Verify the context: confirm the quote was not taken out of context by reading the
   surrounding paragraph in the source.
4. If verification fails after one targeted search → classify the claim as LOW confidence,
   mark `[QUOTE-UNVERIFIED]`, and surface as a pre-spec flag:
   `[EDITORIAL FLAG] Quote "[text]" attributed to [person] — primary source not found`

**This check runs before @fact-checker.** Unverified quotes that enter `article_spec.md`
require structural revision if removed at the fact-check gate.

### Breaking-News Freshness Protocol

For any claim dated within 72 hours of the current session date:

1. Flag as `[BREAKING]` in the evidence artifact alongside the tier rating.
2. Run one targeted verification attempt against the relevant primary source:
   - Financial/donation claims → `fec.gov/data/receipts/individual-contributions/`
   - Arrest/charge/indictment claims → DOJ press releases at `justice.gov/news`
   - Congressional records → `congress.gov`
   - Court filings → PACER or district court public dockets
   - Agency actions → relevant agency `.gov` newsroom
3. If primary source confirms → upgrade to T1/T2. Document the verification URL.
4. If primary source not found after one attempt → accept T3, append `[BREAKING-UNVERIFIED]`.
   Surface a pre-delivery editorial flag in the evidence artifact:
   `[EDITORIAL FLAG] Verify "[claim summary]" at [URL] before publishing`
5. `[BREAKING-UNVERIFIED]` claims must not appear in any article section without an inline caveat:
   *(Editorial note: Verify against [source] before publication.)*
   @engineer reads this flag in `research_context.md` and applies the caveat inline on first draft.

## Phase 2b: @skeptic Evidence Gathering

**Delegate to the `article-skeptic` subagent** rather than operating as @skeptic in this
context. It runs in its own isolated context with no `Read` tool — it cannot reach
`advocate_context.md` under any circumstance, not because it's told not to, but because it
has no capability that could open the file. This is what makes the parallel execution
contract below safe.

Also include the full text of the **Direct Quote Attribution Protocol** and
**Breaking-News Freshness Protocol** (above, under Research Quality Gate) verbatim in the
delegation prompt. The subagent has no `Read` tool and cannot retrieve them itself — if you
omit this text, the subagent has no way to apply the gate.

**Parallel execution contract:** Phase 2a and Phase 2b are formally parallelizable. Once the
`article-advocate` subagent has written its Source URL Index section, extract just that
section's URL list and include it in the `article-skeptic` delegation prompt (a flat list of
URLs, no claims, no metadata) so the skeptic can avoid redundant retrieval — never pass along
the advocate's claims, confidence ratings, or strength assessments. If running the two
subagents in parallel, launch `article-skeptic` immediately with its research vectors; it can
begin searching before the URL index is available and incorporate it once you hand it over.

The subagent gathers DISCONFIRMING evidence per vector — direct rebuttals, failed
replications, methodological critiques, alternative explanations, scope limitations; minimum
2 counter-sources per vector, `[NO DISCONFIRMING EVIDENCE FOUND]` if genuinely none — and
writes `.agents/artifacts/skeptic_evidence.md` itself. See
`.claude/agents/article-skeptic.md` for its full operating method and output format.

## Phase 3: @synthesizer Conflict Mapping

Ingest both evidence artifacts (or unified research if SIMPLE).

Classify each claim pair per vector:

| Classification | Criteria |
|----------------|----------|
| `[CORROBORATED]` | Advocate and skeptic evidence align. High confidence. |
| `[UNCONTESTED]` | Advocate evidence exists, no skeptic counter found. Medium-high confidence. |
| `[CONFLICTING]` | Direct contradiction. Requires explicit handling in article. |
| `[WEAKENED]` | Skeptic evidence narrows but doesn't refute advocate claim. |
| `[INSUFFICIENT]` | Neither side found adequate sources. Knowledge gap. |

For every `[CONFLICTING]` classification, document the conflict axis:
Definitional | Temporal | Methodological | Empirical | Interpretive

**KC-3 Check:** If any single source > 40% of all extracted claims → HALT before writing article_spec.md. Output diagnostic dump.

**KC-6 Check:** If > 50% of vectors classified `[INSUFFICIENT]` → HALT. Output diagnostic dump.
Recommendation: "Research breadth is insufficient. Widen source search, rephrase vectors, or reduce scope."

If both checks pass, write three artifacts:

### research_context.md
Full unified evidence base by research vector. All claims tagged by classification.
Include source tier (`T1/T2/T3`) alongside each claim.

### article_spec.md
```markdown
# Article Specification
## Thesis: [from pipeline_config.json]
## Target Audience: [who + what they already know]
## Pipeline Depth: [from pipeline_config.json]
## Conflict Count: [N CONFLICTING classifications]

## Section Outline
### H2: [Section Title]
- Scope: [1 sentence]
- Word Budget: [N words]
- Key Claims: [ADV-X, SKP-Y, ...]
- Conflicts to Address: [if any]

## Source Mapping
[Which claims map to which sections]

## Risk Flags
[INSUFFICIENT vectors | high-conflict sections | T3-heavy vectors | BREAKING-UNVERIFIED claims]

## Visual Assets
[For each section, result of VIZ-CANDIDATE scan — see below]
```

**Visual Asset Identification (run during spec construction, before handing to orchestrator):**

For each section in `article_spec.md`, check:
- Does this section contain a quantitative comparison (polling, financials, timelines,
  before/after, cross-group data)? → Mark `[VIZ-CANDIDATE]`
- Does this section contain a regulatory or legal process with sequential steps? → Mark `[VIZ-CANDIDATE]`

For each `[VIZ-CANDIDATE]` section, add to the spec under "Visual Assets":
```
Section: [H2 title]
Visual: [descriptive-filename].png
Alt text draft: Chart: [one-sentence takeaway] — [Source name, Year]
```
@engineer renders the alt text inline on first draft. Production generates the actual asset.

If no visual candidates identified: note explicitly: `Visuals: none identified; review if article exceeds 2,000 words`

### conflict_register.md
```markdown
# Conflict Register
## Total Conflicts: [N]

### Conflict C-[N]: [Research Vector]
- Advocate Position: [claim ADV-X]
- Skeptic Position: [claim SKP-Y]
- Axis: [type]
- Conflict Confidence: [HIGH/MEDIUM — how certain is this a real contradiction vs definitional drift]
- Recommended Handling: [present both | author takes position | flag as unresolved]
```

---
> References: `references/claim-taxonomy.md`
