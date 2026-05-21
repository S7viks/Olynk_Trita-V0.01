-- Shopify OAuth credentials per tenant (server-only; never exposed to browser)

CREATE TABLE public.connector_credentials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES public.tenants (id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'shopify',
    shop_domain text NOT NULL,
    access_token_encrypted text NOT NULL,
    scopes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT connector_credentials_tenant_source_unique UNIQUE (tenant_id, source)
);

CREATE INDEX connector_credentials_tenant_idx ON public.connector_credentials (tenant_id);

ALTER TABLE public.connector_credentials ENABLE ROW LEVEL SECURITY;

-- No policies for authenticated: tokens readable only via API service role / direct DB with app filter.
