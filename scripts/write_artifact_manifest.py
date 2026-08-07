#!/usr/bin/env python3
"""Write a hash manifest for one pipeline artifact set."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.artifact_contract import MANIFEST_NAME, artifact_hashes
except ModuleNotFoundError:  # direct `python scripts/write_artifact_manifest.py`
    from artifact_contract import MANIFEST_NAME, artifact_hashes


def write_manifest(root: Path) -> Path:
    root = root.resolve()
    state = json.loads((root / "pipeline_state.json").read_text(encoding="utf-8"))
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "producer": "write_artifact_manifest.py",
        "trace_id": state.get("learning", {}).get("trace_id"),
        "artifacts": {},
    }
    manifest["artifacts"] = artifact_hashes(root)
    output = root / MANIFEST_NAME
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, default=Path(".agents/artifacts"))
    args = parser.parse_args()
    output = write_manifest(args.artifact_root)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
