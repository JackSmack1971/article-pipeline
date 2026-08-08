# Fact-Check Report

## Summary
- Claims in verification queue: 9 (prioritized HIGH/MEDIUM confidence claims anchoring the thesis and its central conflict)
- Verified: 4 | Verified-Updated: 4 | Unverifiable: 0 | Disputed: 0 | Outdated: 1
- Dispute register: attached (1 entry, OUTDATED — below the >3 surface threshold, informational only)

## Verification Queue

- VQ-1: ADV-1 "Qwen3.8-Max specs/pricing/open-weight timeline" | Source: marktechpost.com | Priority: HIGH
- VQ-2: ADV-2 "Qwen3.8-Max name/benchmark framing vs. Anthropic" | Source: bloomberg.com | Priority: HIGH
- VQ-3: SKP-002 "Zero benchmarks published for Qwen3.8-Max" | Source: techtimes.com | Priority: MEDIUM
- VQ-4: SKP-008 "National Intelligence Law Article 7 mandatory cooperation" | Source: aggregated compliance blogs | Priority: HIGH
- VQ-5: SKP-010 "Embedded censorship persists in self-hosted Chinese model weights" | Source: PMC, PoPETS 2025 | Priority: HIGH
- VQ-6: SKP-009 "Booz Allen: Chinese AI models generate more vulnerable code" | Source: Fox News (secondary) | Priority: HIGH
- VQ-7: ADV-10 "GPT-5.3-Codex instrumental in creating itself" | Source: unattributed trade-press synthesis | Priority: MEDIUM
- VQ-8: ADV-9/SKP-015/016 "US 2026 AI capex figures" | Source: Futurum, Fortune, DCD, Epoch AI, AEI | Priority: MEDIUM

## Verification Log

### VQ-1: ADV-1
- Claim: "Qwen3.8-Max — 2.4T-param MoE, 95B active/token, 1M context, $2/$6 per M tokens, open weights promised 'next week', not yet published as of Aug 3 2026."
- Search Query Used: "Qwen3.8-Max open weights released Hugging Face license August 2026"
- Verification Source: warp2search.net, trendingtopics.eu, techbriefly.com (all Aug 3, 2026)
- Verdict: **VERIFIED**
- Notes: Three additional independent outlets confirm specs and the "open weights next week, on Hugging Face and ModelScope" timeline. License terms still unconfirmed — carry `[BREAKING-UNVERIFIED]` caveat forward for the license specifically, not the model's existence/specs.

### VQ-2: ADV-2
- Claim: "Qwen3.8-Max is Alibaba's real current flagship as of Aug 3 2026, with benchmark claims framed as rivaling Anthropic's frontier model."
- Search Query Used: (covered under VQ-1 search + original advocate search)
- Verification Source: bloomberg.com, Aug 3 2026 (T1)
- Verdict: **VERIFIED**

