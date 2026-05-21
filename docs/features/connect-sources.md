# Feature: Connect & Sources

**IDs:** `F-CONN-*`, `F-UI-SOURCES`, `F-CONN-005` / `F-CSV-HUB`  
**Phases:** 0–4

---

## User stories

1. As ops, I connect Shopify and see green health within 4h SLA.
2. As founder, I upload **any** operations CSV (Tally, marketplace export, WMS dump) and see validated rows in the graph or explicit quarantine errors.
3. As ops, I see which of 10 apps are production vs beta vs CSV-capable — **no fake “connected” states**.

---

## UI: Sources page

| Element | Behavior |
|---------|----------|
| Row per connector | Logo, name, status badge, last sync, row count 24h |
| Connect CTA | OAuth or **CSV hub upload** (routes through `F-CONN-005`) |
| Detail drawer | SLA, error message, **quarantine count**, re-sync button |
| Legend | Production / Beta / CSV-capable |

**Status badge rules**

| Badge | Condition |
|-------|-----------|
| Healthy | sync within SLA; CSV: last upload validated with acceptable quarantine rate |
| Degraded | past SLA soft threshold; or CSV partial quarantine |
| Failed | past hard threshold OR auth error OR CSV file-level validation fail |
| Not connected | no credentials and no successful CSV upload for that source |

---

## API endpoints (target)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/sources` | List health per tenant |
| POST | `/api/v1/sources/{id}/connect` | Start OAuth |
| POST | `/api/v1/csv/upload` | CSV hub ingest (see pipeline doc) |
| POST | `/api/v1/sources/{id}/sync` | Manual sync |

---

## CSV hub (`F-CONN-005`) — must work end-to-end

Spec: [P-INGEST-CSV-HUB.md](../pipelines/P-INGEST-CSV-HUB.md)

| Step | Requirement |
|------|-------------|
| Upload | File stored tenant-scoped; metadata + `file_hash` recorded |
| Profile | Auto-detect `tpl_*` **or** user column map to canonical `entity_type` |
| Validate | Schema + types on **canonical** fields; hard fails → quarantine |
| Ingest | Valid rows → `raw.csv_hub_events` (same envelope contract as Shopify) |
| Transform | dbt staging → appropriate gold tables per source router |
| Health | Integration health updated; UI shows counts and quarantine |

**No stubs:** upload endpoints must write raw or return validation errors. Placeholder UI without ingest is forbidden.

### Tally and other T1 apps

`F-CONN-003` (Tally) and marketplace CSV paths **must** call CSV hub — no bypass parser that skips validation or quarantine.

---

## Acceptance tests

- [ ] Tenant A cannot read Tenant B source health
- [ ] Shopify webhook creates exactly one raw row per external_id
- [ ] Failed Tally upload shows **degraded/failed** with quarantine detail, not silent drop
- [ ] Arbitrary CSV with column map produces ≥1 raw row and quarantines invalid rows
- [ ] Re-upload identical file is idempotent (no duplicate raw rows)
- [ ] 10 rows render with correct badge tier at Phase 4 exit
