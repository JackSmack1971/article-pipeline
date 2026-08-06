#!/usr/bin/env python3
"""Evaluate matched article-pipeline trials and compute Qualified Publish Rate (QPR).

The runner keeps evaluator state separate from live article state, binds semantic grades
to exact blinded inputs, rejects malformed/unmatched experiment manifests, and aggregates
paired baseline/candidate outcomes plus optional efficiency telemetry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.article_eval import (
        aggregate_variant,
        citation_structure_report,
        paired_comparison,
        qpr_trial,
        read_json,
        validate_claim_grade,
        validate_editorial_grade,
    )
    from scripts.validate_artifacts import validate
except ModuleNotFoundError:  # direct `python scripts/run_article_eval.py`
    from article_eval import (
        aggregate_variant,
        citation_structure_report,
        paired_comparison,
        qpr_trial,
        read_json,
        validate_claim_grade,
        validate_editorial_grade,
    )
    from validate_artifacts import validate


DEFAULT_RUN_ROOT = Path(".workflow/article-evals")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
RUN_METRIC_NAMES = {
    "cost_usd",
    "wall_time_seconds",
    "input_tokens",
    "output_tokens",
    "tool_calls",
    "agent_calls",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parent.parent


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def require_safe_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{label} must match {SAFE_ID_RE.pattern}")
    return value


def load_corpus(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("corpus must be a JSON array")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each corpus item must be an object")
        item_id = require_safe_id(item.get("id"), "corpus id")
        for key in ("topic_prompt", "target_audience", "expected_depth", "gate_script"):
            if key not in item:
                raise ValueError(f"corpus item {item_id!r} missing {key}")
        if item_id in result:
            raise ValueError(f"duplicate corpus id: {item_id}")
        result[item_id] = item
    return result


def blind_article(markdown: str) -> str:
    """Remove evaluator identity comments without rewriting article prose."""
    lines = [
        line
        for line in markdown.splitlines()
        if not re.match(r"^\s*<!--\s*EVAL-", line, flags=re.IGNORECASE)
    ]
    return "\n".join(lines).strip() + "\n"


def trial_input_sha256(
    *,
    brief: dict[str, Any],
    article: str,
    citation_structure: dict[str, Any],
    decision_context: dict[str, Any] | None,
) -> str:
    payload = {
        "brief": brief,
        "article": article,
        "citation_structure": citation_structure,
        "decision_context": decision_context,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def render_prompt(
    template: str,
    *,
    brief: dict[str, Any],
    article: str,
    input_sha256: str,
    extra: str = "",
    decision_context: dict[str, Any] | None = None,
) -> str:
    return (
        template.replace("{{BRIEF_JSON}}", json.dumps(brief, indent=2, sort_keys=True))
        .replace("{{ARTICLE_MARKDOWN}}", article)
        .replace("{{EXTRA_CONTEXT}}", extra)
        .replace("{{DECISION_CONTEXT}}", json.dumps(decision_context, indent=2, sort_keys=True))
        .replace("{{INPUT_SHA256}}", input_sha256)
    )


def run_grader(command: str, prompt: str, timeout: int) -> dict[str, Any]:
    proc = subprocess.run(
        shlex.split(command),
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"grader failed ({proc.returncode}): {proc.stderr.strip()}")
    output = proc.stdout.strip()
    try:
        value = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"grader did not return pure JSON: {output[:500]!r}") from exc
    if not isinstance(value, dict):
        raise ValueError("grader output must be a JSON object")
    return value


def validate_run_metrics(value: object) -> dict[str, float | int]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("run_metrics must be an object")
    unknown = set(value) - RUN_METRIC_NAMES
    if unknown:
        raise ValueError(f"run_metrics contains unknown fields: {sorted(unknown)}")
    result: dict[str, float | int] = {}
    for key, raw in value.items():
        if not isinstance(raw, (int, float)) or isinstance(raw, bool) or raw < 0:
            raise ValueError(f"run_metrics.{key} must be a non-negative number")
        result[key] = raw
    return result


def trial_key(trial: dict[str, Any]) -> str:
    variant = require_safe_id(trial.get("variant"), "variant")
    brief_id = require_safe_id(trial.get("brief_id"), "brief_id")
    number = trial.get("trial", 1)
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise ValueError("trial must be a positive integer")
    return f"{variant}__{brief_id}__{number}"


def validate_decision_context(value: object, key: str) -> dict[str, Any] | None:
    """Decision context must come from the experiment, not subject self-assessment artifacts."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{key}: decision_context must be an object or null")
    return value


