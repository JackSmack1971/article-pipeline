#!/usr/bin/env python3
"""Validate the article pipeline's persisted artifact contract.

This is deliberately read-only: it reports whether a run is resumable,
review-required, or publishable without rewriting generated artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from scripts.artifact_contract import TODO_RE, canonical_word_count, verify_manifest
except ModuleNotFoundError:  # direct `python scripts/validate_artifacts.py`
    from artifact_contract import TODO_RE, canonical_word_count, verify_manifest


REQUIRED_ALWAYS = {"pipeline_config.json", "pipeline_state.json", "artifact_manifest.json"}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def artifact_name(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    path = Path(value)
    if path.name != value or path.is_absolute() or ".." in path.parts:
        return None
    return value


def metadata_word_count(text: str) -> int | None:
    matches = re.findall(r"(?:Final word count|word count)\D+(\d[\d,]*)", text, re.I)
    return int(matches[-1].replace(",", "")) if matches else None


def validate(root: Path) -> tuple[dict, int]:
    errors: list[str] = []
    warnings: list[str] = []
    root = root.resolve()
    if not root.is_dir():
        return {"status": "INVALID", "errors": [f"artifact root does not exist: {root}"]}, 1

    try:
        config = load_json(root / "pipeline_config.json")
        state = load_json(root / "pipeline_state.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "INVALID", "errors": [str(exc)]}, 1

    for name in REQUIRED_ALWAYS:
        if not (root / name).is_file():
            errors.append(f"missing required artifact: {name}")

    pipeline = config.get("pipeline", {})
    if pipeline.get("adversarial_dialectic"):
        if not (root / "advocate_context.md").is_file():
            errors.append("missing required artifact: advocate_context.md")
        for name in ("skeptic_evidence.md", "research_context.md", "conflict_register.md"):
            if not (root / name).is_file():
                errors.append(f"missing required artifact: {name}")

    if pipeline.get("fact_check"):
        for name in ("fact_check_report.md", "claims_for_drafting.md"):
            if not (root / name).is_file():
                errors.append(f"missing required artifact: {name}")

    if state.get("stage") in {"APPROVAL", "DRAFT", "POSTDRAFT", "SEO", "LEARNING", "COMPLETE"}:
        for name in ("article_spec.md", "article_draft.md"):
            if not (root / name).is_file():
                errors.append(f"missing required artifact: {name}")

    for name in state.get("artifacts_written", []):
        if artifact_name(name) is None:
            errors.append(f"invalid artifact path in state: {name!r}")
        elif not (root / name).is_file():
            errors.append(f"state references missing artifact: {name}")

    draft_path = root / "article_draft.md"
    draft_words = canonical_word_count(draft_path.read_text(encoding="utf-8")) if draft_path.is_file() else None
    state_words = state.get("draft", {}).get("word_count")
    metadata_path = root / "pipeline_metadata.md"
    metadata_words = metadata_word_count(metadata_path.read_text(encoding="utf-8")) if metadata_path.is_file() else None
    counts = {"draft": draft_words, "state": state_words, "metadata": metadata_words}
    known_counts = {value for value in counts.values() if isinstance(value, int)}
    if state.get("stage") == "COMPLETE" and not isinstance(state_words, int):
        errors.append("pipeline_state.json is missing draft.word_count")
    if len(known_counts) > 1:
        errors.append(f"word-count mismatch: {counts}")

    errors.extend(verify_manifest(root))

    blockers: list[str] = []
    conditions: list[dict[str, str]] = []

    def condition(code: str, detail: str, blocking: bool) -> None:
        item = {"code": code, "detail": detail, "severity": "blocking" if blocking else "review-only"}
        conditions.append(item)
        if blocking:
            blockers.append(detail)

    seo = (root / "seo_package.md").read_text(encoding="utf-8") if (root / "seo_package.md").is_file() else ""
    if re.search(r"E-E-A-T[^\n]*FAILED|FAILED[^\n]*E-E-A-T", seo, re.I):
        condition("UNRESOLVED_EDITORIAL_RISK", "SEO E-E-A-T failure", True)
    combined = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.md"))
    if "[PLACEHOLDER-ONLY]" in combined:
        degraded = not (config.get("pipeline", {}).get("tool_availability", {}).get("code_execution", True))
        condition("TOOL_DEGRADED", "visual assets remain placeholders", not degraded)
    todo_files = [path.name for path in root.glob("*.md") if TODO_RE.search(path.read_text(encoding="utf-8"))]
    if todo_files:
        optional = todo_files == ["seo_package.md"] and not config.get("pipeline", {}).get("required_inputs")
        condition("OPTIONAL_METADATA" if optional else "REQUIRED_INPUT",
                   "TODO metadata remains in artifacts", not optional)

    stage = state.get("stage")
    if stage == "COMPLETE" and (errors or blockers):
        warnings.append("state says COMPLETE but the run still requires review")
    if blockers or errors:
        status = "REVIEW_REQUIRED" if stage in {"COMPLETE", "REVIEW_REQUIRED"} else "INVALID"
        exit_code = 2 if blockers and not errors else 1
    elif stage == "COMPLETE":
        status, exit_code = "PUBLISHABLE", 0
    else:
        status, exit_code = str(stage or "UNKNOWN"), 0
    return {"status": status, "stage": stage, "errors": errors, "blockers": blockers,
            "conditions": conditions,
            "warnings": warnings, "word_counts": counts, "artifact_root": str(root)}, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path(".agents/artifacts"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report, code = validate(args.artifact_root)
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['status']}: {report.get('artifact_root', args.artifact_root)}")
        for key in ("errors", "blockers", "warnings"):
            for item in report.get(key, []):
                print(f"- {item}")
        if report.get("word_counts"):
            print(f"- word counts: {report['word_counts']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
