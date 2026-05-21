"use client";

import { useState } from "react";

import { createClient } from "@/lib/supabase/client";

export function LoginForm({ nextPath }: { nextPath: string }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const supabaseConfigured = Boolean(
    process.env.NEXT_PUBLIC_SUPABASE_URL &&
      (process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY)
  );

  async function exchangeSession(accessToken: string) {
    const res = await fetch("/api/auth/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ access_token: accessToken }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(
        (body as { error?: string }).error ?? `Session exchange failed (${res.status})`
      );
    }
    window.location.href = nextPath;
  }

  async function onSupabaseSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    const supabase = createClient();
    if (!supabase) {
      setMessage("Supabase env vars not configured.");
      setBusy(false);
      return;
    }
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error || !data.session) {
      setMessage(error?.message ?? "Sign-in failed");
      setBusy(false);
      return;
    }
    try {
      await exchangeSession(data.session.access_token);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Exchange failed");
      setBusy(false);
    }
  }

  async function onDevPilot() {
    setBusy(true);
    setMessage(null);
    const res = await fetch("/api/auth/dev-token", { method: "POST" });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      setMessage(
        (body as { error?: string }).error ?? "Dev sign-in failed — is API running?"
      );
      setBusy(false);
      return;
    }
    window.location.href = nextPath;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      {supabaseConfigured ? (
        <form onSubmit={onSupabaseSubmit}>
          <label style={{ display: "block", marginBottom: "0.35rem" }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
          />
          <label
            style={{ display: "block", marginTop: "0.75rem", marginBottom: "0.35rem" }}
          >
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={inputStyle}
          />
          <button type="submit" disabled={busy} style={{ ...buttonStyle, marginTop: "1rem" }}>
            {busy ? "Signing in…" : "Sign in with Supabase"}
          </button>
        </form>
      ) : (
        <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          Set <code>NEXT_PUBLIC_SUPABASE_URL</code> and publishable key in{" "}
          <code>trita/apps/web/.env.local</code> for email login.
        </p>
      )}

      <div style={{ borderTop: "1px solid var(--border)", paddingTop: "1rem" }}>
        <p style={{ margin: "0 0 0.75rem", fontSize: "0.9rem", color: "var(--muted)" }}>
          Local pilot (Yoga Bar): mints API JWT via <code>YOGA_BAR_TENANT_ID</code>
        </p>
        <button type="button" onClick={onDevPilot} disabled={busy} style={buttonStyle}>
          Continue as Yoga Bar (dev)
        </button>
      </div>

      {message ? <p style={{ color: "var(--failed)" }}>{message}</p> : null}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.6rem 0.75rem",
  borderRadius: 6,
  border: "1px solid var(--border)",
  background: "var(--surface)",
  color: "var(--text)",
};

const buttonStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.65rem 1rem",
  borderRadius: 6,
  border: "none",
  background: "var(--accent)",
  color: "#fff",
  fontWeight: 600,
  cursor: "pointer",
};
