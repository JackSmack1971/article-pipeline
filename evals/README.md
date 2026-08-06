# Article Pipeline Evaluation Harness

This directory implements the evaluator described by `docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md`.

The harness is intentionally separate from the production article pipeline. Production artifacts live in `.agents/artifacts/`; evaluation outputs live under `.workflow/article-evals/` by default. The evaluator rejects trial roots at or inside the live production artifact directory.

## Qualified Publish Rate

Broad experiments use **Qualified Publish Rate (QPR)**. A trial qualifies only when all four layers pass:

1. the production artifact validator returns `PUBLISHABLE`;
2. independent epistemic grading passes source-support, citation, coverage, and integrity guardrails;
3. a blind editorial grader satisfies the editorial threshold and dimension floor;
4. the run required no undeclared human rescue.

`PUBLISHABLE` alone is necessary but not sufficient.

The epistemic layer also deterministically requires valid `https://` citation structure, at least one material claim under the default thresholds, and zero uncited material claims. A semantic grader cannot manufacture a missing article citation by supplying a source it found independently.

## Components

- `corpus/article_briefs.json` — visible matched development corpus.
- `prompts/claim_grader.md` — independent factual support/citation grader contract.
- `prompts/editorial_grader.md` — blind final-article editorial/audience rubric.
- `thresholds.default.json` — predeclared default QPR thresholds.
- `example-experiment.json` — example matched trial manifest.
- `scripts/article_eval.py` — deterministic citation extraction, grader-contract validation, QPR scoring, paired comparison, and aggregation.
- `scripts/run_article_eval.py` — prepares blinded packets, optionally invokes graders, and produces experiment summaries.

## Evaluator integrity rules

### Exact matched comparison

If an experiment contains more than one variant, every variant must contain the same `(brief_id, trial)` identities. Duplicate trial keys and unmatched baseline/candidate coverage are rejected.

Use `baseline` and `candidate` as variant names for normal A/B experiments.

### Stale-grade protection

Every prepared trial receives an `input_sha256` derived from the exact:

- corpus brief;
- blinded final article;
- deterministic citation extraction;
- external decision context, if supplied.

Both semantic graders must echo that digest. `score` rejects a grade whose digest does not match the prepared trial.

Re-running `prepare` deletes old `claim_grade.json`, `editorial_grade.json`, and `score.json` files before writing the new evaluation packet. A changed article therefore cannot silently reuse earlier semantic evidence.

### Citation binding

For each claim judgment, `citation_url` means the URL actually present in the final article. The grader may search the live web independently, but it may not replace a missing article citation with a source it found itself.

The scorer rejects grader citation URLs that do not occur in the blinded article.

### Prompt-injection boundary

The grader prompts explicitly treat the brief, decision context, and article as untrusted evaluation data. Instructions embedded in article prose do not override the grader contract.

### External decision context

Optional `decision_context` must be supplied by the experiment harness or human gate script. The evaluator does **not** automatically feed subject-generated QA, fact-check, red-team, reader, or research conclusions back into its independent grader.

When supplied, decision context must be identical across matched variants for a given `(brief_id, trial)` pair.

## Trial generation

Generate baseline and candidate articles in fresh, isolated Claude Code processes using the same brief, gate script, model/effort, network policy, tool availability, and resource budget unless the experiment intentionally varies one of those factors.

Archive each completed trial's artifact root outside `.agents/artifacts/`. The archived root must remain internally consistent, including its artifact manifest, because `run_article_eval.py prepare` runs the real production validator against it.

A trial manifest can include optional quality-adjusted efficiency telemetry:

```json
{
  "experiment_id": "cp-20260805-example",
  "trials": [
    {
      "variant": "baseline",
      "brief_id": "standard-source-conflict",
      "trial": 1,
      "artifact_root": "/abs/path/baseline-1",
      "human_rescue": false,
      "decision_context": {
        "conflict_policy": "present material unresolved empirical conflicts neutrally"
      },
      "run_metrics": {
        "cost_usd": 2.18,
        "wall_time_seconds": 410,
        "input_tokens": 22000,
        "output_tokens": 7800,
        "tool_calls": 31,
        "agent_calls": 2
      }
    },
    {
      "variant": "candidate",
      "brief_id": "standard-source-conflict",
      "trial": 1,
      "artifact_root": "/abs/path/candidate-1",
      "human_rescue": false,
      "decision_context": {
        "conflict_policy": "present material unresolved empirical conflicts neutrally"
      },
      "run_metrics": {
        "cost_usd": 1.91,
        "wall_time_seconds": 365,
        "input_tokens": 19500,
        "output_tokens": 7500,
        "tool_calls": 27,
        "agent_calls": 2
      }
    }
  ]
}
```

