#!/usr/bin/env python3
"""Greatness Evaluator v0 (G-001): Great Article Standard v1 excellence scoring.

Scope and relationship to existing evaluators
----------------------------------------------
This evaluator is eval-only and operationally independent. It does NOT replace or weaken
`scripts/validate_artifacts.py`, `claim_citation_grader.py`, `editorial_grader.py`, or
`qpr_runner.py`'s Qualified Publish Rate (QPR) logic. It sits strictly ABOVE that layer:

    QPR / epistemic eligibility (existing, unchanged)
              |
              v
    Greatness Evaluator v0 (this module) -- Excellence Vector scoring, provisional
              |                              thresholds/classification

The caller must supply the epistemic/QPR eligibility decision (e.g. a `qpr_runner.py` trial
record's `qualification.qualified`); this module never re-derives or overrides it. Per Great
Article Standard v1 §2.1, a blocking epistemic failure stops greatness evaluation entirely --
`evaluate()` returns `classification: "EPISTEMICALLY_INELIGIBLE"` without scoring any dimension.

Dimensions and what is NOT evaluated in v0
-------------------------------------------
This module scores exactly the nine Excellence Vector dimensions the Great Article Standard
defines apart from Information Gain: RQ, CQ, SI, IH, RT, AF, HR, SF, PU (Standard §2.2).

IG (Information Gain) is explicitly NOT_EVALUATED. No proxy is substituted -- there is no
competitor corpus or Atomic Information Unit machinery in this repository yet (Standard §5/§7;
`docs/GREATNESS-GAP-ANALYSIS.md` §5/§7/§9 Layer 7). Because the Standard requires demonstrated
information gain for both GREAT (§2.4: "material competitive information gain demonstrated")
and EXCEPTIONAL (§2.4: "demonstrated competitive information advantage"), this evaluator caps
classification at STRONG in v0 even when every other threshold is met -- see `classify()`.

Ownership split (per repository CLAUDE.md policy model)
---------------------------------------------------------
- Semantic grader (one blind `--bare` Claude Code call, no tools, no filesystem, no baseline/
  candidate identity, no internal QA/fact-check conclusions, no token spend, no production
  self-score): judges each atomic criterion's pass/fail and writes a rationale.
- Deterministic code (this file): owns the schema, the criteria rubric text, dimension-score
  aggregation, archetype weighting math, the IH floor, thresholds, and classification.

Thresholds and the PUBLISHABLE/STRONG/GREAT/EXCEPTIONAL labels are provisional calibration
hypotheses per Great Article Standard v1 §2.3/§2.4, not empirical truths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.evals.common import EvalError, atomic_write_json, load_json, run_claude_grader
except ModuleNotFoundError:  # direct invocation
    from common import EvalError, atomic_write_json, load_json, run_claude_grader


EVALUATOR_VERSION = "greatness-evaluator-v0"
RUBRIC_VERSION = "great-article-standard-v1"

# Great Article Standard v1 §2.2 Excellence Vector, minus IG (handled separately below).
# All nine are graded and floor-checked; see WEIGHTED_DIMENSIONS for the composite subset.
EXCELLENCE_DIMENSIONS = ("RQ", "CQ", "SI", "IH", "RT", "AF", "HR", "SF", "PU")

# The Standard's §3 archetype weighting table has no IH column at all: IH is a universal
# minimum floor "outside compensatory weighting" (§2.2), not an archetype-weighted
# contributor. The weighted Excellence Index therefore excludes IH as well as IG; IH is
# still graded and still gates classification via the floor checks in classify().
WEIGHTED_DIMENSIONS = tuple(dim for dim in EXCELLENCE_DIMENSIONS if dim != "IH")

DIMENSION_LABELS: dict[str, str] = {
    "RQ": "Research Quality",
    "CQ": "Coverage Quality",
    "SI": "Synthesis & Insight",
    "IH": "Intellectual Honesty",
    "RT": "Reader Transformation",
    "AF": "Audience Fit",
    "HR": "Human Resonance",
    "SF": "Structure & Flow",
    "PU": "Practical Utility",
}

# Atomic, decomposed criteria per dimension (Standard §2.2 definitions + §9 Layer 4 examples).
# CheckEval-style decomposed binary questions rather than one vague score.
DIMENSION_CRITERIA: dict[str, dict[str, str]] = {
    "RQ": {
        "evidence_authority": "Are the article's claims grounded predominantly in primary, authoritative, or otherwise high-quality sources rather than low-quality secondary aggregation?",
        "methodological_transparency": "Does the article convey relevant methodological context (study design, sample, dataset, or comparable rigor signal) for its empirical claims rather than citing bare conclusions?",
        "triangulation": "Are important claims corroborated by more than one independent source where independent corroboration is plausibly available, rather than resting a broad claim on a single source?",
        "source_diversity_not_redundant": "Does the source set reflect genuinely independent evidence rather than many outlets repeating one underlying press release or study?",
    },
    "CQ": {
        "core_questions_answered": "Does the article answer the core questions a reader of this brief would need answered to consider the topic adequately covered?",
        "no_glaring_omission": "Is there no glaring omission of a sub-topic the brief clearly implies a reader would expect?",
        "background_sufficient": "Is enough background/context given for the declared audience to follow the core argument without an external lookup?",
        "decision_relevant_info_present": "Where the brief implies a decision, comparison, or evaluation, does the article supply the information needed to make it?",
    },
    "SI": {
        "goes_beyond_summary": "Does the article perform synthesis (explanatory models, distinctions, implications) rather than merely restate or summarize its sources?",
        "meaningful_framework_or_distinction": "Does at least one section introduce a genuinely useful framework, distinction, or implication that is not trivially obvious from a single source?",
        "conclusions_follow_from_evidence": "Do the article's stated conclusions and implications actually follow from the evidence presented, rather than overreaching it?",
        "insight_per_section": "Does each major section contribute a distinct insight rather than restating the introduction in different words?",
    },
    "IH": {
        "uncertainty_proportional": "Is uncertainty language proportional to the actual strength of the evidence, with no unsupported strengthening (e.g. possible-to-probable, one-study-to-research-shows)?",
        "counterevidence_treated_seriously": "Is credible counterevidence or the strongest opposing view treated seriously rather than straw-manned, minimized, or omitted?",
        "limitations_disclosed": "Are material limitations, caveats, or scope boundaries of the evidence disclosed to the reader?",
        "fact_inference_separated": "Does the article keep observed fact, inference, and speculation visibly distinct rather than blending them?",
    },
    "RT": {
        "explains_central_conclusion": "Could a reader who only read this article accurately state its central conclusion?",
        "explains_supporting_evidence": "Could a reader who only read this article accurately state the strongest evidence for that conclusion?",
        "explains_limits": "Could a reader who only read this article accurately state what remains uncertain or what would change the conclusion?",
        "actionable_or_evaluable": "Where the brief implies a need to act, decide, or evaluate related claims elsewhere, does the reader leave able to do so?",
    },
    "AF": {
        "vocabulary_matches_audience": "Is vocabulary and jargon level appropriate to the declared audience?",
        "assumed_knowledge_appropriate": "Does the article assume neither too much nor too little prior knowledge for the declared audience?",
        "examples_calibrated": "Are examples or analogies calibrated to the audience's likely frame of reference?",
        "pacing_appropriate": "Is explanatory depth and pacing appropriate for the audience (not rushing past load-bearing concepts, not over-explaining basics for an expert audience)?",
    },
    "HR": {
        "concrete_specificity": "Does the article use concrete, specific detail rather than generic filler language?",
        "voice_not_generic": "Does the prose have a distinguishable voice or register rather than reading as generic, interchangeable machine-produced text?",
        "no_fabricated_experience": "Is there no fabricated first-person experience, invented quotation, or invented scene (Standard E9)?",
        "register_fits_subject": "Is the emotional/editorial register appropriate to the subject and evidence strength, without exaggerated drama the evidence does not support?",
    },
    "SF": {
        "logical_progression": "Does the article progress in a logical order that builds on prior sections rather than jumping arbitrarily?",
        "transitions_earn_place": "Do sections and transitions connect ideas rather than reading as disconnected blocks?",
        "no_filler_section": "Is there no section that could be deleted without losing meaningful information?",
        "conclusion_crystallizes": "Does the conclusion crystallize the argument rather than merely re-summarizing it?",
    },
    "PU": {
        "usable_takeaway_present": "Does the article give the reader at least one concrete, usable takeaway (framework, checklist, criteria, example, or warning)?",
        "recommendations_supported": "Are any recommendations or implied actions actually supported by the article's own evidence?",
        "practical_specificity": "Is practical guidance specific enough to apply, rather than a vague truism?",
        "appropriate_for_archetype": "Is the level of practical utility appropriate to the declared archetype (a narrative feature need not read like a checklist; a decision guide must give usable criteria)?",
    },
}

# Great Article Standard v1 §3 archetype weighting table, including IG exactly as published.
# `renormalized_weights()` strips IG and rescales the remaining nine dimensions to sum to 100,
# since this evaluator does not score IG (see module docstring).
ARCHETYPE_WEIGHTS: dict[str, dict[str, int]] = {
    "Scientific / Scholarly Explainer": {"RQ": 20, "CQ": 15, "IG": 10, "SI": 15, "RT": 10, "AF": 10, "HR": 5, "SF": 5, "PU": 10},
    "Investigative / Current-Affairs Analysis": {"RQ": 20, "CQ": 10, "IG": 15, "SI": 15, "RT": 10, "AF": 5, "HR": 10, "SF": 10, "PU": 5},
    "Strategic / Executive Decision Guide": {"RQ": 15, "CQ": 10, "IG": 15, "SI": 15, "RT": 15, "AF": 10, "HR": 5, "SF": 5, "PU": 10},
    "Technical Tutorial / Technical Explainer": {"RQ": 10, "CQ": 15, "IG": 5, "SI": 10, "RT": 15, "AF": 15, "HR": 5, "SF": 10, "PU": 15},
    "Comparative / Commercial Decision Guide": {"RQ": 15, "CQ": 15, "IG": 15, "SI": 10, "RT": 10, "AF": 10, "HR": 5, "SF": 5, "PU": 15},
    "Argument / Thought Leadership": {"RQ": 15, "CQ": 10, "IG": 15, "SI": 20, "RT": 10, "AF": 10, "HR": 10, "SF": 5, "PU": 5},
    "Human-Centered Narrative / Feature": {"RQ": 15, "CQ": 10, "IG": 10, "SI": 10, "RT": 10, "AF": 10, "HR": 20, "SF": 10, "PU": 5},
    "Breaking-News Analysis": {"RQ": 25, "CQ": 10, "IG": 10, "SI": 15, "RT": 10, "AF": 10, "HR": 5, "SF": 10, "PU": 5},
}

# IG is intentionally NOT_EVALUATED. No proxy score is computed for it anywhere in this module.
IG_ENTRY: dict[str, Any] = {
    "status": "NOT_EVALUATED",
    "reason": (
        "Competitor-corpus ingestion and Atomic Information Unit machinery do not exist in "
        "this repository (Great Article Standard v1 SS5/SS7; docs/GREATNESS-GAP-ANALYSIS.md "
        "SS5/SS7/SS9 Layer 7). No proxy is substituted. Because the Standard requires "
        "demonstrated information gain for GREAT and EXCEPTIONAL (SS2.4), classify() caps "
        "classification at STRONG until IG is implemented and calibrated as its own experiment."
    ),
}

RT_LIMITATION_NOTE = (
    "No production Reader Transformation Contract (predeclared before/after reader state, "
    "predeclared core-question graph) exists yet (Great Article Standard v1 SS4; "
    "docs/GREATNESS-GAP-ANALYSIS.md SS4/SS9 Layer 6). This RT score is a blind post-hoc proxy "
    "-- whether the finished article itself demonstrates the reader could explain the "
    "conclusion, its evidence, and its limits -- not a measurement against a pre-declared "
    "transformation contract. Treat it as provisional until an RTC exists."
)

# Great Article Standard v1 SS2.2 ("universal minimum floor") and SS2.3/SS2.4 thresholds.
# Provisional calibration hypotheses, not empirical truths.
IH_UNIVERSAL_FLOOR = 70.0
STRONG_DIMENSION_FLOOR = 70.0
GREAT_EXCELLENCE_INDEX_MIN = 82.0
GREAT_IH_MIN = 85.0
GREAT_CQ_MIN = 85.0
EXCEPTIONAL_EXCELLENCE_INDEX_MIN = 90.0
EXCEPTIONAL_DIMENSION_FLOOR = 80.0
EXCEPTIONAL_IH_MIN = 90.0
EXCEPTIONAL_CQ_MIN = 95.0


def _criteria_schema(dim: str) -> dict[str, Any]:
    ids = list(DIMENSION_CRITERIA[dim])
    return {
        "type": "object",
        "properties": {
            cid: {
                "type": "object",
                "properties": {"pass": {"type": "boolean"}, "rationale": {"type": "string"}},
                "required": ["pass", "rationale"],
                "additionalProperties": False,
            }
            for cid in ids
        },
        "required": ids,
        "additionalProperties": False,
    }


GREATNESS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "dimensions": {
            "type": "object",
            "properties": {
                dim: {
                    "type": "object",
                    "properties": {
                        "criteria": _criteria_schema(dim),
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    },
                    "required": ["criteria", "confidence"],
                    "additionalProperties": False,
                }
                for dim in EXCELLENCE_DIMENSIONS
            },
            "required": list(EXCELLENCE_DIMENSIONS),
            "additionalProperties": False,
        },
        "archetype_fit_note": {"type": "string"},
        "overall_grader_confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["dimensions", "archetype_fit_note", "overall_grader_confidence"],
    "additionalProperties": False,
}


def renormalized_weights(archetype: str) -> dict[str, float]:
    """Return the archetype's eight non-IG, non-IH weights rescaled to sum to 100.

    ARCHETYPE_WEIGHTS entries mirror the Standard's §3 table exactly (RQ/CQ/IG/SI/RT/AF/HR/
    SF/PU, no IH column). Dropping IG and rescaling the rest to 100 keeps the relative
    proportions the Standard assigned to RQ/CQ/SI/RT/AF/HR/SF/PU intact.
    """
    if archetype not in ARCHETYPE_WEIGHTS:
        raise EvalError(f"unknown archetype {archetype!r}; must be one of {sorted(ARCHETYPE_WEIGHTS)}")
    full = ARCHETYPE_WEIGHTS[archetype]
    ig_weight = full["IG"]
    remaining_total = 100 - ig_weight
    if remaining_total <= 0:
        raise EvalError(f"archetype {archetype!r} allocates all weight to IG; cannot renormalize")
    scale = 100.0 / remaining_total
    return {dim: round(full[dim] * scale, 4) for dim in WEIGHTED_DIMENSIONS}


def compute_dimension_scores(grade: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Deterministically aggregate the semantic grader's atomic pass/fail criteria into scores."""
    dims = grade.get("dimensions") if isinstance(grade.get("dimensions"), dict) else {}
    result: dict[str, dict[str, Any]] = {}
    for dim, criteria_ids in DIMENSION_CRITERIA.items():
        entry = dims.get(dim) if isinstance(dims.get(dim), dict) else {}
        criteria = entry.get("criteria") if isinstance(entry.get("criteria"), dict) else {}
        details = []
        passed = 0
        for cid in criteria_ids:
            c = criteria.get(cid) if isinstance(criteria.get(cid), dict) else {}
            ok = c.get("pass") is True
            if ok:
                passed += 1
            details.append({"id": cid, "pass": ok, "rationale": c.get("rationale", "")})
        total = len(criteria_ids)
        result[dim] = {
            "score": round(100.0 * passed / total, 1) if total else 0.0,
            "passed_criteria": passed,
            "total_criteria": total,
            "criteria": details,
            "confidence": entry.get("confidence", "low"),
        }
    return result


