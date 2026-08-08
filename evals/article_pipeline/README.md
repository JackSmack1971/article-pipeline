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
- For the independent `--bare` graders: `ANTHROPIC_API_KEY` (or an `apiKeyHelper` supplied through explicit grader settings); bare mode does not read OAuth/keychain credentials
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

## Greatness Benchmark Corpus (G-000)

`greatness_corpus_v1.json` is a separate, **development/calibration** corpus of 16
deliberately difficult briefs for measuring performance against
`docs/Great Article Standard v1.md` (see also `docs/GREATNESS-GAP-ANALYSIS.md`). It is not
loaded by default — `qpr_runner.py --corpus` still defaults to `development_corpus.json` — so
adding this corpus does not change production-pipeline behavior. Run it explicitly:

```bash
python3 scripts/evals/qpr_runner.py \
  --baseline-ref main \
  --candidate-ref HEAD \
  --corpus evals/article_pipeline/greatness_corpus_v1.json \
  --trials 1 \
  --dry-run
```

It uses the exact same brief schema and loader as `development_corpus.json` (§ Brief schema
below) plus additional **evaluator-only diagnostic fields** that `qpr_runner.py` never reads
into a subject prompt: `archetype`, `benchmark_rationale`, `stressed_dimensions`,
`primary_failure_modes`, `freshness_matters`, `scholarly_evidence_matters`. `build_subject_prompt()`
only ever reads `topic_brief`, `target_audience`, `intended_thesis`, and `scripted_decisions` —
`tests/test_article_evals.py::GreatnessCorpusTests::test_diagnostic_fields_never_change_the_subject_prompt`
proves this by asserting the generated prompt is identical with or without every diagnostic-only
field present, for every brief in the corpus. No schema or loader change was needed to achieve
this separation; it already existed because the loader is permissive about extra keys.

### Distribution

Two briefs per Great Article Standard §3 archetype (16 total):

- Scientific / Scholarly Explainer — `gc-sci-01`, `gc-sci-02`
- Investigative / Current-Affairs Analysis — `gc-inv-01`, `gc-inv-02`
- Strategic / Executive Decision Guide — `gc-exec-01`, `gc-exec-02`
- Technical Tutorial / Technical Explainer — `gc-tech-01`, `gc-tech-02`
- Comparative / Commercial Decision Guide — `gc-cmp-01`, `gc-cmp-02`
- Argument / Thought Leadership — `gc-arg-01`, `gc-arg-02`
- Human-Centered Narrative / Feature — `gc-narr-01`, `gc-narr-02`
- Breaking-News Analysis — `gc-news-01`, `gc-news-02`

Each pair varies difficulty (`allowed_depths`), fact stability vs. freshness pressure
(`freshness_matters`, `suite_tags`), evidence abundance, contestedness, audience technicality,
and whether an emotional register is appropriate — see each brief's `suite_tags`.

### Adversarial coverage

`primary_failure_modes` on each brief names which of the following it stresses; every mode is
exercised by at least two briefs:

`correlation_to_causation_drift`, `study_scope_overgeneralization`, `newest_vs_strongest_evidence`,
`contradictory_evidence`, `uncertainty_inflation`, `weak_but_popular_claims`,
`seductive_predetermined_thesis`, `fabricated_first_person_experience_pressure`,
`verbosity_after_evidence_exhausted`.

`stressed_dimensions` tags each brief with the Great Article Standard Hard Epistemic Invariants
(E1–E12) and/or Excellence Vector dimensions (RQ, CQ, IG, SI, IH, RT, AF, HR, SF, PU) it is
designed to exercise, for use when building a future Greatness evaluator (§9 of the Standard).

### Contamination controls

Same isolation model as the rest of this harness (see "Important separation" above): the corpus
lives under `evals/`, which `scrub_subject_worktree()` removes from subject worktrees before a
subject session runs. `gc-*` briefs contain no evaluator answer keys or rubric text inside
`topic_brief`/`target_audience`/`intended_thesis` — only the diagnostic-only fields carry
evaluator framing, and those are never placed in the subject prompt (see above).

