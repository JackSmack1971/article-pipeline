# Great Article Standard v1

**Status:** Proposed normative contract  
**Scope:** `JackSmack1971/article-pipeline`  
**Version:** 1.0  
**Purpose:** Define what this repository means by a **great article**, how greatness is measured, which properties are non-negotiable, and what evidence is required before the article pipeline or control plane may change its behavior in pursuit of greater quality.

---

# 0. Purpose and Governing Principle

The purpose of the article pipeline is not merely to produce grammatically competent, SEO-ready, or technically publishable content.

Its purpose is to produce articles that are:

> **exceptionally truthful, deeply researched, intellectually honest, useful, original, comprehensible, memorable, and appropriate to the human reader they are intended to serve.**

The system SHALL optimize for becoming progressively better at producing such articles over repeated runs.

However:

> **Truth is a constraint on greatness, not one component that may be traded against other components.**

An article with beautiful prose, high search performance, strong emotional impact, high novelty, or superior competitor coverage SHALL NOT qualify as great when its material factual claims are unsupported, misleading, stale, materially overgeneralized, fabricated, or incorrectly attributed.

The quality ordering is therefore **lexicographic rather than compensatory**:

```text
TRUTH / EPISTEMIC INTEGRITY
        ↓
INTELLECTUAL HONESTY
        ↓
READER VALUE
        ↓
ORIGINALITY / INFORMATION GAIN
        ↓
INSIGHT / SYNTHESIS
        ↓
HUMANITY / MEMORABILITY
        ↓
SEARCH / DISTRIBUTION OPTIMIZATION
```

A lower layer SHALL NOT override failure at a higher layer.

SEO packages greatness.

SEO does not define greatness.

---

# 0.1 Relationship to Existing Repository Contracts

This standard complements rather than replaces the repository's existing deterministic artifact validation, independent factual/citation grading, editorial grading, and Qualified Publish Rate evaluation.

The current evaluation system is principally designed to determine whether an article is **publishable and defensible** through artifact validity, factual/citation thresholds, editorial thresholds, isolation guardrails, and human-rescue constraints. 

This standard defines the layer above publishability:

> **Whether the article is unusually valuable and substantially better than competent alternatives.**

An article MUST first satisfy the applicable publishability requirements before it may qualify under this Great Article Standard.

---

# 0.2 Normative Language

The terms below have specific meanings.

**MUST / SHALL** — mandatory. Violation disqualifies the relevant result.

**MUST NOT / SHALL NOT** — prohibited.

**SHOULD** — expected unless a documented article-specific reason justifies an exception.

**SHOULD NOT** — normally prohibited unless a documented reason justifies the exception.

**MAY** — optional.

**Hard Gate** — failure cannot be offset by another score.

**Excellence Dimension** — quality dimension optimized after all Hard Gates pass.

**Material Claim** — a factual assertion that materially affects the thesis, reader understanding, recommended action, comparison, interpretation, or credibility of the article.

---

# 0.3 Definition of a Great Article

For this repository:

> **A great article is the most truthful, useful, original, comprehensible, intellectually honest, and memorable treatment of a defined reader's problem that the available evidence can reasonably support.**

Greatness SHALL be evaluated relative to:

1. the target reader;
2. the article's intended purpose;
3. the state of available evidence;
4. the strongest relevant competing content;
5. the article archetype;
6. the information environment at the time of publication.

Greatness is therefore contextual.

A great scientific explainer is not judged identically to a great investigative analysis.

A great executive decision guide is not judged identically to a human-centered narrative.

---

# 1. Hard Epistemic Invariants

The following invariants are non-negotiable.

Failure of any applicable invariant prevents Great Article qualification regardless of all other scores.

## E1. Material Claim Accountability

Every material factual claim MUST be represented by a traceable evidence record.

The system MUST be capable of answering:

- What exactly is being claimed?
- What evidence supports it?
- What source produced that evidence?
- When was the evidence produced?
- What is the source's quality?
- What uncertainty applies?
- What contradictory evidence exists?
- What rhetorical strength is justified?

Target:

**100% of material factual claims accounted for.**

A measured evaluator may contain uncertainty, but the production standard SHALL NOT intentionally budget for a percentage of unsupported material claims.

---

# E2. Source Existence and Attribution Integrity

Every cited source MUST exist and MUST be attributed to the correct:

- author;
- institution;
- publication;
- platform;
- paper;
- dataset;
- filing;
- government body;
- document.

Fabricated citations are prohibited.

Mismatched citations are prohibited.

A real source attached to a claim it does not support SHALL count as an integrity failure.

---

# E3. Claim-Support Fidelity

A citation MUST support the proposition expressed around it.

Citation quantity SHALL NOT substitute for citation quality.

The article MUST NOT imply stronger support than the source provides.

The existing independent factual grader already follows the useful principle of evaluating whether sources support the proposition as written rather than merely whether a URL exists. 

This principle SHALL remain foundational.

---

# E4. Scientific Scope Fidelity

When translating empirical research into prose, the article MUST preserve material scope constraints including, where relevant:

- population;
- sample;
- jurisdiction;
- geography;
- time period;
- treatment/exposure;
- comparator;
- measured outcome;
- effect size;
- confidence interval;
- study design;
- causal status;
- limitations;
- applicability.

