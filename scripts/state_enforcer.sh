#!/usr/bin/env bash
# state_enforcer.sh — Full State Verification layer for the article pipeline's
# .claude/ control plane.
#
# Invoked exclusively by hooks in .claude/settings.json. Reads the Claude
# Code hook JSON payload on stdin, writes hook-protocol JSON (continue,
# hookSpecificOutput, decision, ...) to stdout, and appends one JSON telemetry
# line per invocation. See diagnostics/002-state-verification-layer.md for the
# design rationale and known limitations.
#
# Modes: session-start | pre-write | pre-bash | post-write
set -u

MODE="${1:?usage: state_enforcer.sh <session-start|pre-write|pre-bash|post-write>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ARTIFACT_ROOT="$ROOT_DIR/.agents/artifacts"
STATE_FILE="$ARTIFACT_ROOT/pipeline_state.json"
STATE_DIR="$ROOT_DIR/.agents/.state_enforcer"
BACKUP_DIR="$STATE_DIR/backups"
LOG_FILE="$STATE_DIR/telemetry.jsonl"
PY="${STATE_ENFORCER_PYTHON:-python}"

mkdir -p "$BACKUP_DIR" 2>/dev/null || true

START_NS=$(date +%s%N 2>/dev/null || echo 0)
INPUT_JSON="$(cat)"

export SE_ROOT_DIR="$ROOT_DIR"
export SE_ARTIFACT_ROOT="$ARTIFACT_ROOT"
export SE_STATE_FILE="$STATE_FILE"
export SE_BACKUP_DIR="$BACKUP_DIR"
export SE_LOG_FILE="$LOG_FILE"
export SE_MODE="$MODE"
export SE_START_NS="$START_NS"

# --- Fast paths: skip spawning Python entirely for events that plainly do not
# touch the artifact tree or pipeline_state.json. Path separators may be
# backslash (Windows) or forward slash, so this is a coarse substring check;
# the Python stage does the real, separator-safe path resolution.
case "$MODE" in
  pre-write|post-write)
    case "$INPUT_JSON" in
      *artifacts*) ;;  # falls through to Python
      *) exit 0 ;;
    esac
    ;;
  pre-bash)
    case "$INPUT_JSON" in
      *pipeline_state.json*) ;;  # falls through to Python
      *) exit 0 ;;
    esac
    ;;
esac

# --- Python payload per mode. JSON parsing and path resolution are done in
# Python (already a hard dependency of this repo) rather than bash/regex,
# since there is no jq on this machine and hand-parsed JSON in bash is a
# correctness and injection risk against a policy-enforcement script.
read -r -d '' PY_COMMON <<'PYCOMMON'
import json, os, sys, time

def log(event, outcome, detail=""):
    try:
        start_ns = int(os.environ.get("SE_START_NS", "0") or "0")
        elapsed_ms = max(0, (time.time_ns() - start_ns) // 1_000_000) if start_ns else None
        line = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": os.environ.get("SE_MODE", ""),
            "event": event,
            "outcome": outcome,
            "latency_ms": elapsed_ms,
            "detail": detail,
        }
        with open(os.environ["SE_LOG_FILE"], "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line) + "\n")
    except OSError:
        pass

def emit(obj):
    print(json.dumps(obj))

def resolve(file_path):
    root = os.environ["SE_ROOT_DIR"]
    p = file_path if os.path.isabs(file_path) else os.path.join(root, file_path)
    return os.path.realpath(p)
PYCOMMON

case "$MODE" in

  session-start)
    read -r -d '' PY_BODY <<'PYEOF'
if not os.path.isfile(os.environ["SE_STATE_FILE"]):
    log("session_start", "skipped_no_state")
    sys.exit(0)

import subprocess
root = os.environ["SE_ROOT_DIR"]
artifact_root = os.environ["SE_ARTIFACT_ROOT"]
validator = os.path.join(root, "scripts", "validate_artifacts.py")
proc = subprocess.run(
    [sys.executable, validator, "--artifact-root", artifact_root, "--json"],
    capture_output=True, text=True, cwd=root,
)
try:
    report = json.loads(proc.stdout)
except json.JSONDecodeError:
    report = {"status": "UNKNOWN", "errors": [(proc.stdout + proc.stderr).strip()[:500]]}

status = report.get("status")
stage = report.get("stage")
errors = report.get("errors") or []
blockers = report.get("blockers") or []

