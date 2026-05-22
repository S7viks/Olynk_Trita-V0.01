-- F-ID-001 / F-ID-002: SKU aliases + order payment/shipment bridge

CREATE TABLE public.sku_alias (
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL,
    external_id text NOT NULL,
    canonical_sku_id text NOT NULL,
    confidence numeric(5, 4) NOT NULL DEFAULT 1.0000
        CHECK (confidence >= 0 AND confidence <= 1),
    merged_by text NOT NULL DEFAULT 'auto',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, source, external_id)
);

CREATE INDEX sku_alias_tenant_canonical_idx
    ON public.sku_alias (tenant_id, canonical_sku_id);

CREATE TABLE public.order_bridge (
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    channel_order_key text NOT NULL,
    shopify_order_id text,
    shopify_order_name text,
    shipment_id text,
    payment_id text,
    settlement_id text,
    has_shipment boolean NOT NULL DEFAULT false,
    has_payment boolean NOT NULL DEFAULT false,
    updated_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, channel_order_key)
);

ALTER TABLE public.sku_alias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.order_bridge ENABLE ROW LEVEL SECURITY;

CREATE POLICY sku_alias_select_member ON public.sku_alias
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = sku_alias.tenant_id AND m.user_id = auth.uid()
        )
    );

CREATE POLICY order_bridge_select_member ON public.order_bridge
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.memberships m
            WHERE m.tenant_id = order_bridge.tenant_id AND m.user_id = auth.uid()
        )
    );

GRANT SELECT ON public.sku_alias TO authenticated;
GRANT SELECT ON public.order_bridge TO authenticated;