The article MUST NOT broaden a finding beyond the population, condition, effect, or conclusion justified by the underlying research.

This is a hard requirement because recent empirical work comparing 4,900 LLM-generated scientific summaries with their sources found systematic overgeneralization, with LLM summaries nearly five times more likely than human summaries to generalize beyond the original research.

---

# E5. Causal Fidelity

Correlation MUST NOT silently become causation.

Association MUST NOT become mechanism.

A modeled estimate MUST NOT become observed fact.

A laboratory result MUST NOT silently become real-world effectiveness.

A single observational study MUST NOT silently become scientific consensus.

Any causal statement MUST have evidence appropriate to the causal strength of the language used.

---

# E6. Freshness and Supersession Integrity

Claims presented as current MUST be checked against the most current evidence reasonably available for that claim class.

The newest publication SHALL NOT automatically outrank stronger evidence.

"Latest evidence" means:

> the most current evidence of sufficient rigor and relevance, considered alongside the strongest existing evidence base.

The pipeline MUST detect when:

- figures have changed;
- regulations have changed;
- products have changed;
- policies have changed;
- scientific consensus has evolved;
- later research materially supersedes earlier findings.

Stale material MUST NOT be presented as current fact.

---

# E7. Uncertainty Preservation

Uncertainty found during research MUST survive synthesis and drafting.

The pipeline MUST NOT transform:

```text
possible → probable
associated → caused
suggests → proves
one study → research shows
estimate → fact
preprint → established finding
disputed → settled
unknown → implied certainty
```

without new evidence supporting that transformation.

---

# E8. Conflict Integrity

Material credible disagreement MUST remain visible until legitimately resolved.

The system MUST NOT:

- suppress inconvenient evidence;
- silently choose a preferred side;
- create false balance between unequal evidence;
- hide known contradictions;
- erase methodological limitations.

The weight given to competing positions SHOULD reflect evidence quality, not artificial symmetry.

---

# E9. No Fabricated Human Experience

Human voice SHALL NOT be created through invented first-person experience.

The system MUST NOT fabricate:

- interviews;
- firsthand testing;
- personal history;
- observations;
- quotations;
- scenes;
- emotions attributed to real people;
- private motivations;
- credentials;
- field experience.

Humanity must come from truthful specificity.

---

# E10. Provenance Integrity

Quantitative and high-impact claims MUST remain traceable to their origin.

Whenever practical, the strongest available source SHOULD be the citation:

```text
original dataset > analysis of dataset
original paper > article describing paper
official filing > article describing filing
legislation/regulation > commentary describing it
company documentation > third-party paraphrase
```

Secondary sources MAY be valuable for interpretation, criticism, or context.

They SHOULD NOT replace an accessible primary source merely for convenience.

---

# E11. No False Authority

The article MUST NOT imply expertise, consensus, certainty, or firsthand knowledge that does not exist.

Credential gaps MUST remain explicit rather than being solved through fabrication.

---

# E12. Epistemic Revision Supremacy

If a late-stage process discovers a factual defect, the article MUST reopen the affected content.

No concept of:

- deadline;
- SEO readiness;
- editorial polish;
- competitor superiority;
- prior approval;
- completed stage;
- evaluator score

may protect a factual error from correction.

---

# 2. The Greatness Vector

Greatness SHALL NOT be represented internally as one opaque score.

The canonical quality representation SHALL contain two components:

```text
G = (E, X)
```

where:

**E = Epistemic Gate Vector**

and

**X = Excellence Vector**

---

## 2.1 Epistemic Gate Vector

The Epistemic Gate Vector records applicable invariants from Section 1.

Example conceptual representation:

```text
E = {
  material_claim_accountability,
  citation_integrity,
  claim_support_fidelity,
  scope_fidelity,
  causal_fidelity,
  freshness_integrity,
  uncertainty_preservation,
  conflict_integrity,
  provenance_integrity
}
```

These values are pass/fail plus diagnostic metrics.

They are not averaged.

Any blocking failure produces:

```text
EPISTEMICALLY_INELIGIBLE
```

and the Greatness evaluation stops.

---

# 2.2 Excellence Vector

For epistemically eligible articles:

```text
X = {
  RQ,
  CQ,
  IG,
  SI,
  IH,
  RT,
  AF,
  HR,
  SF,
  PU
}
```

### RQ — Research Quality

Measures:

- evidence authority;
- methodological quality;
- triangulation;
- independence;
- empirical depth;
- appropriate use of primary and scholarly sources.

### CQ — Coverage Quality

Measures whether the article addresses the questions the reader actually needs answered.

### IG — Information Gain

Measures valuable information or treatment that materially exceeds the relevant competitor corpus.

### SI — Synthesis and Insight

Measures whether evidence is turned into useful explanatory models, distinctions, implications, frameworks, or conclusions rather than merely summarized.

### IH — Intellectual Honesty

Measures proportional uncertainty, serious treatment of counterevidence, limitations, and separation of fact from inference.

**IH is additionally subject to a universal minimum floor and therefore cannot be sacrificed by archetype weighting.**

### RT — Reader Transformation

Measures whether the reader finishes the article meaningfully better able to understand, explain, evaluate, decide, or act.

