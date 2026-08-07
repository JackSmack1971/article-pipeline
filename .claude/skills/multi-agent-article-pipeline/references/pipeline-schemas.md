# Pipeline Schemas — v4 Artifact Contracts

Machine-checkable JSON Schema for every artifact below lives in `schemas/` at
the repo root (`pipeline_config.schema.json`, `pipeline_state.schema.json`,
`conflict_decisions.schema.json`, `artifact_manifest.schema.json`). Each JSON
artifact now carries a `schema_version` field; this document is the prose
companion, not a second source of truth — if the two disagree, `schemas/`
wins.

## pipeline_config.json

Written by `article-complexity-triage` at Step 0. Read by all subsequent skills.
`schema_version: 1`.

```json
{
  "schema_version": 1,
  "pipeline": {
    "depth": "SIMPLE|STANDARD|COMPLEX",
    "adversarial_dialectic": true,
    "red_team": false,
    "fact_check": true,
    "seo_pass": true,
    "token_budget": 32000,
    "topic_brief": "<verbatim user input>",
    "thesis": "<extracted thesis, one sentence>",
    "thesis_confidence": "HIGH|MEDIUM",
    "novelty_score": 3,
    "contentiousness_score": 4,
    "scope_score": 2,
    "composite_score": 3.1,
  "budget_adjusted": false,
  "budget_adjustment_reason": null,
  "word_count_method": "canonical_markdown_tokens",
  "routed_at": "2026-04-08T12:00:00Z",
  "author": {
    "name": null,
    "credential": null,
    "affiliation": null
  }
  }
}
```

**Field rules:**
- `depth`: SIMPLE (1.0–2.4) | STANDARD (2.5–3.7) | COMPLEX (3.8–5.0)
- `fact_check`: always false for SIMPLE, always true for STANDARD/COMPLEX
- `red_team`: only true for COMPLEX
- `token_budget`: 24000 / 32000 / 48000 base; +8000 if KC-1 history detected
- `word_count_method`: `canonical_markdown_tokens`; use `scripts/artifact_contract.py`
  for the persisted draft count rather than a separate SEO or prose count.
- `budget_adjusted`: true if base was incremented; `budget_adjustment_reason` explains why
- `author`: optional, all fields nullable. TRIAGE always writes this object — populated from
  a project-level default if the user has declared one (see
  `article-complexity-triage/SKILL.md` Step 4), otherwise left explicitly `null`. A `null`
  value written by TRIAGE means "no author declared, by project convention" — a known,
  legitimate state, not a missing-data error. `article-seo-optimizer`'s E-E-A-T audit branches
  on this: populated → check credential/affiliation signals; explicitly `null` → note the gap
  once without prompting the user, since the absence was already a declared decision.

---

## conflict_decisions.json

Written by orchestrator after Approval Gate `approved` response. Read by @engineer before drafting.
`schema_version: 1`.

```json
{
  "schema_version": 1,
  "decisions": [
    {
      "conflict_id": "C-1",
      "research_vector": "<vector name>",
      "advocate_claim_id": "ADV-3",
      "skeptic_claim_id": "SKP-2",
      "axis": "empirical|definitional|temporal|methodological|interpretive",
      "handling": "neutral|author_position|unresolved",
      "position": "advocate|skeptic|null",
      "note": "<optional human clarification>"
    }
  ],
  "default_handling": "neutral",
  "approved_at": "2026-04-08T13:00:00Z",
  "revision_cycle": 0
}
```

**Field rules:**
- `handling`: `neutral` = present both positions; `author_position` = take a side; `unresolved` = flag explicitly
- `position`: required if `handling = author_position`; null otherwise
- `default_handling`: "neutral" — applied to any conflict not individually specified
- `revision_cycle`: increments on each `revise:` response at Approval Gate

---

## pipeline_state.json

Owned exclusively by `scripts/pipeline_runner.py`. `schema_version: 2` is the
only shape new runs may use — full field definitions are in
`schemas/pipeline_state.schema.json`.

```json
{
  "schema_version": 2,
  "stage": "COMPLETE",
  "gate_history": [
    {"gate": "TRIAGE_THESIS_CONFIRM", "decision": "confirmed", "thesis_confidence": "MEDIUM"},
    {"gate": "APPROVAL", "decision": "approved", "conflict_decisions_file": "conflict_decisions.json"}
  ],
  "revision_cycles": {"APPROVAL": 0},
  "kc_events": [{"code": "KC-3", "status": "PASS", "detail": "max single-source share 10%"}],
  "gate_expedite_count": 0,
  "consecutive_blocked_audits": 0,
  "tool_degradation": [],
  "draft": {"word_count": 2291},
  "eeat": {"status": "PASS", "reason": null},
  "artifacts_written": ["pipeline_config.json", "..."]
}
```

**Field rules — this is the one place counters and telemetry live:**
- `gate_history`, `revision_cycles`, `kc_events`, `gate_expedite_count`, and
  `consecutive_blocked_audits` are always top-level. There is no nested
  `telemetry` object and no separate `gates` array — schema_version 1
  (pre-freeze) runs used that legacy shape; it is frozen historical data only.
