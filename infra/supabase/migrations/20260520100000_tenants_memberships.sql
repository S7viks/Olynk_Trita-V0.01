-- F-PLAT-001: tenants + memberships with RLS (T-P0-001)
-- Apply via Supabase CLI or MCP apply_migration.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE public.membership_role AS ENUM ('owner', 'member', 'viewer');

CREATE TABLE public.tenants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug text NOT NULL,
    display_name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT tenants_slug_unique UNIQUE (slug)
);

CREATE TABLE public.memberships (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES auth.users (id) ON DELETE CASCADE,
    role public.membership_role NOT NULL DEFAULT 'member',
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT memberships_tenant_user_unique UNIQUE (tenant_id, user_id)
);

CREATE INDEX memberships_user_id_idx ON public.memberships (user_id);
CREATE INDEX memberships_tenant_id_idx ON public.memberships (tenant_id);

ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.memberships ENABLE ROW LEVEL SECURITY;

-- Members may read tenants they belong to.
CREATE POLICY tenants_select_member ON public.tenants
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.memberships m
            WHERE m.tenant_id = tenants.id
              AND m.user_id = auth.uid()
        )
    );

-- Users may read their own membership rows.
CREATE POLICY memberships_select_own ON public.memberships
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- No direct INSERT/UPDATE for authenticated on tenants/memberships in V0.0.1 Phase 0
-- (provisioning via service_role / admin flows in later tasks).

GRANT SELECT ON public.tenants TO authenticated;
GRANT SELECT ON public.memberships TO authenticated;
