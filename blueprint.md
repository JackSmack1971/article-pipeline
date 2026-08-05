# Blueprint: Article Pipeline Framework Improvements

**Status:** proposal, not yet implemented.
**Basis:** live inspection of `.claude/skills/**`, `scripts/**`, `CLAUDE.md`, `AGENTS.md`, and the
one completed run currently sitting in this repo (`.agents/artifacts/`, trace `CCUK5X`), including
its self-reported `pipeline_learnings.md` findings and the artifact validator's current output.

Every item below follows this checklist (per `AGENTS.md` §3/§16, adapted for this Claude-facing
document): **Observed failure → Likely cause → Intervention → Placement → Risk → Validation.**
Findings are ranked by evidence strength — proven live bugs first, then structural risks, then
already-self-documented gaps, then hygiene.

---

## 0. How this was derived

This is not a speculative audit. Three sources of ground truth were used:

1. **The validator's live output.** Running `python scripts/validate_artifacts.py --json` against
   the current `.agents/artifacts/` reports the run as `REVIEW_REQUIRED` today, with a concrete,
   reproducible error — not a hypothetical.
2. **The pipeline's own retrospective.** The last run wrote two structured findings into
   `pipeline_learnings.md` and `.agents/knowledge/article-pipeline/{pitfall,context}/` — the
   system already diagnosed two of its own gaps. This blueprint operationalizes those diagnoses
   instead of re-discovering them.
3. **Architecture comparison against this repo's own meta-skills** (`writing-great-claude-subagents`,
   `writing-great-workflows`) — the project's own stated standards for when isolation, deterministic
   code, and prompt-based enforcement are each appropriate.

---

## 1. Deterministic state mutation is missing — proven by a live bug

**Observed failure:** `python scripts/validate_artifacts.py --json` currently returns:

```json
"errors": ["word-count mismatch: {'draft': 2291, 'state': 1983, 'metadata': 2151}"]
```

Three artifacts (`article_draft.md`, `pipeline_state.json.draft.word_count`,
`pipeline_metadata.md`) each carry a different word count for the same delivered article. This is
why the run sits at `REVIEW_REQUIRED` instead of `COMPLETE` right now.

**Likely cause:** `pipeline_state.json.draft.word_count` and the metadata line are written by hand
(as prose instructions tell the model to write them) at whatever moment drafting first finishes.
POSTDRAFT revisions (red-team "address" revised a section; reader-sim "polish" revised three
sections — both recorded in `pipeline_state.json.postdraft`) changed `article_draft.md` afterward,
but nothing re-derived the two dependent counts. There is exactly one canonical counting function
(`artifact_contract.canonical_word_count`), but three independent write sites, and no code path
forces the dependents to stay in sync with the source of truth.

**Intervention:** Add a `sync` subcommand to `scripts/pipeline_runner.py`:

```python
def sync_word_count(root: Path) -> dict:
    """Recompute canonical word count from article_draft.md and write it into
    pipeline_state.json and the 'Final word count' line in pipeline_metadata.md."""
```

Call it automatically at the end of `finalize()`, and require every workflow step that edits
`article_draft.md` after initial drafting (POSTDRAFT "address"/"polish" revisions, any future
polish pass) to call `pipeline_runner.py sync-word-count` before proceeding, the same way they
already call `validate_artifacts.py`.

