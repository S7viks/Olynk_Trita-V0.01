"use client";

import Link from "next/link";
import { useState } from "react";

import { AuthAlert } from "@/components/auth/auth-alert";
import { AuthDivider } from "@/components/auth/auth-divider";
import { AuthField } from "@/components/auth/auth-field";
import { AuthLayout } from "@/components/auth/auth-layout";
import { AuthUnavailable } from "@/components/auth/auth-unavailable";
import { GoogleButton } from "@/components/auth/google-button";
import { OrbitButton } from "@/components/orbit/button";
import { isSupabaseAuthConfigured } from "@/lib/auth/config";
import { startGoogleSignIn } from "@/lib/auth/oauth";
import {
  completeTritaSession,
  redirectAfterSession,
} from "@/lib/auth/session-client";
import { createClient } from "@/lib/supabase/client";

export function SignupPageClient() {
  const authReady = isSupabaseAuthConfigured();
  const [company, setCompany] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!authReady) {
    return <AuthUnavailable backHref="/login" />;
  }

  function onGoogle() {
    setBusy(true);
    setMessage(null);
    startGoogleSignIn("/onboarding");
  }

  async function establishFromSupabase(
    accessToken: string,
    userEmail: string
  ): Promise<void> {
    const { onboarding_complete } = await completeTritaSession({
      accessToken,
      email: userEmail,
      company_name: company.trim(),
    });
    redirectAfterSession(onboarding_complete);
  }

  async function onEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    const supabase = createClient();
    if (!supabase) {
      setMessage("Registration is temporarily unavailable.");
      setBusy(false);
      return;
    }
    if (!company.trim()) {
      setMessage("Enter your company or brand name.");
      setBusy(false);
      return;
    }

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { company_name: company.trim() },
      },
    });

    if (error) {
      setMessage(error.message);
      setBusy(false);
      return;
    }

    let accessToken = data.session?.access_token;

    // Confirm email off: Supabase usually returns a session. If not, sign in immediately.
    if (!accessToken && data.user) {
      const signIn = await supabase.auth.signInWithPassword({ email, password });
      if (signIn.error || !signIn.data.session) {
        setMessage(
          signIn.error?.message ??
            "Account may have been created. Try signing in from the login page."
        );
        setBusy(false);
        return;
      }
      accessToken = signIn.data.session.access_token;
    }

    if (!accessToken) {
      setMessage("Account created but no session was issued. Try signing in.");
      setBusy(false);
      return;
    }

    try {
      await establishFromSupabase(accessToken, email);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Could not start your workspace.");
      setBusy(false);
    }
  }

  return (
    <AuthLayout
      title="Create your workspace"
      subtitle="Sign up with Google or email. You go straight into onboarding — no confirmation email."
      footer={
        <p className="text-center text-[13px] text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-primary hover:underline">
            Sign in
          </Link>
        </p>
      }
    >
      <div className="space-y-5">
        <GoogleButton
          label="Sign up with Google"
          disabled={busy}
          onClick={onGoogle}
        />

        <AuthDivider label="or register with email" />

        <form onSubmit={onEmailSubmit} className="space-y-4">
          <AuthField
            label="Company name"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="e.g. Organik Truck"
            required
            autoComplete="organization"
            disabled={busy}
          />
          <AuthField
            label="Work email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            placeholder="you@brand.com"
            disabled={busy}
          />
          <AuthField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
            hint="At least 8 characters"
            disabled={busy}
          />
          <OrbitButton type="submit" fullWidth disabled={busy}>
            {busy ? "Setting up workspace…" : "Create account"}
          </OrbitButton>
        </form>

        {message ? <AuthAlert tone="error">{message}</AuthAlert> : null}
      </div>
    </AuthLayout>
  );
}