def compute_excellence_index(dimension_scores: dict[str, float], weights: dict[str, float]) -> float:
    """Archetype-weighted composite over WEIGHTED_DIMENSIONS only (excludes IG and IH)."""
    total_weight = sum(weights.get(dim, 0.0) for dim in WEIGHTED_DIMENSIONS)
    if total_weight <= 0:
        return 0.0
    weighted = sum(dimension_scores.get(dim, 0.0) * weights.get(dim, 0.0) for dim in WEIGHTED_DIMENSIONS)
    return round(weighted / total_weight, 1)


def classify(
    *,
    epistemic_eligible: bool,
    dimension_scores: dict[str, float],
    excellence_index: float,
) -> dict[str, Any]:
    """Deterministic classification. See module docstring for why GREAT/EXCEPTIONAL are capped."""
    if not epistemic_eligible:
        return {
            "classification": "EPISTEMICALLY_INELIGIBLE",
            "ih_floor_pass": None,
            "would_meet_great_excellence_thresholds_excluding_ig": None,
            "would_meet_exceptional_excellence_thresholds_excluding_ig": None,
            "blocking_reasons": [
                "epistemic/QPR eligibility failed; per Great Article Standard v1 SS2.1 greatness "
                "evaluation stops and no Excellence Dimension is scored"
            ],
        }

    ih = dimension_scores.get("IH", 0.0)
    cq = dimension_scores.get("CQ", 0.0)
    min_dim = min(dimension_scores.values()) if dimension_scores else 0.0
    ih_floor_pass = ih >= IH_UNIVERSAL_FLOOR

    blocking: list[str] = []
    if not ih_floor_pass:
        blocking.append(
            f"IH score {ih:.1f} is below the universal IH floor {IH_UNIVERSAL_FLOOR:.1f} "
            "(Standard SS2.2: IH cannot be sacrificed by archetype weighting)"
        )

    would_great = (
        excellence_index >= GREAT_EXCELLENCE_INDEX_MIN
        and ih >= GREAT_IH_MIN
        and cq >= GREAT_CQ_MIN
    )
    would_exceptional = (
        excellence_index >= EXCEPTIONAL_EXCELLENCE_INDEX_MIN
        and min_dim >= EXCEPTIONAL_DIMENSION_FLOOR
        and ih >= EXCEPTIONAL_IH_MIN
        and cq >= EXCEPTIONAL_CQ_MIN
    )

    if blocking or min_dim < STRONG_DIMENSION_FLOOR:
        classification = "PUBLISHABLE"
        if min_dim < STRONG_DIMENSION_FLOOR and not any("IH score" in reason for reason in blocking):
            blocking.append(
                f"dimension score {min_dim:.1f} is below the STRONG floor {STRONG_DIMENSION_FLOOR:.1f}"
            )
    else:
        classification = "STRONG"
        if would_great or would_exceptional:
            blocking.append(
                "excellence-index/IH/CQ thresholds for GREAT/EXCEPTIONAL were met, but "
                "classification is capped at STRONG because IG is NOT_EVALUATED -- the "
                "Standard requires demonstrated information gain for both (SS2.4)"
            )

    return {
        "classification": classification,
        "ih_floor_pass": ih_floor_pass,
        "would_meet_great_excellence_thresholds_excluding_ig": would_great,
        "would_meet_exceptional_excellence_thresholds_excluding_ig": would_exceptional,
        "blocking_reasons": blocking,
    }


