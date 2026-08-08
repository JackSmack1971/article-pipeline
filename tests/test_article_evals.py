import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.evals.claim_citation_grader import compute_claim_metrics, extract_markdown_citations
from scripts.evals.editorial_grader import DIMENSIONS, compute_editorial_metrics
from scripts.evals.greatness_evaluator import (
    ARCHETYPE_WEIGHTS,
    DIMENSION_CRITERIA,
    EXCELLENCE_DIMENSIONS,
    IG_ENTRY,
    STRONG_DIMENSION_FLOOR,
    WEIGHTED_DIMENSIONS,
    classify,
    compute_dimension_scores,
    compute_excellence_index,
    epistemic_eligibility_from_qpr_record,
    evaluate,
    renormalized_weights,
)
from scripts.evals.qpr_runner import (
    aggregate_arm,
    build_subject_prompt,
    dynamic_isolation_guardrails,
    extract_agent_calls,
    greatness_result_for_trial,
    load_corpus,
    match_scripted_decision,
    paired_bootstrap_ci,
    qualification,
    recommendation,
    should_run_greatness,
)

GREATNESS_CORPUS_PATH = Path(__file__).resolve().parent.parent / "evals" / "article_pipeline" / "greatness_corpus_v1.json"
REQUIRED_ARCHETYPES = {
    "Scientific / Scholarly Explainer",
    "Investigative / Current-Affairs Analysis",
    "Strategic / Executive Decision Guide",
    "Technical Tutorial / Technical Explainer",
    "Comparative / Commercial Decision Guide",
    "Argument / Thought Leadership",
    "Human-Centered Narrative / Feature",
    "Breaking-News Analysis",
}
REQUIRED_FAILURE_MODES = {
    "correlation_to_causation_drift",
    "study_scope_overgeneralization",
    "newest_vs_strongest_evidence",
    "contradictory_evidence",
    "uncertainty_inflation",
    "weak_but_popular_claims",
    "seductive_predetermined_thesis",
    "fabricated_first_person_experience_pressure",
    "verbosity_after_evidence_exhausted",
}
# Fields that exist only to inform evaluator-side analysis and must never shape what the
# subject session sees; build_subject_prompt() must be indifferent to their contents.
DIAGNOSTIC_ONLY_FIELDS = (
    "archetype",
    "benchmark_rationale",
    "stressed_dimensions",
    "primary_failure_modes",
    "freshness_matters",
    "scholarly_evidence_matters",
    "suite_tags",
)


def synthetic_grade(fail_map=None):
    """Build a synthetic Greatness grader payload from the real DIMENSION_CRITERIA rubric.

    fail_map maps dimension -> set of criterion ids that should be marked pass=False; every
    other criterion in every dimension passes. Building from DIMENSION_CRITERIA itself (rather
    than a hardcoded criteria list) means these fixtures track the live rubric, not a stale copy.
    """
    fail_map = fail_map or {}
    dimensions = {}
    for dim, criteria in DIMENSION_CRITERIA.items():
        failing = fail_map.get(dim, set())
        dimensions[dim] = {
            "criteria": {
                cid: {"pass": cid not in failing, "rationale": "synthetic fixture"} for cid in criteria
            },
            "confidence": "high",
        }
    return {"dimensions": dimensions, "archetype_fit_note": "synthetic", "overall_grader_confidence": "high"}


class ClaimCitationMetricsTests(unittest.TestCase):
    def test_hard_guardrail_fails_on_mismatched_attribution(self):
        grade = {
            "claims": [
                {
                    "claim": "A",
                    "material": True,
                    "presented_as_current_fact": True,
                    "citation_url": "https://example.com/a",
                    "support": "supports",
                    "factual_status": "current",
                    "citation_integrity": "mismatched_attribution",
                }
            ]
        }
        metrics = compute_claim_metrics(grade)
        self.assertEqual(metrics["integrity_violation_count"], 1)
        self.assertFalse(metrics["hard_guardrail_pass"])

    def test_precision_and_support_are_computed_from_claim_rows(self):
        grade = {
            "claims": [
                {
                    "claim": "A",
                    "material": True,
                    "presented_as_current_fact": True,
                    "citation_url": "https://example.com/a",
                    "support": "supports",
                    "factual_status": "current",
                    "citation_integrity": "valid",
                },
                {
                    "claim": "B",
                    "material": True,
                    "presented_as_current_fact": True,
                    "citation_url": "https://example.com/b",
                    "support": "partial",
                    "factual_status": "current",
                    "citation_integrity": "valid",
                },
            ]
        }
        grade["citations"] = [
            {"anchor": "A", "url": "https://example.com/a", "integrity": "valid", "nearby_claim_support": "supports"},
            {"anchor": "B", "url": "https://example.com/b", "integrity": "valid", "nearby_claim_support": "partial"},
        ]
        expected = extract_markdown_citations("[A](https://example.com/a) [B](https://example.com/b)")
        metrics = compute_claim_metrics(grade, expected)
        self.assertEqual(metrics["material_claim_precision"], 0.5)
        self.assertEqual(metrics["citation_support_rate"], 0.5)
        self.assertEqual(metrics["citation_audit_coverage_rate"], 1.0)


