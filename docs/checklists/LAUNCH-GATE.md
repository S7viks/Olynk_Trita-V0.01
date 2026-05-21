# Launch Gate Checklist (V0.0.1)

Use at **Week 16** go/no-go. Every item must be checked or explicitly waived with sign-off.

---

## Product

- [ ] **6+ sources production-grade** for pilot tenant (Shopify, Unicommerce, Tally, Shiprocket, CSV hub, Razorpay)
- [ ] **10 sources visible** in Sources UI with correct status badges
- [ ] **Decision Inbox** — accept / reject / snooze with required reject enum
- [ ] **Audit log** — immutable; timeline per decision
- [ ] **Tier-2 drafts** — PO + email on approve; Tier 3 disabled in config
- [ ] **Outcome jobs** — T+7 and T+14 running
- [ ] **4 reports** — aging, dead stock, reorder queue, data health (numbers match cards)
- [ ] **Causal L1+** on at least one card type in production pilot
- [ ] **Proactive feed** auto-populates from triggers
- [ ] **Email digest** — weekly + urgent cap tested
- [ ] **Chat** — inventory-scoped; refuses without evidence

---

## Engineering

- [ ] **Tenant isolation CI** green on `main`
- [ ] **No demo 502s** — Render health check 7d clean
- [ ] **Idempotent ingest** — webhook replay test pass
- [ ] **Idempotent decision emit** — dedup key enforced
- [ ] **Suppression** — ≤7 cards / 7 days verified
- [ ] **Integrity suppress** — stale Shopify/Uni blocks emit
- [ ] **OpenMeter** — all meters receiving events
- [ ] **Internal economics dashboard** — weekly per-tenant view
- [ ] **Red team report** — cross-tenant + hallucination documented
- [ ] **Load test** — 10 synthetic tenants ingest SLO met
- [ ] **Secrets** — OAuth encrypted; not in client bundles
- [ ] **Webhook HMAC** — verified for Shopify (and others live)

---

## Data & causal

- [ ] **Identity** — ≥90% order lines resolve for pilot (or blocked cards only)
- [ ] **COGS gate** — no ₹ impact when Tally unit cost missing
- [ ] **L3 label** — only when DoWhy refutation pass (manual audit 10 cards)
- [ ] **No simulation** — confirm no twin/forecast hero paths in prod config

---

## Commercial

- [ ] **Billing** — can charge ₹10,000+ / month
- [ ] **Legal** — privacy + terms published
- [ ] **Evidence pack template** — used for 3 pilots
- [ ] **≥1 paid conversion** OR signed LOI with conversion date + evidence path
- [ ] **Onboarding Day 0–7** — in-app checklist live

---

## Publish on launch day

- [ ] Landing page (Third Observer positioning)
- [ ] `app.` subdomain — inbox-first onboarding
- [ ] Connect guides + CSV templates
- [ ] Git tag `v0.0.1`

---

## Waivers

| Item waived | Reason | Approver | Date |
|-------------|--------|----------|------|
| | | | |
