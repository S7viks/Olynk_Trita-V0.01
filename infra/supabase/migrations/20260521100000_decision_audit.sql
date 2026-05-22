-- F-DEC-005: immutable decision audit + snooze support

ALTER TABLE public.decisions
    ADD COLUMN IF NOT EXISTS snoozed_until timestamptz;

CREATE TYPE public.decision_audit_action AS ENUM (
    'emitted',
    'viewed',
    'approved',
    'rejected',
    'snoozed',
    'draft_created'
);

CREATE TYPE public.decision_reject_reason AS ENUM (
    'wrong_qty',
    'wrong_sku_mapping',
    'already_ordered',
    'supplier_issue',
    'promo_planned',
    'data_stale',
    'not_actionable',
    'other'
);

CREATE TABLE public.decision_audit (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    decision_id uuid NOT NULL REFERENCES public.decisions (id) ON DELETE CASCADE,
    user_id uuid NOT NULL,
    action public.decision_audit_action NOT NULL,
    reason_enum public.decision_reject_reason,
    reason_text text,
    projection_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX decision_audit_decision_id_idx ON public.decision_audit (decision_id, created_at);
CREATE INDEX decision_audit_tenant_id_idx ON public.decision_audit (tenant_id);

ALTER TABLE public.decision_audit ENABLE ROW LEVEL SECURITY;

CREATE POLICY decision_audit_select_member ON public.decision_audit
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1
            FROM public.memberships m
            WHERE m.tenant_id = decision_audit.tenant_id
              AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON public.decision_audit TO authenticated;
