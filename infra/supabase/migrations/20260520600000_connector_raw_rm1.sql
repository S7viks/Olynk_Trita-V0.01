-- RM-1: raw envelopes for Unicommerce, Shiprocket, Razorpay (F-CONN-002, 004, 006)

CREATE TABLE raw.unicommerce_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'unicommerce',
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT unicommerce_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX unicommerce_events_tenant_ingested_idx
    ON raw.unicommerce_events (tenant_id, ingested_at DESC);

CREATE TABLE raw.shiprocket_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'shiprocket',
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT shiprocket_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX shiprocket_events_tenant_ingested_idx
    ON raw.shiprocket_events (tenant_id, ingested_at DESC);

CREATE TABLE raw.razorpay_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'razorpay',
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT razorpay_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX razorpay_events_tenant_ingested_idx
    ON raw.razorpay_events (tenant_id, ingested_at DESC);

ALTER TABLE raw.unicommerce_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw.shiprocket_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw.razorpay_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY unicommerce_events_select_member ON raw.unicommerce_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = unicommerce_events.tenant_id AND m.user_id = auth.uid()
        )
    );

CREATE POLICY shiprocket_events_select_member ON raw.shiprocket_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = shiprocket_events.tenant_id AND m.user_id = auth.uid()
        )
    );

CREATE POLICY razorpay_events_select_member ON raw.razorpay_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = razorpay_events.tenant_id AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON raw.unicommerce_events TO authenticated;
GRANT SELECT ON raw.shiprocket_events TO authenticated;
GRANT SELECT ON raw.razorpay_events TO authenticated;

ALTER TABLE public.connector_credentials
    ALTER COLUMN shop_domain DROP NOT NULL;
