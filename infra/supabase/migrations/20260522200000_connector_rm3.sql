-- F-CONN-007..009: Delhivery, Meta Ads, Google Ads raw envelopes

CREATE TABLE raw.delhivery_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'delhivery',
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT delhivery_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX delhivery_events_tenant_ingested_idx
    ON raw.delhivery_events (tenant_id, ingested_at DESC);

CREATE TABLE raw.meta_ads_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'meta_ads',
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT meta_ads_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX meta_ads_events_tenant_ingested_idx
    ON raw.meta_ads_events (tenant_id, ingested_at DESC);

CREATE TABLE raw.google_ads_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'google_ads',
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT google_ads_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX google_ads_events_tenant_ingested_idx
    ON raw.google_ads_events (tenant_id, ingested_at DESC);

ALTER TABLE raw.delhivery_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw.meta_ads_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw.google_ads_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY delhivery_events_select_member ON raw.delhivery_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = delhivery_events.tenant_id AND m.user_id = auth.uid()
        )
    );

CREATE POLICY meta_ads_events_select_member ON raw.meta_ads_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = meta_ads_events.tenant_id AND m.user_id = auth.uid()
        )
    );

CREATE POLICY google_ads_events_select_member ON raw.google_ads_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = google_ads_events.tenant_id AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON raw.delhivery_events TO authenticated;
GRANT SELECT ON raw.meta_ads_events TO authenticated;
GRANT SELECT ON raw.google_ads_events TO authenticated;