class EditorialMetricsTests(unittest.TestCase):
    def test_dimension_mean_and_fatal_issue(self):
        grade = {
            "dimensions": {name: {"score": 4, "rationale": "ok"} for name in DIMENSIONS},
            "fatal_editorial_issues": [{"category": "thesis_drift", "detail": "drift"}],
            "publication_recommendation": "substantive_revision",
        }
        metrics = compute_editorial_metrics(grade)
        self.assertEqual(metrics["mean_score"], 4.0)
        self.assertEqual(metrics["minimum_dimension_score"], 4)
        self.assertFalse(metrics["hard_guardrail_pass"])


class QprTests(unittest.TestCase):
    def good_claim_result(self):
        return {
            "metrics": {
                "material_claim_precision": 1.0,
                "citation_support_rate": 1.0,
                "hard_guardrail_pass": True,
            }
        }

    def good_editorial_result(self):
        return {
            "metrics": {
                "mean_score": 4.25,
                "minimum_dimension_score": 4,
                "hard_guardrail_pass": True,
            }
        }

    def brief(self):
        return {
            "id": "x",
            "topic_brief": "topic",
            "target_audience": "audience",
            "scripted_decisions": {"approval": "approved"},
            "allowed_depths": ["STANDARD"],
        }

    def test_qualification_requires_publishable_and_quality(self):
        result = qualification(
            validator={"status": "PUBLISHABLE"},
            claim_result=self.good_claim_result(),
            editorial_result=self.good_editorial_result(),
            subject={"human_rescue_required": False, "route_depth": "STANDARD"},
            brief=self.brief(),
            static_guardrails={"pass": True},
            dynamic_guardrails={"pass": True},
        )
        self.assertTrue(result["qualified"])

    def test_human_rescue_disqualifies(self):
        result = qualification(
            validator={"status": "PUBLISHABLE"},
            claim_result=self.good_claim_result(),
            editorial_result=self.good_editorial_result(),
            subject={"human_rescue_required": True, "route_depth": "STANDARD"},
            brief=self.brief(),
            static_guardrails={"pass": True},
            dynamic_guardrails={"pass": True},
        )
        self.assertFalse(result["qualified"])
        self.assertTrue(any("human rescue" in reason for reason in result["reasons"]))

    def test_extract_agent_calls_from_stream_events(self):
        payload = {
            "_events": [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "article-skeptic", "prompt": "URLs only"}}
                ]}}
            ]
        }
        calls = extract_agent_calls(payload)
        self.assertEqual(calls[0]["subagent_type"], "article-skeptic")

    def test_dynamic_isolation_detects_advocate_claim_leak_to_skeptic(self):
        root = Path(tempfile.mkdtemp())
        artifacts = root / ".agents" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "pipeline_config.json").write_text(json.dumps({"pipeline": {"adversarial_dialectic": True}}), encoding="utf-8")
        claim = "This distinctive advocate claim should never be copied into the skeptic delegation prompt verbatim."
        (artifacts / "advocate_context.md").write_text(f"- **Statement:** {claim}\n", encoding="utf-8")
        subject = {"turns": [{"agent_calls": [
            {"subagent_type": "article-advocate", "prompt": "support"},
            {"subagent_type": "article-skeptic", "prompt": f"challenge this: {claim}"},
        ]}]}
        result = dynamic_isolation_guardrails(root, subject)
        self.assertFalse(result["pass"])

    def test_dynamic_isolation_detects_full_body_leak_to_red_team(self):
        root = Path(tempfile.mkdtemp())
        artifacts = root / ".agents" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "pipeline_config.json").write_text(json.dumps({"pipeline": {"red_team": True}}), encoding="utf-8")
        body = "This is a deliberately long body paragraph containing sensitive supporting argument context that the red team must not receive. " * 2
        draft = f"# Title\n\n## Body\n\n{body}\n\n## Conclusion\n\nConclusion text."
        (artifacts / "article_draft.md").write_text(draft, encoding="utf-8")
        subject = {"turns": [{"agent_calls": [
            {"subagent_type": "article-red-team", "prompt": body[:150]},
        ]}]}
        result = dynamic_isolation_guardrails(root, subject)
        self.assertFalse(result["pass"])

    def test_match_scripted_approval(self):
        brief = self.brief()
        decision = match_scripted_decision("⛔ APPROVAL GATE — Pipeline Paused", brief, set(), "APPROVAL")
        self.assertEqual(decision, ("approval", "approved"))

    def test_corpus_validation_rejects_duplicate_ids(self):
        root = Path(tempfile.mkdtemp())
        payload = self.brief()
        (root / "a.json").write_text(json.dumps(payload), encoding="utf-8")
        (root / "b.json").write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(Exception):
            load_corpus(root)

    def test_aggregate_separates_infrastructure_errors(self):
        records = [
            {"qualification": {"qualified": True, "hard_guardrail_failures": []}, "subject": {"total_cost_usd": 2, "total_duration_ms": 3, "total_input_tokens": 4, "total_output_tokens": 5}},
            {"evaluator_error": "boom"},
        ]
        summary = aggregate_arm(records)
        self.assertEqual(summary["trials"], 2)
        self.assertEqual(summary["evaluable_trials"], 1)
        self.assertEqual(summary["qpr"], 1.0)
        self.assertEqual(summary["operational_qpr"], 0.5)

    def test_bootstrap_constant_difference(self):
        self.assertEqual(paired_bootstrap_ci([1.0, 1.0, 1.0], samples=100, seed=1), (1.0, 1.0))

    def test_recommendation_rejects_guardrail_regression(self):
        baseline = {"hard_guardrail_failure_count": 0}
        candidate = {"hard_guardrail_failure_count": 1}
        paired = {"paired_evaluable_trials": 10, "candidate_minus_baseline_qpr": 0.5, "paired_bootstrap_95_ci": [0.2, 0.8]}
        result = recommendation(baseline, candidate, paired, minimum_qpr_delta=0.05, noninferiority_margin=0.02, minimum_pairs=6)
        self.assertEqual(result["decision"], "reject")


