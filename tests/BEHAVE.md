# Behavioral / E2E Contract

> Commands are **stubs** until `trita/` exists. Each suite must exit **0** when run for a feature to be considered behaviorally verified.

Map suites to VAs in [`VALIDATION.md`](../VALIDATION.md). Record exact commands and exit codes in [`HANDOFF.md`](../HANDOFF.md).

---

## Suite: isolation (VA-01, VA-02)

**When:** After FastAPI + Supabase RLS land.

```bash
cd trita/apps/api
pip install -e ".[dev]"
pytest tests/test_tenant_from_jwt.py tests/isolation/test_rls_migration_contract.py -q
# Expected: exit 0

# Optional Postgres RLS integration (Supabase or local with auth schema):
# TRITA_RUN_ISOLATION=1 DATABASE_URL=postgresql://... pytest tests/isolation/test_cross_tenant_rls.py -q
```

---

## Suite: auth_jwt (VA-01)

```bash
cd trita/apps/api
pytest tests/test_tenant_from_jwt.py -q
```

---

## Suite: shopify_oauth (OAuth path — VA-04 webhooks deferred)

```bash
cd trita/apps/api
pip install -e ".[dev]"
pip install -e ../../data/dlt
pytest tests/test_shopify_oauth.py tests/test_shopify_sync.py tests/isolation/test_connector_credentials_migration.py -q
```

---

## Suite: ingest_shopify (VA-04, VA-05)

```bash
cd trita/data/dlt
pip install -e ".[dev]"
pytest tests/test_envelope.py tests/test_shopify_pipeline.py tests/test_raw_migration_contract.py -q
# Expected: exit 0 (T-P0-010, T-P0-011 contract)

# Idempotency (Postgres):
# TRITA_RUN_ISOLATION=1 DATABASE_URL=... pytest tests/test_shopify_idempotency.py -q
```

## Suite: dbt_graph (VA-05)

```bash
cd trita/data/dbt
pip install -e ".[dev]"
pytest tests/test_dbt_contract.py -q
# Expected: exit 0 — contract

pip install dbt-core==1.8.2 dbt-postgres==1.8.2
python ../../../scripts/run_dbt.py run
# Expected: exit 0 — 9 models (staging → gold)

TRITA_RUN_VA05=1 C:\Python313\python.exe -m pytest tests/test_va05_yoga_bar.py -q
# Expected: exit 0 — Yoga Bar raw → gold.dim_sku + fact_inventory_daily (requires raw data + YOGA_BAR_TENANT_ID)
```

---

## Suite: health_api (VA-06)

```bash
cd trita/apps/api
python -m pytest tests/test_integration_health.py -q
# Expected: exit 0 — Shopify row shape; tenant isolation

# Live (optional, requires DATABASE_URL + migration 20260520500000):
# TEST_JWT from dev/auth/token or mint_test_token with YOGA_BAR_TENANT_ID
curl -s -H "Authorization: Bearer $TEST_JWT" "$API_URL/v1/integrations/health"
```

## Suite: rm0_gate (MISSION item 15)

```bash
python scripts/verify_rm0_gate.py
# Expected: exit 0 — raw>0, gold.dim_sku>0, integration_health=healthy, no decision tables
```

## Suite: web_auth (T-P0-040)

```bash
cd trita
pnpm install
pnpm --filter @trita/web build
# Expected: exit 0 — Next.js compiles with auth + 7-route shell
```

---

## Suite: llm (VA-07)

```bash
cd trita/apps/api
python -m pytest tests/test_llm_budget.py tests/test_llm_draft.py -q
```

---

## Suite: adr001 (T-P0-050)

```bash
cd trita/apps/api
pytest tests/test_adr001_accepted.py -q
# Expected: exit 0 — ADR-001 Status Accepted, registry + spec links
```

## Suite: orchestrator (VA-09)

```bash
cd trita/data/orchestration
pip install -e . -e ../dlt -e ../../apps/api
python -m pytest tests/test_daily_shell_defs.py -q

cd ../../..
python scripts/run_daily_shell.py
# Expected: exit 0; prints raw_events and gold_dim_sku > 0
```

Live integration (optional):

```bash
TRITA_RUN_VA09=1 python -m pytest trita/data/orchestration/tests/test_va09_integration.py -q
```

---

## Suite: deploy_health (VA-10)

**Local (Phase 0 default):**

```powershell
.\scripts\start-local.ps1
# other terminal:
.\scripts\dev-health.ps1
```

```bash
pytest trita/apps/api/tests/test_render_blueprint.py -q
# Blueprint contract only — cloud apply deferred
```

**Cloud (when card on file):** set `RENDER_HEALTH_URL` to public API host, then `check_render_health.sh`.

## Suite: litellm (VA-07 / F-PLAT-003)

```bash
cd trita/apps/api
pytest tests/test_llm_budget.py tests/test_llm_draft.py -q
# Expected: exit 0 — budget fallback + VA-03 output guard
```

---

## Suite: env_secrets (VA-11)

```bash
# From repo root — required keys documented; no secret-like template values
pytest trita/apps/api/tests/test_env_example.py -q

# CI grep — no .env committed with live service role material
git grep -l "SUPABASE_SERVICE_ROLE_KEY=" -- ':!*.example' ':!.env.example' ':!HANDOFF.md' ':!tests/BEHAVE.md' && exit 1 || exit 0
```

---

## Suite: csv_hub (VA-26) — RM-1

```bash
pytest trita/apps/api/tests/test_csv_hub.py -q
# Includes: idempotent replay, upload status tenant isolation

python scripts/verify_rm1_gate.py
# Expected: VA-13/14/26 PASS for YOGA_BAR_TENANT_ID
```

If VA-13 fails with zero order lines:

```bash
python scripts/seed_yoga_bar_shopify_orders.py
python scripts/run_dbt.py run
python scripts/refresh_identity.py
python scripts/verify_rm1_gate.py
```

**Supabase pooler:** CLI scripts use `scripts/_pg_connect.py` (`prepare_threshold=None` on `pooler.supabase.com`). If `refresh_identity.py` fails with `DuplicatePreparedStatement`, confirm `.env` `DATABASE_URL` uses `postgres.<project_ref>` username (see `infra/supabase/PROJECT.md`).

---

## Milestone 3+ (not required for RM-0)

| Suite | VAs | Notes |
|-------|-----|-------|
| `decision_suppression` | VA-15, VA-16 | ≤7/week; dedup key |
| `integrity_suppress` | VA-17 | Stale Shopify/Uni blocks emit |
| `causal_l3` | VA-18, VA-19 | Refutation pass before L3 |
| `inbox_e2e` | VA-15+ | Playwright — TBD path |

---

## Recording results

In HANDOFF **Scrutiny / Behavioral**:

```markdown
**BEHAVE:**
- Command: `pytest ...`
- Exit code: 0
- VAs covered: VA-02, VA-05
```
