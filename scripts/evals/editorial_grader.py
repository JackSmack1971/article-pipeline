#!/usr/bin/env python3
"""Blind editorial and target-audience grader for article-pipeline outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.evals.common import EvalError, atomic_write_json, load_json, run_claude_grader
except ModuleNotFoundError:  # direct invocation
    from common import EvalError, atomic_write_json, load_json, run_claude_grader


DIMENSIONS = (
    "thesis_coherence",
    "logical_continuity",
    "evidence_integration",
    "calibrated_nuance",
    "audience_fit",
    "clarity",
    "usefulness",
    "structure_and_flow",
)

EDITORIAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "dimensions": {
            "type": "object",
            "properties": {
                name: {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "rationale": {"type": "string"},
                    },
                    "required": ["score", "rationale"],
                    "additionalProperties": False,
                }
                for name in DIMENSIONS
            },
            "required": list(DIMENSIONS),
            "additionalProperties": False,
        },
        "fatal_editorial_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "thesis_drift",
                            "material_internal_contradiction",
                            "misleading_framing",
                            "audience_mismatch",
                            "incomprehensible_core_argument",
                            "unsupported_actionable_recommendation",
                            "other",
                        ],
                    },
                    "detail": {"type": "string"},
                },
                "required": ["category", "detail"],
                "additionalProperties": False,
            },
        },
        "top_strengths": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "top_weaknesses": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "publication_recommendation": {
            "type": "string",
            "enum": ["publish", "publish_with_minor_edits", "substantive_revision", "do_not_publish"],
        },
        "grader_confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": [
        "dimensions",
        "fatal_editorial_issues",
        "top_strengths",
        "top_weaknesses",
        "publication_recommendation",
        "grader_confidence",
    ],
    "additionalProperties": False,
}


def compute_editorial_metrics(grade: dict[str, Any]) -> dict[str, Any]:
    dimensions = grade.get("dimensions") if isinstance(grade.get("dimensions"), dict) else {}
    scores = {
        name: int(dimensions[name]["score"])
        for name in DIMENSIONS
        if isinstance(dimensions.get(name), dict) and isinstance(dimensions[name].get("score"), int)
    }
    mean = sum(scores.values()) / len(scores) if scores else 0.0
    minimum = min(scores.values()) if scores else 0
    fatal = grade.get("fatal_editorial_issues") if isinstance(grade.get("fatal_editorial_issues"), list) else []
    recommendation = grade.get("publication_recommendation")
    return {
        "dimension_scores": scores,
        "mean_score": mean,
        "minimum_dimension_score": minimum,
        "fatal_issue_count": len(fatal),
        "publication_recommendation": recommendation,
        "hard_guardrail_pass": len(fatal) == 0 and recommendation != "do_not_publish",
    }


def build_instructions(brief: dict[str, Any]) -> str:
    topic = brief.get("topic_brief", "")
    audience = brief.get("target_audience", "general informed readers")
    intended_thesis = brief.get("intended_thesis", "The article should develop a defensible thesis from the research rather than mechanically preserve a predetermined answer.")
    return f"""You are a blind senior editor grading a finished article. You are independent from the system that produced it. You do not know whether this article came from the baseline or candidate control plane, and you must not infer or speculate about that.

Topic brief:
{topic}

Target audience:
{audience}

Intended thesis / editorial direction:
{intended_thesis}

The article text is provided on stdin.

Score each dimension from 1 to 5 using this anchor:
1 = seriously deficient; 2 = substantial problems; 3 = competent but clearly improvable; 4 = strong publication-quality work; 5 = exceptional and difficult to improve materially.

Dimensions:
- thesis_coherence: the article has a clear, defensible through-line and conclusion.
- logical_continuity: claims and sections follow from one another without hidden leaps.
- evidence_integration: evidence is interpreted and connected to the argument rather than dumped or cherry-picked. Do NOT independently fact-check URLs; a separate grader does that.
- calibrated_nuance: uncertainty, counterevidence, limits, and contested points are represented proportionately without false balance.
- audience_fit: explanation depth, jargon, assumed knowledge, and examples suit the declared audience.
- clarity: sentences and paragraphs are readable, specific, and not needlessly opaque.
- usefulness: a reader leaves with a materially better understanding, framework, or decision basis.
- structure_and_flow: headings, ordering, transitions, and pacing support comprehension.

Fatal issues are reserved for problems that should block publication even if average prose quality is high: material thesis drift, internal contradiction, misleading framing, severe audience mismatch, an incomprehensible core argument, or actionable recommendations that the article itself does not support.

Do not grade SEO packaging, hidden artifacts, process compliance, or whether the author used a particular workflow. Grade only the final article against the brief and audience. Return only the requested structured result."""


def grade_article(
    article_text: str,
    brief: dict[str, Any],
    *,
    model: str,
    effort: str,
    max_budget_usd: float,
    timeout_seconds: int,
) -> dict[str, Any]:
    raw = run_claude_grader(
        build_instructions(brief),
        article_text,
        EDITORIAL_SCHEMA,
        model=model,
        effort=effort,
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
        allow_web=False,
    )
    grade = raw["structured_output"]
    return {
        "grade": grade,
        "metrics": compute_editorial_metrics(grade),
        "grader_metrics": raw["metrics"],
        "process_returncode": raw["process_returncode"],
        "stderr": raw["stderr"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default="opus")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--max-budget-usd", type=float, default=1.5)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    try:
        result = grade_article(
            args.article.read_text(encoding="utf-8"),
            load_json(args.brief),
            model=args.model,
            effort=args.effort,
            max_budget_usd=args.max_budget_usd,
            timeout_seconds=args.timeout_seconds,
        )
    except (OSError, EvalError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "EVALUATOR_ERROR", "error": str(exc)}, indent=2))
        return 2

    if args.output:
        atomic_write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
