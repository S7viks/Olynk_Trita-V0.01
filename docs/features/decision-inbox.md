# Feature: Decision Inbox

**IDs:** `F-INBOX-*`, `F-DEC-*`, `F-DRAFT-*`  
**Phase:** 2 (core), enriched Phase 3 (causal)

---

## User stories

1. As founder, I see ≤7 new inventory decisions per week, prioritized by ₹ at risk.
2. As ops, I approve a reorder and get a PO draft (Tier 2).
3. As founder, I reject with reason so Trita learns suppression patterns.
4. As ops, I see blocked cards when SKU mapping is wrong — not wrong reorder qty.

---

## Screens

### Decision Inbox (primary)

- Tabs: Open | Snoozed | Done
- Sort: ₹ impact desc (default), created_at, SKU
- Card preview: type, SKU name, ₹ floor, cover days, L0 fact line

### Card detail

| Section | Content |
|---------|---------|
| Impact | ₹ floor, horizon, assumptions |
| Facts | velocity, cover, aging (L0) |
| Drivers | L1/L2/L3 per causal-policy |
| Recommendation | qty, supplier, tier |
| Evidence | Links to report rows / raw lineage |
| Actions | Approve, Reject, Snooze 7d |
| Inaction | ₹ if ignored |

### Timeline

- emit → view → approve/reject → draft created → outcome T+7/T+14

---

## API endpoints (target)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/decisions` | List inbox |
| GET | `/api/v1/decisions/{id}` | Detail + reasoning |
| POST | `/api/v1/decisions/{id}/approve` | Audit + optional tier-2 |
| POST | `/api/v1/decisions/{id}/reject` | reason_enum required |
| POST | `/api/v1/decisions/{id}/snooze` | days param |
| GET | `/api/v1/decisions/{id}/timeline` | Audit entries |

---

## Suppression (must test)

| Test | Expected |
|------|----------|
| Same SKU+type+week | 1 card only |
| 8th card in 7 days | suppressed |
| Shopify failed SLA | 0 new inventory cards |
| Missing COGS | D-BLOCKED or no ₹ on CAPITAL |

---

## Tier 2 drafts

- Trigger: approve on REORDER with tier=2 setting
- PO draft: JSON schema validated before save
- Email draft: supplier template + SKU table
- **No** external API write

---

## Acceptance tests

- [ ] projection_hash stable for same metrics snapshot
- [ ] Reject without enum → 400
- [ ] Pilot records ≥1 accept or reject with audit row
- [ ] Report numbers == card numbers for same SKU set