def read_actual_depth(artifact_root: Path) -> str | None:
    path = artifact_root / "pipeline_config.json"
    if not path.is_file():
        return None
    config = read_json(path)
    pipeline = config.get("pipeline")
    return pipeline.get("depth") if isinstance(pipeline, dict) and isinstance(pipeline.get("depth"), str) else None


def validate_matched_manifest(trials: list[dict[str, Any]]) -> None:
    """All variants in a comparison must cover exactly the same brief/trial identities."""
    by_variant: dict[str, set[tuple[str, int]]] = {}
    seen_keys: set[str] = set()
    for trial in trials:
        key = trial_key(trial)
        if key in seen_keys:
            raise ValueError(f"duplicate trial key: {key}")
        seen_keys.add(key)
        variant = str(trial["variant"])
        pair = (str(trial["brief_id"]), int(trial.get("trial", 1)))
        by_variant.setdefault(variant, set()).add(pair)
    if len(by_variant) <= 1:
        return
    expected = next(iter(by_variant.values()))
    mismatches = {variant: sorted(pairs) for variant, pairs in by_variant.items() if pairs != expected}
    if mismatches:
        raise ValueError(f"experiment variants are not matched on brief/trial identities: {mismatches}")

    by_pair: dict[tuple[str, int], list[str]] = {}
    for trial in trials:
        pair = (str(trial["brief_id"]), int(trial.get("trial", 1)))
        context = trial.get("decision_context")
        encoded = json.dumps(context, sort_keys=True, separators=(",", ":"))
        by_pair.setdefault(pair, []).append(encoded)
    divergent = [pair for pair, contexts in by_pair.items() if len(set(contexts)) > 1]
    if divergent:
        raise ValueError(f"decision_context differs across matched variants: {sorted(divergent)}")


def invalidate_stale_outputs(trial_dir: Path) -> None:
    for name in ("claim_grade.json", "editorial_grade.json", "score.json"):
        path = trial_dir / name
        if path.exists():
            path.unlink()