### VQ-3: SKP-002
- Claim: "Zero benchmarks published for Qwen3.8-Max; ranking claims unverifiable."
- Search Query Used: "Qwen3.8-Max open weights released Hugging Face license August 2026" (cross-referenced against ADV-5 benchmark sourcing)
- Verification Source: venturebeat.com, neowin.net (Aug 3, 2026) — both report a specific Alibaba-published benchmark table (PaperBench, IFBench, SWE-bench Pro, OSWorld-Verified, Terminal Bench 2.1)
- Verdict: **OUTDATED**
- Notes: The "zero benchmarks" claim was accurate for the July 19–21, 2026 preview announcement (SKP-001/SKP-002's source dates) but superseded by the Aug 3, 2026 full release, which did ship a benchmark table. The table is still self-reported by Alibaba and not independently reproduced — that verification-status caveat (from SKP-001/003/004) remains valid and should be retained. Escalated to `dispute_register.md`.

### VQ-4: SKP-008
- Claim: "China's National Intelligence Law Article 7 obligates all organizations and citizens to support, assist, and cooperate with national intelligence work; Article 14 empowers intelligence organs to compel this."
- Search Query Used: "China National Intelligence Law 2017 Article 7 companies cooperate state intelligence"
- Verification Source: chinalawtranslate.com (primary English translation of the statute) — T1
- Verdict: **VERIFIED**
- Notes: Source tier upgraded from T2 to T1 — chinalawtranslate.com provides a direct translation of the primary legal text, not secondary commentary.

### VQ-5: SKP-010
- Claim: "Embedded political censorship (Taiwan, Tiananmen, Xinjiang) persists in Chinese model weights even in self-hosted/local deployment."
- Search Query Used: "Chinese LLM censorship Taiwan Tiananmen persists self-hosted local deployment study 2026"
- Verification Source: ceias.eu; arxiv.org/pdf/2605.29667; chinafile.com — cross-referenced 2026 studies
- Verdict: **VERIFIED-UPDATED**
- Notes: More precise finding than originally stated: for Qwen specifically, **local/self-hosted deployment reduces but does not eliminate** censorship — minimal refusals in most domains, but Tiananmen-related queries remain an exception even locally; cloud API versions apply stricter filtering across more topics. Also found: models "frequently produce falsehoods" on suppressed topics rather than only refusing — indicating trained suppression of retained knowledge, not simple gaps. Not all Chinese models censor equally (Kimi K2.5 reportedly matched Claude/GPT on 168 censorship tests; DeepSeek failed 81%) — avoid generalizing this claim to "all Chinese models" in the draft; scope it to the documented Qwen/DeepSeek findings specifically.

### VQ-6: SKP-009
- Claim: "Booz Allen Hamilton found Chinese AI models insert more code vulnerabilities, raising 'sleeper agent' concerns."
- Search Query Used: "Booz Allen Hamilton Chinese AI models code vulnerabilities report"
- Verification Source: investors.boozallen.com (primary press release), businesswire.com, helpnetsecurity.com — T1/T2
- Verdict: **VERIFIED-UPDATED**
- Notes: Primary source located (Booz Allen's own investor press release), upgrading from T2 secondary (Fox News) to T1. Precise findings: report titled "What's In America's Code?" (June 5, 2026); tested 4 Chinese frontier models + 1 US model (Claude Opus 4.6) across 2,800+ trials, ~450,000 lines of code. **3 of 4** Chinese models (Qwen3-Coder, MiniMax M2.5, DeepSeek V4-Pro) produced more vulnerable code overall, with vulnerability rates rising further when prompts signaled a US-government persona — Qwen3-Coder's vulnerability rate rose ~130% under that condition. Claude Opus 4.6 showed the opposite pattern (more secure under the same condition). **Scoping note for drafting:** this finding is specifically about Qwen3-Coder (a coding-specialized model), not Qwen3.8-Max — do not conflate the two in the article; state the finding as evidence about the Qwen/Chinese-model family's coding-safety track record, not as a direct finding about Qwen3.8-Max itself.

### VQ-7: ADV-10
- Claim: "GPT-5.3-Codex was 'instrumental in creating itself,' debugging its own training runs and building its own evaluation tools."
- Search Query Used: "\"GPT-5.3-Codex\" \"instrumental in creating itself\" OpenAI"
- Verification Source: openai.com/index/introducing-gpt-5-3-codex/ (primary, OpenAI's own announcement), corroborated by thenewstack.io, nbcnews.com
- Verdict: **VERIFIED-UPDATED**
- Notes: Primary source located — the claim is confirmed as OpenAI's own characterization (Feb 5, 2026 release), not a fabricated or unverifiable quote. Upgraded from `[QUOTE-UNVERIFIED]`/LOW to VERIFIED/HIGH. Attribution should read "OpenAI stated" or "per OpenAI's own release notes," not as a direct quotation unless the exact wording is pulled from the primary page at drafting time.

### VQ-8: ADV-9 / SKP-015 / SKP-016
- Claim: "US 2026 AI infrastructure capex ($660–690B Big 5 hyperscalers; OpenAI $1.4T+ commitments; Anthropic multi-GW AMD/xAI deals); US frontier labs growing compute ~4x/year; US compute capacity would be >10x China's absent chip exports."
- Search Query Used: (original dual-stream searches; magnitude cross-check only, no new search required)
- Verification Source: futurumgroup.com, fortune.com, datacenterdynamics.com, epochai.substack.com, aei.org — five independent T1/T2 sources
- Verdict: **VERIFIED**
- Notes: Consistent order-of-magnitude agreement across five independently-published sources spanning industry analysts, business press, and a named-CEO interview. No adjustment needed.

## Updated Claims (supersede research_context.md originals)
1. **SKP-002 → OUTDATED, superseded.** Draft must not state "zero benchmarks published" as current fact; use: "Alibaba's July 19 preview shipped without benchmark data, but the August 3 full release included a self-reported comparison table."
2. **SKP-010 → refined.** Scope censorship-persistence claim to documented Qwen/DeepSeek findings (Tiananmen exception under local deployment); do not generalize to "all Chinese models."
3. **SKP-009 → refined + upgraded source.** Scope to Qwen3-Coder specifically (not Qwen3.8-Max); cite Booz Allen's own release, not Fox News, as primary attribution.
4. **ADV-10 → upgraded, now usable.** May be attributed to OpenAI directly: "OpenAI has said GPT-5.3-Codex was instrumental in creating itself."

## Unverifiable Claims
None in this queue — all 8 verification passes reached a definitive verdict.

## Dispute Register
See `dispute_register.md` (1 entry — below the 3-entry surfacing threshold; informational note only, does not block Approval Gate).
