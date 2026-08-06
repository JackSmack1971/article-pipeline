#!/usr/bin/env python3
"""Evaluate matched article-pipeline trials and compute Qualified Publish Rate (QPR).

The runner does not let the production pipeline grade itself. It runs the repository's
artifact validator, prepares blind grader prompts, optionally invokes independent grader
commands, validates their JSON contracts, and aggregates per-variant QPR.

Trial artifacts must live outside the repository's live `.agents/artifacts/` directory.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.article_eval import aggregate_variant, citation_structure_report, qpr_trial, read_json
    from scripts.validate_artifacts import validate
except ModuleNotFoundError:  # direct `python scripts/run_article_eval.py`
    from article_eval import aggregate_variant, citation_structure_report, qpr_trial, read_json
    from validate_artifacts import validate


DEFAULT_RUN_ROOT = Path(".workflow/article-evals")


def load_corpus(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("corpus must be a JSON array")
    result: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("each corpus item requires string id")
        if item["id"] in result:
            raise ValueError(f"duplicate corpus id: {item['id']}")
        result[item["id"]] = item
    return result


def blind_article(markdown: str) -> str:
    """Remove obvious experiment identity comments without altering article prose."""
    lines = [line for line in markdown.splitlines() if not line.startswith("<!-- EVAL-")]
    return "\n".join(lines).strip() + "\n"


def render_prompt(template: str, *, brief: dict[str, Any], article: str, extra: str = "") -> str:
    return template.replace("{{BRIEF_JSON}}", json.dumps(brief, indent=2, sort_keys=True)).replace(
        "{{ARTICLE_MARKDOWN}}", article
    ).replace("{{EXTRA_CONTEXT}}", extra)


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


def trial_key(trial: dict[str, Any]) -> str:
    return f"{trial['variant']}__{trial['brief_id']}__{trial.get('trial', 1)}"


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
    experiment_id = manifest.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        raise ValueError("manifest requires experiment_id")
    corpus = load_corpus(corpus_path)
    claim_template = claim_template_path.read_text(encoding="utf-8")
    editorial_template = editorial_template_path.read_text(encoding="utf-8")
    out = run_root / experiment_id
    out.mkdir(parents=True, exist_ok=True)

    prepared: list[dict[str, Any]] = []
    for trial in trials:
        if not isinstance(trial, dict):
            raise ValueError("trial entries must be objects")
        brief_id = trial.get("brief_id")
        variant = trial.get("variant")
        if brief_id not in corpus:
            raise ValueError(f"unknown brief_id: {brief_id!r}")
        if not isinstance(variant, str) or not variant:
            raise ValueError("trial requires variant")
        artifact_root = Path(str(trial.get("artifact_root", ""))).resolve()
        if not artifact_root.is_dir():
            raise ValueError(f"artifact_root does not exist: {artifact_root}")
        if artifact_root.name == "artifacts" and artifact_root.parent.name == ".agents":
            raise ValueError("evaluation trials must not point at live .agents/artifacts")
        article_path = artifact_root / "article_draft.md"
        if not article_path.is_file():
            raise ValueError(f"missing article_draft.md: {artifact_root}")

        report, _ = validate(artifact_root)
        article = blind_article(article_path.read_text(encoding="utf-8"))
        structure = citation_structure_report(article)
        key = trial_key(trial)
        trial_dir = out / key
        trial_dir.mkdir(parents=True, exist_ok=True)
        (trial_dir / "article.blind.md").write_text(article, encoding="utf-8")
        (trial_dir / "deterministic.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (trial_dir / "citation_structure.json").write_text(json.dumps(structure, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        extra = json.dumps({"citation_structure": structure}, indent=2, sort_keys=True)
        claim_prompt = render_prompt(claim_template, brief=corpus[brief_id], article=article, extra=extra)
        editorial_prompt = render_prompt(editorial_template, brief=corpus[brief_id], article=article)
        (trial_dir / "claim_grader_prompt.md").write_text(claim_prompt, encoding="utf-8")
        (trial_dir / "editorial_grader_prompt.md").write_text(editorial_prompt, encoding="utf-8")

        claim_grade_path = trial_dir / "claim_grade.json"
        editorial_grade_path = trial_dir / "editorial_grade.json"
        if claim_grader_command:
            value = run_grader(claim_grader_command, claim_prompt, grader_timeout)
            claim_grade_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if editorial_grader_command:
            value = run_grader(editorial_grader_command, editorial_prompt, grader_timeout)
            editorial_grade_path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        prepared.append({
            "key": key,
            "variant": variant,
            "brief_id": brief_id,
            "trial": trial.get("trial", 1),
            "artifact_root": str(artifact_root),
            "human_rescue": bool(trial.get("human_rescue", False)),
            "deterministic_publishable": report.get("status") == "PUBLISHABLE",
            "trial_dir": str(trial_dir),
        })

    prepared_path = out / "prepared_trials.json"
    prepared_path.write_text(json.dumps({"experiment_id": experiment_id, "trials": prepared}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return prepared_path


def score(prepared_path: Path, *, thresholds_path: Path | None = None) -> dict[str, Any]:
    prepared = read_json(prepared_path)
    thresholds: dict[str, Any] = {}
    if thresholds_path:
        thresholds = read_json(thresholds_path)
    editorial_threshold = float(thresholds.get("editorial_mean", 4.0))
    minimum_editorial_dimension = float(thresholds.get("minimum_editorial_dimension", 3.0))
    maximum_material_unsupported = int(thresholds.get("maximum_material_unsupported", 0))
    minimum_material_claim_precision = float(thresholds.get("minimum_material_claim_precision", 0.9))

    scored: list[dict[str, Any]] = []
    for trial in prepared.get("trials", []):
        trial_dir = Path(trial["trial_dir"])
        claim_path = trial_dir / "claim_grade.json"
        editorial_path = trial_dir / "editorial_grade.json"
        if not claim_path.is_file() or not editorial_path.is_file():
            raise ValueError(f"missing grader output for {trial['key']}; run graders or populate JSON files")
        result = qpr_trial(
            deterministic_publishable=bool(trial["deterministic_publishable"]),
            claim_grade=read_json(claim_path),
            editorial_grade=read_json(editorial_path),
            human_rescue=bool(trial.get("human_rescue", False)),
            editorial_threshold=editorial_threshold,
            minimum_editorial_dimension=minimum_editorial_dimension,
            maximum_material_unsupported=maximum_material_unsupported,
            minimum_material_claim_precision=minimum_material_claim_precision,
        )
        result.update({key: trial[key] for key in ("key", "variant", "brief_id", "trial")})
        scored.append(result)
        (trial_dir / "score.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    by_variant: dict[str, list[dict[str, Any]]] = {}
    for trial in scored:
        by_variant.setdefault(trial["variant"], []).append(trial)
    variants = {name: aggregate_variant(items) for name, items in sorted(by_variant.items())}
    names = sorted(variants)
    comparison = None
    if len(names) == 2:
        baseline_name = "baseline" if "baseline" in variants else names[0]
        candidate_name = "candidate" if "candidate" in variants else names[1]
        comparison = {
            "baseline": baseline_name,
            "candidate": candidate_name,
            "qpr_absolute_delta": variants[candidate_name]["qpr"] - variants[baseline_name]["qpr"],
        }
    summary = {"experiment_id": prepared.get("experiment_id"), "thresholds": {
        "editorial_mean": editorial_threshold,
        "minimum_editorial_dimension": minimum_editorial_dimension,
        "maximum_material_unsupported": maximum_material_unsupported,
        "minimum_material_claim_precision": minimum_material_claim_precision,
    }, "variants": variants, "comparison": comparison, "trials": scored}
    summary_path = prepared_path.parent / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="validate trial bundles and prepare/run blind graders")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument("--corpus", type=Path, default=Path("evals/corpus/article_briefs.json"))
    prepare.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    prepare.add_argument("--claim-prompt", type=Path, default=Path("evals/prompts/claim_grader.md"))
    prepare.add_argument("--editorial-prompt", type=Path, default=Path("evals/prompts/editorial_grader.md"))
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
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"EVAL_ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
