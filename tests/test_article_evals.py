import json
import tempfile
import unittest
from pathlib import Path

from scripts.evals.claim_citation_grader import compute_claim_metrics, extract_markdown_citations
from scripts.evals.editorial_grader import DIMENSIONS, compute_editorial_metrics
from scripts.evals.qpr_runner import (
    aggregate_arm,
    dynamic_isolation_guardrails,
    extract_agent_calls,
    load_corpus,
    match_scripted_decision,
    paired_bootstrap_ci,
    qualification,
    recommendation,
)


class ClaimCitationMetricsTests(unittest.TestCase):
    def test_hard_guardrail_fails_on_mismatched_attribution(self):
        grade = {
            "claims": [
                {
                    "claim": "A",
                    "material": True,
                    "presented_as_current_fact": True,
                    "citation_url": "https://example.com/a",
                    "support": "supports",
                    "factual_status": "current",
                    "citation_integrity": "mismatched_attribution",
                }
            ]
        }
        metrics = compute_claim_metrics(grade)
        self.assertEqual(metrics["integrity_violation_count"], 1)
        self.assertFalse(metrics["hard_guardrail_pass"])

    def test_precision_and_support_are_computed_from_claim_rows(self):
        grade = {
            "claims": [
                {
                    "claim": "A",
                    "material": True,
                    "presented_as_current_fact": True,
                    "citation_url": "https://example.com/a",
                    "support": "supports",
                    "factual_status": "current",
                    "citation_integrity": "valid",
                },
                {
                    "claim": "B",
                    "material": True,
                    "presented_as_current_fact": True,
                    "citation_url": "https://example.com/b",
                    "support": "partial",
                    "factual_status": "current",
                    "citation_integrity": "valid",
                },
            ]
        }
        grade["citations"] = [
            {"anchor": "A", "url": "https://example.com/a", "integrity": "valid", "nearby_claim_support": "supports"},
            {"anchor": "B", "url": "https://example.com/b", "integrity": "valid", "nearby_claim_support": "partial"},
        ]
        expected = extract_markdown_citations("[A](https://example.com/a) [B](https://example.com/b)")
        metrics = compute_claim_metrics(grade, expected)
        self.assertEqual(metrics["material_claim_precision"], 0.5)
        self.assertEqual(metrics["citation_support_rate"], 0.5)
        self.assertEqual(metrics["citation_audit_coverage_rate"], 1.0)


class EditorialMetricsTests(unittest.TestCase):
    def test_dimension_mean_and_fatal_issue(self):
        grade = {
            "dimensions": {name: {"score": 4, "rationale": "ok"} for name in DIMENSIONS},
            "fatal_editorial_issues": [{"category": "thesis_drift", "detail": "drift"}],
            "publication_recommendation": "substantive_revision",
        }
        metrics = compute_editorial_metrics(grade)
        self.assertEqual(metrics["mean_score"], 4.0)
        self.assertEqual(metrics["minimum_dimension_score"], 4)
        self.assertFalse(metrics["hard_guardrail_pass"])


