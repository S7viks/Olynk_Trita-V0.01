"use client";

import { useState } from "react";

import type { NotificationSettings, TenantContext } from "@/lib/trita-api";

export function SettingsForm({
  tenant,
  initial,
}: {
  tenant: TenantContext;
  initial: NotificationSettings;
}) {
  const [emailTo, setEmailTo] = useState(initial.email_to ?? "");
  const [weekly, setWeekly] = useState(initial.weekly_digest_enabled);
  const [urgent, setUrgent] = useState(initial.urgent_enabled);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [ok, setOk] = useState(false);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMessage(null);
    setOk(false);
    try {
      const res = await fetch("/api/settings/notifications", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email_to: emailTo.trim() || null,
          weekly_digest_enabled: weekly,
          urgent_enabled: urgent,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error((body as { error?: string }).error ?? "Save failed");
      }
      setOk(true);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <div className="ui-card">
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1.1rem" }}>Tenant</h2>
        <dl style={{ margin: 0, fontSize: "0.9rem" }}>
          <dt style={{ color: "var(--muted)" }}>Tenant ID</dt>
          <dd style={{ margin: "0.15rem 0 0.75rem" }}>
            <code>{tenant.tenant_id}</code>
          </dd>
          <dt style={{ color: "var(--muted)" }}>Role</dt>
          <dd style={{ margin: "0.15rem 0 0" }}>{tenant.role}</dd>
        </dl>
      </div>

      <form className="ui-card" onSubmit={onSave}>
        <h2 style={{ margin: "0 0 0.75rem", fontSize: "1.1rem" }}>Notifications</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", margin: "0 0 1rem" }}>
          Weekly digest and urgent alerts (F-PROACTIVE-003/004). Delivery logs in{" "}
          <code>digest_deliveries</code>.
        </p>
        <label className="ui-label" htmlFor="email-to">
          Digest email
        </label>
        <input
          id="email-to"
          className="ui-input"
          type="email"
          value={emailTo}
          onChange={(e) => setEmailTo(e.target.value)}
          placeholder="ops@yourbrand.com"
        />
        <label style={{ display: "flex", gap: "0.5rem", marginTop: "1rem", alignItems: "center" }}>
          <input
            type="checkbox"
            checked={weekly}
            onChange={(e) => setWeekly(e.target.checked)}
          />
          <span>Weekly inventory digest</span>
        </label>
        <label style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", alignItems: "center" }}>
          <input
            type="checkbox"
            checked={urgent}
            onChange={(e) => setUrgent(e.target.checked)}
          />
          <span>Urgent alerts (capped)</span>
        </label>
        <button
          type="submit"
          className="ui-btn ui-btn-primary"
          disabled={busy}
          style={{ marginTop: "1.25rem" }}
        >
          {busy ? "Saving…" : "Save notifications"}
        </button>
        {ok ? <p className="ui-alert ui-alert-success" style={{ marginTop: "0.75rem" }}>Saved.</p> : null}
        {message ? <p className="ui-alert ui-alert-error" style={{ marginTop: "0.75rem" }}>{message}</p> : null}
      </form>

      <div className="ui-card">
        <h2 style={{ margin: "0 0 0.5rem", fontSize: "1.1rem" }}>Lead times</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", margin: 0 }}>
          Default <code>lead_time_days</code> is set in dbt (<code>14</code>). Per-SKU overrides
          ship in a later settings release (F-SETTINGS-001).
        </p>
      </div>
    </div>
  );
}
