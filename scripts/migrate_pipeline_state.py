#!/usr/bin/env python3
"""Migrate pipeline_state.json from legacy schema_version 1 to canonical schema_version 2.

schema_version 1 (legacy) nested gate and counter data under a top-level
'gates' array and a 'telemetry' object: telemetry.revision_cycles,
telemetry.kc_events (using 'check'/'result' field names),
telemetry.gate_expedite_count, telemetry.consecutive_blocked_audits,
telemetry.tool_degradation.

schema_version 2 (canonical, what scripts/pipeline_runner.py has always
written via record_gate/increment_revision/record_kc_event/
record_audit_verdict) flattens all of that to top-level fields: gate_history,
revision_cycles, kc_events (using 'code'/'status'), gate_expedite_count,
consecutive_blocked_audits, tool_degradation. See schemas/pipeline_state.schema.json.

This module is invoked through the sanctioned mutation path,
`python scripts/pipeline_runner.py migrate-state`, so the state-file write
shield in .claude/settings.local.json (which only allows unchained
pipeline_runner.py invocations to touch pipeline_state.json) covers it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_SCHEMA_VERSION = 2


def _migrate_kc_event(event: dict) -> dict:
    migrated = dict(event)
    if "check" in migrated and "code" not in migrated:
        migrated["code"] = migrated.pop("check")
    if "result" in migrated and "status" not in migrated:
        migrated["status"] = migrated.pop("result")
    return migrated


def _migrate_gate(gate: dict) -> dict:
    migrated = dict(gate)
    if "result" in migrated and "decision" not in migrated:
        migrated["decision"] = migrated.pop("result")
    return migrated


def migrate(state: dict) -> tuple[dict, bool]:
    """Return (migrated_state, changed). Idempotent: a schema_version 2 state
    is returned unchanged."""
    version = state.get("schema_version")
    if version == CURRENT_SCHEMA_VERSION:
        return state, False
    if version not in (None, 1):
        raise ValueError(f"unknown pipeline_state.json schema_version: {version!r}")

    migrated = dict(state)
    telemetry = migrated.pop("telemetry", {}) or {}
    legacy_gates = migrated.pop("gates", []) or []

    gate_history = [_migrate_gate(g) for g in legacy_gates] + list(migrated.get("gate_history", []))
    if gate_history:
        migrated["gate_history"] = gate_history

    revision_cycles = {**telemetry.get("revision_cycles", {}), **migrated.get("revision_cycles", {})}
    if revision_cycles:
        migrated["revision_cycles"] = revision_cycles

    kc_events = [_migrate_kc_event(e) for e in telemetry.get("kc_events", [])] + list(migrated.get("kc_events", []))
    if kc_events:
        migrated["kc_events"] = kc_events

    if "gate_expedite_count" not in migrated:
        if "gate_expedite_count" in telemetry:
            migrated["gate_expedite_count"] = telemetry["gate_expedite_count"]
    if "consecutive_blocked_audits" not in migrated:
        if "consecutive_blocked_audits" in telemetry:
            migrated["consecutive_blocked_audits"] = telemetry["consecutive_blocked_audits"]

    tool_degradation = list(telemetry.get("tool_degradation", [])) + list(migrated.get("tool_degradation", []))
    if tool_degradation:
        migrated["tool_degradation"] = tool_degradation

    migrated["schema_version"] = CURRENT_SCHEMA_VERSION
    return migrated, True


def migrate_file(root: Path) -> dict:
    root = root.resolve()
    path = root / "pipeline_state.json"
    state = json.loads(path.read_text(encoding="utf-8"))
    migrated, changed = migrate(state)
    if changed:
        path.write_text(json.dumps(migrated, indent=2) + "\n", encoding="utf-8")
    return {"status": "MIGRATED" if changed else "ALREADY_CURRENT", "schema_version": migrated["schema_version"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(".agents/artifacts"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        result = migrate_file(args.artifact_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2) if args.as_json else result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
