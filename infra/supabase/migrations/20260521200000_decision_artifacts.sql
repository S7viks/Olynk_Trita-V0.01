-- F-DRAFT-001, F-DRAFT-002: Tier-2 PO + supplier email artifacts (no external write)

CREATE TYPE public.decision_artifact_type AS ENUM (
    'po_draft',
    'supplier_email'
);

CREATE TABLE public.decision_artifacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    decision_id uuid NOT NULL REFERENCES public.decisions (id) ON DELETE CASCADE,
    artifact_type public.decision_artifact_type NOT NULL,
    payload jsonb NOT NULL,
    source text NOT NULL DEFAULT 'template',
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT decision_artifacts_payload_object CHECK (jsonb_typeof(payload) = 'object')
);

CREATE UNIQUE INDEX decision_artifacts_decision_type_uidx
    ON public.decision_artifacts (decision_id, artifact_type);

CREATE INDEX decision_artifacts_tenant_decision_idx
    ON public.decision_artifacts (tenant_id, decision_id);

ALTER TABLE public.decision_artifacts ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_artifacts_select_member ON public.decision_artifacts
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.memberships m
            WHERE m.tenant_id = decision_artifacts.tenant_id
              AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON public.decision_artifacts TO authenticated;
