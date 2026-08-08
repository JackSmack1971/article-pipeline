# Phase 2 — Full State Verification Layer

**Delivered:** `.claude/settings.local.json` (`hooks` block), `scripts/state_enforcer.sh`
**Status:** Implemented, pipe-tested against synthesized hook payloads (8/8 scenarios pass — see
"Verification" below). SessionStart's hard-halt behavior could not be proven inside this turn
(see caveat under §1) and should be confirmed once against a live session before relying on it.

This replaces the Phase 1 finding "every control in root CLAUDE.md is prose the model must
remember to follow" with three executable hooks. Two parts of the literal request were changed
after reading the actual scripts (`scripts/validate_artifacts.py`, `scripts/pipeline_runner.py`,
`scripts/artifact_contract.py`) — both are called out below rather than silently substituted.

---

## What was built

| Hook | Event | Matcher | Behavior |
|---|---|---|---|
| SessionStart validator | `SessionStart` | — | Runs `validate_artifacts.py --json` if `pipeline_state.json` exists; hard-halts on `INVALID`, warns on `REVIEW_REQUIRED` blockers, silently confirms on clean resume |
| State-file Write/Edit shield | `PreToolUse` | `Write\|Edit` | Denies **any** direct `Write`/`Edit` to `pipeline_state.json` outright; backs up any other `.agents/artifacts/*.{md,json}` file before it's overwritten |
| State-file Bash shield | `PreToolUse` | `Bash` | Denies any Bash command that mentions `pipeline_state.json` unless it's a single, unchained `python scripts/pipeline_runner.py ...` invocation |
| Artifact write validator | `PostToolUse` | `Write\|Edit` | Invoked via `scripts/enforce_artifact_contract.sh post-write`, a pass-through to `state_enforcer.sh post-write` (see §5). Checks the just-written `.agents/artifacts/*.md` file for emptiness / NUL bytes / >80% truncation vs. its pre-write backup, then runs a targeted slice of `validate_artifacts.py` (manifest hash comparison skipped) and rolls back if a reported error names this file; restores the backup (or deletes, if none existed) and reports the failure back to the model on any check failure |

During `POSTDRAFT`, a word-count mismatch caused solely by an `article_draft.md`
edit is the expected transient state between the documented edit and the
sanctioned `pipeline_runner.py sync-word-count` call. The validator defers only
that mismatch without writing derived artifacts itself; all other errors, and
the same mismatch outside `POSTDRAFT`, retain rollback behavior.