class GreatnessCorpusTests(unittest.TestCase):
    """G-000: development corpus for Great Article Standard v1 calibration.

    See evals/article_pipeline/README.md#greatness-benchmark-corpus-g-000. This is
    development/calibration data, not held-out proof; these tests only enforce the
    corpus's own declared shape and the subject-prompt separation contract.
    """

    def setUp(self):
        self.briefs = load_corpus(GREATNESS_CORPUS_PATH)
        self.by_id = {brief["id"]: brief for brief in self.briefs}

    def test_corpus_size_in_range(self):
        self.assertGreaterEqual(len(self.briefs), 12)
        self.assertLessEqual(len(self.briefs), 20)

    def test_every_archetype_covered(self):
        seen = {brief.get("archetype") for brief in self.briefs}
        missing = REQUIRED_ARCHETYPES - seen
        self.assertFalse(missing, f"archetypes missing from corpus: {missing}")

    def test_every_adversarial_failure_mode_covered_at_least_twice(self):
        counts: dict[str, int] = {}
        for brief in self.briefs:
            for mode in brief.get("primary_failure_modes", []):
                counts[mode] = counts.get(mode, 0) + 1
        missing = REQUIRED_FAILURE_MODES - set(counts)
        self.assertFalse(missing, f"failure modes never exercised: {missing}")
        under_covered = {mode: n for mode, n in counts.items() if mode in REQUIRED_FAILURE_MODES and n < 2}
        self.assertFalse(under_covered, f"failure modes exercised fewer than twice: {under_covered}")

    def test_every_brief_declares_required_diagnostic_fields(self):
        required = {
            "archetype",
            "benchmark_rationale",
            "stressed_dimensions",
            "primary_failure_modes",
            "freshness_matters",
            "scholarly_evidence_matters",
        }
        for brief in self.briefs:
            missing = required - set(brief)
            self.assertFalse(missing, f"brief {brief['id']!r} missing diagnostic fields: {missing}")
            self.assertIsInstance(brief["stressed_dimensions"], list)
            self.assertTrue(brief["stressed_dimensions"])
            self.assertIsInstance(brief["primary_failure_modes"], list)
            self.assertTrue(brief["primary_failure_modes"])
            self.assertIsInstance(brief["freshness_matters"], bool)
            self.assertIsInstance(brief["scholarly_evidence_matters"], bool)

    def test_diagnostic_fields_never_change_the_subject_prompt(self):
        """Evaluator-only diagnostics must not leak into subject-visible prompts.

        build_subject_prompt() must be a pure function of the subject-visible fields
        (topic_brief, target_audience, intended_thesis, scripted_decisions). Stripping
        every diagnostic-only field must not change the generated prompt at all.
        """
        for brief in self.briefs:
            with self.subTest(brief_id=brief["id"]):
                stripped = {k: v for k, v in brief.items() if k not in DIAGNOSTIC_ONLY_FIELDS}
                self.assertEqual(build_subject_prompt(brief), build_subject_prompt(stripped))

    def test_seductive_thesis_briefs_are_tagged(self):
        # These briefs specifically test "seductive predetermined theses that should be
        # revised/rejected" (Great Article Standard E12 / §0 lexicographic ordering).
        for brief_id in ("gc-arg-01", "gc-arg-02", "gc-inv-02"):
            brief = self.by_id[brief_id]
            self.assertIn("seductive_predetermined_thesis", brief["primary_failure_modes"])


