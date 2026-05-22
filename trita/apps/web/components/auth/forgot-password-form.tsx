"use client";

import Link from "next/link";
import { useState } from "react";

import { AuthAlert } from "@/components/auth/auth-alert";
import { AuthField } from "@/components/auth/auth-field";
import { AuthLayout } from "@/components/auth/auth-layout";
import { AuthUnavailable } from "@/components/auth/auth-unavailable";
import { OrbitButton } from "@/components/orbit/button";
import { isSupabaseAuthConfigured } from "@/lib/auth/config";
import { createClient } from "@/lib/supabase/client";

export function ForgotPasswordPageClient() {
  const authReady = isSupabaseAuthConfigured();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  if (!authReady) {
    return <AuthUnavailable backHref="/login" />;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const supabase = createClient();
    if (!supabase) {
      setMessage("Password reset is temporarily unavailable.");
      return;
    }
    setBusy(true);
    setMessage(null);
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/login`,
    });
    setBusy(false);
    if (error) {
      setMessage(error.message);
      return;
    }
    setSent(true);
  }

  if (sent) {
    return (
      <AuthLayout
        title="Check your email"
        subtitle="If an account exists for that address, you will receive a reset link shortly."
        showLegal={false}
        footer={
          <p className="text-center text-[13px]">
            <Link href="/login" className="font-semibold text-primary hover:underline">
              Back to sign in
            </Link>
          </p>
        }
      >
        <AuthAlert tone="success">
          When the link arrives, open it to choose a new password, then sign in to Trita.
        </AuthAlert>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Reset password"
      subtitle="Enter the work email on your account. We will send a secure link to set a new password."
      footer={
        <p className="text-center text-[13px]">
          <Link href="/login" className="font-semibold text-primary hover:underline">
            Back to sign in
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
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
        <OrbitButton type="submit" fullWidth disabled={busy}>
          {busy ? "Sending…" : "Send reset link"}
        </OrbitButton>
        {message ? <AuthAlert tone="error">{message}</AuthAlert> : null}
      </form>
    </AuthLayout>
  );
}