`human_rescue` means an intervention outside the predeclared gate script was needed to get the run through the pipeline. Required scripted approvals are not rescue.

Supported `run_metrics` fields are:

- `cost_usd`
- `wall_time_seconds`
- `input_tokens`
- `output_tokens`
- `tool_calls`
- `agent_calls`

All are optional and non-negative. Efficiency medians are computed from the trials that actually provide the corresponding field; keep telemetry collection matched across variants when using efficiency as a decision metric.

## Prepare blind evaluation packets

```bash
python3 scripts/run_article_eval.py prepare \
  --manifest evals/my-experiment.json
```

This writes under `.workflow/article-evals/<experiment-id>/`:

- `article.blind.md`;
- `deterministic.json`;
- `citation_structure.json`;
- `decision_context.json`;
- `claim_grader_prompt.md`;
- `editorial_grader_prompt.md`;
- `prepared_trials.json`.

The prepared metadata also records expected versus actual pipeline depth so routing changes are visible rather than silently folded into the article score.

## Run graders automatically

Any grader command is supported if it reads the complete prompt from stdin and writes one pure JSON object to stdout.

```bash
python3 scripts/run_article_eval.py prepare \
  --manifest evals/my-experiment.json \
  --claim-grader-command "my-independent-claim-grader --json" \
  --editorial-grader-command "my-blind-editorial-grader --json"
```

For Claude-based graders:

- use fresh grader processes separate from subject processes;
- hold grader model/version and grader tools constant across baseline/candidate;
- give the claim grader independent web retrieval when factual support must be checked;
- do not expose baseline/candidate identity or production self-assessment artifacts;
- do not allow article text to override the grader system/instruction layer.

If graders are run manually or elsewhere, place their JSON at:

```text
.workflow/article-evals/<experiment-id>/<trial-key>/claim_grade.json
.workflow/article-evals/<experiment-id>/<trial-key>/editorial_grade.json
```

The grader must echo the exact `input_sha256` printed in its prompt.

## Compute QPR

```bash
python3 scripts/run_article_eval.py score \
  --prepared .workflow/article-evals/<experiment-id>/prepared_trials.json \
  --thresholds evals/thresholds.default.json
```

The runner writes `summary.json` and `score.json` for every trial.

Default epistemic requirements:

- grader confirms whole-article material-claim coverage;
- at least 1 material factual claim is graded;
- zero fabricated citations;
- zero uncited material claims;
- zero material claims graded `UNSUPPORTED` or `CITATION_MISMATCH`;
- at least 90% of material claims graded fully `SUPPORTED`;
- no disputed/outdated claim presented as settled;
- no silent drift from supplied external decision context;
- no non-HTTPS article citations.

Default editorial requirements:

- mean score at least 4.0/5 across six dimensions;
- no individual dimension below 3.0;
- no editorial hard failure.

These thresholds are deliberately strict for broad QPR experiments. A subsystem experiment may predeclare a narrower primary metric, but factual/citation integrity guardrails should remain unless the experiment explicitly studies the grader itself.

## Comparison output

For two-variant experiments, `summary.json` includes paired outcome counts:

- both qualified;
- candidate-only qualified;
- baseline-only qualified;
- neither qualified;
- QPR absolute delta.

This matters because the same aggregate QPR can hide very different per-brief behavior.

When `run_metrics` are supplied, variant summaries include medians for all trials and separately for qualified-publish trials. Prefer quality-adjusted metrics such as median cost among qualified publishes over raw cheapness.

## Matched corpus design

The visible corpus covers:

- an inexpensive evergreen SIMPLE explainer;
- quantitative policy with regional variation;
- conflicting productivity evidence;
- current technical/security claims;
- fast-moving AI/vendor claims;
- contentious causal public-health evidence;
- a case where evidence should weaken the starting thesis;
- a source-scarce governance topic where uncertainty must remain visible.

This corpus is for development and regression work. Serious Class C/D confirmation should add candidate-inaccessible held-out briefs with the same challenge distribution. Do not copy hidden briefs, hidden grader logic, or confirmatory transcripts into the visible corpus after use.

## Interpretation

QPR is a conjunction, so a low score is diagnostic rather than self-explanatory. Inspect:

- deterministic publish rate;
- epistemic pass rate;
- editorial pass rate;
- human rescue rate;
- material-claim precision;
- editorial mean;
- paired disagreement counts;
- efficiency among qualified trials;
- expected versus actual routing.

A candidate that raises deterministic completion while lowering epistemic or editorial performance is not an improvement. A candidate that preserves QPR while materially reducing quality-adjusted cost or orchestration complexity may be a valid simplification under a predeclared non-inferiority experiment.

Do not optimize against a single favorable article. Pair baseline and candidate on the same briefs, repeat stochastic trials, inspect discordant pairs, and treat suspiciously perfect performance as an integrity signal.