def build_instructions(brief: dict[str, Any], archetype: str) -> str:
    topic = brief.get("topic_brief", "")
    audience = brief.get("target_audience", "general informed readers")
    intended_thesis = brief.get("intended_thesis", "")
    criteria_text = "\n\n".join(
        f"{dim} -- {DIMENSION_LABELS[dim]}:\n"
        + "\n".join(f"  - {cid}: {question}" for cid, question in DIMENSION_CRITERIA[dim].items())
        for dim in EXCELLENCE_DIMENSIONS
    )
    return f"""You are a blind evaluator applying the Great Article Standard v1 Excellence Vector to a finished article. You are independent from the system that produced it. You do not know, and must not speculate about, whether this is a baseline or candidate system, its internal QA/fact-check conclusions, its token spend, or any production self-score.

Declared archetype: {archetype}

Topic brief:
{topic}

Target audience:
{audience}

Intended thesis / editorial direction:
{intended_thesis}

The article text is provided on stdin.

Evaluate ONLY the nine dimensions and atomic criteria below. For every criterion, set pass=true only if the article clearly and specifically satisfies it; default to pass=false when the evidence in the article is ambiguous, generic, or absent. Every rationale must cite something specific from the article, not restate the question.

{criteria_text}

Do not evaluate Information Gain, competitor comparison, or novelty relative to other pages -- that dimension is intentionally out of scope for this pass and is scored separately by machinery that does not exist yet. Do not let apparent novelty, or its absence, influence any of the nine dimensions above.

Do not reward length, confident tone, or rubric-keyword repetition. A shorter, well-hedged, honestly uncertain article should score IH criteria higher than a longer, confidently wrong one. Return only the requested structured result."""