class GreatnessEvaluatorTests(unittest.TestCase):
    """G-001: Greatness Evaluator v0 core (scripts/evals/greatness_evaluator.py).

    Uses synthetic grader output for classify()/compute_dimension_scores() so these tests
    never shell out to `claude` -- evaluate()'s live-grader branch is exercised only through
    the eligible=False short-circuit, which never calls run_claude_grader.
    """

    def _grade(self, pass_map=None):
        """Build a synthetic grader payload; pass_map overrides specific dim->criterion->bool."""
        pass_map = pass_map or {}
        dimensions = {}
        for dim, criteria in {
            "RQ": ["evidence_authority", "methodological_transparency", "triangulation", "source_diversity_not_redundant"],
            "CQ": ["core_questions_answered", "no_glaring_omission", "background_sufficient", "decision_relevant_info_present"],
            "SI": ["goes_beyond_summary", "meaningful_framework_or_distinction", "conclusions_follow_from_evidence", "insight_per_section"],
            "IH": ["uncertainty_proportional", "counterevidence_treated_seriously", "limitations_disclosed", "fact_inference_separated"],
            "RT": ["explains_central_conclusion", "explains_supporting_evidence", "explains_limits", "actionable_or_evaluable"],
            "AF": ["vocabulary_matches_audience", "assumed_knowledge_appropriate", "examples_calibrated", "pacing_appropriate"],
            "HR": ["concrete_specificity", "voice_not_generic", "no_fabricated_experience", "register_fits_subject"],
            "SF": ["logical_progression", "transitions_earn_place", "no_filler_section", "conclusion_crystallizes"],
            "PU": ["usable_takeaway_present", "recommendations_supported", "practical_specificity", "appropriate_for_archetype"],
        }.items():
            overrides = pass_map.get(dim, {})
            dimensions[dim] = {
                "criteria": {cid: {"pass": overrides.get(cid, True), "rationale": "because"} for cid in criteria},
                "confidence": "high",
            }
        return {"dimensions": dimensions, "archetype_fit_note": "fits", "overall_grader_confidence": "high"}

    def test_archetype_weights_sum_to_100_including_ig(self):
        for archetype, weights in ARCHETYPE_WEIGHTS.items():
            with self.subTest(archetype=archetype):
                self.assertEqual(sum(weights.values()), 100)

    def test_renormalized_weights_exclude_ig_and_ih_and_sum_to_100(self):
        for archetype in ARCHETYPE_WEIGHTS:
            with self.subTest(archetype=archetype):
                weights = renormalized_weights(archetype)
                self.assertNotIn("IG", weights)
                self.assertNotIn("IH", weights)
                self.assertEqual(set(weights), set(WEIGHTED_DIMENSIONS))
                self.assertAlmostEqual(sum(weights.values()), 100.0, places=2)

    def test_renormalized_weights_unknown_archetype_raises(self):
        with self.assertRaises(Exception):
            renormalized_weights("Not A Real Archetype")

    def test_compute_dimension_scores_all_pass_is_100(self):
        scores = compute_dimension_scores(self._grade())
        for dim in EXCELLENCE_DIMENSIONS:
            self.assertEqual(scores[dim]["score"], 100.0)
            self.assertEqual(scores[dim]["passed_criteria"], scores[dim]["total_criteria"])

    def test_compute_dimension_scores_missing_dimension_scores_zero(self):
        scores = compute_dimension_scores({"dimensions": {}})
        for dim in EXCELLENCE_DIMENSIONS:
            self.assertEqual(scores[dim]["score"], 0.0)

    def test_compute_excellence_index_matches_weighted_mean(self):
        weights = {dim: 100.0 / len(WEIGHTED_DIMENSIONS) for dim in WEIGHTED_DIMENSIONS}
        scores = {dim: 80.0 for dim in EXCELLENCE_DIMENSIONS}
        self.assertAlmostEqual(compute_excellence_index(scores, weights), 80.0, places=1)

    def test_compute_excellence_index_ignores_ih(self):
        weights = {dim: 100.0 / len(WEIGHTED_DIMENSIONS) for dim in WEIGHTED_DIMENSIONS}
        scores = {dim: 80.0 for dim in EXCELLENCE_DIMENSIONS}
        baseline = compute_excellence_index(scores, weights)
        scores_low_ih = dict(scores, IH=0.0)
        self.assertAlmostEqual(compute_excellence_index(scores_low_ih, weights), baseline, places=1)

    def test_classify_epistemically_ineligible_blocks_regardless_of_scores(self):
        perfect_scores = {dim: 100.0 for dim in EXCELLENCE_DIMENSIONS}
        result = classify(epistemic_eligible=False, dimension_scores=perfect_scores, excellence_index=100.0)
        self.assertEqual(result["classification"], "EPISTEMICALLY_INELIGIBLE")
        self.assertNotIn(result["classification"], {"GREAT", "EXCEPTIONAL"})

    def test_classify_ih_below_floor_caps_at_publishable(self):
        scores = {dim: 100.0 for dim in EXCELLENCE_DIMENSIONS}
        scores["IH"] = STRONG_DIMENSION_FLOOR - 1
        result = classify(epistemic_eligible=True, dimension_scores=scores, excellence_index=95.0)
        self.assertEqual(result["classification"], "PUBLISHABLE")
        self.assertFalse(result["ih_floor_pass"])

    def test_classify_never_reaches_great_or_exceptional_because_ig_not_evaluated(self):
        # Every threshold for GREAT/EXCEPTIONAL is deliberately satisfied here; classify()
        # must still cap at STRONG and say why, per the module's IG=NOT_EVALUATED design.
        scores = {dim: 99.0 for dim in EXCELLENCE_DIMENSIONS}
        result = classify(epistemic_eligible=True, dimension_scores=scores, excellence_index=99.0)
        self.assertEqual(result["classification"], "STRONG")
        self.assertTrue(result["would_meet_great_excellence_thresholds_excluding_ig"])
        self.assertTrue(result["would_meet_exceptional_excellence_thresholds_excluding_ig"])
        self.assertTrue(any("IG is NOT_EVALUATED" in reason for reason in result["blocking_reasons"]))

    def test_classify_low_scores_stay_publishable(self):
        scores = {dim: 50.0 for dim in EXCELLENCE_DIMENSIONS}
        result = classify(epistemic_eligible=True, dimension_scores=scores, excellence_index=50.0)
        self.assertEqual(result["classification"], "PUBLISHABLE")

    def test_evaluate_ineligible_short_circuits_without_scoring_dimensions(self):
        brief = {"archetype": "Scientific / Scholarly Explainer", "topic_brief": "x", "target_audience": "y"}
        result = evaluate(
            "article text",
            brief,
            epistemic_eligible=False,
            epistemic_reasons=["material claim precision below threshold"],
            model="opus",
            effort="high",
            max_budget_usd=1.0,
            timeout_seconds=60,
        )
        self.assertEqual(result["classification"]["classification"], "EPISTEMICALLY_INELIGIBLE")
        self.assertIsNone(result["excellence_index"])
        self.assertIsNone(result["grader"])
        self.assertEqual(result["dimensions"]["IG"], IG_ENTRY)
        self.assertEqual(len(result["dimensions"]), 1)  # only IG; no Excellence Vector scored

    def test_evaluate_unknown_archetype_raises(self):
        brief = {"archetype": "Not A Real Archetype"}
        with self.assertRaises(Exception):
            evaluate(
                "article text",
                brief,
                epistemic_eligible=True,
                epistemic_reasons=[],
                model="opus",
                effort="high",
                max_budget_usd=1.0,
                timeout_seconds=60,
            )

    def test_epistemic_eligibility_from_qpr_record(self):
        qualified_record = {"qualification": {"qualified": True, "reasons": [], "hard_guardrail_failures": []}}
        eligible, reasons = epistemic_eligibility_from_qpr_record(qualified_record)
        self.assertTrue(eligible)
        self.assertEqual(reasons, [])

        unqualified_record = {
            "qualification": {
                "qualified": False,
                "reasons": ["editorial mean 3.500 < 4.000"],
                "hard_guardrail_failures": ["fatal editorial guardrail failed"],
            }
        }
        eligible, reasons = epistemic_eligibility_from_qpr_record(unqualified_record)
        self.assertFalse(eligible)
        self.assertIn("editorial mean 3.500 < 4.000", reasons)
        self.assertIn("fatal editorial guardrail failed", reasons)

    def test_dimension_criteria_ids_match_schema(self):
        # Every criterion id referenced in the grade payload must be one the schema/rubric
        # actually declares -- guards against rubric/schema drift.
        from scripts.evals.greatness_evaluator import DIMENSION_CRITERIA, GREATNESS_SCHEMA

        for dim in EXCELLENCE_DIMENSIONS:
            schema_ids = set(GREATNESS_SCHEMA["properties"]["dimensions"]["properties"][dim]["properties"]["criteria"]["required"])
            self.assertEqual(schema_ids, set(DIMENSION_CRITERIA[dim]))


