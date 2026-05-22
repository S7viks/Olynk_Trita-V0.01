-- Tenant fields for email/Google signup + onboarding gate (F-ONBOARD-001)

ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS owner_email text,
    ADD COLUMN IF NOT EXISTS onboarding_completed_at timestamptz;

CREATE INDEX IF NOT EXISTS tenants_owner_email_idx
    ON public.tenants (lower(owner_email))
    WHERE owner_email IS NOT NULL;
