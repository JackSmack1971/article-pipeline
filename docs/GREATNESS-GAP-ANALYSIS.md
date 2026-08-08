# Greatness Gap Analysis

**Maps:** `docs/Great Article Standard v1.md` (v1.0, proposed) against the current state of this repository.
**Status:** Analysis artifact, not a normative document. Produced by inspection of `.claude/skills/`, `.claude/agents/`, `scripts/`, `docs/`, and a completed run's `.agents/artifacts/` (trace `CCUK5X`).
**Method:** Every clause group below gets: what exists, what partially exists, what's missing, a mechanism recommendation (agent / deterministic code / evaluator), and — where relevant — what should explicitly not be added. Per `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md`, nothing here authorizes implementation; any adopted gap-closer is itself a Class B/C/D experiment.

---

## 0. Governing Principle (lexicographic ordering, §0)

**Exists.** The repo's own `CLAUDE.md` pipeline is sequential (TRIAGE→RESEARCH→FACTCHECK→APPROVAL→DRAFT→POSTDRAFT→SEO→LEARNING) and `pipeline_runner.py` treats SEO/E-E-A-T failure as a hard `REVIEW_REQUIRED` blocker rather than something a downstream stage can silently override — this is the lexicographic ordering in practice (the live run is stuck exactly here: a clean factual/editorial PASS blocked by one E-E-A-T signal, and the system is *not* auto-resolving it by fabricating a byline). **Gap:** the ordering is implicit in stage sequencing and one hardcoded blocker type (`UNRESOLVED_EDITORIAL_RISK`), not a general "higher layer wins" rule. If a future SEO-stage change ever tried to soften a factual caveat for readability, nothing currently detects that as a layer violation. **Mechanism:** deterministic — a general rule belongs in `validate_artifacts.py`/`article_eval.py`, not in agent prompts. **Don't add:** a numeric "lexicographic score" — the standard explicitly rejects compensatory scoring (§0); keep it pass/fail-then-gate, matching current design.

## 1. Hard Epistemic Invariants (E1–E12)

| Invariant | Exists | Partial | Missing | Mechanism |
|---|---|---|---|---|
| **E1** Material Claim Accountability | `claims_for_drafting.md` (flat claim index + PosteriorConfidence), `fact_check_report.md` | Coverage is asserted by the fact-checker/auditor's judgment, not proven | No deterministic check that *every* material claim in `article_draft.md` traces to a `CF` entry | **Evaluator** (script diffing draft claims against `CF` index) — currently agent-only via `article-qa-auditor` |
| **E2** Source Existence/Attribution | `article-fact-checker` verifies via WebSearch, source-tier weighting (T1–T4) | Verification is per-claim during FACTCHECK stage only | No re-check that a citation still resolves/matches at SEO or delivery time; no automated URL-liveness or author/institution cross-check | **Deterministic** spot-check (URL fetch + string match) as a supplement, not a replacement, to agent verification |
| **E3** Claim-Support Fidelity | `article-fact-checker` verdicts (`[VERIFIED]/[DISPUTED]/[OUTDATED]` etc.) explicitly judge support, not just existence | — | — | **Agent** — this is inherently a judgment call; keep it there |
| **E4** Scientific Scope Fidelity | Source-tier weighting exists | No explicit population/sample/jurisdiction/CI preservation checklist anywhere in `article-fact-checker` or `article-qa-auditor` | An E4-specific checklist item | **Evaluator/checklist** addition to `references/audit-checklist.md` — cheap, high-value, matches existing severity-tag pattern |
| **E5** Causal Fidelity | Implicit in fact-checker verdicts | — | No explicit check for correlation→causation language drift | **Checklist item**, same file as E4 |
| **E6** Freshness/Supersession | Breaking-News Freshness Protocol (72-hour claims vs. primary sources: fec.gov, justice.gov, congress.gov) in `article-fact-checker` | Covers breaking-news currency only, not general "has this figure/policy since changed" | Broader freshness sweep for non-breaking claims | **Agent**, extend existing fact-checker phase rather than new skill |
| **E7** Uncertainty Preservation | `[DISPUTED]` tagging, `conflict_register.md`, KC-6 | The exact transition list in the Standard (`possible→probable`, `one study→research shows`, etc.) has no explicit textual check | A grep-able list of banned unsupported strengthenings | **Evaluator** — deterministic string/pattern scan is cheap and precise for this specific list; pair with agent judgment for paraphrased cases |
| **E8** Conflict Integrity | `conflict_register.md`, `dispute_register.md`, KC-6 (0/7 vectors INSUFFICIENT in sampled run) | Strong existing match | — | Already deterministic (KC-6 vector check) + agent synthesis — keep as-is |
| **E9** No Fabricated Human Experience | No explicit rule found in any skill | — | Nothing currently scans for `"When I tested…"` / `"I spoke with…"` style fabricated first-person claims | **Evaluator** — deterministic pattern scan (first-person experiential phrases) as a cheap tripwire, backstopped by holistic audit |
| **E10** Provenance Integrity | Source-tier weighting (T1–T4) partially encodes "prefer primary" | Not an explicit primary-over-secondary substitution rule | — | **Checklist item**, low cost |
| **E11** No False Authority | E-E-A-T audit checks Expertise/Experience/Authoritativeness/Trustworthiness | E-E-A-T is SEO/presentation-framed, not phrased as "does the article's *text* imply expertise it lacks" | Distinct from E11's target (in-text false-authority claims vs. byline metadata) | **Agent**, fold into holistic audit as a distinct checklist item — don't conflate with SEO E-E-A-T |
| **E12** Epistemic Revision Supremacy | KC-events + revision-cycle cap + HALT/escalate exist for gates *within* a stage | No rule forces re-opening RESEARCH/DRAFT if a defect is found at SEO or LEARNING stage — the current live blocker is process (missing byline), not factual, so it hasn't tested this path | A late-discovery-reopens-upstream-stage rule | **Deterministic** stage-graph amendment in `pipeline_runner.py` (an allowed backward transition triggered by a specific blocker class) — this is the one E-invariant gap with real teeth missing |

