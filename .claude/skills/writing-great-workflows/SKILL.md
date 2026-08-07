---
name: writing-great-workflows
description: Reference for designing, writing, reviewing, and empirically improving Claude Code dynamic workflow files.
disable-model-invocation: true
---

A dynamic workflow moves the **plan into code**. The script owns orchestration; agents own judgment and I/O. The root virtue is **controlled scaling**: spend extra agents only where the work can be separated, the results can be verified, and the expected gain justifies the cost.

**Bold terms** are defined in [`GLOSSARY.md`](GLOSSARY.md). For version-sensitive runtime facts, consult [`references/EVIDENCE.md`](references/EVIDENCE.md). For JavaScript conventions specific to the workflow runtime, consult [`references/JAVASCRIPT.md`](references/JAVASCRIPT.md).

## Ground the runtime before authoring

Dynamic workflows are evolving quickly. Before relying on an exact primitive, option, limit, permission behavior, save path, or resume behavior:

1. Inspect the installed Claude Code version when available.
2. Prefer the current official Dynamic Workflows and Agent SDK documentation over examples copied from old issues, blog posts, or generated scripts.
3. Classify a claim as **documented**, **observed**, or **speculative**. Only documented behavior becomes a hard rule in the workflow. Observed behavior may guide a test. Speculation must not become an API assumption.
4. If the requested design depends on a version-specific feature, state the version boundary in the workflow's surrounding documentation or comments rather than burying it in prose.

Completion criterion: every runtime feature the design depends on is either current documented behavior or explicitly isolated behind a testable assumption.

## Decide whether a workflow is the right abstraction

Use a workflow when the value comes from **orchestration shape**: repeatable loops, branching, fan-out/fan-in, staged verification, or many independent work units whose intermediate results should stay in script variables.

Prefer another primitive when its owner should hold the plan:

- **Subagent** — a few delegated tasks; Claude still decides what happens next.
- **Skill** — reusable procedural knowledge; Claude follows instructions but remains the orchestrator.
- **Agent team** — a handful of long-running peers need to communicate, coordinate, or share a task list.
- **Workflow** — the runtime should execute an inspectable orchestration graph and keep intermediate state outside the main conversation.

The test is not “could multiple agents help?” It is: **what decision should code make that Claude should not have to remake turn by turn?** If there is no clear answer, do not add a workflow.

Completion criterion: the design names the orchestration decision being moved into code and why a simpler primitive is insufficient.

## Draw the independence graph

Parallelism is earned by **independence**, not by task size.

For each work unit, identify:

- input it reads;
- state it may mutate;
- output it returns;
- dependencies that must complete first;
- resources or files another work unit may also change.

Then choose the narrowest shape that fits:

- **Chain** — each stage depends on the previous stage's result.
- **Fan-out / fan-in** — independent items can run concurrently, then aggregate.
- **Propose / verify** — independent agents generate candidates; a separate verifier tests them.
- **Evaluator / optimizer** — a producer improves an artifact against a stable criterion.
- **Saturation loop** — repeat discovery until a measurable round adds no new information.

Do not parallelize tightly coupled edits merely because concurrency is available. If workers can collide on mutable state, isolate the work or serialize the conflicting region.

Completion criterion: every parallel edge is justified by independent inputs/state, and every dependency is explicit in the control flow.

## Define contracts before prompts

Treat each `agent()` boundary as a typed interface, not a chat hand-off.

For every stage, define:

- one objective;
- the minimum context needed to achieve it;
- a structured output when downstream code depends on fields;
- what `null`, an empty result, or an unverifiable result means;
- a stable label that makes the run inspectable.

Prefer narrow JSON schemas with required fields over prose that downstream code must reinterpret. Keep large artifacts in the environment when possible and pass concise identifiers or summaries between agents; the workflow script should coordinate, not become a transcript bus.

Completion criterion: downstream control flow never depends on parsing an ambiguous paragraph when a structured contract can express the decision.

## Budget before fan-out

More agents are not a correctness proof. Multi-agent gains are workload-dependent and can be erased by coordination, verification, context, or token costs.

Before a large run, define a **cost envelope**:

- expected number of agents;
- likely expensive stages;
- maximum rounds for loops;
- stop conditions for saturation or repair;
- what smaller pilot slice can falsify the design cheaply.

Start with the smallest fan-out that exercises the topology. Increase width only when evals show a measurable gain. Use stronger models where judgment is the bottleneck and cheaper models where the task is mechanical, but confirm the current model-routing API before writing option names.

Completion criterion: the workflow has bounded scale and a pilot path; no loop or fan-out grows solely because “more perspectives” sounds safer.

## Write orchestration JavaScript, not application JavaScript

The workflow runtime is JavaScript-shaped but purpose-specific. Keep the script focused on control flow:

