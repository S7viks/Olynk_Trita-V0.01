# Scrutiny — Code Review Contract

**Reviewer** is a separate agent from the implementer. Verdict is recorded in [`HANDOFF.md`](HANDOFF.md) under **Scrutiny / Behavioral**.

---

## Required checks

### Security & tenancy

- [ ] `tenant_id` from JWT only — never from request body or unchecked query
- [ ] New tables/APIs covered by RLS or app filter + isolation test
- [ ] No secrets in diff; `.env` not committed
- [ ] `service_role` paths filter by `tenant_id`

### Deterministic engine

- [ ] No LLM path computes inventory qty, cover days, or ₹ impact
- [ ] Numbers trace to dbt/engine sources, not model free-text

### Decisions (when touching inbox/emit)

- [ ] Dedup key `(tenant, type, sku, week)` enforced
- [ ] Weekly cap ≤7 new cards / 7 days
- [ ] Integrity suppress when Shopify or Unicommerce stale past SLA
- [ ] Tier 3 external writes not enabled

### Causal (when touching causal)

- [ ] L3 only after DoWhy refutation pass per [`docs/context/causal-policy.md`](docs/context/causal-policy.md)
- [ ] UI labels match L0–L3 policy

### Process

- [ ] PR description includes feature ID (`F-*`)
- [ ] [`docs/features/REGISTRY.md`](docs/features/REGISTRY.md) status updated if applicable
- [ ] Pipeline registry updated if new job

---

## Verdict template

```markdown
### Scrutiny — [Feature Name] — [Date]
**Reviewer:** Scrutiny Chat #[N]
**Verdict:** PASS | FAIL

**Blockers (if FAIL):**
- ...

**Non-blocking notes:**
- ...
```

---

## FAIL rules

- Any security/tenancy blocker → **FAIL** until fixed
- VALIDATION assertion would be violated → **FAIL**
- Missing isolation test for new tenant-scoped surface → **FAIL**

Do not merge on FAIL. Re-run scrutiny after fix.