def epistemic_eligibility_from_qpr_record(record: dict[str, Any]) -> tuple[bool, list[str]]:
    """Derive eligibility from a qpr_runner.py trial record.json without re-deriving QPR logic."""
    qualification = record.get("qualification") if isinstance(record.get("qualification"), dict) else {}
    eligible = qualification.get("qualified") is True
    reasons = list(qualification.get("reasons", [])) + list(qualification.get("hard_guardrail_failures", []))
    return eligible, reasons


def evaluate(
    article_text: str,
    brief: dict[str, Any],
    *,
    epistemic_eligible: bool,
    epistemic_reasons: list[str],
    model: str,
    effort: str,
    max_budget_usd: float,
    timeout_seconds: int,
) -> dict[str, Any]:
    archetype = brief.get("archetype")
    if archetype not in ARCHETYPE_WEIGHTS:
        raise EvalError(
            f"brief is missing a valid archetype (got {archetype!r}); must be one of "
            f"{sorted(ARCHETYPE_WEIGHTS)} per Great Article Standard v1 SS3"
        )
    weights = renormalized_weights(archetype)

    result: dict[str, Any] = {
        "evaluator_version": EVALUATOR_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "archetype": archetype,
        "archetype_weights_excluding_ig": weights,
        "epistemic_eligibility": {
            "eligible": epistemic_eligible,
            "reasons": list(epistemic_reasons),
            "source": "caller-supplied QPR/epistemic qualification; this evaluator does not re-derive eligibility",
        },
        "dimensions": {"IG": dict(IG_ENTRY)},
    }

    if not epistemic_eligible:
        result["excellence_index"] = None
        result["classification"] = classify(epistemic_eligible=False, dimension_scores={}, excellence_index=0.0)
        result["grader"] = None
        return result

    raw = run_claude_grader(
        build_instructions(brief, archetype),
        article_text,
        GREATNESS_SCHEMA,
        model=model,
        effort=effort,
        max_budget_usd=max_budget_usd,
        timeout_seconds=timeout_seconds,
        allow_web=False,
    )
    grade = raw["structured_output"]
    dim_scores = compute_dimension_scores(grade)
    dim_scores["RT"]["limitation"] = RT_LIMITATION_NOTE
    scores_only = {dim: entry["score"] for dim, entry in dim_scores.items()}
    excellence_index = compute_excellence_index(scores_only, weights)

    result["dimensions"].update(dim_scores)
    result["excellence_index"] = excellence_index
    result["classification"] = classify(
        epistemic_eligible=True,
        dimension_scores=scores_only,
        excellence_index=excellence_index,
    )
    result["grader"] = {
        "model": model,
        "effort": effort,
        "archetype_fit_note": grade.get("archetype_fit_note"),
        "overall_confidence": grade.get("overall_grader_confidence"),
        "metrics": raw["metrics"],
        "process_returncode": raw["process_returncode"],
        "stderr": raw["stderr"],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--brief", type=Path, required=True, help="brief JSON; must include an 'archetype' field (Standard SS3)")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default="opus")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--max-budget-usd", type=float, default=1.5)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    eligibility = parser.add_mutually_exclusive_group()
    eligibility.add_argument(
        "--qpr-record", type=Path,
        help="qpr_runner.py trial record.json; derives eligibility from its qualification result",
    )
    eligibility.add_argument("--epistemic-eligible", action="store_true")
    eligibility.add_argument("--epistemic-ineligible", action="store_true")
    parser.add_argument("--epistemic-reason", action="append", default=[], dest="epistemic_reasons")
    args = parser.parse_args()

    try:
        brief = load_json(args.brief)
        if args.qpr_record:
            record = load_json(args.qpr_record)
            eligible, reasons = epistemic_eligibility_from_qpr_record(record)
        elif args.epistemic_ineligible:
            eligible = False
            reasons = list(args.epistemic_reasons) or ["caller declared epistemic ineligibility"]
        elif args.epistemic_eligible:
            eligible = True
            reasons = list(args.epistemic_reasons)
        else:
            raise EvalError("one of --qpr-record, --epistemic-eligible, or --epistemic-ineligible is required")

        result = evaluate(
            args.article.read_text(encoding="utf-8"),
            brief,
            epistemic_eligible=eligible,
            epistemic_reasons=reasons,
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
