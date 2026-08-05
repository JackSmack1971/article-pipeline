#!/usr/bin/env python3
"""Persist safe pipeline stage transitions and final completion state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from scripts.artifact_contract import canonical_word_count
    from scripts.validate_artifacts import validate
    from scripts.write_artifact_manifest import write_manifest
except ModuleNotFoundError:  # direct `python scripts/pipeline_runner.py`
    from artifact_contract import canonical_word_count
    from validate_artifacts import validate
    from write_artifact_manifest import write_manifest


MAX_GATE_REVISIONS = 3
MAX_CONSECUTIVE_BLOCKED = 3
GATE_DECISIONS = {"approved", "expedite", "revise", "abort"}

ALLOWED_NEXT = {
    "TRIAGE": {"RESEARCH"},
    "RESEARCH": {"FACTCHECK", "APPROVAL"},
    "FACTCHECK": {"APPROVAL"},
    "APPROVAL": {"DRAFT"},
    "DRAFT": {"POSTDRAFT", "SEO"},
    "POSTDRAFT": {"SEO"},
    "SEO": {"LEARNING"},
    "LEARNING": {"COMPLETE"},
    "REVIEW_REQUIRED": {"TRIAGE", "RESEARCH", "FACTCHECK", "APPROVAL", "DRAFT", "POSTDRAFT", "SEO", "LEARNING"},
}


def state_path(root: Path) -> Path:
    return root.resolve() / "pipeline_state.json"


def load_state(root: Path) -> dict:
    with state_path(root).open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("pipeline_state.json must contain a JSON object")
    return value


def save_state(root: Path, state: dict) -> None:
    state_path(root).write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    write_manifest(root)


def advance(root: Path, target: str) -> dict:
    state = load_state(root)
    current = state.get("stage")
    if target == "COMPLETE":
        raise ValueError("use finalize to enter COMPLETE")
    if target not in ALLOWED_NEXT.get(current, set()):
        raise ValueError(f"invalid stage transition: {current!r} -> {target!r}")
    state["stage"] = target
    save_state(root, state)
    return {"stage": target, "status": "ADVANCED"}


def sync_word_count(root: Path) -> dict:
    """Recompute canonical word count from article_draft.md and write it into
    pipeline_state.json and the 'Final word count' line in pipeline_metadata.md."""
    root = root.resolve()
    draft_path = root / "article_draft.md"
    if not draft_path.is_file():
        raise ValueError(f"missing required artifact: {draft_path.name}")
    count = canonical_word_count(draft_path.read_text(encoding="utf-8"))

    state = load_state(root)
    state.setdefault("draft", {})["word_count"] = count
    save_state(root, state)

    metadata_path = root / "pipeline_metadata.md"
    if metadata_path.is_file():
        text = metadata_path.read_text(encoding="utf-8")
        pattern = re.compile(r"(Final word count:\s*)([\d,]+)", re.I)
        formatted = f"{count:,}"
        if pattern.search(text):
            text = pattern.sub(lambda m: f"{m.group(1)}{formatted}", text, count=1)
        else:
            text = text.rstrip("\n") + f"\n\n## Drafting Summary\n- Final word count: {formatted}\n"
        metadata_path.write_text(text, encoding="utf-8")
        write_manifest(root)

    return {"word_count": count, "status": "SYNCED"}


def record_gate(root: Path, gate: str, decision: str) -> dict:
    """Log a gate decision and, on 'expedite', increment gate_expedite_count."""
    if decision not in GATE_DECISIONS:
        raise ValueError(f"invalid gate decision: {decision!r} (must be one of {sorted(GATE_DECISIONS)})")
    state = load_state(root)
    state.setdefault("gate_history", []).append({"gate": gate, "decision": decision})
    if decision == "expedite":
        state["gate_expedite_count"] = state.get("gate_expedite_count", 0) + 1
    save_state(root, state)
    result = {"gate": gate, "decision": decision, "status": "RECORDED"}
    if decision == "expedite" and state["gate_expedite_count"] >= 2:
        result["warning"] = "KC-2 tightening: gate_expedite_count >= 2"
    return result


def increment_revision(root: Path, gate: str) -> dict:
    """Increment a gate's revision cycle count, refusing the 4th call per gate."""
    state = load_state(root)
    cycles = state.setdefault("revision_cycles", {})
    current = cycles.get(gate, 0)
    if current >= MAX_GATE_REVISIONS:
        return {"gate": gate, "revision_cycles": current, "status": "HALT_REQUIRED",
                "reason": f"gate {gate!r} already used all {MAX_GATE_REVISIONS} revision cycles"}
    cycles[gate] = current + 1
    save_state(root, state)
    return {"gate": gate, "revision_cycles": cycles[gate], "status": "RECORDED"}