class QprTests(unittest.TestCase):
    def good_claim_result(self):
        return {
            "metrics": {
                "material_claim_precision": 1.0,
                "citation_support_rate": 1.0,
                "hard_guardrail_pass": True,
            }
        }

    def good_editorial_result(self):
        return {
            "metrics": {
                "mean_score": 4.25,
                "minimum_dimension_score": 4,
                "hard_guardrail_pass": True,
            }
        }

    def brief(self):
        return {
            "id": "x",
            "topic_brief": "topic",
            "target_audience": "audience",
            "scripted_decisions": {"approval": "approved"},
            "allowed_depths": ["STANDARD"],
        }

    def test_qualification_requires_publishable_and_quality(self):
        result = qualification(
            validator={"status": "PUBLISHABLE"},
            claim_result=self.good_claim_result(),
            editorial_result=self.good_editorial_result(),
            subject={"human_rescue_required": False, "route_depth": "STANDARD"},
            brief=self.brief(),
            static_guardrails={"pass": True},
            dynamic_guardrails={"pass": True},
        )
        self.assertTrue(result["qualified"])

    def test_human_rescue_disqualifies(self):
        result = qualification(
            validator={"status": "PUBLISHABLE"},
            claim_result=self.good_claim_result(),
            editorial_result=self.good_editorial_result(),
            subject={"human_rescue_required": True, "route_depth": "STANDARD"},
            brief=self.brief(),
            static_guardrails={"pass": True},
            dynamic_guardrails={"pass": True},
        )
        self.assertFalse(result["qualified"])
        self.assertTrue(any("human rescue" in reason for reason in result["reasons"]))

    def test_extract_agent_calls_from_stream_events(self):
        payload = {
            "_events": [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "article-skeptic", "prompt": "URLs only"}}
                ]}}
            ]
        }
        calls = extract_agent_calls(payload)
        self.assertEqual(calls[0]["subagent_type"], "article-skeptic")

    def test_dynamic_isolation_detects_advocate_claim_leak_to_skeptic(self):
        root = Path(tempfile.mkdtemp())
        artifacts = root / ".agents" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "pipeline_config.json").write_text(json.dumps({"pipeline": {"adversarial_dialectic": True}}), encoding="utf-8")
        claim = "This distinctive advocate claim should never be copied into the skeptic delegation prompt verbatim."
        (artifacts / "advocate_context.md").write_text(f"- **Statement:** {claim}\n", encoding="utf-8")
        subject = {"turns": [{"agent_calls": [
            {"subagent_type": "article-advocate", "prompt": "support"},
            {"subagent_type": "article-skeptic", "prompt": f"challenge this: {claim}"},
        ]}]}
        result = dynamic_isolation_guardrails(root, subject)
        self.assertFalse(result["pass"])

    def test_dynamic_isolation_detects_full_body_leak_to_red_team(self):
        root = Path(tempfile.mkdtemp())
        artifacts = root / ".agents" / "artifacts"
        artifacts.mkdir(parents=True)
        (artifacts / "pipeline_config.json").write_text(json.dumps({"pipeline": {"red_team": True}}), encoding="utf-8")
        body = "This is a deliberately long body paragraph containing sensitive supporting argument context that the red team must not receive. " * 2
        draft = f"# Title\n\n## Body\n\n{body}\n\n## Conclusion\n\nConclusion text."
        (artifacts / "article_draft.md").write_text(draft, encoding="utf-8")
        subject = {"turns": [{"agent_calls": [
            {"subagent_type": "article-red-team", "prompt": body[:150]},
        ]}]}
        result = dynamic_isolation_guardrails(root, subject)
        self.assertFalse(result["pass"])

    def test_match_scripted_approval(self):
        brief = self.brief()
        decision = match_scripted_decision("⛔ APPROVAL GATE — Pipeline Paused", brief, set(), "APPROVAL")
        self.assertEqual(decision, ("approval", "approved"))

    def test_corpus_validation_rejects_duplicate_ids(self):
        root = Path(tempfile.mkdtemp())
        payload = self.brief()
        (root / "a.json").write_text(json.dumps(payload), encoding="utf-8")
        (root / "b.json").write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(Exception):
            load_corpus(root)

    def test_aggregate_separates_infrastructure_errors(self):
        records = [
            {"qualification": {"qualified": True, "hard_guardrail_failures": []}, "subject": {"total_cost_usd": 2, "total_duration_ms": 3, "total_input_tokens": 4, "total_output_tokens": 5}},
            {"evaluator_error": "boom"},
        ]
        summary = aggregate_arm(records)
        self.assertEqual(summary["trials"], 2)
        self.assertEqual(summary["evaluable_trials"], 1)
        self.assertEqual(summary["qpr"], 1.0)
        self.assertEqual(summary["operational_qpr"], 0.5)

    def test_bootstrap_constant_difference(self):
        self.assertEqual(paired_bootstrap_ci([1.0, 1.0, 1.0], samples=100, seed=1), (1.0, 1.0))

    def test_recommendation_rejects_guardrail_regression(self):
        baseline = {"hard_guardrail_failure_count": 0}
        candidate = {"hard_guardrail_failure_count": 1}
        paired = {"paired_evaluable_trials": 10, "candidate_minus_baseline_qpr": 0.5, "paired_bootstrap_95_ci": [0.2, 0.8]}
        result = recommendation(baseline, candidate, paired, minimum_qpr_delta=0.05, noninferiority_margin=0.02, minimum_pairs=6)
        self.assertEqual(result["decision"], "reject")


if __name__ == "__main__":
    unittest.main()