**Overall E-vector verdict:** 5 of 12 invariants (E3, E8, and the judgment-based portions of E1/E2/E7) are well covered by existing agent skills. E4/E5/E9/E10/E11 are cheap checklist additions. **E12 is the one structural gap** — worth a real experiment, not a checklist line, because it changes the state machine.

## 2. Greatness Vector — G = (E, X)

**Exists (E half):** covered above.
**Exists (X half — partial mapping only):**

| Dimension | Closest existing analog | Gap |
|---|---|---|
| RQ (Research Quality) | Source-tier weighting, KC-3 diversity check | No explicit 0–100 score, no methodological-quality rubric |
| CQ (Coverage Quality) | `reader_questions.md` gap analysis (reader-simulation) | Measures comprehension gaps in the *finished* draft, not pre-declared core-question coverage (see §4 gap below) |
| IG (Information Gain) | **Missing entirely** — no competitor corpus exists (see §5, §7) | — |
| SI (Synthesis/Insight) | `article-qa-auditor` holistic audit qualitatively checks this | Not scored separately |
| IH (Intellectual Honesty) | Closest existing coverage: conflict register + fact-check disputes | Not scored/floored; the Standard requires a hard universal minimum floor regardless of archetype — nothing enforces that today |
| RT (Reader Transformation) | `article-reader-simulation` (comprehension gaps, accessibility rating) | Different construct: measures friction, not before/after state achievement (see §4) |
| AF (Audience Fit) | `reader-personas.md` (Practitioner/Informed Outsider/Expert Critical Reader) | Reasonably well covered |
| HR (Human Resonance) | Prose/style checks in holistic audit | Not scored separately |
| SF (Structure/Flow) | Inline section-by-section audit | Not scored separately |
| PU (Practical Utility) | Implicit in QA checklist | Not scored separately |

**Verdict:** No dimension in X is currently scored 0–100 or aggregated into an Excellence Index; the pipeline currently produces pass/fail/PASS_WITH_NOTES verdicts, which is consistent with the Standard's Layer 1–3 (deterministic/audit/coverage) but stops short of Layer 4+ (Excellence Checklist, blind editorial, pairwise). **Mechanism:** this is squarely an **evaluator** concern (Layer 4-8, §9 below) — do not try to make drafting agents self-score on 10 axes; that invites the anti-gaming failure mode explicitly warned against in §13.

## 3. Article Archetypes and Weighting (§3)

