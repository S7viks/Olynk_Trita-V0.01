-- T-P0-010 / F-INGEST-SHOPIFY: raw envelope for Shopify (P-INGEST-SHOPIFY)

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE raw.shopify_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'shopify',
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT shopify_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX shopify_events_tenant_ingested_idx
    ON raw.shopify_events (tenant_id, ingested_at DESC);

ALTER TABLE raw.shopify_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY shopify_events_select_member ON raw.shopify_events
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.memberships m
            WHERE m.tenant_id = shopify_events.tenant_id
              AND m.user_id = auth.uid()
        )
    );

-- Ingest uses service_role with explicit tenant_id filter (T-P0-003 audit scope).
GRANT SELECT ON raw.shopify_events TO authenticated;
