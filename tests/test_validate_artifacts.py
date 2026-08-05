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
        root = self.make_run(metadata="Final word count: 2\nE-E-A-T: FAILED")
        (root / "seo_package.md").write_text("E-E-A-T: FAILED", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
