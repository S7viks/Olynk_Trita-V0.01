"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AuthAlert } from "@/components/auth/auth-alert";
import { AuthDivider } from "@/components/auth/auth-divider";
import { AuthField } from "@/components/auth/auth-field";
import { AuthLayout } from "@/components/auth/auth-layout";
import { AuthUnavailable } from "@/components/auth/auth-unavailable";
import { GoogleButton } from "@/components/auth/google-button";
import { OrbitButton } from "@/components/orbit/button";
import { isDevLoginEnabled, isSupabaseAuthConfigured } from "@/lib/auth/config";
import { startGoogleSignIn } from "@/lib/auth/oauth";
import {
  completeTritaSession,
  redirectAfterSession,
} from "@/lib/auth/session-client";
import { createClient } from "@/lib/supabase/client";

export function LoginForm({ nextPath }: { nextPath: string }) {
  const authReady = isSupabaseAuthConfigured();
  const devLogin = isDevLoginEnabled();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!busy) return;
    const timer = window.setTimeout(() => {
      setBusy(false);
      setMessage(
        "Sign-in is taking too long. Ensure Trita API is running (.\\scripts\\start-api.ps1 -ReplacePort8000) and try again."
      );
    }, 30_000);
    return () => window.clearTimeout(timer);
  }, [busy]);

  async function onEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!authReady) return;
    setBusy(true);
    setMessage(null);
    const supabase = createClient();
    if (!supabase) {
      setMessage("Sign-in is temporarily unavailable. Please try again later.");
      setBusy(false);
      return;
    }
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error || !data.session) {
      setMessage(
        error?.message === "Invalid login credentials"
          ? "Email or password is incorrect."
          : (error?.message ?? "Sign-in failed. Please try again.")
      );
      setBusy(false);
      return;
    }
    try {
      const { onboarding_complete } = await completeTritaSession({
        accessToken: data.session.access_token,
        email,
      });
      redirectAfterSession(onboarding_complete, nextPath);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "We could not start your session.";
      setMessage(
        err instanceof DOMException && err.name === "TimeoutError"
          ? "Session request timed out. Start Trita API with .\\scripts\\start-api.ps1 -ReplacePort8000 from the repo root."
          : msg
      );
      setBusy(false);
    }
  }

  function onGoogle() {
    if (!authReady) return;
    setBusy(true);
    setMessage(null);
    startGoogleSignIn("/onboarding");
  }

  async function onDevPilot() {
    setBusy(true);
    setMessage(null);
    const res = await fetch("/api/auth/dev-token", { method: "POST" });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setMessage((body as { error?: string }).error ?? "Pilot sign-in failed.");
      setBusy(false);
      return;
    }
    window.location.href = nextPath;
  }

  return (
    <div className="space-y-5">
      <GoogleButton
        label="Continue with Google"
        disabled={busy || !authReady}
        onClick={onGoogle}
      />

      <AuthDivider label="or continue with email" />

      <form onSubmit={onEmailSubmit} className="space-y-4">
        <AuthField
          label="Work email"
          type="email"
          name="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          autoComplete="email"
          placeholder="you@brand.com"
          disabled={!authReady || busy}
        />
        <div>
          <AuthField
            label="Password"
            type="password"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            disabled={!authReady || busy}
          />
          <p className="mt-2 text-right">
            <Link
              href="/forgot-password"
              className="text-[12px] font-semibold text-primary hover:underline"
            >
              Forgot password?
            </Link>
          </p>
        </div>
        <OrbitButton type="submit" fullWidth disabled={busy || !authReady}>
          {busy ? "Signing in…" : "Sign in"}
        </OrbitButton>
      </form>

      {!authReady ? (
        <AuthAlert tone="info">
          Sign-in is not configured for this host. Set Supabase credentials on the deployment, then
          reload this page.
        </AuthAlert>
      ) : null}

      {message ? <AuthAlert tone="error">{message}</AuthAlert> : null}

      {devLogin ? (
        <details className="rounded-lg border border-dashed border-border/80 bg-muted/30 px-3 py-2">
          <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Internal pilot access
          </summary>
          <OrbitButton
            type="button"
            variant="ghost"
            fullWidth
            className="mt-2"
            onClick={onDevPilot}
            disabled={busy}
          >
            Continue as Yoga Bar (pilot)
          </OrbitButton>
        </details>
      ) : null}
    </div>
  );
}

export function LoginPageClient({
  nextPath,
  error,
}: {
  nextPath: string;
  error?: string;
}) {
  if (!isSupabaseAuthConfigured()) {
    return <AuthUnavailable />;
  }

  const oauthError =
    error === "oauth"
      ? "Google sign-in was cancelled or could not be completed. Try again or use email."
      : error
        ? decodeURIComponent(error)
        : undefined;

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your inventory workspace. New teams are set up automatically on first sign-in."
      footer={
        <p className="text-center text-[13px] text-muted-foreground">
          New to Trita?{" "}
          <Link href="/signup" className="font-semibold text-primary hover:underline">
            Create an account
          </Link>
        </p>
      }
    >
      {oauthError ? <AuthAlert tone="error">{oauthError}</AuthAlert> : null}
      <div className={oauthError ? "mt-4" : undefined}>
        <LoginForm nextPath={nextPath} />
      </div>
    </AuthLayout>
  );
}
