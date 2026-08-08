# Research Context Summary

## Thesis
Chinese open-weight frontier models now offer real, verified cost and flexibility advantages over US closed-source models, but that flexibility carries embedded governance/security dependencies, while US labs retain a widening raw-compute moat — leaving the AI market's future genuinely divided between commoditizing pressure and scaling velocity.

## Confirmed Claims (CORROBORATED / UNCONTESTED)
- ADV-1/ADV-2 (T1/T2): Qwen3.8-Max is real — 2.4T-param MoE, 95B active/token, 1M context, $2/$6 per M tokens, launched Aug 3 2026; open weights promised, not yet published.
- ADV-3 (T2): Qwen pricing runs ~5–15x cheaper than US closed frontier models on API basis.
- ADV-6 (T2): UBS: Chinese models cost 15–20% of top-tier US products; enterprise adoption 0%→4% (Oct 2025–Mar 2026); DeepSeek token share <1%→17% in one month on one platform.
- ADV-9 (T1/T2): US 2026 AI capex: $660–690B (Big 5 hyperscalers); OpenAI $1.4T+ commitments; Anthropic multi-billion AMD/xAI compute deals.
- SKP-008 (T2, HIGH): China's National Intelligence Law (2017) obligates cooperation with state intelligence — Western DPAs cannot override this.
- SKP-010 (T2, HIGH): Peer-reviewed evidence of embedded political censorship (Taiwan/Tiananmen/Xinjiang) persisting in Chinese model weights even when self-hosted outside China.
- SKP-015/016 (T2): US frontier labs growing compute ~4x/year; absent chip exports, US compute capacity would be >10x China's in 2026.
- Hardware: China deliberately shifting to Huawei Ascend (DeepSeek V4, GLM-5 built for it); Huawei targeting 600K–750K chips in 2026 — but SKP-013/014 (T3): Ascend still ~2 years behind Nvidia; CANN not yet CUDA-competitive.

## Contested Claims (CONFLICTING / WEAKENED)
- C-1 (Cost, MEDIUM conf.): ADV-3/ADV-6 (cheap API pricing) vs. SKP-005/006/007 (self-hosting TCO underestimated 3–5x; only cheaper at high utilization/scale).
- C-2 (Enterprise risk vs. flexibility, HIGH conf. — thesis crux): ADV-4/6/7 (Apache 2.0 flexibility, growing adoption, "not inherently dangerous") vs. SKP-008/009/010/011/012 (NIL data exposure, Booz Allen code-vulnerability findings, embedded censorship travels with weights, lawmaker scrutiny).
- C-3 (Commoditization scope, MEDIUM conf.): ADV-8 (Atlantic Council: real capability gap) vs. SKP-017/018/019/020 (moats persist in distribution/integration/compute; adoption concentrated in cost-sensitive startups, not regulated enterprise; ~10% self-hosted share projected by 2027).
- Vector 1/3 (benchmarks, WEAKENED): ADV-5's mixed benchmark wins/losses are self-reported by Alibaba, not independently verified (SKP-001–004).

## Knowledge Gaps (INSUFFICIENT)
None — all 7 vectors returned adequate evidence both sides (KC-6 pass).

## Source Inventory
T1: Bloomberg | T1/T2: Futurum Group | T2: MarkTechPost, Developers Digest, BenchLM.ai, VentureBeat, Neowin, TechCrunch, Atlantic Council, Fortune, DataCenterDynamics, arXiv (x2), Fox News, PMC, PoPETS 2025, CEIAS, Epoch AI, AEI, Rest of World, Tech Startups, BigGo Finance | T3: Digital Applied, TechTimes, Azumo, GMI Cloud, Tech-Insider/Convequity, ChinaTalk, MindCast AI, Wikipedia (background)

## Editorial Flags Carried Forward
1. `[BREAKING-UNVERIFIED]` Qwen3.8-Max open-weight release date/license — unconfirmed as of Aug 3 2026.
2. `[QUOTE-UNVERIFIED]` ADV-10 "instrumental in creating itself" — exclude as direct quote.
3. Re-verify SKP-002's "zero benchmarks published" claim against Alibaba's latest release notes — may be stale within hours.