- `kc_events` items use `code`/`status` (not the legacy `check`/`result`).
- A `pipeline_state.json` missing `schema_version`, or carrying a legacy
  `telemetry`/`gates` key, is refused by `pipeline_runner.py`'s `load_state()`
  with an explicit error pointing at the migration command below — the
  runner will not silently interpret an ambiguous shape.
- Migrate a legacy file with: `python scripts/pipeline_runner.py migrate-state
  --artifact-root .agents/artifacts --json` (backed by
  `scripts/migrate_pipeline_state.py`). This is the only sanctioned mutation
  path per the `.claude/settings.local.json` state-file shield, and it
  regenerates `artifact_manifest.json` afterward.
- `eeat`: optional, `{status: "PASS"|"FAIL"|"NA", reason: string|null}`. Written by
  `pipeline_runner.py::sync_eeat_status` (called from `finalize()`), parsed structurally from
  `seo_package.md`'s "E-E-A-T block present" checklist row rather than left for
  `validate_artifacts.py` to infer from prose. Absent when `seo_package.md` doesn't exist yet
  or `seo_pass` is disabled. `status: FAIL` is the `UNRESOLVED_EDITORIAL_RISK` blocking
  condition below.

---

## Persisted run contract

`scripts/pipeline_runner.py` owns persisted stage transitions and finalization;
`scripts/validate_artifacts.py` is the canonical final gate. It uses the same
word-count function as `scripts/write_artifact_manifest.py`, verifies
`artifact_manifest.json` hashes (`schema_version: 1`,
`schemas/artifact_manifest.schema.json`), and returns structured conditions:

- `REQUIRED_INPUT` and `UNRESOLVED_EDITORIAL_RISK` block publication.
- `OPTIONAL_METADATA` and `TOOL_DEGRADED` are review-only when explicitly
  declared by the route or tool-availability fields.

The runner must run the validator after the final artifact write and before
the final state write. It may write `COMPLETE` only on `PUBLISHABLE`; otherwise
it writes `REVIEW_REQUIRED`. A manifest is invalidated by any later artifact
edit and must be regenerated before completion.

`finalize()` is the single derived-artifact reconciliation authority: it
recomputes every value derived from `article_draft.md` — canonical word count
and structured E-E-A-T status — and writes them into `pipeline_state.json`,
`pipeline_metadata.md`, and `seo_package.md` *before* regenerating
`artifact_manifest.json` and calling the validator:

```
article_draft.md → derive canonical values → state / metadata / SEO → manifest → validator → COMPLETE
```

This is deterministic given unchanged source artifacts, so calling `finalize`
twice in a row produces the same tree. `validate_artifacts.py` cross-checks
every derived representation (`draft`, `state`, `metadata`, `seo` word counts;
`pipeline_state.json['eeat']` vs. `seo_package.md`'s checklist row) and errors
on any disagreement rather than silently trusting one of them.

---

## Kill Switch Conditions — v4

| Code | Trigger | When Checked |
|------|---------|--------------|
| KC-1 | Token utilization > 85% BEFORE Step 3 | Post-research, pre-draft |
| KC-2 | Third non-substantive revision at Approval Gate | Step 2 |
| KC-3 | Single source > 40% of all extracted claims | End of @synthesizer Phase 3 |
| KC-4 | @engineer fails inline audit 2× on same section | Step 3 loop |
| KC-5 | Token utilization > 85% DURING Step 3 (mid-draft) | After each section in Step 3 loop |
| KC-6 | > 50% of research vectors classified [INSUFFICIENT] | End of @synthesizer Phase 3 |

KC-5 adds mid-draft protection that KC-1 cannot provide (KC-1 only fires pre-draft).
KC-6 catches breadth failure before it becomes a drafting quality problem.

---

## Artifact Map — All Pipeline Outputs

| Artifact | Written By | Read By |
|----------|-----------|---------|
| `pipeline_config.json` | @triage | all skills |
| `pipeline_state.json` | @runner | @runner (all stages) |
| `advocate_context.md` | @advocate | @skeptic (URLs only), @synthesizer |
| `skeptic_evidence.md` | @skeptic | @synthesizer |
| `research_context.md` | @synthesizer | @summarizer, @fact-checker, @engineer (on-demand) |
| `research_context_summary.md` | @summarizer | @engineer (primary), @qa |
| `article_spec.md` | @synthesizer | @engineer, @qa, @reader, @seo-optimizer |
| `conflict_register.md` | @synthesizer | human (Approval Gate) |
| `fact_check_report.md` | @fact-checker | @engineer, @qa |
| `dispute_register.md` | @fact-checker | human (Approval Gate, if > 3 disputes) |
| `conflict_decisions.json` | @runner / orchestrator | @engineer |
| `article_draft.md` | @engineer | @qa, @adversary (conclusion only), @reader, @seo-optimizer |
| `pipeline_metadata.md` | @engineer | human (internal run record — never merged into draft) |
| `audit_log.md` | @qa (inline) | @runner |
| `audit_report.md` | @qa (holistic) | @runner |
| `red_team_report.md` | @adversary | human |
| `reader_questions.md` | @reader | human |
| `seo_package.md` | @seo-optimizer | human |
| `pipeline_learnings.md` | @qa | @triage (next run) |