def prepare_or_grade(
    manifest_path: Path,
    *,
    corpus_path: Path,
    run_root: Path,
    claim_template_path: Path,
    editorial_template_path: Path,
    claim_grader_command: str | None,
    editorial_grader_command: str | None,
    grader_timeout: int,
) -> Path:
    manifest = read_json(manifest_path)
    trials = manifest.get("trials")
    if not isinstance(trials, list) or not trials:
        raise ValueError("manifest requires non-empty trials list")
    if not all(isinstance(trial, dict) for trial in trials):
        raise ValueError("trial entries must be objects")
    validate_matched_manifest(trials)

    experiment_id = require_safe_id(manifest.get("experiment_id"), "experiment_id")
    corpus = load_corpus(corpus_path)
    claim_template = claim_template_path.read_text(encoding="utf-8")
    editorial_template = editorial_template_path.read_text(encoding="utf-8")

    live_artifact_root = (repository_root() / ".agents" / "artifacts").resolve()
    resolved_run_root = run_root.resolve()
    if is_within(resolved_run_root, live_artifact_root):
        raise ValueError("evaluation run root must not be inside live .agents/artifacts")
    out = resolved_run_root / experiment_id
    out.mkdir(parents=True, exist_ok=True)

    prepared: list[dict[str, Any]] = []
    for trial in trials:
        brief_id = require_safe_id(trial.get("brief_id"), "brief_id")
        variant = require_safe_id(trial.get("variant"), "variant")
        if brief_id not in corpus:
            raise ValueError(f"unknown brief_id: {brief_id!r}")
        key = trial_key(trial)

        human_rescue = trial.get("human_rescue", False)
        if not isinstance(human_rescue, bool):
            raise ValueError(f"{key}: human_rescue must be boolean")
        run_metrics = validate_run_metrics(trial.get("run_metrics"))
        decision_context = validate_decision_context(trial.get("decision_context"), key)

        artifact_value = trial.get("artifact_root")
        if not isinstance(artifact_value, str) or not artifact_value.strip():
            raise ValueError(f"{key}: artifact_root must be a non-empty path string")
        artifact_root = Path(artifact_value).expanduser().resolve()
        if not artifact_root.is_dir():
            raise ValueError(f"artifact_root does not exist: {artifact_root}")
        if is_within(artifact_root, live_artifact_root):
            raise ValueError("evaluation trials must not point at or inside live .agents/artifacts")
        article_path = artifact_root / "article_draft.md"
        if not article_path.is_file():
            raise ValueError(f"missing article_draft.md: {artifact_root}")

        report, _ = validate(artifact_root)
        article = blind_article(article_path.read_text(encoding="utf-8"))
        structure = citation_structure_report(article)
        input_sha256 = trial_input_sha256(
            brief=corpus[brief_id],
            article=article,
            citation_structure=structure,
            decision_context=decision_context,
        )

        trial_dir = out / key
        trial_dir.mkdir(parents=True, exist_ok=True)
        invalidate_stale_outputs(trial_dir)
        (trial_dir / "article.blind.md").write_text(article, encoding="utf-8")
        (trial_dir / "deterministic.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (trial_dir / "citation_structure.json").write_text(
            json.dumps(structure, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (trial_dir / "decision_context.json").write_text(
            json.dumps(decision_context, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        extra = json.dumps({"citation_structure": structure}, indent=2, sort_keys=True)
        claim_prompt = render_prompt(
            claim_template,
            brief=corpus[brief_id],
            article=article,
            input_sha256=input_sha256,
            extra=extra,
            decision_context=decision_context,
        )
        editorial_prompt = render_prompt(
            editorial_template,
            brief=corpus[brief_id],
            article=article,
            input_sha256=input_sha256,
            decision_context=None,
        )
        (trial_dir / "claim_grader_prompt.md").write_text(claim_prompt, encoding="utf-8")
        (trial_dir / "editorial_grader_prompt.md").write_text(editorial_prompt, encoding="utf-8")

        citation_urls = {
            item["url"]
            for item in structure.get("citations", [])
            if isinstance(item, dict) and isinstance(item.get("url"), str)
        }
        claim_grade_path = trial_dir / "claim_grade.json"
        editorial_grade_path = trial_dir / "editorial_grade.json"
        if claim_grader_command:
            value = run_grader(claim_grader_command, claim_prompt, grader_timeout)
            validate_claim_grade(
                value,
                expected_input_sha256=input_sha256,
                article_citation_urls=citation_urls,
            )
            claim_grade_path.write_text(
                json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        if editorial_grader_command:
            value = run_grader(editorial_grader_command, editorial_prompt, grader_timeout)
            validate_editorial_grade(value, expected_input_sha256=input_sha256)
            editorial_grade_path.write_text(
                json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        actual_depth = read_actual_depth(artifact_root)
        prepared.append(
            {
                "key": key,
                "variant": variant,
                "brief_id": brief_id,
                "trial": trial.get("trial", 1),
                "artifact_root": str(artifact_root),
                "human_rescue": human_rescue,
                "deterministic_publishable": report.get("status") == "PUBLISHABLE",
                "input_sha256": input_sha256,
                "expected_depth": corpus[brief_id].get("expected_depth"),
                "actual_depth": actual_depth,
                "route_match": actual_depth == corpus[brief_id].get("expected_depth"),
                "run_metrics": run_metrics,
                "trial_dir": str(trial_dir),
            }
        )

    prepared_path = out / "prepared_trials.json"
    prepared_path.write_text(
        json.dumps({"experiment_id": experiment_id, "trials": prepared}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return prepared_path


def _number_threshold(
    thresholds: dict[str, Any],
    key: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    raw = thresholds.get(key, default)
    if not isinstance(raw, (int, float)) or isinstance(raw, bool):
        raise ValueError(f"threshold {key} must be numeric")
    value = float(raw)
    if not minimum <= value <= maximum:
        raise ValueError(f"threshold {key} must be in [{minimum}, {maximum}]")
    return value


def _integer_threshold(thresholds: dict[str, Any], key: str, default: int) -> int:
    raw = thresholds.get(key, default)
    if not isinstance(raw, int) or isinstance(raw, bool) or raw < 0:
        raise ValueError(f"threshold {key} must be a non-negative integer")
    return raw


def score(prepared_path: Path, *, thresholds_path: Path | None = None) -> dict[str, Any]:
    prepared = read_json(prepared_path)
    prepared_trials = prepared.get("trials")
    if not isinstance(prepared_trials, list) or not prepared_trials:
        raise ValueError("prepared trial file requires non-empty trials list")

    thresholds: dict[str, Any] = read_json(thresholds_path) if thresholds_path else {}
    editorial_threshold = _number_threshold(thresholds, "editorial_mean", 4.0, 1.0, 5.0)
    minimum_editorial_dimension = _number_threshold(
        thresholds, "minimum_editorial_dimension", 3.0, 1.0, 5.0
    )
    maximum_material_unsupported = _integer_threshold(
        thresholds, "maximum_material_unsupported", 0
    )
    maximum_material_uncited = _integer_threshold(thresholds, "maximum_material_uncited", 0)
    minimum_material_claims = _integer_threshold(thresholds, "minimum_material_claims", 1)
    minimum_material_claim_precision = _number_threshold(
        thresholds, "minimum_material_claim_precision", 0.9, 0.0, 1.0
    )

    scored: list[dict[str, Any]] = []
    for trial in prepared_trials:
        if not isinstance(trial, dict):
            raise ValueError("prepared trials must be objects")
        trial_dir = Path(str(trial["trial_dir"]))
        claim_path = trial_dir / "claim_grade.json"
        editorial_path = trial_dir / "editorial_grade.json"
        structure_path = trial_dir / "citation_structure.json"
        if not claim_path.is_file() or not editorial_path.is_file():
            raise ValueError(f"missing grader output for {trial['key']}; run graders or populate JSON files")
        if not structure_path.is_file():
            raise ValueError(f"missing citation structure for {trial['key']}")

        result = qpr_trial(
            deterministic_publishable=bool(trial["deterministic_publishable"]),
            claim_grade=read_json(claim_path),
            editorial_grade=read_json(editorial_path),
            human_rescue=bool(trial.get("human_rescue", False)),
            input_sha256=str(trial["input_sha256"]),
            citation_structure=read_json(structure_path),
            editorial_threshold=editorial_threshold,
            minimum_editorial_dimension=minimum_editorial_dimension,
            maximum_material_unsupported=maximum_material_unsupported,
            maximum_material_uncited=maximum_material_uncited,
            minimum_material_claims=minimum_material_claims,
            minimum_material_claim_precision=minimum_material_claim_precision,
        )
        result.update(
            {
                key: trial[key]
                for key in (
                    "key",
                    "variant",
                    "brief_id",
                    "trial",
                    "expected_depth",
                    "actual_depth",
                    "route_match",
                    "run_metrics",
                )
            }
        )
        scored.append(result)
        (trial_dir / "score.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    by_variant: dict[str, list[dict[str, Any]]] = {}
    for trial in scored:
        by_variant.setdefault(trial["variant"], []).append(trial)
    variants = {name: aggregate_variant(items) for name, items in sorted(by_variant.items())}

    comparison = None
    names = sorted(variants)
    if len(names) == 2:
        baseline_name = "baseline" if "baseline" in variants else names[0]
        candidate_name = "candidate" if "candidate" in variants else names[1]
        comparison = {
            "baseline": baseline_name,
            "candidate": candidate_name,
            **paired_comparison(by_variant[baseline_name], by_variant[candidate_name]),
        }

    summary = {
        "experiment_id": prepared.get("experiment_id"),
        "thresholds": {
            "editorial_mean": editorial_threshold,
            "minimum_editorial_dimension": minimum_editorial_dimension,
            "maximum_material_unsupported": maximum_material_unsupported,
            "maximum_material_uncited": maximum_material_uncited,
            "minimum_material_claims": minimum_material_claims,
            "minimum_material_claim_precision": minimum_material_claim_precision,
        },
        "variants": variants,
        "comparison": comparison,
        "trials": scored,
    }
    summary_path = prepared_path.parent / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="validate trial bundles and prepare/run blind graders")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument("--corpus", type=Path, default=Path("evals/corpus/article_briefs.json"))
    prepare.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    prepare.add_argument("--claim-prompt", type=Path, default=Path("evals/prompts/claim_grader.md"))
    prepare.add_argument(
        "--editorial-prompt", type=Path, default=Path("evals/prompts/editorial_grader.md")
    )
    prepare.add_argument("--claim-grader-command")
    prepare.add_argument("--editorial-grader-command")
    prepare.add_argument("--grader-timeout", type=int, default=900)

    score_parser = sub.add_parser("score", help="validate grader JSON and compute QPR")
    score_parser.add_argument("--prepared", type=Path, required=True)
    score_parser.add_argument("--thresholds", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_or_grade(
                args.manifest,
                corpus_path=args.corpus,
                run_root=args.run_root,
                claim_template_path=args.claim_prompt,
                editorial_template_path=args.editorial_prompt,
                claim_grader_command=args.claim_grader_command,
                editorial_grader_command=args.editorial_grader_command,
                grader_timeout=args.grader_timeout,
            )
            print(result)
        else:
            print(json.dumps(score(args.prepared, thresholds_path=args.thresholds), indent=2, sort_keys=True))
    except (
        OSError,
        ValueError,
        RuntimeError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as exc:
        print(f"EVAL_ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
