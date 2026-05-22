# trita-decisions

Decision contract, deterministic emitter, suppression (F-DEC-001..004).

## Card types

- `INVENTORY_REORDER` — `stockout_risk`
- `INVENTORY_DEAD_STOCK` — `dead_stock`
- `INVENTORY_CAPITAL_TRAP` — slow velocity + capital ≥ ₹5k
- `INVENTORY_BLOCKED` — missing COGS on actionable flags

## Rules

- Dedup: `(tenant_id, type, sku_id, ISO week)` → `suppression_key`
- Cap: ≤7 new cards per rolling 7 days per tenant
- Integrity: no emit when Shopify or Unicommerce is `degraded`/`failed` (connected)
- Tier 3 execution disabled (`execution.tier` = 1 only)

## Usage

```python
from trita_decisions import emit_decisions

with conn:
    result = emit_decisions(conn, tenant_id)
```

```bash
python scripts/emit_decisions.py
```

API: `POST /v1/decisions/emit`, `GET /v1/decisions?tab=open|snoozed|done`, `GET /{id}`, `POST /{id}/approve|reject|snooze`, `GET /{id}/timeline`

Web: `/inbox` (F-INBOX-001..004)
