"""Smoke tests for scripts/state_enforcer.sh, the PreToolUse/PostToolUse/
SessionStart hook script that enforces the pipeline_state.json write shield
and the artifact backup/rollback contract described in
diagnostics/002-state-verification-layer.md.

The diagnostics doc says these hooks were "tested with synthesized hook
payloads" but the repository discovery report found no committed test that
actually exercises the script end-to-end -- scripts/verify.sh only checks
`bash -n` syntax. These tests replace that manual/undocumented verification
with an automated one, run against a throwaway copy of the script tree so
state_enforcer.sh's own root-resolution (BASH_SOURCE-relative) gives full
isolation from this repository's real .agents/artifacts/.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# On Windows, plain "bash" can resolve to WSL's System32\bash.exe (which needs
# /mnt/c/... paths) instead of Git Bash/MSYS (which accepts C:/... paths, and
# is what scripts/verify.sh and the real hooks run under). Prefer the
# well-known Git-for-Windows location when present so Windows-style temp
# paths resolve; fall back to whatever "bash" the PATH provides elsewhere.
_GIT_BASH = Path(r"C:\Program Files\Git\usr\bin\bash.exe")
BASH = str(_GIT_BASH) if _GIT_BASH.is_file() else "bash"


def run_hook(root: Path, mode: str, payload: dict) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["STATE_ENFORCER_PYTHON"] = sys.executable
    return subprocess.run(
        [BASH, (root / "scripts" / "state_enforcer.sh").as_posix(), mode],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


class HookEnforcerSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        (self.tmp / "scripts").mkdir()
        for name in (
            "state_enforcer.sh",
            "validate_artifacts.py",
            "artifact_contract.py",
            "pipeline_runner.py",
            "migrate_pipeline_state.py",
            "write_artifact_manifest.py",
        ):
            shutil.copy2(SCRIPTS_DIR / name, self.tmp / "scripts" / name)

        artifacts = self.tmp / ".agents" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "pipeline_config.json").write_text(json.dumps({"pipeline": {}}), encoding="utf-8")
        (artifacts / "pipeline_state.json").write_text(
            json.dumps({"stage": "COMPLETE", "draft": {"word_count": 2}}), encoding="utf-8"
        )
        (artifacts / "article_spec.md").write_text("spec", encoding="utf-8")
        (artifacts / "article_draft.md").write_text("one two", encoding="utf-8")
        (artifacts / "pipeline_metadata.md").write_text("Final word count: 2", encoding="utf-8")

        from scripts.write_artifact_manifest import write_manifest

        write_manifest(artifacts)  # pure function of --artifact-root; no BASH_SOURCE isolation needed

        self.artifacts = artifacts

    def test_session_start_reports_ok_for_a_publishable_run(self):
        result = run_hook(self.tmp, "session-start", {})
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output.get("suppressOutput"))
        self.assertIn("artifact contract OK", output["hookSpecificOutput"]["additionalContext"])

    def test_pre_bash_allows_sanctioned_unchained_runner_command(self):
        payload = {"tool_input": {"command": "python scripts/pipeline_runner.py advance"}}
        result = run_hook(self.tmp, "pre-bash", payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_pre_bash_denies_chained_command_mentioning_state_file(self):
        payload = {"tool_input": {"command": "python scripts/pipeline_runner.py advance; cat .agents/artifacts/pipeline_state.json"}}
        result = run_hook(self.tmp, "pre-bash", payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_pre_write_denies_direct_write_to_state_file(self):
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(self.artifacts / "pipeline_state.json")},
        }
        result = run_hook(self.tmp, "pre-write", payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("pipeline_runner.py", output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_post_write_accepts_a_well_formed_markdown_write(self):
        draft = self.artifacts / "article_draft.md"
        payload = {
            "tool_input": {"file_path": str(draft)},
            "tool_response": {"success": True},
        }
        run_hook(self.tmp, "pre-write", payload)  # seed a backup
        result = run_hook(self.tmp, "post-write", payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output.get("suppressOutput"))

    def test_post_write_rolls_back_a_truncated_write(self):
        draft = self.artifacts / "article_draft.md"
        payload = {
            "tool_input": {"file_path": str(draft)},
            "tool_response": {"success": True},
        }
        run_hook(self.tmp, "pre-write", payload)  # seed a backup with the original content
        draft.write_text("", encoding="utf-8")  # simulate a truncated/corrupt write
        result = run_hook(self.tmp, "post-write", payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output.get("decision"), "block")
        self.assertIn("empty", output["reason"])
        self.assertEqual(draft.read_text(encoding="utf-8"), "one two")  # restored from backup

    def test_post_write_auto_syncs_word_count_on_legitimate_draft_edit(self):
        # Regression test for the edit-then-sync deadlock: a legitimate edit to
        # article_draft.md that changes its word count must NOT be rolled back
        # just because pipeline_state.json hasn't been reconciled yet -- the
        # hook should auto-run the same `pipeline_runner.py sync-word-count`
        # the pipeline's own "polish"/"address" protocol calls next anyway.
        draft = self.artifacts / "article_draft.md"
        payload = {
            "tool_input": {"file_path": str(draft)},
            "tool_response": {"success": True},
        }
        run_hook(self.tmp, "pre-write", payload)  # seed a backup of "one two" (2 words)
        draft.write_text("one two three four", encoding="utf-8")  # legitimate edit -> 4 words
        result = run_hook(self.tmp, "post-write", payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertNotEqual(output.get("decision"), "block", output)
        self.assertEqual(draft.read_text(encoding="utf-8"), "one two three four")  # not rolled back

        state = json.loads((self.artifacts / "pipeline_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["draft"]["word_count"], 4)  # reconciled by the auto-sync
        metadata = (self.artifacts / "pipeline_metadata.md").read_text(encoding="utf-8")
        self.assertIn("Final word count: 4", metadata)  # sync-word-count updates this too

    def test_post_write_still_rolls_back_a_genuine_metadata_word_count_error(self):
        # pipeline_metadata.md's word count is hand-authored prose, not derived
        # from article_draft.md, so a mismatch there can be a real authoring
        # bug -- auto-sync must stay scoped to article_draft.md only.
        metadata = self.artifacts / "pipeline_metadata.md"
        payload = {
            "tool_input": {"file_path": str(metadata)},
            "tool_response": {"success": True},
        }
        run_hook(self.tmp, "pre-write", payload)  # seed a backup of "Final word count: 2"
        metadata.write_text("Final word count: 99", encoding="utf-8")  # wrong vs. draft's 2 words
        result = run_hook(self.tmp, "post-write", payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output.get("decision"), "block")
        self.assertIn("word-count mismatch", output["reason"])
        self.assertEqual(metadata.read_text(encoding="utf-8"), "Final word count: 2")  # restored


if __name__ == "__main__":
    unittest.main()
