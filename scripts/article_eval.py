#!/usr/bin/env python3
"""Core grading and QPR helpers for article-pipeline experiments.

Deterministic code owns artifact/citation structure, grader-contract validation,
stale-evidence binding, QPR scoring, paired comparison, and aggregation.
Independent graders own semantic source-support and editorial judgments.
"""

from __future__ import annotations

import json
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+[^)]*)?\)")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GENERIC_ANCHORS = {"here", "link", "source", "read more", "learn more", "this", "website"}
CLAIM_VERDICTS = {"SUPPORTED", "PARTIAL", "UNSUPPORTED", "UNVERIFIABLE", "CITATION_MISMATCH"}
MATERIALITIES = {"MATERIAL", "MINOR"}
REQUIRED_EDITORIAL_DIMENSIONS = {
    "coherence",
    "audience_fit",
    "reasoning",
    "nuance",
    "readability",
    "usefulness",
}
CLAIM_TOP_LEVEL_REQUIRED = {
    "input_sha256",
    "coverage_complete",
    "judgments",
    "disputed_or_outdated_as_settled",
    "silent_conflict_drift",
}
CLAIM_TOP_LEVEL_ALLOWED = CLAIM_TOP_LEVEL_REQUIRED | {"notes"}
CLAIM_JUDGMENT_KEYS = {
    "claim",
    "materiality",
    "citation_url",
    "verdict",
    "fabricated_citation",
    "reason",
}
EDITORIAL_TOP_LEVEL_REQUIRED = {
    "input_sha256",
    "dimensions",
    "hard_failure",
    "strengths",
    "weaknesses",
}
EDITORIAL_TOP_LEVEL_ALLOWED = EDITORIAL_TOP_LEVEL_REQUIRED | {"notes"}


@dataclass(frozen=True)
class Citation:
    anchor: str
    url: str


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def extract_citations(markdown: str) -> list[Citation]:
    return [Citation(anchor=m.group(1).strip(), url=m.group(2).strip()) for m in LINK_RE.finditer(markdown)]


def citation_structure_report(markdown: str) -> dict[str, Any]:
    citations = extract_citations(markdown)
    invalid_absolute = [c.url for c in citations if not c.url.startswith("https://")]
    generic_anchors = [c.anchor for c in citations if c.anchor.strip().lower() in GENERIC_ANCHORS]
    urls = [c.url for c in citations]
    return {
        "citation_count": len(citations),
        "distinct_url_count": len(set(urls)),
        "invalid_absolute_urls": invalid_absolute,
        "generic_anchors": generic_anchors,
        "duplicate_url_count": len(urls) - len(set(urls)),
        "citations": [{"anchor": c.anchor, "url": c.url} for c in citations],
    }


