# Evaluating Claude Code project subagents

A subagent is not validated by reading its Markdown. Validate the **delegation contract** at four layers: discovery, routing, boundary, and outcome.

This protocol is intentionally harness-independent. It can be run manually in Claude Code, scripted with non-interactive invocations, or adapted to an evaluation framework.

## 1. Write the success contract before the prompt

For each agent, record four statements:

```text
ROUTE: Tasks of type X should select this agent; neighboring type Y should not.
BOUNDARY: The worker may do A/B/C and cannot do D/E.
OUTCOME: A successful run leaves state/result Z, proven by checks Q.
RETURN: The parent receives fields R1/R2/R3 and no raw exploration dump.
```

If any statement is vague, authoring is premature. You cannot tell whether a prompt change improved behavior without a success definition.

## 2. Discovery and parse check

Goal: prove Claude Code loaded the definition you think it loaded.

Checklist:

- File is under the intended `.claude/agents/` project scope.
- YAML frontmatter parses.
- `name` and `description` exist.
- No same-name project agent unintentionally shadows it.
- The session was restarted if the `agents` directory itself was created after session start.
- `claude doctor` / `/doctor` reports no relevant duplicate or configuration issue.
- When debugging discovery, use Claude Code debug facilities before rewriting a correct agent prompt.

**Pass:** the exact intended agent identity is available to explicit invocation and diagnostics show no relevant discovery error.

## 3. Explicit invocation suite

Explicitly select the agent for representative tasks. This isolates worker quality from router quality.

Create 3–10 tasks spanning:

- ordinary happy path;
- one ambiguous input;
- one incomplete-input case where repository inspection should resolve the gap;
- one edge case that tests the agent's scope boundary;
- one failure case where the correct result is “cannot safely conclude” or a handoff.

Grade:

- Did it inspect the required sources?
- Did it stay inside its role?
- Did it use permitted tools correctly?
- Did it meet the completion criterion?
- Is the returned result compact and sufficient?

Prefer outcome checks over exact transcript matching. A correct worker may reach the same verified state through different valid tool sequences.

## 4. Routing suite

Routing evals answer a different question: _does the parent choose this worker when it should?_

Create two balanced sets.

### Should route

Use prompts that vary surface wording while preserving intent:

```text
Review whether this migration can lock the users table during deploy.
Check rollback safety for the new schema change.
Before merge, assess backward compatibility of these migrations.
```

### Should not route

Use near-neighbor prompts, not obviously unrelated ones:

```text
Implement the migration and update the ORM model.
Explain how this schema works to a new engineer.
Deploy the approved migration to staging.
```

The negative set is essential. A description that routes everything is not “high recall”; it is a broken partition.

### Repeated trials

Run multiple trials per prompt because model routing is stochastic and can change with model/version. A practical small regression suite can use three trials per case and require all three for high-confidence operational routes. For exploratory capability work, track pass rate instead of requiring perfection.

Record separately:

- correct auto-delegation;
- wrong-agent delegation;
- no delegation;
- explicit invocation success.

This separation tells you whether a regression is in the worker or the router.

## 5. Capability-boundary suite

Test capabilities by action, not by reading frontmatter.

For every important allowed capability:

- provide a task that genuinely requires it;
- verify the worker can execute it and finish.

For every important denied capability:

- provide a task or adversarial instruction that would tempt the action;
- verify the runtime prevents it or the configured gate reliably intercepts it.

Examples:

- A review-only agent should not be able to edit files if read-only is a hard requirement.
- A worktree-isolated implementer should make repository changes in its isolated worktree, not the main checkout.
- A deployment guard hook should be tested by an attempted deployment command on the exact platform/version in use.

**Pass:** required actions remain possible; prohibited actions are prevented by runtime control rather than prompt goodwill.

## 6. Fresh-context suite

Test whether the worker silently depends on parent history.

Procedure:

1. In the parent conversation, discuss a non-obvious constraint.
2. Invoke the worker with a delegation message that does **not** restate that constraint.
3. Ask whether the worker can discover the constraint from project-visible truth.
4. If not, decide whether the constraint belongs in the agent body/project instructions or must be passed in every handoff.

A good project subagent should succeed from its durable contract plus discoverable project state and the task-specific delegation message—not luck about conversation inheritance.

## 7. Outcome graders

Use the cheapest deterministic grader that proves the result.

Examples:

- implementation agent: targeted tests, type/lint checks, expected file diff;
- code reviewer: planted defects detected, false-positive budget, cited file/line evidence;
- migration reviewer: known unsafe migration identified, safe control accepted, rollback risk correctly classified;
- documentation researcher: required primary sources cited, unsupported claims rejected;
- refactor agent: behavioral tests unchanged, public API preserved, complexity metric or static check improved.

Use model-based grading only for qualities that deterministic checks cannot capture cleanly, and calibrate it against human judgment on a sample.

## 8. Return-contract grader

The parent should receive the smallest useful artifact.

A generic return rubric:

```text
PASS if the final message contains:
- decision or completed outcome;
- evidence needed to trust it;
- verification performed and result;
- changed files/artifacts when applicable;
- unresolved risks or blockers.

FAIL if it primarily contains:
- raw search logs;
- long file dumps;
- detailed internal chronology;
- repeated context the parent already has;
- a claim of success without verification evidence.
```

Tune the rubric per worker. The return contract is part of context engineering, not merely style.

## 9. Regression bank

Every real failure becomes a named test case.

Store at minimum:

```yaml
id: route-migration-vs-implementation-001
prompt: "Implement the migration and update the ORM model."
expected_agent: not:migration-reviewer
checks:
  - migration-reviewer is not selected automatically
reason: "Regression from description broadened during 2026-08 tuning"
```

Keep capability and regression suites separate:

- **Capability suite:** hard/new cases that reveal what the agent can learn to do better.
- **Regression suite:** previously working contracts that should remain near-perfect.

When editing only the description, still run worker regression tests: description edits sometimes accompany other file changes, model upgrades, or parser changes. When editing the body, still run routing tests: repository architecture may have changed around the agent.

## 10. Upgrade protocol

Claude Code mechanics and model behavior change frequently. After a material CLI/model upgrade:

1. Run discovery/parse checks across all project agents.
2. Run the routing regression suite with the new default model.
3. Run hard-boundary tests for permissions/hooks/isolation.
4. Run a representative outcome subset.
5. Inspect failures before rewriting prompts; first determine whether the change is discovery, routing policy, capability resolution, or worker reasoning.
6. Update the dated mechanics in [`REFERENCE.md`](REFERENCE.md) only after verifying the new behavior against official docs and local tests.

## Minimal scorecard

| Dimension | Target | Notes |
|---|---:|---|
| Discovery | 100% | Intended definition loads; no ambiguous duplicate |
| Explicit worker outcome | Project-defined | Prefer deterministic outcome checks |
| Should-route precision | High | Near-neighbor negatives matter most |
| Should-route recall | High | Measure separately from explicit success |
| Hard-boundary enforcement | 100% for critical controls | Test exact version/platform |
| Return contract | Near 100% | Parent gets enough evidence without context flood |
| Regression suite | Near 100% | Failures should block risky prompt/config changes |

Do not optimize a single aggregate score until you can see each dimension separately. A worker with perfect output but poor routing is broken; a router with perfect selection but an overpowered worker is also broken.
