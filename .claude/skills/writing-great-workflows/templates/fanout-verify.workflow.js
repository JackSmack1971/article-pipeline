export const meta = {
  name: 'fanout-verify',
  description: 'Discover independent work units, inspect each one, then independently verify every candidate finding',
}

const DISCOVERY_SCHEMA = {
  type: 'object',
  required: ['items'],
  properties: {
    items: { type: 'array', items: { type: 'string' } },
  },
}

const REVIEW_SCHEMA = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['summary', 'evidence'],
        properties: {
          summary: { type: 'string' },
          evidence: { type: 'string' },
        },
      },
    },
  },
}

const VERIFY_SCHEMA = {
  type: 'object',
  required: ['verified', 'reason'],
  properties: {
    verified: { type: 'boolean' },
    reason: { type: 'string' },
  },
}

const discovered = await agent(
  'Identify the independent items that should be reviewed. Return only items inside the requested scope.',
  { schema: DISCOVERY_SCHEMA, label: 'discover' },
)

if (!discovered) return { status: 'error', stage: 'discover' }

const reviews = await pipeline(discovered.items, item =>
  agent(
    `Review ${item}. Report only concrete findings with evidence that a verifier can independently re-check.`,
    { schema: REVIEW_SCHEMA, label: `review:${item}` },
  ),
)

const candidates = reviews
  .filter(Boolean)
  .flatMap((review, index) =>
    review.findings.map(finding => ({
      item: discovered.items[index],
      finding,
    })),
  )

const verifications = await pipeline(candidates, candidate =>
  agent(
    `Independently verify this candidate against the underlying artifact. Do not trust the reviewer's conclusion.\n\n${JSON.stringify(candidate)}`,
    { schema: VERIFY_SCHEMA, label: `verify:${candidate.item}` },
  ),
)

return candidates
  .map((candidate, index) => ({ candidate, verification: verifications[index] }))
  .filter(entry => entry.verification?.verified === true)
