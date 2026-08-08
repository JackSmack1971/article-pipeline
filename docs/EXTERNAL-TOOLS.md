# External Tools

Third-party tools the control plane is aware of but has not adopted. An entry
here is a discovery record, not an endorsement — adoption of anything that
changes Claude Code behavior (hooks, skills, permissions) must go through
`docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` before it is wired in.

## graphify

- **What it is**: CLI (`graphifyy` on PyPI, command `graphify`) that turns a
  codebase, docs, and other files into a queryable knowledge graph. Code is
  parsed locally via tree-sitter AST (deterministic, no API calls); docs,
  PDFs, images, and video go through the assistant's model API. Apache-2.0,
  maintained by Graphify Labs (YC S26). Source: <https://github.com/Graphify-Labs/graphify>.
- **Install**:
  ```bash
  uv tool install graphifyy        # or: pipx install graphifyy
  graphify install --project       # writes .claude/skills/graphify/SKILL.md into this repo
  ```
  `--project` scopes the install to this repository instead of the user
  profile; drop it to install the skill user-wide instead. Add `--strict` to
  the install to make the PreToolUse hook (below) block instead of nudge.
- **Already present on this machine**: `graphify` v0.8.38 is on `PATH`
  (`~/.local/bin/graphify`), older than the latest published release
  (v0.9.36 as of 2026-08-07). An empty, untracked `graphify-out/` directory
  already exists at the repo root — not gitignored, not populated. No
  `.claude/skills/graphify/` and no graphify-related hook is currently
  registered in `.claude/settings.json` or `.claude/settings.local.json`;
  the CLI has not actually been run against this repo yet.
- **Behavioral impact if installed**: `graphify install` (default) registers
  a `PreToolUse` hook that nudges Claude Code toward `graphify query` before
  raw `Read`/`Glob` calls on source files; `--strict` blocks the first raw
  source read per session and redirects it through the graph instead. This
  is a control-plane change under the improvement protocol's scope (hooks
  that materially affect tool behavior) — treat it as at least a Class B
  experiment, not a drive-by install.
- **Fit for this repo**: two distinct halves exist here.
  - *Control-plane half* (`scripts/`, `.claude/skills`, `.claude/agents`,
    hooks): this is exactly the kind of AST-graph-shaped artifact graphify
    targets, and could plausibly help future audits/onboarding (e.g. tracing
    which skill delegates to which agent, or which script a hook shells out
    to) — worth a real Class B experiment against the improvement protocol
    if that need becomes concrete.
  - *Article-pipeline half* (`.agents/artifacts/*.md`, `*.json` research
    artifacts): these are ephemeral, gitignored, regenerated per run — prose
    research context rather than a codebase. graphify's core value
    (deterministic AST code graphing) doesn't apply, and a persistent graph
    over transient per-run artifacts has unclear payoff. Not a fit unless a
    concrete cross-run research-reuse need emerges.
- **Status**: not installed by the control plane. Documented per user
  request on 2026-08-07 for future reference.