def _validate_exact_keys(value: dict[str, Any], required: set[str], allowed: set[str], label: str) -> None:
    missing = required - set(value)
    unknown = set(value) - allowed
    if missing:
        raise ValueError(f"{label} missing fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"{label} contains unknown fields: {sorted(unknown)}")


def _validate_input_sha256(value: object, expected_input_sha256: str | None, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{label} input_sha256 must be a lowercase SHA-256 hex digest")
    if expected_input_sha256 is not None and value != expected_input_sha256:
        raise ValueError(f"{label} input_sha256 does not match prepared trial input")
    return value


def validate_claim_grade(
    value: dict[str, Any],
    *,
    expected_input_sha256: str | None = None,
    article_citation_urls: set[str] | None = None,
) -> None:
    _validate_exact_keys(value, CLAIM_TOP_LEVEL_REQUIRED, CLAIM_TOP_LEVEL_ALLOWED, "claim grade")
    _validate_input_sha256(value.get("input_sha256"), expected_input_sha256, "claim grade")
    if value.get("coverage_complete") is not True:
        raise ValueError("claim grade coverage_complete must be true")

    judgments = value.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("claim grade requires a judgments list")
    for index, item in enumerate(judgments):
        if not isinstance(item, dict):
            raise ValueError(f"claim judgment {index} must be an object")
        _validate_exact_keys(item, CLAIM_JUDGMENT_KEYS, CLAIM_JUDGMENT_KEYS, f"claim judgment {index}")
        if item.get("verdict") not in CLAIM_VERDICTS:
            raise ValueError(f"claim judgment {index} has invalid verdict")
        if item.get("materiality") not in MATERIALITIES:
            raise ValueError(f"claim judgment {index} has invalid materiality")
        if not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise ValueError(f"claim judgment {index} requires claim text")
        citation_url = item.get("citation_url")
        if citation_url is not None:
            if not isinstance(citation_url, str) or not citation_url.startswith("https://"):
                raise ValueError(f"claim judgment {index} citation_url must be an https URL or null")
        if not isinstance(item.get("fabricated_citation"), bool):
            raise ValueError(f"claim judgment {index} requires fabricated_citation boolean")
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError(f"claim judgment {index} requires reason")
        if article_citation_urls is not None and citation_url is not None and citation_url not in article_citation_urls:
            raise ValueError(f"claim judgment {index} citation_url does not appear in the blinded article")

    for key in ("disputed_or_outdated_as_settled", "silent_conflict_drift"):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"claim grade requires {key} boolean")
    if "notes" in value and not isinstance(value["notes"], str):
        raise ValueError("claim grade notes must be a string")


def claim_metrics(
    value: dict[str, Any],
    *,
    expected_input_sha256: str | None = None,
    article_citation_urls: set[str] | None = None,
) -> dict[str, Any]:
    validate_claim_grade(
        value,
        expected_input_sha256=expected_input_sha256,
        article_citation_urls=article_citation_urls,
    )
    judgments = value["judgments"]
    material = [j for j in judgments if j["materiality"] == "MATERIAL"]
    supported = [j for j in material if j["verdict"] == "SUPPORTED"]
    unsupported = [j for j in material if j["verdict"] in {"UNSUPPORTED", "CITATION_MISMATCH"}]
    partial = [j for j in material if j["verdict"] == "PARTIAL"]
    unverifiable = [j for j in material if j["verdict"] == "UNVERIFIABLE"]
    uncited = [j for j in material if j["citation_url"] is None]
    fabricated = [j for j in judgments if j["fabricated_citation"]]
    denominator = len(material)
    return {
        "coverage_complete": value["coverage_complete"],
        "material_claims": denominator,
        "material_supported": len(supported),
        "material_partial": len(partial),
        "material_unsupported": len(unsupported),
        "material_unverifiable": len(unverifiable),
        "material_uncited": len(uncited),
        "material_claim_precision": (len(supported) / denominator) if denominator else 0.0,
        "fabricated_citations": len(fabricated),
        "disputed_or_outdated_as_settled": value["disputed_or_outdated_as_settled"],
        "silent_conflict_drift": value["silent_conflict_drift"],
    }


def validate_editorial_grade(
    value: dict[str, Any],
    *,
    expected_input_sha256: str | None = None,
) -> None:
    _validate_exact_keys(value, EDITORIAL_TOP_LEVEL_REQUIRED, EDITORIAL_TOP_LEVEL_ALLOWED, "editorial grade")
    _validate_input_sha256(value.get("input_sha256"), expected_input_sha256, "editorial grade")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("editorial grade requires dimensions object")
    if set(dimensions) != REQUIRED_EDITORIAL_DIMENSIONS:
        raise ValueError(
            "editorial grade dimensions must be exactly "
            f"{sorted(REQUIRED_EDITORIAL_DIMENSIONS)}"
        )
    for name in REQUIRED_EDITORIAL_DIMENSIONS:
        score = dimensions[name]
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 1 <= score <= 5:
            raise ValueError(f"editorial dimension {name} must be numeric 1..5")
    if not isinstance(value.get("hard_failure"), bool):
        raise ValueError("editorial grade requires hard_failure boolean")
    for key in ("strengths", "weaknesses"):
        entries = value.get(key)
        if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
            raise ValueError(f"editorial grade {key} must be a list of strings")
    if "notes" in value and not isinstance(value["notes"], str):
        raise ValueError("editorial grade notes must be a string")


def editorial_metrics(
    value: dict[str, Any],
    threshold: float = 4.0,
    minimum_dimension: float = 3.0,
    *,
    expected_input_sha256: str | None = None,
) -> dict[str, Any]:
    validate_editorial_grade(value, expected_input_sha256=expected_input_sha256)
    dimensions = value["dimensions"]
    mean = sum(float(dimensions[name]) for name in REQUIRED_EDITORIAL_DIMENSIONS) / len(REQUIRED_EDITORIAL_DIMENSIONS)
    low = min(float(dimensions[name]) for name in REQUIRED_EDITORIAL_DIMENSIONS)
    passed = not value["hard_failure"] and mean >= threshold and low >= minimum_dimension
    return {"mean": mean, "minimum": low, "pass": passed, "hard_failure": value["hard_failure"]}


def qpr_trial(
    *,
    deterministic_publishable: bool,
    claim_grade: dict[str, Any],
    editorial_grade: dict[str, Any],
    human_rescue: bool,
    input_sha256: str,
    citation_structure: dict[str, Any],
    editorial_threshold: float = 4.0,
    minimum_editorial_dimension: float = 3.0,
    maximum_material_unsupported: int = 0,
    maximum_material_uncited: int = 0,
    minimum_material_claims: int = 1,
    minimum_material_claim_precision: float = 0.9,
) -> dict[str, Any]:
    citation_urls = {
        item["url"]
        for item in citation_structure.get("citations", [])
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    }
    claims = claim_metrics(
        claim_grade,
        expected_input_sha256=input_sha256,
        article_citation_urls=citation_urls,
    )
    editorial = editorial_metrics(
        editorial_grade,
        editorial_threshold,
        minimum_editorial_dimension,
        expected_input_sha256=input_sha256,
    )
    citation_structure_pass = not citation_structure.get("invalid_absolute_urls")
    epistemic_pass = (
        claims["coverage_complete"]
        and claims["material_claims"] >= minimum_material_claims
        and claims["fabricated_citations"] == 0
        and claims["material_unsupported"] <= maximum_material_unsupported
        and claims["material_uncited"] <= maximum_material_uncited
        and claims["material_claim_precision"] >= minimum_material_claim_precision
        and citation_structure_pass
        and not claims["disputed_or_outdated_as_settled"]
        and not claims["silent_conflict_drift"]
    )
    qualified = bool(deterministic_publishable and epistemic_pass and editorial["pass"] and not human_rescue)
    return {
        "qualified_publish": qualified,
        "deterministic_publishable": deterministic_publishable,
        "epistemic_pass": epistemic_pass,
        "editorial_pass": editorial["pass"],
        "citation_structure_pass": citation_structure_pass,
        "human_rescue": human_rescue,
        "claim_metrics": claims,
        "editorial_metrics": editorial,
    }


def _mean(values: list[float]) -> float | None:
    return (sum(values) / len(values)) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def aggregate_variant(trials: list[dict[str, Any]]) -> dict[str, Any]:
    if not trials:
        return {"trials": 0, "qualified_publishes": 0, "qpr": 0.0}

    qualified_trials = [trial for trial in trials if trial.get("qualified_publish")]
    result: dict[str, Any] = {
        "trials": len(trials),
        "qualified_publishes": len(qualified_trials),
        "qpr": len(qualified_trials) / len(trials),
        "deterministic_publish_rate": sum(1 for t in trials if t.get("deterministic_publishable")) / len(trials),
        "epistemic_pass_rate": sum(1 for t in trials if t.get("epistemic_pass")) / len(trials),
        "editorial_pass_rate": sum(1 for t in trials if t.get("editorial_pass")) / len(trials),
        "human_rescue_rate": sum(1 for t in trials if t.get("human_rescue")) / len(trials),
        "mean_material_claim_precision": _mean(
            [float(t["claim_metrics"]["material_claim_precision"]) for t in trials]
        ),
        "mean_editorial_score": _mean([float(t["editorial_metrics"]["mean"]) for t in trials]),
    }

    metric_names = (
        "cost_usd",
        "wall_time_seconds",
        "input_tokens",
        "output_tokens",
        "tool_calls",
        "agent_calls",
    )
    efficiency: dict[str, Any] = {}
    for name in metric_names:
        all_values = [
            float(t["run_metrics"][name])
            for t in trials
            if isinstance(t.get("run_metrics"), dict) and isinstance(t["run_metrics"].get(name), (int, float))
        ]
        qualified_values = [
            float(t["run_metrics"][name])
            for t in qualified_trials
            if isinstance(t.get("run_metrics"), dict) and isinstance(t["run_metrics"].get(name), (int, float))
        ]
        if all_values:
            efficiency[f"median_{name}"] = _median(all_values)
        if qualified_values:
            efficiency[f"median_{name}_qualified"] = _median(qualified_values)
    if efficiency:
        result["efficiency"] = efficiency
    return result


def paired_comparison(
    baseline_trials: list[dict[str, Any]],
    candidate_trials: list[dict[str, Any]],
) -> dict[str, Any]:
    def keyed(trials: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
        result: dict[tuple[str, int], dict[str, Any]] = {}
        for trial in trials:
            key = (str(trial["brief_id"]), int(trial["trial"]))
            if key in result:
                raise ValueError(f"duplicate paired trial: {key}")
            result[key] = trial
        return result

    baseline = keyed(baseline_trials)
    candidate = keyed(candidate_trials)
    if set(baseline) != set(candidate):
        missing_candidate = sorted(set(baseline) - set(candidate))
        missing_baseline = sorted(set(candidate) - set(baseline))
        raise ValueError(
            "baseline/candidate trials are not matched; "
            f"missing_candidate={missing_candidate}, missing_baseline={missing_baseline}"
        )

    both = candidate_only = baseline_only = neither = 0
    for key in baseline:
        b = bool(baseline[key].get("qualified_publish"))
        c = bool(candidate[key].get("qualified_publish"))
        if b and c:
            both += 1
        elif c:
            candidate_only += 1
        elif b:
            baseline_only += 1
        else:
            neither += 1
    total = len(baseline)
    return {
        "matched_pairs": total,
        "both_qualified": both,
        "candidate_only_qualified": candidate_only,
        "baseline_only_qualified": baseline_only,
        "neither_qualified": neither,
        "qpr_absolute_delta": ((both + candidate_only) - (both + baseline_only)) / total if total else 0.0,
    }
