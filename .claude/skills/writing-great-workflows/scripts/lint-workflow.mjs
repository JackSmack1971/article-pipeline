#!/usr/bin/env node
import fs from 'node:fs'

const path = process.argv[2]
if (!path) {
  console.error('Usage: node lint-workflow.mjs <workflow.js>')
  process.exit(2)
}

const source = fs.readFileSync(path, 'utf8')
const findings = []

const add = (level, rule, message) => findings.push({ level, rule, message })

if (!/export\s+const\s+meta\s*=/.test(source)) {
  add('error', 'meta', 'Missing `export const meta = ...`.')
}
if (!/\bname\s*:\s*['"`][^'"`]+['"`]/.test(source)) {
  add('warning', 'meta-name', 'Could not find a literal `meta.name`.')
}
if (!/\bdescription\s*:\s*['"`][^'"`]+['"`]/.test(source)) {
  add('warning', 'meta-description', 'Could not find a literal `meta.description`.')
}

const directIoPatterns = [
  [/from\s+['"]node:fs['"]|require\(['"](?:node:)?fs['"]\)/, 'filesystem module'],
  [/from\s+['"](?:node:)?child_process['"]|require\(['"](?:node:)?child_process['"]\)/, 'child_process module'],
  [/\bBun\.spawn\b|\bDeno\.Command\b/, 'runtime shell/process API'],
]
for (const [pattern, label] of directIoPatterns) {
  if (pattern.test(source)) {
    add('error', 'direct-io', `Found ${label}; workflow scripts should coordinate agents and let agents perform filesystem/shell I/O.`)
  }
}

if (/while\s*\(\s*true\s*\)|for\s*\(\s*;\s*;\s*\)/.test(source)) {
  add('error', 'unbounded-loop', 'Found an obviously unbounded loop. Add a semantic stop condition and a hard maximum.')
}

if (/\bagent\s*\(/.test(source) && !/\bif\s*\([^)]*!?\s*\w+[^)]*\)|\.filter\(Boolean\)|\?\./.test(source)) {
  add('info', 'nullability', 'Agent calls can produce `null`; confirm the script handles failed/stopped results where that matters.')
}

if (/\|\|\s*\d+/.test(source) && /args\??\./.test(source)) {
  add('info', 'defaulting', 'If zero is a valid argument, prefer `??` over `||` for defaults.')
}

if (/Promise\.all\s*\(/.test(source) && /agent\s*\(/.test(source)) {
  add('info', 'generic-concurrency', 'Generic Promise concurrency may be valid, but prefer documented workflow orchestration primitives when they express the same shape and improve observability/replay integration.')
}

console.log(JSON.stringify({ path, findings }, null, 2))
process.exit(findings.some(f => f.level === 'error') ? 1 : 0)
