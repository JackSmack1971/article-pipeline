#!/usr/bin/env python3
"""Independent factual-claim and citation grader for article-pipeline outputs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.evals.common import EvalError, atomic_write_json, load_json, run_claude_grader
except ModuleNotFoundError:  # direct `python scripts/evals/claim_citation_grader.py`
    from common import EvalError, atomic_write_json, load_json, run_claude_grader


CLAIM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "material": {"type": "boolean"},
                    "presented_as_current_fact": {"type": "boolean"},
                    "citation_url": {"type": ["string", "null"]},
                    "support": {"type": "string", "enum": ["supports", "partial", "does_not_support", "contradicts", "unverifiable"]},
                    "factual_status": {"type": "string", "enum": ["current", "outdated", "contradicted", "uncertain", "not_applicable"]},
                    "citation_integrity": {"type": "string", "enum": ["valid", "missing", "dead_or_unreachable", "mismatched_attribution", "likely_fabricated", "not_applicable"]},
                    "verification_urls": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                },
                "required": ["claim", "material", "presented_as_current_fact", "citation_url", "support", "factual_status", "citation_integrity", "verification_urls", "notes"],
                "additionalProperties": false
            }
        },
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "anchor": {"type": "string"},
                    "url": {"type": "string"},
                    "integrity": {"type": "string", "enum": ["valid", "dead_or_unreachable", "mismatched_attribution", "likely_fabricated"]},
                    "nearby_claim_support": {"type": "string", "enum": ["supports", "partial", "does_not_support", "not_applicable"]},
                    "notes": {"type": "string"}
                },
                "required": ["anchor", "url", "integrity", "nearby_claim_support", "notes"],
                "additionalProperties": false
            }
        },
        "article_level_findings": {"type": "array", "items": {"type": "string"}},
        "grader_confidence": {"type": "string", "enum": ["high", "medium", "low"]}
    },
    "required": ["claims", "citations", "article_level_findings", "grader_confidence"],
    "additionalProperties": false
}

INTEGRITY_VIOLATIONS = {"mismatched_attribution", "likely_fabricated"}
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https://[^)\s]+)\)")


def extract_markdown_citations(article_text: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for anchor, url in MARKDOWN_LINK_RE.findall(article_text):
        if url in seen:
            continue
        seen.add(url)
        result.append({"anchor": anchor, "url": url})
    return result


def compute_claim_metrics(grade: dict[str, Any], expected_citations: list[dict[str, str]] | None = None) -> dict[str, Any]:
    claims = [item for item in grade.get("claims", []) if isinstance(item, dict)]
    material = [item for item in claims if item.get("material") is True]
    cited_material = [item for item in material if isinstance(item.get("citation_url"), str) and item.get("citation_url")]
    citations = [item for item in grade.get("citations", []) if isinstance(item, dict)]
    fully_supported = [item for item in material if item.get("support") == "supports" and item.get("factual_status") not in {"outdated", "contradicted"}]
    citation_supported = [item for item in citations if item.get("nearby_claim_support") == "supports" and item.get("integrity") == "valid"]
    applicable_citations = [item for item in citations if item.get("nearby_claim_support") != "not_applicable"]
    missing_citations = [item for item in material if item.get("citation_integrity") == "missing"]
    integrity_violations = [item for item in claims if item.get("citation_integrity") in INTEGRITY_VIOLATIONS]
    integrity_violations.extend(item for item in citations if item.get("integrity") in INTEGRITY_VIOLATIONS)
    stale_or_contradicted = [item for item in material if item.get("presented_as_current_fact") is True and item.get("factual_status") in {"outdated", "contradicted"}]
    unsupported = [item for item in material if item.get("support") in {"does_not_support", "contradicts", "unverifiable"}]

    material_count = len(material)
    cited_count = len(applicable_citations)
    expected_citations = expected_citations or []
    expected_urls = {item["url"] for item in expected_citations if isinstance(item.get("url"), str)}
    audited_urls = {item.get("url") for item in citations if isinstance(item.get("url"), str)}
    audit_target = min(len(expected_urls), 50)
    audited_expected = len(expected_urls & audited_urls)
    audit_coverage = min(audited_expected / audit_target, 1.0) if audit_target else 1.0
    ungraded_urls = sorted(expected_urls - audited_urls) if len(expected_urls) <= 50 else []
    citation_audit_complete = audit_coverage >= 1.0
    return {
        "material_claim_count": material_count,
        "fully_supported_material_claims": len(fully_supported),
        "material_claim_precision": len(fully_supported) / material_count if material_count else 1.0,
        "cited_material_claim_count": len(cited_material),
        "audited_applicable_citation_count": cited_count,
        "citation_support_pass_count": len(citation_supported),
        "citation_support_rate": len(citation_supported) / cited_count if cited_count else (1.0 if not expected_urls else 0.0),
        "article_markdown_citation_count": len(expected_urls),
        "citation_audit_target_count": audit_target,
        "citation_audit_coverage_rate": audit_coverage,
        "ungraded_citation_count": len(ungraded_urls),
        "ungraded_citation_urls": ungraded_urls[:20],
        "missing_material_citation_count": len(missing_citations),
        "unsupported_material_claim_count": len(unsupported),
        "integrity_violation_count": len(integrity_violations),
        "stale_or_contradicted_current_fact_count": len(stale_or_contradicted),
        "hard_guardrail_pass": not integrity_violations and not stale_or_contradicted and citation_audit_complete
    }


def build_instructions(brief: dict[str, Any], max_claims: int) -> str:
    audience = brief.get("target_audience", "the declared target audience")
    topic = brief.get("topic_brief", "")
    return f"""You are an independent factual-claim and citation auditor. You are NOT part of the article pipeline that wrote the article. Do not trust the article's own confidence labels, source appendix, fact-check report, or prose merely because they exist.