### Adding a brief

1. Pick the archetype(s) and adversarial failure mode(s) the new brief should stress; check
   `stressed_dimensions`/`primary_failure_modes` coverage isn't already saturated for that mode.
2. Give it a unique `gc-<archetype-abbrev>-NN` id and fill every field required by
   `GreatnessCorpusTests.test_every_brief_declares_required_diagnostic_fields`.
3. Keep `topic_brief`/`target_audience`/`intended_thesis` subject-visible-safe: write them as if
   a real editor handed them to a writer, not as grading instructions.
4. Run `python3 -m unittest discover -s tests -p 'test_*.py'` — the corpus-shape and
   prompt-separation tests run automatically.

### What this corpus is not

This is **development/calibration data** used to build and iterate on future Greatness
evaluation machinery (Layers 2–8 of Standard §9). It is visible to anyone with repository
access and is not a held-out proof of pipeline quality. Per
`docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` §4.5/§4.6, any claim that the pipeline reliably
produces "great" articles requires a separate held-out corpus outside this repository,
frozen grader/harness versions, and the same isolation discipline already used for QPR
confirmation runs.

## Greatness Evaluator v0 (G-001)

`scripts/evals/greatness_evaluator.py` scores a finished article against the Excellence Vector
in `docs/Great Article Standard v1.md` §2.2. It is **eval-only and operationally independent**:
it does not replace, weaken, or re-derive `validate_artifacts.py`, `claim_citation_grader.py`,
`editorial_grader.py`, or QPR — it consumes an existing QPR/epistemic qualification decision as
an input and sits strictly above it.

```bash
python3 scripts/evals/greatness_evaluator.py \
  --article path/to/article_draft.md \
  --brief evals/article_pipeline/greatness_corpus_v1.json \
  --qpr-record ../article-eval-results/.../trials/<trial>/record.json
```

(`--brief` must resolve to a single brief object with an `archetype` field; pass one extracted
brief, not the corpus wrapper. `--epistemic-eligible`/`--epistemic-ineligible` plus
`--epistemic-reason` are available instead of `--qpr-record` for manual/dry runs.)

Key design points, each directly answering a requirement in `docs/GREATNESS-GAP-ANALYSIS.md` §2/§9:

- **Scores exactly nine dimensions** — RQ, CQ, SI, IH, RT, AF, HR, SF, PU — each via 4 atomic,
  decomposed yes/no criteria with a grader rationale (CheckEval-style; Standard §9 Layer 4),
  not one vague score.
- **IG (Information Gain) is explicitly `NOT_EVALUATED`.** No proxy is substituted — there is no
  competitor corpus or Atomic Information Unit machinery in this repository (Standard §5/§7).
- **Ownership split**: the semantic grader (one blind `--bare` Claude Code call, no tools, no
  filesystem, no baseline/candidate identity, no internal QA/fact-check conclusions, no token
  spend, no production self-score — same blind pattern as `editorial_grader.py`) judges each
  criterion. All schema validation, aggregation, archetype weighting math, thresholds, and
  classification are deterministic Python.
- **Archetype weighting** uses the exact §3 table (`ARCHETYPE_WEIGHTS`), evaluator-side only —
  no production archetype routing was added. The table has no IH column (IH is a universal floor,
  not archetype-weighted, per §2.2); the weighted Excellence Index excludes IG and IH, both of
  which are still graded/floor-checked outside the weighted composite.
- **IH universal floor**: any article scoring below the floor is capped at `PUBLISHABLE`
  regardless of every other dimension or the Excellence Index.
- **Epistemic/QPR ineligibility always forces `EPISTEMICALLY_INELIGIBLE`** and skips scoring
  entirely (Standard §2.1: "the Greatness evaluation stops") — it can never classify `GREAT` or
  `EXCEPTIONAL`.
