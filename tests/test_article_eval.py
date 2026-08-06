import unittest

from scripts.article_eval import (
    aggregate_variant,
    citation_structure_report,
    editorial_metrics,
    paired_comparison,
    qpr_trial,
)


INPUT_SHA = "a" * 64
CITATION_STRUCTURE = {
    "invalid_absolute_urls": [],
    "citations": [{"anchor": "descriptive evidence", "url": "https://example.com/source"}],
}

GOOD_CLAIM_GRADE = {
    "input_sha256": INPUT_SHA,
    "coverage_complete": True,
    "judgments": [
        {
            "claim": "A material factual claim",
            "materiality": "MATERIAL",
            "citation_url": "https://example.com/source",
            "verdict": "SUPPORTED",
            "fabricated_citation": False,
            "reason": "source supports proposition",
        }
    ],
    "disputed_or_outdated_as_settled": False,
    "silent_conflict_drift": False,
}

GOOD_EDITORIAL_GRADE = {
    "input_sha256": INPUT_SHA,
    "dimensions": {
        "coherence": 4,
        "audience_fit": 4,
        "reasoning": 4,
        "nuance": 4,
        "readability": 4,
        "usefulness": 4,
    },
    "hard_failure": False,
    "strengths": ["clear"],
    "weaknesses": [],
}


def qpr(**overrides):
    args = {
        "deterministic_publishable": True,
        "claim_grade": GOOD_CLAIM_GRADE,
        "editorial_grade": GOOD_EDITORIAL_GRADE,
        "human_rescue": False,
        "input_sha256": INPUT_SHA,
        "citation_structure": CITATION_STRUCTURE,
    }
    args.update(overrides)
    return qpr_trial(**args)


class ArticleEvalTests(unittest.TestCase):
    def test_citation_structure_reports_invalid_and_generic_links(self):
        report = citation_structure_report(
            "Claim with [source](http://example.com) and [descriptive evidence](https://example.org/a)."
        )
        self.assertEqual(report["citation_count"], 2)
        self.assertEqual(report["invalid_absolute_urls"], ["http://example.com"])
        self.assertEqual(report["generic_anchors"], ["source"])

    def test_editorial_threshold_requires_mean_and_dimension_floor(self):
        grade = {
            **GOOD_EDITORIAL_GRADE,
            "dimensions": dict(GOOD_EDITORIAL_GRADE["dimensions"], nuance=2),
        }
        metrics = editorial_metrics(
            grade,
            threshold=3.5,
            minimum_dimension=3.0,
            expected_input_sha256=INPUT_SHA,
        )
        self.assertFalse(metrics["pass"])

    def test_qualified_publish_requires_all_layers(self):
        self.assertTrue(qpr()["qualified_publish"])

    def test_zero_material_claims_cannot_pass_epistemic_layer(self):
        grade = {**GOOD_CLAIM_GRADE, "judgments": []}
        result = qpr(claim_grade=grade)
        self.assertEqual(result["claim_metrics"]["material_claims"], 0)
        self.assertFalse(result["epistemic_pass"])

    def test_uncited_material_claim_is_hard_qpr_failure(self):
        judgment = {
            **GOOD_CLAIM_GRADE["judgments"][0],
            "citation_url": None,
        }
        result = qpr(claim_grade={**GOOD_CLAIM_GRADE, "judgments": [judgment]})
        self.assertEqual(result["claim_metrics"]["material_uncited"], 1)
        self.assertFalse(result["qualified_publish"])

    def test_grade_citation_must_exist_in_article(self):
        judgment = {
            **GOOD_CLAIM_GRADE["judgments"][0],
            "citation_url": "https://example.com/not-in-article",
        }
        with self.assertRaisesRegex(ValueError, "does not appear"):
            qpr(claim_grade={**GOOD_CLAIM_GRADE, "judgments": [judgment]})

    def test_stale_grade_digest_is_rejected(self):
        grade = {**GOOD_CLAIM_GRADE, "input_sha256": "b" * 64}
        with self.assertRaisesRegex(ValueError, "does not match"):
            qpr(claim_grade=grade)

    def test_incomplete_claim_coverage_is_rejected(self):
        grade = {**GOOD_CLAIM_GRADE, "coverage_complete": False}
        with self.assertRaisesRegex(ValueError, "coverage_complete"):
            qpr(claim_grade=grade)

    def test_invalid_article_link_fails_qpr_even_if_semantics_grade_passes(self):
        structure = {
            "invalid_absolute_urls": ["http://example.com/source"],
            "citations": [{"anchor": "evidence", "url": "https://example.com/source"}],
        }
        result = qpr(citation_structure=structure)
        self.assertFalse(result["citation_structure_pass"])
        self.assertFalse(result["qualified_publish"])

    def test_fabricated_citation_is_hard_qpr_failure(self):
        grade = {
            **GOOD_CLAIM_GRADE,
            "judgments": [
                {**GOOD_CLAIM_GRADE["judgments"][0], "fabricated_citation": True}
            ],
        }
        result = qpr(claim_grade=grade)
        self.assertFalse(result["epistemic_pass"])
        self.assertFalse(result["qualified_publish"])

    def test_human_rescue_prevents_qualified_publish(self):
        self.assertFalse(qpr(human_rescue=True)["qualified_publish"])

    def test_unsupported_material_claim_fails_by_default(self):
        grade = {
            **GOOD_CLAIM_GRADE,
            "judgments": [
                {**GOOD_CLAIM_GRADE["judgments"][0], "verdict": "UNSUPPORTED"}
            ],
        }
        self.assertFalse(qpr(claim_grade=grade)["qualified_publish"])

    def test_paired_comparison_requires_exact_pairing(self):
        baseline = [
            {"brief_id": "a", "trial": 1, "qualified_publish": True},
            {"brief_id": "b", "trial": 1, "qualified_publish": False},
        ]
        candidate = [
            {"brief_id": "a", "trial": 1, "qualified_publish": True},
        ]
        with self.assertRaisesRegex(ValueError, "not matched"):
            paired_comparison(baseline, candidate)

    def test_paired_comparison_reports_discordant_pairs(self):
        baseline = [
            {"brief_id": "a", "trial": 1, "qualified_publish": True},
            {"brief_id": "b", "trial": 1, "qualified_publish": False},
        ]
        candidate = [
            {"brief_id": "a", "trial": 1, "qualified_publish": False},
            {"brief_id": "b", "trial": 1, "qualified_publish": True},
        ]
        result = paired_comparison(baseline, candidate)
        self.assertEqual(result["candidate_only_qualified"], 1)
        self.assertEqual(result["baseline_only_qualified"], 1)
        self.assertEqual(result["qpr_absolute_delta"], 0.0)

    def test_aggregate_reports_quality_adjusted_efficiency(self):
        trials = [
            {
                **qpr(),
                "run_metrics": {"cost_usd": 2.0, "wall_time_seconds": 100},
            },
            {
                **qpr(human_rescue=True),
                "run_metrics": {"cost_usd": 1.0, "wall_time_seconds": 50},
            },
        ]
        result = aggregate_variant(trials)
        self.assertEqual(result["efficiency"]["median_cost_usd"], 1.5)
        self.assertEqual(result["efficiency"]["median_cost_usd_qualified"], 2.0)


if __name__ == "__main__":
    unittest.main()
