#!/usr/bin/env bash
# enforce_artifact_contract.sh — the settings.local.json entry point for the
# PreToolUse/PostToolUse artifact-contract gate on .agents/artifacts/*.md
# writes.
#
# This is a thin pass-through to scripts/state_enforcer.sh, not a second
# implementation. state_enforcer.sh already owns the checkpoint (pre-write
# backup), validation (post-write structural checks + targeted
# validate_artifacts.py --skip-manifest-hash contract check), and rollback
# logic for exactly this hook pair — see
# diagnostics/002-state-verification-layer.md §5 for why the full validator
# (with the manifest hash check) is not run on every write, and why this
# stays one execution path instead of two independent hooks racing over the
# same backup files.
set -u

MODE="${1:?usage: enforce_artifact_contract.sh <pre-write|post-write>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$SCRIPT_DIR/state_enforcer.sh" "$MODE"