### AF — Audience Fit

Measures vocabulary, assumed knowledge, explanatory depth, examples, pacing, and conceptual difficulty against the declared audience.

### HR — Human Resonance

Measures specificity, emotional truth, concreteness, voice, memorable framing, narrative appropriateness, and absence of generic machine-like prose.

### SF — Structure and Flow

Measures information architecture, momentum, sequence, transitions, pacing, and whether each section earns its place.

### PU — Practical Utility

Measures usable value:

- frameworks;
- examples;
- decision criteria;
- comparisons;
- checklists;
- explanations;
- implications;
- actions;
- warnings;
- models.

---

# 2.3 Scoring Principle

Excellence dimensions SHOULD ultimately be normalized to a 0–100 scale through independently calibrated evaluation.

Initial interpretation:

```text
90–100  Exceptional
80–89   Excellent
70–79   Strong
60–69   Competent
<60     Materially improvable
```

These labels are provisional until calibrated against human judgment.

No threshold MAY be weakened merely because the pipeline fails to reach it.

---

# 2.4 Greatness Classification

Initial v1 categories:

### PUBLISHABLE

Existing publication controls pass.

### STRONG

Publishable plus no Excellence Dimension below 70.

### GREAT

Publishable plus:

- archetype-weighted Excellence Index ≥ 82;
- IH ≥ 85;
- CQ ≥ 85;
- material competitive information gain demonstrated;
- core Reader Transformation requirements substantially achieved.

### EXCEPTIONAL

Publishable plus:

- archetype-weighted Excellence Index ≥ 90;
- no Excellence Dimension below 80;
- IH ≥ 90;
- core-question coverage ≥ 95%;
- demonstrated competitive information advantage;
- independent evaluations show consistent superiority over strong alternatives.

These thresholds are hypotheses to be calibrated.

They are not empirical truths.

---

# 3. Article Archetypes and Weighting

Complexity determines how much control-plane machinery is required.

Archetype determines what excellence means for the resulting article.

Every article MUST declare a primary archetype before drafting.

A secondary archetype MAY be declared when appropriate.

Epistemic gates and the IH floor apply universally regardless of archetype.

The initial Excellence Index SHALL weight the remaining dimensions as follows.

| Archetype | RQ | CQ | IG | SI | RT | AF | HR | SF | PU |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Scientific / Scholarly Explainer | 20 | 15 | 10 | 15 | 10 | 10 | 5 | 5 | 10 |
| Investigative / Current-Affairs Analysis | 20 | 10 | 15 | 15 | 10 | 5 | 10 | 10 | 5 |
| Strategic / Executive Decision Guide | 15 | 10 | 15 | 15 | 15 | 10 | 5 | 5 | 10 |
| Technical Tutorial / Technical Explainer | 10 | 15 | 5 | 10 | 15 | 15 | 5 | 10 | 15 |
| Comparative / Commercial Decision Guide | 15 | 15 | 15 | 10 | 10 | 10 | 5 | 5 | 15 |
| Argument / Thought Leadership | 15 | 10 | 15 | 20 | 10 | 10 | 10 | 5 | 5 |
| Human-Centered Narrative / Feature | 15 | 10 | 10 | 10 | 10 | 10 | 20 | 10 | 5 |
| Breaking-News Analysis | 25 | 10 | 10 | 15 | 10 | 10 | 5 | 10 | 5 |

Weights total 100 for each archetype.

Weights MUST NOT affect hard epistemic requirements.

An article SHOULD NOT become narrative simply because narrative receives a high weight.

Archetype selection MUST precede prose optimization.

---

# 4. Reader Transformation Contract

Every article MUST define the intended change in the reader before substantial drafting begins.

This SHALL be called the **Reader Transformation Contract (RTC).**

The RTC MUST describe:

## 4.1 Reader Before-State

- Who is this reader?
- What do they already know?
- What are they likely to misunderstand?
- What question brought them here?
- What decision or problem are they facing?
- What vocabulary can be assumed?
- What evidence will they require to trust the article?
- What emotional relationship do they have to the topic?

## 4.2 Reader After-State

At completion, what should the reader be able to:

- explain;
- distinguish;
- evaluate;
- decide;
- do;
- avoid;
- question;
- remember?

## 4.3 Core Questions

The article MUST identify questions whose absence would make the article incomplete.

Questions SHOULD be classified as:

```text
CORE
BACKGROUND
DECISION
SKEPTICAL
EMPIRICAL
FRESHNESS
COUNTERFACTUAL
FOLLOW-UP
```

Research supports explicit sub-question decomposition both for retrieval quality and response coverage. A 2025 retrieval study reported substantial gains from question decomposition, and separate NAACL work found core sub-question coverage strongly associated with human preference and improved generated answers.

Accordingly:

> Research completion SHALL be defined partly by important-question coverage rather than source count.

---

# 4.4 Transformation Test

A finished article SHOULD be evaluable without relying solely on an editor's impression.

A blind reader/evaluator SHOULD be asked to use only the article to answer predeclared questions such as:

- What is the article's central conclusion?
- What evidence most strongly supports it?
- What evidence limits it?
- What should the reader now understand that they might not have understood before?
- What remains uncertain?
- What would change the recommendation?
- What action, if any, is justified?

