-- F-PROACTIVE-001..004: proactive feed + digest delivery log

CREATE TYPE public.proactive_severity AS ENUM ('info', 'highlight', 'urgent', 'alert');

CREATE TABLE public.proactive_feed_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    trigger_id text NOT NULL,
    severity public.proactive_severity NOT NULL DEFAULT 'info',
    title text NOT NULL,
    body text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    dedup_key text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT proactive_feed_dedup UNIQUE (tenant_id, trigger_id, dedup_key)
);

CREATE INDEX proactive_feed_tenant_created_idx
    ON public.proactive_feed_events (tenant_id, created_at DESC);

CREATE TYPE public.digest_channel AS ENUM ('email', 'slack');

CREATE TYPE public.digest_kind AS ENUM ('weekly', 'urgent');

CREATE TABLE public.digest_deliveries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    channel public.digest_channel NOT NULL,
    digest_kind public.digest_kind NOT NULL,
    subject text NOT NULL,
    body text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    delivery_day date NOT NULL DEFAULT (current_date),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX digest_deliveries_tenant_day_idx
    ON public.digest_deliveries (tenant_id, digest_kind, delivery_day DESC);

CREATE TABLE public.notification_settings (
    tenant_id uuid PRIMARY KEY REFERENCES public.tenants (id) ON DELETE CASCADE,
    weekly_digest_enabled boolean NOT NULL DEFAULT true,
    urgent_enabled boolean NOT NULL DEFAULT true,
    email_to text,
    slack_webhook_url text,
    updated_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.proactive_feed_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.digest_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY proactive_feed_select_member ON public.proactive_feed_events
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = proactive_feed_events.tenant_id
              AND m.user_id = auth.uid()
        )
    );

CREATE POLICY digest_deliveries_select_member ON public.digest_deliveries
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = digest_deliveries.tenant_id
              AND m.user_id = auth.uid()
        )
    );

CREATE POLICY notification_settings_select_member ON public.notification_settings
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = notification_settings.tenant_id
              AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON public.proactive_feed_events TO authenticated;
GRANT SELECT ON public.digest_deliveries TO authenticated;
GRANT SELECT ON public.notification_settings TO authenticated;
