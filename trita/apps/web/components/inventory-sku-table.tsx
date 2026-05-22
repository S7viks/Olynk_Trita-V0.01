import Link from "next/link";

import type { SkuMetricRow } from "@/lib/trita-api";

const SORT_OPTIONS: { key: string; label: string }[] = [
  { key: "days_of_cover", label: "Cover" },
  { key: "aging_days", label: "Aging" },
  { key: "capital_at_risk", label: "₹ at risk" },
  { key: "velocity_7d", label: "Velocity" },
  { key: "sku_code", label: "SKU" },
];

function formatNum(n: number | null, digits = 1): string {
  if (n == null) return "—";
  return Number.isInteger(n) ? String(n) : n.toFixed(digits);
}

function buildHref(
  base: Record<string, string | undefined>,
  patch: Record<string, string | undefined>
): string {
  const params = new URLSearchParams();
  const merged = { ...base, ...patch };
  for (const [k, v] of Object.entries(merged)) {
    if (v) params.set(k, v);
  }
  const qs = params.toString();
  return `/inventory${qs ? `?${qs}` : ""}`;
}

export function InventorySkuTable({
  items,
  metricDate,
  searchParams,
}: {
  items: SkuMetricRow[];
  metricDate: string | null;
  searchParams: {
    sort?: string;
    order?: string;
    stockout_only?: string;
    dead_stock_only?: string;
  };
}) {
  const sort = searchParams.sort ?? "days_of_cover";
  const order = searchParams.order ?? "asc";
  const stockoutOnly = searchParams.stockout_only === "1";
  const deadOnly = searchParams.dead_stock_only === "1";
  const base = {
    sort,
    order,
    stockout_only: stockoutOnly ? "1" : undefined,
    dead_stock_only: deadOnly ? "1" : undefined,
  };

  return (
    <div>
      {metricDate ? (
        <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
          Latest metric date: {metricDate} · {items.length} SKUs
        </p>
      ) : null}

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem",
          margin: "1rem 0",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>Sort:</span>
        {SORT_OPTIONS.map((opt) => {
          const nextOrder =
            sort === opt.key && order === "asc" ? "desc" : "asc";
          const active = sort === opt.key;
          return (
            <Link
              key={opt.key}
              href={buildHref(base, { sort: opt.key, order: nextOrder })}
              style={{
                padding: "0.25rem 0.6rem",
                borderRadius: 6,
                border: `1px solid ${active ? "var(--accent)" : "var(--border)"}`,
                fontSize: "0.85rem",
                textDecoration: "none",
                color: active ? "var(--accent)" : "var(--text)",
              }}
            >
              {opt.label}
              {active ? (order === "asc" ? " ↑" : " ↓") : ""}
            </Link>
          );
        })}
        <span style={{ margin: "0 0.25rem", color: "var(--border)" }}>|</span>
        <Link
          href={buildHref(base, {
            stockout_only: stockoutOnly ? undefined : "1",
          })}
          style={{
            padding: "0.25rem 0.6rem",
            borderRadius: 6,
            border: `1px solid ${stockoutOnly ? "var(--failed)" : "var(--border)"}`,
            fontSize: "0.85rem",
            textDecoration: "none",
          }}
        >
          Stockout risk only
        </Link>
        <Link
          href={buildHref(base, {
            dead_stock_only: deadOnly ? undefined : "1",
          })}
          style={{
            padding: "0.25rem 0.6rem",
            borderRadius: 6,
            border: `1px solid ${deadOnly ? "var(--degraded)" : "var(--border)"}`,
            fontSize: "0.85rem",
            textDecoration: "none",
          }}
        >
          Dead stock only
        </Link>
        {(stockoutOnly || deadOnly) && (
          <Link href="/inventory" style={{ fontSize: "0.85rem" }}>
            Clear filters
          </Link>
        )}
      </div>

      {items.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>
          No SKUs match filters. Run dbt metrics after ingest (
          <code>scripts/run_dbt.py run --select sku_metrics_daily</code>).
        </p>
      ) : (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            background: "var(--surface)",
            borderRadius: 8,
            overflow: "hidden",
            fontSize: "0.9rem",
          }}
        >
          <thead>
            <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
              <th style={{ padding: "0.65rem 0.75rem" }}>SKU</th>
              <th style={{ padding: "0.65rem 0.75rem" }}>On hand</th>
              <th style={{ padding: "0.65rem 0.75rem" }}>Vel 7d</th>
              <th style={{ padding: "0.65rem 0.75rem" }}>Cover (d)</th>
              <th style={{ padding: "0.65rem 0.75rem" }}>Aging</th>
              <th style={{ padding: "0.65rem 0.75rem" }}>₹ risk</th>
              <th style={{ padding: "0.65rem 0.75rem" }}>Flags</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr
                key={row.canonical_sku_id}
                style={{ borderBottom: "1px solid var(--border)" }}
              >
                <td style={{ padding: "0.65rem 0.75rem", fontWeight: 600 }}>
                  {row.sku_code}
                </td>
                <td style={{ padding: "0.65rem 0.75rem" }}>
                  {formatNum(row.on_hand, 0)}
                </td>
                <td style={{ padding: "0.65rem 0.75rem" }}>
                  {formatNum(row.velocity_7d)}
                </td>
                <td style={{ padding: "0.65rem 0.75rem" }}>
                  {formatNum(row.days_of_cover)}
                </td>
                <td style={{ padding: "0.65rem 0.75rem" }}>
                  {row.aging_days != null ? `${row.aging_days}d` : "—"}
                </td>
                <td style={{ padding: "0.65rem 0.75rem" }}>
                  {row.capital_at_risk != null
                    ? `₹${Math.round(row.capital_at_risk).toLocaleString("en-IN")}`
                    : "—"}
                </td>
                <td style={{ padding: "0.65rem 0.75rem", fontSize: "0.8rem" }}>
                  {row.stockout_risk ? (
                    <span style={{ color: "var(--failed)" }}>stockout </span>
                  ) : null}
                  {row.dead_stock ? (
                    <span style={{ color: "var(--degraded)" }}>dead </span>
                  ) : null}
                  {row.cogs_missing ? (
                    <span style={{ color: "var(--muted)" }}>no COGS</span>
                  ) : null}
                  {!row.stockout_risk && !row.dead_stock && !row.cogs_missing
                    ? "—"
                    : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p style={{ marginTop: "1rem", fontSize: "0.9rem" }}>
        <Link href="/reports/health">Data Health report →</Link>
      </p>
    </div>
  );
}
