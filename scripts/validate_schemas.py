#!/usr/bin/env python3
"""Validate the article pipeline's JSON Schema contracts.

Two checks, both read-only:

1. Meta-validation: every schemas/*.schema.json is itself a well-formed
   Draft 2020-12 JSON Schema document.
2. Instance validation: the corresponding committed artifact under
   --artifact-root (default .agents/artifacts), if present, conforms to its
   schema. Missing instance files are skipped rather than treated as errors
   -- a fresh clone or an in-progress run legitimately won't have every
   artifact yet (see scripts/validate_artifacts.py's own required-artifact
   logic for that separate concern).

This intentionally does not evaluate business-state rules (stage transitions,
gate counts, KC events); scripts/validate_artifacts.py owns that. This script
only answers "does the JSON shape match the contract every skill was written
against" -- the failure mode this exists to catch is a schema and a producer/
consumer silently drifting apart.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

SCHEMA_TO_ARTIFACT = {
    "pipeline_config.schema.json": "pipeline_config.json",
    "pipeline_state.schema.json": "pipeline_state.json",
    "conflict_decisions.schema.json": "conflict_decisions.json",
    "artifact_manifest.schema.json": "artifact_manifest.json",
}


def validate(schema_root: Path, artifact_root: Path) -> list[str]:
    errors: list[str] = []
    schema_files = sorted(schema_root.glob("*.schema.json"))
    if not schema_files:
        errors.append(f"no schema files found under {schema_root}")
        return errors

    for schema_path in schema_files:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{schema_path.name}: invalid JSON ({exc})")
            continue

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            errors.append(f"{schema_path.name}: not a valid JSON Schema ({exc.message})")
            continue

        artifact_name = SCHEMA_TO_ARTIFACT.get(schema_path.name)
        if artifact_name is None:
            continue
        instance_path = artifact_root / artifact_name
        if not instance_path.is_file():
            continue

        try:
            instance = json.loads(instance_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{artifact_name}: invalid JSON ({exc})")
            continue

        validator = Draft202012Validator(schema)
        for error in sorted(validator.iter_errors(instance), key=str):
            path = "/".join(str(p) for p in error.absolute_path) or "<root>"
            errors.append(f"{artifact_name}: {path}: {error.message}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-root", type=Path, default=Path("schemas"))
    parser.add_argument("--artifact-root", type=Path, default=Path(".agents/artifacts"))
    args = parser.parse_args()

    errors = validate(args.schema_root, args.artifact_root)
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} schema contract violation(s)", file=sys.stderr)
        return 1

    print("OK: all schemas valid; all present artifact instances conform")
    return 0


if __name__ == "__main__":
    sys.exit(main())