**Missing entirely.** `pipeline_config.json` has depth (SIMPLE/STANDARD/COMPLEX) and flags, not an article-type archetype (Scientific Explainer, Investigative Analysis, etc.) with per-archetype RQ/CQ/IG/SI/RT/AF/HR/SF/PU weights. The only "archetype"-flavored artifact found is *reader* archetypes (personas), a different axis than *article* archetypes.
**Mechanism if adopted:** archetype selection is a **deterministic classification step** (add a field to `pipeline_config.json`, populated by `article-complexity-triage` from the brief) feeding a **deterministic weighting table** (a data file, not agent-computed math) consumed only by the evaluator, never by drafting. **Don't add:** archetype-conditional drafting instructions that change factual rigor — the Standard is explicit that weights must not affect hard epistemic requirements (§3, last line).

## 4. Reader Transformation Contract (§4)

**Partial.** `article-reader-simulation` produces an accessibility rating and comprehension gaps — post-hoc, on the finished draft. The Standard wants an RTC **declared before drafting** (before-state, after-state, core/background/decision/skeptical/empirical/freshness/counterfactual/follow-up question classification) and then a blind transformation test against it.
**Missing:** the pre-declaration step. `article-complexity-triage` or `article-research-dialectic` would be the natural owner (it already declares thesis + audience).
**Mechanism:** the *contract itself* (before/after state, question list) is **agent-authored** (requires judgment about the reader); *coverage measurement* against it (did the draft answer the CORE questions) is a good candidate for a **deterministic** cross-reference (checklist-of-questions vs. section-headers/claims), same pattern as the existing inline audit.
**Don't add:** treating RT as satisfied by the existing reader-simulation output — that measures a different thing (friction, not achievement of a pre-declared after-state) and conflating them would be measurement-gaming exactly like §13 warns against.

## 5. Competitor Opportunity Model (§5)

**Missing entirely.** No competitor-corpus skill, no MUST MATCH/BEAT/ADD/AVOID classification, no `CO_j` scoring anywhere in the repo. This is the largest structural gap in the whole Standard relative to current capability.
**Mechanism:** this is a genuinely new capability, not a checklist add. If pursued: a competitor-research **agent** stream (parallel to advocate/skeptic, same isolation pattern already used) to gather and *abstract* competitor pages (§5.1 explicitly wants structural abstraction, not raw text piped into drafting context — that's a direct anti-gaming/anti-imitation safeguard already baked into the Standard, and matches this repo's existing "advocate can't see skeptic's raw context" isolation philosophy). The `CO_j` weighted score is **deterministic** arithmetic over agent-produced 0–1 ratings — same pattern as KC-3's numeric threshold.
**Don't add without an experiment:** per §12.2, this MUST demonstrate CIG improvement, coverage/reader-value improvement, and higher blind win rate, and MUST NOT regress factual precision, citation integrity, originality, or QPR before adoption. This is a Class C (cross-cutting orchestration) experiment at minimum under the improvement protocol — new agent stream, new artifact, new gate.

## 6. Scholarly Evidence Standard (§6)

**Partial.** `article-fact-checker` has source-tier weighting (T1–T4) and a Breaking-News Freshness Protocol — this maps to the Standard's "Current-State Lane." **Missing:** an explicit "Scholarly Lane" distinction (systematic reviews > guidelines > primary studies > datasets > preprints > expert synthesis) for causal/scientific/health/psych/econ claims, and the structured "Empirical Evidence Card" fields (population, sample size, design, comparator, uncertainty, replication/publication/retraction status) — `claims_for_drafting.md` currently carries a flatter claim/evidence/PosteriorConfidence shape.
**Mechanism:** lane distinction is an **agent** decision (which lane a claim belongs to); the Evidence Card is a **schema** addition to `CF`'s structure (deterministic template, agent-filled) — same shape as the existing PosteriorConfidence field, just richer.

## 7. Information-Gain Metric (§7)

**Missing entirely**, and structurally depends on §5 (competitor corpus) existing first — there is nothing to compute Novelty (N) or Evidence Advantage (E) against. `pipeline_config.json`'s `novelty_score` is a different, pre-existing concept (topic novelty for *triage depth routing*, not AIU-level information gain against competitors) and should not be repurposed to mean this.
**Mechanism if pursued:** downstream of §5's agent-abstracted competitor corpus; the AIU decomposition is **agent** work, the `Gain_i`/`CIG` arithmetic is **deterministic**.
**Don't add:** per §12.4, before using this as a reward/adoption criterion it MUST be calibrated against human novelty judgments and tested for gameability (obscure trivia, unsupported claims, contrarianism, padding). Do not wire CIG into any automated gate until that calibration exists — it would be a Class D (evaluator) change under the improvement protocol, the highest-evidence-bar category.

