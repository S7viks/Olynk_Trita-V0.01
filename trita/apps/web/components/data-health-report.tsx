import Link from "next/link";

import type { DataHealthReport } from "@/lib/trita-api";

const STATUS_COLOR: Record<string, string> = {
  healthy: "var(--healthy)",
  degraded: "var(--degraded)",
  failed: "var(--failed)",
  disconnected: "var(--disconnected)",
};

function formatInr(value: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

export function DataHealthReportView({ report }: { report: DataHealthReport }) {
  const m = report.metrics;
  const id = report.identity;
  const s = report.summary;

  return (
    <div>
      <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
        As of {new Date(report.generated_at).toLocaleString()} · tenant{" "}
        {report.tenant_id}
        {m.metric_date ? ` · metrics ${m.metric_date}` : null}
      </p>

      <section style={{ marginTop: "1.25rem" }}>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>Graph alignment</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(10rem, 1fr))",
            gap: "0.75rem",
          }}
        >
          <MetricCard
            label="SKUs in mart"
            value={String(m.sku_count)}
            ok={m.aligned}
            hint={m.aligned ? "Matches gold.dim_sku" : `${m.dim_sku_count} in dim_sku`}
          />
          <MetricCard
            label="Order line resolution"
            value={`${Math.round((id.resolution.resolution_rate ?? 0) * 100)}%`}
            ok={id.resolution.meets_va13}
            hint={`${id.resolution.resolved_lines}/${id.resolution.total_lines} lines`}
          />
          <MetricCard
            label="Stockout risk"
            value={String(m.stockout_risk_count)}
            ok={m.stockout_risk_count === 0}
          />
          <MetricCard
            label="Dead stock"
            value={String(m.dead_stock_count)}
          />
          <MetricCard
            label="Missing COGS"
            value={String(m.cogs_missing_count)}
          />
          <MetricCard
            label="Capital at risk"
            value={formatInr(m.capital_at_risk_total)}
          />
        </div>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.75rem" }}>
          Connectors ({s.connectors_unhealthy} need attention)
        </h2>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            background: "var(--surface)",
            borderRadius: 8,
            overflow: "hidden",
          }}
        >
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
              <th style={{ padding: "0.75rem 1rem" }}>Source</th>
              <th style={{ padding: "0.75rem 1rem" }}>Status</th>
              <th style={{ padding: "0.75rem 1rem" }}>Last sync</th>
              <th style={{ padding: "0.75rem 1rem" }}>Detail</th>
            </tr>
          </thead>
          <tbody>
            {report.integrations.map((row) => (
              <tr key={row.source} style={{ borderBottom: "1px solid var(--border)" }}>
                <td style={{ padding: "0.75rem 1rem", fontWeight: 600 }}>
                  {row.display_name ?? row.source}
                  {row.mode === "csv_hub" ? (
                    <span
                      style={{
                        marginLeft: "0.5rem",
                        fontSize: "0.75rem",
                        color: "var(--muted)",
                      }}
                    >
                      CSV
                    </span>
                  ) : null}
                </td>
                <td style={{ padding: "0.75rem 1rem" }}>
                  <span
                    style={{
                      color: STATUS_COLOR[row.status] ?? "var(--text)",
                      fontWeight: 600,
                    }}
                  >
                    {row.status}
                  </span>
                </td>
                <td style={{ padding: "0.75rem 1rem", color: "var(--muted)" }}>
                  {row.last_sync_at
                    ? new Date(row.last_sync_at).toLocaleString()
                    : "—"}
                </td>
                <td style={{ padding: "0.75rem 1rem", fontSize: "0.85rem" }}>
                  {row.detail?.message ? String(row.detail.message) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={{ marginTop: "0.75rem", fontSize: "0.9rem" }}>
          <Link href="/sources">Manage sources →</Link>
        </p>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>Identity bridge</h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", margin: 0 }}>
          {id.alias_count} SKU aliases · {id.bridge.order_keys} order keys ·{" "}
          {id.bridge.with_both} with shipment + payment (
          {Math.round(id.bridge.full_bridge_rate * 100)}% full bridge)
        </p>
      </section>
    </div>
  );
}

function MetricCard({
  label,
  value,
  ok,
  hint,
}: {
  label: string;
  value: string;
  ok?: boolean;
  hint?: string;
}) {
  const border =
    ok === true
      ? "var(--healthy)"
      : ok === false
        ? "var(--degraded)"
        : "var(--border)";
  return (
    <div
      style={{
        padding: "0.75rem 1rem",
        background: "var(--surface)",
        border: `1px solid ${border}`,
        borderRadius: 8,
      }}
    >
      <div style={{ fontSize: "0.8rem", color: "var(--muted)" }}>{label}</div>
      <div style={{ fontSize: "1.25rem", fontWeight: 600, marginTop: "0.25rem" }}>
        {value}
      </div>
      {hint ? (
        <div style={{ fontSize: "0.75rem", color: "var(--muted)", marginTop: "0.25rem" }}>
          {hint}
        </div>
      ) : null}
    </div>
  );
}
