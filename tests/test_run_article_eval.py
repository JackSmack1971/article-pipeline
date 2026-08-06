import tempfile
import unittest
from pathlib import Path

from scripts.run_article_eval import (
    blind_article,
    invalidate_stale_outputs,
    require_safe_id,
    trial_input_sha256,
    validate_matched_manifest,
)


class RunArticleEvalTests(unittest.TestCase):
    def test_blind_article_removes_indented_eval_identity_comments(self):
        article = "# Title\n  <!-- EVAL-VARIANT: candidate -->\nBody\n"
        self.assertNotIn("EVAL-VARIANT", blind_article(article))
        self.assertIn("Body", blind_article(article))

    def test_unsafe_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            require_safe_id("../escape", "variant")

    def test_duplicate_trial_key_is_rejected(self):
        trials = [
            {"variant": "baseline", "brief_id": "x", "trial": 1},
            {"variant": "baseline", "brief_id": "x", "trial": 1},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate trial key"):
            validate_matched_manifest(trials)

    def test_unmatched_variant_coverage_is_rejected(self):
        trials = [
            {"variant": "baseline", "brief_id": "x", "trial": 1},
            {"variant": "baseline", "brief_id": "y", "trial": 1},
            {"variant": "candidate", "brief_id": "x", "trial": 1},
        ]
        with self.assertRaisesRegex(ValueError, "not matched"):
            validate_matched_manifest(trials)

    def test_decision_context_must_match_across_variants(self):
        trials = [
            {"variant": "baseline", "brief_id": "x", "trial": 1, "decision_context": {"policy": "neutral"}},
            {"variant": "candidate", "brief_id": "x", "trial": 1, "decision_context": {"policy": "take-side"}},
        ]
        with self.assertRaisesRegex(ValueError, "decision_context differs"):
            validate_matched_manifest(trials)

    def test_input_digest_changes_when_article_changes(self):
        brief = {"id": "x"}
        structure = {"citations": []}
        first = trial_input_sha256(
            brief=brief,
            article="one",
            citation_structure=structure,
            decision_context=None,
        )
        second = trial_input_sha256(
            brief=brief,
            article="two",
            citation_structure=structure,
            decision_context=None,
        )
        self.assertNotEqual(first, second)

    def test_prepare_invalidation_removes_old_semantic_evidence(self):
        root = Path(tempfile.mkdtemp())
        for name in ("claim_grade.json", "editorial_grade.json", "score.json"):
            (root / name).write_text("stale", encoding="utf-8")
        (root / "article.blind.md").write_text("keep", encoding="utf-8")
        invalidate_stale_outputs(root)
        self.assertTrue((root / "article.blind.md").exists())
        self.assertFalse((root / "claim_grade.json").exists())
        self.assertFalse((root / "editorial_grade.json").exists())
        self.assertFalse((root / "score.json").exists())


if __name__ == "__main__":
    unittest.main()
