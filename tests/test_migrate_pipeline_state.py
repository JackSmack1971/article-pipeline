import json
import tempfile
import unittest
from pathlib import Path

from scripts.migrate_pipeline_state import migrate, migrate_file
from scripts.pipeline_runner import load_state


LEGACY_STATE = {
    "stage": "COMPLETE",
    "gates": [
        {"gate": "TRIAGE_THESIS_CONFIRM", "result": "confirmed", "thesis_confidence": "MEDIUM"},
        {"gate": "APPROVAL", "result": "approved", "revision_cycles": 0},
    ],
    "telemetry": {
        "revision_cycles": {},
        "kc_events": [{"check": "KC-3", "result": "PASS", "detail": "max single-source share 10%"}],
        "gate_expedite_count": 0,
        "consecutive_blocked_audits": 0,
        "tool_degradation": ["code_execution: false"],
    },
    "draft": {"word_count": 5},
}


class MigratePipelineStateTests(unittest.TestCase):
    def test_migrate_flattens_legacy_telemetry_and_gates(self):
        migrated, changed = migrate(LEGACY_STATE)
        self.assertTrue(changed)
        self.assertEqual(migrated["schema_version"], 2)
        self.assertNotIn("telemetry", migrated)
        self.assertNotIn("gates", migrated)
        self.assertEqual(migrated["gate_history"][0]["gate"], "TRIAGE_THESIS_CONFIRM")
        self.assertEqual(migrated["gate_history"][0]["decision"], "confirmed")
        self.assertEqual(migrated["kc_events"][0]["code"], "KC-3")
        self.assertEqual(migrated["kc_events"][0]["status"], "PASS")
        self.assertEqual(migrated["gate_expedite_count"], 0)
        self.assertEqual(migrated["tool_degradation"], ["code_execution: false"])

    def test_migrate_is_idempotent(self):
        migrated_once, _ = migrate(LEGACY_STATE)
        migrated_twice, changed = migrate(migrated_once)
        self.assertFalse(changed)
        self.assertEqual(migrated_once, migrated_twice)

    def test_migrate_rejects_unknown_schema_version(self):
        with self.assertRaises(ValueError):
            migrate({"stage": "COMPLETE", "schema_version": 99})

    def test_migrate_file_updates_state_on_disk_and_is_readable_by_load_state(self):
        root = Path(tempfile.mkdtemp())
        (root / "pipeline_state.json").write_text(json.dumps(LEGACY_STATE), encoding="utf-8")

        result = migrate_file(root)
        self.assertEqual(result["status"], "MIGRATED")

        state = load_state(root)
        self.assertEqual(state["schema_version"], 2)

        second = migrate_file(root)
        self.assertEqual(second["status"], "ALREADY_CURRENT")


if __name__ == "__main__":
    unittest.main()