- **`GREAT`/`EXCEPTIONAL` are structurally capped at `STRONG` in v0.** Both require demonstrated
  information gain (§2.4), which cannot be true while IG is `NOT_EVALUATED`. `classify()` still
  reports whether the excellence-index/IH/CQ thresholds were met (`would_meet_..._excluding_ig`)
  as a diagnostic, so the cap is visible rather than silently absorbed.
- **Raw dimension scores and per-criterion diagnostics are preserved** alongside the weighted
  Excellence Index, not just the aggregate.
- **RT (Reader Transformation) carries a fixed limitation note** on every run: no production
  Reader Transformation Contract exists yet (Standard §4), so RT is a post-hoc proxy, not a
  measurement against a predeclared before/after contract.
- Output includes `evaluator_version`, `rubric_version`, grader `model`/`effort`/confidence, and
  per-dimension confidence — thresholds and the PUBLISHABLE/STRONG/GREAT/EXCEPTIONAL labels are
  provisional calibration hypotheses (Standard §2.3/§2.4), not empirical truths.

Regression coverage lives in `tests/test_article_evals.py::GreatnessEvaluatorTests` and never
shells out to `claude` (it exercises `classify()`/`compute_dimension_scores()`/
`compute_excellence_index()` directly with synthetic grader payloads, plus the
`epistemic_eligible=False` short-circuit of `evaluate()`).

### QPR integration (`--evaluate-greatness`)

`qpr_runner.py` can optionally attach a Greatness result to each trial record without changing
QPR at all:

```bash
python3 scripts/evals/qpr_runner.py \
  --baseline-ref main \
  --candidate-ref HEAD \
  --corpus evals/article_pipeline/greatness_corpus_v1.json \
  --evaluate-greatness \
  --trials 1
```

`--evaluate-greatness` is opt-in and additive only: `should_run_greatness()` gates it on the flag
plus the brief declaring a known archetype (so `development_corpus.json` briefs, which have no
`archetype` field, are never scored regardless of the flag), and it never touches
`qualification()` or `aggregate_arm()` — the functions that actually compute QPR. On success the
full `evaluate()` result (eligibility, archetype, all nine raw dimension scores and diagnostics,
weighted excellence index, provisional classification, `IG=NOT_EVALUATED`, evaluator/rubric
version) lands unmodified at `record["greatness"]`. On failure the error lands separately at
`record["greatness_error"]`, distinct from `record["evaluator_error"]` (harness/subject
infrastructure failures) and from `record["qualification"]` (article/subject failures), so a
Greatness scoring problem can never be conflated with, suppress, or inflate a QPR outcome.
`--greatness-model`/`--greatness-effort`/`--greatness-max-budget-usd`/`--greatness-timeout-seconds`
control the grader call; the chosen configuration is recorded in `experiment_manifest.json` under
`greatness_evaluation`.

Regression coverage: `tests/test_article_evals.py::GreatnessQprIntegrationTests`.

### Calibration readiness

See `docs/GREATNESS-EVALUATOR-CALIBRATION.md` for evaluator independence, deterministic-vs-semantic
ownership, the anti-gaming test strategy and what it does/does not prove, provisional-threshold
status, known limitations, and exactly what human calibration and held-out confirmation are still
required before this evaluator can inform any real decision. Current status:
**NOT_READY_FOR_HUMAN_CALIBRATION**.

### What G-001 v0 does not do

Per the goal scope for this increment, deliberately absent: competitor research/corpus
ingestion, CIG/IG scoring or any proxy for it, pairwise competitor evaluation, a production
Reader Transformation Contract, scholarly retrieval infrastructure, a humanity/prose rewrite
pass, and any wiring into `pipeline_runner.py` finalize or production archetype routing. Adding
any of these is a separate, higher-evidence-bar experiment under
`docs/CONTROL-PLANE-IMPROVEMENT-PROTOCOL.md` (Class C/D) — see `docs/GREATNESS-GAP-ANALYSIS.md`
§5/§7/§9 for what each would require.

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