Reader Transformation is demonstrated when these answers are accurate and sufficiently complete.

---

# 5. Competitor Opportunity Model

Competitor research exists to discover **reader value opportunities**.

It does not exist to imitate competitors.

The system SHALL define a relevant Competitive Corpus using an appropriate mixture of:

- strongest ranking pages;
- direct editorial/commercial competitors;
- authoritative subject-matter sources;
- high-performing specialist publications;
- community discussions where useful;
- recent expert commentary;
- first-party documentation;
- other pages the target reader would plausibly encounter.

Pages MUST be compared only when their search intent or reader purpose is sufficiently related.

---

# 5.1 Competitive Analysis Dimensions

Each relevant competitor SHOULD be abstracted into:

- target audience;
- apparent intent;
- thesis/angle;
- questions answered;
- questions omitted;
- evidence used;
- evidence quality;
- evidence age;
- unique information;
- examples;
- original data;
- practical tools;
- recommendations;
- explanatory strengths;
- explanatory weaknesses;
- unresolved questions;
- questionable claims;
- stale claims;
- reader-friction points.

The Competitive Corpus SHALL be analyzed structurally.

Competitor wording SHOULD NOT be passed directly into the drafting context when an abstracted representation can accomplish the task.

The goal is independent superiority, not stylistic averaging.

---

# 5.2 Opportunity Classes

Competitive opportunities SHALL be divided into four classes.

## MUST MATCH

Information that strong competitors consistently provide and the target reader reasonably expects.

Omitting this material causes incompleteness.

## MUST BEAT

Material competitors address inadequately because of:

- weak evidence;
- stale evidence;
- poor explanation;
- shallow reasoning;
- incomplete treatment;
- weak examples;
- poor uncertainty handling;
- low utility.

## MUST ADD

High-value information, synthesis, evidence, models, analysis, tools, or questions absent from the competitive corpus.

This category represents the primary information moat.

## MUST AVOID

Patterns common in competitor content that reduce quality:

- unsupported conventional wisdom;
- stale statistics;
- copied framing;
- generic introductions;
- filler;
- unearned certainty;
- superficial summaries;
- duplicated talking points;
- misleading comparisons.

---

# 5.3 Competitive Opportunity Score

Candidate opportunity `j` MAY be represented as:

```text
CO_j =
0.30(RI) +
0.20(CG) +
0.20(EG) +
0.15(FG) +
0.15(UG)
```

where:

**RI — Reader Importance**  
How much does the gap matter to the target reader?

**CG — Coverage Gap**  
How poorly does the competitor corpus address it?

**EG — Evidence Gap**  
How much stronger can our evidence be?

**FG — Freshness Gap**  
How materially newer or more current can our answer be?

**UG — Utility Gap**  
How much more useful can our treatment be?

Each component is normalized 0–1.

Competitive opportunities MUST NOT be pursued when credible evidence cannot support them.

---

# 5.4 Search Competition Is Not the Sole Standard

The system SHOULD seek to produce substantial additional value compared with other available pages rather than merely rewrite them.

This aligns with current Google people-first guidance, which explicitly asks whether content provides original information, substantial analysis, insight beyond the obvious, and substantial value compared with other search results.

Search guidance SHALL remain secondary to reader value and truth.

---

# 6. Scholarly Evidence Standard

When an article makes material empirical claims, the pipeline MUST identify the evidence class required to support them.

Generic web retrieval SHALL NOT be treated as a complete scholarly evidence search.

A 2025 systematic review of GenAI use in evidence synthesis found very high miss rates when generative systems were used for literature searching, supporting the need for structured retrieval and human/evaluator safeguards rather than assuming LLM search is exhaustive.

---

# 6.1 Evidence Retrieval Lanes

The pipeline SHOULD conceptually distinguish at least:

### Current-State Lane

Appropriate for:

- current events;
- current pricing;
- current regulation;
- current company information;
- current market information;
- breaking developments;
- product specifications;
- official filings.

### Scholarly Lane

Appropriate for:

- causal claims;
- scientific mechanisms;
- health claims;
- psychology;
- social science;
- economics;
- educational outcomes;
- engineering performance;
- environmental claims;
- empirical behavioral claims.

These lanes MAY converge during synthesis.

They SHOULD NOT be treated as interchangeable.

---

# 6.2 Evidence Hierarchy

No universal source hierarchy works for every claim.

Evidence strength MUST be evaluated relative to claim type.

For empirical scientific claims, preferred evidence may include:

1. high-quality systematic reviews/meta-analyses;
2. relevant guidelines or consensus statements;
3. strong primary peer-reviewed studies;
4. authoritative datasets;
5. preprints where clearly labeled and justified;
6. expert synthesis for interpretation.

For current factual claims:

1. primary/official documentation;
2. direct filings/data;
3. authoritative reporting;
4. specialist secondary analysis.

For interpretive claims, multiple independent high-quality sources SHOULD be preferred.

---

# 6.3 Latest Does Not Mean Newest

Evidence SHALL be selected according to:

```text
RIGOR
×
RELEVANCE
×
DIRECTNESS
×
INDEPENDENCE
×
RECENCY
×
APPLICABILITY
```

