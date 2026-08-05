# Article Pipeline Evaluation Harness

This directory is the visible development corpus for the control-plane evaluator described in
`docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md`.

The evaluator has four parts:

1. **Matched subject runs** — `scripts/evals/qpr_runner.py` runs the same brief against a baseline
   git ref and a candidate git ref in fresh detached worktrees. Pair order is randomized.
2. **Independent factual/citation grading** — `scripts/evals/claim_citation_grader.py` runs in
   Claude Code `--bare` mode with web tools. It independently checks material factual claims and
   every practical citation URL rather than trusting the pipeline's own fact-check artifacts.
3. **Blind editorial grading** — `scripts/evals/editorial_grader.py` runs in `--bare` mode with no
   tools and sees only the final article plus the brief/audience. It does not know baseline vs.
   candidate identity.
4. **Qualified Publish Rate (QPR)** — a run qualifies only when the persisted article contract is
   `PUBLISHABLE`, factual/citation thresholds pass, editorial thresholds pass, hard guardrails
   remain intact, route expectations are satisfied, and no undeclared human rescue was required.

## Important separation

The subject worktree is scrubbed of `evals/`, `scripts/evals/`, prior `.agents/artifacts/`, and by
default prior article-pipeline knowledge before Claude runs. Subject sessions load **project**
settings/skills/CLAUDE.md but disable auto memory. Graders run separately in `--bare` mode so the
candidate control plane cannot rewrite their behavior.

This is strong development isolation, not a security sandbox. For confirmatory held-out evaluation,
place the corpus outside the repository and run subject worktrees inside an OS/container boundary
that cannot read evaluator files, hidden tasks, prior results, or grader credentials.

## Requirements

- Python 3.11+
- Git
- Current Claude Code CLI (`claude`)
- Claude authentication usable from non-interactive `claude -p`
- Network access for article research and the factual/citation grader

The runner uses current Claude Code programmatic features including `-p`, `--output-format json`,
`--json-schema`, `--resume`, `--setting-sources project`, `--max-budget-usd`, and `--bare` grader
sessions.

## Validate the harness without spending model budget

```bash
python3 -m unittest discover -s tests -p 'test_*.py'

python3 scripts/evals/qpr_runner.py \
  --baseline-ref main \
  --candidate-ref HEAD \
  --dry-run
```

`--dry-run` resolves refs, validates the corpus, records the environment, and writes an experiment
manifest, but does not launch subject or grader sessions.

## Run one matched development brief

```bash
python3 scripts/evals/qpr_runner.py \
  --baseline-ref main \
  --candidate-ref control-plane/my-change \
  --brief-id remote-work-productivity \
  --trials 1 \
  --minimum-pairs 1
```

By default results are written to a sibling directory:

```text
../article-eval-results/article-eval-YYYYMMDD-HHMMSS/
```

They are deliberately not written into `.agents/artifacts/`.

## Run the visible development suite

```bash
python3 scripts/evals/qpr_runner.py \
  --baseline-ref main \
  --candidate-ref control-plane/my-change \
  --trials 1
```

The checked-in corpus currently spans:

- stable technical explanation;
- consumer quantitative explanation;
- contested social-science evidence;
- lifecycle quantitative methodology;
- complex energy-policy conflict;
- fast-moving enterprise AI decisions;
- emerging-technology commercialization uncertainty;
- fast-moving semiconductor/geopolitical policy.

One trial per eight briefs produces eight paired observations. For a consequential cross-cutting
change, increase `--trials` and use a held-out corpus for confirmation.

## Held-out confirmation

The corpus can be an external JSON file containing either one brief object or a `{ "briefs": [...] }` wrapper (directories of brief JSON files are also supported):

```bash
python3 scripts/evals/qpr_runner.py \
  --baseline-ref <frozen-baseline-sha> \
  --candidate-ref <frozen-candidate-sha> \
  --corpus /secure/heldout/article-briefs.json \
  --trials 3 \
  --output-dir /secure/results/experiment-42
```

Do not modify the candidate after seeing a held-out result and then reuse that same held-out case as
independent confirmation.

## Brief schema

Each brief is a JSON object. Required fields are `id`, `topic_brief`, `target_audience`, and
`scripted_decisions`. Common optional fields are:

```json
{
  "id": "example",
  "suite_tags": ["complex", "freshness"],
  "topic_brief": "...",
  "target_audience": "...",
  "intended_thesis": "...",
  "allowed_depths": ["STANDARD", "COMPLEX"],
  "scripted_decisions": {
    "thesis_confirmation": "confirmed",
    "approval": "approved — use neutral handling for every conflict not individually specified",
    "red_team": "address",
    "reader": "polish",
    "delivery": "deliver_without"
  },
  "max_claims_to_grade": 30,
  "thresholds": {
    "material_claim_precision_min": 0.95,
    "citation_support_rate_min": 0.95,
    "editorial_mean_min": 4.0,
    "editorial_dimension_min": 3,
    "max_missing_material_citations": 0
  }
}
```

Gate decisions are predeclared so baseline and candidate receive the same editorial choices. The
runner also supports resuming a subject session if a normal gate still returns control despite the
preauthorization. If an unexpected decision is required, the run is marked as needing undeclared
human rescue and cannot qualify.

## QPR qualification

Default thresholds are intentionally demanding:

- artifact validator status: `PUBLISHABLE`;
- material factual-claim precision: at least 0.95;
- citation support rate: at least 0.95;
- missing material citations: 0;
- editorial mean: at least 4.0/5;
- every editorial dimension: at least 3/5;
- no mismatched or likely fabricated citation;
- no outdated/contradicted claim presented as current fact;
- no fatal editorial issue;
- advocate/skeptic/red-team capability isolation remains intact;
- no undeclared human rescue;
- route depth is within the brief's declared acceptable set when one is supplied.

The runner reports both:

- **QPR** over evaluable trials, excluding separately classified evaluator/infrastructure failures;
- **operational QPR** over all scheduled trials, so flaky infrastructure cannot disappear from the
  operational picture.

It also reports median subject cost, latency, and tokens per qualified article.

## Experiment outputs

Each trial stores:

- copied article-run artifacts;
- subject turn outputs and Claude Code usage/cost metadata;
- deterministic validator result;
- independent claim/citation grade;
- blind editorial grade;
- qualification reasons and hard-guardrail failures.

The experiment root stores:

- `experiment_manifest.json` — refs, models, budgets, environment, evaluator digest, corpus digest;
- `records.json` — all trial records;
- `summary.json` — arm-level QPR, operational QPR, paired delta, bootstrap interval, and the
  predeclared accept/reject/inconclusive recommendation.

Treat the recommendation as an experimental decision aid, not permission to merge around an
unexplained guardrail failure or evaluator defect.
