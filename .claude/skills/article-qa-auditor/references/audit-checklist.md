# Audit Checklist — Severity Reference

SKILL.md's Inline and Holistic checklists carry their own severity tags and are
authoritative for verdict determination on every run. This file holds the severity
taxonomy those tags draw from, plus elaboration too long to repeat inline.

## Severity Definitions

| Level | Meaning | Blocks Section? |
|-------|---------|-----------------|
| [CRITICAL] | Factual error, fabricated citation, unresolved CONFLICTING claim, silent conflict resolution | Yes — SECTION BLOCKED |
| [MAJOR] | Missing citation on factual claim, [Unverified] presented as fact, spec deviation > 30%, word budget > 30% over, missing source URL | Yes — SECTION BLOCKED |
| [MINOR] | Citation format non-standard, word budget 15–30% over, transition quality | No — SECTION PASS WITH NOTES |
| [STYLE] | Prohibited phrase, wrong emphasis type, passive construction | No — SECTION PASS WITH NOTES |
| [URL-MISSING] | No URL available for a cited source | [MAJOR] — SECTION BLOCKED |

## Elaboration

**Phrase link spot-check (holistic only):** For any section citing multiple documents from
the same organization, verify each phrase link URL leads to the specific document that
contains the cited claim — not a different document from the same org. Right source
family, wrong specific document is a `[MAJOR]` finding. Method: hover-check the URL
against the attributed claim. The linked document must contain the specific figure,
quote, or finding cited.
