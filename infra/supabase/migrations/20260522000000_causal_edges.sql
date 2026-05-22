-- F-CAUSAL-001..003: causal edges (association + DoWhy promotion)

CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TYPE analytics.causal_evidence_type AS ENUM (
    'association',
    'causal_candidate',
    'causal_verified'
);

CREATE TYPE analytics.causal_refutation_status AS ENUM (
    'pending',
    'pass',
    'fail'
);

CREATE TABLE analytics.causal_edges (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    sku_id text NOT NULL,
    cause_variable text NOT NULL,
    effect_variable text NOT NULL,
    evidence_type analytics.causal_evidence_type NOT NULL,
    epistemic_layer text NOT NULL CHECK (epistemic_layer IN ('L1', 'L2', 'L3')),
    lag_days integer NOT NULL DEFAULT 0,
    correlation numeric,
    confidence numeric,
    refutation_status analytics.causal_refutation_status NOT NULL DEFAULT 'pending',
    refutation_details jsonb NOT NULL DEFAULT '{}'::jsonb,
    n_weeks integer NOT NULL DEFAULT 0,
    completeness numeric NOT NULL DEFAULT 0,
    narrative text,
    promoted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT causal_edges_refutation_l3 CHECK (
        epistemic_layer <> 'L3'
        OR (
            evidence_type = 'causal_verified'
            AND refutation_status = 'pass'
            AND refutation_details <> '{}'::jsonb
        )
    )
);

CREATE INDEX causal_edges_tenant_sku_idx
    ON analytics.causal_edges (tenant_id, sku_id, epistemic_layer DESC);

CREATE INDEX causal_edges_tenant_promoted_idx
    ON analytics.causal_edges (tenant_id, promoted_at DESC NULLS LAST);

CREATE UNIQUE INDEX causal_edges_dedup_uidx
    ON analytics.causal_edges (tenant_id, sku_id, cause_variable, effect_variable, lag_days);

ALTER TABLE analytics.causal_edges ENABLE ROW LEVEL SECURITY;

CREATE POLICY causal_edges_select_member ON analytics.causal_edges
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.memberships m
            WHERE m.tenant_id = causal_edges.tenant_id
              AND m.user_id = auth.uid()
        )
    );

GRANT USAGE ON SCHEMA analytics TO authenticated;
GRANT SELECT ON analytics.causal_edges TO authenticated;