- `export const meta` names and describes the workflow.
- Use `const` by default; use `let` only for deliberate evolving state such as a round counter or previous fingerprint.
- Keep predicates and data transforms small and local.
- Use top-level `await` as the runtime supports it.
- Delegate filesystem reads, writes, shell commands, web access, and project mutations to agents rather than importing Node I/O modules into the workflow.
- Treat every `agent()` result as fallible; stopped or unrecoverable calls may produce `null`.
- Preserve stable input ordering when ordering affects replay, ranking, or result attribution.
- Bound loops with both a hard ceiling and a semantic stop condition when practical.
- Use comments for invariants or non-obvious runtime constraints, not to narrate syntax.

Do not run a workflow file through `node` and treat success or failure as authoritative validation. Claude's workflow runtime has its own injected primitives and execution semantics. Static checks should be advisory unless they model that runtime explicitly.

Completion criterion: the script is mostly orchestration, has bounded control flow, handles fallible agent results, and contains no assumed Node-only I/O path.

## Close the verification gap

Fan-out increases the chance that a good answer exists; it does not guarantee the system can identify it. Verification must have an **oracle** or at least evidence that discriminates candidates.

Prefer, in descending order:

1. deterministic tests, type checks, build results, parsers, or executable assertions;
2. comparison to a known-good implementation or invariant;
3. an independent verifier with access to the underlying artifact/evidence;
4. diverse reviewers with distinct criteria;
5. majority vote only when the task and evals show voting is calibrated.

A verifier should re-open the evidence, reproduce the claim, or test the artifact. Merely asking another agent “is this correct?” is correlated rephrasing, not independent verification.

When verification fails, represent the result explicitly as failed or unverified. Do not silently convert missing evidence into a negative or a pass.

Completion criterion: every high-impact reported claim or mutation has an evidence path that can distinguish a plausible wrong answer from a correct one.

## Design for interruption and replay

A workflow run is resumable only within the same Claude Code session, and replay follows agent start order. A running agent is not cached; cached reuse stops at the first unfinished agent and later-started agents rerun even if they had completed.

Design consequences:

- prefer reasonably sized work units over one giant agent when interruption is plausible;
- keep ordering stable enough that reruns remain understandable;
- make repeated stages safe to execute again when possible;
- avoid relying on “completed once” side effects that become harmful if replayed;
- split human sign-off boundaries into separate workflows because the runtime does not accept arbitrary mid-run user input.

Completion criterion: an interrupted run can replay later work without creating an unsafe or logically inconsistent end state.

## Evaluate the topology, not just the output

Run evals before declaring the workflow better than a single-agent baseline. Start small; large eval suites are not required to find large early effects.

Use representative cases and record at least:

- end-state task success;
- verified false positives / false negatives when applicable;
- token use;
- elapsed time;
- agent count and rounds;
- failure / null / retry behavior;
- variance across repeated runs.

Compare against the simplest credible baseline. Then ablate one choice at a time: verifier on/off, fan-out width, schema vs free-form output, stage model, stopping rule, or work-unit size.

For state-changing workflows, grade end state and discrete checkpoints rather than requiring one “correct” trajectory. Include negative controls that should not trigger edits or findings.

Completion criterion: the workflow earns its extra orchestration with measured improvement on the user's actual objective, not with a more elaborate trace.

## Review and prune

A saved workflow is executable policy. Keep each behavior in one place.

During review, hunt:

- **accidental serialism** — independent work awaited one item at a time;
- **false parallelism** — concurrent workers contend on the same mutable state;
- **verification gap** — many candidates, weak selection;
- **runaway width** — fan-out proportional to an unbounded input with no budget;
- **runaway depth** — iterative loops without semantic progress tests;
- **contract drift** — prompts and downstream code disagree about output shape;
- **replay hazard** — side effects become unsafe when a later stage reruns;
- **substrate mismatch** — Node, shell, or browser assumptions inside the workflow script itself;
- **version sediment** — old implementation details presented as current guarantees.

Delete orchestration that does not improve measured outcomes. A shorter workflow with a stronger oracle is usually preferable to a larger workflow with weak arbitration.

## Progressive disclosure

Read these only when the branch needs them:

- [`GLOSSARY.md`](GLOSSARY.md) — domain model and failure-mode vocabulary.
- [`references/EVIDENCE.md`](references/EVIDENCE.md) — dated empirical findings, documented runtime constraints, and conflicts in the evidence.
- [`references/JAVASCRIPT.md`](references/JAVASCRIPT.md) — JavaScript conventions and runtime-specific caveats.
- [`templates/fanout-verify.workflow.js`](templates/fanout-verify.workflow.js) — discovery → independent audit → adversarial verification.
- [`templates/fix-until-green.workflow.js`](templates/fix-until-green.workflow.js) — bounded evaluator/optimizer loop with a stall condition.
- [`evals/CASES.md`](evals/CASES.md) — cases for testing whether this skill improves workflow decisions rather than merely producing valid-looking JavaScript.
- [`scripts/lint-workflow.mjs`](scripts/lint-workflow.mjs) — conservative text-level lint for obvious hazards; it deliberately does not pretend to parse or execute Claude's workflow runtime.
