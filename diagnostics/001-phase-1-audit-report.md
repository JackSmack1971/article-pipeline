# Phase 1 Forensic Audit — `.claude/` Control Plane

**Scope:** `C:\TEST repos\article pipeline\.claude\` (project-level config directory)
**Method:** Read-only inspection (Read/Glob/Grep/Bash-listing only). No files modified, no
state-changing commands executed. 28 files enumerated, agent/skill frontmatter and reference
docs read in full or in representative excerpt.
**Note on framing:** this repo's own root `CLAUDE.md` already states an explicit policy
model for exactly this kind of audit — "treat prompt instructions as guidance and executable
controls as enforcement... verify the executable path and realistic bypass paths." This
report follows that standard rather than taking skill/agent prose at face value.

---

## 1. Context Management — Grade: **C**

**Inventory**

| Mechanism | Present? | Evidence |
|---|---|---|
| `.claudeignore` | **Absent** | No file at repo root or in `.claude/` |
| `.gitignore` at project root | **Absent** | Only `.pytest_cache/.gitignore` and a stray `.gitignore.check` exist; nothing governs `.agents/artifacts/` despite CLAUDE.md's "ephemeral artifacts must remain untracked by git" requirement |
| Model-invoked skill descriptions | 12 skills, all with rich trigger phrasing | `.claude/skills/*/SKILL.md` frontmatter |
| `disable-model-invocation` used to cut always-loaded cost | Yes, on 5 reference/meta skills | `writing-claude-code-rules`, `writing-great-claude-subagents`, `writing-great-skills`, `writing-great-workflows` |
| Progressive disclosure (SKILL.md → references/) | Partially adopted | `article-qa-auditor`, `article-seo-optimizer`, `writing-great-workflows` split detail into `references/`; **`multi-agent-article-pipeline/SKILL.md` does not** |

**Anti-patterns found**

1. **Brute-force context dumping in the orchestrator skill.** `multi-agent-article-pipeline/SKILL.md` is 443 lines — the largest file in the directory — and is the top-level, always-eligible-for-autoload skill that composes all seven others. It inlines pipeline stage logic, schemas, and persona detail rather than deferring to `references/pipeline-schemas.md` and `references/personas.md`, which exist alongside it but are only partially used. This is the single highest-leverage token-bloat target for Phase 2.
2. **No `.claudeignore` inheritance to prune.** Because the file doesn't exist, there's nothing scoping which parts of the repo (`docs-control-plane/`, `graphify-out/`, `.pytest_cache/`) are excluded from ambient context discovery. Combined with the always-on `multi-agent-article-pipeline` description text, this is additive token cost with no corresponding floor.
3. **No AST-level or symbol-level awareness anywhere in `.claude/`.** All context inclusion is file-granular (whole-file Read via skills/agents) or description-granular (frontmatter). There is no mechanism analogous to targeted symbol lookup — every skill invocation that touches an artifact re-reads full markdown files (`research_context.md`, `article_draft.md`, etc.) rather than diffed or indexed slices.
4. **Compression step exists but is manual/prose-only.** `RC → RS` (research_context.md → research_context_summary.md, targeting "~60–80% context reduction") is specified in the root CLAUDE.md as a modeled behavior, not a deterministic script. There's no executable in `scripts/` performing this reduction — it depends on the model doing it correctly each run, which is consistent with the repo's own stated policy problem ("guidance vs. enforcement").

**What's working**

- `disable-model-invocation: true` is correctly applied to the four meta/reference skills (`writing-great-*`) that should never be autoloaded into an article-generation session — good hygiene, real token savings.
- Reference-doc splitting on `article-qa-auditor` (audit-checklist.md, markdown-style.md) and `article-research-dialectic` (claim-taxonomy.md) is a legitimate targeted-disclosure pattern and should be the template applied to the orchestrator skill.

---

## 2. State Persistence — Grade: **D**

**Inventory**

| Mechanism | Present? | Location |
|---|---|---|
| Diff checkpoints | **Absent** | No checkpoint/snapshot files anywhere under `.claude/` |
| Architectural decision records (ADRs) | **Absent from `.claude/`** | ADR-equivalent material lives in `docs/ARCHITECTURE.md` (outside scope) per the control-plane CLAUDE.md, not in `.claude/` |
| Vector memory store | **Absent** | No embeddings, index, or vector DB config found |
| Pipeline run-state file | Present, but **outside `.claude/` entirely** | `.agents/artifacts/pipeline_state.json` |
| Cross-run learning store | Present, but **outside `.claude/` entirely** | `.agents/artifacts/pipeline_learnings.md`, `.agents/knowledge/article-pipeline/{context,pitfall}/` |

**Core finding: `.claude/` is stateless by design — all persistence lives in `.agents/`.**

This is the most important structural fact for the Phase 2 redesign: `.claude/` contains
zero mutable state. Every stateful artifact (`pipeline_state.json`, `pipeline_config.json`,
`conflict_decisions.json`, `artifact_manifest.json`, the entire `.agents/artifacts/` and
`.agents/knowledge/` tree) lives one directory over, governed by `scripts/pipeline_runner.py`,
`scripts/validate_artifacts.py`, and `scripts/write_artifact_manifest.py`. `.claude/` is
correctly a **passive configuration store** — agents, skills, and permission grants — exactly
as this task's own `<context>` block characterizes it, but that's actually the *correct*
separation of concerns (config vs. runtime state), not automatically a defect to be collapsed
in the redesign.

**Anti-patterns found**

1. **State amnesia between sessions is real but by design-gap, not by architecture.** `PS.stage` resumption depends on `TRIAGE` re-reading `pipeline_state.json` and running `validate_artifacts.py` — but nothing in `.claude/` enforces that this happens; it's prose instruction in root `CLAUDE.md` ("If PS exists: read it..."). A model that skips the read (context compaction, a fresh session invoked mid-pipeline via a different entry point) has no deterministic gate forcing resumption-correctness — no hook fires on session start to validate `.agents/artifacts/` against `.claude/skills/` expectations.
2. **No rollback/checkpoint primitive for `.agents/artifacts/*.md` writes.** Each skill (advocate, skeptic, synthesizer, drafter, etc.) has unilateral `Write` access to its owned artifacts per the Artifact Ownership table in root CLAUDE.md, but ownership is a documentation convention, not an OS- or hook-level write boundary — see §3.
3. **`__pycache__` committed alongside source.** `.claude/skills/multi-agent-article-pipeline/scripts/__pycache__/generate_chart.cpython-314.pyc` is present in the tracked skill directory — a build artifact masquerading as persistent state. Not a security issue but is exactly the kind of "abandoned/dead artifact" state-hygiene finding this audit is meant to surface, and it's a bad model for state directory cleanliness generally.

---

## 3. Governance & Security — Grade: **C-**

**Inventory**

| Control | Present? | Evidence |
|---|---|---|
| Per-agent tool allowlists | **Yes** — 3 of 3 subagents | `.claude/agents/*.md` frontmatter `tools:` |
| Per-skill tool allowlists | **No** — 0 of 12 skills | No `SKILL.md` in this repo declares a `tools:` or `allowed-tools:` frontmatter key |
| Project permission allowlist | Present, narrow | `.claude/settings.local.json` |
| `.env` / secret exposure | **Not found in `.claude/`** | No `.env` file present at project root; no secret material observed in scanned files |
| Hooks (pre/post-tool-use enforcement) | **Absent** | No `hooks` key anywhere in `.claude/settings.local.json`; the only hits for the string "hooks" are prose mentions inside `writing-claude-code-rules` and `writing-great-claude-subagents` reference docs, not executable wiring |
| RBAC across roles (advocate/skeptic/red-team/drafter/auditor) | **Partial, agent-level only** | See below |

**What's working — real, enforced isolation on the three delegated subagents**

- `article-advocate.md`: `tools: [WebSearch, Write]` — no `Read`. Combined with root CLAUDE.md's rule that skeptic "MUST NOT read advocate_context.md," this is backed by an actual capability boundary: the advocate can't read anything back even if a later prompt tried to get it to.
- `article-red-team.md`: `tools: [WebSearch]` — no `Read`, no `Write`. Its own file states this plainly: "You have no Read tool, so there is no way for you to go find the rest of the draft even if you wanted to." This is the one place in the directory where the root CLAUDE.md's kill-condition language ("Never send full AD to red-team") is backed by a capability boundary, not just an instruction the orchestrator has to remember to honor.
- `article-skeptic.md`: `tools: [WebSearch, Write]` — same shape as advocate.

This is a legitimately good pattern and directly answers the "RBAC" requirement — but it
covers only the **3 agents**, not the **12 skills**.

**Anti-patterns / vulnerabilities found**

1. **No RBAC at the skill layer — this is the primary governance gap.** Every `SKILL.md` in `.claude/skills/` runs with whatever tool access the invoking session already has; none declare a restricting `tools:`/`allowed-tools:` frontmatter field. Concretely: `article-fact-checker`, `article-qa-auditor`, `article-seo-optimizer`, and the `multi-agent-article-pipeline` orchestrator itself all execute with the full ambient permission set (Read/Write/Bash/WebSearch per root CLAUDE.md's tool list), not a scoped subset appropriate to their described job. The Artifact Ownership table in root CLAUDE.md ("AD → drafter," "RT → red-team," etc.) is a **documentation-level convention with zero executable backing** for anything running as a skill rather than a `.claude/agents/` subagent. Any skill can write to any artifact, including ones it doesn't own, and nothing in `.claude/` would stop or flag it.
2. **`settings.local.json` permission list is broad-surfaced Bash, not scoped-per-role.** The allowlist grants `Bash(python3 *)` (unbounded argument wildcard) and `Bash(python -c ' *)` (arbitrary inline Python execution pattern) at the project level, available to every skill/session, not gated to the specific scripts (`validate_artifacts.py`, `pipeline_runner.py`, `write_artifact_manifest.py`) that root CLAUDE.md actually calls out by name. `Bash(cat)` with no argument constraint is also present. These are permissive enough to defeat the intent of a scoped, auditable execution surface — a skill or an injected instruction inside fetched web content (skills use `WebSearch`) could invoke arbitrary Python via the already-approved `python -c` pattern without a new permission prompt.
3. **No hook-based enforcement of any kind exists.** There is no `PreToolUse`/`PostToolUse`/`SessionStart` hook in `.claude/settings.local.json`. Every guarantee in the root CLAUDE.md that reads like a control ("Never send full AD to red-team," "3 consecutive BLOCKED audits → HALT," "Persist stage, gates, telemetry... in PS") is enforced only by the model choosing to follow prose instructions during a given turn — with the sole exception of the 3 subagents' tool-capability boundaries described above. This is the central "guidance vs. enforcement" gap the parent repo's own root `CLAUDE.md` explicitly warns about, and `.claude/` here does not yet close it.
4. **No `.env` exposure was found, but there's also no explicit denial rule guarding against it.** Absence of a leak today is not the same as a boundary — `settings.local.json` has no `deny` block at all (only `allow`), so there's no explicit statement that `Read`/`Bash cat` may not touch `.env`, credentials, or `.agents/artifacts/*.json` outside the intended flow. Recommend adding an explicit `deny` list in Phase 2 rather than relying on the absence of matching files today.

---

## 4. Execution Hooks — Grade: **F**

**Inventory**

| Mechanism | Present? |
|---|---|
| `hooks` block in `settings.local.json` | **Absent** |
| Pre-mutation checks (pre-write/pre-bash validation) | **Absent** as a hook; exists only as a *manually-invoked* script (`scripts/validate_artifacts.py`, described in root CLAUDE.md as "the read-only contract check") |
| Post-mutation linters | **Absent** |
| Automated rollback | **Absent** |
| Local dev loop integration (test runners, formatters on save) | **Absent from `.claude/`**; `Bash(python -m pytest tests/ -v)` etc. are pre-approved permission patterns, meaning the model can choose to run them, but nothing forces it |

**Anti-patterns found**

1. **Zero automated integration points.** Every "hook-shaped" behavior described in root CLAUDE.md — `validate_artifacts.py` on resume, `write_artifact_manifest.py` after final writes, `pipeline_runner.py finalize` before marking `COMPLETE` — is a script that the model is instructed to *remember to call*, not something wired to fire automatically on a matching tool-use event. There is no `PostToolUse` hook tied to `Write` on `.agents/artifacts/*.md` that would auto-run the validator; no `PreToolUse` hook blocking a stage transition without gate evidence.
2. **No pre-mutation gate on the one truly irreversible operation this pipeline defines** — publishing / setting `PS.stage=COMPLETE`. Root CLAUDE.md is explicit that this should only happen after `pipeline_runner.py finalize` reports `PUBLISHABLE`, but that check is advisory (an instruction the orchestrator must remember to run), not a hook that intercepts the write to `pipeline_state.json` and rejects a premature `COMPLETE` value.
3. **No linter/formatter hook on the one executable artifact in scope**, `scripts/generate_chart.py` under `multi-agent-article-pipeline/scripts/` — its compiled `__pycache__` output being tracked (see §2) is itself evidence no pre-commit/pre-write hygiene hook runs against this directory.

---

## Summary Scorecard

| Vector | Grade | Primary Bottleneck |
|---|---|---|
| Context Management | C | Orchestrator skill (443 lines) not decomposed; no `.claudeignore` |
| State Persistence | D | No checkpoint/rollback primitive; state-vs-config split is correct in principle but has no session-start enforcement |
| Governance & Security | C- | RBAC exists only at agent layer (3/15 total constructs); skill layer and `settings.local.json` are broad-surfaced |
| Execution Hooks | F | No hooks configured at all; every control is prose-enforced |

**Highest-leverage Phase 2 targets, in order:**

1. Wire a `PreToolUse`/`PostToolUse` hook pair around `.agents/artifacts/*` writes to make artifact ownership and the `validate_artifacts.py` contract check executable rather than documented.
2. Add `tools:`/scoped-permission frontmatter to the 12 skills currently running with full ambient access — extend the pattern already proven correct on the 3 subagents.
3. Add a `SessionStart` hook that runs `validate_artifacts.py` and refuses to proceed past `TRIAGE` on a state/artifact mismatch, closing the state-amnesia gap.
4. Decompose `multi-agent-article-pipeline/SKILL.md` using the same references/-split pattern already used successfully elsewhere in the directory.
5. Add an explicit `deny` block to `settings.local.json` (secrets, `.agents/artifacts/*.json` outside the pipeline's own write paths) and narrow the `python3 *` / `python -c ' *` wildcard grants to the specific scripts actually named in root CLAUDE.md.

*End of Phase 1 audit. No files under `.claude/` were modified. No state-changing terminal commands were executed. This report is the only artifact written.*
