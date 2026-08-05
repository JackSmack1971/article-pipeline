# JavaScript for Claude Code Dynamic Workflows

This reference separates general JavaScript practice from Claude's workflow substrate. The objective is readable orchestration, not maximal language cleverness.

## 1. Treat the runtime as JavaScript-shaped, not Node-equivalent

Current Claude Code documentation describes saved workflow bodies as plain JavaScript with top-level `await`, while also imposing runtime-specific constraints: the workflow script itself does not directly access filesystem or shell; agents perform I/O. The runtime injects workflow primitives such as `agent()` and `pipeline()`.

Consequences:

- Do not import `node:fs`, `child_process`, or similar modules as an architectural assumption.
- Do not use `node --check` as a pass/fail validator for a workflow file. The runtime may support script-level semantics that ordinary Node modules do not model.
- Prefer documented workflow primitives over clever Promise choreography when the primitives express the intended orchestration and make progress/replay visible.

## 2. Use `const` by default

Use `const` for stage results, schemas, labels, and derived collections. Use `let` only where the binding intentionally evolves (round counter state, previous fingerprint, aggregate accumulator). This narrows the mutation surface and makes replay reasoning easier.

Remember: `const` makes the binding non-reassignable; it does not freeze the object. Avoid mutating shared objects across stages when returning a new object or array is clearer.

## 3. Make nullability explicit

Current workflow docs state that `agent()` may resolve to `null` when stopped or after an unrecoverable API error, and `pipeline()` preserves that `null` in the result array.

Patterns:

```js
const results = await pipeline(items, item => agent(`...${item}...`))
const completed = results.filter(Boolean)
```

If dropping failed units would hide an important gap, do not blindly filter them. Preserve the input alongside the result or return an explicit status so the final output can say which units were unverified.

## 4. Prefer schemas at control-flow boundaries

When downstream JavaScript will branch, sort, filter, group, or loop based on an agent result, request a JSON schema. At minimum:

- declare `type`;
- declare `required` fields that control flow depends on;
- constrain arrays/items and enums where useful;
- keep the schema narrow enough that a human can inspect it quickly.

Schema-driven output is a contract, not a guarantee of semantic truth. Verify important fields against underlying evidence.

## 5. Preserve falsy values intentionally

Use optional chaining (`?.`) when a value may be absent, and nullish coalescing (`??`) when only `null`/`undefined` should trigger a default. Avoid `||` for defaults when `0`, `false`, or `''` are legitimate values.

Example:

```js
const maxRounds = args?.maxRounds ?? 4
```

## 6. Parallelize dependencies, not syntax

General JavaScript guidance correctly warns that independent async operations awaited one-by-one can become accidentally serial. But a workflow should use the runtime's documented orchestration primitives when possible, because they integrate with workflow limits, progress, and replay semantics.

Do not translate every `await` in a loop into generic `Promise.all()`. Sequential `await` is correct when the next iteration depends on the prior result, when it mutates shared state, or when a bounded evaluator/optimizer loop is intentional.

## 7. Bound loops twice

For iterative workflows, use:

- a semantic stop condition (`ok`, no new findings, unchanged error fingerprint); and
- a hard maximum round count.

Example shape:

```js
for (let round = 1; round <= MAX_ROUNDS; round++) {
  const check = await agent('...', { schema: CHECK_SCHEMA })
  if (!check) return { status: 'error', reason: 'checker failed' }
  if (check.ok) return { status: 'passed', round }
  if (check.fingerprint === previousFingerprint) {
    return { status: 'stalled', round, remaining: check.items }
  }
  previousFingerprint = check.fingerprint
  await agent('Fix only the reported items ...')
}
```

A hard cap prevents runaway cost; the progress test prevents pointless cost.

## 8. Keep ordering stable when it carries meaning

Array methods and Promise combinators preserve result ordering by input position even when work completes out of order. Workflow replay is also start-order-sensitive. Avoid incidental reordering before launching work when labels, resume behavior, or attribution depend on a stable mapping.

If you intentionally rank or shuffle work, make that choice explicit and document why.

## 9. Make prompts small interfaces

A good work-unit prompt resembles a function contract:

- objective;
- exact scope;
- allowed evidence / tools if relevant;
- output schema;
- completion test;
- explicit exclusions only when they prevent costly scope expansion.

Avoid embedding every prior stage's transcript. Pass only the fields needed for the next decision.

## 10. Prefer readable data transforms

Use `map`, `filter`, `flatMap`, destructuring, and small predicate functions where they reveal the orchestration. Avoid dense chained expressions that mix prompt construction, agent execution, error handling, ranking, and verification in one statement.

The best workflow script should read like a compact execution plan.

## Sources

- Claude Code Dynamic Workflows documentation, current as of 2026-08-03.
- MDN: `const`, top-level `await`/modules, `Promise.all`, optional chaining, nullish coalescing.
- ESLint: `no-await-in-loop` (including its documented exceptions).
- JSON Schema Draft 2020-12 validation vocabulary.
