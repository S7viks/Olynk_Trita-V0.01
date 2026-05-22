import Link from "next/link";
import type { CSSProperties } from "react";

import type { DecisionDetail, InboxListItem } from "@/lib/trita-api";

const TABS = [
  { key: "open", label: "Open" },
  { key: "snoozed", label: "Snoozed" },
  { key: "done", label: "Done" },
] as const;

function formatInr(n: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(n);
}

export function InboxTabs({ active }: { active: string }) {
  return (
    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
      {TABS.map((t) => (
        <Link
          key={t.key}
          href={`/inbox?tab=${t.key}`}
          style={{
            padding: "0.4rem 0.85rem",
            borderRadius: 6,
            border: `1px solid ${active === t.key ? "var(--accent)" : "var(--border)"}`,
            background: active === t.key ? "var(--surface)" : "transparent",
            color: active === t.key ? "var(--accent)" : "var(--text)",
            textDecoration: "none",
            fontSize: "0.9rem",
            fontWeight: active === t.key ? 600 : 400,
          }}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}

export function InboxList({
  items,
  selectedId,
  tab,
}: {
  items: InboxListItem[];
  selectedId: string | null;
  tab: string;
}) {
  if (items.length === 0) {
    return (
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        No cards in this tab. Run{" "}
        <code>POST /v1/decisions/emit</code> or{" "}
        <code>python scripts/emit_decisions.py</code> after metrics.
      </p>
    );
  }

  return (
    <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {items.map((item) => {
        const active = selectedId === item.id;
        return (
          <li key={item.id} style={{ marginBottom: "0.35rem" }}>
            <Link
              href={`/inbox?tab=${tab}&id=${item.id}`}
              style={{
                display: "block",
                padding: "0.75rem 1rem",
                borderRadius: 8,
                border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
                background: "var(--surface)",
                textDecoration: "none",
                color: "var(--text)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <strong>{item.sku_code ?? item.sku_id}</strong>
                <span style={{ color: "var(--degraded)", fontWeight: 600 }}>
                  {formatInr(item.inr_floor)}
                </span>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.25rem" }}>
                {item.type.replace("INVENTORY_", "")} · {item.preview || item.event}
              </div>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export function DecisionDetailPanel({
  decision,
  rejectReasons,
}: {
  decision: DecisionDetail;
  rejectReasons: string[];
}) {
  const card = decision.card;
  const impact = (card.impact as Record<string, unknown>) || {};
  const reasoning = (card.reasoning as Record<string, unknown>) || {};
  const recommendation = (card.recommendation as Record<string, unknown>) || {};
  const inaction = (card.inaction_model as Record<string, unknown>) || {};
  const canAct = decision.status === "open";

  return (
    <div
      style={{
        padding: "1rem 1.25rem",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
      }}
    >
      <h2 style={{ marginTop: 0, fontSize: "1.15rem" }}>
        {decision.sku_code ?? decision.sku_id}
      </h2>
      <p style={{ color: "var(--muted)", fontSize: "0.85rem", margin: "0 0 1rem" }}>
        {decision.type} · {decision.status} · {formatInr(decision.inr_floor)} at risk
      </p>

      <section style={{ marginBottom: "1rem" }}>
        <h3 style={{ fontSize: "0.95rem" }}>Impact</h3>
        <p style={{ margin: 0, fontSize: "0.9rem" }}>
          Floor {formatInr(Number(impact.inr_floor ?? 0))} · horizon{" "}
          {String(impact.horizon_days ?? "—")} days
        </p>
      </section>

      <section style={{ marginBottom: "1rem" }}>
        <h3 style={{ fontSize: "0.95rem" }}>Recommendation (Tier 1)</h3>
        <p style={{ margin: 0, fontSize: "0.9rem" }}>
          {String(recommendation.action_template ?? "—")}
          {recommendation.parameters
            ? ` — ${JSON.stringify(recommendation.parameters)}`
            : ""}
        </p>
      </section>

      <section style={{ marginBottom: "1rem" }}>
        <h3 style={{ fontSize: "0.95rem" }}>Evidence (L0)</h3>
        <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.85rem" }}>
          {((reasoning.evidence_refs as string[]) || []).map((ref) => (
            <li key={ref}>{ref}</li>
          ))}
        </ul>
      </section>

      {inaction.inr_at_risk_if_ignored != null ? (
        <section style={{ marginBottom: "1rem" }}>
          <h3 style={{ fontSize: "0.95rem" }}>If ignored</h3>
          <p style={{ margin: 0, fontSize: "0.9rem" }}>
            {formatInr(Number(inaction.inr_at_risk_if_ignored))}
            {inaction.days_to_stockout != null
              ? ` · ~${String(inaction.days_to_stockout)} days to stockout`
              : ""}
          </p>
        </section>
      ) : null}

      {canAct ? (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "0.5rem",
            marginBottom: "1rem",
          }}
        >
          <form action={`/api/decisions/${decision.id}/approve`} method="post">
            <button type="submit" style={btnPrimary}>
              Approve
            </button>
          </form>
          <form
            action={`/api/decisions/${decision.id}/snooze`}
            method="post"
            style={{ display: "inline" }}
          >
            <input type="hidden" name="days" value="7" />
            <button type="submit" style={btnSecondary}>
              Snooze 7d
            </button>
          </form>
        </div>
      ) : null}

      {canAct ? (
        <form
          action={`/api/decisions/${decision.id}/reject`}
          method="post"
          style={{ marginBottom: "1rem" }}
        >
          <h3 style={{ fontSize: "0.95rem" }}>Reject (reason required)</h3>
          <select
            name="reason_enum"
            required
            style={{
              width: "100%",
              padding: "0.5rem",
              marginBottom: "0.5rem",
              background: "var(--bg)",
              color: "var(--text)",
              border: "1px solid var(--border)",
              borderRadius: 6,
            }}
          >
            <option value="">Select reason…</option>
            {rejectReasons.map((r) => (
              <option key={r} value={r}>
                {r.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          <input
            name="reason_text"
            placeholder="Optional note"
            style={{
              width: "100%",
              padding: "0.5rem",
              marginBottom: "0.5rem",
              background: "var(--bg)",
              color: "var(--text)",
              border: "1px solid var(--border)",
              borderRadius: 6,
            }}
          />
          <button type="submit" style={btnDanger}>
            Reject
          </button>
        </form>
      ) : null}

      <section>
        <h3 style={{ fontSize: "0.95rem" }}>Timeline</h3>
        {decision.timeline.length === 0 ? (
          <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>No audit entries yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0, fontSize: "0.85rem" }}>
            {decision.timeline.map((e) => (
              <li
                key={e.id}
                style={{
                  padding: "0.5rem 0",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <strong>{e.action}</strong>
                {e.reason_enum ? ` · ${e.reason_enum}` : ""}
                <span style={{ display: "block", color: "var(--muted)" }}>
                  {e.timestamp ? new Date(e.timestamp).toLocaleString() : "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

const btnPrimary: CSSProperties = {
  padding: "0.45rem 0.9rem",
  background: "var(--healthy)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: "0.85rem",
};

const btnSecondary: CSSProperties = {
  padding: "0.45rem 0.9rem",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: "0.85rem",
};

const btnDanger: CSSProperties = {
  padding: "0.45rem 0.9rem",
  background: "var(--failed)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: "0.85rem",
};