class GreatnessAntiGamingTests(unittest.TestCase):
    """G-001 anti-gaming validation (Great Article Standard v1 §13).

    These tests do not, and cannot, validate the live semantic grader's real-world judgment --
    that requires human calibration against real articles, tracked as an open item in
    docs/GREATNESS-EVALUATOR-CALIBRATION.md. What they do prove: given the criteria a competent,
    rubric-following grader *should* mark pass/fail for a genuine-vs-gamed article pair (grounded
    directly in DIMENSION_CRITERIA's own rubric text, not invented), the deterministic
    aggregation/classification layer preserves that distinction instead of washing it out through
    averaging, an unenforced floor, or an aggregation bug that rewards the gamed variant anyway.
    Do not read a passing test here as "the evaluator resists gaming" -- read it as "the
    aggregation math does not itself defeat a grader that resists gaming."
    """

    def scores(self, fail_map):
        return compute_dimension_scores(synthetic_grade(fail_map))

    def test_concise_accurate_beats_verbose_padded(self):
        bad = self.scores({"SF": {"no_filler_section"}, "PU": {"practical_specificity"}})
        good = self.scores({})
        self.assertLess(bad["SF"]["score"], good["SF"]["score"])
        self.assertLess(bad["PU"]["score"], good["PU"]["score"])

    def test_calibrated_uncertainty_beats_unjustified_certainty(self):
        bad = self.scores({"IH": {"uncertainty_proportional", "fact_inference_separated"}})
        good = self.scores({})
        self.assertLess(bad["IH"]["score"], good["IH"]["score"])
        # Two of four IH criteria fail (50%) -- below both the universal IH floor and the STRONG
        # dimension floor (both 70.0); the deterministic guardrail must actually engage here.
        scores = {dim: 100.0 for dim in EXCELLENCE_DIMENSIONS}
        scores["IH"] = bad["IH"]["score"]
        result = classify(epistemic_eligible=True, dimension_scores=scores, excellence_index=95.0)
        self.assertEqual(result["classification"], "PUBLISHABLE")
        self.assertFalse(result["ih_floor_pass"])

    def test_strong_evidence_beats_citation_heavy_weak_evidence(self):
        # Many citations that are redundant/low-authority is not the same as strong evidence;
        # RQ separates authority and independence from raw citation count.
        bad = self.scores({"RQ": {"evidence_authority", "source_diversity_not_redundant"}})
        good = self.scores({})
        self.assertLess(bad["RQ"]["score"], good["RQ"]["score"])

    def test_specific_truthful_prose_beats_generic_filler(self):
        bad = self.scores({"HR": {"concrete_specificity", "voice_not_generic"}})
        good = self.scores({})
        self.assertLess(bad["HR"]["score"], good["HR"]["score"])

    def test_genuine_insight_beats_unsupported_contrarianism(self):
        bad = self.scores({"SI": {"conclusions_follow_from_evidence"}})
        good = self.scores({})
        self.assertLess(bad["SI"]["score"], good["SI"]["score"])

    def test_correct_scope_beats_overgeneralization(self):
        # Extending a narrow study population to a universal claim is the fact/inference
        # separation and proportional-uncertainty failure the IH rubric targets.
        bad = self.scores({"IH": {"fact_inference_separated", "uncertainty_proportional"}})
        good = self.scores({})
        self.assertLess(bad["IH"]["score"], good["IH"]["score"])

    def test_supported_recommendation_beats_persuasive_unsupported_recommendation(self):
        bad = self.scores({"PU": {"recommendations_supported"}})
        good = self.scores({})
        self.assertLess(bad["PU"]["score"], good["PU"]["score"])

    def test_authentic_tone_beats_forced_emotionality(self):
        bad = self.scores({"HR": {"register_fits_subject"}})
        good = self.scores({})
        self.assertLess(bad["HR"]["score"], good["HR"]["score"])

    def test_fabricated_first_person_experience_is_penalized(self):
        bad = self.scores({"HR": {"no_fabricated_experience"}})
        good = self.scores({})
        self.assertLess(bad["HR"]["score"], good["HR"]["score"])
        # KNOWN LIMITATION (documented in docs/GREATNESS-EVALUATOR-CALIBRATION.md): a single
        # failing criterion out of four is only a 25-point dimension penalty (75.0), which does
        # not itself cross the 70.0 floor. v0 has no per-criterion severity weighting, so an
        # isolated fabrication does not alone force PUBLISHABLE -- this test documents that gap
        # rather than hiding it.
        self.assertGreaterEqual(bad["HR"]["score"], STRONG_DIMENSION_FLOOR)

    def test_deterministic_layer_ignores_rationale_length_and_keyword_stuffing(self):
        # The aggregator only ever reads the boolean `pass` field -- a compromised or sycophantic
        # grader call cannot inflate a score by writing a longer or rubric-keyword-stuffed
        # rationale, because compute_dimension_scores() never looks at rationale content or
        # length. This is a structural (not merely observed) anti-gaming property.
        plain = synthetic_grade({})
        stuffed = synthetic_grade({})
        for entry in stuffed["dimensions"].values():
            for criterion in entry["criteria"].values():
                criterion["rationale"] = ("rigorous excellent insightful authoritative " * 500) + criterion["rationale"]
        plain_scores = compute_dimension_scores(plain)
        stuffed_scores = compute_dimension_scores(stuffed)
        for dim in EXCELLENCE_DIMENSIONS:
            self.assertEqual(plain_scores[dim]["score"], stuffed_scores[dim]["score"])
            self.assertEqual(plain_scores[dim]["passed_criteria"], stuffed_scores[dim]["passed_criteria"])

    def test_rubric_criteria_text_retains_anti_gaming_language(self):
        # Guards against silent rubric drift removing the exact language the cases above rely on.
        expectations = {
            ("SF", "no_filler_section"): "deleted without losing meaningful information",
            ("IH", "uncertainty_proportional"): "unsupported strengthening",
            ("RQ", "source_diversity_not_redundant"): "independent evidence",
            ("HR", "concrete_specificity"): "generic filler",
            ("SI", "conclusions_follow_from_evidence"): "overreaching",
            ("PU", "recommendations_supported"): "supported by the article's own evidence",
            ("HR", "register_fits_subject"): "exaggerated drama",
            ("HR", "no_fabricated_experience"): "fabricated first-person experience",
        }
        for (dim, cid), phrase in expectations.items():
            with self.subTest(dim=dim, cid=cid):
                self.assertIn(phrase, DIMENSION_CRITERIA[dim][cid])


