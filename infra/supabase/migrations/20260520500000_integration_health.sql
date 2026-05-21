-- F-CONN-HEALTH: per-tenant connector health (T-P0-041 / VA-06)
-- API writes via service role; members read via RLS.

CREATE TYPE public.integration_status AS ENUM (
    'healthy',
    'degraded',
    'failed',
    'disconnected'
);

CREATE TABLE public.integration_health (
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL,
    status public.integration_status NOT NULL DEFAULT 'disconnected',
    last_sync_at timestamptz,
    freshness_sla_hours integer NOT NULL DEFAULT 24,
    detail jsonb,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT integration_health_pkey PRIMARY KEY (tenant_id, source)
);

CREATE INDEX integration_health_tenant_id_idx ON public.integration_health (tenant_id);

ALTER TABLE public.integration_health ENABLE ROW LEVEL SECURITY;

CREATE POLICY integration_health_select_member ON public.integration_health
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.memberships m
            WHERE m.tenant_id = integration_health.tenant_id
              AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON public.integration_health TO authenticated;
