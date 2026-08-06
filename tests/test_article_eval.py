import unittest

from scripts.article_eval import (
    citation_structure_report,
    editorial_metrics,
    qpr_trial,
)


GOOD_CLAIM_GRADE = {
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
    "dimensions": {
        "coherence": 4,
        "audience_fit": 4,
        "reasoning": 4,
        "nuance": 4,
        "readability": 4,
        "usefulness": 4,
    },
    "hard_failure": False,
}


class ArticleEvalTests(unittest.TestCase):
    def test_citation_structure_reports_invalid_and_generic_links(self):
        report = citation_structure_report(
            "Claim with [source](http://example.com) and [descriptive evidence](https://example.org/a)."
        )
        self.assertEqual(report["citation_count"], 2)
        self.assertEqual(report["invalid_absolute_urls"], ["http://example.com"])
        self.assertEqual(report["generic_anchors"], ["source"])

    def test_editorial_threshold_requires_mean_and_dimension_floor(self):
        grade = dict(GOOD_EDITORIAL_GRADE)
        grade["dimensions"] = dict(GOOD_EDITORIAL_GRADE["dimensions"], nuance=2)
        metrics = editorial_metrics(grade, threshold=3.5, minimum_dimension=3.0)
        self.assertFalse(metrics["pass"])

    def test_qualified_publish_requires_all_layers(self):
        result = qpr_trial(
            deterministic_publishable=True,
            claim_grade=GOOD_CLAIM_GRADE,
            editorial_grade=GOOD_EDITORIAL_GRADE,
            human_rescue=False,
        )
        self.assertTrue(result["qualified_publish"])

    def test_fabricated_citation_is_hard_qpr_failure(self):
        grade = {
            **GOOD_CLAIM_GRADE,
            "judgments": [{**GOOD_CLAIM_GRADE["judgments"][0], "fabricated_citation": True}],
        }
        result = qpr_trial(
            deterministic_publishable=True,
            claim_grade=grade,
            editorial_grade=GOOD_EDITORIAL_GRADE,
            human_rescue=False,
        )
        self.assertFalse(result["epistemic_pass"])
        self.assertFalse(result["qualified_publish"])

    def test_human_rescue_prevents_qualified_publish(self):
        result = qpr_trial(
            deterministic_publishable=True,
            claim_grade=GOOD_CLAIM_GRADE,
            editorial_grade=GOOD_EDITORIAL_GRADE,
            human_rescue=True,
        )
        self.assertFalse(result["qualified_publish"])

    def test_unsupported_material_claim_fails_by_default(self):
        grade = {
            **GOOD_CLAIM_GRADE,
            "judgments": [{**GOOD_CLAIM_GRADE["judgments"][0], "verdict": "UNSUPPORTED"}],
        }
        result = qpr_trial(
            deterministic_publishable=True,
            claim_grade=grade,
            editorial_grade=GOOD_EDITORIAL_GRADE,
            human_rescue=False,
        )
        self.assertFalse(result["qualified_publish"])


if __name__ == "__main__":
    unittest.main()
