"""Shared utilities for article-pipeline evaluation.

The evaluator intentionally runs subject sessions and grader sessions differently:
subject sessions load project policy/skills, while graders run in Claude Code bare mode
so candidate instructions cannot influence grading.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable, Iterator


class EvalError(RuntimeError):
    """Raised for evaluator/harness failures rather than subject failures."""


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EvalError(f"expected JSON object in {path}")
    return value


def run_process(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    stdin: str | None = None,
    timeout_seconds: int = 1800,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            env=merged_env,
            input=stdin,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        raise EvalError(f"command not found: {cmd[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise EvalError(f"command timed out after {timeout_seconds}s: {' '.join(cmd[:4])}") from exc
    if check and proc.returncode != 0:
        raise EvalError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def parse_claude_json(proc: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    if not proc.stdout.strip():
        raise EvalError(f"Claude produced no stdout (exit {proc.returncode}): {proc.stderr.strip()}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise EvalError(
            f"Claude stdout was not JSON (exit {proc.returncode}): {proc.stdout[:1000]!r}"
        ) from exc
    if not isinstance(payload, dict):
        raise EvalError("Claude JSON response must be an object")
    return payload


def parse_claude_stream(proc: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalError(f"invalid stream-json line from Claude: {line[:500]!r}") from exc
        if isinstance(event, dict):
            events.append(event)
    result = next((event for event in reversed(events) if event.get("type") == "result"), None)
    if not isinstance(result, dict):
        raise EvalError(f"Claude stream contained no result event (exit {proc.returncode})")
    result = dict(result)
    result["_events"] = events
    return result


def claude_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    return {
        "total_cost_usd": payload.get("total_cost_usd"),
        "duration_ms": payload.get("duration_ms"),
        "duration_api_ms": payload.get("duration_api_ms"),
        "num_turns": payload.get("num_turns"),
        "session_id": payload.get("session_id"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
    }


def run_claude_subject(
    prompt: str,
    *,
    cwd: Path,
    model: str,
    effort: str,
    max_budget_usd: float,
    timeout_seconds: int,
    resume_session_id: str | None = None,
) -> dict[str, Any]:
    """Run a production-like subject session with project config but no user/local settings."""
    cmd = [
        "claude",
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--forward-subagent-text",
        "--model",
        model,
        "--effort",
        effort,
        "--setting-sources",
        "project",
        "--permission-mode",
        "dontAsk",
        "--allowedTools",
        "Read,Write,Edit,WebSearch,WebFetch,Agent,Bash(python *),Bash(python3 *)",
        "--max-budget-usd",
        str(max_budget_usd),
    ]
    if resume_session_id:
        cmd.extend(["--resume", resume_session_id])
    cmd.append(prompt)
    env = {
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        # Keep hidden grader/corpus paths out of dynamic prompt sections.
        "CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD": "0",
    }
    proc = run_process(cmd, cwd=cwd, env=env, timeout_seconds=timeout_seconds)
    payload = parse_claude_stream(proc)
    payload["_process_returncode"] = proc.returncode
    payload["_stderr"] = proc.stderr
    return payload


def run_claude_grader(
    instructions: str,
    document_payload: str,
    schema: dict[str, Any],
    *,
    model: str,
    effort: str,
    max_budget_usd: float,
    timeout_seconds: int,
    allow_web: bool,
) -> dict[str, Any]:
    """Run an independent bare grader with structured output.

    Candidate CLAUDE.md, skills, hooks, plugins, MCP servers, and auto memory are not loaded.
    The document itself is piped on stdin so the grader does not need filesystem access.
    """
    cmd = [
        "claude",
        "--bare",
        "-p",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, separators=(",", ":")),
        "--model",
        model,
        "--effort",
        effort,
        "--permission-mode",
        "dontAsk",
        "--max-budget-usd",
        str(max_budget_usd),
        "--no-session-persistence",
    ]
    if allow_web:
        cmd.extend(["--tools", "WebSearch,WebFetch", "--allowedTools", "WebSearch,WebFetch"])
    else:
        cmd.extend(["--tools", ""])
    cmd.append(instructions)
    proc = run_process(
        cmd,
        env={"CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"},
        stdin=document_payload,
        timeout_seconds=timeout_seconds,
    )
    payload = parse_claude_json(proc)
    structured = payload.get("structured_output")
    if not isinstance(structured, dict):
        raise EvalError(f"grader returned no structured_output: {payload.get('result')!r}")
    return {
        "structured_output": structured,
        "metrics": claude_metrics(payload),
        "process_returncode": proc.returncode,
        "stderr": proc.stderr,
    }


def resolve_git_ref(repo: Path, ref: str) -> str:
    proc = run_process(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], cwd=repo)
    if proc.returncode != 0:
        raise EvalError(f"cannot resolve git ref {ref!r}: {proc.stderr.strip()}")
    return proc.stdout.strip()


@contextlib.contextmanager
def detached_worktree(repo: Path, ref: str, parent: Path, name: str) -> Iterator[Path]:
    """Create a temporary detached worktree and always remove it."""
    path = parent / name
    if path.exists():
        shutil.rmtree(path)
    proc = run_process(["git", "worktree", "add", "--detach", str(path), ref], cwd=repo)
    if proc.returncode != 0:
        raise EvalError(f"git worktree add failed: {proc.stderr.strip()}")
    try:
        yield path
    finally:
        run_process(["git", "worktree", "remove", "--force", str(path)], cwd=repo)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)


def scrub_subject_worktree(worktree: Path, *, preserve_knowledge: bool = False) -> None:
    """Remove evaluator material and prior run state from a subject worktree."""
    # Evaluation logic/corpus must not be visible to the subject in serious comparisons.
    for rel in ("evals", "scripts/evals"):
        shutil.rmtree(worktree / rel, ignore_errors=True)
    for path in (worktree / "tests").glob("test_eval*.py") if (worktree / "tests").exists() else []:
        path.unlink(missing_ok=True)

    artifacts = worktree / ".agents" / "artifacts"
    if artifacts.exists():
        for child in artifacts.iterdir():
            if child.name in {".gitkeep", "placeholder"}:
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    artifacts.mkdir(parents=True, exist_ok=True)

    if not preserve_knowledge:
        knowledge = worktree / ".agents" / "knowledge" / "article-pipeline"
        if knowledge.exists():
            shutil.rmtree(knowledge)
        knowledge.mkdir(parents=True, exist_ok=True)


def copy_trial_artifacts(worktree: Path, destination: Path) -> None:
    src = worktree / ".agents" / "artifacts"
    destination.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return
    for child in src.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)


def run_validator(worktree: Path) -> dict[str, Any]:
    proc = run_process(
        [
            "python3",
            "scripts/validate_artifacts.py",
            "--artifact-root",
            ".agents/artifacts",
            "--json",
        ],
        cwd=worktree,
        timeout_seconds=120,
    )
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "status": "EVALUATOR_ERROR",
            "errors": [f"validator output was not JSON: {proc.stdout[:500]!r}"],
            "exit_code": proc.returncode,
            "stderr": proc.stderr,
        }
    if isinstance(report, dict):
        report["exit_code"] = proc.returncode
        report["stderr"] = proc.stderr
        return report
    return {"status": "EVALUATOR_ERROR", "errors": ["validator output was not an object"]}


def sum_numeric(items: Iterable[dict[str, Any]], key: str) -> float:
    total = 0.0
    for item in items:
        value = item.get(key)
        if isinstance(value, (int, float)):
            total += float(value)
    return total


def median(values: Iterable[float]) -> float | None:
    collected = [float(v) for v in values]
    return statistics.median(collected) if collected else None


def now_id(prefix: str = "article-eval") -> str:
    return time.strftime(f"{prefix}-%Y%m%d-%H%M%S", time.gmtime())


def ensure_external_output(repo: Path, output_dir: Path) -> None:
    """Reject output under live article state; warn-by-design for other repo locations."""
    repo = repo.resolve()
    output_dir = output_dir.resolve()
    artifact_root = (repo / ".agents" / "artifacts").resolve()
    if output_dir == artifact_root or artifact_root in output_dir.parents:
        raise EvalError("evaluation output must never be written under .agents/artifacts")
