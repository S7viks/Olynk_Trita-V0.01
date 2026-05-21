# Phase 4 — Ten Apps + Hardening (Weeks 12–14)

**Goal:** All 10 sources in UI with honest badges; production reliability and security pass.

**Exit:** All 10 listed in Sources UI; load test + red team documented.

---

## Connectors

| Connector | Mode | Task |
|-----------|------|------|
| `C-GA4` | API daily | Traffic in SKU-week matrix |
| `C-AMAZON` | CSV → SP-API beta | Marketplace orders/inventory |

---

## Work packages

### WP4-A — Complete connector set

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P4-001 | GA4 dlt tap + staging | `Session` features in matrix |
| T-P4-002 | Amazon CSV path (production) | Orders in graph |
| T-P4-003 | Amazon SP-API beta flag | Badge: beta |
| T-P4-004 | Sources UI: 10 rows + legend | Market promise = honest |

**Features:** `F-CONN-009`, `F-CONN-010`

---

### WP4-B — Orchestration hardening

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P4-010 | All jobs idempotent | Re-run no duplicate cards |
| T-P4-011 | Backfill strategy documented | Per connector |
| T-P4-012 | LLM call dedup on job retry | OpenMeter accurate |

**Pipelines:** Review all in [../pipelines/REGISTRY.md](../pipelines/REGISTRY.md)

---

### WP4-C — Load & security

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P4-020 | Synthetic 10-tenant load test | Ingest SLO met |
| T-P4-021 | Red team: cross-tenant | Documented pass |
| T-P4-022 | Red team: LLM hallucination | Refuse without evidence |
| T-P4-023 | Red team: prompt injection in chat | Scoped tools only |

**Features:** `F-SEC-001`, `F-SEC-002`

---

### WP4-D — Pilot evidence pack

| Task ID | Task | Done when |
|---------|------|-----------|
| T-P4-030 | Weekly ₹ report template | Conservative methodology |
| T-P4-031 | Auto-fill from outcomes T+7/14 | Ops can send to pilot |
| T-P4-032 | Internal unit economics dashboard | Per-tenant weekly |

**Features:** `F-OPS-001`, `F-OPS-002`

---

## Deliverables checklist

- [ ] GA4 + Amazon in graph (minimum CSV)
- [ ] 10 sources in UI with correct badges
- [ ] Idempotent orchestration
- [ ] Load test report
- [ ] Red team report
- [ ] Evidence pack generated for 3 pilots

---

## References

- [../checklists/LAUNCH-GATE.md](../checklists/LAUNCH-GATE.md)