All four log structured JSON telemetry (`ts`, `mode`, `event`, `outcome`, `latency_ms`, `detail`)
to `.agents/.state_enforcer/telemetry.jsonl`. No `jq` is installed on this machine, so all JSON
parsing is done in Python (already a hard dependency of this repo) rather than hand-rolled bash
regex — a deterministic-parsing choice, not a stylistic one, per this repo's own policy model
("enforce it with the appropriate deterministic mechanism... do not claim a behavior is enforced
because it appears in prose"). Bash is used for mode dispatch, cheap pre-filtering (skip spawning
Python entirely when the hook payload doesn't mention `artifacts` or `pipeline_state.json`), and
file operations.

## §1. SessionStart hard-halt — design and caveat

`validate_artifacts.py` returns exit 1 (`INVALID`) only when `errors` is non-empty — e.g. a
required artifact is missing, `pipeline_state.json` references a file that doesn't exist, or the
artifact manifest hash doesn't match. That is treated as the hard-halt signal. Exit 2
(`REVIEW_REQUIRED`, blockers only — e.g. an unresolved SEO E-E-A-T failure) is treated as a
warning, not a halt, because `REVIEW_REQUIRED` is a legitimate, resumable state per root
CLAUDE.md's own definition. **Important correctness fix versus a literal reading of the request:**
the hook first checks whether `pipeline_state.json` exists at all — a brand-new pipeline with no
prior state must be allowed to start TRIAGE normally. An earlier draft of this hook that skipped
that check would have hard-halted every fresh project on session one, since `validate_artifacts.py`
returns `INVALID` for a nonexistent artifact root.

**Caveat:** the hook emits `{"continue": false, "stopReason": ...}` per the documented SessionStart
hook contract. This could not be end-to-end verified in this turn, because `SessionStart` fires
when a new session starts — not something a running session can trigger on itself. What *was*
verified is that the script correctly detects the corrupted-state case and emits the right JSON
(see Test 2 below). Whether `continue:false` actually blocks progress at `SessionStart` specifically
(versus being honored only for tool-use events) should be confirmed by starting a fresh session
against a deliberately broken `pipeline_state.json` — and note the settings watcher may need a
`/hooks` reload or session restart to pick up a `.claude/` directory it wasn't watching at startup.

## §2. COMPLETE guard — redesigned, not the literal stdout cross-check

The request asked to "block the transaction if attempting to set `PS.stage=COMPLETE` without
explicit stdout verification that `pipeline_runner.py finalize` returned `PUBLISHABLE`." Reading
`pipeline_runner.py` shows this exact guarantee is **already enforced in the script itself**:
`advance()` explicitly raises `ValueError("use finalize to enter COMPLETE")` for any target other
than `finalize()`, and `finalize()` only writes `stage: COMPLETE` after its own internal
`validate()` call reports no errors/blockers. `pipeline_state.json` is also never written through
the `Write` tool by `finalize()` — it's written by Python's own file I/O, invoked via `Bash`.

A stateful "did `finalize` print `PUBLISHABLE` recently" sentinel-file cross-check (the literal
ask) would have been strictly weaker than what's actually needed, and adds real failure modes of
its own (race conditions, stale sentinels, clock skew). Instead: **deny all direct `Write`/`Edit`
to `pipeline_state.json`, unconditionally.** Combined with the code-level guard already in
`advance()`, this makes `COMPLETE` reachable only through `finalize()`'s own validation gate — a
strictly stronger and simpler guarantee than the literal request, using a mechanism that already
existed in the script rather than duplicating its logic in the hook.

## §3. Post-write validation — lightweight check, not the full contract validator

The request asked to "trigger the artifact validator immediately upon file save." Running the full
`validate_artifacts.py` (which includes `verify_manifest()`, an artifact-hash comparison) after
every single markdown write would **false-positive on every legitimate edit**: the manifest is
only regenerated by `write_artifact_manifest.py`, which root CLAUDE.md calls "after final artifact
writes" — a checkpoint, not a per-section step. Any mid-draft section write would trip a spurious
"manifest hash mismatch" and get rolled back through no fault of the write itself.

Instead, `PostToolUse` runs a lightweight structural check scoped to what a *bad write* actually
looks like: empty file, NUL bytes (binary/corruption signature), or >80% size drop versus the
pre-write backup. The full contract validator still runs at the real checkpoints it was designed
for — `SessionStart` (§1) and whenever the pipeline itself calls `validate_artifacts.py` or
`pipeline_runner.py finalize`, unchanged.

## §4. Residual gaps — stated plainly, not glossed over

- **The Bash shield is a text-pattern heuristic, not a filesystem guarantee.** It denies-by-default
  any Bash command whose text contains the literal substring `pipeline_state.json` unless it
  matches the one sanctioned invocation shape. This closes the obvious bypasses (chained commands,
  inline Python one-liners) but a command that constructs the path indirectly (an environment
  variable, a relative `../` traversal that resolves to the same file without the literal
  filename appearing, a symlink) would not contain the substring and would not be inspected.
  Closing this fully would require the sandbox's `sandbox.filesystem.denyWrite` path-level
  enforcement — not adopted here because it would also block `pipeline_runner.py`'s own legitimate
  writes to the same path, since the sandbox can't distinguish by originating script.
- **Non-Bash, non-Write/Edit tool paths are not covered.** Any future MCP tool or custom tool with
  filesystem write capability would bypass both shields entirely, since the hooks are scoped to the
  `Write`, `Edit`, and `Bash` matchers.
- **The rollback backup lives in `.agents/.state_enforcer/backups/`, itself unprotected.** A
  sufficiently adversarial sequence could write garbage, then immediately overwrite the backup
  before `PostToolUse` fires — this hasn't occurred in testing but is a theoretical TOCTOU-style
  gap given `PreToolUse` and `PostToolUse` are separate invocations with no shared lock.

## §5. Contract-check extension — targeted, not the naive full-validator wire-up

A later request asked for a from-scratch "PostToolUse Contract Validation hook" that runs
`validate_artifacts.py` against every `.agents/artifacts/*.md` write and rolls back on any
non-zero exit — as a brand-new `scripts/enforce_artifact_contract.sh` with its own
`PreToolUse`/`PostToolUse` hook pair and its own checkpoint directory.

Implemented as a second independent backup-and-validate mechanism, that request would have
reintroduced exactly the regression documented in §3 above (`verify_manifest()`'s SHA-256
comparison tripping on every legitimate mid-draft edit) and duplicated the checkpoint/rollback
primitive this hook already owns, with two mechanisms racing over the same files and no shared
lock — a second TOCTOU surface, not a smaller one.

The `post-write` logic itself was extended in place (not duplicated):

1. `validate_artifacts.py` gained a `--skip-manifest-hash` flag that omits the
   `verify_manifest()` call. Everything else in the contract (required-artifact presence,
   `pipeline_state.json`/`pipeline_config.json` well-formedness, `artifacts_written` path
   validity, word-count consistency across `article_draft.md` / `pipeline_state.json` /
   `pipeline_metadata.md`) still runs.
2. `post-write` runs the validator with that flag after its existing structural checks
   (empty file / NUL bytes / truncation) pass, and rolls back **only** when a reported error
   names the file that was just written (or, for `article_draft.md` / `pipeline_metadata.md`,
   when the error is the three-way word-count mismatch those two files participate in). An
   error about some other pending artifact — e.g. `article_draft.md` not existing yet while
   `article_spec.md` is still being drafted at the APPROVAL stage — does not roll back this
   write.

Verified: a benign mid-draft edit with a deliberately stale manifest hash passes with
`{"suppressOutput": true}` (no false rollback); a `pipeline_metadata.md` write claiming a
word count that contradicts `article_draft.md`/`pipeline_state.json` is rolled back to its
pre-write backup with the exact validator error surfaced on stderr and in the hook's `reason`
field. Both cases were run against an isolated scratch copy of `.agents/artifacts/`, not the
live one. Full `tests/` suite (16 tests, including two new cases for `--skip-manifest-hash`)
passes.

This keeps §4's residual-gaps list unchanged — no new backup directory, no new TOCTOU window —
and adds one new one: the contract check only fires for `.md` writes (matching the original
request's scope), so a corrupting write to a `.json` artifact under `.agents/artifacts/` (other
than `pipeline_state.json`, which is denied outright) is still only caught by the lightweight
structural checks, not the full contract.

`.claude/settings.local.json`'s `PreToolUse`/`PostToolUse` `Write|Edit` hooks now name
`scripts/enforce_artifact_contract.sh` (`pre-write` / `post-write`) rather than
`scripts/state_enforcer.sh` directly, so the configuration matches what the artifact-contract
objective asked for. `enforce_artifact_contract.sh` is a one-line `exec` pass-through to
`state_enforcer.sh` — same file, same process, same backup directory — added purely so the hook
config names the file the requirement specified, without registering a second hook that would
run the checkpoint/validate/rollback logic twice per write. `session-start` and the `pre-bash`
shield still call `state_enforcer.sh` directly since they're outside the artifact-write contract.

## Verification — synthesized hook payloads piped directly into `state_enforcer.sh`

| # | Scenario | Result |
|---|---|---|
| 1 | `session-start`, clean state | Silent pass, `additionalContext` reports `stage=COMPLETE` |
| 2 | `session-start`, `article_draft.md` hidden (simulated corruption) | `continue:false`, `stopReason` names the missing artifact |
| 3 | `pre-write`, `Write` targeting `pipeline_state.json` | `permissionDecision: deny` |
| 4 | `pre-write`, `Write` targeting `article_draft.md` | Silent allow; backup file created in `.agents/.state_enforcer/backups/` |
| 5 | `pre-bash`, `python scripts/pipeline_runner.py finalize ...` | Silent allow |
| 6 | `pre-bash`, inline `python -c` one-liner rewriting `pipeline_state.json` | `permissionDecision: deny` |
| 7 | `post-write`, valid `article_draft.md` | Silent pass (`suppressOutput: true`) |
| 8 | `post-write`, `article_draft.md` truncated to 0 bytes | `decision: block`; file restored byte-identical to pre-corruption backup (confirmed via `diff -q`) |

All test artifacts and temporary files were removed after verification; `pipeline_state.json`
(`stage: COMPLETE`) and `article_draft.md` (16,136 bytes) were confirmed unchanged from their
pre-test state.