## 8. Truth-Preserving Humanity Rules (§8)

**Partial.** The pipeline has a POSTDRAFT reader-simulation "polish" step that revises flagged sections with inline re-audit (matches §8.3's rule that a humanity pass's new factual propositions must re-enter verification — this already happens structurally, since polish triggers re-audit of changed sections). **Missing:** no declared "emotional/editorial register" field (§8.1) in `article_spec.md`/`pipeline_config.json`, and no explicit E9-style scan for fabricated first-person experience (already noted in §1 above) or analogy-integrity check (§8.6).
**Mechanism:** register declaration is **agent**-authored at spec time (cheap addition to `AS`); the re-verification-on-polish behavior is **already deterministic** in effect (re-audit is a required step, not optional) — good existing match, no new machinery needed there.

## 9. Independent Greatness-Evaluation Protocol (§9, Layers 1–8)

| Layer | Exists | Gap |
|---|---|---|
| L1 Deterministic Integrity | **Yes** — `validate_artifacts.py`, manifest hashing, schema/stage legality | — |
| L2 Independent Epistemic Audit | **Partial** — `article-fact-checker` exists, but it's not operationally independent from the producer (same pipeline run, same session); the Standard explicitly says "MUST NOT be trusted merely because it exists" | Independence would require a separate evaluation pass with no shared context/state with drafting — currently the same pipeline's own fact-check report *is* treated as sufficient |
| L3 Question-Coverage Audit | **Missing** — depends on §4's pre-declared Question Graph existing | — |
| L4 Excellence Checklist | **Partial** — `article-qa-auditor`'s severity-tagged checklist is close in *style* (decomposed, atomic-ish) but scores accuracy/style, not the 10 Excellence dimensions | — |
| L5 Blind Editorial Evaluation | **Missing** — no blind-evaluator concept (evaluator seeing only brief+audience+final article, no pipeline artifacts) | — |
| L6 Reader Transformation Evaluation | **Missing**, depends on §4 | — |
| L7 Information-Gain Evaluation | **Missing**, depends on §5/§7 | — |
| L8 Competitive Pairwise Evaluation | **Missing**, depends on §5; also needs anti-position-bias controls (order randomization) not present anywhere in the repo | — |

**Verdict:** Layers 1 and (loosely) 4 exist. Layers 2, 3, 5, 6, 7, 8 are all missing or structurally dependent on gaps already identified above (§4, §5, §7). This is the clearest evidence that adopting the full Standard is a multi-experiment program, not a single change — L5/L8 in particular ("independent," "blind," position-debiased) are explicitly the kind of evaluator change that `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` classifies as Class D and requires the highest evidence bar (E4, held-out validation) for.

## 10. Learning Signals (§10)

**Strong existing match.** `pipeline_learnings.md` + `article-complexity-triage`'s Pre-Triage Learning Ingestion already implement most of this: tagged entries (`[CALIBRATION]`, `[THRESHOLD_ADJUST]`, `[GATE_HYGIENE]`), a minimum-evidence-for-change policy that's a near-exact match for §10.10's escalation ladder (the repo's THRESHOLD_ADJUST already requires ≥3 matching entries — this *is* §10.10's "3+ comparable occurrences → candidate hypothesis," already implemented). **Gap:** §10.4 (Publication Corrections as critical negative signal) and §10.5 (Reader Outcomes) have no artifact or hook — there's no post-publication feedback channel into the pipeline at all currently, which is expected since the pipeline doesn't currently track anything past delivery.
**Mechanism:** this is **procedural memory**, already correctly agent-mediated per §10.9 — no change needed to the existing mechanism, only to what feeds it (a post-publication corrections artifact, which is a delivery-side/out-of-repo concern more than a pipeline one).

## 11. Signals Forbidden From Overriding Truth (§11)

**Consistent by omission** — the repo currently has no CTR/engagement/virality/ranking signals wired into any gate at all, so there's nothing to demonstrate violates §11. This is a "don't add" section as much as a "build" section: the correct posture is to *not* introduce any of the listed signals into `pipeline_runner.py`'s validate/finalize logic, ever, even for efficiency reasons. Worth stating explicitly rather than leaving implicit, since §5/§7 additions (competitor ranking data, engagement-flavored signals) are exactly the kind of thing that could accidentally smuggle a forbidden signal into a gate if implemented carelessly.