A weak paper published yesterday does not automatically override a strong meta-analysis published last year.

The objective is the latest **reliable** evidence state.

---

# 6.4 Empirical Evidence Card

For important empirical claims, the evidence representation SHOULD preserve:

- research question;
- study design;
- population;
- sample size;
- setting;
- exposure/intervention;
- comparator;
- outcome;
- quantitative result;
- uncertainty;
- limitations;
- conflicts of interest where material;
- replication status;
- publication status;
- publication date;
- retraction/correction status;
- applicability to the article's claim.

The drafting process SHOULD consume this structured meaning rather than a free-floating paper summary.

---

# 6.5 Evidence Breadth

A single source SHOULD NOT establish a broad empirical proposition when meaningful independent evidence is available.

Source diversity SHOULD reflect evidence independence rather than domain count alone.

Ten articles repeating one press release equal approximately one underlying source, not ten independent confirmations.

---

# 6.6 Preprints

Preprints MAY be used when:

- the topic is genuinely current;
- the absence of peer review is explicit;
- the claim's rhetorical strength reflects that uncertainty;
- stronger peer-reviewed evidence is unavailable or incomplete.

Preprints MUST NOT silently masquerade as settled scholarship.

---

# 7. Information-Gain Metric

Originality SHALL mean **valuable new information or synthesis**, not unusual wording.

The unit of information-gain analysis SHALL be the **Atomic Information Unit (AIU).**

An AIU is one independently meaningful proposition, distinction, finding, framework element, or evidence-backed implication.

This concept is compatible with emerging document-novelty research such as NovAScore, which evaluates novelty using salient atomic information rather than surface-level textual difference.

---

# 7.1 AIU Gain Dimensions

Each eligible AIU receives:

**S — Salience**  
How important is this information to the reader or thesis?

**N — Novelty**  
How absent is this information from the Competitive Corpus?

**E — Evidence Advantage**  
How much better supported is our treatment than the strongest competitor treatment?

**F — Freshness Advantage**  
How materially more current is the information?

**V — Reader Value Delta**  
How much does this information improve understanding or decision quality?

All values are normalized 0–1.

---

# 7.2 Atomic Gain

```text
Gain_i =
0.40N_i +
0.25E_i +
0.10F_i +
0.25V_i
```

Only epistemically eligible AIUs count.

A novel unsupported claim earns zero Information Gain and may trigger an epistemic failure.

---

# 7.3 Competitive Information Gain

```text
CIG =
100 ×
Σ(S_i × Gain_i)
───────────────
Σ(S_i)
```

A redundancy penalty MAY be applied for large quantities of low-value repeated material.

Information Gain SHOULD reward:

- genuinely new evidence;
- newer evidence;
- superior source quality;
- previously unanswered important questions;
- useful synthesis;
- meaningful frameworks;
- explanatory distinctions;
- original analysis.

It SHALL NOT reward:

- synonyms;
- stylistic novelty;
- contrarianism for its own sake;
- unsupported speculation;
- unnecessary length.

---

# 7.4 Information Density Principle

The article SHOULD maximize:

> **valuable verified information per unit of reader attention.**

Research on long-form factuality indicates that increasing output length can reduce factual precision as reliable facts become exhausted.

Therefore:

> More words are not evidence of greater depth.

Research depth MAY greatly exceed publication length.

Only material that earns its place SHOULD survive into the final article.

---

# 8. Truth-Preserving Humanity Rules

The pipeline SHOULD write with human force when the topic benefits from it.

It MUST NOT manufacture humanity by manufacturing facts.

---

# 8.1 Emotional Register

The article specification SHOULD declare an appropriate emotional/editorial register, such as:

- forensic;
- authoritative;
- investigative;
- conversational;
- urgent;
- contemplative;
- empathetic;
- visceral;
- skeptical;
- technical;
- narrative.

The register MUST serve the article rather than being applied mechanically.

---

# 8.2 Factual Spine

The material factual structure of the article SHALL form a **factual spine**.

Humanity, voice, rhythm, analogy, scene, and narrative techniques MAY alter expression.

They MUST NOT silently change the factual meaning of that spine.

---

# 8.3 Humanity Pass Rule

A later prose/humanity pass MAY improve:

- rhythm;
- specificity;
- imagery;
- transitions;
- openings;
- pacing;
- sentence variation;
- tension;
- analogy;
- emotional weight;
- memorable framing.

After such a pass:

> Any newly introduced factual proposition MUST enter the claim-verification process.

If the humanity pass alters the semantic strength of a factual claim, that change MUST be detected and revalidated.

---

# 8.4 Earned Emotion

Emotional intensity MUST be proportional to documented stakes.

The system SHALL NOT:

- sensationalize weak evidence;
- exaggerate suffering;
- invent emotional reactions;
- use fear beyond the evidence;
- convert uncertainty into dramatic certainty.

Narrative techniques can increase engagement and persuasion, which makes epistemic safeguards more important rather than less important. Research on narrative transportation documents effects on engagement, empathy, and persuasion.

---

# 8.5 Truthful Specificity

Whenever possible, humanity SHOULD be created from real specificity:

- documented events;
- actual quotations;
- real case studies;
- real consequences;
- observed data;
- named systems;
- concrete examples;
- user-provided experience;
- published testimony.

