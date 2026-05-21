# Supabase project (canonical)

| Field | Value |
|-------|--------|
| **Project ref** | `vodcfevbhltftbpjybrf` |
| **API URL** | `https://vodcfevbhltftbpjybrf.supabase.co` |
| **Dashboard** | `https://supabase.com/dashboard/project/vodcfevbhltftbpjybrf` |

All local dev (`.env`), dlt ingest, and FastAPI must use **this** project.

## Cursor MCP

Re-link the Supabase MCP plugin to **`vodcfevbhltftbpjybrf`** in Cursor settings.

## Connection strings

Copy **Session/Transaction pooler** and **Direct** URLs from Dashboard → Project Settings → Database. Pattern:

- **Pooler (app runtime):** `postgresql://postgres.vodcfevbhltftbpjybrf:[PASSWORD]@<region>.pooler.supabase.com:6543/postgres`
- **Direct (DDL/migrations):** `postgresql://postgres:[PASSWORD]@db.vodcfevbhltftbpjybrf.supabase.co:5432/postgres`

`Tenant or user not found` on pooler usually means the username is `postgres` instead of `postgres.vodcfevbhltftbpjybrf`.

## Apply migrations

```bash
# From repo root — uses DATABASE_URL in .env
python scripts/apply_migrations.py
```

Or Supabase CLI: `supabase link --project-ref vodcfevbhltftbpjybrf` then `supabase db push`.