## 12. Baseline/Candidate Experiments (§12)

**Fully covered by an existing mechanism.** `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` already implements everything §12.1 asks for (hypothesis, intervention, primary metric, baseline/candidate, evaluation method, rejection criteria, matched conditions, randomized ordering) and more (Class A–D taxonomy, E0–E5 evidence levels, 26-item acceptance checklist). §12.2–§12.10 map cleanly onto specific experiment classes under that protocol (competitive-intelligence agent → Class C; evidence-retrieval → Class B/C; IG metric/RT evaluation/new evaluators → Class D; local skill tweaks → Class B). **No new experiment framework should be built** — §12 is satisfied by pointing every Greatness-related change through the existing protocol, which the Standard itself anticipates (§12, opening line: "the repository already states that control-plane changes should be falsifiable experiments... this principle applies fully to Great Article improvements").

## 13. Anti-Gaming Principle (§13)

**No explicit periodic gaming-test mechanism exists**, but the repo's existing design choices already embody the spirit in several places: capability-isolated subagents (advocate/skeptic/red-team can't read what they shouldn't, preventing anchoring-as-a-gaming-vector), and the improvement protocol's explicit prohibition on optimizing against hidden evaluator answers. **Gap:** nothing currently *tests* whether a metric can be improved without improving real quality — this only matters once §2/§7/§9's scored dimensions exist, so it's not an independent gap today, just a required companion to any future evaluator work (already covered by the improvement protocol's Class D requirements).

## 14–16. Philosophy (relative greatness, final test, governing maxim)

Not independently actionable — these are framing sections. §15's Final Greatness Test is effectively a compressed restatement of §9's Layer 4/5 checklist and requires the same missing infrastructure. §16's governing maxim is already consistent with this repo's `CLAUDE.md` ("Research integrity outranks pipeline completion," "Never... convert disputed claims into settled facts") — no gap, no action.

---

## Summary Table

| Standard Section | Coverage | Primary Missing Piece | Next Step Classification |
|---|---|---|---|
| §0 Governing Principle | Implicit | General layer-violation detection | Deterministic (small) |
| §1 E1–E12 | ~50% | E12 reopen-on-late-defect; E4/E5/E9/E10/E11 checklist items | Mixed — E12 is Class B experiment, rest are checklist edits |
| §2 Greatness Vector | E-half only | Scored X dimensions | Evaluator, Class D |
| §3 Archetypes | Missing | Archetype field + weighting table | Deterministic + Class B |
| §4 Reader Transformation | Partial | Pre-declared RTC before drafting | Agent, Class B |
| §5 Competitor Model | Missing | Entire capability | Agent stream, Class C |
| §6 Scholarly Evidence | Partial | Lane distinction + Evidence Card schema | Schema + agent, Class B |
| §7 Information Gain | Missing | Depends on §5 | Deterministic math + Class D calibration |
| §8 Humanity Rules | Partial | Register declaration, E9/analogy checks | Cheap additions, Class A/B |
| §9 Evaluation Layers | 1.5/8 | L2 independence, L3/L5/L6/L7/L8 | Evaluator program, Class D |
| §10 Learning Signals | Strong | Post-publication feedback channel | Out of current scope |
| §11 Forbidden Signals | N/A (no violations) | Explicit negative-space documentation | None — vigilance only |
| §12 Experiments | Fully covered | Nothing | Use existing protocol as-is |
| §13 Anti-Gaming | Implicit | Periodic gaming test (once scoring exists) | Bundled into Class D work |
| §14–16 | Consistent | None | None |

**Bottom line:** the repository's existing machinery (deterministic gates, fact-checking, conflict/dispute tracking, red-team, reader-simulation, learning ingestion, and — critically — the Control-Plane Improvement Protocol itself) already satisfies the Standard's *process* requirements (§10, §12) and roughly half its *epistemic invariants* (§1). What's structurally absent is everything downstream of competitor awareness (§5, §7) and independent scored evaluation (§2 X-vector, §9 L2/L3/L5–L8) — these are the two real capability gaps, not the many small checklist items, and both require new agent capabilities plus Class C/D experiments before any part of them touches a production gate.
