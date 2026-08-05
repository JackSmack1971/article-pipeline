# Pipeline Metadata

## Tool Degradation Log
- `[TOOL-UNAVAILABLE: code_execution]` matplotlib not installed in this environment. All 3 VIZ-CANDIDATE sections in article_spec.md (pricing comparison, benchmark scores, US AI capex) marked `[PLACEHOLDER-ONLY]`. Alt-text written inline by @engineer during drafting; no chart images generated this run.

## Gate History
- TRIAGE_THESIS_CONFIRM: thesis confirmed by user without rephrase (2026-08-03).
- APPROVAL: approved, 0 revision cycles (2026-08-03).
- RED_TEAM (POSTDRAFT): threat level MEDIUM (scope-overreach on "freedom from lock-in"), user selected "address" — one sentence added to conclusion distinguishing vendor lock-in from ecosystem/geopolitical dependency, changed section re-audited PASS.
- READER_SIMULATION (POSTDRAFT): accessibility rating MOSTLY ACCESSIBLE (3 HIGH / 2 MEDIUM / 1 LOW gaps), user selected "polish" — top 3 HIGH gaps resolved (benchmark-name definitions, MoE/active-parameter explanation, CUDA gloss), all 3 changed sections re-audited PASS.

## Revision Cycles
- Section 8 (conclusion): 1 targeted revision post-red-team.
- Sections 1, 3, 5: 1 targeted revision each post-reader-simulation polish pass.
(All within the 3-revision-cycle-per-gate limit; no HALT triggered.)

## KC Events
- KC-3 (source concentration): PASS — highest single-source share 10% (techstartups.com, 3/30 claims).
- KC-6 (vector insufficiency): PASS — 0/7 vectors INSUFFICIENT.

## Expedites
(none yet)

## Fact-Check Summary
- 8 claims verified in priority queue; 4 VERIFIED, 4 VERIFIED-UPDATED (more precise values), 1 OUTDATED (SKP-002, resolved via dispute DR-1), 0 DISPUTED, 0 UNVERIFIABLE.
- Dispute register: 1 entry (below 3-entry user-surfacing threshold).

## Drafting Summary
- 8 sections drafted with inline QA audit: 7 SECTION PASS, 1 SECTION PASS WITH NOTES (§6, ADV-10 quote resolution — CF/fact-check upgrade took precedence over stale spec exclusion note, documented in audit_log.md).
- Holistic audit (COMPLEX depth): PASS. No CRITICAL/MAJOR findings. Full report: `audit_report.md`.
- Consecutive BLOCKED audits: 0 (no HALT triggered).
- Final word count: 2,291 (within 1,800–3,200 range; spec estimate was ~3,050).

## Material Gate Decisions
- Red team (MEDIUM threat) → addressed via targeted conclusion revision.
- Reader simulation (MOSTLY ACCESSIBLE) → polished via targeted revision of 3 sections.
- SEO E-E-A-T checklist item 17 (author credentials) → FAILED; flagged to user, not resolved (cannot fabricate author identity). See `seo_package.md` E-E-A-T Gaps section.

## Token Delta
- Not independently instrumented in this environment; no KC-5 threshold breach observed across drafting or postdraft phases.