Specificity is preferred over generic emotional language.

---

# 8.6 Analogy Integrity

Analogies MAY clarify difficult ideas.

An analogy MUST NOT imply a causal, quantitative, or structural equivalence that is false.

Where an analogy materially simplifies reality, the limitation SHOULD be clear.

---

# 8.7 No AI Self-Mythology

The article MUST NOT impersonate a human writer's lived history.

Statements such as:

```text
"When I tested..."
"In my years covering..."
"I remember when..."
"I spoke with..."
```

require authentic corresponding evidence.

---

# 9. Independent Greatness-Evaluation Protocol

The producer SHALL NOT be the sole judge of whether its own article is great.

Greatness evaluation MUST be operationally independent from production to the extent practical.

The candidate control plane MUST NOT control its evaluator.

---

# 9.1 Evaluation Layers

Greatness evaluation SHALL occur in the following order.

## Layer 1 — Deterministic Integrity

Check:

- required artifacts;
- schemas;
- stage legality;
- manifests;
- deterministic publication contract.

## Layer 2 — Independent Epistemic Audit

Independently verify:

- material claims;
- citation integrity;
- factual currency;
- contradictions;
- scope fidelity;
- causal fidelity.

The article's own fact-check report MUST NOT be trusted as evaluation evidence merely because it exists.

## Layer 3 — Question-Coverage Audit

Compare the finished article with the predeclared Question Graph.

Measure:

- core-question coverage;
- decision-question coverage;
- skeptical-question coverage;
- empirical-question coverage.

## Layer 4 — Excellence Checklist

Use decomposed, atomic questions for subjective quality wherever practical.

Examples:

```text
Does the opening establish real stakes?
Does the introduction state a defensible thesis?
Does each major section answer an important reader question?
Does the conclusion crystallize rather than merely summarize?
Is the strongest counterargument treated seriously?
Is any important paragraph generic enough to fit an unrelated article?
Does each major section contain a useful insight?
Are recommendations supported by the article's own evidence?
```

Checklist-style evaluation is preferred because recent CheckEval research found decomposed binary questions improved evaluator agreement and interpretability compared with broad subjective ratings.

## Layer 5 — Blind Editorial Evaluation

A senior-editor evaluator SHOULD judge only:

- brief;
- audience;
- final article.

It SHOULD NOT see:

- internal confidence labels;
- pipeline artifacts;
- control-plane identity;
- baseline/candidate identity.

## Layer 6 — Reader Transformation Evaluation

A blind target-reader simulation SHOULD determine whether the article actually enables the intended after-state.

## Layer 7 — Information-Gain Evaluation

Compare verified AIUs against the Competitive Corpus.

## Layer 8 — Competitive Pairwise Evaluation

Compare the finished article against strong competitor pieces.

Evaluation SHOULD occur across dimensions rather than only by asking:

> Which article do you prefer?

Pairwise order MUST be swapped or randomized.

Evaluator identity SHOULD be blinded when practical.

LLM-as-judge systems have documented position and other preference biases, so pairwise judgments SHALL NOT be trusted without anti-bias controls and human calibration.

---

# 9.2 Multiple Evaluators

Subjective Greatness dimensions SHOULD NOT rely permanently on one model family.

Where economically feasible:

- use multiple judge models;
- compare disagreement;
- periodically calibrate against humans;
- track evaluator drift across model upgrades.

An evaluator that materially changes behavior after a model update MUST be revalidated.

---

# 9.3 Human Calibration Corpus

The Greatness evaluator MUST eventually be calibrated against human-reviewed examples.

The corpus SHOULD include articles independently labeled:

```text
EXCEPTIONAL
GREAT
STRONG
COMPETENT
POOR
```

Annotations SHOULD identify why.

Source/publication identity SHOULD be blinded where practical to reduce authority bias.

The corpus SHOULD span article archetypes.

---

# 9.4 Greatness Qualification Rate

The control plane MAY maintain:

**GQR — Greatness Qualification Rate**

GQR SHALL mean:

```text
greatness-qualified articles
────────────────────────────
evaluable completed articles
```

GQR MUST be reported alongside its component metrics.

GQR MUST NOT replace QPR.

QPR asks:

> Can we reliably produce publishable work?

GQR asks:

> Can we reliably produce genuinely outstanding work?

---

# 10. Learning Signals Allowed to Change Future Behavior

The pipeline MAY learn from the following signals when provenance and sample size are retained.

## 10.1 Independent Evaluator Results

Allowed:

- recurring weak dimensions;
- coverage failures;
- information-gain failures;
- reader-transformation failures;
- factual failure classes;
- excessive verbosity;
- recurring structural failures.

---

# 10.2 Human Editorial Changes

Human edits are high-value learning data.

The learning system MAY record:

- what was changed;
- why;
- which class of issue it represented;
- whether similar corrections recur.

It SHOULD learn procedures rather than memorize transient facts.

---

# 10.3 Human Preference Judgments

Repeated blind human preferences MAY influence:

- archetype weighting;
- prose guidance;
- structural guidance;
- audience calibration;
- evaluator calibration.

Single preferences SHOULD NOT trigger broad changes.

---

