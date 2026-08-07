import json
import tempfile
import unittest
from pathlib import Path

from scripts.write_artifact_manifest import main as write_manifest
from scripts.validate_artifacts import validate


class ValidateArtifactsTests(unittest.TestCase):
    def refresh_manifest(self, root):
        import sys
        old_argv = sys.argv
        try:
            sys.argv = ["write_artifact_manifest.py", "--artifact-root", str(root)]
            write_manifest()
        finally:
            sys.argv = old_argv

    def make_run(self, state=None, metadata="Final word count: 2"):
        root = Path(tempfile.mkdtemp())
        for name in ("pipeline_config.json", "pipeline_state.json"):
            (root / name).write_text("{}", encoding="utf-8")
        (root / "pipeline_config.json").write_text(json.dumps({"pipeline": {}}), encoding="utf-8")
        current_state = state or {"stage": "COMPLETE", "draft": {"word_count": 2}}
        (root / "pipeline_state.json").write_text(json.dumps(current_state), encoding="utf-8")
        (root / "article_spec.md").write_text("spec", encoding="utf-8")
        (root / "article_draft.md").write_text("one two", encoding="utf-8")
        (root / "pipeline_metadata.md").write_text(metadata, encoding="utf-8")
        self.refresh_manifest(root)
        return root

    def test_complete_run_with_matching_contract_is_publishable(self):
        report, code = validate(self.make_run())
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PUBLISHABLE")

    def test_blockers_downgrade_complete_to_review_required(self):
        root = self.make_run()
        (root / "seo_package.md").write_text(
            "| 17 | E-E-A-T block present | **FAIL — see E-E-A-T Gaps below** |",
            encoding="utf-8")
        self.refresh_manifest(root)
        report, code = validate(root)
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")

    def test_word_count_drift_requires_review(self):
        report, code = validate(self.make_run(metadata="Final word count: 99"))
        self.assertEqual(code, 1)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertTrue(any("word-count mismatch" in item for item in report["errors"]))

    def test_expected_tool_degradation_is_review_only(self):
        root = self.make_run()
        (root / "pipeline_config.json").write_text(json.dumps({"pipeline": {
            "tool_availability": {"code_execution": False}
        }}), encoding="utf-8")
        (root / "article_spec.md").write_text("[PLACEHOLDER-ONLY] chart.webp", encoding="utf-8")
        self.refresh_manifest(root)
        report, code = validate(root)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PUBLISHABLE")
        self.assertEqual(report["conditions"][0]["code"], "TOOL_DEGRADED")

    def test_manifest_detects_post_manifest_edit(self):
        root = self.make_run()
        (root / "article_draft.md").write_text("one changed", encoding="utf-8")
        report, code = validate(root)
        self.assertEqual(code, 1)
        self.assertTrue(any("manifest hash mismatch: article_draft.md" in item for item in report["errors"]))

    def test_skip_manifest_hash_ignores_post_manifest_edit(self):
        root = self.make_run()
        (root / "article_draft.md").write_text("one changed", encoding="utf-8")
        report, code = validate(root, skip_manifest_hash=True)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PUBLISHABLE")
        self.assertFalse(any("manifest hash mismatch" in item for item in report["errors"]))

    def test_skip_manifest_hash_still_reports_missing_required_artifact(self):
        root = self.make_run()
        (root / "article_spec.md").unlink()
        self.refresh_manifest(root)
        report, code = validate(root, skip_manifest_hash=True)
        self.assertEqual(code, 1)
        self.assertTrue(any("missing required artifact: article_spec.md" in item for item in report["errors"]))

    def test_stale_seo_word_count_is_flagged_as_mismatch(self):
        root = self.make_run()
        (root / "seo_package.md").write_text(
            "| 9 | Word count ≥ 1,800 | PASS (999 words) |", encoding="utf-8")
        self.refresh_manifest(root)
        report, code = validate(root)
        self.assertEqual(code, 1)
        self.assertTrue(any("word-count mismatch" in item for item in report["errors"]))
        self.assertEqual(report["word_counts"]["seo"], 999)

    def test_eeat_fail_vocabulary_without_ed_suffix_is_still_caught(self):
        # Regression: validate_artifacts.py previously matched only the literal
        # string "FAILED" via regex, so a producer using "FAIL" (the vocabulary
        # seo-schema.md itself specifies) silently passed validation.
        root = self.make_run()
        (root / "seo_package.md").write_text(
            "| 17 | E-E-A-T block present | **FAIL — see E-E-A-T Gaps below** |",
            encoding="utf-8")
        self.refresh_manifest(root)
        report, code = validate(root)
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "REVIEW_REQUIRED")
        self.assertTrue(any("E-E-A-T" in b for b in report["blockers"]))

    def test_eeat_status_mismatch_between_state_and_seo_is_an_error(self):
        root = self.make_run(state={
            "stage": "COMPLETE", "draft": {"word_count": 2}, "eeat": {"status": "PASS", "reason": None},
        })
        (root / "seo_package.md").write_text(
            "| 17 | E-E-A-T block present | **FAIL — see E-E-A-T Gaps below** |",
            encoding="utf-8")
        self.refresh_manifest(root)
        report, code = validate(root)
        self.assertEqual(code, 1)
        self.assertTrue(any("eeat status mismatch" in item for item in report["errors"]))

    def test_eeat_pass_via_structured_state_does_not_block(self):
        root = self.make_run(state={
            "stage": "COMPLETE", "draft": {"word_count": 2}, "eeat": {"status": "PASS", "reason": None},
        })
        (root / "seo_package.md").write_text(
            "| 17 | E-E-A-T block present | PASS |", encoding="utf-8")
        self.refresh_manifest(root)
        report, code = validate(root)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PUBLISHABLE")


if __name__ == "__main__":
    unittest.main()
