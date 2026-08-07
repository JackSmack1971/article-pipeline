"""Shared, deterministic rules for persisted pipeline artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


WORD_RE = re.compile(r"\b[\w’'-]+\b")
TODO_RE = re.compile(r"\[TODO(?::[^\]]*)?\]", re.IGNORECASE)
MANIFEST_NAME = "artifact_manifest.json"
EEAT_STATUSES = {"PASS", "FAIL", "NA"}


def canonical_word_count(text: str) -> int:
    """Count words in the persisted Markdown draft using the pipeline contract."""
    return len(WORD_RE.findall(text))


def seo_word_count(text: str) -> int | None:
    """Extract the '(N words)' figure from seo_package.md's word-count checklist row."""
    match = re.search(r"\((\d[\d,]*)\s*words\)", text, re.I)
    return int(match.group(1).replace(",", "")) if match else None


def extract_eeat_status(text: str) -> dict[str, str | None] | None:
    """Parse seo_package.md's 'E-E-A-T block present' checklist row into a
    structured {status, reason} value, instead of leaving downstream callers
    to infer machine state from prose vocabulary (e.g. 'FAIL' vs 'FAILED').

    Returns None if seo_package.md has no such row (e.g. seo_pass disabled).
    Raises ValueError if the row exists but its status cell uses no recognized
    PASS/FAIL/NA vocabulary — this is a producer contract violation and must
    surface rather than silently pass.
    """
    row = re.search(r"E-E-A-T block present\s*\|([^\n|]*)\|", text, re.I)
    if not row:
        return None
    cell = row.group(1).strip()
    if re.search(r"\bFAIL(?:ED)?\b", cell, re.I):
        status = "FAIL"
    elif re.search(r"\bN/?A\b", cell, re.I):
        status = "NA"
    elif re.search(r"\bPASS\b", cell, re.I):
        status = "PASS"
    else:
        raise ValueError(f"unrecognized E-E-A-T checklist status: {cell!r}")

    reason = None
    if status == "FAIL":
        gaps = re.search(r"^##\s*E-E-A-T Gaps\s*\n(.*?)(?=\n##\s|\Z)", text, re.I | re.M | re.S)
        reason = gaps.group(1).strip() if gaps else cell
    return {"status": status, "reason": reason}


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
