# Trita V0.0.1 — Master Context

Single source of product truth for builders. When code and this doc disagree, **fix code** then **update this doc**.

---

## Executive summary

| Item | Decision |
|------|----------|
| **Product** | Trita by OLynk — *Third Observer*; connected intelligence OS |
| **ICP** | ₹5–50 Cr Indian D2C (apparel, FMCG, beauty); founders + ops |
| **Wedge** | Inventory intelligence: stockouts, cover, aging, reorder, dead stock |
| **Moat** | Multi-source graph + grounded ₹ decisions + causal gates + proactive inbox |
| **V0.0.1** | Web app; 10 integrations listed; 6 production-grade at launch; no simulation |
| **Stack** | Next.js · FastAPI · Supabase · dlt/dbt · LiteLLM (Gemini/Groq) · OpenMeter |
| **Launch gate** | 1 paying @ ₹10K+ · ≥₹50K pilot impact · ≥1 accepted inventory decision |

### One-line pitch

> Trita connects the 10 tools you already use into one live graph, warns you before stockouts with ₹-backed decisions you can approve or reject, and explains *why* — with evidence, not vibes.

### Team sentence

**V0.0.1 ships a web-first Trita that fuses the 10 apps Indian D2C brands already use into one graph, proactively surfaces grounded inventory decisions with optional causal drivers, and proves ₹ impact through approve/reject audit — before mobile, simulation, or autonomous execution.**

---

## What Trita is / is not

| Not | Is |
|-----|-----|
| D2C analytics / BI dashboard | Tenant-scoped **business graph** |
| Generic AI copilot | **Decision Inbox** + audit/approve |
| Simulation / digital twin | **Proactive advisor** (web-first) |
| Ask anything per tenant | **Inventory-scoped** narrow chat |

**Name:** Sanskrit **त्रित** = *The Third* · **Third Observer:** brand sees intent, market sees outcomes, Trita sees **causality** across connected data.

---

## In scope (V0.0.1)

| Layer | Deliverable |
|-------|-------------|
| Connect | 10 apps + CSV hub + integration health |
| Graph | Commerce + logistics + finance + ads (wide internal, narrow UX) |
| Analyze | Deterministic inventory + association + causal refutation |
| Decide | Decision Inbox (inventory only), suppression, audit |
| Act | Tier 1 suggest · Tier 2 drafts (PO/email) · Tier 3 **off** |
| Explain | Reports (evidence) + narrow grounded chat |
| Proactive | Triggers → inbox → email/Slack digest |
| Operate | Tenant isolation, DQ, observability, unit economics |

---

## Out of scope (V0.0.1)

- Simulation / digital twin / L5 kernel
- RL / auto policy training
- Mobile app, WhatsApp-first
- Tier-3 auto-write to external systems
- Full logistics/finance **product modules** (data in graph; UI later)
- 25 connectors day one
- Cross-tenant benchmarks
- Auto-spawn agents per tenant

---

## Customer promise vs engineering truth

| Audience | Message |
|----------|---------|
| **Market** | “10 apps integrated.” |
| **Engineering** | **6 production-grade** at launch; remainder **CSV or beta API** with honest health badges until connector factory is stable. |

**Production-grade connectors (launch):** Shopify, Unicommerce, Tally (CSV), Shiprocket, CSV hub, Razorpay.

---

## The 10 applications (canonical)

| # | App | Graph role |
|---|-----|------------|
| 1 | Shopify | Orders, SKUs, storefront inventory |
| 2 | Unicommerce | Warehouse truth, committed stock |
| 3 | Tally | COGS, unit cost, payables |
| 4 | Shiprocket | Shipments, NDR/RTO, delays |
| 5 | Delhivery | Carrier lane, transit/RTO |
| 6 | Razorpay | Settlements, payout timing |
| 7 | Meta Ads | Spend → lagged demand |
| 8 | Google Ads | Same |
| 9 | GA4 | Traffic / conversion priors |
| 10 | Amazon Seller Central | Marketplace channel |

**Swaps:** WooCommerce (#10 alt), Cashfree (#6 alt).

---

## Core principles (implementation)

1. **Causal discipline** — L0–L3 labels; L3 only after DoWhy refutation pass; no simulation.
2. **Math ownership** — Deterministic engine owns all numbers; LLM owns language only.
3. **Integrity before advice** — Unresolved identity or missing COGS → `INVENTORY_BLOCKED`, not guesses.
4. **Proactive without spam** — Dedup, weekly cap, integrity suppress.
5. **Web-first** — In-app feed P0; email/Slack P1; WhatsApp V0.0.2+.
6. **Unit economics visible** — OpenMeter from day one; cost per accepted decision tracked.

---

## Success metrics (60 days post-launch)

| Metric | Target |
|--------|--------|
| Paying customers | ≥1 @ ₹10K+ |
| Pilot ₹ impact | ≥₹50K conservative |
| Time to first decision | ≤7 days from connect |
| Decision acceptance rate | ≥30% surfaced (post-tuning) |
| Connectors healthy | ≥6/10 green per tenant |
| Cross-tenant incidents | 0 |
| LLM cost % of MRR | <30% at Starter |

---

## Reference pilots

Organik Truck, Manaca, TAOS — 45-day pilot, evidence packs weekly.

---

## Related docs

- [architecture.md](./architecture.md)
- [data-graph.md](./data-graph.md)
- [decision-contract.md](./decision-contract.md)
- [causal-policy.md](./causal-policy.md)
- [integrations.md](./integrations.md)
- [agents.md](./agents.md)
- [stack-oss.md](./stack-oss.md)
- [../roadmap/00-overview.md](../roadmap/00-overview.md)
