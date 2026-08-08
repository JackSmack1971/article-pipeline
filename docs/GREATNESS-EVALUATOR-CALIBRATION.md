# Greatness Evaluator v0 — Calibration Readiness

**Scope:** `scripts/evals/greatness_evaluator.py` (G-001), scored against `evals/article_pipeline/greatness_corpus_v1.json`
(G-000), per `docs/Great Article Standard v1.md` and `docs/GREATNESS-GAP-ANALYSIS.md`. This document is itself an
evaluator-status artifact under `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` — it does not authorize production
adoption; it states what is built, what evidence supports it, and exactly what is still missing before human
calibration can begin.

## 1. What this evaluator is and is not

G-001 is **eval-only and operationally independent**. It never runs inside the production pipeline
(`CLAUDE.md`'s TRIAGE→...→COMPLETE), is never invoked by `pipeline_runner.py finalize`, and is not wired into any
production gate, archetype routing, or drafting instruction. It consumes a QPR/epistemic eligibility decision as an
input and sits strictly above `scripts/validate_artifacts.py` / `claim_citation_grader.py` / `editorial_grader.py` /
`qpr_runner.py` — see the module docstring in `greatness_evaluator.py` for the layering diagram.

**It does not replace QPR.** `scripts/evals/qpr_runner.py --evaluate-greatness` attaches a Greatness result to a
trial record (`record["greatness"]`) purely additively: `qualification()` and `aggregate_arm()` — the functions that
actually compute Qualified Publish Rate — are unmodified and never read the Greatness result. A Greatness failure is
captured in `record["greatness_error"]`, kept separate from `record["evaluator_error"]` (harness/subject
infrastructure failures) and from `record["qualification"]`/`record["subject"]` (article/subject failures), so a
Greatness scoring problem can never silently suppress or inflate a QPR outcome. `should_run_greatness()` gates
scoring on an explicit `--evaluate-greatness` flag plus the brief declaring a known Great Article Standard v1 §3
archetype — development-corpus briefs (no `archetype` field) are never scored, so adding this flag changes nothing
about existing QPR runs unless a caller opts in.

## 2. Deterministic vs. semantic ownership

| Layer | Owns | Mechanism |
|---|---|---|
| Semantic grader | Judging each of the 36 atomic criteria (4 per dimension × 9 dimensions) pass/fail with a rationale | One blind `claude --bare` call, no tools, no filesystem, no baseline/candidate identity, no access to internal QA/fact-check conclusions or production self-score (`common.run_claude_grader`) |
| Deterministic code | Schema validation, dimension-score aggregation, archetype-weight renormalization, the IH universal floor, STRONG/GREAT/EXCEPTIONAL thresholds, and final classification | Pure Python in `greatness_evaluator.py`: `compute_dimension_scores()`, `compute_excellence_index()`, `classify()`, `renormalized_weights()` |

This split matters for anti-gaming: the deterministic layer never reads raw article text, rationale length, or
keyword content — it only ever consumes the grader's boolean `pass` fields
(`tests/test_article_evals.py::GreatnessAntiGamingTests::test_deterministic_layer_ignores_rationale_length_and_keyword_stuffing`
proves this structurally, not just by observation). Whatever gaming resistance the system has, it lives entirely in
the semantic grader's judgment quality — which is exactly the part this v0 has **not yet** been calibrated against
human judgment (§5 below).

## 3. Anti-gaming strategy and what the test suite actually proves

Great Article Standard v1 §13 requires periodically testing whether a quality metric can be improved without
improving real quality. `tests/test_article_evals.py::GreatnessAntiGamingTests` covers nine gaming vectors named in
the evaluator-validation goal for this increment:

1. concise/accurate vs. verbose/padded (SF.no_filler_section, PU.practical_specificity)
2. calibrated uncertainty vs. unjustified certainty (IH.uncertainty_proportional)
3. strong evidence vs. citation-heavy weak evidence (RQ.evidence_authority, RQ.source_diversity_not_redundant)
4. specific truthful prose vs. generic filler (HR.concrete_specificity, HR.voice_not_generic)
5. genuine supported insight vs. unsupported contrarianism (SI.conclusions_follow_from_evidence)
6. correct empirical scope vs. overgeneralization (IH.fact_inference_separated, IH.uncertainty_proportional)
7. evidence-supported recommendation vs. persuasive unsupported recommendation (PU.recommendations_supported)
8. authentic neutral/technical tone vs. forced emotionality (HR.register_fits_subject)
9. fabricated first-person experience (HR.no_fabricated_experience)

Each test builds a synthetic grader payload directly from the live `DIMENSION_CRITERIA` rubric (not a hand-copied
duplicate), sets the specific criteria a competent grader should mark `pass=False` for the "gamed" variant, and
proves the deterministic aggregation/classification layer preserves the resulting score gap rather than erasing it.
A companion test (`test_rubric_criteria_text_retains_anti_gaming_language`) pins the exact rubric phrases these
cases depend on, so a future rubric edit that silently weakens anti-gaming language fails loudly instead of leaving
these tests passing against a rubric that no longer says what the test assumes.

**What this proves:** the arithmetic and thresholds cannot be gamed by writing a longer or more confident rationale,
and cannot average away a genuine dimension failure into an unrelated high score, given a grader that correctly
applies the rubric.

**What this does not prove:** that the live semantic grader (a Claude Code `--bare` call) actually resists these
nine gaming pressures in practice against real, adversarially-written articles. That is a human-calibration
question, not a unit-test question — see §5. Per the goal for this increment, no human-calibration result is
asserted, fabricated, or implied by these tests passing.

**Known limitation surfaced by the tests, not hidden by them:** a single failing criterion out of four is only a
25-point (75.0) dimension penalty, which does not itself cross either the 70.0 IH universal floor or the 70.0 STRONG
dimension floor (`test_fabricated_first_person_experience_is_penalized` documents this explicitly). v0 has no
per-criterion severity weighting — an isolated fabricated-experience criterion failure lowers the HR score but does
not alone force a `PUBLISHABLE` cap. In practice this specific gap is defended in depth: fabricated first-person
experience of the kind E9 targets is also the kind of claim `claim_citation_grader.py`'s independent grader and QPR
hard guardrails are positioned to catch upstream of Greatness scoring. It remains a real v0 limitation of the
Greatness rubric's own severity model and is not silently smoothed over here.

## 4. Provisional thresholds

All numeric thresholds in `greatness_evaluator.py` (`IH_UNIVERSAL_FLOOR=70`, `STRONG_DIMENSION_FLOOR=70`,
`GREAT_EXCELLENCE_INDEX_MIN=82`, `GREAT_IH_MIN=85`, `GREAT_CQ_MIN=85`, `EXCEPTIONAL_EXCELLENCE_INDEX_MIN=90`,
`EXCEPTIONAL_DIMENSION_FLOOR=80`, `EXCEPTIONAL_IH_MIN=90`, `EXCEPTIONAL_CQ_MIN=95`) are **calibration hypotheses
carried forward from Great Article Standard v1 §2.3/§2.4**, not empirically derived cut points. No human-rated
article corpus has been scored against them yet. `GREAT`/`EXCEPTIONAL` are additionally structurally capped at
`STRONG` in v0 regardless of these thresholds, because both require demonstrated Information Gain (§2.4) and IG is
`NOT_EVALUATED` (no competitor corpus exists in this repository; see `docs/GREATNESS-GAP-ANALYSIS.md` §5/§7/§9 Layer
7). Treat every classification label this evaluator emits as provisional until §5 below is complete.

## 5. What human calibration and held-out confirmation still require

None of the following exists yet. All are required before any Greatness output can inform a real decision (an
adoption gate, an editorial recommendation, a production signal):

1. **A human-rated reference set.** A sample of real (not synthetic) articles — spanning the eight archetypes and,
   ideally, spanning known-good, known-mediocre, and known-bad quality tiers — rated independently by human
   editors/subject-matter readers against the same nine Excellence Vector dimensions, with no exposure to this
   evaluator's own output.
2. **Grader-vs-human agreement measurement.** Run `greatness_evaluator.py`'s live semantic grader against that same
   set and measure agreement (e.g. per-dimension correlation, or per-criterion precision/recall against human
   pass/fail judgments) rather than assuming rubric text alone guarantees grader fidelity.
3. **Threshold recalibration from evidence.** Adjust `IH_UNIVERSAL_FLOOR`/`STRONG_DIMENSION_FLOOR`/`GREAT_*`/
   `EXCEPTIONAL_*` (or explicitly confirm the current provisional values) based on where human raters actually draw
   the PUBLISHABLE/STRONG/GREAT/EXCEPTIONAL lines, not before.
4. **A live adversarial-gaming pass against the real grader.** The unit tests in §3 test the deterministic layer
   only. A genuine anti-gaming pass requires generating real gamed articles (padded, citation-stuffed, confidently
   wrong, etc.) and running them through the actual `claude --bare` grader call to see whether the live grader is
   fooled — this is Great Article Standard v1 §13's "periodically test whether quality metrics can be improved
   without actually improving quality" requirement, and it cannot be satisfied by mocked fixtures.
5. **Held-out confirmation**, per `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` §4.5/§4.6: G-000
   (`greatness_corpus_v1.json`) is development/calibration data, visible in this repository. Any claim that the
   evaluator reliably scores article quality requires a separate held-out corpus outside this repository, frozen
   evaluator/grader versions, and the same isolation discipline `qpr_runner.py` already applies to subject worktrees.
6. **Grader-vs-grader stability measurement.** Because the semantic grader is itself a stochastic model call, run
   the same article through the grader multiple times and measure score variance before treating a single grader
   call's output as a stable signal (Control-Plane Improvement Protocol Phase 5, "Prefer grading outcomes over
   requiring one exact trajectory").
7. **QPR-integration field audit under a real run.** `--evaluate-greatness` has been exercised via `--dry-run` and
   via the unit tests in `GreatnessQprIntegrationTests`, but not yet against a real `qpr_runner.py` subject trial
   producing a real `article_draft.md`. Before relying on `record["greatness"]` in any analysis, confirm a live run
   populates it with the expected fields (eligibility, archetype, all nine raw dimension scores, diagnostics,
   weighted index, provisional classification, `IG=NOT_EVALUATED`, evaluator/rubric version) exactly as it does in
   the fixture shown in §6.

## 6. Sample Greatness result (fixture, not a live run)

Produced by monkeypatching `greatness_evaluator.run_claude_grader` with an all-pass synthetic grade (same shape as
`GreatnessEvaluatorTests._grade()`) and calling `evaluate()` directly, so no live model call or network access was
used to produce it. Shown to demonstrate every required field is present and correctly shaped — this is
illustrative, not a calibration result. Each dimension's `criteria` array normally contains one
`{"id", "pass", "rationale"}` object per atomic criterion (4 per dimension); abbreviated to `["... 4 atomic
criterion diagnostics ..."]` below purely for readability — the real per-criterion detail (e.g.
`{"id": "evidence_authority", "pass": true, "rationale": "..."}`) is always present in `dimensions.<DIM>.criteria`:

```json
{
  "evaluator_version": "greatness-evaluator-v0",
  "rubric_version": "great-article-standard-v1",
  "archetype": "Scientific / Scholarly Explainer",
  "archetype_weights_excluding_ig": {
    "RQ": 22.2222, "CQ": 16.6667, "SI": 16.6667, "RT": 11.1111,
    "AF": 11.1111, "HR": 5.5556, "SF": 5.5556, "PU": 11.1111
  },
  "epistemic_eligibility": {
    "eligible": true,
    "reasons": [],
    "source": "caller-supplied QPR/epistemic qualification; this evaluator does not re-derive eligibility"
  },
  "dimensions": {
    "IG": {
      "status": "NOT_EVALUATED",
      "reason": "Competitor-corpus ingestion and Atomic Information Unit machinery do not exist in this repository (Great Article Standard v1 SS5/SS7; docs/GREATNESS-GAP-ANALYSIS.md SS5/SS7/SS9 Layer 7). No proxy is substituted. Because the Standard requires demonstrated information gain for GREAT and EXCEPTIONAL (SS2.4), classify() caps classification at STRONG until IG is implemented and calibrated as its own experiment."
    },
    "RQ": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["... 4 atomic criterion diagnostics ..."]},
    "CQ": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."]},
    "SI": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."]},
    "IH": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."]},
    "RT": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."], "limitation": "No production Reader Transformation Contract ... this RT score is a blind post-hoc proxy ... Treat it as provisional until an RTC exists."},
    "AF": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."]},
    "HR": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."]},
    "SF": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."]},
    "PU": {"score": 100.0, "passed_criteria": 4, "total_criteria": 4, "confidence": "high", "criteria": ["..."]}
  },
  "excellence_index": 100.0,
  "classification": {
    "classification": "STRONG",
    "ih_floor_pass": true,
    "would_meet_great_excellence_thresholds_excluding_ig": true,
    "would_meet_exceptional_excellence_thresholds_excluding_ig": true,
    "blocking_reasons": [
      "excellence-index/IH/CQ thresholds for GREAT/EXCEPTIONAL were met, but classification is capped at STRONG because IG is NOT_EVALUATED -- the Standard requires demonstrated information gain for both (SS2.4)"
    ]
  },
  "grader": {
    "model": "opus", "effort": "high",
    "archetype_fit_note": "...", "overall_confidence": "high",
    "metrics": {"...": "..."}, "process_returncode": 0, "stderr": ""
  }
}
```

Every field the goal for this increment requires is present: eligibility (`epistemic_eligibility`), archetype
(`archetype`), all nine raw dimension scores plus diagnostics (`dimensions.RQ`...`dimensions.PU`, each with `score`,
`passed_criteria`/`total_criteria`, per-criterion `criteria` detail, and `confidence`), weighted index
(`excellence_index`), provisional classification (`classification`), `IG=NOT_EVALUATED` (`dimensions.IG.status`),
and evaluator/rubric version (`evaluator_version`, `rubric_version`). When attached to a `qpr_runner.py` trial record
via `--evaluate-greatness`, this exact structure lands unmodified at `record["greatness"]`; a Greatness-specific
failure lands separately at `record["greatness_error"]` and never touches `record["qualification"]`.

## 7. Status

**NOT_READY_FOR_HUMAN_CALIBRATION.**

Reasons:

- No human-rated reference corpus exists yet (§5.1); there is nothing to calibrate against.
- Grader-vs-human agreement has never been measured (§5.2); the semantic grader's real-world gaming resistance is
  unverified — the anti-gaming test suite (§3) validates only the deterministic aggregation layer, by design, not
  the live grader.
- All numeric thresholds are carried forward from the Standard's own provisional values (§4), not derived from any
  evidence produced in this repository.
- No live adversarial-gaming pass against the real `claude --bare` grader call has been run (§5.4).
- QPR integration (`--evaluate-greatness`) has unit and dry-run coverage but has not yet been exercised against a
  live subject trial producing a real article (§5.7).

This evaluator is **not production-authoritative** and must not be treated as one: it does not gate
`pipeline_runner.py finalize`, does not affect QPR qualification, and its classification labels
(PUBLISHABLE/STRONG/GREAT/EXCEPTIONAL) are hypotheses to be tested, not verdicts to be trusted. Moving to
`READY_FOR_HUMAN_CALIBRATION` requires completing §5 items 1–2 at minimum (a reference corpus and a first
grader-vs-human agreement measurement); moving beyond that to any production-facing use requires the full
Control-Plane Improvement Protocol Class D evidence bar (`docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md`), including
held-out validation.