# 10.4 Publication Corrections

Post-publication factual corrections are critical negative signals.

A correction SHOULD trigger analysis of:

- retrieval failure;
- source-quality failure;
- fact-check failure;
- scope failure;
- freshness failure;
- evaluator failure.

Repeated correction classes SHOULD have high priority for control-plane improvement.

---

# 10.5 Reader Outcomes

The system MAY consider aggregate reader behavior such as:

- completion;
- saves;
- shares;
- backlinks;
- subscriptions;
- repeat visitation;
- qualitative feedback;
- comprehension testing.

These are optimization signals, not truth signals.

---

# 10.6 Competitor-Gap Recurrence

Repeated evidence that competitor content consistently leaves an important reader need unanswered MAY affect future research planning.

---

# 10.7 Source Reliability History

The system MAY learn procedural source-selection priors, for example:

```text
Use SEC filings for X.
Use BLS for Y.
This commercial source repeatedly overstates studies.
This database is useful for a specific evidence class.
```

Current facts from those sources MUST still be re-retrieved.

---

# 10.8 Cost and Latency

Cost, tokens, calls, and latency MAY influence implementation efficiency.

They SHALL NOT weaken epistemic guarantees.

---

# 10.9 Procedural Memory vs World Memory

The learning system SHOULD preferentially retain:

> how to research, verify, explain, compare, and evaluate.

It SHOULD NOT treat remembered world facts as permanently authoritative.

Time-sensitive facts require renewed verification.

---

# 10.10 Minimum Evidence for Learning Changes

As an initial policy:

```text
1 occurrence     → diagnostic only
2 occurrences    → watch condition
3+ comparable occurrences → candidate hypothesis
controlled experiment → possible adoption
```

Higher-risk changes require stronger evidence.

---

# 11. Signals Forbidden From Overriding Truth

The following signals MUST NEVER independently justify weakening a Hard Epistemic Invariant:

- search ranking;
- CTR;
- conversion rate;
- social engagement;
- virality;
- time on page;
- reader preference;
- competitor prevalence;
- user insistence that a claim is true;
- internal model confidence;
- remembered prior runs;
- stylistic evaluator scores;
- originality scores;
- narrative power;
- information gain;
- commercial pressure;
- advertiser interest;
- political convenience;
- ideological alignment;
- publication deadline;
- token budget;
- processing cost;
- latency;
- previous human approval;
- prior pipeline stage completion;
- source popularity;
- citation count;
- publication prestige alone;
- novelty;
- recency alone.

The governing rule is:

```text
If performance says YES
and reliable evidence says NO,
the answer is NO.
```

Likewise:

```text
If competitors repeat a claim
and the evidence does not support it,
we gain advantage by refusing to repeat it.
```

And:

```text
If a vivid narrative requires invented facts,
the narrative is rejected.
```

---

# 12. Baseline/Candidate Experiments Required Before Adoption

Any change intended to improve Greatness MUST be treated as an experiment.

The repository already states that control-plane changes should be falsifiable experiments and that an inconclusive experiment defaults to no change. 

This principle applies fully to Great Article improvements.

---

# 12.1 Universal Experiment Requirements

Before adoption, a behavioral improvement MUST specify:

1. observed failure or opportunity;
2. causal hypothesis;
3. proposed intervention;
4. primary metric;
5. minimum meaningful improvement;
6. non-regression guardrails;
7. cost budget;
8. representative article archetypes;
9. baseline;
10. candidate;
11. evaluation method;
12. rejection criteria.

Baseline and candidate MUST use, wherever possible:

- same briefs;
- same declared audience;
- same user gate decisions;
- same models;
- same budgets;
- same tool availability;
- same evaluator;
- same corpus;
- same acceptance criteria.

Candidate and baseline ordering SHOULD be randomized.

---

# 12.2 New Competitive-Intelligence Agent

Before adoption:

MUST demonstrate:

- increased Competitive Information Gain;
- improved question coverage or reader value;
- higher blind competitive win rate.

MUST NOT regress:

- factual precision;
- citation integrity;
- article originality through imitation;
- QPR;
- cost beyond the declared acceptable range.

Testing MUST include niches with both strong and weak competitor content.

---

# 12.3 Scholarly-Evidence Retrieval Improvements

Before adoption:

MUST demonstrate improved:

- relevant-evidence recall;
- evidence quality;
- scope fidelity;
- current-state accuracy.

MUST be tested on tasks where known high-quality scholarly evidence exists.

MUST include adversarial cases containing:

- weak new studies;
- strong older reviews;
- preprints;
- contradictory studies;
- retractions where practical;
- secondary reporting that misstates primary research.

---

# 12.4 Information-Gain Metric

Before using the metric as a reward or adoption criterion:

MUST be calibrated against human novelty/value judgments.

MUST test whether it can be gamed using:

- obscure trivia;
- unsupported claims;
- needless contrarianism;
- excessive detail;
- superficial rewording.

A candidate metric MUST reward meaningful novelty rather than textual difference.

---

# 12.5 Reader Transformation Evaluation

Before becoming a Greatness gate:

MUST show meaningful agreement with human reader assessments.

MUST demonstrate that higher RTC scores correspond with improved:

- understanding;
- recall;
- decision quality;
- ability to explain key concepts.

