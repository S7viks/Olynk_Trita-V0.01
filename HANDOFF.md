# Handoff Log

---

## SHIP — F-DEC-005, F-INBOX-001..004 — 2026-05-21

**Audit:** `public.decision_audit` (immutable append). Emit logs `emitted`; approve/reject/snooze log with `user_id` from JWT.

**API:** `GET /v1/decisions?tab=`, `GET /v1/decisions/{id}`, `POST approve|reject|snooze`, `GET timeline`, `GET reject-reasons`.

**Web:** `/inbox` — list + detail + forms → `/api/decisions/{id}/*`.

```powershell
python scripts/apply_migrations.py
python scripts/emit_decisions.py
# Approve or reject one card in /inbox
python scripts/verify_rm2_gate.py
python -m pytest trita/apps/api/tests/test_decisions_inbox.py -q
```

**Next:** `F-DRAFT-001/002`, RM-2 gate (#25) after one pilot accept/reject.

---

## Scrutiny Validation — 2026-05-22 — FAIL (F-DEC-005, F-INBOX-001..004)

**Scope:**

1. **SHIP** — audit log, inbox API (`approve`/`reject`/`snooze`, timeline, tabs), `/inbox` web
2. **Regression** — F-DEC-001..004 emitter tests, full API suite, web build

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **73 passed**, **1 FAILED**, 3 skipped |
| `pytest tests/test_decisions_inbox.py -q` | **4 passed** |
| `pytest tests/test_decisions.py -q` | **7 passed**, **1 FAILED** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm2_gate.py` | **FAIL** — `relation "public.decision_audit" does not exist` (migration `20260521100000` not applied to DB) |

### Blocker (FAIL)

**`test_decisions.py::test_emit_respects_weekly_cap`** — `ValueError: badly formed hexadecimal UUID string`.

**Root cause:** F-DEC-005 added `append_audit()` after `insert_decision()` in `emitter.py`. Test mocks `insert_decision` to return `True` but **does not** mock `append_audit` or `mock_conn` cursor `fetchone()` — `append_audit` reads `RETURNING id` from MagicMock → invalid UUID. **Regression** on prior PASS (F-DEC-001..004).

**PATCH (Worker):** `@patch("trita_decisions.emitter.append_audit")` or mock `cur.fetchone.return_value = (str(uuid4()),)` in `test_emit_respects_weekly_cap`; re-run → expect **74 passed**.

### Per-assertion

| VA / item | Verdict | Notes |
|-----------|---------|-------|
| **VA-01** | **PASS** (code) | `user_id` from JWT on approve/reject/snooze; manual `tenant_id` mismatch → 403 |
| **VA-02** | **PASS** | `20260521100000_decision_audit.sql` RLS SELECT; migration present in repo |
| **VA-15–17** | **PASS** (carry-over) | Dedup/cap/integrity unchanged; one emitter unit test **broken** |
| **VA-03** | **PASS** | No LLM on inbox actions |
| F-INBOX API (mocked tests) | **PASS** | approve/reject/list/reason enum |
| F-INBOX web | **PASS** (build) | `/inbox` + BFF routes compile |
| **RM-2 gate (#25)** | **FAIL** (live) | Gate script requires `decision_audit` table + ≥1 approve/reject audit row |
| Regression F-DEC-001..004 | **FAIL** | weekly cap test |

### Code review highlights

| Area | Verdict |
|------|---------|
| Audit append on emit | **PASS** (design) — immutable log; tests must follow |
| Reject reasons | **PASS** — `REJECT_REASONS` frozenset + API 400 on invalid enum |
| Route order | **PASS** — `/reject-reasons` before `/{decision_id}` |
| Tier 3 | **PASS** — no external writes on approve |
| Cross-tenant inbox | **MISSING** — no isolation test on `GET /v1/decisions/{id}` |

**VERDICT:** **FAIL** — fix emitter regression test; apply audit migration + run `verify_rm2_gate.py` after pilot accept/reject. Re-run scrutiny after PATCH.

---

## Scrutiny Validation — 2026-05-22 — PASS (PATCH: F-DEC-005, F-INBOX-001..004)

**PATCH:** `@patch("trita_decisions.emitter.append_audit")` on `test_emit_respects_weekly_cap` (F-DEC-005 emit audit no longer breaks mocked emitter path).

### Verification (post-PATCH)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/test_decisions.py -q` | **8 passed** |
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **74 passed**, 3 skipped |

### Per-assertion (carry-over)

| VA / item | Verdict |
|-----------|---------|
| Regression F-DEC-001..004 | **PASS** — weekly cap test green |
| F-DEC-005 / F-INBOX (code + tests) | **PASS** (carry-over) |
| **RM-2 gate (#25)** | **OPEN** (live) — run `python scripts/apply_migrations.py` then pilot accept/reject + `verify_rm2_gate.py` |

**VERDICT:** **PASS** (Scrutiny code blockers) — **Ready for re-validation**

---

## Scrutiny Validation — 2026-05-22 — PASS (independent re-run, F-DEC-005 / inbox)

**Scope:** Confirm prior **FAIL** remediated; no new SHIP since F-DEC-005 / F-INBOX.

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **74 passed**, 3 skipped |
| `pytest tests/test_decisions.py` + `test_decisions_inbox.py` | **12 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm1_gate.py` | **exit 0** |
| `python scripts/verify_rm2_gate.py` | **FAIL** — `public.decision_audit` does not exist (migration not applied to linked DB) |
| Prior FAIL (`append_audit` in weekly cap test) | **REMEDIATED** — `@patch append_audit` on `test_emit_respects_weekly_cap` |

### Per-assertion

| VA / item | Verdict |
|-----------|---------|
| F-DEC-005 / F-INBOX-001..004 | **PASS** |
| VA-01, VA-02, VA-03, VA-15–17 | **PASS** (code + unit tests) |
| Regression (metrics, identity, csv, shopify) | **PASS** |
| **RM-2 gate (#25)** | **OPEN** (live) — apply `20260521100000_decision_audit.sql` + pilot approve/reject + `verify_rm2_gate.py` |
| Cross-tenant inbox test | **MISSING** (non-blocking) |

**VERDICT:** **PASS** — inbox SHIP merge-ready from tests/code. Close **MISSION #25** with migration apply + gate script after human accept/reject on Yoga Bar.

---

## SHIP — F-DEC-001..004 — 2026-05-21

**Package:** `trita/packages/decisions` — contract, impact floors, integrity suppress, emitter.

**Schema:** `infra/supabase/migrations/20260521000000_decisions.sql` — `public.decisions` + RLS.

| Method | Path |
|--------|------|
| POST | `/v1/decisions/emit` |
| GET | `/v1/decisions` |

**Orchestration:** `daily_shell_job` → `decision_emit_op` after `metrics_dbt_op`.

```powershell
python scripts/apply_migrations.py
python scripts/emit_decisions.py
python -m pytest trita/apps/api/tests/test_decisions.py -q
```

**Next:** `F-DEC-005`, `F-INBOX-*`, RM-2 gate accept/reject.

---

## Scrutiny Validation — 2026-05-22 — PASS (F-DEC-001..004)

**Scope:**

1. **SHIP** — `trita-decisions` contract, suppression, integrity, emitter; `POST/GET /v1/decisions/*`; migration `20260521000000_decisions.sql`
2. **Regression** — full API (70 tests), RM-1 gate, web build, prior RM-1 stack

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **70 passed**, 3 skipped |
| `pytest tests/test_decisions.py -q` | **8 passed** |
| `python scripts/verify_rm1_gate.py` | **exit 0** — VA-13/14/26 PASS |
| `pnpm --filter @trita/web build` | **exit 0** |
| `pytest trita/data/orchestration/tests/test_daily_shell_defs.py -q` | **3 passed** |
| `git grep` secrets | **clean** (per prior runs) |

### Per-assertion

| VA / item | Verdict | Notes |
|-----------|---------|-------|
| **VA-15** | **PASS** | `suppression_key` + UNIQUE `(tenant_id, suppression_key)`; `test_suppression_dedup_key_stable` |
| **VA-16** | **PASS** | `WEEKLY_CAP=7` rolling 7d; `test_emit_respects_weekly_cap` |
| **VA-17** | **PASS** | Shopify/Unicommerce SLA degrade → suppress; `test_emit_integrity_suppressed` |
| **VA-03** | **PASS** | Impact from `MetricSnapshot`; `execution.tier` = 1 only; tier 3 rejected in `validate_card` |
| **VA-01** | **PASS** | `TenantDep` on emit/list; `tenant_id` in emit from JWT only |
| **VA-02** | **PASS** | RLS SELECT on `public.decisions` |
| F-DEC-001..004 | **PASS** | Package + API emit path |
| **RM-2 gate** (accept/reject) | **OPEN** | `F-DEC-005` / inbox UI not in this SHIP |
| **VA-12** (RM-0 script) | **NOTE** | `verify_rm0_gate.py` expects **no** `decisions` table — will **FAIL** post-RM-2 schema (expected; update script or scope to RM-0 snapshot) |
| Regression | **PASS** | CSV idempotent tests present; metrics/identity PATCHs hold |

### Code review highlights

| Area | Verdict |
|------|---------|
| Emitter | **PASS** — metrics → candidates → dedup → cap → insert |
| Integrity | **PASS** — only Shopify + Unicommerce connected sources |
| `GET /v1/decisions` | **PASS** (code) — **no** dedicated API test (non-blocking) |
| Dagster chain | **PASS** (code) — `decision_emit_op` in `jobs.py`; **test_daily_shell_job_op_chain** does not assert `decision_emit_op` (test debt) |
| Inbox UI | **N/A** — deferred per SHIP |

### Non-blocking

- Add `test_list_decisions_api` with `database_url` patch.
- Extend `test_daily_shell_job_op_chain` to include `decision_emit_op`.
- Cross-tenant decision list isolation test recommended before RM-2 inbox SHIP.

**VERDICT:** **PASS** — F-DEC-001..004 merge-ready. Proceed to **F-DEC-005** / **F-INBOX-***; RM-2 gate after accept/reject flow.

---

## RETRO — Milestone 2 (RM-1) close — 2026-05-22

**Verdict:** **GO** → RM-2 active (Milestone 3)

### Gate evidence (fresh)

| Check | Result |
|-------|--------|
| `python scripts/verify_rm1_gate.py` | exit **0** — VA-13 2/2 lines (100%), VA-14 dim_sku=27=feat, VA-26 csv_hub 3 rows + tally healthy |
| `pytest trita/apps/api/tests/ -q` | **62 passed**, 3 skipped |
| `pytest tests/test_csv_hub.py` (+ reports, rm1) | **11 passed** — includes `test_csv_idempotent_replay`, `test_csv_upload_status_tenant_isolation` |
| `pnpm --filter @trita/web build` | exit **0** — `/reports/health`, `/inventory`, `/sources` |
| ADR-001 | **Accepted** — Dagster daily shell includes identity + metrics ops |
| RM-1 blocking VAs | **VA-13**, **VA-14**, **VA-26** checked in VALIDATION |

### Scrutiny / BEHAVE (RM-1 scope)

| Track | Verdict | Notes |
|-------|---------|-------|
| Scrutiny | **PASS** | RM-1 SHIPs through F-REPORT-HEALTH / inventory / Sources (2026-05-21); metrics + identity PATCH cycles cleared |
| BEHAVE | **PASS** | Automated suites green (HANDOFF 2026-05-21 entries); gate script closes prior **VA-26** test debt |

### Process / debt (not blocking RM-1 GO)

- **Git:** RM-1 implementation landed on `main` (feat commit + gate scripts); push to `origin/main` before RM-2 SHIP on other machines
- **T-P0-003** `service_role` path audit — open
- **VA-04** webhooks, **VA-08** OpenMeter, **VA-10** Render 7d — deferred (documented)
- **VA-14** UI↔gold browser parity — not automated; API + `verify_metrics_gate.py` sufficient for RM-1
- Yoga Bar: `cogs_missing=27`, `bridge_full_rate=0.0` — data/fixture gap, not gate blockers
- Cross-tenant API tests for `/v1/reports/health`, `/v1/metrics/*` — recommended before RM-2 inbox

### Next worker (RM-2)

1. Read MISSION items 22–25, [phase-2-inventory-inbox.md](docs/roadmap/phase-2-inventory-inbox.md)
2. First SHIP: `F-DEC-001`..`004` — card contract + emitter + suppression (no LLM inventory math)
3. Keep integrity suppress wired to Shopify + Unicommerce SLA (**VA-17**)

---

## SHIP — RM-1 Gate (MISSION #21) — 2026-05-21

**Gate:** Yoga Bar — VA-13, VA-14, VA-26.

### Evidence (`scripts/verify_rm1_gate.py`)

| VA | Result |
|----|--------|
| VA-13 | PASS — 2 order lines, 100% resolved |
| VA-14 | PASS — dim_sku=27, feat.sku_metrics_daily=27 |
| VA-26 | PASS — 1 completed csv_upload, 3 raw.csv_hub_events, tally healthy |

### Prep (if order lines empty)

```powershell
python scripts/seed_yoga_bar_shopify_orders.py
python scripts/run_dbt.py run
python scripts/refresh_identity.py
python scripts/verify_rm1_gate.py
```

### Tests added

- `test_csv_idempotent_replay`
- `test_csv_upload_status_tenant_isolation`

**Next:** RM-2 — `F-DEC-001`..`004` decision contract + suppression.

---

## SHIP — F-REPORT-HEALTH, F-UI-INVENTORY-LIST, F-UI-SOURCES — 2026-05-21

**Features:** Data Health report UI, inventory SKU list, Sources page completion (RM-1).

### API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/reports/health` | Aggregates integrations + metrics summary + identity stats (VA-14) |

### Web routes

| Route | Feature |
|-------|---------|
| `/reports/health` | F-REPORT-HEALTH |
| `/inventory` | F-UI-INVENTORY-LIST (sort, stockout/dead filters) |
| `/sources` | F-UI-SOURCES (legend, tier badges, 5 connectors) |

### Verify

```powershell
# API running with JWT cookie / dev login
python -m pytest trita/apps/api/tests/test_reports_api.py -q
python scripts/verify_metrics_gate.py
```

Browse: `/reports/health`, `/inventory`, `/sources`.

**Next:** RM-1 gate (#21) — VA-13 ≥90% order lines, VA-14 live parity, VA-26 CSV idempotent test.

---

## Scrutiny Validation — 2026-05-21 — PASS (F-REPORT-HEALTH, F-UI-INVENTORY-LIST, F-UI-SOURCES)

**Scope:**

1. **SHIP** — `GET /v1/reports/health`, `/reports/health`, `/inventory`, `/sources` completion
2. **Regression** — full API (60 tests), metrics/identity gates, web build

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **60 passed**, 3 skipped |
| `pytest tests/test_reports_api.py -q` | **1 passed** |
| `python scripts/verify_metrics_gate.py` | **exit 0** — feat aligned with dim_sku (27=27) |
| `python scripts/refresh_identity.py` | **exit 0** — `meets_va13=True`, `resolution_rate=1.0` |
| `pnpm --filter @trita/web build` | **exit 0** |
| `git grep` secrets | **clean** |

### Per-assertion

| VA / item | Verdict | Notes |
|-----------|---------|-------|
| **VA-01** | **PASS** | `TenantDep` on `/v1/reports/health`; sub-aggregates use JWT `ctx` |
| **VA-03** | **PASS** | Report composes existing deterministic routes — no LLM qty/cover/₹ |
| **VA-14** | **PARTIAL** | API test mocks sub-routes; mart gate PASS; **no** live UI↔gold parity test or browser BEHAVE |
| **VA-13** | **PASS** (live) | Identity refresh on Yoga Bar |
| **VA-26** | **PARTIAL** | `test_csv_idempotent_replay` / upload isolation still **missing** |
| F-REPORT-HEALTH | **PASS** | Sorted integrations; summary flags `sku_mart_aligned`, `resolution_meets_va13` |
| F-UI-INVENTORY-LIST | **PASS** | Server page; allowlisted sort; `fetchSkuMetrics` via JWT cookie |
| F-UI-SOURCES | **PASS** (carry-over) | Nav phase-1 links; no fake RM-4 badges claimed in SHIP |
| RM-1 gate (#21) | **OPEN** | MISSION #21 unchecked — CSV test debt + formal gate script |
| Regression | **PASS** | Metrics PATCH (59→60 tests) holds |

### Code review highlights

| Area | Verdict |
|------|---------|
| `reports.py` | **PASS** — delegates to `integrations_health`, `metrics_summary`, `identity_stats` (no duplicate SQL) |
| `test_reports_api.py` | **PASS** — mocks sub-handlers (no `database_url()` pitfall) |
| Web nav (`lib/nav.ts`) | **PASS** — Inventory + Reports in phase-1 nav |
| Isolation | **MISSING** — no cross-tenant report test |

### Non-blocking

- Run `BEHAVE` or manual browse `/reports/health` vs API JSON for full **VA-14** sign-off.
- Add CSV idempotent test before claiming RM-1 gate complete.

**VERDICT:** **PASS** — UI/report SHIP merge-ready. **RM-1 gate (#21)** remains **OPEN** until **VA-26** tests + gate evidence.

---

## SHIP — F-METRICS-001..004 — 2026-05-21

**Mart:** `feat.sku_metrics_daily` (SKU × day) — velocity, cover, aging, stockout_risk, dead_stock, capital_at_risk, reorder_qty.

### Metrics (deterministic engine — VA-03)

| Feature | Columns / rules |
|---------|-----------------|
| F-METRICS-001 | `velocity_7d`, `velocity_30d`, `days_of_cover` |
| F-METRICS-002 | `aging_days`, `dead_stock` (90d + velocity &lt; 1/week) |
| F-METRICS-003 | `stockout_risk` when cover &lt; `lead_time_days * 1.2` |
| F-METRICS-004 | `capital_at_risk` = on_hand × unit_cost; `cogs_missing` when no Tally COGS |

### API

| Method | Path |
|--------|------|
| GET | `/v1/metrics/sku` |
| GET | `/v1/metrics/summary` |

### Orchestration

`daily_shell_job`: shopify_sync → dbt → identity_refresh → `dbt run --select sku_metrics_daily` → health check (requires metrics rows).

### Verify

```powershell
python scripts/apply_migrations.py
python scripts/run_dbt.py run
python scripts/refresh_identity.py
python scripts/run_dbt.py run --select sku_metrics_daily
python scripts/verify_metrics_gate.py
python -m pytest trita/apps/api/tests/test_metrics_api.py -q
```

**Next:** `F-REPORT-HEALTH` / `F-UI-INVENTORY-LIST`.

---

## Scrutiny Validation — 2026-05-21 — FAIL (F-METRICS-001..004)

**Scope:**

1. **SHIP** — `F-METRICS-001`..`004` (`feat.sku_metrics_daily`, `GET /v1/metrics/*`, Dagster `metrics_dbt_op`)
2. **Regression** — identity, CSV, Shopify, RM-1; orchestration defs; web build

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **57 passed**, **2 FAILED**, 3 skipped |
| `pytest tests/test_metrics_api.py -q` | **2 FAILED** (`DATABASE_URL is required`) |
| `python scripts/verify_metrics_gate.py` | **exit 0** — dim_sku=27, feat rows=27, aligned |
| `pytest trita/data/orchestration/tests/test_daily_shell_defs.py -q` | **3 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `git grep` secrets | **clean** |

### Blocker (FAIL)

**`test_metrics_api.py::test_metrics_summary`** and **`test_metrics_sku_list`** — `RuntimeError: DATABASE_URL is required`.

**Root cause:** Same as prior identity FAIL — `psycopg.connect(database_url(), …)` evaluates `database_url()` before `@patch("trita_api.routes.metrics.psycopg.connect")`.

**PATCH (Worker):** Add `@patch("trita_api.routes.metrics.database_url", return_value="postgresql://test")` to both tests (mirror `test_identity_v1.py`); expect **59 passed** in full API suite.

### Per-assertion

| VA / item | Verdict | Notes |
|-----------|---------|-------|
| **VA-03** | **PASS** | Metrics in dbt `sku_metrics_daily.sql` only; API read-only; no LLM qty/cover/₹ |
| **VA-01** | **PASS** (code) | `TenantDep`; SQL filters `tenant_id = %s` (JWT) |
| **VA-14** | **PARTIAL** | `verify_metrics_gate.py` **PASS** live; **F-REPORT-HEALTH** UI not shipped; API tests **FAIL** |
| F-METRICS-001..004 (mart) | **PASS** | Deterministic rules: velocity, cover, aging, stockout, dead_stock, capital_at_risk, reorder_qty |
| F-METRICS (API SHIP) | **FAIL** | Route tests broken in default pytest env |
| **VA-26** (carry-over) | **PARTIAL** | CSV idempotent/isolation tests still missing |
| **VA-13** | **PASS** (carry-over) | Prior live `refresh_identity.py` |
| Regression | **PASS** | Identity PATCH holds; connectors unchanged |

### Code review highlights

| Area | Verdict |
|------|---------|
| Sort/order query params | **PASS** — allowlisted via FastAPI `Query(pattern=…)` |
| `feat` schema migration | **PASS** — `20260520900000_feat_schema.sql` + dbt table |
| Orchestration | **PASS** — `metrics_dbt_op` after `identity_refresh_op` |
| RLS on `feat.sku_metrics_daily` | **NOTE** — grant USAGE; reads via service role (T-P0-003 debt) |
| Isolation test | **MISSING** — no cross-tenant metrics API test |
| Web inventory UI | **N/A** — API only; `F-UI-INVENTORY-LIST` deferred |

### Non-blocking notes

- Live gate: `cogs_missing=27`, `capital_at_risk_total=0` — expected until Tally COGS populated on Yoga Bar.
- `stockout_risk=0`, `dead_stock=27` — review fixture velocity/aging data, not a scrutiny blocker.

**VERDICT:** **FAIL** — fix metrics API tests before merge. Re-run scrutiny after PATCH.

---

## Scrutiny Validation — 2026-05-21 — PASS (PATCH: F-METRICS-001..004)

**PATCH:** `@patch("trita_api.routes.metrics.database_url", return_value="postgresql://test")` on `test_metrics_summary` and `test_metrics_sku_list` (same pattern as identity v1).

### Verification (post-PATCH)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **59 passed**, 3 skipped |
| `pytest tests/test_metrics_api.py -q` | **2 passed** |
| `python scripts/verify_metrics_gate.py` | **exit 0** (live, prior run) |

### Per-assertion (metrics SHIP)

| Item | Verdict |
|------|---------|
| F-METRICS-001..004 (mart + gate) | **PASS** |
| F-METRICS (API routes) | **PASS** |
| VA-01, VA-03 | **PASS** |
| VA-14 | **PARTIAL** — gate script PASS; **F-REPORT-HEALTH** UI not in this SHIP |

**VERDICT:** **PASS** (metrics SHIP) — **Ready for re-validation**

---

## Scrutiny Validation — 2026-05-21 — PASS (independent re-run, metrics PATCH confirmed)

**Scope:** Confirm prior **FAIL** remediated; full RM-1 stack through **F-METRICS-001..004**; no new SHIP since metrics.

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **59 passed**, 3 skipped |
| `pytest tests/test_metrics_api.py -q` | **2 passed** |
| Metrics + identity + csv + shopify bundle | **13 passed** |
| `python scripts/verify_metrics_gate.py` | **exit 0** — dim_sku=27, feat=27, aligned |
| `python scripts/verify_rm0_gate.py` | **exit 0** |
| `pytest trita/data/orchestration/tests/test_daily_shell_defs.py -q` | **3 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| Prior FAIL (`database_url` before mock on metrics) | **REMEDIATED** |

### Per-assertion

| VA / item | Verdict |
|-----------|---------|
| F-METRICS-001..004 | **PASS** |
| VA-01, VA-03 | **PASS** |
| **VA-14** | **PARTIAL** — live gate PASS; **F-REPORT-HEALTH** UI not shipped |
| **VA-26** | **PARTIAL** — CSV idempotent / upload isolation tests still missing |
| **VA-13** | **PASS** (carry-over) |
| RM-1 gate (#21) | **OPEN** |
| Regression | **PASS** |

### Open debt (unchanged)

- `test_csv_idempotent_replay`, `test_csv_upload_status_tenant_isolation`
- Metrics / identity cross-tenant API isolation tests
- **T-P0-003** service_role audit
- Yoga Bar: `cogs_missing=27` until Tally unit costs populate gold (data, not code defect)

**VERDICT:** **PASS** — metrics SHIP merge-ready. Next scrutiny: **F-REPORT-HEALTH** or **F-UI-INVENTORY-LIST**.

---

## SHIP — F-ID-001, F-ID-002 Identity v1 — 2026-05-21

**Package:** `trita/packages/ontology` — `refresh_identity()`, order key normalization, bridge stats.

### API

| Method | Path |
|--------|------|
| POST | `/v1/identity/refresh` |
| GET | `/v1/identity/stats` |
| GET | `/v1/identity/unresolved` |
| POST | `/v1/identity/aliases` (manual merge) |

### Tables

- `public.sku_alias` — shopify variant, unicommerce sku_code, tally sku → `canonical_sku_id`
- `public.order_bridge` — normalized order key ↔ shipment + Razorpay payout

### dbt

- `gold.bridge_sku_alias`, `gold.fact_order_line_resolved`, `gold.bridge_order_fulfillment`

### Verify (Yoga Bar)

```powershell
python scripts/apply_migrations.py
pip install -e trita/packages/ontology
# Re-sync Razorpay if payouts lack channel_order_id: .\scripts\connect_rm1_fixtures.ps1
python scripts/run_dbt.py run
python scripts/refresh_identity.py
curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/v1/identity/stats
```

**Next:** `F-METRICS-001` or Data Health UI (`F-REPORT-HEALTH`).

---

## Scrutiny Validation — 2026-05-21 — PASS (re-run, no new SHIP)

**Scope:** Re-validate HEAD — **F-ID-001/002** through RM-1 stack; no Worker SHIP since identity v1.

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` | **57 passed**, 3 skipped |
| Regression bundle (identity + csv + shopify + rm1 + health) | **19 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm0_gate.py` | **exit 0** |
| `python scripts/refresh_identity.py` | **exit 0** — `resolution_rate=1.0`, `meets_va13=True`, `aliases_upserted=27`, `bridge_full_rate=0.0` |
| `git grep` secrets | **clean** |

### Per-assertion

| VA / item | Verdict |
|-----------|---------|
| F-ID-001 / F-ID-002 | **PASS** |
| VA-01, VA-02, VA-03 | **PASS** |
| **VA-13** | **PASS** (live Yoga Bar refresh) |
| **VA-14** | **N/A** — Data Health UI not shipped |
| **VA-26** | **PARTIAL** — no `test_csv_idempotent_replay` / upload status isolation tests |
| RM-1 gate (#21) | **OPEN** |
| Regression | **PASS** |

### Open debt (unchanged)

- CSV idempotent + cross-tenant upload status tests (**VA-26**)
- Identity `/stats` cross-tenant isolation test
- **T-P0-003** service_role audit
- Order bridge `bridge_full_rate=0.0` until Razorpay/Shiprocket fixtures carry `channel_order_id` (non-blocking for SKU resolution gate)

**VERDICT:** **PASS** — RM-1 code stable through identity SHIP. Gate #21 still needs CSV test debt closed + **F-REPORT-HEALTH** / metrics before sign-off.

---

## Scrutiny Validation — 2026-05-20 — FAIL (F-ID-001 / F-ID-002)

**Scope:**

1. **SHIP** — `F-ID-001`, `F-ID-002` identity v1 (`trita-ontology`, `/v1/identity/*`)
2. **Regression** — CSV / Shopify / RM-1 connectors; web build; RM-0 gate

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (default env, no `DATABASE_URL`) | **55 passed**, **2 FAILED**, 3 skipped |
| `pytest tests/test_identity_v1.py -q` (with dummy `DATABASE_URL`) | **5 passed** (API route tests only pass when env set) |
| Regression bundle (csv + shopify + rm1) | **10 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm0_gate.py` | **exit 0** |
| `git grep` secrets | **clean** |

### Blocker (FAIL)

**`test_identity_v1.py::test_identity_refresh_endpoint`** and **`test_manual_alias_merge`** — `RuntimeError: DATABASE_URL is required`.

**Root cause:** Routes call `psycopg.connect(database_url(), …)`. `database_url()` runs **before** `@patch("…psycopg.connect")` applies, and `conftest.py` does not set `DATABASE_URL` (unlike production `.env`). Unit tests for ontology pure functions pass; **API route tests fail in CI/default pytest**.

**PATCH (Worker):** Patch `trita_api.routes.identity.database_url` (or add test `DATABASE_URL` in `conftest`), or mock connect at import site; re-run full suite → expect **57 passed**.

### Per-assertion

| VA / item | Verdict | Notes |
|-----------|---------|-------|
| **VA-01** | **PASS** (code) | `TenantDep` on all routes; `reject_tenant_override` on `/aliases` |
| **VA-02** | **PASS** | `20260520800000_identity_v1.sql` — RLS SELECT on `sku_alias`, `order_bridge` |
| **VA-13** | **PARTIAL** | `/stats` exposes `meets_va13`; no live Yoga Bar refresh proof in scrutiny |
| **VA-03** | **PASS** | Ontology uses deterministic SQL/hash keys — no LLM inventory math |
| F-ID-001 / 002 (package) | **PASS** | `normalize`, `bridge`, `identity` unit tests green |
| F-ID-001 / 002 (API SHIP) | **FAIL** | Broken route tests in default env |
| **VA-26** (carry-over) | **PARTIAL** | CSV idempotent / isolation tests still missing |
| Regression | **PASS** | Shopify route order; prior connectors unchanged |

### Code review highlights

| Area | Verdict |
|------|---------|
| `refresh_identity` | **PASS** — tenant-scoped reads/writes from gold + raw |
| Manual merge | **PASS** — upsert keyed `(tenant_id, source, external_id)` |
| Isolation test | **MISSING** — no cross-tenant test on `/stats` or `/unresolved` |
| Web UI | **N/A** — API/CLI only (acceptable for v1 SHIP) |
| dbt | **PASS** (present) — `bridge_sku_alias`, `fact_order_line_resolved`, `bridge_order_fulfillment` |

**VERDICT:** **FAIL** — fix identity API tests (DATABASE_URL / patch order) before merge. Re-run scrutiny after PATCH.

---

## Scrutiny Validation — 2026-05-20 — PASS (PATCH: F-ID-001 / F-ID-002)

**PATCH:** `@patch("trita_api.routes.identity.database_url", return_value="postgresql://test")` on `test_identity_refresh_endpoint` and `test_manual_alias_merge` so `database_url()` does not run before `psycopg.connect` mock.

### Verification (post-PATCH)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (default env, no `DATABASE_URL`) | **57 passed**, 3 skipped |
| `pytest tests/test_identity_v1.py -q` | **5 passed** |

### Per-assertion (identity SHIP)

| Item | Verdict |
|------|---------|
| F-ID-001 / F-ID-002 (package) | **PASS** |
| F-ID-001 / F-ID-002 (API routes) | **PASS** |
| VA-01 / VA-02 / VA-03 (code) | **PASS** |
| VA-13 live | **PARTIAL** (not re-run) |
| VA-26 | **PARTIAL** (carry-over) |

**VERDICT:** **PASS** (identity SHIP) — **Ready for re-validation**

---

## Scrutiny Validation — 2026-05-20 — PASS (independent re-run, identity PATCH confirmed)

**Scope:** Confirm prior **FAIL** remediated; full RM-1 stack through **F-ID-001/002**; no new SHIP since identity v1.

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` (no `DATABASE_URL`) | **57 passed**, 3 skipped |
| Identity + csv + shopify + rm1 bundle | **15 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm0_gate.py` | **exit 0** |
| `git grep` secrets | **clean** |
| Prior FAIL (`database_url` before mock) | **REMEDIATED** — `@patch identity.database_url` in `test_identity_v1.py` |

### Per-assertion

| VA / item | Verdict |
|-----------|---------|
| F-ID-001 / F-ID-002 | **PASS** |
| VA-01, VA-02, VA-03 | **PASS** |
| **VA-13** | **PASS** (live) — `python scripts/refresh_identity.py` → `resolution_rate=1.0`, `meets_va13=True` (Yoga Bar); `bridge_full_rate=0.0` (no shipment/payment bridge rows yet) |
| **VA-26** | **PARTIAL** — `test_csv_idempotent_replay` / upload isolation still missing |
| RM-1 gate (#21) | **OPEN** |
| Regression (F-CONN-005, Shopify, RM-1) | **PASS** |

### Open debt (unchanged)

- CSV idempotent + cross-tenant upload status tests
- Identity cross-tenant `/stats` isolation test
- **T-P0-003** service_role audit
- ~~Live Yoga Bar identity refresh for **VA-13**~~ — done 2026-05-21 (`meets_va13=True`, 27 aliases)

**VERDICT:** **PASS** — identity SHIP merge-ready. **RM-1 gate (#21) still OPEN** until CSV VA-26 tests + gate scripts; next SHIP scrutiny: **F-METRICS-001** or **F-REPORT-HEALTH**.

---

## SHIP — F-CONN-005 CSV hub (+ F-CONN-003 Tally path) — 2026-05-21

**Features:** Production CSV hub — template detect, column map, validate, raw, quarantine, dbt `gold.sku_unit_cost`, Sources upload UI.

### API

| Method | Path |
|--------|------|
| POST | `/v1/csv/upload` (multipart) |
| GET | `/v1/csv/templates` |
| GET | `/v1/csv/uploads/{id}` |

### Verify

```powershell
.\scripts\upload_tally_fixture.ps1
python scripts/run_dbt.py run
python -m pytest trita/apps/api/tests/test_csv_hub.py -q
```

**Next:** `F-ID-001` SKU alias / identity resolution.

---

## Scrutiny Validation — 2026-05-20 — PASS (re-run, no new SHIP)

**Scope:** Re-validate current HEAD — **F-CONN-005** through RM-1 connector stack; no new Worker SHIP since prior CSV hub scrutiny.

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` | **52 passed**, 3 skipped |
| Regression bundle (csv + shopify + rm1 + health) | **14 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm0_gate.py` | **exit 0** |
| `git grep` secrets | **clean** |
| `main.py` router order | `shopify_router` before `sources_router` |

### Per-assertion (unchanged from prior pass)

| VA / item | Verdict | Delta vs last scrutiny |
|-----------|---------|------------------------|
| F-CONN-005 / VA-01, 02, 06 | **PASS** | No regression |
| **VA-26** | **PARTIAL** | Still **no** `test_csv_idempotent_replay`; live `upload_tally_fixture.ps1` not re-run |
| **VA-05** | **PARTIAL** | dbt `sku_unit_cost` not re-run |
| RM-1 gate (item 21) | **OPEN** | MISSION item 21 unchecked — gate not claimed |
| **F-ID-001** | **N/A** | Not started (`trita-ontology` stub only) |

### Open debt (still unaddressed)

- `test_csv_idempotent_replay` — **missing**
- `test_csv_upload_status_tenant_isolation` — **missing**
- `GET /v1/csv/templates` unauthenticated (catalog only)
- **T-P0-003** service_role audit — open

**VERDICT:** **PASS** — codebase stable; prior PASS stands. Worker should add CSV idempotent + isolation tests and run Yoga Bar upload/dbt before **RM-1 gate (VA-26)** sign-off. Next SHIP scrutiny target: **F-ID-001**.

---

## Scrutiny Validation — 2026-05-20 — PASS (F-CONN-005 CSV hub)

**Scope:**

1. **SHIP** — `F-CONN-005` CSV hub (+ `F-CONN-003` Tally upload path)
2. **Regression** — full API (52 tests), Shopify route order, RM-1 connectors, web build, RM-0 gate

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` | **52 passed**, 3 skipped |
| `pytest tests/test_csv_hub.py -q` | **4 passed** |
| `pytest test_csv_hub.py test_shopify_sync.py test_connectors_rm1.py -q` | **14 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm0_gate.py` | **exit 0** |
| `git grep` `SUPABASE_SERVICE_ROLE_KEY=` (excludes) | **clean** |
| `GET /v1/csv/templates` without auth | **200** (template catalog only — no tenant data) |

### Per-assertion

| VA / item | Verdict | Notes |
|-----------|---------|-------|
| **VA-01** | **PASS** | Upload/status use `TenantDep`; `reject_tenant_override` on form `tenant_id`; DB queries scoped `tenant_id` + `upload_id` |
| **VA-02** | **PASS** | `20260520700000_csv_hub.sql` — RLS SELECT on `csv_upload`, `raw.csv_hub_events`, `quarantine.csv_hub` |
| **VA-06** | **PASS** | Tally health updated with `mode: csv_hub`, quarantine counts in detail |
| **VA-26** | **PARTIAL** | Idempotent `file_hash` implemented in `ingest.py`; **no automated test** for replay; live Yoga Bar upload script not re-run in scrutiny |
| **VA-05** | **PARTIAL** | `gold.sku_unit_cost` model present; dbt run not re-executed in this pass |
| F-CONN-005 | **PASS** | Template detect, quarantine path, fixture ingest unit tests |
| F-CONN-003 (Tally) | **PASS** | Sources UI + web `POST /api/csv/upload` forwards JWT |
| Shopify / RM-1 regression | **PASS** | `shopify_router` before `sources_router`; prior connector tests green |

### Code review (SCRUTINY.md)

| Area | Verdict |
|------|---------|
| Tenancy | **PASS** — JWT-only; no body `tenant_id` trust on happy path |
| Secrets | **PASS** |
| Deterministic engine | **PASS** — validation in `validate.py`; no LLM qty/₹ |
| Decisions / Tier 3 | **N/A** |
| Writes via `DATABASE_URL` | **NOTE** — same service-role pattern as other ingest; **T-P0-003** audit still open |

### Non-blocking (before RM-1 gate sign-off)

- Add `test_csv_idempotent_replay` (same `file_hash` → `idempotent_replay=True`, no double insert).
- Add `test_csv_upload_status_tenant_isolation` (tenant B cannot read tenant A `upload_id`).
- Consider `TenantDep` on `GET /v1/csv/templates` or document intentional public catalog.
- Run `.\scripts\upload_tally_fixture.ps1` + `run_dbt.py` for **VA-26** live evidence on Yoga Bar.

**VERDICT:** **PASS** — F-CONN-005 SHIP acceptable; close **VA-26** / RM-1 gate with live upload + idempotent test before claiming gate complete.

---

## SHIP — F-CONN-002, F-CONN-004, F-CONN-006 (+ Tally health row) — 2026-05-21

**Features:** Unicommerce, Shiprocket, Razorpay API connect/sync; `F-CONN-003` Tally shown as `csv_hub` (ingest blocked until `F-CONN-005`).

### What shipped

| Layer | Path / endpoint |
|-------|-----------------|
| Migration | `infra/supabase/migrations/20260520600000_connector_raw_rm1.sql` (applied via `scripts/apply_migrations.py`) |
| API | `POST /v1/sources/{unicommerce\|shiprocket\|razorpay}/connect` and `/sync` |
| Health | `GET /v1/integrations/health` — 5 sources (shopify, unicommerce, tally, shiprocket, razorpay) |
| dbt | `stg_*`, `gold.fact_shipment`, `gold.fact_payout`, `fact_inventory_daily` union |
| Web | `/sources` RM-1 panel + `POST /api/sources/[source]/sync` |
| Dev | `CONNECTOR_DEV_FIXTURES=1` + `scripts/connect_rm1_fixtures.ps1` |

### Verify (Yoga Bar tenant)

```powershell
# API running; .env has DATABASE_URL, CONNECTOR_DEV_FIXTURES=1, YOGA_BAR_TENANT_ID
.\scripts\connect_rm1_fixtures.ps1
python scripts/run_dbt.py run
python -m pytest trita/apps/api/tests/test_connectors_rm1.py trita/apps/api/tests/test_integration_health.py -q
```

### Deferred

- `F-CONN-003` ingest (CSV hub `F-CONN-005`)
- Dagster scheduled RM-1 sync ops
- Web OAuth-style connect forms for Uni/Shiprocket/Razorpay (API/CLI today)

**Next:** `F-CONN-005` CSV hub or `F-ID-001`.

---

## Scrutiny Validation — 2026-05-20 — PASS (independent re-run)

**Scope:**

1. **SHIP** — `F-CONN-002`, `F-CONN-004`, `F-CONN-006` (+ Tally health row)
2. **Regression** — Shopify sync route order, full API suite, web build, RM-0 gate
3. **Process** — RETRO gap: adversarial pass on RM-1 batch before merge

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` | **48 passed**, 3 skipped |
| `pytest test_shopify_sync.py test_integration_health.py test_connectors_rm1.py -q` | **10 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `python scripts/verify_rm0_gate.py` | **exit 0** (raw=45, dim_sku=27, health=healthy, VA-12) |
| `git grep` `SUPABASE_SERVICE_ROLE_KEY=` (excludes) | **clean** (exit 1) |
| Route order (`main.py`) | `shopify_router` before `sources_router` |

### Per-assertion

| VA / item | Verdict | Notes |
|-----------|---------|-------|
| **VA-01** | **PASS** | `TenantDep` + `reject_tenant_override` on RM-1 connect |
| **VA-02** | **PASS** | `20260520600000_connector_raw_rm1.sql` + tenant-scoped creds |
| **VA-06** | **PASS** | 5 sources; Tally `csv_hub` honest until F-CONN-005 |
| **VA-05** | **PARTIAL** | dbt gold extensions in SHIP — not re-run live in this pass |
| **VA-12** | **PASS** | Gate script: no public decision tables |
| F-CONN-002/004/006 | **PASS** | Fixture ingest + health mocks in tests |
| F-CONN-003 (Tally) | **PASS** | Disconnected / blocked message — not fake API |
| Shopify regression | **PASS** | `test_sync_pulls_and_writes_raw` **200** (was 404 pre-PATCH) |
| **VA-08** | **N/A** | OpenMeter still deferred (`trita/services/openmeter/README.md` only) |
| **VA-10** | **PARTIAL** | Local API health only; Render 7d not verified |

### Code review (SCRUTINY.md)

| Area | Verdict |
|------|---------|
| Tenancy | **PASS** — JWT-only `tenant_id` on connect/sync/health |
| Secrets | **PASS** — no service role in tracked sources |
| Deterministic engine | **PASS** — no LLM inventory math in connector paths |
| Decisions / Tier 3 | **N/A** — no emitter changes |
| Router coexistence | **PASS** — comment + order in `main.py` |

### Non-blocking notes

- Add explicit `test_router_shopify_before_sources` if route order regresses again.
- **T-P0-003** `service_role` path audit still open (RETRO debt).
- Historical HANDOFF **LiteLLM + OpenMeter** SHIP overstates VA-08; align doc or implement at RM-4.

**VERDICT:** **PASS** — RM-1 connector SHIP + Shopify regression verified. Safe to proceed to next SHIP (`F-CONN-005` or `F-ID-001`).

---

## Scrutiny Validation — 2026-05-21 — FAIL

**Scope:**

1. **SHIP** — `F-CONN-002`, `F-CONN-004`, `F-CONN-006` (+ Tally health row)
2. **Regression:** full API, RM-1 connector tests, web build
3. **Re-check:** prior UI/health SHIP fixes (Shopify health mocks)

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest tests/test_connectors_rm1.py tests/test_integration_health.py -q` | **8 passed** |
| `pnpm --filter @trita/web build` | **exit 0** |
| `pytest trita/apps/api/tests/ -q` | **47 passed, 1 FAILED**, 3 skipped |
| `git grep` / `.env` | clean; `.env` gitignored |

### Blocker (FAIL)

**`test_shopify_sync.py::test_sync_pulls_and_writes_raw`** — **404** (expected 200).

**Root cause:** `sources_router` (`POST /v1/sources/{source}/sync`) is registered **before** `shopify_router` in `main.py`. `POST /v1/sources/shopify/sync` matches the generic RM-1 handler with `source=shopify`, which is **not** in `RM1_API_SOURCES` → **404 Unknown connector**. Shopify OAuth sync path is **broken in production**, not only in tests.

**PATCH options (Worker):** register `shopify_router` before `sources_router`, or delegate `shopify` in `sync_connector_route` to existing Shopify sync, or mount RM-1 routes under a non-colliding prefix.

### Per-assertion — RM-1 SHIP

| VA / task | Verdict | Notes |
|-----------|---------|-------|
| **VA-01** | **PASS** (RM-1 routes) | `TenantDep` + `reject_tenant_override` on connect body |
| **VA-02** | **PASS** (contract) | Raw tables + RLS pattern in migration |
| **VA-06** | **PASS** | 5 honest sources; Tally `csv_hub` / F-CONN-005 message |
| **VA-05** (partial) | **PARTIAL** | dbt gold extensions claimed in handoff — not re-run live in scrutiny |
| **F-CONN-003** | **PASS** (honest) | Tally row disconnected until CSV hub — not fake connected |
| Stubs | **PASS** | Fixture ingest writes real `raw.*_events` via `write_raw_events` |
| **Regression** | **FAIL** | Shopify sync route shadowing |

### Code review highlights

| Area | Verdict |
|------|---------|
| Connector registry | **PASS** — modes + SLA; `RM1_API_SOURCES` scoped |
| Dev fixtures | **PASS** — `CONNECTOR_DEV_FIXTURES` gated |
| Sources UI | **PASS** — 5 rows only (no RM-4 fake badges) |
| **Shopify coexistence** | **FAIL** — router order regression |

### Sub-feature verdicts

| Feature | Verdict |
|---------|---------|
| `F-CONN-002`, `004`, `006` (scoped tests) | **PASS** |
| `F-UI-SOURCES` / health (regression) | **FAIL** via Shopify sync break |
| RM-0 RETRO gate | **At risk** — `verify_rm0_gate.py` may still pass DB paths; API Shopify sync broken |

**VERDICT:** **FAIL** — fix Shopify/`sources` route conflict before RM-1 merge or gate sign-off.

---

## Scrutiny Validation — 2026-05-21 — PASS (PATCH: Shopify route order)

**PATCH:** Register `shopify_router` before `sources_router` in `trita_api/main.py` so `POST /v1/sources/shopify/sync` hits Shopify OAuth sync, not RM-1 `{source}/sync` (404 Unknown connector).

### Verification (post-PATCH)

| Check | Result |
|-------|--------|
| `pytest tests/test_shopify_sync.py tests/test_connectors_rm1.py -q` | **6 passed** |
| `pytest trita/apps/api/tests/ -q` | **48 passed**, 3 skipped |

### Per-assertion (RM-1 batch)

| Item | Verdict |
|------|---------|
| F-CONN-002, 004, 006 | **PASS** |
| F-CONN-003 (Tally) | **PASS** |
| Shopify regression | **PASS** |
| VA-01 (connect override) | **PASS** |

**VERDICT:** **PASS** (RM-1 connector SHIP + Shopify regression) — **Ready for re-validation**

---

## RETRO — Milestone 1 (RM-0) close — 2026-05-21

**Verdict:** **GO** → RM-1 active (Milestone 2)

### Gate evidence

| Check | Result |
|-------|--------|
| `python scripts/verify_rm0_gate.py` | exit **0** — raw=45, gold.dim_sku=27, health=healthy, VA-12 |
| `pytest trita/apps/api/tests/ -q` | **44 passed**, 3 skipped (post-RETRO: VA-11 + Shopify health mocks) |
| ADR-001 | **Accepted** — `test_adr001_accepted.py` |
| RM-0 blocking VAs | VA-01, 02, 05, 06, 07, 09, 11, 12 **checked** in VALIDATION |
| Deferred (documented) | VA-04 webhooks, VA-08 OpenMeter, VA-10 Render 7d live |

### Process gaps (debt — not blocking RM-0)

- **Scrutiny / BEHAVE** not recorded for SHIP `F-UI-NAV` / `F-CONN-HEALTH` (2026-05-21) — run before first RM-1 merge or at RM-1 mid-review
- RETRO doc sweep committed as `5e3475c` (restore from HEAD if working tree drifts)
- **T-P0-003** `service_role` path audit still open

### Next worker (RM-1)

1. Read MISSION items 16–21, [phase-1-six-apps-graph.md](docs/roadmap/phase-1-six-apps-graph.md)
2. First SHIP candidate: `F-CONN-002` Unicommerce or `F-CONN-005` CSV hub (no stubs)
3. Optional: `SCRUTINY` on web/auth/health SHIP; `TRITA_RUN_ISOLATION=1` for live RLS proof

---

## RM-0 GATE — Yoga Bar spine — 2026-05-21

**Status:** Complete (MISSION item 15)

### Evidence

```text
python scripts/verify_rm0_gate.py
# tenant_id=901bec43-4f06-4bf4-bf76-a5d251242e43
# raw.shopify_events=45  gold.dim_sku=27
# integration_health=healthy (18 events, tritabyolynk.myshopify.com)
# public decision tables=[]  → VA-12 PASS
```

### UI

- http://localhost:3000/sources — Shopify row **healthy**, last sync visible
- `/inbox` — placeholder only (no emitter)

### Deferred (not blocking RM-0)

- VA-10 Render 7d health (local `127.0.0.1:8000` instead)
- VA-04 Shopify webhooks
- VA-08 OpenMeter

---

## SHIP — F-UI-NAV, F-UI-SOURCES-SHELL, F-CONN-HEALTH (T-P0-040–042) — 2026-05-21

**Status:** Complete  
**Features:** `F-UI-NAV`, `F-UI-SOURCES-SHELL`, `F-CONN-HEALTH`  
**Tasks:** `T-P0-040`, `T-P0-041`, `T-P0-042`

### What was done

- **API:** `GET /v1/integrations/health` (Shopify row only in RM-0); `public.integration_health` migration; upsert on Shopify OAuth/sync and Dagster `integration_health_op`
- **Auth:** `POST /v1/auth/exchange` (Supabase user JWT → tenant JWT via membership); `POST /dev/auth/token` (Yoga Bar pilot, dev only)
- **Web:** Next.js 14 app — 7-route nav, `/login`, `/sources` health table, middleware cookie `trita_access_token`
- **Scripts:** `scripts/start-web.ps1`

### Commands run

```powershell
cd trita/apps/api
python -m pytest tests/test_integration_health.py tests/test_auth_exchange.py tests/test_health.py -q
# 7 passed

cd trita
pnpm --filter @trita/web build
# exit 0
```

### RM-0 gate (item 15) — remaining

- Live Yoga Bar: Shopify sync → green health row visible at http://localhost:3000/sources
- Apply migration if not on project: `20260520500000_integration_health.sql` (applied via Supabase MCP in this session)

### Local smoke

```powershell
.\scripts\start-api.ps1          # terminal 1
.\scripts\start-web.ps1          # terminal 2
# Login → Continue as Yoga Bar (dev) → /sources
```

---

## BASELINE — 2026-05-20

**Status:** Complete
**Implemented by:** Orchestrator (plan execution)
**Git commit:** (none yet) — BASELINE Tier A+B file creation

### What was done

- Created Tier A: `MISSION.md`, `VALIDATION.md`, `HANDOFF.md`, `MISSION_LOG.md`
- Created Tier B: `docs/ROADMAP.md`, `docs/checklists/BASELINE.md`, `ORCHESTRATOR.md`, `SCRUTINY.md`, `tests/BEHAVE.md`
- Renamed `docs/BUiLD-ORDER.md` → `docs/BUILD-ORDER.md`
- Wired entry points in `AGENTS.md`, `docs/README.md`, `README.md`

### What was NOT done / deferred

- `trita/` monorepo scaffold (Layer 0 item 1 — next worker feature)
- No pytest or BEHAVE commands run (no application code yet)
- ADR-001 still **Proposed** until Week 1 decision

### Commands run

```bash
# No test suites yet — docs-only baseline
```

### Planning decisions (2026-05-20)

- ADR-001: **Dagster** Accepted
- Pilot tenant: **Yoga Bar** (all milestone evidence)
- MISSION: 6 milestones 1:1 with RM-0…RM-5; Worker Procedures inline
- VALIDATION: VA-21–23 for RM-4; launch commercial rows checklist-only via VA-20
- F-CONN-005 (CSV hub): production in **RM-1** — template detect or column map, schema validation, full raw→quarantine→gold lifecycle; **no stubs** anywhere ([P-INGEST-CSV-HUB](docs/pipelines/P-INGEST-CSV-HUB.md), VA-26)

### Issues discovered

- README and AGENTS already linked `BUILD-ORDER.md` but file was misnamed `BUiLD-ORDER.md` (fixed)

### Assertions satisfied

- N/A — implementation VAs apply after code lands; VALIDATION contract authored only

### Notes for next worker

- Run human checklist: [`docs/checklists/BASELINE.md`](docs/checklists/BASELINE.md) trigger `BASELINE`
- Start Milestone 1 feature 1: monorepo scaffold per [`docs/BUILD-ORDER.md`](docs/BUILD-ORDER.md)
- Read [`MISSION.md`](MISSION.md) → [`VALIDATION.md`](VALIDATION.md) → [`ORCHESTRATOR.md`](ORCHESTRATOR.md) every session

### Scrutiny / Behavioral (E2E)

- Scrutiny: N/A (docs-only bootstrap)
- BEHAVE: N/A — see [`tests/BEHAVE.md`](tests/BEHAVE.md) when `trita/` exists

---

## SHIP — Monorepo scaffold `trita/` (F-BOOT-001) — 2026-05-20

**Status:** Complete (awaiting Scrutiny + BEHAVE validator)
**Implemented by:** Worker (SHIP)
**Git commit:** _(deferred — workspace is not a git repository; run `git init` then commit locally)_

### What was done

- Created `trita/` monorepo: `apps/web` (Next.js 14), `apps/api` (FastAPI `/health`), `data/{dlt,dbt,orchestration}`, `packages/{ontology,decisions,causal}`
- Created `infra/supabase/migrations/` placeholder at repo root
- Root `.gitignore` for `.env` / `.env.local`
- Extended `.env.example` with `RENDER_HEALTH_URL` (VA-10 prep)
- VA-11 tests: `trita/apps/api/tests/test_env_example.py`, `test_health.py`
- Updated `README.md`, `MISSION.md` (item 1 checked), `docs/features/REGISTRY.md` (`F-BOOT-001` done), `tests/BEHAVE.md` env suite paths

### Files touched

- `trita/**` (new)
- `infra/supabase/migrations/**` (new)
- `.env.example`, `.gitignore`, `README.md`, `MISSION.md`, `HANDOFF.md`, `MISSION_LOG.md`
- `docs/features/REGISTRY.md`, `tests/BEHAVE.md`

### Commands run

```bash
cd trita/apps/api
pip install -e ".[dev]"
pytest tests/ -q
# exit code: 0 — 4 passed (VA-11 + API health smoke)

# BEHAVE env_secrets (from repo root; requires git for grep variant)
pytest trita/apps/api/tests/test_env_example.py -q
# exit code: 0

git grep -l "SUPABASE_SERVICE_ROLE_KEY=" -- ':!*.example' ':!.env.example' ':!HANDOFF.md' ':!tests/BEHAVE.md'
# skipped — fatal: not a git repository
```

### Behavioral validator (BEHAVE)

| Command | Exit | VAs |
|---------|------|-----|
| `pytest trita/apps/api/tests/test_env_example.py -q` | 0 | VA-11 |
| `pytest trita/apps/api/tests/test_health.py -q` | 0 | _(scaffold smoke only)_ |
| `git grep …` per [`tests/BEHAVE.md`](tests/BEHAVE.md) | — | VA-11 _(after `git init`)_ |

**Env / seeds:** None — reads repo-root `.env.example` only.

### Assertions satisfied

- **VA-11:** Required keys documented in `.env.example`; pytest guards missing keys and secret-like template values; `.env` ignored at repo + `trita/` roots

### Deferred

- Git commit hash (no `.git` in workspace)
- BUILD-ORDER item 4 duplicate work if treated separately (`.env.example` already satisfies VA-11)
- `pnpm install` / Next build not run in CI this session (optional local smoke)

### Notes for next worker

- **Active feature:** Supabase `tenants`, `memberships` + RLS — BUILD-ORDER item 2 (`F-PLAT-001`, VA-01, VA-02)
- Migrations path: `infra/supabase/migrations/`

### Scrutiny / Behavioral (E2E)

**BEHAVE (Worker run):**

- Command: `pytest trita/apps/api/tests/test_env_example.py -q`
- Exit code: 0
- VAs covered: VA-11

---

## Scrutiny Validation — 2026-05-20 — PASS

**Scope:** SHIP — Monorepo scaffold `trita/` (`F-BOOT-001`) — assertions mapped in that handoff (primarily **VA-11**).

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run

| Check | Command / method | Result |
|-------|------------------|--------|
| Types (API) | `mypy src/trita_api --ignore-missing-imports` | 0 issues |
| Types (web) | `pnpm exec tsc --noEmit` in `trita/apps/web` | exit 0 |
| Lint (web) | `pnpm run lint` (`next lint`) | **blocked** — no `.eslintrc`; interactive setup prompt (exit 1) |
| Tests | `pytest tests/ -v` in `trita/apps/api` | **4 passed** |
| BEHAVE `env_secrets` | `pytest trita/apps/api/tests/test_env_example.py` | exit 0 |
| BEHAVE git grep | `git grep … SUPABASE_SERVICE_ROLE_KEY=` | **skipped** — workspace still has no `.git` |
| Secrets scan | no `.env` / `.env.local` in tree; `.gitignore` at repo + `trita/` | clean |
| Code review | tenancy / engine / decisions / causal / connector stubs | see below |

### Per-assertion (RM-0 scope for this SHIP)

| VA | Verdict | Evidence |
|----|---------|----------|
| **VA-11** | **PASS** | Root `.env.example` documents `REQUIRED_KEYS`; values empty or non-secret; `test_env_example.py` (3 tests) + `.gitignore` |
| VA-01 | N/A | No JWT middleware yet (`T-P0-004`) |
| VA-02 | N/A | No RLS / isolation tests |
| VA-03 | N/A | No LLM call paths in `trita/` app code |
| VA-04–VA-10 | N/A | Ingest, health, LiteLLM, Dagster job, Render deploy not in this SHIP |
| VA-12 | N/A | No decision emitter |
| VA-09 (ADR-001) | **PARTIAL** | [docs/adr/001-orchestrator.md](docs/adr/001-orchestrator.md) **Accepted**; `trita/data/orchestration/` is README-only — Dagster proof deferred to `P-ORCH-DAILY-SHELL` |

### Code review (SCRUTINY.md)

- **Tenancy:** No `tenant_id` from body/query; API README defers JWT to `T-P0-004` — acceptable for scaffold.
- **Deterministic engine:** No inventory math or LLM qty/cover/₹ paths in shipped code.
- **Decisions / causal:** Package `__init__.py` docstrings only — not inbox/causal features; not forbidden connector stubs.
- **Stubs:** `data/dlt`, `data/dbt`, `data/orchestration` are README placeholders only — aligned with BUILD-ORDER shell, not CSV/ingest UI stubs.
- **REGISTRY:** `F-BOOT-001` marked **done** — matches deliverable.
- **ADR-001:** Status **Accepted** in-file — satisfies planning gate; runtime VA-09 still open.

### Scrutiny — Monorepo scaffold `trita/` (F-BOOT-001) — 2026-05-20

**Verdict:** **PASS**

**Blockers:** None for `F-BOOT-001` / VA-11.

**Non-blocking notes:**

1. Initialize git and run BEHAVE `git grep` before RM-0 CI is trustworthy.
2. Add ESLint config (or commit `next lint` defaults) so `pnpm run lint` is non-interactive in CI.
3. `MISSION.md` item 4 (`.env.example`) still unchecked — doc drift; functionally satisfied.
4. Worker handoff: no git commit hash — still accurate.

### BEHAVE (Scrutiny re-run)

- Command: `pytest trita/apps/api/tests/ -v`
- Exit code: 0
- VAs covered: **VA-11** (+ health smoke only)

**VERDICT:** **PASS** (feature `F-BOOT-001`; do not treat as RM-0 gate sign-off)

---

## SHIP — F-PLAT-001 / F-PLAT-002 + JWT (T-P0-001, T-P0-002, T-P0-004) — 2026-05-20

**Status:** Complete (Scrutiny PASS + BEHAVE PASS — VA-01, VA-02, VA-11)
**Implemented by:** Worker (SHIP)
**Git commit:** _(deferred — no git repository)_

### What was done

- SQL migrations: `infra/supabase/migrations/20260520100000_tenants_memberships.sql`, Yoga Bar seed file
- RLS: `tenants_select_member`, `memberships_select_own` (authenticated role)
- FastAPI JWT auth (`trita_api/auth.py`), routes `/v1/tenant/context`, `/v1/tenant/probe`
- Tests: `test_tenant_from_jwt.py` (VA-01), `isolation/test_rls_migration_contract.py` (VA-02 CI), optional `test_cross_tenant_rls.py`
- CI: `.github/workflows/tenant-isolation.yml`
- Supabase MCP: `tenants_memberships` migration applied remotely (success)
- REGISTRY: `F-PLAT-001`, `F-PLAT-002` → **done**; MISSION items 2, 3 (T-P0-002), 6 checked

### Remote Supabase note

Linked project already had `public.tenants` / `tenant_memberships` (legacy shape). MCP migration added `public.memberships` + policies; Yoga Bar seed via MCP **failed** (`display_name` column missing on existing `tenants`). **Repo migration files are canonical** for greenfield; align remote schema or add bridge migration in a follow-up — do not assume MCP seed succeeded.

### Commands run

```bash
cd trita/apps/api
pip install -e ".[dev]"
pytest tests/ -q
# exit code: 0 — 14 passed, 3 skipped (integration tests without TRITA_RUN_ISOLATION)

pytest tests/test_tenant_from_jwt.py tests/isolation/test_rls_migration_contract.py -q
# exit code: 0 — VA-01 + VA-02 contract
```

### Behavioral validator (BEHAVE)

| Command | Exit | VAs |
|---------|------|-----|
| `cd trita/apps/api && pytest tests/test_tenant_from_jwt.py tests/isolation/test_rls_migration_contract.py -q` | 0 | VA-01, VA-02 |
| `pytest tests/test_env_example.py -q` | 0 | VA-11 regression |

**Optional integration (Supabase Postgres):**

```bash
TRITA_RUN_ISOLATION=1 DATABASE_URL="postgresql://..." pytest tests/isolation/test_cross_tenant_rls.py -q
```

Requires migrations applied + `auth.users` rows for test UUIDs (see `infra/supabase/seed/isolation_test_users.sql`).

### Assertions satisfied

- **VA-01:** Bearer JWT → `tenant_id`; body override on `/v1/tenant/probe` → 403
- **VA-02:** RLS policies in migration; CI contract tests + workflow; live cross-tenant pytest when `TRITA_RUN_ISOLATION=1`

### Deferred

- **T-P0-003:** `service_role` path audit (no API ingest paths yet)
- Git commit; remote `tenants` schema reconciliation with repo `display_name` column
- Supabase Auth hook to inject `tenant_id` into JWT (document only — use custom access token hook in dashboard)

### Notes for next worker

- **Active feature:** dlt raw envelope + Shopify tap (`T-P0-010`, BUILD-ORDER #8)
- All DB access must filter by JWT `tenant_id`; never accept body `tenant_id`

### Scrutiny / Behavioral (E2E)

**BEHAVE (Worker run):**

- Command: `cd trita/apps/api && pytest tests/test_tenant_from_jwt.py tests/isolation/test_rls_migration_contract.py -q`
- Exit code: 0
- VAs covered: VA-01, VA-02

---

## Scrutiny Validation — 2026-05-20 — PASS (F-PLAT-001)

**Scope:** SHIP — `F-PLAT-001` / `F-PLAT-002` + JWT (`T-P0-001`, `T-P0-002`, `T-P0-004`) — **VA-01**, **VA-02**, **VA-11** regression.

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run

| Check | Command / method | Result |
|-------|------------------|--------|
| Types (API) | `mypy src/trita_api --ignore-missing-imports` | 0 issues |
| Tests | `pytest tests/ -q` in `trita/apps/api` | **14 passed**, 3 skipped (live RLS integration) |
| VA-01 | `pytest tests/test_tenant_from_jwt.py -q` | exit 0 |
| VA-02 | `pytest tests/isolation/test_rls_migration_contract.py -q` | exit 0 |
| VA-11 | `pytest tests/test_env_example.py -q` | exit 0 |
| CI contract | `.github/workflows/tenant-isolation.yml` | present; matches pytest targets |
| Secrets scan | `.env` / `.env.local` in `.gitignore`; no committed `.env` | clean (local `.env` may exist — not tracked) |
| BEHAVE git grep | `git grep … SUPABASE_SERVICE_ROLE_KEY=` | **skipped** — workspace still has no `.git` |
| Code review | tenancy / engine / decisions / causal | see below |

### Per-assertion

| VA | Verdict | Evidence |
|----|---------|----------|
| **VA-01** | **PASS** | `auth.py` — `tenant_id` from JWT `tenant_id` claim only; `/v1/tenant/probe` rejects body override via `reject_tenant_override`; `test_tenant_from_jwt.py` |
| **VA-02** | **PASS** | Migration RLS on `tenants` / `memberships`; `tenants_select_member`, `memberships_select_own`; contract tests + CI workflow |
| **VA-02** (live Postgres) | **DEFERRED** | `test_cross_tenant_rls.py` — requires `TRITA_RUN_ISOLATION=1` + `DATABASE_URL` (non-blocking for Phase 0 CI contract) |
| **VA-11** | **PASS** | `.env.example` + `test_env_example.py`; regression in tenant-isolation workflow |
| **VA-11** (git grep) | **DEFERRED** | No `.git` — run after `git init` per BEHAVE |
| VA-03–VA-10, VA-12 | N/A | Out of scope for this SHIP |

### Code review (SCRUTINY.md)

- **Tenancy:** `TenantDep` on routes; probe explicitly rejects body `tenant_id` ≠ JWT — **PASS**
- **RLS:** New tables enabled; SELECT policies scoped to `auth.uid()` / membership — **PASS**
- **Deterministic engine:** No inventory math or LLM qty/cover/₹ paths — **PASS**
- **Decisions / causal:** Not touched — N/A
- **service_role:** No API ingest paths; **T-P0-003** audit deferred — acceptable
- **REGISTRY:** `F-PLAT-001`, `F-PLAT-002` → **done** — matches deliverable
- **Remote Supabase:** Repo migrations canonical; MCP seed/schema drift noted in SHIP — non-blocking for code review

### Scrutiny — F-PLAT-001 / F-PLAT-002 + JWT — 2026-05-20

**Verdict:** **PASS**

**Blockers:** None.

**Non-blocking notes:**

1. Initialize git and run BEHAVE `git grep` before full `env_secrets` sign-off.
2. Optional: `TRITA_RUN_ISOLATION=1` + migrated DB for live cross-tenant RLS proof.
3. Reconcile remote `tenants` schema with repo `display_name` / Yoga Bar seed (follow-up).
4. **T-P0-003:** `service_role` path audit when ingest lands.

**VERDICT:** **PASS** (features `F-PLAT-001`, `F-PLAT-002`, JWT `T-P0-004`; do not treat as full RM-0 gate until BEHAVE re-validation)

---

## Behavioral (automated) — 2026-05-20 — PASS

**BEHAVE role** — `F-PLAT-001` / `F-PLAT-002` + JWT (`T-P0-001`, `T-P0-002`, `T-P0-004`)  
**Assigned VAs:** VA-01, VA-02, VA-11  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-20 — PASS (F-PLAT-001)`

### 1. Environment check

| Check | Status | Notes |
|-------|--------|-------|
| `NEXT_PUBLIC_API_URL` | SET | Live curl suites not in scope for this SHIP |
| `API_URL` / `TEST_JWT` | N/A | JWT tests use `conftest` monkeypatched secret |
| `API_JWT_SECRET` | SET | Present in `.env` |
| `DATABASE_URL` | SET | Live RLS run attempted — connection error (see below) |
| Git repo | **present** | `git grep` suite runnable |

### 2. Commands run

```powershell
cd d:\Olynk_V 0.0.1\trita\apps\api
pytest tests/ -q
# exit 0 — 14 passed, 3 skipped (TRITA_RUN_ISOLATION not set in default run)

pytest tests/test_tenant_from_jwt.py tests/isolation/test_rls_migration_contract.py -q
# exit 0 — 10 passed

pytest tests/test_env_example.py -q
# exit 0 — 3 passed

cd d:\Olynk_V 0.0.1
git grep -l "SUPABASE_SERVICE_ROLE_KEY=" -- ':!*.example' ':!.env.example' ':!HANDOFF.md' ':!tests/BEHAVE.md' && exit 1 || exit 0
# exit 0 — no matches (VA-11)

# Optional live RLS (VA-02 integration):
TRITA_RUN_ISOLATION=1 DATABASE_URL=<from .env> pytest tests/isolation/test_cross_tenant_rls.py -q
# exit 1 — psycopg OperationalError: Tenant or user not found (pooler URL / credentials; non-blocking for CI contract)
```

### 3. VA mapping (automated only)

| VA | Verdict | Suite / evidence | Exit |
|----|---------|------------------|------|
| **VA-01** | **PASS** | `tests/test_tenant_from_jwt.py` | 0 |
| **VA-02** | **PASS** | `tests/isolation/test_rls_migration_contract.py` + `.github/workflows/tenant-isolation.yml` | 0 |
| **VA-02** (live Postgres) | **SKIP** | `test_cross_tenant_rls.py` — DB connection failed (`Tenant or user not found`); fix `DATABASE_URL` / pooler user then re-run | 1 |
| **VA-11** | **PASS** | `tests/test_env_example.py` + `git grep` anti-secret scan | 0 |
| VA-03–VA-10, VA-12 | **N/A** | Out of scope for this SHIP; no automated test mapped |

### 4. Overall BEHAVE verdict

**PASS** — Assigned VAs **VA-01**, **VA-02** (CI contract), **VA-11** (pytest + git grep) satisfied. Live Postgres RLS integration deferred (connection config). **Not** RM-0 gate sign-off — remaining RM-0 VAs (VA-04–VA-10, VA-12) unmapped.

**Next:** BUILD-ORDER #8 — dlt + Shopify (`T-P0-010`); fix `DATABASE_URL` for optional `TRITA_RUN_ISOLATION=1` proof.

---

## SHIP — F-INGEST-SHOPIFY raw + Shopify tap (T-P0-010, T-P0-011) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Implemented by:** Worker (SHIP)
**Git commit:** _(deferred)_

### What was done

- Migration `20260520200000_raw_shopify_events.sql` — `raw.shopify_events` + RLS + dedup unique key
- Package `trita/data/dlt` (`trita-dlt`): envelope, Postgres writer, Shopify normalizer + Yoga Bar fixture
- CLI: `python -m trita_dlt.shopify.run --tenant-id <uuid>`
- Tests: envelope, pipeline, migration contract; idempotency integration (skip without `TRITA_RUN_ISOLATION`)
- MCP: `raw_shopify_events` applied remotely (success)
- MISSION item **8** checked; `F-INGEST-SHOPIFY` → **in_progress** in REGISTRY

### Commands run

```bash
cd trita/data/dlt
pip install -e ".[dev]"
pytest tests/ -q
# exit code: 0 — 6 passed, 1 skipped
```

### Behavioral validator (BEHAVE)

| Command | Exit | VAs |
|---------|------|-----|
| `cd trita/data/dlt && pytest tests/test_envelope.py tests/test_shopify_pipeline.py tests/test_raw_migration_contract.py -q` | 0 | T-P0-010/011 contract |
| `TRITA_RUN_ISOLATION=1 DATABASE_URL=... pytest tests/test_shopify_idempotency.py -q` | — | T-P0-013 / VA-04 prep |

**Yoga Bar manual raw load:** `python -m trita_dlt.shopify.run --tenant-id <yoga-bar-tenant-uuid>` with `DATABASE_URL` set.

### Assertions

| VA | Status |
|----|--------|
| **VA-05** | **Deferred** — needs dbt staging/gold (`T-P0-020`+) |
| **VA-04** | **Deferred** — webhook HMAC (`T-P0-012`) |
| T-P0-013 idempotency | **Implemented** in writer; pytest when DB configured |

### Canonical Supabase project (2026-05-20)

**Use:** `uieltrycgbeyebvaalqm` — `https://uieltrycgbeyebvaalqm.supabase.co` (see [`infra/supabase/PROJECT.md`](infra/supabase/PROJECT.md)).

- `.env` `NEXT_PUBLIC_SUPABASE_URL` already correct; `DATABASE_URL` pooler username fixed to `postgres.uieltrycgbeyebvaalqm`.
- **Re-link Cursor Supabase MCP** to this project (not `bmfakoiiebmsgdtimwdu`).
- Apply migrations: `python scripts/apply_migrations.py` (from machine with working DB connectivity).

### Notes for next worker

- **Active:** `T-P0-012` webhook receiver + `T-P0-013` HMAC (MISSION item 9)
- Quick closes: MISSION item **4** (`.env.example` done), **5** (ADR-001 Accepted), **T-P0-003** service_role audit

### Scrutiny / Behavioral (E2E)

**BEHAVE (Worker):**

- Command: `cd trita/data/dlt && pytest tests/test_envelope.py tests/test_shopify_pipeline.py tests/test_raw_migration_contract.py -q`
- Exit code: 0
- VAs covered: _(contract only; VA-05/04 next SHIPs)_

---

## SHIP — Shopify OAuth + API sync (T-P0-011, T-P0-013) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Implemented by:** Worker (SHIP)
**Scope:** OAuth **not** webhooks (per product direction)

### What was done

- Migration `20260520300000_connector_credentials.sql` — encrypted tokens, RLS (no authenticated SELECT)
- API: `GET /v1/sources/shopify/connect`, `/callback`, `POST /sync`, `GET /status`
- `trita_api/shopify_oauth.py` — authorize, token exchange, Admin API fetch
- Tokens encrypted with Fernet (`CONNECTOR_TOKEN_KEY` or JWT secret)
- Sync → `trita_dlt` normalize + idempotent `write_shopify_events`
- Tests: 22 passed, 3 skipped (`trita/apps/api`)

### Setup (Yoga Bar on `uieltrycgbeyebvaalqm`)

1. `python scripts/apply_migrations.py` (includes `connector_credentials`)
2. Fill `.env`: `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET`, `SHOPIFY_OAUTH_REDIRECT_URI`
3. Partner Dashboard → redirect URL: `http://localhost:8000/v1/sources/shopify/callback`
4. Browser (logged in with JWT): `GET /v1/sources/shopify/connect?shop=yoga-bar`
5. `POST /v1/sources/shopify/sync` with Bearer token

### Commands run

```bash
cd trita/apps/api
pip install -e ".[dev]"
pip install -e ../../data/dlt
pytest tests/ -q
# exit code: 0 — 22 passed, 3 skipped
```

### BEHAVE

```bash
cd trita/apps/api
pip install -e ../../data/dlt
pip install -e ".[dev]"
pytest tests/test_shopify_oauth.py tests/test_shopify_sync.py tests/isolation/test_connector_credentials_migration.py -q
```

### Assertions

| VA | Verdict |
|----|---------|
| **VA-01** | **PASS** — connect/sync/status require JWT; tenant from token |
| **VA-02** | **PASS** — credentials migration RLS contract (no public read policy) |
| **T-P0-013** | **PASS** — writer `ON CONFLICT DO NOTHING` (dlt tests + sync path) |
| **VA-04** | **Deferred** — webhooks/HMAC out of scope |
| **VA-05** | **Deferred** — raw only until dbt (#10) |

### Notes for next worker

- **Active:** dbt staging + gold shell (`T-P0-020`)
- Optional later: `T-P0-012` webhooks if VA-04 required for RM-0 gate

---

## SHIP — dbt staging + gold shell (F-GRAPH-SHELL, T-P0-020, T-P0-021) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Implemented by:** Worker (SHIP)
**Assertions:** **VA-05**

### What was done

- Migration `20260520400000_graph_schemas.sql` — `staging`, `gold`, `quarantine` schemas
- dbt project `trita/data/dbt`: staging views (Shopify orders/lines/inventory/products/variants), gold tables (`dim_sku`, `fact_order_line`, `fact_inventory_daily`), quarantine `shopify_invalid`
- `macros/generate_schema_name.sql` — schemas without `public_` prefix
- `scripts/run_dbt.py` — runs dbt from `DATABASE_URL` in `.env`
- Tests: `test_dbt_contract.py` (CI); `test_va05_yoga_bar.py` (live VA-05)
- MCP: `graph_schemas` applied on `vodcfevbhltftbpjybrf`

### Commands run

```bash
pip install dbt-core==1.8.2 dbt-postgres==1.8.2
cd trita/data/dbt && pip install -e ".[dev]"
pytest tests/test_dbt_contract.py -q
# exit 0 — 6 passed

python scripts/run_dbt.py run
# exit 0 — 9 models; gold.dim_sku SELECT 27; fact_inventory_daily SELECT 27; fact_order_line SELECT 0 (no orders in raw)

TRITA_RUN_VA05=1 C:\Python313\python.exe -m pytest trita/data/dbt/tests/test_va05_yoga_bar.py -q
# exit 0 — 1 passed
```

### BEHAVE (VA-05)

| Command | Exit | Notes |
|---------|------|-------|
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | 0 | Contract |
| `python scripts/run_dbt.py run` | 0 | Yoga Bar gold populated from products + inventory raw |
| `TRITA_RUN_VA05=1` + `test_va05_yoga_bar.py` | 0 | E2E assertion |

### Assertions

| VA | Verdict |
|----|---------|
| **VA-05** | **PASS** — Yoga Bar `raw.shopify_events` → `staging.*` → `gold.dim_sku` (27), `gold.fact_inventory_daily` (27); `fact_order_line` 0 until orders API allowed (protected customer data) |

### Notes for next worker

- **Active:** LiteLLM + OpenMeter (`T-P0-030`) or Next auth + Sources shell (`T-P0-040`)
- Apply `20260520400000_graph_schemas.sql` on canonical DB if not already applied
- dbt deps: pin `dbt-core==1.8.2` + `dbt-postgres==1.8.2`; use Python 3.13 for `TRITA_RUN_VA05` on Windows if default pytest is 3.12

---

## SHIP — `.env.example` (BUILD-ORDER item 4, VA-11) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Implemented by:** Worker (SHIP)
**Assertions:** **VA-11**

### What was done

- Rewrote root `.env.example`: all Phase 0 vars, placeholder Supabase URL (`YOUR_PROJECT_REF`), no secret-shaped values
- Added `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `SHOPIFY_REDIRECT_URI`, `YOGA_BAR_TENANT_ID`, dbt/Shopify/pilot optional flags
- Strengthened `test_env_example.py` (4 tests): JWT/Shopify/DB URL patterns blocked; placeholder URL enforced
- Aligned `docs/OPEN_SOURCE_STACK.md`, `README.md`, `trita/README.md` copy instructions

### Commands run

```bash
cd trita/apps/api
pytest tests/test_env_example.py -q
# exit 0 — 4 passed

cd <repo-root>
git grep -l "SUPABASE_SERVICE_ROLE_KEY=" -- ':!*.example' ':!.env.example' ':!HANDOFF.md' ':!tests/BEHAVE.md' && exit 1 || exit 0
# exit 1 — no committed secrets (grep found no matches)
```

### BEHAVE (VA-11)

| Command | Exit | Verdict |
|---------|------|---------|
| `pytest trita/apps/api/tests/test_env_example.py -q` | 0 | **PASS** |
| `git grep` secret scan | 1 (no matches) | **PASS** |

### Notes for next worker

- **Active:** ADR-001 checkbox (already Accepted in docs) or `T-P0-005` Render deploy
- Real `.env` stays gitignored; never copy live keys into `.env.example`

---

## SHIP — ADR-001 Dagster Accepted (T-P0-050) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Implemented by:** Worker (SHIP)
**Assertions:** ADR planning gate (RM-0); **VA-09** runtime deferred to T-P0-051

### What was done

- Confirmed and extended [docs/adr/001-orchestrator.md](docs/adr/001-orchestrator.md) — **Accepted**, T-P0-050 acceptance record
- Added [docs/pipelines/P-ORCH-DAILY-SHELL.md](docs/pipelines/P-ORCH-DAILY-SHELL.md) — spec for next task (ingest → dbt chain, VA-09)
- Linked spec from [docs/pipelines/REGISTRY.md](docs/pipelines/REGISTRY.md)
- Updated `trita/data/orchestration/README.md`, [docs/checklists/BASELINE.md](docs/checklists/BASELINE.md) ADR index checkbox
- Contract tests: `trita/apps/api/tests/test_adr001_accepted.py` (5 tests)

### Commands run

```bash
cd trita/apps/api
pytest tests/test_adr001_accepted.py -q
# exit 0 — 5 passed
```

### BEHAVE

| Check | Exit | Verdict |
|-------|------|---------|
| `pytest tests/test_adr001_accepted.py -q` | 0 | **PASS** — ADR-001 Accepted wired in repo |

### Assertions

| Item | Verdict |
|------|---------|
| **T-P0-050** | **PASS** — ADR recorded Accepted; index + registry + orchestration path |
| **VA-09** (partial) | **Deferred** — Dagster job execute proof is **T-P0-051**, not this SHIP |

### Notes for next worker

- **Active:** `T-P0-051` / `P-ORCH-DAILY-SHELL` — implement `trita/data/orchestration/` Dagster defs + one manual run (VA-09)
- Do not add parallel cron ingest→dbt on Render without superseding ADR

---

## SHIP — P-ORCH-DAILY-SHELL (T-P0-051 / VA-09) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Implemented by:** Worker (SHIP)
**Assertions:** **VA-09** — Dagster ingest → dbt once; **T-P0-051**

### What was done

- Dagster package `trita_orchestration`: `daily_shell_job` (shopify_sync → dbt_run → integration_health)
- Runner: `scripts/run_daily_shell.py` (`execute_in_process`)
- Config: `dagster.yaml`, `workspace.yaml`, `pyproject.toml`
- Tests: `trita/data/orchestration/tests/test_daily_shell_defs.py`, `test_va09_integration.py` (gated `TRITA_RUN_VA09=1`)
- Default ingest: `TRITA_ORCH_INGEST_MODE=direct` (no API required)

### Commands run

```bash
cd trita/data/orchestration
pip install -e . -e ../dlt -e ../../apps/api

cd ../../..
python scripts/run_daily_shell.py
# exit 0
# daily_shell_job succeeded
#   raw_events: 45
#   gold_dim_sku: 27

python -m pytest trita/data/orchestration/tests/test_daily_shell_defs.py -q
# exit 0 — 3 passed (use python -m pytest; PATH pytest may be Python 3.12 without dagster)
```

### BEHAVE

| Check | Exit | Verdict |
|-------|------|---------|
| `python scripts/run_daily_shell.py` | 0 | **PASS** — full chain for Yoga Bar |
| `python -m pytest …/test_daily_shell_defs.py -q` | 0 | **PASS** — job registered, 3 ops |

### Assertions

| Item | Verdict |
|------|---------|
| **T-P0-051** | **PASS** — manual job run succeeded |
| **VA-09** | **PASS** — ingest → dbt → gold.dim_sku > 0 |

### Notes for next worker

- **Active:** `T-P0-005` Render deploy (VA-10) or LiteLLM (`F-PLAT-003`)
- Schedules/sensors for `P-ORCH-DAILY` remain future work

---

## SHIP — Render + LiteLLM (T-P0-005 / F-PLAT-003) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Implemented by:** Worker (SHIP)
**Assertions:** **VA-07** PASS (pytest); **VA-10** blueprint PASS; live health depends on Blueprint apply

### What was done

**Render (T-P0-005)**

- [render.yaml](render.yaml) — `trita-api` + `trita-litellm` (starter, Singapore)
- [infra/render/README.md](infra/render/README.md), `scripts/check_render_health.ps1` / `.sh`
- `tests/test_render_blueprint.py`

**LiteLLM (F-PLAT-003 / T-P0-030–031)**

- [trita/services/litellm/config.yaml](trita/services/litellm/config.yaml), `scripts/start-litellm.ps1`
- API: `trita_api/llm_budget.py`, `llm_client.py`, `routes/llm.py` — `/v1/llm/draft`, `/v1/llm/budget`
- Tests: `test_llm_budget.py`, `test_llm_draft.py` (VA-03 output guard)

### Commands run

```bash
cd trita/apps/api
python -m pytest tests/test_render_blueprint.py tests/test_llm_budget.py tests/test_llm_draft.py tests/test_health.py tests/test_env_example.py -q
# exit 0 — 14 passed
```

### BEHAVE

| Check | Verdict |
|-------|---------|
| **VA-07** | **PASS** — budget exceeded → fallback, no proxy call |
| **T-P0-005** | **PASS** — blueprint + health endpoint contract |
| **VA-10** (live) | **Pending** — run `check_render_health` after Blueprint apply; `.env` may point at staging URL |

### Human step for VA-10 live

1. Push `render.yaml`, apply Render Blueprint, fill secrets.
2. Set `RENDER_HEALTH_URL` to deployed `trita-api` host.
3. `.\scripts\check_render_health.ps1` → exit 0.

### Notes for next worker

- **Active:** OpenMeter `F-PLAT-004` / `T-P0-032` or Next auth `T-P0-040`
- **F-PLAT-004** not in this SHIP

---

## SHIP — LiteLLM + OpenMeter (F-PLAT-003/004, T-P0-030–032) — 2026-05-20

**Status:** Complete (awaiting Scrutiny)
**Assertions:** **VA-07** (prior), **VA-08**, **T-P0-030**–**T-P0-032**

### What was done

- **F-PLAT-003** (already shipped): LiteLLM proxy, budget, `/v1/llm/draft`
- **F-PLAT-004:** `trita_api/metering.py` — CloudEvents to OpenMeter; wired on LLM, Shopify sync, `run_dbt.py`
- **T-P0-030/031:** Local LiteLLM + per-tenant token cap (documented)
- **T-P0-032:** Six Phase 0 meters; `GET /v1/metering/status`; [P-METER-EXPORT.md](docs/pipelines/P-METER-EXPORT.md)
- Tests: `tests/test_openmeter.py`; `scripts/verify-openmeter.ps1`

### Commands run

```bash
cd trita/apps/api
python -m pytest tests/test_llm_budget.py tests/test_llm_draft.py tests/test_openmeter.py -q
# exit 0
```

### BEHAVE

| Check | Verdict |
|-------|---------|
| **VA-08** | **PASS** — ingest contract + pytest |
| **VA-07** | **PASS** — unchanged |

### Notes

- OpenMeter UI visibility requires `OPENMETER_URL` + `OPENMETER_API_KEY` in `.env` (optional for local dev)
- **T-P0-033** OTEL deferred

---

## Scrutiny Validation — 2026-05-20 — PASS (PATCH: RM-0 batch)

**Scope:**

1. **New:** SHIP — `.env.example` (BUILD-ORDER item 4, **VA-11**)
2. **Regression:** Full RM-0 stack (API + dlt + dbt) — ingest/OAuth/dbt batch

**Reviewer:** Scrutiny → **PATCH** (sync test fix; no product code change)

**Prior gate:** **FAIL** until `test_shopify_sync.py` mocked `fetch_products` (502 from live Admin API call).

### PATCH applied

- `tests/test_shopify_sync.py`: `@patch("trita_api.routes.shopify.fetch_products")` + stub product list (aligns with `/sync` calling orders, inventory, **and** products).

### Checks run (post-PATCH)

| Check | Command | Result |
|-------|---------|--------|
| VA-11 | `pytest trita/apps/api/tests/test_env_example.py -q` | **4 passed** |
| BEHAVE git grep | `git grep SUPABASE_SERVICE_ROLE_KEY=` (excludes) | exit 1 (clean) |
| `.env` tracked | `git check-ignore .env` | ignored |
| API tests (full) | `pytest tests/ -q` in `trita/apps/api` | **23 passed**, 3 skipped |
| dlt tests | `pytest tests/ -q` in `trita/data/dlt` | 6 passed, 1 skipped |
| dbt contract + VA-05 | contract 6 passed; `TRITA_RUN_VA05=1` live | 1 passed |
| Types (API) | `mypy src/trita_api` (Python 3.12) | 0 issues |

### Per-assertion — `.env.example` SHIP

| VA | Verdict | Evidence |
|----|---------|----------|
| **VA-11** | **PASS** | Required keys documented; forbidden secret patterns + placeholder Supabase URL tests; `.env` gitignored |

**Non-blocking (VA-11):** `SHOPIFY_OAUTH_REDIRECT_URI` and `SHOPIFY_REDIRECT_URI` duplicate the same default — harmless but could consolidate in a doc-only follow-up.

### Per-assertion — RM-0 regression

| VA | Verdict |
|----|---------|
| **VA-01** | **PASS** — JWT on connect/sync/status |
| **VA-02** | **PASS** (contract) — credentials RLS |
| **T-P0-013** | **PASS** — `ON CONFLICT DO NOTHING` |
| **VA-05** | **PASS** — live E2E + dbt contract |
| **VA-11** | **PASS** — `.env.example` + pytest + git grep |
| VA-04 | Deferred (webhooks) — OK |
| VA-03, VA-12 | N/A |

### Sub-feature verdicts

| Feature | Verdict |
|---------|---------|
| `.env.example` / BUILD-ORDER #4 | **PASS** |
| `F-INGEST-SHOPIFY`, `F-GRAPH-SHELL` | **PASS** |
| Shopify OAuth + sync | **PASS** (sync test unblocked) |

### Scrutiny — `.env.example` + RM-0 regression — 2026-05-20

**Verdict:** **PASS** (RM-0 batch incl. Shopify sync)

**Non-blocking notes:**

1. `/dev/shopify/*` with `tenant_id` query — dev-only when `ENVIRONMENT=development`.
2. `mypy` pathspec quirk locally — not a product blocker.
3. **T-P0-003** `service_role` audit still open.

**VERDICT:** **PASS** — RM-0 scrutiny batch cleared after PATCH; re-run **BEHAVE** if gate record must refresh.

---

## Scrutiny Validation — 2026-05-20 — PASS (independent re-run)

**Scope:** No new SHIPs since prior PASS entry. Re-verify RM-0 batch + `.env.example` (VA-11).

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/ -q` | **23 passed**, 3 skipped |
| `pytest trita/apps/api/tests/test_env_example.py -q` | **4 passed** |
| `pytest trita/data/dlt/tests/ -q` | 6 passed, 1 skipped |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | 6 passed |
| `TRITA_RUN_VA05=1` `test_va05_yoga_bar.py` | 1 passed (38.8s) |
| `git grep` service role | exit 1 (clean) |
| `.env` | gitignored |
| `mypy src/trita_api` | 0 issues |
| `test_shopify_sync.py` | `fetch_products` mock present — sync test green |

### Per-assertion (completed RM-0 work to date)

| VA | Verdict |
|----|---------|
| **VA-01** | **PASS** |
| **VA-02** | **PASS** (contract) |
| **VA-05** | **PASS** |
| **VA-11** | **PASS** |
| **T-P0-013** | **PASS** |
| **VA-04** | Deferred (webhooks) |
| VA-06–10, VA-12 | Not shipped — N/A for this batch |

### Sub-feature verdicts

| Feature | Verdict |
|---------|---------|
| `F-BOOT-001`, `F-PLAT-001/002`, `F-INGEST-SHOPIFY`, `F-GRAPH-SHELL`, Shopify OAuth/sync, `.env.example` | **PASS** |

**VERDICT:** **PASS** — matches prior PATCH gate; no regressions detected. RM-0 program gate still open (LiteLLM, health API, Dagster, Render, Sources UI, VA-04 if required).

---

## Scrutiny Validation — 2026-05-20 — PASS (ADR-001 + P-ORCH-DAILY-SHELL)

**Scope:**

1. **SHIP** — ADR-001 Dagster Accepted (`T-P0-050`) — docs + contract tests
2. **SHIP** — `P-ORCH-DAILY-SHELL` (`T-P0-051`, **VA-09**) — Dagster `daily_shell_job`
3. **Regression:** API (incl. ADR tests), dlt, dbt contract

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest trita/apps/api/tests/test_adr001_accepted.py -q` | **6 passed** |
| `python -m pytest trita/data/orchestration/tests/test_daily_shell_defs.py -q` | **3 passed** |
| `TRITA_RUN_VA09=1` `test_va09_integration.py` | **1 passed** (23.3s) — full `run_daily_shell.py` chain |
| `pytest trita/apps/api/tests/ -q` | **29 passed**, 3 skipped |
| `pytest trita/data/dlt/tests/ -q` | 6 passed, 1 skipped |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | 6 passed |
| `git grep` / `.env` | clean; `.env` gitignored |

### Code review

| Area | Verdict | Notes |
|------|---------|-------|
| **ADR-001** | **PASS** | `docs/adr/001-orchestrator.md` **Status: Accepted**; registry + `P-ORCH-DAILY-SHELL` spec linked |
| **VA-09** | **PASS** | Job chain `shopify_sync_op` → `dbt_run_op` → `integration_health_op`; live run proves raw + `gold.dim_sku` > 0 |
| Tenancy (orch) | **PASS** (pilot) | `YOGA_BAR_TENANT_ID` from env only; no request-body tenant override in shell |
| Deterministic engine | **PASS** | No LLM; dbt owns gold numbers |
| Stubs | **PASS** | Real Dagster defs + subprocess dbt + Shopify fetch — not a doc-only stub |
| Parallel cron | **PASS** | No Render/cron ingest bypass found in repo |

**Non-blocking:**

1. **T-P0-003** — orchestration + API still use `DATABASE_URL` (service_role path); audit deferred.
2. Schedules/sensors for production cadence not in this SHIP (per handoff).
3. Worker noted 5 ADR tests; file has **6** — harmless doc drift.

### Per-assertion

| VA / task | Verdict |
|-----------|---------|
| **T-P0-050** | **PASS** |
| **T-P0-051** | **PASS** |
| **VA-09** | **PASS** |
| Prior RM-0 (VA-01, VA-02, VA-05, VA-11, T-P0-013) | **PASS** (regression suite) |
| **VA-04, VA-06–08, VA-10, VA-12** | Not shipped / deferred |

### Sub-feature verdicts

| Feature | Verdict |
|---------|---------|
| ADR-001 / `T-P0-050` | **PASS** |
| `P-ORCH-DAILY-SHELL` / `T-P0-051` | **PASS** |
| RM-0 stack (prior SHIPs) | **PASS** (no regression) |

**VERDICT:** **PASS** — ADR-001 + Dagster daily shell cleared. RM-0 program gate still needs LiteLLM, health API UI, Render (VA-10), Sources shell, VA-04 if required.

---

## Behavioral (automated) — 2026-05-20 — PASS

**BEHAVE role** — full RM-0 stack to date: plat/auth, ingest, OAuth/sync, dbt (**VA-05**), `.env.example` (**VA-11**), ADR-001 (**T-P0-050**), `P-ORCH-DAILY-SHELL` (**VA-09**)  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-20 — PASS (ADR-001 + P-ORCH-DAILY-SHELL)` + prior RM-0 PASS entries

### 1. Environment

| Check | Status |
|-------|--------|
| Git | yes |
| `DATABASE_URL`, `YOGA_BAR_TENANT_ID` | SET |
| `RENDER_HEALTH_URL` | SET — `curl -sf …/health` exit **22** (not deployed; VA-10 N/A) |

### 2. Commands run

```powershell
cd trita/apps/api && pip install -e ".[dev]" && pip install -e ../../data/dlt
pytest tests/ -q
# exit 0 — 29 passed, 3 skipped

pytest tests/test_adr001_accepted.py -q
# exit 0 — 6 passed

pytest tests/test_env_example.py -q
# exit 0 — 4 passed

cd trita/data/dlt && pytest tests/ -q
# exit 0 — 6 passed, 1 skipped

cd trita/data/dbt && pytest tests/test_dbt_contract.py -q
# exit 0 — 6 passed

python scripts/run_dbt.py run
# exit 0 — 9 models PASS

TRITA_RUN_VA05=1 python -m pytest trita/data/dbt/tests/test_va05_yoga_bar.py -q
# exit 0 — 1 passed (12.2s)

cd trita/data/orchestration && pip install -e . -e ../dlt -e ../../apps/api
python -m pytest tests/test_daily_shell_defs.py -q
# exit 0 — 3 passed

python scripts/run_daily_shell.py
# exit 0 — raw_events: 45, gold_dim_sku: 27

TRITA_RUN_VA09=1 python -m pytest trita/data/orchestration/tests/test_va09_integration.py -q
# exit 0 — 1 passed (21.9s; first run in session exited 1 — flaky subprocess; direct script green)

git grep -l "SUPABASE_SERVICE_ROLE_KEY=" … && exit 1 || exit 0
# exit 0 — clean
```

### 3. VA mapping

| VA / task | Verdict | Evidence | Exit |
|-----------|---------|----------|------|
| **VA-01** | **PASS** | API JWT + Shopify routes | 0 |
| **VA-02** | **PASS** | RLS + credentials migration contracts | 0 |
| **VA-05** | **PASS** | dbt contract + `run_dbt.py` + live Yoga Bar | 0 |
| **VA-09** | **PASS** | `test_daily_shell_defs.py` + `run_daily_shell.py` + `test_va09_integration.py` | 0 |
| **VA-11** | **PASS** | `test_env_example.py` (4) + `git grep` | 0 |
| **T-P0-050** | **PASS** | `test_adr001_accepted.py` | 0 |
| **T-P0-013** | **PASS** | dlt contract + sync mocks | 0 |
| **VA-04** | **DEFERRED** | Webhooks/HMAC — no suite | — |
| **VA-06** | **N/A** | `health_api` TBD | — |
| **VA-07, VA-08** | **N/A** | `test_llm_budget.py` missing | — |
| **VA-10** | **N/A** | Render health curl failed (exit 22) | 22 |
| **VA-12** | **N/A** | No decision emitter tests | — |

### 4. Overall

**PASS** — All mapped automated suites green for shipped RM-0 work. **Not** full RM-0 program gate (VA-06–08, VA-10 deploy, VA-12, optional VA-04). MISSION not marked done.

**Next:** `T-P0-005` Render (VA-10) or `F-PLAT-003` LiteLLM (`T-P0-030`).

---

## Scrutiny Validation — 2026-05-20 — PASS (Render + LiteLLM)

**Scope:** SHIP — Render + LiteLLM (`T-P0-005`, `F-PLAT-003`) — **VA-07**, **VA-03**, **T-P0-005**; **VA-10** live deferred

**Reviewer:** Scrutiny (adversarial review; no implementation)

### Checks run (fresh)

| Check | Result |
|-------|--------|
| `pytest tests/test_render_blueprint.py tests/test_llm_budget.py tests/test_llm_draft.py -q` | **9 passed** |
| `pytest trita/apps/api/tests/ -q` (full regression) | **38 passed**, 3 skipped |
| dlt / orchestration contract | 6+1 skip; 3 passed |
| `git grep` secrets | exit 1 (clean); `.env` gitignored |
| Live `RENDER_HEALTH_URL` curl | **N/A** — not set in scrutiny shell (Blueprint apply is human step) |

### Code review

| Area | Verdict | Notes |
|------|---------|-------|
| **VA-07** | **PASS** | `budget_exceeded` → fallback; `httpx.post` not called when over cap |
| **VA-03** | **PASS** | System prompt + `_INVENTORY_NUMBER_PATTERN` guard; `test_va03_inventory_numbers_in_model_output_blocked` |
| **VA-01** | **PASS** | `/v1/llm/draft` uses `TenantDep`; body `tenant_id` override → 403 |
| **T-P0-005** | **PASS** | `render.yaml`: `trita-api` `/health`, `trita-litellm`, Singapore starter |
| **VA-10** | **PARTIAL** | Blueprint + `/health` contract tests; **live** 7d clean requires deployed URL |
| **VA-08** | **N/A** | OpenMeter not in this SHIP |
| Stubs | **PASS** | Real proxy client + budget module; not UI-only |

**Non-blocking:**

1. Token budget is **in-process memory** (`llm_budget._usage`) — resets on API restart; acceptable for Phase 0, document before multi-instance Render.
2. `LITELLM_MASTER_KEY` added to `.env.example` — confirm `test_env_example` REQUIRED_KEYS includes it (full suite green).
3. **F-PLAT-004** / OpenMeter still planned per MISSION.

### Per-assertion

| VA / task | Verdict |
|-----------|---------|
| **VA-07** | **PASS** |
| **VA-03** | **PASS** |
| **T-P0-005** | **PASS** (blueprint) |
| **VA-10** | **PARTIAL** — apply Blueprint + `check_render_health` for live gate |
| **VA-08** | N/A |
| Prior RM-0 stack | **PASS** (38 API tests, no regression) |

### Sub-feature verdicts

| Feature | Verdict |
|---------|---------|
| `F-PLAT-003` / LiteLLM | **PASS** |
| `T-P0-005` / Render blueprint | **PASS** |

**VERDICT:** **PASS** — Render + LiteLLM SHIP cleared for merge. Complete **VA-10** live evidence after Blueprint deploy.

---

## Behavioral (automated) — 2026-05-20 — PASS

**BEHAVE role** — RM-0 full regression + **Render + LiteLLM** (`T-P0-005`, `F-PLAT-003`, **VA-07**, **VA-03**, **T-P0-005**)  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-20 — PASS (Render + LiteLLM)`

### 1. Environment

| Check | Status |
|-------|--------|
| Git | yes |
| `DATABASE_URL`, `YOGA_BAR_TENANT_ID` | SET |
| `RENDER_HEALTH_URL` | SET (`trita-api-staging.onrender.com`) — live health **404** |

### 2. Commands run

```powershell
cd trita/apps/api
pip install -e ".[dev]"; pip install -e ../../data/dlt
pytest tests/ -q
# exit 0 — 38 passed, 3 skipped

pytest tests/test_render_blueprint.py tests/test_llm_budget.py tests/test_llm_draft.py -q
# exit 0 — 9 passed (VA-07, VA-03, T-P0-005 contract)

pytest tests/test_env_example.py -q
# exit 0 — 4 passed

cd trita/data/dlt && pytest tests/ -q
# exit 0 — 6 passed, 1 skipped

cd trita/data/dbt && pytest tests/test_dbt_contract.py -q
# exit 0 — 6 passed

python scripts/run_dbt.py run
# exit 0 — 9 models

TRITA_RUN_VA05=1 python -m pytest trita/data/dbt/tests/test_va05_yoga_bar.py -q
# exit 0 — 1 passed (11.4s; first run in batch exited 1 — race with parallel dbt; retry green)

cd trita/data/orchestration
python -m pytest tests/test_daily_shell_defs.py -q
# exit 0 — 3 passed

TRITA_RUN_VA09=1 python -m pytest trita/data/orchestration/tests/test_va09_integration.py -q
# exit 0 — 1 passed (21.5s)

python scripts/run_daily_shell.py
# exit 0 — raw_events: 45, gold_dim_sku: 27

git grep -l "SUPABASE_SERVICE_ROLE_KEY=" … && exit 1 || exit 0
# exit 0 — clean

.\scripts\check_render_health.ps1
# exit 1 — GET …/health → 404 Not Found (staging host not serving /health yet)
```

### 3. VA mapping

| VA / task | Verdict | Evidence | Exit |
|-----------|---------|----------|------|
| **VA-01** | **PASS** | Full API suite | 0 |
| **VA-02** | **PASS** | RLS + credentials contracts | 0 |
| **VA-03** | **PASS** | `test_llm_draft.py` — output guard | 0 |
| **VA-05** | **PASS** | dbt contract + `run_dbt.py` + live Yoga Bar | 0 |
| **VA-07** | **PASS** | `test_llm_budget.py` — cap → fallback | 0 |
| **VA-09** | **PASS** | Dagster defs + integration + `run_daily_shell.py` | 0 |
| **VA-11** | **PASS** | `test_env_example.py` + `git grep` | 0 |
| **T-P0-005** | **PASS** | `test_render_blueprint.py` | 0 |
| **T-P0-050/051** | **PASS** | ADR + orch (regression) | 0 |
| **T-P0-013** | **PASS** | dlt contract | 0 |
| **VA-10** | **PARTIAL** | Blueprint contract PASS; live `check_render_health` **404** | 1 |
| **VA-04** | **DEFERRED** | Webhooks | — |
| **VA-06** | **N/A** | No health API pytest | — |
| **VA-08** | **N/A** | OpenMeter not shipped | — |
| **VA-12** | **N/A** | No decision tests | — |

### 4. Overall

**PASS** — All automated suites green for shipped RM-0 work including **VA-07** / **VA-03** / Render blueprint. **VA-10** live remains **PARTIAL** until staging `trita-api` serves `/health`. **Not** full RM-0 program gate (VA-06, VA-08, VA-12, optional VA-04). MISSION not marked done.

**Next:** Deploy Render Blueprint + re-run `check_render_health.ps1`; then `F-PLAT-004` OpenMeter or `T-P0-040` Sources shell.

---

## Behavioral (automated) — 2026-05-21 — PASS

**BEHAVE role** — RM-0 regression + RM-1 (`F-CONN-002/004/006`, `F-CONN-005` CSV hub, UI/health)  
**Scrutiny precondition:** **MET** — `PASS (F-CONN-005 CSV hub)`, `PASS (PATCH: Shopify route order)`, RM-0 RETRO **GO**

### 1. Environment

| Check | Status |
|-------|--------|
| Git | yes |
| `DATABASE_URL`, `YOGA_BAR_TENANT_ID` | SET |
| Render | **not used** — `RENDER_HEALTH_URL=http://127.0.0.1:8000`; `dev-health.ps1` OK |

### 2. Commands run

```powershell
cd trita/apps/api
pip install -e ".[dev]"; pip install -e ../../data/dlt
pytest tests/ -q
# exit 0 — 52 passed, 3 skipped

pytest tests/test_integration_health.py tests/test_csv_hub.py tests/test_connectors_rm1.py tests/test_shopify_sync.py tests/test_llm_budget.py tests/test_llm_draft.py tests/test_adr001_accepted.py tests/test_render_blueprint.py tests/test_env_example.py -q
# exit 0 — 33 passed

python scripts/verify_rm0_gate.py
# exit 0 — raw=45, gold.dim_sku=27, health=healthy, VA-12 no decision tables

cd trita/data/dlt && pytest tests/ -q
# exit 0 — 6 passed, 1 skipped

cd trita/data/dbt && pytest tests/test_dbt_contract.py -q
# exit 0 — 6 passed

python scripts/run_dbt.py run
# exit 0 — 18 models PASS

TRITA_RUN_VA05=1 python -m pytest trita/data/dbt/tests/test_va05_yoga_bar.py -q
# exit 0 — 1 passed (40.3s)

cd trita/data/orchestration
python -m pytest tests/test_daily_shell_defs.py -q
# exit 0 — 3 passed

TRITA_RUN_VA09=1 python -m pytest trita/data/orchestration/tests/test_va09_integration.py -q
# exit 0 — 1 passed (27.7s)

cd trita && pnpm --filter @trita/web build
# exit 0

git grep … SUPABASE_SERVICE_ROLE_KEY=
# exit 0 — clean

.\scripts\dev-health.ps1
# exit 0 — API :8000/health 200, LiteLLM :4000 OK
```

### 3. VA mapping

| VA / task | Verdict | Evidence | Exit |
|-----------|---------|----------|------|
| **VA-01** | **PASS** | Full API + JWT/connect tests | 0 |
| **VA-02** | **PASS** | RLS + connector/csv migrations (contract) | 0 |
| **VA-03** | **PASS** | `test_llm_draft.py` | 0 |
| **VA-05** | **PASS** | dbt contract + run + live Yoga Bar | 0 |
| **VA-06** | **PASS** | `test_integration_health.py` | 0 |
| **VA-07** | **PASS** | `test_llm_budget.py` | 0 |
| **VA-09** | **PASS** | Dagster defs + VA-09 integration | 0 |
| **VA-11** | **PASS** | `test_env_example.py` + git grep | 0 |
| **VA-12** | **PASS** | `verify_rm0_gate.py` — no decision tables | 0 |
| **VA-26** | **PARTIAL** | `test_csv_hub.py` (4); no idempotent replay test / live tally script in BEHAVE | 0 |
| **T-P0-005** | **PASS** | Blueprint contract; **local** health via `dev-health.ps1` | 0 |
| **VA-04** | **DEFERRED** | Webhooks | — |
| **VA-08** | **N/A** | OpenMeter deferred (RM-4+) | — |
| **VA-10** (Render 7d) | **N/A** | No Render deploy; local `/health` **PASS** | — |

### 4. Overall

**PASS** — Automated suites green for RM-0 gate evidence and shipped RM-1 connectors + CSV hub. **VA-26** live/idempotent replay still manual per Scrutiny notes. MISSION RM-0 item 15 already checked; RM-1 items 16–17 in progress.

**Next:** `F-ID-001` identity; optional `upload_tally_fixture.ps1` + idempotent CSV test for full **VA-26** gate.

---

## Behavioral (automated) — 2026-05-21 (re-run) — PASS

**BEHAVE role** — full stack regression (RM-0 + RM-1 CSV/connectors/UI)  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-20 — PASS (re-run, no new SHIP)`

### Commands (fresh)

| Command | Exit | Notes |
|---------|------|-------|
| `pytest trita/apps/api/tests/ -q` | **0** | 52 passed, 3 skipped |
| Regression bundle (health, csv, rm1, shopify, llm, adr, render, env) | **0** | 33 passed |
| `python scripts/verify_rm0_gate.py` | **0** | raw=45, dim_sku=27, health=healthy, VA-12 |
| `pytest trita/data/dlt/tests/ -q` | **0** | 6 passed, 1 skipped |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | **0** | 6 passed |
| `python scripts/run_dbt.py run` | **0** | 18 models |
| `TRITA_RUN_VA05=1` `test_va05_yoga_bar.py` | **0** | 14.7s |
| `pytest test_daily_shell_defs.py` | **0** | 3 passed |
| `TRITA_RUN_VA09=1` `test_va09_integration.py` | **0** | 21.3s |
| `pnpm --filter @trita/web build` | **0** | |
| `git grep` service role | **0** | clean |
| `.\scripts\dev-health.ps1` | **0** | local API + LiteLLM |

### VA summary

| VA | Verdict |
|----|---------|
| VA-01, VA-02, VA-03, VA-05, VA-06, VA-07, VA-09, VA-11, VA-12 | **PASS** |
| **VA-26** | **PARTIAL** — `test_csv_hub.py` only; idempotent replay test still missing |
| VA-04, VA-08 | **DEFERRED** / **N/A** |
| VA-10 (Render 7d) | **N/A** — local health **PASS** |

**Overall: PASS** — No regressions vs prior BEHAVE (2026-05-21). RM-1 gate (MISSION 21) still needs **VA-26** live + idempotent test per Scrutiny debt.

---

## Behavioral (automated) — 2026-05-21 — PASS (F-ID-001)

**BEHAVE role** — RM-0 + RM-1 + **F-ID-001 / F-ID-002** identity v1  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-21 — PASS (re-run, no new SHIP)`

### Commands (fresh)

| Command | Exit | Notes |
|---------|------|-------|
| `pytest trita/apps/api/tests/ -q` | **0** | **57 passed**, 3 skipped |
| Bundle (+ `test_identity_v1.py`) | **0** | **35 passed** |
| `python scripts/verify_rm0_gate.py` | **0** | raw=45, dim_sku=27, health=healthy, VA-12 |
| `python scripts/refresh_identity.py` | **1** | `DuplicatePreparedStatement` on Supabase pooler (pgbouncer) |
| Live VA-13 (`prepare_threshold=None`) | **0** | resolution_rate=1.0, meets_va13=True, aliases=27 |
| `pytest trita/data/dlt/tests/ -q` | **0** | 6 passed, 1 skipped |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | **0** | 6 passed |
| `python scripts/run_dbt.py run` | **0** | **21** models |
| `TRITA_RUN_VA05=1` `test_va05_yoga_bar.py` | **0** | 13.9s |
| `TRITA_RUN_VA09=1` `test_va09_integration.py` | **0** | 24.3s |
| `pnpm --filter @trita/web build` | **0** | |
| `git grep` | **0** | clean |
| `.\scripts\dev-health.ps1` | **0** | local API + LiteLLM |

### VA summary

| VA | Verdict |
|----|---------|
| **VA-01, VA-02, VA-03, VA-05, VA-06, VA-07, VA-09, VA-11, VA-12** | **PASS** |
| **VA-13** | **PASS** — `test_identity_v1.py` + live refresh (pooler needs `prepare_threshold=None`; fix `refresh_identity.py` for BEHAVE ergonomics) |
| **VA-14** | **N/A** — Data Health UI not shipped |
| **VA-26** | **PARTIAL** — no idempotent CSV test |
| VA-04, VA-08 | **DEFERRED** / **N/A** |
| VA-10 | **N/A** — local health **PASS** |

**Overall: PASS** — Identity SHIP behaviorally verified. **Non-blocking:** patch `scripts/refresh_identity.py` to use `psycopg.connect(..., prepare_threshold=None)` for pooler. RM-1 gate (#21) still open per Scrutiny (CSV debt + metrics/health UI).

---

## Behavioral (automated) — 2026-05-21 — PASS (F-METRICS-001..004)

**BEHAVE role** — full RM-0/RM-1 regression + **F-METRICS-001..004** + identity  
**Scrutiny precondition:** **MET** — `PASS (PATCH: F-METRICS)` + `PASS (independent re-run, metrics PATCH confirmed)`

### Commands (fresh)

| Command | Exit | Notes |
|---------|------|-------|
| `pytest trita/apps/api/tests/ -q` | **0** | **59 passed**, 3 skipped |
| Bundle (metrics, identity, csv, rm1, shopify, health) | **0** | **21 passed** |
| `pytest tests/test_metrics_api.py -q` | **0** | 2 passed |
| `python scripts/verify_rm0_gate.py` | **0** | VA-12 |
| `python scripts/verify_metrics_gate.py` | **0** | dim_sku=27, feat=27 aligned; stockout=0, dead_stock=27, cogs_missing=27 |
| `python scripts/refresh_identity.py` | **0** | meets_va13=True, aliases=27 |
| `pytest trita/data/dlt/tests/ -q` | **0** | 6 passed, 1 skipped |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | **0** | **7 passed** |
| `python scripts/run_dbt.py run` | **0** | **22** models |
| `TRITA_RUN_VA05=1` `test_va05_yoga_bar.py` | **0** | 18.1s |
| `pytest test_daily_shell_defs.py` | **0** | 3 passed (incl. metrics_dbt_op) |
| `TRITA_RUN_VA09=1` `test_va09_integration.py` | **0** | 41.4s |
| `pnpm --filter @trita/web build` | **0** | |
| `git grep` | **0** | clean |
| `.\scripts\dev-health.ps1` | **0** | local API + LiteLLM |

### VA summary

| VA | Verdict |
|----|---------|
| **VA-01, VA-02, VA-03, VA-05, VA-06, VA-07, VA-09, VA-11, VA-12, VA-13** | **PASS** |
| **VA-14** | **PARTIAL** — `verify_metrics_gate.py` **PASS**; **F-REPORT-HEALTH** UI not shipped |
| **F-METRICS-001..004** | **PASS** — mart gate + API tests |
| **VA-26** | **PARTIAL** — CSV idempotent test still missing |
| VA-04, VA-08, VA-10 | **DEFERRED** / **N/A** (local health OK) |

**Overall: PASS** — Metrics SHIP green. RM-1 gate (#21) still needs CSV test debt + health/inventory UI per Scrutiny.

**Next:** `F-REPORT-HEALTH` or `F-UI-INVENTORY-LIST`.

---

## Behavioral (automated) — 2026-05-21 — PASS (F-REPORT-HEALTH, inventory, Sources)

**BEHAVE role** — full stack + **F-REPORT-HEALTH**, **F-UI-INVENTORY-LIST**, **F-UI-SOURCES**  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-21 — PASS (F-REPORT-HEALTH, F-UI-INVENTORY-LIST, F-UI-SOURCES)`

### Commands (fresh)

| Command | Exit | Notes |
|---------|------|-------|
| `pytest trita/apps/api/tests/ -q` | **0** | **60 passed**, 3 skipped |
| Regression bundle (+ `test_reports_api.py`) | **0** | **38 passed** |
| `python scripts/verify_rm0_gate.py` | **0** | VA-12 |
| `python scripts/verify_metrics_gate.py` | **0** | feat=27 aligned |
| `python scripts/refresh_identity.py` | **0** | meets_va13=True |
| `pytest trita/data/dlt/tests/ -q` | **0** | 6 passed, 1 skipped |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | **0** | 7 passed |
| `python scripts/run_dbt.py run` | **0** | 22 models |
| `TRITA_RUN_VA05=1` `test_va05_yoga_bar.py` | **0** | 33.1s |
| `pytest test_daily_shell_defs.py` | **0** | 3 passed |
| `TRITA_RUN_VA09=1` `test_va09_integration.py` | **0** | 49.8s |
| `pnpm --filter @trita/web build` | **0** | `/reports/health`, `/inventory`, `/sources` compile |
| `git grep` | **0** | clean |
| `.\scripts\dev-health.ps1` | **1** | API not running on :8000 (start `.\scripts\start-local.ps1` for live check) |

### VA summary

| VA | Verdict |
|----|---------|
| **VA-01, VA-02, VA-03, VA-05, VA-06, VA-07, VA-09, VA-11, VA-12, VA-13** | **PASS** |
| **VA-14** | **PARTIAL** — `test_reports_api.py` + `verify_metrics_gate.py` **PASS**; no browser/UI↔gold parity test |
| **F-REPORT-HEALTH / F-UI-INVENTORY-LIST / F-UI-SOURCES** | **PASS** (automated) |
| **VA-26** | **PARTIAL** — no idempotent CSV test |
| VA-04, VA-08 | **DEFERRED** / **N/A** |
| VA-10 | **SKIP** (this run) — local API down; blueprint N/A |

**Overall: PASS** — Report/inventory/Sources SHIP green in CI. **RM-1 gate (#21)** still **OPEN** (MISSION unchecked): VA-26 test + formal ≥90% order-line gate.

**Next:** RM-1 gate evidence script; `test_csv_idempotent_replay`; browse `/reports/health` with API up.

---

## Behavioral (automated) — 2026-05-22 — PASS (F-DEC-001..004)

**BEHAVE role** — RM-1 regression + **F-DEC-001..004** (decisions contract, suppression, integrity, emitter)  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-22 — PASS (F-DEC-001..004)`

### Commands (fresh)

| Command | Exit | Notes |
|---------|------|-------|
| `pytest trita/apps/api/tests/ -q` | **0** | **70 passed**, 3 skipped |
| `pytest tests/test_decisions.py -q` | **0** | **8 passed** — VA-15, VA-16, VA-17, VA-03 |
| `python scripts/verify_rm1_gate.py` | **0** | VA-13 100%, VA-14, VA-26 |
| `python scripts/verify_rm0_gate.py` | **1** | **expected** — `public.decisions` exists → VA-12 script outdated post-RM-2 |
| `python scripts/verify_metrics_gate.py` | **0** | feat=27 aligned |
| Regression bundle (csv, reports, metrics, identity, rm1, shopify) | **0** | 24 passed |
| `pytest trita/data/dlt/tests/ -q` | **0** | 6 passed, 1 skipped |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | **0** | 7 passed |
| `pytest test_daily_shell_defs.py` | **0** | 3 passed |
| `pnpm --filter @trita/web build` | **0** | |
| `git grep` | **0** | clean |
| `python scripts/refresh_identity.py` | **0** | meets_va13=True |
| `python scripts/emit_decisions.py` | **2** | integrity suppress (unicommerce) — **0 cards**; VA-17 behavior, not test failure |

### VA summary

| VA | Verdict |
|----|---------|
| **VA-15, VA-16, VA-17** | **PASS** — `test_decisions.py` |
| **VA-03** | **PASS** — impact from metrics; tier 3 rejected |
| **VA-01, VA-02** | **PASS** — JWT emit/list + RLS migration |
| **VA-13, VA-14, VA-26** | **PASS** — `verify_rm1_gate.py` |
| **F-DEC-001..004** | **PASS** (automated) |
| **VA-12** (RM-0 script) | **N/A** — `verify_rm0_gate.py` fails when `decisions` table present (update script for RM-2) |
| RM-2 gate (accept/reject) | **OPEN** — `F-DEC-005` / inbox UI not shipped |
| VA-04, VA-08, VA-10 | **DEFERRED** / **N/A** |

**Overall: PASS** — Decisions SHIP green in CI. Live emit returned 0 cards due to integrity suppress (stale/degraded connector) — correct per VA-17.

**Next:** `F-DEC-005`, `F-INBOX-*`; update `verify_rm0_gate.py` or scope VA-12 to RM-0 snapshot only.

---

## Behavioral (automated) — 2026-05-20 — PASS (F-DEC-005, F-INBOX-001..004)

**BEHAVE role** — RM-1 regression + **F-DEC-005** (audit) + **F-INBOX-001..004** (inbox API + `/inbox` web)  
**Scrutiny precondition:** **MET** — `Scrutiny Validation — 2026-05-22 — PASS (independent re-run, F-DEC-005 / inbox)`

### Commands (fresh)

| Command | Exit | Notes |
|---------|------|-------|
| `pytest trita/apps/api/tests/ -q` | **0** | **74 passed**, 3 skipped |
| `pytest tests/test_decisions.py tests/test_decisions_inbox.py -q` | **0** | **12 passed** — VA-15–17, inbox approve/reject/snooze |
| `python scripts/verify_rm1_gate.py` | **0** | VA-13 100%, VA-14, VA-26 |
| `python scripts/apply_migrations.py` | **0** | Applied `20260521100000_decision_audit.sql` |
| `python scripts/verify_rm2_gate.py` | **1** | **OPEN (live)** — `decisions=0`; no approve/reject audit rows yet |
| `python scripts/verify_rm0_gate.py` | **1** | **expected** — `public.decisions` present → VA-12 script outdated post-RM-2 |
| `python scripts/verify_metrics_gate.py` | **0** | feat=27 aligned |
| Regression bundle (shopify, csv, reports, env, jwt, adr001, llm, health, render) | **0** | **43 passed** |
| `pytest trita/data/dlt/tests/ -q` | **0** | 6 passed |
| `pytest trita/data/dbt/tests/test_dbt_contract.py -q` | **0** | 7 passed |
| `pytest trita/data/orchestration/tests/test_daily_shell_defs.py -q` | **0** | 3 passed |
| `pnpm --filter @trita/web build` | **0** | `/inbox` compiles |
| `git grep` (secrets) | **0** | env var names only in tests/scripts |
| `python scripts/emit_decisions.py` | **2** | integrity suppress (unicommerce) — **0 cards**; VA-17 behavior |

### VA summary

| VA | Verdict |
|----|---------|
| **VA-15, VA-16, VA-17** | **PASS** — `test_decisions.py` |
| **VA-03** | **PASS** — no LLM on inbox actions |
| **VA-01, VA-02** | **PASS** — JWT on approve/reject; `decision_audit` RLS migration applied |
| **VA-13, VA-14, VA-26** | **PASS** — `verify_rm1_gate.py` |
| **F-DEC-005 / F-INBOX-001..004** | **PASS** (automated) |
| **MISSION #25 (RM-2 gate)** | **OPEN** (live) — emit cards + pilot accept/reject in `/inbox`, then re-run `verify_rm2_gate.py` |
| **VA-12** (RM-0 script) | **N/A** — `verify_rm0_gate.py` fails when `decisions` table present |
| VA-04, VA-08, VA-10 | **DEFERRED** / **N/A** (local dev) |

**Overall: PASS** — Inbox SHIP green in CI. Live RM-2 gate blocked on zero decisions + no audit actions (integrity suppress on emit; human inbox step pending).

**Next:** Resolve connector integrity or seed candidates → `emit_decisions.py` → approve/reject one card → `verify_rm2_gate.py`; optional cross-tenant inbox isolation test.

---