The article text will be provided on stdin. The evaluation topic is:
{topic}
Target audience: {audience}

Audit up to {max_claims} MATERIAL factual claims, prioritizing claims that are quantitative, causal, comparative, current, central to the thesis, or likely to affect a reader's decision. Ignore pure opinion, obvious transitions, and trivial definitions unless they are materially wrong.

Separately audit every unique markdown citation URL you can identify in the article (up to 50 unique URLs). For each citation, check source identity/integrity and whether it supports the factual proposition immediately around its anchor. If there are more than 50, audit the 50 attached to the most material claims and note the truncation in article_level_findings.

For each selected claim:
1. Identify the exact proposition being asserted.
2. If the article gives a markdown citation, inspect that URL when possible and determine whether the cited source actually supports the proposition as written.
3. Independently search the web for corroboration or contradiction. Prefer primary sources, official data, peer-reviewed research, and authoritative institutional sources.
4. Distinguish a dead/transiently unreachable URL from a likely fabricated citation. Use `likely_fabricated` only when the attributed source/title/entity appears not to exist or the URL/source identity is invented. Use `mismatched_attribution` when the link exists but is attributed to the wrong organization/platform/source.
5. Mark a claim `outdated` when it is presented as current but materially superseded. Mark `contradicted` only when reliable evidence directly conflicts with it.
6. `supports` means the cited/verified evidence supports the claim as stated. `partial` means the article overstates or generalizes beyond the evidence. `unverifiable` means reasonable independent checking could not establish it.

Do not reward citation quantity. Grade support quality and factual status. Do not use article style as evidence of truth. Return only the requested structured result."""


def grade_article(article_text: str, brief: dict[str, Any], *, model: str, effort: str, max_budget_usd: float, timeout_seconds: int, max_claims: int = 30) -> dict[str, Any]:
    raw = run_claude_grader(build_instructions(brief, max_claims), article_text, CLAIM_SCHEMA, model=model, effort=effort, max_budget_usd=max_budget_usd, timeout_seconds=timeout_seconds, allow_web=True)
    grade = raw["structured_output"]
    expected_citations = extract_markdown_citations(article_text)
    return {"grade": grade, "metrics": compute_claim_metrics(grade, expected_citations), "grader_metrics": raw["metrics"], "process_returncode": raw["process_returncode"], "stderr": raw["stderr"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", type=Path, required=True)
    parser.add_argument("--brief", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default="opus")
    parser.add_argument("--effort", default="high")
    parser.add_argument("--max-budget-usd", type=float, default=2.5)
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--max-claims", type=int, default=30)
    args = parser.parse_args()
    try:
        result = grade_article(args.article.read_text(encoding="utf-8"), load_json(args.brief), model=args.model, effort=args.effort, max_budget_usd=args.max_budget_usd, timeout_seconds=args.timeout_seconds, max_claims=args.max_claims)
    except (OSError, EvalError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "EVALUATOR_ERROR", "error": str(exc)}, indent=2))
        return 2
    if args.output:
        atomic_write_json(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