**Placement:** `scripts/pipeline_runner.py` (deterministic code, per `AGENTS.md` §9 — this is
exactly a case where "code should make a decision the model should not have to remake turn by
turn," per `writing-great-workflows`). Reference the new subcommand from
`multi-agent-article-pipeline/SKILL.md` Step 4 ("address"), Step 5 ("polish"), and Step 7
(finalize).

**Risk:** Low. This is additive and strictly narrows an existing failure mode; it cannot make a
passing run fail. The only risk is scope creep if `sync` is asked to do more than recompute one
number — keep it to word count only.

**Validation:** Add `tests/test_pipeline_runner.py::test_sync_word_count_reconciles_all_three`
that seeds mismatched values, calls `sync_word_count`, and asserts all three converge. Then run
`python scripts/validate_artifacts.py --json` against the *actual current* `.agents/artifacts/`
run and confirm the mismatch error disappears — this is a real regression fix, not just a new
test, since the repo currently has a broken run sitting in it.

---

## 2. Adversarial "isolation" is prompt-enforced, not capability-enforced

**Observed failure:** `CLAUDE.md`'s hard constraints require that "skeptic may read advocate's
Source URL Index only, never `advocate_context.md`" and that red-team "never see the full
`AD`, only thesis + conclusion." But `.claude/agents/` does not exist in this repository —
confirmed by directory listing. Every persona (`@advocate`, `@skeptic`, `@synthesizer`,
`@engineer`, `@qa`, `@adversary`, `@reader`, `@seo-optimizer`) is a role the *same* Claude Code
session simulates in sequence, inside one shared context window. `CLAUDE.md` itself hedges this:
*"Where Claude Code supports independent subagents, run advocate and skeptic as separate agents
with isolated context. Otherwise preserve the same information boundary manually."* Claude Code
does support this (project subagents via `.claude/agents/` + the `Agent` tool) — it's simply not
wired up. The isolation the pipeline's entire epistemic design depends on ("skeptic must not
anchor on advocate's framing," "red-team must not anchor on the author's argument") is currently
a **prose instruction inside the same context that already contains the forbidden content**, not
a structural barrier.

**Likely cause:** The pipeline was built skill-first (reusable procedures the orchestrating
session follows) before subagent isolation was wired in. This is a reasonable v1 default, but
this repo's own `writing-great-claude-subagents/SKILL.md` names exactly this situation as the
first-order reason to use a subagent: *"Context isolation is the point... adversarial
independence"* is one of its named triggers, and its failure-mode list calls this pattern out
directly: *"Prompt enforcement — a prose prohibition is mistaken for a hard control."*

**Intervention:** Introduce three project subagents, each with a narrow, capability-scoped
surface (not just an instruction) so the boundary is enforced by what the worker *can reach*,
not by what it's told not to look at:

- `.claude/agents/article-advocate.md` — tools: `WebSearch`, `Write` (scoped to
  `advocate_context.md`). No `Read` on any prior-run artifact.
- `.claude/agents/article-skeptic.md` — tools: `WebSearch`, `Read` (only the Source URL Index
  section — pass it in the delegation prompt rather than granting file access to
  `advocate_context.md` at all), `Write` (scoped to `skeptic_evidence.md`).
- `.claude/agents/article-red-team.md` — tools: `WebSearch` only, no `Read` at all. The
  orchestrator passes the thesis + conclusion text directly in the delegation prompt; the worker
  has no filesystem path to `article_draft.md` even if it wanted one.

Keep `@synthesizer`, `@summarizer`, `@fact-checker`, `@engineer`, `@qa`, `@reader`,
`@seo-optimizer` as in-context skill executions — they legitimately need broad read access to
prior artifacts, and per `writing-great-claude-subagents`, isolation is only worth its "fresh
context tax" when it earns something. For those roles it wouldn't.

**Placement:** New files under `.claude/agents/`. Update
`article-research-dialectic/SKILL.md` Phase 2a/2b and `article-red-team/SKILL.md` to say
"delegate to the `article-advocate`/`article-skeptic`/`article-red-team` subagent" instead of
"operate as @advocate." `multi-agent-article-pipeline/SKILL.md` Steps 1 and 4 get the same
update.

**Risk:** Medium. Subagents don't inherit the parent transcript, so each delegation prompt must
carry every fact the worker needs (research vectors, thesis, output path) explicitly — a context
assumption bug here would silently degrade research quality rather than error loudly. Mitigate by
keeping the delegation prompt template in the calling skill file, reviewed alongside this change,
and by running a real triage→research pass afterward to confirm output artifacts still match the
existing schema in `pipeline-schemas.md`.

**Validation:** No automated test can verify "the skeptic never saw X" from outside the model, but
the capability boundary itself is checkable: confirm the `article-skeptic` agent definition has no
`Read` grant reaching `advocate_context.md`, and manually diff one adversarial research run's
output against a baseline (pre-change) run on the same topic brief to confirm evidence quality
doesn't regress (per `writing-great-claude-subagents`'s "boundary check" + "outcome check").

---

## 3. Gate/KC counters are hand-edited JSON, not script-owned state

**Observed failure:** The same root cause as Finding 1, generalized. `pipeline_state.json` fields
like `gate_expedite_count`, `consecutive_blocked_audits`, `revision_cycles`, and `kc_events` are
written by the model directly editing JSON, per prose instructions ("increment
`gate_expedite_count`", "REVISION_COUNT += 1"), with the hard limits (max 3 revision cycles, 2
consecutive `SECTION BLOCKED` before KC-4, 3 consecutive `BLOCKED` audits before HALT) enforced
only by the model correctly doing arithmetic inside a long session. `scripts/pipeline_runner.py`
today only owns `advance` (stage transition) and `finalize` — it has no subcommand for the
counters that actually gate HALT/escalate behavior.

