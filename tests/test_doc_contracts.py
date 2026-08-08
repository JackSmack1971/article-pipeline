import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class SourceAppendixContractTests(unittest.TestCase):
    """Regression: article-qa-auditor's holistic checklist and
    article-seo-optimizer's E-E-A-T/on-page schema both required a trailing
    'Source Appendix' that references/markdown-style.md bans outright
    ('No trailing citation block.'). One artifact could never satisfy both
    contracts at once."""

    def test_qa_auditor_holistic_checklist_does_not_require_banned_appendix(self):
        text = (REPO_ROOT / ".claude/skills/article-qa-auditor/SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("Source Appendix present and complete", text)

    def test_seo_schema_does_not_require_banned_appendix(self):
        text = (REPO_ROOT / ".claude/skills/article-seo-optimizer/references/seo-schema.md").read_text(encoding="utf-8")
        self.assertNotIn("Source Appendix present | Must exist and contain", text)
        self.assertNotIn("Source Appendix complete; no", text)

    def test_seo_schema_citation_check_aligns_with_phrase_link_standard(self):
        text = (REPO_ROOT / ".claude/skills/article-seo-optimizer/references/seo-schema.md").read_text(encoding="utf-8")
        self.assertIn("phrase-linked citations", text)

    def test_claims_table_makes_missing_urls_explicit(self):
        pipeline = (REPO_ROOT / ".claude/skills/multi-agent-article-pipeline/SKILL.md").read_text(encoding="utf-8")
        personas = (REPO_ROOT / ".claude/skills/multi-agent-article-pipeline/references/personas.md").read_text(encoding="utf-8")

        self.assertIn("| Claim ID | Final Value | Source URL | URL Status |", pipeline)
        self.assertIn("| ADV-9 | [original claim] | — | URL-MISSING |", pipeline)
        self.assertIn("`URL Status` is required for every row", pipeline)
        self.assertIn("publisher homepage, database homepage, search URL, or guessed URL", pipeline)
        self.assertIn('that row\'s `URL Status` is `AVAILABLE`', personas)
        self.assertIn("cite by attribution only", personas)


if __name__ == "__main__":
    unittest.main()
