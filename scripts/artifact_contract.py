"""Shared, deterministic rules for persisted pipeline artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


WORD_RE = re.compile(r"\b[\w’'-]+\b")
TODO_RE = re.compile(r"\[TODO(?::[^\]]*)?\]", re.IGNORECASE)
MANIFEST_NAME = "artifact_manifest.json"


def canonical_word_count(text: str) -> int:
    """Count words in the persisted Markdown draft using the pipeline contract."""
    return len(WORD_RE.findall(text))


def artifact_hashes(root: Path) -> dict[str, dict[str, int | str]]:
    """Return stable hashes for all files except the manifest itself."""
    artifacts: dict[str, dict[str, int | str]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != MANIFEST_NAME:
            relative = path.relative_to(root).as_posix()
            artifacts[relative] = {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
    return artifacts


def verify_manifest(root: Path) -> list[str]:
    """Report missing, changed, or untracked files against the saved manifest."""
    path = root / MANIFEST_NAME
    if not path.is_file():
        return [f"missing required artifact: {MANIFEST_NAME}"]
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        recorded = manifest["artifacts"]
        if not isinstance(recorded, dict):
            raise ValueError("artifacts must be an object")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        return [f"invalid {MANIFEST_NAME}: {exc}"]

    current = artifact_hashes(root)
    errors: list[str] = []
    for name, expected in recorded.items():
        if name not in current:
            errors.append(f"manifest references missing artifact: {name}")
        elif current[name] != expected:
            errors.append(f"manifest hash mismatch: {name}")
    for name in sorted(set(current) - set(recorded)):
        errors.append(f"artifact missing from manifest: {name}")
    return errors