if proc.returncode == 1 or status == "INVALID":
    detail = "; ".join(errors) or "artifact/state contract violation"
    log("session_start", "halt", detail)
    emit({
        "continue": False,
        "stopReason": (
            "[STATE_ENFORCER] SessionStart HALT: pipeline_state.json / .agents/artifacts "
            f"contract mismatch ({detail}). Re-run TRIAGE validation or repair the artifact "
            "set before any stage transition."
        ),
        "systemMessage": f"State Enforcer: HALTED — {detail}",
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                "[STATE_ENFORCER] HARD HALT. python scripts/validate_artifacts.py --json reported "
                f"status={status} stage={stage} errors={errors}. Per the pipeline contract "
                "(root CLAUDE.md, TRIAGE step 0), do not proceed past TRIAGE. Resolve the listed "
                "errors, or explicitly re-run article-complexity-triage, before continuing."
            ),
        },
    })
    sys.exit(0)

if proc.returncode == 2 or blockers:
    log("session_start", "warn_review_required", "; ".join(blockers))
    emit({
        "systemMessage": f"State Enforcer: REVIEW_REQUIRED — {len(blockers)} blocker(s) pending",
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"[STATE_ENFORCER] Resumed at stage={stage} with unresolved blockers={blockers}. "
                "This run cannot reach COMPLETE until these are resolved (see pipeline_runner.py finalize)."
            ),
        },
    })
    sys.exit(0)

log("session_start", "ok", f"stage={stage}")
emit({
    "suppressOutput": True,
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": f"[STATE_ENFORCER] Resumed pipeline at stage={stage}; artifact contract OK.",
    },
})
PYEOF
    printf '%s' "$INPUT_JSON" | "$PY" -c "$PY_COMMON
$PY_BODY"
    ;;

  pre-write)
    read -r -d '' PY_BODY <<'PYEOF'
payload = json.loads(sys.stdin.read())
tool_name = payload.get("tool_name", "")
tool_input = payload.get("tool_input") or {}
file_path = tool_input.get("file_path")
if not file_path:
    sys.exit(0)

state_file = os.path.realpath(os.environ["SE_STATE_FILE"])
artifact_root = os.path.realpath(os.environ["SE_ARTIFACT_ROOT"])
abs_path = resolve(file_path)

if abs_path == state_file:
    log("pre_write", "deny", file_path)
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "[STATE_ENFORCER] pipeline_state.json is mutated only by "
                "scripts/pipeline_runner.py (advance/finalize/record-gate/record-kc-event/"
                "increment-revision/record-audit-verdict) so PS.stage can reach COMPLETE only "
                f"through finalize()'s own validate() gate. Direct {tool_name} to this file is "
                "blocked; run the appropriate pipeline_runner.py subcommand instead."
            ),
        }
    })
    sys.exit(0)

if abs_path.startswith(artifact_root + os.sep) and os.path.splitext(abs_path)[1] in (".md", ".json"):
    import shutil, time as _t
    if os.path.isfile(abs_path):
        os.makedirs(os.environ["SE_BACKUP_DIR"], exist_ok=True)
        rel = os.path.relpath(abs_path, artifact_root).replace(os.sep, "__")
        dest = os.path.join(os.environ["SE_BACKUP_DIR"], f"{rel}.{int(_t.time()*1000)}.bak")
        shutil.copy2(abs_path, dest)
        log("pre_write", "backed_up", rel)
    else:
        log("pre_write", "no_prior_version", os.path.relpath(abs_path, artifact_root))
sys.exit(0)
PYEOF
    printf '%s' "$INPUT_JSON" | "$PY" -c "$PY_COMMON
$PY_BODY"
    ;;

  pre-bash)
    read -r -d '' PY_BODY <<'PYEOF'
import re
payload = json.loads(sys.stdin.read())
command = (payload.get("tool_input") or {}).get("command", "")

sanctioned = re.match(r'^\s*python3?\s+(?:\.[\\/])?scripts[\\/]pipeline_runner\.py\b', command)
chained = re.search(r'[;&|`]|\$\(', command)

if sanctioned and not chained:
    log("pre_bash", "allow", command[:200])
    sys.exit(0)

log("pre_bash", "deny", command[:200])
emit({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            "[STATE_ENFORCER] Bash commands referencing pipeline_state.json are blocked unless "
            "they are a single, unchained `python scripts/pipeline_runner.py ...` invocation — "
            "the only sanctioned path to mutate pipeline state. This is a heuristic guard on "
            "command text, not a filesystem-level guarantee; see diagnostics/002 for the residual-"
            "bypass caveat."
        ),
    }
})
PYEOF
    printf '%s' "$INPUT_JSON" | "$PY" -c "$PY_COMMON
$PY_BODY"
    ;;

  post-write)
    read -r -d '' PY_BODY <<'PYEOF'
import glob, shutil

