#!/usr/bin/env bash
# verify.sh — canonical "does this checkout reproduce the control plane"
# check. Run after cloning, and before trusting the hooks registered in
# .claude/settings.json to actually enforce anything.
#
# This intentionally does NOT run scripts/validate_artifacts.py: that
# command checks the state of a specific, in-progress article-pipeline run
# under .agents/artifacts/ (see root CLAUDE.md), not the correctness of the
# checkout itself. A fresh clone with no run in progress, or a repo sitting
# in a legitimate REVIEW_REQUIRED state, would fail it for reasons unrelated
# to code correctness.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY="${VERIFY_PYTHON:-python}"

echo "== hook script syntax =="
bash -n scripts/state_enforcer.sh
bash -n scripts/enforce_artifact_contract.sh
echo "ok"

echo "== settings JSON validity =="
"$PY" -c "import json; json.load(open('.claude/settings.json')); print('.claude/settings.json ok')"

echo "== python unit tests =="
"$PY" -m pytest tests/ -v
