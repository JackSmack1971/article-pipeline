---
name: article-red-team
description: >
  Constructs the strongest possible counterargument to any article thesis using logical,
  empirical, and framing attack vectors. Receives only the thesis statement and conclusion
  section — never the full draft — to prevent anchoring. Produces a structured threat
  assessment with recommended response and threat level rating. Usable standalone on any
  claim or position. Triggers on: red team this, challenge this thesis, steelman the
  opposition, strongest counterargument, adversarial review, find the holes in this
  argument, attack this claim. Activates automatically at Step 4 of multi-agent-article-pipeline
  for COMPLEX depth only. Do NOT trigger on requests for supporting arguments, balanced
  analysis, or fact-checking tasks.
---

# Article Red Team — v4

## Purpose

Post-draft adversarial challenge. The human decides whether the attack warrants a response.

## Delegation

**Delegate to the `article-red-team` subagent** rather than operating as @adversary in this
context. Pass in the delegation prompt ONLY:
1. The thesis statement (from `article_spec.md` line 1)
2. The conclusion section text (final section of `article_draft.md`)

Do not pass, summarize, or paraphrase the rest of the article body. The subagent has no
`Read` tool and no `Write` tool — it has no filesystem path to `article_draft.md` even if it
wanted one, and it returns its report as its final message rather than persisting it itself.
This is a capability boundary, not a prompt instruction: anchoring on the author's arguments
would produce a weaker, less useful red team, so the constraint is enforced by what the
worker can reach, not by what it's told not to look at.

The subagent runs the attack across three vectors (logical, empirical via `WebSearch`, and
framing) and returns a structured Red Team Report — see `.claude/agents/article-red-team.md`
for the full protocol and output format.

**On return:** write the subagent's report verbatim to `.agents/artifacts/red_team_report.md`
— this artifact is orchestrator-owned, not subagent-owned, since the worker has no `Write`
tool.

---
> References: `references/attack-vectors.md`