payload = json.loads(sys.stdin.read())
tool_input = payload.get("tool_input") or {}
tool_response = payload.get("tool_response") or {}
file_path = tool_input.get("file_path")
if not file_path:
    sys.exit(0)

state_file = os.path.realpath(os.environ["SE_STATE_FILE"])
artifact_root = os.path.realpath(os.environ["SE_ARTIFACT_ROOT"])
backup_dir = os.environ["SE_BACKUP_DIR"]
abs_path = resolve(file_path)

if abs_path == state_file:
    # The PreToolUse shield should have denied this before it ever landed.
    log("post_write", "anomaly_state_file_written", file_path)
    emit({
        "decision": "block",
        "reason": (
            "[STATE_ENFORCER] CRITICAL: a write to pipeline_state.json reached PostToolUse — "
            "the PreToolUse shield should have denied this. Treat pipeline_state.json as "
            "untrusted until it is re-checked with `python scripts/validate_artifacts.py --json`."
        ),
    })
    sys.exit(0)

if not (abs_path.startswith(artifact_root + os.sep) and abs_path.endswith(".md")):
    sys.exit(0)

if tool_response.get("success") is False:
    log("post_write", "skipped_tool_failed", file_path)
    sys.exit(0)

rel = os.path.relpath(abs_path, artifact_root).replace(os.sep, "__")
candidates = sorted(glob.glob(os.path.join(backup_dir, f"{rel}.*.bak")))
latest_backup = candidates[-1] if candidates else None

def fail(reason):
    restored = False
    if latest_backup:
        shutil.copy2(latest_backup, abs_path)
        restored = True
    elif os.path.isfile(abs_path):
        os.remove(abs_path)
    log("post_write", "rollback", f"{rel}: {reason}")
    message = (
        f"[STATE_ENFORCER] POST-WRITE VALIDATION FAILED for {rel}: {reason}. "
        + (f"Rolled back to backup {os.path.basename(latest_backup)}."
           if restored else "No prior backup existed; removed the corrupt file "
           "(rolled back to its pre-write state of not existing).")
    )
    print(message, file=sys.stderr)
    emit({
        "decision": "block",
        "reason": message,
    })

try:
    size = os.path.getsize(abs_path)
except OSError as exc:
    fail(f"file unreadable after write ({exc})")
    sys.exit(0)

if size == 0:
    fail("file is empty after write")
    sys.exit(0)

with open(abs_path, "rb") as fh:
    data = fh.read()

if b"\x00" in data:
    fail("file contains NUL bytes (binary/corruption signature)")
    sys.exit(0)

if latest_backup:
    prev_size = os.path.getsize(latest_backup)
    if prev_size > 200 and size < prev_size * 0.2:
        fail(f"file shrank from {prev_size}B to {size}B (>80% drop) — likely truncated write")
        sys.exit(0)

# Targeted contract check: run the read-only validator with the manifest
# hash comparison disabled (--skip-manifest-hash), since the manifest is
# only regenerated at the final write_artifact_manifest.py checkpoint and
# would otherwise flag every legitimate mid-draft edit as a hash mismatch
# (see diagnostics/002-state-verification-layer.md §3). Only roll back when
# a reported error actually names this file, so an unrelated pending
# artifact (e.g. article_draft.md not yet written while spec is still being
# drafted) cannot block this write.
import subprocess
validator = os.path.join(os.environ["SE_ROOT_DIR"], "scripts", "validate_artifacts.py")
proc = subprocess.run(
    [sys.executable, validator, "--artifact-root", artifact_root, "--json", "--skip-manifest-hash"],
    capture_output=True, text=True, cwd=os.environ["SE_ROOT_DIR"],
)
try:
    contract_report = json.loads(proc.stdout)
except json.JSONDecodeError:
    contract_report = None

if contract_report is not None and proc.returncode == 1:
    implicated = [e for e in (contract_report.get("errors") or []) if rel.split("__")[-1] in e]
    if rel in ("article_draft.md", "pipeline_metadata.md"):
        implicated += [e for e in (contract_report.get("errors") or []) if "word-count mismatch" in e]
    if implicated:
        fail("contract violation: " + "; ".join(dict.fromkeys(implicated)))
        sys.exit(0)

for old in candidates[:-3]:
    try:
        os.remove(old)
    except OSError:
        pass

log("post_write", "validated", rel)
emit({"suppressOutput": True})
PYEOF
    printf '%s' "$INPUT_JSON" | "$PY" -c "$PY_COMMON
$PY_BODY"
    ;;

  *)
    echo "[STATE_ENFORCER] unknown mode: $MODE" >&2
    exit 1
    ;;
esac
