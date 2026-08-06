#!/usr/bin/env python3
"""Matched baseline/candidate experiment runner for Qualified Publish Rate (QPR)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.evals.claim_citation_grader import grade_article as grade_claims
    from scripts.evals.common import (
        EvalError,
        atomic_write_json,
        claude_metrics,
        copy_trial_artifacts,
        detached_worktree,
        ensure_external_output,
        load_json,
        median,
        now_id,
        resolve_git_ref,
        run_claude_subject,
        run_process,
        run_validator,
        scrub_subject_worktree,
        sum_numeric,
    )
    from scripts.evals.editorial_grader import grade_article as grade_editorial
except ModuleNotFoundError:  # direct invocation
    from claim_citation_grader import grade_article as grade_claims
    from common import (
        EvalError,
        atomic_write_json,
        claude_metrics,
        copy_trial_artifacts,
        detached_worktree,
        ensure_external_output,
        load_json,
        median,
        now_id,
        resolve_git_ref,
        run_claude_subject,
        run_process,
        run_validator,
        scrub_subject_worktree,
        sum_numeric,
    )
    from editorial_grader import grade_article as grade_editorial


DEFAULT_THRESHOLDS = {
    "material_claim_precision_min": 0.95,
    "citation_support_rate_min": 0.95,
    "editorial_mean_min": 4.0,
    "editorial_dimension_min": 3,
    "max_missing_material_citations": 0,
}

GATE_PATTERNS = {
    "thesis_confirmation": [r"confirm[^\n]{0,80}thesis", r"thesis[^\n]{0,80}confirm"],
    "approval": [r"APPROVAL GATE", r"approved.*conflict"],
    "red_team": [r"Red Team Report", r"Threat Level"],
    "reader": [r"Reader Simulation", r"Accessibility Rating"],
    "delivery": [r"author[^\n]{0,100}(deliver|byline)", r"E-E-A-T[^\n]{0,100}(decision|gap)"],
}


def load_corpus(path: Path) -> list[dict[str, Any]]:
    files = [path] if path.is_file() else sorted(path.glob("*.json"))
    if not files:
        raise EvalError(f"no brief JSON files found under {path}")
    briefs: list[dict[str, Any]] = []
    for file in files:
        value = json.loads(file.read_text(encoding="utf-8"))
        if isinstance(value, dict) and isinstance(value.get("briefs"), list):
            for item in value["briefs"]:
                if not isinstance(item, dict):
                    raise EvalError(f"corpus wrapper in {file} contains a non-object brief")
                briefs.append(item)
        elif isinstance(value, dict):
            briefs.append(value)
        else:
            raise EvalError(f"corpus file {file} must be a brief object or an object with a briefs array")
    seen: set[str] = set()
    for brief in briefs:
        brief_id = brief.get("id")
        if not isinstance(brief_id, str) or not brief_id:
            raise EvalError("every brief requires a non-empty string id")
        if brief_id in seen:
            raise EvalError(f"duplicate brief id: {brief_id}")
        seen.add(brief_id)
        for key in ("topic_brief", "target_audience", "scripted_decisions"):
            if key not in brief:
                raise EvalError(f"brief {brief_id!r} missing {key}")
        if not isinstance(brief["scripted_decisions"], dict):
            raise EvalError(f"brief {brief_id!r} scripted_decisions must be an object")
    return briefs


def thresholds_for(brief: dict[str, Any]) -> dict[str, Any]:
    result = dict(DEFAULT_THRESHOLDS)
    override = brief.get("thresholds")
    if isinstance(override, dict):
        result.update(override)
    return result


def build_subject_prompt(brief: dict[str, Any]) -> str:
    decisions = brief.get("scripted_decisions", {})
    decision_lines = "\n".join(f"- {key}: {value}" for key, value in decisions.items())
    intended = brief.get("intended_thesis") or "Develop the strongest defensible thesis supported by the research; do not preserve an unsupported starting assumption."
    return f"""/multi-agent-article-pipeline

Produce the article described below using the repository's normal article pipeline.

TOPIC BRIEF
{brief['topic_brief']}

TARGET AUDIENCE
{brief['target_audience']}

EDITORIAL DIRECTION
{intended}