---

# 12.6 Humanity / Prose Pass

Before adoption:

MUST demonstrate human preference improvement or calibrated HR improvement.

MUST have:

```text
zero tolerated regression
```

for:

- factual precision;
- claim semantics;
- citation integrity;
- uncertainty preservation.

Tests MUST specifically attempt to induce:

- invented scenes;
- stronger causal language;
- exaggerated certainty;
- fabricated first-person experience.

---

# 12.7 Archetype Routing

Before adoption or material threshold changes:

MUST compare automated archetype classifications with qualified human labels.

MUST demonstrate downstream article-quality improvement compared with generic treatment.

Routing errors MUST be analyzed by archetype pair.

---

# 12.8 New Greatness Evaluators

Evaluator changes are high-risk because changing the judge can create artificial improvement.

Before adoption:

MUST be compared against:

- the previous evaluator;
- human judgments;
- known good/bad examples;
- adversarial examples.

SHOULD use held-out evaluation.

The candidate pipeline MUST NOT be optimized against hidden evaluator answers.

If the evaluator itself changes, results under the old evaluator SHOULD be retained for comparison.

---

# 12.9 Learning-System Changes

Before allowing accumulated learning to modify production behavior:

MUST test:

- stale-memory behavior;
- false pattern learning;
- outlier robustness;
- conflicting feedback;
- feedback loops;
- whether engagement signals produce sensationalism;
- whether search signals produce keyword-driven quality regression.

Longitudinal evaluation SHOULD be used because learning-system harm may not appear in a single run.

---

# 12.10 Local Prompt or Skill Changes

Small behavioral changes MAY use focused experiments but still MUST show:

- target failure before;
- target improvement after;
- no relevant regression;
- repository verification.

---

# 12.11 Adoption Rule

An improvement SHALL be retained only when:

```text
primary improvement demonstrated
AND
hard epistemic guarantees preserved
AND
QPR non-inferior
AND
important Greatness dimensions non-inferior
AND
cost is justified
AND
no simpler mechanism achieves equivalent value
```

An inconclusive result means:

```text
DO NOT ADOPT
```

until stronger evidence exists.

---

# 13. Anti-Gaming Principle

The article pipeline MUST optimize for the underlying reader and epistemic outcomes, not artifacts of the evaluators.

Examples of prohibited optimization include:

- adding length because judges prefer longer answers;
- manufacturing novelty to raise IG;
- inserting emotional language solely to increase HR;
- repeating rubric terminology to manipulate evaluators;
- choosing evidence because the grader is likely to recognize it;
- suppressing uncertainty because certainty reads more confidently;
- adding low-value subquestions merely to increase coverage.

The system SHALL periodically test whether quality metrics can be improved without actually improving human-evaluated article quality.

If so, the metric is defective.

---

# 14. Greatness Is Relative but Truth Is Not

Competitive standards evolve.

Reader expectations evolve.

Available research evolves.

Language evolves.

The standard of what constitutes exceptional treatment of a topic SHOULD therefore become more demanding as the information environment improves.

However, the Hard Epistemic Invariants do not become weaker because competitors are worse.

The system MAY say:

> We are substantially better than every competing page.

It MUST NOT conclude:

> Therefore our remaining factual errors are acceptable.

---

# 15. The Final Greatness Test

Before an article qualifies as GREAT, the independent evaluation process should be able to answer **yes** to all of the following:

### Truth

Is every material factual proposition reasonably supportable?

### Evidence

Did the article use evidence appropriate to the strength and type of its claims?

### Scope

Did it preserve the actual boundaries of the research?

### Currency

Is current information genuinely current?

### Honesty

Did inconvenient evidence and uncertainty survive the writing process?

### Coverage

Did it answer the questions the intended reader most needs answered?

### Insight

Did it do meaningful intellectual work beyond summarizing sources?

### Originality

Does it add valuable information, analysis, synthesis, evidence, or utility beyond the strongest available alternatives?

### Transformation

Is the intended reader measurably better informed or better equipped after reading?

### Humanity

Does the article sound specific, alive, purposeful, and appropriate to its subject without fabricating human experience?

### Economy

Does each important section earn the reader's attention?

### Competitive Superiority

Would independent evaluators and qualified humans consistently choose this article over strong competing treatments for the declared reader and purpose?

Only after those questions are satisfied should the pipeline use the word:

> **great.**

---

# 16. Governing Maxim

The Great Article Standard is summarized by the following hierarchy:

> **Be true before being persuasive.**  
> **Be useful before being impressive.**  
> **Be original by discovering and synthesizing, not by rephrasing.**  
> **Be human by being specific and honest, not by pretending to have lived experience.**  
> **Beat competitors by serving the reader better, not by imitating them.**  
> **Use the newest reliable evidence without confusing recency for rigor.**  
> **Measure quality without allowing the measurement to become the objective.**  
> **Learn from every run without allowing yesterday's knowledge to masquerade as today's fact.**  
> **Add complexity only when experiments demonstrate that it creates better articles.**

The pipeline has succeeded when it no longer merely knows how to produce an article.

It has succeeded when it can explain, measure, test, and continuously improve **why that article deserves to exist instead of the thousands of competent alternatives already available.**