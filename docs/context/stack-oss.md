# Stack & OSS Adoption

## Adopt directly

| Component | Repo | Use in Trita |
|-----------|------|--------------|
| Ingest | [dlt-hub/dlt](https://github.com/dlt-hub/dlt) | All connector taps |
| Verified sources | [dlt-hub/verified-sources](https://github.com/dlt-hub/verified-sources) | Starting points for Shopify, etc. |
| Transform | [dbt-labs/dbt-core](https://github.com/dbt-labs/dbt-core) | Staging → gold |
| DQ | [metaplane/dbt-expectations](https://github.com/metaplane/dbt-expectations) | Quarantine gates |
| Orchestration | [dagster-io/dagster](https://github.com/dagster-io/dagster) or [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) | Pick one in Phase 0 |
| LLM gateway | [BerriAI/litellm](https://github.com/BerriAI/litellm) | Gemini + Groq |
| Causal | [py-why/dowhy](https://github.com/py-why/dowhy) | Refutation gate |
| Metering | [openmeterio/openmeter](https://github.com/openmeterio/openmeter) | Unit economics |
| Local SQL | [duckdb/duckdb](https://github.com/duckdb/duckdb) | Dev analytics |
| Forecast (optional) | statsforecast | Demand bands only |

**Optional parallel:** [airbytehq/airbyte](https://github.com/airbytehq/airbyte) for connector scale later — not V0.0.1 critical path.

---

## Build in-house (moat)

- Commerce ontology + identity resolution
- Decision contract + suppression + audit
- Integrity → blocked cards
- ₹ impact engine (conservative floors)
- Causal promotion policy
- Integration health UX

---

## Do not ship (inspire only)

- Random inventory-forecast GitHub demos — pattern reference only

---

## Version pins (set in Phase 0 scaffold)

| Package | Notes |
|---------|-------|
| Python | 3.11+ |
| Node | 20 LTS |
| Next.js | 14 |
| FastAPI | Latest stable |
| Supabase | CLI + hosted |

---

## Efficiency rules

- Groq for chat; Gemini for cards and drafts
- Cache `ContextProjection` per `(tenant, sku, hour)`
- Batch nightly metrics; intraday **only** Shopify + Unicommerce inventory/orders
- Per-tenant LiteLLM budget hard cap → template fallback

---

## OpenMeter meters

| Meter | Source |
|-------|--------|
| `llm_tokens_in`, `llm_tokens_out`, `llm_requests` | LiteLLM |
| `connector_sync_rows`, `connector_api_calls` | dlt |
| `dbt_run_seconds` | dbt |
| `decisions_emitted`, `decisions_accepted` | API |
| `storage_bytes` | Supabase |

Internal dashboard weekly: COGS, MRR, gross margin %, cost per accepted decision, cost per ₹ proven impact.
