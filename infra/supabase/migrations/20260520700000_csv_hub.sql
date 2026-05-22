-- F-CONN-005: CSV hub raw envelope, quarantine, upload metadata

CREATE TYPE public.csv_upload_status AS ENUM ('processing', 'completed', 'failed');

CREATE TABLE public.csv_upload (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    file_hash text NOT NULL,
    file_name text,
    logical_source text NOT NULL,
    entity_type text,
    template_id text,
    mapping_profile jsonb,
    status public.csv_upload_status NOT NULL DEFAULT 'processing',
    row_count integer NOT NULL DEFAULT 0,
    valid_count integer NOT NULL DEFAULT 0,
    quarantine_count integer NOT NULL DEFAULT 0,
    inserted_count integer NOT NULL DEFAULT 0,
    skipped_count integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT csv_upload_tenant_hash UNIQUE (tenant_id, file_hash)
);

CREATE INDEX csv_upload_tenant_created_idx
    ON public.csv_upload (tenant_id, created_at DESC);

CREATE TABLE raw.csv_hub_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL,
    external_id text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    payload_hash text NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    lineage jsonb,
    CONSTRAINT csv_hub_events_dedup UNIQUE (tenant_id, source, external_id, entity_type)
);

CREATE INDEX csv_hub_events_tenant_ingested_idx
    ON raw.csv_hub_events (tenant_id, ingested_at DESC);

CREATE TABLE quarantine.csv_hub (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    upload_id uuid NOT NULL REFERENCES public.csv_upload (id) ON DELETE CASCADE,
    source text NOT NULL,
    entity_type text,
    row_number integer NOT NULL,
    error_code text NOT NULL,
    raw_snippet jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX csv_hub_quarantine_tenant_upload_idx
    ON quarantine.csv_hub (tenant_id, upload_id);

ALTER TABLE public.csv_upload ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw.csv_hub_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE quarantine.csv_hub ENABLE ROW LEVEL SECURITY;

CREATE POLICY csv_upload_select_member ON public.csv_upload
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = csv_upload.tenant_id AND m.user_id = auth.uid()
        )
    );

CREATE POLICY csv_hub_events_select_member ON raw.csv_hub_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = csv_hub_events.tenant_id AND m.user_id = auth.uid()
        )
    );

CREATE POLICY csv_hub_quarantine_select_member ON quarantine.csv_hub
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = csv_hub.tenant_id AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON public.csv_upload TO authenticated;
GRANT SELECT ON raw.csv_hub_events TO authenticated;
GRANT SELECT ON quarantine.csv_hub TO authenticated;