def record_kc_event(root: Path, code: str, status: str, detail: str = "") -> dict:
    """Log a kill-condition (KC-1..KC-6) check outcome."""
    state = load_state(root)
    state.setdefault("kc_events", []).append({"code": code, "status": status, "detail": detail})
    save_state(root, state)
    result = {"code": code, "status": status, "recorded": True}
    if status == "HALT":
        result["action"] = "HALT_REQUIRED"
    return result


def record_audit_verdict(root: Path, verdict: str) -> dict:
    """Track consecutive BLOCKED inline/holistic audit verdicts; refuse past the 3rd."""
    state = load_state(root)
    if verdict == "BLOCKED":
        state["consecutive_blocked_audits"] = state.get("consecutive_blocked_audits", 0) + 1
    else:
        state["consecutive_blocked_audits"] = 0
    save_state(root, state)
    count = state["consecutive_blocked_audits"]
    status = "HALT_REQUIRED" if count >= MAX_CONSECUTIVE_BLOCKED else "RECORDED"
    return {"verdict": verdict, "consecutive_blocked_audits": count, "status": status}


def finalize(root: Path) -> tuple[dict, int]:
    root = root.resolve()
    sync_word_count(root)
    state = load_state(root)
    state["stage"] = "REVIEW_REQUIRED"
    save_state(root, state)
    report, _ = validate(root)
    state["stage"] = "COMPLETE" if not report["errors"] and not report["blockers"] else "REVIEW_REQUIRED"
    save_state(root, state)
    report, code = validate(root)
    return report, code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=(
        "advance", "finalize", "sync-word-count",
        "record-gate", "record-kc-event", "increment-revision", "record-audit-verdict",
    ))
    parser.add_argument("--stage")
    parser.add_argument("--gate")
    parser.add_argument("--decision", choices=sorted(GATE_DECISIONS))
    parser.add_argument("--code")
    parser.add_argument("--kc-status", choices=("PASS", "HALT"))
    parser.add_argument("--verdict", choices=("PASS", "PASS_WITH_NOTES", "BLOCKED"))
    parser.add_argument("--detail", default="")
    parser.add_argument("--artifact-root", type=Path, default=Path(".agents/artifacts"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        if args.command == "advance":
            if not args.stage:
                parser.error("advance requires --stage")
            report, code = advance(args.artifact_root, args.stage), 0
        elif args.command == "sync-word-count":
            report, code = sync_word_count(args.artifact_root), 0
        elif args.command == "record-gate":
            if not args.gate or not args.decision:
                parser.error("record-gate requires --gate and --decision")
            report = record_gate(args.artifact_root, args.gate, args.decision)
            code = 2 if report["status"] == "HALT_REQUIRED" else 0
        elif args.command == "increment-revision":
            if not args.gate:
                parser.error("increment-revision requires --gate")
            report = increment_revision(args.artifact_root, args.gate)
            code = 2 if report["status"] == "HALT_REQUIRED" else 0
        elif args.command == "record-kc-event":
            if not args.code or not args.kc_status:
                parser.error("record-kc-event requires --code and --kc-status")
            report = record_kc_event(args.artifact_root, args.code, args.kc_status, args.detail)
            code = 2 if report["status"] == "HALT" else 0
        elif args.command == "record-audit-verdict":
            if not args.verdict:
                parser.error("record-audit-verdict requires --verdict")
            report = record_audit_verdict(args.artifact_root, args.verdict)
            code = 2 if report["status"] == "HALT_REQUIRED" else 0
        else:
            report, code = finalize(args.artifact_root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True) if args.as_json else report)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