class GreatnessQprIntegrationTests(unittest.TestCase):
    """G-001/QPR integration: Greatness attaches to a trial record without replacing QPR.

    should_run_greatness()/greatness_result_for_trial() are pure functions that qpr_runner.py's
    run_one() calls; testing them directly avoids shelling out to `claude` or standing up a git
    worktree, while still exercising the real gating and eligibility-derivation logic.
    """

    def qualified_result(self):
        return {"qualified": True, "reasons": [], "hard_guardrail_failures": []}

    def unqualified_result(self):
        return {
            "qualified": False,
            "reasons": ["editorial mean 3.500 < 4.000"],
            "hard_guardrail_failures": ["fatal editorial guardrail failed"],
        }

    def test_should_run_greatness_requires_enabled_and_known_archetype(self):
        archetype_brief = {"id": "x", "archetype": "Scientific / Scholarly Explainer"}
        no_archetype_brief = {"id": "y"}
        unknown_archetype_brief = {"id": "z", "archetype": "Not A Real Archetype"}
        self.assertTrue(should_run_greatness(archetype_brief, enabled=True))
        self.assertFalse(should_run_greatness(archetype_brief, enabled=False))
        self.assertFalse(should_run_greatness(no_archetype_brief, enabled=True))
        self.assertFalse(should_run_greatness(unknown_archetype_brief, enabled=True))

    def test_greatness_result_for_trial_ineligible_short_circuits_without_grader_call(self):
        # Uses the qualification=False path, which evaluate() short-circuits before ever calling
        # run_claude_grader -- so this proves real eligibility-derivation and schema/field
        # behavior deterministically, with no live model call and no CI nondeterminism.
        brief = {"id": "x", "archetype": "Scientific / Scholarly Explainer", "topic_brief": "t", "target_audience": "a"}
        result = greatness_result_for_trial(
            "article text",
            brief,
            self.unqualified_result(),
            model="opus",
            effort="high",
            max_budget_usd=1.0,
            timeout_seconds=60,
        )
        self.assertEqual(result["classification"]["classification"], "EPISTEMICALLY_INELIGIBLE")
        self.assertIsNone(result["excellence_index"])
        self.assertIsNone(result["grader"])
        self.assertEqual(result["archetype"], "Scientific / Scholarly Explainer")
        self.assertEqual(result["dimensions"]["IG"], IG_ENTRY)
        # Both the QPR-qualification reasons and hard-guardrail failures are preserved, not
        # collapsed -- greatness never re-derives or overrides the QPR eligibility decision.
        self.assertIn("editorial mean 3.500 < 4.000", result["epistemic_eligibility"]["reasons"])
        self.assertIn("fatal editorial guardrail failed", result["epistemic_eligibility"]["reasons"])

    def test_greatness_result_for_trial_passes_qualified_true_through_as_eligible(self):
        # Patch the imported evaluate() so no live grader/subprocess call happens; this proves
        # the wrapper derives eligible=True (not False) from a qualified QPR result and forwards
        # model/effort/budget/timeout unchanged, without re-deriving eligibility itself.
        brief = {"id": "x", "archetype": "Scientific / Scholarly Explainer", "topic_brief": "t", "target_audience": "a"}
        with patch("scripts.evals.qpr_runner.evaluate_greatness") as mock_evaluate:
            mock_evaluate.return_value = {"classification": {"classification": "STRONG"}}
            result = greatness_result_for_trial(
                "article text",
                brief,
                self.qualified_result(),
                model="opus",
                effort="high",
                max_budget_usd=1.0,
                timeout_seconds=60,
            )
        self.assertEqual(result, {"classification": {"classification": "STRONG"}})
        mock_evaluate.assert_called_once()
        _, kwargs = mock_evaluate.call_args
        self.assertTrue(kwargs["epistemic_eligible"])
        self.assertEqual(kwargs["epistemic_reasons"], [])
        self.assertEqual(kwargs["model"], "opus")
        self.assertEqual(kwargs["max_budget_usd"], 1.0)


if __name__ == "__main__":
    unittest.main()