**Likely cause:** `advance`/`finalize` were built for the two structurally simplest transitions
(stage, and terminal validation). The counters accumulated organically as `CLAUDE.md`'s hard
constraints grew, without a matching script surface.

**Intervention:** Add `pipeline_runner.py record-gate`, `record-kc-event`, and
`increment-revision --gate <name>` subcommands. Each validates against the same fixed thresholds
`CLAUDE.md` already states (max 3 gate revisions → refuse and report `HALT_REQUIRED`; 3rd
consecutive `BLOCKED` → same) and writes atomically, the same pattern `advance()` already uses.
This turns "the model must remember to check `revision_cycles >= 3`" into "the script refuses the
4th call and returns the halt signal" — moving an *objective* rule from prose into code, per
`AGENTS.md` §9's own distinction between deterministic checks and editorial judgment.

**Placement:** `scripts/pipeline_runner.py`, mirrored by a short update to `multi-agent-article-pipeline/SKILL.md`'s
gate sections replacing "increment X in `PS`" language with "call `pipeline_runner.py record-gate
...`".

**Risk:** Low-medium. Overly rigid validation could reject a legitimate edge case (e.g., a gate
name typo blocking a real advance). Keep the subcommand's own error messages actionable and let
`REVIEW_REQUIRED` stay reachable manually as an escape hatch, matching the existing
`ALLOWED_NEXT["REVIEW_REQUIRED"]` design.

**Validation:** Unit tests analogous to the existing `test_invalid_transition_is_rejected`: seed 3
prior revision cycles, assert the 4th `increment-revision` call raises/returns a halt status
rather than silently incrementing to 4.

---

## 4. Spec staleness after fact-check upgrades — already self-diagnosed

**Observed failure:** Documented by the pipeline itself in
`.agents/knowledge/article-pipeline/pitfall/article_20260803T000000Z.md`: a claim
(`ADV-10`) was marked excluded in `article_spec.md`'s Key Claims notes at spec-approval time, then
later upgraded to `VERIFIED-UPDATED` by fact-check. `claims_for_drafting.md` reflected the
upgrade; `article_spec.md` did not. The engineer resolved it correctly this time by treating
`claims_for_drafting.md` as authoritative and documenting the reasoning inline — but only because
the model re-derived the precedence rule from first principles mid-run.

**Likely cause:** `article_spec.md` is written once (Step 1, by `@synthesizer`) before
`FACTCHECK` runs (Step 1.5); nothing back-patches it afterward, and no instruction states
precedence explicitly ahead of time.

**Intervention:** The pipeline's own recommendation (option b, the cheaper of the two it proposed)
is correct and should be adopted as written: state explicitly, once, at the Step 3 drafting
kickoff in `multi-agent-article-pipeline/SKILL.md`, that `claims_for_drafting.md` supersedes
`article_spec.md`'s Key Claims exclusion notes on any conflict. This is a one-sentence addition,
not new machinery — per `AGENTS.md` §3, prefer the smallest effective change, and a deterministic
back-patch script (option a) is not justified by a single observed instance.

**Placement:** `multi-agent-article-pipeline/SKILL.md` Step 3 preamble (`@engineer reads:`
section) and `article-qa-auditor/SKILL.md`'s `@engineer Drafting Mode` section, where the read
order is already specified.

**Risk:** Very low. Pure clarification, no behavior change to any artifact schema.

**Validation:** None needed beyond review — this is a prose precision fix, not a code change. If
it recurs a third time despite the explicit precedence statement, escalate to a deterministic
check (scan `article_spec.md` claim-exclusion notes against `claims_for_drafting.md` verdicts in
`validate_artifacts.py`, surfaced as a review-only condition).

---

## 5. SEO E-E-A-T author check is structurally unsatisfiable — already self-diagnosed

**Observed failure:** Documented in
`.agents/knowledge/article-pipeline/context/article_20260803T000000Z.md`: `article-seo-optimizer`'s
On-Page Checklist item 17 requires an author name/credential, but no artifact in the pipeline
carries one, and `CLAUDE.md` correctly forbids fabricating one. The check fails identically on
every run, consuming a gate interaction each time to tell the user the same thing.

**Likely cause:** No `author` field exists anywhere in the schema
(`pipeline-schemas.md`'s `pipeline_config.json` contract has no such field).

**Intervention:** Add an optional `author` object (`name`, `credential`, `affiliation`, all
nullable) to `pipeline_config.json`, populated at TRIAGE from a project-level default (a new,
short section in `CLAUDE.md` or a sibling config file the user fills in once) if the user has one,
else left explicitly `null`. `article-seo-optimizer/SKILL.md`'s E-E-A-T audit then treats "author
field present and populated" vs. "author field explicitly absent by project convention" as two
different, both-legitimate states — only the latter produces the "Gaps" note, and it does so
without prompting the user mid-pipeline, since the absence was already a known, declared decision
rather than a surprise rediscovered every run.

**Placement:** Schema addition in `references/pipeline-schemas.md`, triage write logic in
`article-complexity-triage/SKILL.md` Step 4, read/branch logic in
`article-seo-optimizer/SKILL.md`'s E-E-A-T Audit section.

**Risk:** Low. Purely additive field; absence behaves exactly as today.

**Validation:** Run SEO pass twice — once with `author` populated (confirm all four E-E-A-T
signals can now pass), once with it left `null` (confirm the existing documented-gap behavior is
preserved, not silently suppressed).

---

## 6. Persona rules are duplicated across two files — instruction entropy

**Observed failure:** `article-research-dialectic/references/personas.md` restates each
persona's hard constraints (e.g., @skeptic's URL-only access rule, @engineer's citation format,
@qa's severity taxonomy) in near-full at `multi-agent-article-pipeline/references/personas.md`,
while the *operational* version of the same rules already lives in each skill's own `SKILL.md`
(which is what's actually loaded when that skill executes). Two documents now state the same hard
constraints with no cross-reference, which `writing-great-claude-subagents/SKILL.md` names
directly as **replica drift**: "the same rule exists in `CLAUDE.md`, a skill, the agent body...
pick one source of truth and point to it from the others."

**Likely cause:** `personas.md` was written as a single-file persona reference before each
persona's constraints were also folded into its own `SKILL.md` for operational use; nothing was
pruned afterward.

**Intervention:** Keep each skill's own `SKILL.md` as the canonical, operationally-loaded source
for that persona's hard constraints (it's what's actually read at execution time). Trim
`personas.md` to a short cross-reference table: persona name, one-line role, output artifact, and
a pointer to the owning `SKILL.md` — not a restatement of the constraints themselves.

**Placement:** `.claude/skills/multi-agent-article-pipeline/references/personas.md`.

**Risk:** Very low — this is a deletion/consolidation, not new behavior. The only risk is
removing a constraint that exists *only* in `personas.md` and nowhere else; diff both files
line-by-line before trimming to confirm nothing is orphaned.

**Validation:** Re-run one pipeline stage per trimmed persona (or at minimum re-read the shortened
file) to confirm the cross-reference table still gives the orchestrator enough to route correctly
— this is a documentation change, so review is the validation.

---

## What was checked and found already sound (no action)

- **SIMPLE-depth ceremony:** already lean — skips adversarial dialectic, fact-check stays
  optional per triage, red-team is COMPLEX-only, mini-audit replaces full holistic. No forced
  fields observed. Matches `AGENTS.md` §11's proportionality standard; no change recommended.
- **Deterministic-vs-editorial split in `validate_artifacts.py`:** already well-drawn — it checks
  objective things (missing files, hash mismatches, word-count consistency, TODO markers) and
  explicitly leaves subjective quality to the audit skills. This is the right pattern; Findings 1
  and 3 above extend it rather than replace it.
- **Kill-condition design (KC-1..6):** thresholds and check points are specific and testable in
  principle; the gap is *enforcement location* (Finding 3), not the rule design itself.

---

## Suggested implementation order

1. **Finding 1** (word-count sync) — fixes the repo's actual current broken state; smallest,
   highest-confidence change.
2. **Finding 4** (spec precedence sentence) — near-zero cost, already fully specified by the
   pipeline's own retrospective.
3. **Finding 5** (author field) — small schema addition, already fully specified.
4. **Finding 3** (script-owned counters) — moderate effort, generalizes Finding 1's fix.
5. **Finding 2** (real subagent isolation) — highest effort and highest architectural payoff;
   do this once the deterministic-state work (1, 3) is in place, since subagent delegation will
   also need to call the same `pipeline_runner.py` state-mutation commands from outside the main
   session's own context.
6. **Finding 6** (persona doc consolidation) — do last, opportunistically, once Finding 2 has
   settled what each `SKILL.md`'s canonical constraint text should say.
