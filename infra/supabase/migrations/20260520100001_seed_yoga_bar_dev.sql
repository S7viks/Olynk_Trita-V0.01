-- Dev/staging seed: pilot tenant Yoga Bar (no auth.users — run after pilot users exist).
-- Safe to re-run: slug is unique.

INSERT INTO public.tenants (slug, display_name)
VALUES ('yoga-bar', 'Yoga Bar')
ON CONFLICT (slug) DO NOTHING;
