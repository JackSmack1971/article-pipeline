# Article Pipeline — Claude Code orchestration repo

This is not a conventional Python application. It is a **Claude Code orchestration repo**: a
`CLAUDE.md`-driven pipeline for producing research-backed long-form articles, plus a set of
Python scripts and Claude Code hooks that make parts of that pipeline's contract *deterministic*
instead of purely prose-enforced.

There is no server, no build, no package to `pip install`. "Running" this project means opening
the repo in Claude Code and letting it follow `CLAUDE.md`.

## What actually orchestrates a run

The orchestrator is **Claude Code itself**, following the state machine described in
[`CLAUDE.md`](CLAUDE.md):

```
TRIAGE → RESEARCH → FACTCHECK → APPROVAL → DRAFT → POSTDRAFT → SEO → LEARNING → COMPLETE
```

Each stage is a `.claude/skills/*` skill invoked by the Claude Code session (see
`.claude/skills/multi-agent-article-pipeline/SKILL.md` for the full composition, and
`.claude/agents/*.md` for the advocate/skeptic/red-team subagents used for adversarial
isolation). All of that control flow — which skill runs next, how gates are presented, how
revision cycles are counted — lives in `CLAUDE.md` prose and skill definitions, not in a Python
scheduler. There is no `scripts/workflow.py` or `orchestration/workflow.json` in this repo;
if you find a reference to either elsewhere in this repo's docs, treat it as aspirational/stale,
not as describing code that exists here.

## What Python owns

Python does **not** orchestrate the pipeline. It enforces the parts of the contract that must
hold regardless of model judgment, per this repo's own policy model ("treat prompt instructions
as guidance and executable controls as enforcement" — `CLAUDE.md`):

| Script | Owns |
|---|---|
| `scripts/artifact_contract.py` | Shared deterministic rules: word counts, E-E-A-T status extraction, manifest hashing |
| `scripts/validate_artifacts.py` | Read-only contract check over a run in `.agents/artifacts/` → `PUBLISHABLE` \| `REVIEW_REQUIRED` \| `INVALID` |
| `scripts/pipeline_runner.py` | The **only** sanctioned path to mutate `pipeline_state.json` (gate decisions, stage advance, `finalize()` → `COMPLETE`) |
| `scripts/migrate_pipeline_state.py` | Schema migration for `pipeline_state.json` (legacy → current) |
| `scripts/write_artifact_manifest.py` | Writes the artifact hash manifest used by the validator |
| `scripts/state_enforcer.sh`, `scripts/enforce_artifact_contract.sh` | Hook entry points (see below) |

These scripts have **no third-party dependencies** — stdlib only. `pytest` (see
`requirements.txt`) is a dev-only dependency, needed to run the test suite / `make verify`, not
to run the pipeline itself.

## How hooks are activated

Claude Code hook registration lives in [`.claude/settings.json`](.claude/settings.json), which is
**committed** — this is what makes the enforcement reproducible from a clean clone. It wires:

- `SessionStart` → `scripts/state_enforcer.sh session-start` — validates `pipeline_state.json` on
  resume, hard-halts on a corrupted/invalid contract.
- `PreToolUse` (`Write|Edit`) → `scripts/enforce_artifact_contract.sh pre-write` — checkpoints the
  write target.
- `PreToolUse` (`Bash`) → `scripts/state_enforcer.sh pre-bash` — denies Bash commands that would
  touch `pipeline_state.json` outside the sanctioned `pipeline_runner.py` path.
- `PostToolUse` (`Write|Edit`) → `scripts/enforce_artifact_contract.sh post-write` — structural
  validation and rollback of just-written artifacts.

See `diagnostics/002-state-verification-layer.md` for the full design rationale and known gaps.

`.claude/settings.local.json` is **not** committed (it's git-ignored by convention, for
per-developer permission allowlists) and must never be the only place a hook is registered —
anything that needs to survive a clean clone belongs in `.claude/settings.json`.

## How to verify the checkout

```sh
make verify
# or directly:
bash scripts/verify.sh
```

This checks hook script syntax, validates `.claude/settings.json` as JSON, and runs the Python
test suite (`pytest tests/`). It does **not** run `scripts/validate_artifacts.py` — that command
checks the state of a specific, in-progress article-pipeline run under `.agents/artifacts/`, not
the correctness of the checkout. Run it yourself when you actually have a pipeline run to check:

```sh
python scripts/validate_artifacts.py --json
```

## Which artifacts are canonical vs. historical

**Canonical (live, read by the pipeline and its hooks):**
- `.agents/artifacts/*` — the persisted state of the current/most recent pipeline run
  (`pipeline_state.json`, `pipeline_config.json`, research/draft/SEO artifacts, etc.). Owned per
  the table in `CLAUDE.md`'s "Artifact Ownership" section.
- `schemas/*.schema.json` — JSON Schemas the artifact contract is checked against.
- `.claude/settings.json` — committed hook registration.

**Historical (point-in-time reports, not re-run or re-validated automatically):**
- `diagnostics/*.md` — forensic audit / design write-ups from specific past sessions. Read them
  for rationale; don't assume they describe the current code without checking.
- `blueprint.md` — a dated improvement proposal, explicitly marked "proposal, not yet
  implemented" at the top of the file.
- `evals/article_pipeline/*` — a fixed evaluation corpus, not regenerated per run.

If a historical document and the actual code disagree, the code wins — this is the same
"executable behavior outranks prose" principle `CLAUDE.md` applies to itself.
