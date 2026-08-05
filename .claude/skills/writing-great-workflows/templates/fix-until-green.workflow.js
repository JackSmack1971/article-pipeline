export const meta = {
  name: 'fix-until-green',
  description: 'Run a checker and repair failures until it passes, stalls, or reaches a hard round limit',
}

const MAX_ROUNDS = args?.maxRounds ?? 5

const CHECK_SCHEMA = {
  type: 'object',
  required: ['ok', 'fingerprint', 'failures'],
  properties: {
    ok: { type: 'boolean' },
    fingerprint: { type: 'string' },
    failures: { type: 'array', items: { type: 'string' } },
  },
}

let previousFingerprint = null

for (let round = 1; round <= MAX_ROUNDS; round++) {
  const check = await agent(
    'Run the authoritative project check. Return whether it passes, a stable fingerprint of the remaining failures, and concise failure identifiers.',
    { schema: CHECK_SCHEMA, label: `check:${round}` },
  )

  if (!check) return { status: 'error', stage: 'check', round }
  if (check.ok) return { status: 'passed', round }

  if (check.fingerprint === previousFingerprint) {
    return { status: 'stalled', round, failures: check.failures }
  }

  previousFingerprint = check.fingerprint

  const repair = await agent(
    `Fix only these currently verified failures, then stop so the next round can re-run the authoritative check:\n${JSON.stringify(check.failures)}`,
    { label: `repair:${round}` },
  )

  if (!repair) return { status: 'error', stage: 'repair', round }
}

return { status: 'max-rounds', rounds: MAX_ROUNDS }
