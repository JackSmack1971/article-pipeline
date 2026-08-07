import json
import tempfile
import unittest
from pathlib import Path

from scripts.pipeline_runner import (
    advance,
    finalize,
    increment_revision,
    load_state,
    migrate_state,
    record_audit_verdict,
    record_gate,
    record_kc_event,
    sync_eeat_status,
    sync_word_count,
)


class PipelineRunnerTests(unittest.TestCase):
    def make_run(self, stage="LEARNING"):
        root = Path(tempfile.mkdtemp())
        (root / "pipeline_config.json").write_text(json.dumps({"pipeline": {}}), encoding="utf-8")
        (root / "pipeline_state.json").write_text(json.dumps({
            "stage": stage,
            "draft": {"word_count": 2},
        }), encoding="utf-8")
        (root / "article_spec.md").write_text("spec", encoding="utf-8")
        (root / "article_draft.md").write_text("one two", encoding="utf-8")
        (root / "pipeline_metadata.md").write_text("Final word count: 2", encoding="utf-8")
        from scripts.write_artifact_manifest import write_manifest
        write_manifest(root)
        return root

    def test_invalid_transition_is_rejected(self):
        with self.assertRaises(ValueError):
            advance(self.make_run("DRAFT"), "COMPLETE")

    def test_finalize_is_the_only_completion_path(self):
        report, code = finalize(self.make_run())
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PUBLISHABLE")
        state = json.loads((Path(report["artifact_root"]) / "pipeline_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["stage"], "COMPLETE")

    def test_sync_word_count_reconciles_all_three(self):
        root = self.make_run("POSTDRAFT")
        (root / "article_draft.md").write_text("one two three four five", encoding="utf-8")
        (root / "pipeline_state.json").write_text(json.dumps({
            "stage": "POSTDRAFT",
            "draft": {"word_count": 2},
        }), encoding="utf-8")
        (root / "pipeline_metadata.md").write_text(
            "## Drafting Summary\n- Final word count: 999 (within range)\n", encoding="utf-8")

        result = sync_word_count(root)
        self.assertEqual(result["word_count"], 5)

        state = json.loads((root / "pipeline_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["draft"]["word_count"], 5)
        metadata = (root / "pipeline_metadata.md").read_text(encoding="utf-8")
        self.assertIn("Final word count: 5 (within range)", metadata)

    def test_increment_revision_refuses_the_fourth_call(self):
        root = self.make_run("APPROVAL")
        for _ in range(3):
            result = increment_revision(root, "APPROVAL")
            self.assertEqual(result["status"], "RECORDED")
        fourth = increment_revision(root, "APPROVAL")
        self.assertEqual(fourth["status"], "HALT_REQUIRED")
        state = json.loads((root / "pipeline_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["revision_cycles"]["APPROVAL"], 3)

    def test_record_gate_tracks_expedite_count_and_warns_at_two(self):
        root = self.make_run("APPROVAL")
        first = record_gate(root, "APPROVAL", "expedite")
        self.assertNotIn("warning", first)
        second = record_gate(root, "APPROVAL", "expedite")
        self.assertIn("warning", second)
        state = json.loads((root / "pipeline_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["gate_expedite_count"], 2)

    def test_record_gate_rejects_unknown_decision(self):
        with self.assertRaises(ValueError):
            record_gate(self.make_run("APPROVAL"), "APPROVAL", "maybe")

    def test_record_kc_event_flags_halt_action(self):
        root = self.make_run("RESEARCH")
        result = record_kc_event(root, "KC-3", "HALT", "single source > 40%")
        self.assertEqual(result["action"], "HALT_REQUIRED")
        state = json.loads((root / "pipeline_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["kc_events"][0]["code"], "KC-3")

    def test_record_audit_verdict_halts_on_third_consecutive_blocked(self):
        root = self.make_run("DRAFT")
        self.assertEqual(record_audit_verdict(root, "BLOCKED")["status"], "RECORDED")
        self.assertEqual(record_audit_verdict(root, "BLOCKED")["status"], "RECORDED")
        third = record_audit_verdict(root, "BLOCKED")
        self.assertEqual(third["status"], "HALT_REQUIRED")
        self.assertEqual(third["consecutive_blocked_audits"], 3)

    def test_record_audit_verdict_resets_on_pass(self):
        root = self.make_run("DRAFT")
        record_audit_verdict(root, "BLOCKED")
        record_audit_verdict(root, "BLOCKED")
        reset = record_audit_verdict(root, "PASS")
        self.assertEqual(reset["consecutive_blocked_audits"], 0)

    def test_save_state_stamps_current_schema_version(self):
        root = self.make_run("APPROVAL")
        record_gate(root, "APPROVAL", "approved")
        state = json.loads((root / "pipeline_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["schema_version"], 2)

    def test_load_state_refuses_legacy_shape(self):
        root = self.make_run("COMPLETE")
        (root / "pipeline_state.json").write_text(json.dumps({
            "stage": "COMPLETE",
            "gates": [{"gate": "APPROVAL", "result": "approved"}],
            "telemetry": {"kc_events": []},
        }), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_state(root)

    def test_migrate_state_unblocks_the_legacy_shape_guard(self):
        root = self.make_run("COMPLETE")
        (root / "pipeline_state.json").write_text(json.dumps({
            "stage": "COMPLETE",
            "gates": [{"gate": "APPROVAL", "result": "approved"}],
            "telemetry": {"kc_events": [], "gate_expedite_count": 0},
            "draft": {"word_count": 2},
        }), encoding="utf-8")

        result = migrate_state(root)
        self.assertEqual(result["status"], "MIGRATED")

        state = load_state(root)
        self.assertEqual(state["schema_version"], 2)
        self.assertEqual(state["gate_history"][0]["decision"], "approved")

    def make_seo_package(self, root, *, eeat_cell, word_count=2151):
        (root / "seo_package.md").write_text(
            "## On-Page Checklist\n\n"
            "| # | Check | Result |\n"
            "|---|-------|--------|\n"
            f"| 9 | Word count ≥ 1,800 | PASS ({word_count:,} words) |\n"
            f"| 17 | E-E-A-T block present | {eeat_cell} |\n\n"
            "## E-E-A-T Gaps\n\n"
            "Item 17 fails on one signal:\n\n"
            "- **Expertise (FAIL):** No author byline.\n",
            encoding="utf-8",
        )

    def test_finalize_reconciles_stale_seo_word_count_with_canonical_draft(self):
        root = self.make_run("SEO")
        self.make_seo_package(root, eeat_cell="PASS", word_count=999)
        finalize(root)
        seo_text = (root / "seo_package.md").read_text(encoding="utf-8")
        self.assertIn("(2 words)", seo_text)
        self.assertNotIn("(999 words)", seo_text)

    def test_sync_eeat_status_extracts_structured_fail_from_fail_vocabulary(self):
        root = self.make_run("SEO")
        self.make_seo_package(root, eeat_cell="**FAIL — see E-E-A-T Gaps below**")
        result = sync_eeat_status(root)
        self.assertEqual(result["eeat"]["status"], "FAIL")
        state = load_state(root)
        self.assertEqual(state["eeat"]["status"], "FAIL")
        self.assertIn("Expertise (FAIL)", state["eeat"]["reason"])

    def test_finalize_blocks_completion_on_structural_eeat_fail(self):
        root = self.make_run("SEO")
        self.make_seo_package(root, eeat_cell="**FAIL — see E-E-A-T Gaps below**")
        report, code = finalize(root)
        self.assertEqual(report["stage"], "REVIEW_REQUIRED")
        self.assertTrue(any("E-E-A-T" in b for b in report["blockers"]))
        state = load_state(root)
        self.assertEqual(state["eeat"], {"status": "FAIL", "reason": state["eeat"]["reason"]})

    def test_finalize_completes_when_eeat_passes(self):
        root = self.make_run("SEO")
        self.make_seo_package(root, eeat_cell="PASS")
        report, code = finalize(root)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PUBLISHABLE")
        state = load_state(root)
        self.assertEqual(state["eeat"], {"status": "PASS", "reason": None})

    def test_sync_eeat_status_is_not_applicable_without_seo_package(self):
        root = self.make_run("DRAFT")
        result = sync_eeat_status(root)
        self.assertEqual(result["status"], "NOT_APPLICABLE")
        state = load_state(root)
        self.assertNotIn("eeat", state)

    def test_finalize_run_twice_produces_the_same_manifest_tree(self):
        root = self.make_run("SEO")
        self.make_seo_package(root, eeat_cell="PASS")
        finalize(root)
        first_manifest = json.loads((root / "artifact_manifest.json").read_text(encoding="utf-8"))["artifacts"]
        report, code = finalize(root)
        second_manifest = json.loads((root / "artifact_manifest.json").read_text(encoding="utf-8"))["artifacts"]
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "PUBLISHABLE")
        self.assertEqual(first_manifest, second_manifest)


if __name__ == "__main__":
    unittest.main()
