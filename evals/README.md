# Article Pipeline Evaluation Harness

This directory implements the evaluator described by `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md`.

The harness is intentionally separate from the production article pipeline. Production artifacts live in `.agents/artifacts/`; evaluation artifacts live under `.workflow/article-evals/` by default. Never point an experiment trial directly at the live `.agents/artifacts/` directory.

## What the harness measures

Broad experiments use **Qualified Publish Rate (QPR)**. A trial qualifies only when all four layers pass:

1. the production artifact validator returns `PUBLISHABLE`;
2. an independent claim/citation grader satisfies the epistemic thresholds and hard guardrails;
3. a blind editorial grader satisfies the editorial threshold and dimension floor;
4. the run required no undeclared human rescue.

`PUBLISHABLE` alone is therefore necessary but not sufficient.

## Components

- `corpus/article_briefs.json` — matched visible development corpus. The exact same brief should be used for baseline and candidate.
- `prompts/claim_grader.md` — independent factual support/citation grader contract. The grader is expected to retrieve sources independently when semantic verification is required.
- `prompts/editorial_grader.md` — blind final-article editorial/audience rubric. It receives no baseline/candidate identity or pipeline traces.
- `thresholds.default.json` — predeclared default QPR thresholds.
- `example-experiment.json` — minimal trial manifest.
- `scripts/article_eval.py` — deterministic extraction, contract validation, QPR scoring, and aggregation.
- `scripts/run_article_eval.py` — prepares blind packets, optionally invokes graders, and produces experiment summaries.

## Why semantic graders are external

Python can deterministically verify artifact state, link syntax, counts, and grader schemas. It cannot establish that a live web source actually supports a proposition or that an article is genuinely coherent for its target audience.

For that reason, semantic graders are separate processes. They receive only the information needed for their role:

- claim grader: brief + blind article + deterministic citation extraction;
- editorial grader: brief + blind article only.

Do not pass production `fact_check_report.md`, `audit_report.md`, `reader_questions.md`, `red_team_report.md`, variant identity, or pipeline reasoning to either grader. Those are subject outputs, not independent evidence.

## Trial generation

Generate baseline and candidate articles in fresh, isolated Claude Code processes using the same brief, gate script, model/effort, network policy, tool availability, and resource budget unless the experiment intentionally varies one of those factors.

Archive each completed trial's artifact root outside `.agents/artifacts/`. The archived root must remain internally consistent, including its artifact manifest, because `run_article_eval.py prepare` runs the real production validator against it.

A trial manifest looks like:

```json
{
  "experiment_id": "cp-20260805-example",
  "trials": [
    {
      "variant": "baseline",
      "brief_id": "standard-source-conflict",
      "trial": 1,
      "artifact_root": "/abs/path/baseline-1",
      "human_rescue": false
    },
    {
      "variant": "candidate",
      "brief_id": "standard-source-conflict",
      "trial": 1,
      "artifact_root": "/abs/path/candidate-1",
      "human_rescue": false
    }
  ]
}
```

`human_rescue` means an intervention outside the predeclared gate script was needed to get the run through the pipeline. Required scripted approvals are not rescue.

## Prepare blind evaluation packets

```bash
python3 scripts/run_article_eval.py prepare \
  --manifest evals/my-experiment.json
```

This writes under `.workflow/article-evals/<experiment-id>/`:

- a blinded copy of each final article;
- deterministic validator output;
- deterministic citation-structure output;
- claim-grader prompt;
- editorial-grader prompt;
- `prepared_trials.json`.

The command refuses to evaluate the live `.agents/artifacts/` directory.

## Run graders automatically

Any grader command is supported if it reads the complete prompt from stdin and writes one pure JSON object to stdout.

Example shape:

```bash
python3 scripts/run_article_eval.py prepare \
  --manifest evals/my-experiment.json \
  --claim-grader-command "my-independent-claim-grader --json" \
  --editorial-grader-command "my-blind-editorial-grader --json"
```

For Claude-based graders, configure the grader process separately from the subject and keep its prompt/context independent. Prefer a fixed grader model/version for an experiment. If the grader has web access, use it for claim verification; the editorial grader does not need subject traces or web research.

If graders are run manually or by another system, place their pure JSON responses at:

```text
.workflow/article-evals/<experiment-id>/<trial-key>/claim_grade.json
.workflow/article-evals/<experiment-id>/<trial-key>/editorial_grade.json
```

The required JSON shapes are specified in the prompt files and enforced by `scripts/article_eval.py`.

## Compute QPR

```bash
python3 scripts/run_article_eval.py score \
  --prepared .workflow/article-evals/<experiment-id>/prepared_trials.json \
  --thresholds evals/thresholds.default.json
```

The runner writes `summary.json` and a `score.json` for every trial.

Default epistemic requirements:

- zero fabricated citations;
- zero material claims graded `UNSUPPORTED` or `CITATION_MISMATCH`;
- at least 90% of material claims graded fully `SUPPORTED`;
- no disputed/outdated claim presented as settled;
- no silent drift from an explicit conflict decision.

Default editorial requirements:

- mean score at least 4.0/5 across six dimensions;
- no individual dimension below 3.0;
- no editorial hard failure.

These thresholds are deliberately strict for broad QPR experiments. A subsystem experiment may predeclare a narrower primary metric, but hard integrity guardrails should remain.

## Matched corpus design

The visible corpus currently covers:

- an inexpensive evergreen SIMPLE explainer;
- quantitative policy with regional variation;
- conflicting productivity evidence;
- current technical/security claims;
- fast-moving AI/vendor claims;
- contentious causal public-health evidence;
- a case where evidence should weaken the starting thesis;
- a source-scarce governance topic where uncertainty must remain visible.

This corpus is for development and regression work. Serious Class C/D confirmation should add candidate-inaccessible held-out briefs with the same distribution of challenge types. Do not copy hidden briefs or grader answers into this directory after they have been used as confirmatory evidence.

## Interpretation

QPR is a conjunction, so a low score is diagnostic rather than self-explanatory. Inspect the layer-specific rates in `summary.json`:

- deterministic publish rate;
- epistemic pass rate;
- editorial pass rate;
- human rescue rate;
- QPR.

A candidate that raises deterministic completion while lowering epistemic pass rate is not an improvement. A candidate that preserves QPR while materially reducing cost or orchestration complexity may be a valid simplification under a predeclared non-inferiority experiment.

Do not optimize against a single favorable article. Pair baseline and candidate on the same briefs, repeat stochastic trials, and inspect disagreements and suspiciously perfect results as required by the improvement protocol.