This is a matched evaluation run. The following responses are explicit, predeclared user decisions for this run. When the corresponding gate is reached and the listed response is a valid option, apply it exactly; do not invent a different choice and do not ask for confirmation again unless the pipeline requires information not covered here.
{decision_lines}

Evaluation integrity requirements:
- Follow the production pipeline and all normal factual/citation controls.
- Write production artifacts only under `.agents/artifacts/`.
- Do not search for, inspect, infer, or modify evaluator code, benchmark corpora, grader prompts, expected answers, sibling worktrees, or experiment results.
- Do not optimize for an imagined grader. Optimize for a genuinely publishable article for the target audience.
- Continue through normal pipeline stages until COMPLETE or a legitimate REVIEW_REQUIRED/HALT condition is reached.
"""


def load_state(worktree: Path) -> dict[str, Any]:
    path = worktree / ".agents" / "artifacts" / "pipeline_state.json"
    if not path.is_file():
        return {}
    try:
        return load_json(path)
    except (OSError, json.JSONDecodeError, EvalError):
        return {}


def match_scripted_decision(text: str, brief: dict[str, Any], used: set[str], stage: str | None) -> tuple[str, str] | None:
    decisions = brief.get("scripted_decisions", {})
    stage_preferences = {
        "TRIAGE": ["thesis_confirmation"],
        "APPROVAL": ["approval"],
        "POSTDRAFT": ["red_team", "reader"],
        "SEO": ["delivery"],
    }
    candidates = stage_preferences.get(stage or "", []) + list(GATE_PATTERNS)
    for key in candidates:
        if key in used or key not in decisions:
            continue
        patterns = GATE_PATTERNS.get(key, [])
        if stage and key in stage_preferences.get(stage, []):
            if stage != "POSTDRAFT" or any(re.search(pattern, text, re.I) for pattern in patterns):
                return key, str(decisions[key])
        if any(re.search(pattern, text, re.I) for pattern in patterns):
            return key, str(decisions[key])
    return None


def terminal_stage(stage: str | None) -> bool:
    return stage in {"COMPLETE", "REVIEW_REQUIRED"}


def extract_agent_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("type") == "tool_use" and value.get("name") in {"Agent", "Task"}:
                tool_input = value.get("input")
                if isinstance(tool_input, dict):
                    calls.append(tool_input)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload.get("_events", []))
    return calls


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def agent_call_name(call: dict[str, Any]) -> str:
    for key in ("subagent_type", "agent", "name", "agent_name"):
        value = call.get(key)
        if isinstance(value, str):
            return value
    return ""


def agent_call_prompt(call: dict[str, Any]) -> str:
    for key in ("prompt", "task", "instructions"):
        value = call.get(key)
        if isinstance(value, str):
            return value
    return ""


def dynamic_isolation_guardrails(worktree: Path, subject: dict[str, Any]) -> dict[str, Any]:
    all_calls = [call for turn in subject.get("turns", []) for call in turn.get("agent_calls", [])]
    config_path = worktree / ".agents" / "artifacts" / "pipeline_config.json"
    config = load_json(config_path) if config_path.is_file() else {}
    pipeline = config.get("pipeline") if isinstance(config.get("pipeline"), dict) else {}
    expected_dialectic = bool(pipeline.get("adversarial_dialectic"))
    expected_red = bool(pipeline.get("red_team"))

    named = [(agent_call_name(call).lower(), agent_call_prompt(call)) for call in all_calls]
    advocate_calls = [prompt for name, prompt in named if "article-advocate" in name or name.endswith("advocate")]
    skeptic_calls = [prompt for name, prompt in named if "article-skeptic" in name or name.endswith("skeptic")]
    red_calls = [prompt for name, prompt in named if "article-red-team" in name or "red-team" in name]

    checks: list[dict[str, Any]] = []
    if expected_dialectic:
        checks.append({"check": "advocate delegated", "pass": bool(advocate_calls), "count": len(advocate_calls)})
        checks.append({"check": "skeptic delegated", "pass": bool(skeptic_calls), "count": len(skeptic_calls)})
    if expected_red:
        checks.append({"check": "red team delegated", "pass": bool(red_calls), "count": len(red_calls)})

    advocate_path = worktree / ".agents" / "artifacts" / "advocate_context.md"
    leaked_fragments: list[str] = []
    if skeptic_calls and advocate_path.is_file():
        sensitive: list[str] = []
        for line in advocate_path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*-\s*\*\*(Statement|Strength):\*\*\s*(.+)", line, re.I)
            if match and len(normalize_text(match.group(2))) >= 30:
                sensitive.append(match.group(2).strip())
        skeptic_text = normalize_text("\n".join(skeptic_calls))
        for fragment in sensitive:
            normalized = normalize_text(fragment)
            if normalized and normalized in skeptic_text:
                leaked_fragments.append(fragment[:180])
        checks.append({
            "check": "skeptic prompt excludes advocate claims/framing",
            "pass": not leaked_fragments,
            "leaked_fragments": leaked_fragments[:10],
        })

    draft_path = worktree / ".agents" / "artifacts" / "article_draft.md"
    leaked_body_fragments: list[str] = []
    if red_calls and draft_path.is_file():
        draft = draft_path.read_text(encoding="utf-8")
        h2_positions = [match.start() for match in re.finditer(r"(?m)^##\s+", draft)]
        pre_conclusion = draft[: h2_positions[-1]] if h2_positions else ""
        candidates = [normalize_text(p) for p in re.split(r"\n\s*\n", pre_conclusion)]
        red_text = normalize_text("\n".join(red_calls))
        for paragraph in candidates:
            if len(paragraph) < 100:
                continue
            probe = paragraph[:120]
            if probe in red_text:
                leaked_body_fragments.append(probe)
        checks.append({
            "check": "red-team prompt excludes pre-conclusion article body",
            "pass": not leaked_body_fragments,
            "leaked_fragments": leaked_body_fragments[:10],
        })

    return {
        "pass": all(item.get("pass") is True for item in checks) if checks else True,
        "agent_call_count": len(all_calls),
        "checks": checks,
    }


def subject_capability_guardrails(worktree: Path) -> dict[str, Any]:
    requirements = {
        "article-advocate.md": {"must_include": {"WebSearch", "Write"}, "must_exclude": {"Read"}},
        "article-skeptic.md": {"must_include": {"WebSearch", "Write"}, "must_exclude": {"Read"}},
        "article-red-team.md": {"must_include": {"WebSearch"}, "must_exclude": {"Read", "Write"}},
    }
    checks: list[dict[str, Any]] = []
    for filename, rule in requirements.items():
        path = worktree / ".claude" / "agents" / filename
        if not path.is_file():
            checks.append({"agent": filename, "pass": False, "reason": "missing agent definition"})
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
        tools: set[str] = set()
        in_tools = False
        for line in frontmatter.splitlines():
            if line.strip() == "tools:":
                in_tools = True
                continue
            if in_tools:
                match = re.match(r"\s*-\s*([A-Za-z0-9_-]+)\s*$", line)
                if match:
                    tools.add(match.group(1))
                    continue
                if line and not line.startswith((" ", "\t")):
                    in_tools = False
        missing = sorted(rule["must_include"] - tools)
        forbidden = sorted(rule["must_exclude"] & tools)
        passed = not missing and not forbidden
        checks.append({
            "agent": filename,
            "pass": passed,
            "tools": sorted(tools),
            "missing_required_tools": missing,
            "forbidden_tools_present": forbidden,
        })
    return {"pass": all(item["pass"] for item in checks), "checks": checks}


def claude_infrastructure_failure(payload: dict[str, Any]) -> str | None:
    if payload.get("_process_returncode") in (None, 0):
        return None
    text = f"{payload.get('result', '')}\n{payload.get('_stderr', '')}".lower()
    patterns = (
        "authentication", "not logged in", "rate limit", "rate_limit", "overloaded",
        "billing", "connection error", "network error", "model not found", "model_not_found",
        "server error", "service unavailable",
    )
    for pattern in patterns:
        if pattern in text:
            return pattern
    return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_subject_trial(
    worktree: Path,
    brief: dict[str, Any],
    *,
    model: str,
    effort: str,
    max_budget_usd: float,
    timeout_seconds: int,
    max_resume_turns: int,
) -> dict[str, Any]:
    used_decisions: set[str] = set()
    turns: list[dict[str, Any]] = []
    payload = run_claude_subject(
        build_subject_prompt(brief),
        cwd=worktree,
        model=model,
        effort=effort,
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
    )
    human_rescue_required = False
    infrastructure_error: str | None = None

    for turn_index in range(max_resume_turns + 1):
        result_text = str(payload.get("result") or "")
        metrics = claude_metrics(payload)
        turns.append({
            "index": turn_index,
            "result": result_text,
            "metrics": metrics,
            "process_returncode": payload.get("_process_returncode"),
            "stderr": payload.get("_stderr", ""),
            "agent_calls": extract_agent_calls(payload),
        })
        infra = claude_infrastructure_failure(payload)
        if infra:
            infrastructure_error = infra
            break
        state = load_state(worktree)
        stage = state.get("stage") if isinstance(state.get("stage"), str) else None
        if terminal_stage(stage):
            break
        if turn_index >= max_resume_turns:
            human_rescue_required = True
            break
        decision = match_scripted_decision(result_text, brief, used_decisions, stage)
        if decision is None:
            human_rescue_required = True
            break
        key, response = decision
        used_decisions.add(key)
        session_id = metrics.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            human_rescue_required = True
            break
        spent = sum_numeric([turn["metrics"] for turn in turns], "total_cost_usd")
        remaining_budget = max_budget_usd - spent
        if remaining_budget <= 0:
            human_rescue_required = True
            break
        payload = run_claude_subject(
            response,
            cwd=worktree,
            model=model,
            effort=effort,
            max_budget_usd=max(0.01, remaining_budget),
            timeout_seconds=timeout_seconds,
            resume_session_id=session_id,
        )

    state = load_state(worktree)
    config_path = worktree / ".agents" / "artifacts" / "pipeline_config.json"
    config = load_json(config_path) if config_path.is_file() else {}
    turn_metrics = [turn["metrics"] for turn in turns]
    return {
        "turns": turns,
        "used_scripted_decisions": sorted(used_decisions),
        "human_rescue_required": human_rescue_required,
        "infrastructure_error": infrastructure_error,
        "final_stage": state.get("stage"),
        "route_depth": (config.get("pipeline") or {}).get("depth") if isinstance(config.get("pipeline"), dict) else None,
        "total_cost_usd": sum_numeric(turn_metrics, "total_cost_usd"),
        "total_input_tokens": int(sum_numeric(turn_metrics, "input_tokens")),
        "total_output_tokens": int(sum_numeric(turn_metrics, "output_tokens")),
        "total_duration_ms": int(sum_numeric(turn_metrics, "duration_ms")),
        "total_api_duration_ms": int(sum_numeric(turn_metrics, "duration_api_ms")),
    }


def qualification(
    *,
    validator: dict[str, Any],
    claim_result: dict[str, Any] | None,
    editorial_result: dict[str, Any] | None,
    subject: dict[str, Any],
    brief: dict[str, Any],
    static_guardrails: dict[str, Any],
    dynamic_guardrails: dict[str, Any],
) -> dict[str, Any]:
    thresholds = thresholds_for(brief)
    reasons: list[str] = []
    hard_guardrail_failures: list[str] = []

    if validator.get("status") != "PUBLISHABLE":
        reasons.append(f"validator status is {validator.get('status')!r}, not PUBLISHABLE")
    if not static_guardrails.get("pass"):
        hard_guardrail_failures.append("adversarial capability isolation guardrail failed")
    if not dynamic_guardrails.get("pass"):
        hard_guardrail_failures.append("adversarial delegation-payload isolation guardrail failed")
    if subject.get("human_rescue_required"):
        reasons.append("undeclared human rescue would be required")

    allowed_depths = brief.get("allowed_depths")
    route_depth = subject.get("route_depth")
    if isinstance(allowed_depths, list) and allowed_depths and route_depth not in allowed_depths:
        reasons.append(f"route depth {route_depth!r} not in allowed depths {allowed_depths!r}")

    if claim_result is None:
        reasons.append("claim/citation grader unavailable")
    else:
        cm = claim_result["metrics"]
        if cm.get("material_claim_precision", 0.0) < thresholds["material_claim_precision_min"]:
            reasons.append(
                f"material claim precision {cm.get('material_claim_precision', 0.0):.3f} < "
                f"{thresholds['material_claim_precision_min']:.3f}"
            )
        if cm.get("citation_support_rate", 0.0) < thresholds["citation_support_rate_min"]:
            reasons.append(
                f"citation support rate {cm.get('citation_support_rate', 0.0):.3f} < "
                f"{thresholds['citation_support_rate_min']:.3f}"
            )
        if cm.get("missing_material_citation_count", 0) > thresholds["max_missing_material_citations"]:
            reasons.append(
                f"missing material citations {cm.get('missing_material_citation_count', 0)} > "
                f"{thresholds['max_missing_material_citations']}"
            )
        if not cm.get("hard_guardrail_pass"):
            hard_guardrail_failures.append("citation integrity or stale/contradicted-current-fact violation")

    if editorial_result is None:
        reasons.append("editorial grader unavailable")
    else:
        em = editorial_result["metrics"]
        if em.get("mean_score", 0.0) < thresholds["editorial_mean_min"]:
            reasons.append(
                f"editorial mean {em.get('mean_score', 0.0):.3f} < {thresholds['editorial_mean_min']:.3f}"
            )
        if em.get("minimum_dimension_score", 0) < thresholds["editorial_dimension_min"]:
            reasons.append(
                f"editorial minimum dimension {em.get('minimum_dimension_score', 0)} < "
                f"{thresholds['editorial_dimension_min']}"
            )
        if not em.get("hard_guardrail_pass"):
            hard_guardrail_failures.append("fatal editorial guardrail failed")

    qualified = not reasons and not hard_guardrail_failures
    return {
        "qualified": qualified,
        "thresholds": thresholds,
        "reasons": reasons,
        "hard_guardrail_failures": hard_guardrail_failures,
    }


def trial_infrastructure_error(record: dict[str, Any]) -> bool:
    if record.get("evaluator_error"):
        return True
    subject = record.get("subject")
    return isinstance(subject, dict) and bool(subject.get("infrastructure_error"))


def aggregate_arm(records: list[dict[str, Any]]) -> dict[str, Any]:
    infrastructure = [record for record in records if trial_infrastructure_error(record)]
    evaluable = [record for record in records if not trial_infrastructure_error(record)]
    qualified = [record for record in evaluable if record.get("qualification", {}).get("qualified")]
    hard_failures = sum(len(record.get("qualification", {}).get("hard_guardrail_failures", [])) for record in evaluable)
    qpr = len(qualified) / len(evaluable) if evaluable else 0.0
    operational_qpr = len(qualified) / len(records) if records else 0.0
    return {
        "trials": len(records),
        "evaluable_trials": len(evaluable),
        "infrastructure_errors": len(infrastructure),
        "qualified_trials": len(qualified),
        "qpr": qpr,
        "operational_qpr": operational_qpr,
        "hard_guardrail_failure_count": hard_failures,
        "total_grader_cost_usd": sum(
            float(record.get("grader_cost_usd", 0.0)) for record in records if isinstance(record.get("grader_cost_usd", 0.0), (int, float))
        ),
        "median_subject_cost_per_qualified_usd": median(
            record["subject"]["total_cost_usd"] for record in qualified if isinstance(record.get("subject"), dict)
        ),
        "median_subject_duration_ms_per_qualified": median(
            record["subject"]["total_duration_ms"] for record in qualified if isinstance(record.get("subject"), dict)
        ),
        "median_subject_input_tokens_per_qualified": median(
            record["subject"]["total_input_tokens"] for record in qualified if isinstance(record.get("subject"), dict)
        ),
        "median_subject_output_tokens_per_qualified": median(
            record["subject"]["total_output_tokens"] for record in qualified if isinstance(record.get("subject"), dict)
        ),
    }


def paired_bootstrap_ci(differences: list[float], *, samples: int = 10000, seed: int = 0) -> tuple[float, float] | None:
    if not differences:
        return None
    rng = random.Random(seed)
    n = len(differences)
    means = []
    for _ in range(samples):
        draw = [differences[rng.randrange(n)] for _ in range(n)]
        means.append(sum(draw) / n)
    means.sort()
    lo = means[max(0, math.floor(0.025 * (samples - 1)))]
    hi = means[min(samples - 1, math.ceil(0.975 * (samples - 1)))]
    return lo, hi


def compare_paired(records: list[dict[str, Any]], *, seed: int) -> dict[str, Any]:
    by_key: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for record in records:
        key = (str(record["brief_id"]), int(record["trial_index"]))
        by_key.setdefault(key, {})[str(record["arm"])] = record
    differences: list[float] = []
    wins = losses = ties = 0
    for pair in by_key.values():
        if "baseline" not in pair or "candidate" not in pair:
            continue
        baseline, candidate = pair["baseline"], pair["candidate"]
        if trial_infrastructure_error(baseline) or trial_infrastructure_error(candidate):
            continue
        b = 1.0 if baseline.get("qualification", {}).get("qualified") else 0.0
        c = 1.0 if candidate.get("qualification", {}).get("qualified") else 0.0
        diff = c - b
        differences.append(diff)
        if diff > 0:
            wins += 1
        elif diff < 0:
            losses += 1
        else:
            ties += 1
    delta = sum(differences) / len(differences) if differences else 0.0
    ci = paired_bootstrap_ci(differences, seed=seed)
    return {
        "paired_evaluable_trials": len(differences),
        "candidate_minus_baseline_qpr": delta,
        "candidate_wins": wins,
        "candidate_losses": losses,
        "ties": ties,
        "paired_bootstrap_95_ci": list(ci) if ci else None,
    }


def recommendation(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    paired: dict[str, Any],
    *,
    minimum_qpr_delta: float,
    noninferiority_margin: float,
    minimum_pairs: int,
) -> dict[str, Any]:
    if candidate["hard_guardrail_failure_count"] > baseline["hard_guardrail_failure_count"]:
        return {"decision": "reject", "reason": "candidate introduced additional hard-guardrail failures"}
    if paired["paired_evaluable_trials"] < minimum_pairs:
        return {"decision": "inconclusive", "reason": "too few paired evaluable trials"}
    delta = paired["candidate_minus_baseline_qpr"]
    ci = paired.get("paired_bootstrap_95_ci")
    if delta < -noninferiority_margin:
        return {"decision": "reject", "reason": "QPR regressed beyond the non-inferiority margin"}
    if delta >= minimum_qpr_delta and isinstance(ci, list) and ci[0] >= -noninferiority_margin:
        return {"decision": "accept", "reason": "QPR met the minimum worthwhile effect without guardrail regression"}
    return {"decision": "inconclusive", "reason": "observed QPR change did not clear the predeclared acceptance rule"}


def run_one(
    *,
    repo: Path,
    ref: str,
    arm: str,
    brief: dict[str, Any],
    trial_index: int,
    temp_parent: Path,
    output_dir: Path,
    subject_model: str,
    subject_effort: str,
    subject_budget: float,
    subject_timeout: int,
    max_resume_turns: int,
    grader_model: str,
    grader_effort: str,
    claim_budget: float,
    editorial_budget: float,
    grader_timeout: int,
    preserve_knowledge: bool,
) -> dict[str, Any]:
    trial_name = f"{brief['id']}-t{trial_index}-{arm}"
    record: dict[str, Any] = {
        "arm": arm,
        "ref": ref,
        "brief_id": brief["id"],
        "trial_index": trial_index,
        "started_at": utc_now(),
    }
    trial_out = output_dir / "trials" / trial_name
    trial_out.mkdir(parents=True, exist_ok=True)

    try:
        with detached_worktree(repo, ref, temp_parent, trial_name) as worktree:
            scrub_subject_worktree(worktree, preserve_knowledge=preserve_knowledge)
            static_guardrails = subject_capability_guardrails(worktree)
            record["static_guardrails"] = static_guardrails
            subject = run_subject_trial(
                worktree,
                brief,
                model=subject_model,
                effort=subject_effort,
                max_budget_usd=subject_budget,
                timeout_seconds=subject_timeout,
                max_resume_turns=max_resume_turns,
            )
            dynamic_guardrails = dynamic_isolation_guardrails(worktree, subject)
            validator = run_validator(worktree)
            copy_trial_artifacts(worktree, trial_out / "artifacts")
            record["subject"] = subject
            record["dynamic_guardrails"] = dynamic_guardrails
            record["validator"] = validator

        article_path = trial_out / "artifacts" / "article_draft.md"
        claim_result = editorial_result = None
        if article_path.is_file():
            article_text = article_path.read_text(encoding="utf-8")
            claim_result = grade_claims(
                article_text,
                brief,
                model=grader_model,
                effort=grader_effort,
                max_budget_usd=claim_budget,
                timeout_seconds=grader_timeout,
                max_claims=int(brief.get("max_claims_to_grade", 30)),
            )
            editorial_result = grade_editorial(
                article_text,
                brief,
                model=grader_model,
                effort=grader_effort,
                max_budget_usd=editorial_budget,
                timeout_seconds=grader_timeout,
            )
        record["claim_citation"] = claim_result
        record["editorial"] = editorial_result
        grader_cost = 0.0
        for result in (claim_result, editorial_result):
            if isinstance(result, dict):
                value = (result.get("grader_metrics") or {}).get("total_cost_usd")
                if isinstance(value, (int, float)):
                    grader_cost += float(value)
        record["grader_cost_usd"] = grader_cost
        record["qualification"] = qualification(
            validator=record["validator"],
            claim_result=claim_result,
            editorial_result=editorial_result,
            subject=record["subject"],
            brief=brief,
            static_guardrails=record["static_guardrails"],
            dynamic_guardrails=record["dynamic_guardrails"],
        )
    except (EvalError, OSError, json.JSONDecodeError) as exc:
        record["evaluator_error"] = str(exc)

    record["finished_at"] = utc_now()
    atomic_write_json(trial_out / "record.json", record)
    return record


def command_version(repo: Path, cmd: list[str]) -> str | None:
    try:
        proc = run_process(cmd, cwd=repo, timeout_seconds=30)
    except EvalError:
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


def sha256_files(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path.name).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def environment_snapshot(repo: Path) -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "claude_code_version": command_version(repo, ["claude", "--version"]),
        "git_version": command_version(repo, ["git", "--version"]),
        "subject_setting_sources": "project",
        "auto_memory_disabled": True,
        "subject_permission_mode": "dontAsk",
        "grader_mode": "bare",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--baseline-ref", default="main")
    parser.add_argument("--candidate-ref", default="HEAD")
    parser.add_argument("--corpus", type=Path, default=Path("evals/article_pipeline/development_corpus.json"))
    parser.add_argument("--brief-id", action="append", dest="brief_ids")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260805)
    parser.add_argument("--subject-model", default="opus")
    parser.add_argument("--subject-effort", default="high")
    parser.add_argument("--subject-max-budget-usd", type=float, default=12.0)
    parser.add_argument("--subject-timeout-seconds", type=int, default=3600)
    parser.add_argument("--max-resume-turns", type=int, default=6)
    parser.add_argument("--grader-model", default="opus")
    parser.add_argument("--grader-effort", default="high")
    parser.add_argument("--claim-grader-max-budget-usd", type=float, default=2.5)
    parser.add_argument("--editorial-grader-max-budget-usd", type=float, default=1.5)
    parser.add_argument("--grader-timeout-seconds", type=int, default=1200)
    parser.add_argument("--preserve-knowledge", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--minimum-qpr-delta", type=float, default=0.05)
    parser.add_argument("--noninferiority-margin", type=float, default=0.02)
    parser.add_argument("--minimum-pairs", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(json.dumps({"status": "EVALUATOR_ERROR", "error": f"not a git repository root: {repo}"}, indent=2))
        return 2
    try:
        baseline_sha = resolve_git_ref(repo, args.baseline_ref)
        candidate_sha = resolve_git_ref(repo, args.candidate_ref)
        briefs = load_corpus(args.corpus if args.corpus.is_absolute() else repo / args.corpus)
        if args.brief_ids:
            wanted = set(args.brief_ids)
            briefs = [brief for brief in briefs if brief["id"] in wanted]
            missing = wanted - {brief["id"] for brief in briefs}
            if missing:
                raise EvalError(f"unknown brief ids: {sorted(missing)}")
        if not briefs:
            raise EvalError("no briefs selected")
        if args.trials < 1:
            raise EvalError("--trials must be >= 1")

        output_dir = args.output_dir
        if output_dir is None:
            output_dir = repo.parent / "article-eval-results" / now_id()
        output_dir = output_dir.resolve()
        ensure_external_output(repo, output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        evaluator_files = [
            repo / "scripts" / "evals" / "common.py",
            repo / "scripts" / "evals" / "claim_citation_grader.py",
            repo / "scripts" / "evals" / "editorial_grader.py",
            repo / "scripts" / "evals" / "qpr_runner.py",
        ]
        corpus_path = args.corpus if args.corpus.is_absolute() else repo / args.corpus
        corpus_files = [corpus_path] if corpus_path.is_file() else sorted(corpus_path.glob("*.json"))
        manifest = {
            "baseline_ref": args.baseline_ref,
            "baseline_sha": baseline_sha,
            "candidate_ref": args.candidate_ref,
            "candidate_sha": candidate_sha,
            "brief_ids": [brief["id"] for brief in briefs],
            "trials_per_brief": args.trials,
            "seed": args.seed,
            "subject_model": args.subject_model,
            "subject_effort": args.subject_effort,
            "subject_max_budget_usd": args.subject_max_budget_usd,
            "grader_model": args.grader_model,
            "grader_effort": args.grader_effort,
            "claim_grader_max_budget_usd": args.claim_grader_max_budget_usd,
            "editorial_grader_max_budget_usd": args.editorial_grader_max_budget_usd,
            "preserve_knowledge": args.preserve_knowledge,
            "minimum_qpr_delta": args.minimum_qpr_delta,
            "noninferiority_margin": args.noninferiority_margin,
            "minimum_pairs": args.minimum_pairs,
            "environment": environment_snapshot(repo),
            "evaluator_sha256": sha256_files([path for path in evaluator_files if path.is_file()]),
            "corpus_sha256": sha256_files(corpus_files),
        }
        atomic_write_json(output_dir / "experiment_manifest.json", manifest)
        if args.dry_run:
            print(json.dumps({"status": "DRY_RUN_OK", "output_dir": str(output_dir), **manifest}, indent=2))
            return 0

        rng = random.Random(args.seed)
        records: list[dict[str, Any]] = []
        with tempfile.TemporaryDirectory(prefix="article-eval-subjects-") as temp_dir:
            temp_parent = Path(temp_dir)
            for brief in briefs:
                for trial_index in range(1, args.trials + 1):
                    arms = [
                        ("baseline", baseline_sha),
                        ("candidate", candidate_sha),
                    ]
                    rng.shuffle(arms)
                    for arm, ref in arms:
                        record = run_one(
                            repo=repo,
                            ref=ref,
                            arm=arm,
                            brief=brief,
                            trial_index=trial_index,
                            temp_parent=temp_parent,
                            output_dir=output_dir,
                            subject_model=args.subject_model,
                            subject_effort=args.subject_effort,
                            subject_budget=args.subject_max_budget_usd,
                            subject_timeout=args.subject_timeout_seconds,
                            max_resume_turns=args.max_resume_turns,
                            grader_model=args.grader_model,
                            grader_effort=args.grader_effort,
                            claim_budget=args.claim_grader_max_budget_usd,
                            editorial_budget=args.editorial_grader_max_budget_usd,
                            grader_timeout=args.grader_timeout_seconds,
                            preserve_knowledge=args.preserve_knowledge,
                        )
                        records.append(record)
                        atomic_write_json(output_dir / "records.json", {"records": records})

        baseline_records = [record for record in records if record["arm"] == "baseline"]
        candidate_records = [record for record in records if record["arm"] == "candidate"]
        baseline_summary = aggregate_arm(baseline_records)
        candidate_summary = aggregate_arm(candidate_records)
        paired = compare_paired(records, seed=args.seed)
        decision = recommendation(
            baseline_summary,
            candidate_summary,
            paired,
            minimum_qpr_delta=args.minimum_qpr_delta,
            noninferiority_margin=args.noninferiority_margin,
            minimum_pairs=args.minimum_pairs,
        )
        report = {
            "manifest": manifest,
            "baseline": baseline_summary,
            "candidate": candidate_summary,
            "paired": paired,
            "recommendation": decision,
            "records_file": str(output_dir / "records.json"),
        }
        atomic_write_json(output_dir / "summary.json", report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (EvalError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "EVALUATOR_ERROR", "error": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
