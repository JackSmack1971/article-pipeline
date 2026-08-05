# Reader Personas — Audience Calibration Guide

## How to Calibrate

The target audience is defined in `article_spec.md`. Match your simulation persona to one
of the archetypes below. If the spec describes a hybrid, blend the two closest archetypes.

---

## Archetype: Practitioner

**Who:** Mid-career professional in the article's domain. Works in the field daily. Reads
for actionable insight, not academic completeness.

**What they already know:** Domain vocabulary, standard workflows, major players/tools in
the space, recent news headlines about the field.

**What they don't know:** Deep academic theory, adjacent domain specifics, vendor-specific
implementations outside their stack, regulatory nuances outside their jurisdiction.

**Reading behavior:** Scans H2 headings first. If the intro doesn't promise a specific payoff
in the first 2 paragraphs, they leave. Will tolerate density if the payoff is clear.

**Drift signal:** If you catch yourself thinking "any reasonable person in this field knows
this" — stop. That IS the assumed knowledge to flag.

---

## Archetype: Informed Outsider

**Who:** Smart generalist adjacent to the field. Might be a senior manager, journalist, or
professional in a related domain. Reads to build a mental model, not to act.

**What they already know:** High-level field terminology, the major companies/names, why the
field matters. May have read one or two popular articles on the topic.

**What they don't know:** Acronyms, sub-domain distinctions, technical implementation, anything
requiring hands-on experience.

**Reading behavior:** Linear reader. Follows every argument. Loses trust quickly when jargon
appears without definition. Will reread a confusing paragraph once; if still unclear, abandons.

**Drift signal:** If you catch yourself thinking "this is clearly explained" — pause. Re-read
as someone who has never worked in this field.

---

## Archetype: Expert Critical Reader

**Who:** Domain expert reviewing the article for credibility. Reads to find errors, gaps, or
overreach. Will cite-check claims they know are contested.

**What they already know:** Everything the practitioner knows, plus academic literature,
contested claims in the field, historical context.

**What they don't know:** The author's specific dataset or primary source access.

**Reading behavior:** Jumps to the thesis, then to claims they know are contestable. Will not
forgive unattributed superlatives, scope overreach, or a missing citation on a contested fact.

**Drift signal:** This persona is most prone to expert drift. Force yourself to flag logical
leaps even when you personally can fill them in. The article must stand on its own.

---

## Pipeline Depth → Persona Mapping

| Pipeline Depth | Primary Persona | Rigor Level |
|----------------|----------------|-------------|
| SIMPLE | Informed Outsider | Low — surface major gaps only |
| STANDARD | Practitioner | Medium — flag domain jargon and logical leaps |
| COMPLEX | Expert Critical Reader | High — flag scope overreach, evidence opacity, unsupported causal claims |

For COMPLEX depth: use Expert Critical Reader AND Practitioner in sequence. Report which
persona flagged each gap.
