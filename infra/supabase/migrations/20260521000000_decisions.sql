-- F-DEC-001..005: decision cards + suppression key (RM-2)

CREATE TYPE public.decision_status AS ENUM (
    'open',
    'snoozed',
    'approved',
    'rejected'
);

CREATE TYPE public.decision_type AS ENUM (
    'INVENTORY_REORDER',
    'INVENTORY_DEAD_STOCK',
    'INVENTORY_CAPITAL_TRAP',
    'INVENTORY_BLOCKED'
);

CREATE TABLE public.decisions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    decision_type public.decision_type NOT NULL,
    sku_id text NOT NULL,
    event text NOT NULL,
    status public.decision_status NOT NULL DEFAULT 'open',
    suppression_key text NOT NULL,
    projection_hash text NOT NULL,
    inr_floor numeric NOT NULL DEFAULT 0,
    card jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT decisions_suppression_unique UNIQUE (tenant_id, suppression_key)
);

CREATE INDEX decisions_tenant_created_idx ON public.decisions (tenant_id, created_at DESC);
CREATE INDEX decisions_tenant_status_idx ON public.decisions (tenant_id, status);
CREATE INDEX decisions_tenant_type_idx ON public.decisions (tenant_id, decision_type);

ALTER TABLE public.decisions ENABLE ROW LEVEL SECURITY;

CREATE POLICY decisions_select_member ON public.decisions
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.memberships m
            WHERE m.tenant_id = decisions.tenant_id
              AND m.user_id = auth.uid()
        )
    );

-- Inserts via service_role / API server (JWT middleware); no authenticated INSERT in V0.0.1.

GRANT SELECT ON public.decisions TO authenticated;
