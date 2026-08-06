#!/usr/bin/env python3
"""Core grading and QPR helpers for article-pipeline experiments.

This module deliberately separates deterministic checks from semantic judgments.
Python owns artifact validation, citation structure, grader-contract validation, and
metric aggregation. Independent graders own source-support and editorial judgments.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+[^)]*)?\)")
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


def validate_claim_grade(value: dict[str, Any]) -> None:
    judgments = value.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("claim grade requires a judgments list")
    for index, item in enumerate(judgments):
        if not isinstance(item, dict):
            raise ValueError(f"claim judgment {index} must be an object")
        if item.get("verdict") not in CLAIM_VERDICTS:
            raise ValueError(f"claim judgment {index} has invalid verdict")
        if item.get("materiality") not in MATERIALITIES:
            raise ValueError(f"claim judgment {index} has invalid materiality")
        if not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise ValueError(f"claim judgment {index} requires claim text")
        citation_url = item.get("citation_url")
        if citation_url is not None and (not isinstance(citation_url, str) or not citation_url.strip()):
            raise ValueError(f"claim judgment {index} citation_url must be string or null")
        if not isinstance(item.get("fabricated_citation"), bool):
            raise ValueError(f"claim judgment {index} requires fabricated_citation boolean")
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ValueError(f"claim judgment {index} requires reason")
    for key in ("disputed_or_outdated_as_settled", "silent_conflict_drift"):
        if not isinstance(value.get(key), bool):
            raise ValueError(f"claim grade requires {key} boolean")


def claim_metrics(value: dict[str, Any]) -> dict[str, Any]:
    validate_claim_grade(value)
    judgments = value["judgments"]
    material = [j for j in judgments if j["materiality"] == "MATERIAL"]
    supported = [j for j in material if j["verdict"] == "SUPPORTED"]
    unsupported = [j for j in material if j["verdict"] in {"UNSUPPORTED", "CITATION_MISMATCH"}]
    partial = [j for j in material if j["verdict"] == "PARTIAL"]
    unverifiable = [j for j in material if j["verdict"] == "UNVERIFIABLE"]
    fabricated = [j for j in judgments if j["fabricated_citation"]]
    denominator = len(material)
    return {
        "material_claims": denominator,
        "material_supported": len(supported),
        "material_partial": len(partial),
        "material_unsupported": len(unsupported),
        "material_unverifiable": len(unverifiable),
        "material_claim_precision": (len(supported) / denominator) if denominator else 1.0,
        "fabricated_citations": len(fabricated),
        "disputed_or_outdated_as_settled": value["disputed_or_outdated_as_settled"],
        "silent_conflict_drift": value["silent_conflict_drift"],
    }


def validate_editorial_grade(value: dict[str, Any]) -> None:
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("editorial grade requires dimensions object")
    missing = REQUIRED_EDITORIAL_DIMENSIONS - set(dimensions)
    if missing:
        raise ValueError(f"editorial grade missing dimensions: {sorted(missing)}")
    for name in REQUIRED_EDITORIAL_DIMENSIONS:
        score = dimensions[name]
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not 1 <= score <= 5:
            raise ValueError(f"editorial dimension {name} must be numeric 1..5")
    if not isinstance(value.get("hard_failure"), bool):
        raise ValueError("editorial grade requires hard_failure boolean")


def editorial_metrics(value: dict[str, Any], threshold: float = 4.0, minimum_dimension: float = 3.0) -> dict[str, Any]:
    validate_editorial_grade(value)
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
    editorial_threshold: float = 4.0,
    minimum_editorial_dimension: float = 3.0,
    maximum_material_unsupported: int = 0,
    minimum_material_claim_precision: float = 0.9,
) -> dict[str, Any]:
    claims = claim_metrics(claim_grade)
    editorial = editorial_metrics(editorial_grade, editorial_threshold, minimum_editorial_dimension)
    epistemic_pass = (
        claims["fabricated_citations"] == 0
        and claims["material_unsupported"] <= maximum_material_unsupported
        and claims["material_claim_precision"] >= minimum_material_claim_precision
        and not claims["disputed_or_outdated_as_settled"]
        and not claims["silent_conflict_drift"]
    )
    qualified = bool(deterministic_publishable and epistemic_pass and editorial["pass"] and not human_rescue)
    return {
        "qualified_publish": qualified,
        "deterministic_publishable": deterministic_publishable,
        "epistemic_pass": epistemic_pass,
        "editorial_pass": editorial["pass"],
        "human_rescue": human_rescue,
        "claim_metrics": claims,
        "editorial_metrics": editorial,
    }


def aggregate_variant(trials: list[dict[str, Any]]) -> dict[str, Any]:
    if not trials:
        return {"trials": 0, "qualified_publishes": 0, "qpr": 0.0}
    qualified = sum(1 for trial in trials if trial.get("qualified_publish"))
    return {
        "trials": len(trials),
        "qualified_publishes": qualified,
        "qpr": qualified / len(trials),
        "deterministic_publish_rate": sum(1 for t in trials if t.get("deterministic_publishable")) / len(trials),
        "epistemic_pass_rate": sum(1 for t in trials if t.get("epistemic_pass")) / len(trials),
        "editorial_pass_rate": sum(1 for t in trials if t.get("editorial_pass")) / len(trials),
        "human_rescue_rate": sum(1 for t in trials if t.get("human_rescue")) / len(trials),
    }
