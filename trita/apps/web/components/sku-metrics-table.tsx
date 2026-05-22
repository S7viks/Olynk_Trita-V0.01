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

function formatInr(n: number | null): string {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(n);
}

function buildHref(
  basePath: string,
  base: Record<string, string | undefined>,
  patch: Record<string, string | undefined>
): string {
  const params = new URLSearchParams();
  const merged = { ...base, ...patch };
  for (const [k, v] of Object.entries(merged)) {
    if (v) params.set(k, v);
  }
  const qs = params.toString();
  return `${basePath}${qs ? `?${qs}` : ""}`;
}

export function SkuMetricsTable({
  items,
  metricDate,
  searchParams,
  basePath,
  showReorderQty = false,
}: {
  items: SkuMetricRow[];
  metricDate: string | null;
  searchParams: {
    sort?: string;
    order?: string;
    stockout_only?: string;
    dead_stock_only?: string;
  };
  basePath: string;
  showReorderQty?: boolean;
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
          const nextOrder = sort === opt.key && order === "asc" ? "desc" : "asc";
          const active = sort === opt.key;
          return (
            <Link
              key={opt.key}
              href={buildHref(basePath, base, { sort: opt.key, order: nextOrder })}
              className={`ui-btn ui-btn-secondary`}
              style={{
                padding: "0.35rem 0.65rem",
                fontSize: "0.8rem",
                fontWeight: active ? 600 : 400,
                borderColor: active ? "var(--accent)" : undefined,
              }}
            >
              {opt.label}
              {active ? ` ${order === "asc" ? "↑" : "↓"}` : ""}
            </Link>
          );
        })}
        <Link
          href={buildHref(basePath, base, {
            stockout_only: stockoutOnly ? undefined : "1",
          })}
          className="ui-btn ui-btn-secondary"
          style={{
            padding: "0.35rem 0.65rem",
            fontSize: "0.8rem",
            marginLeft: "0.5rem",
            borderColor: stockoutOnly ? "var(--accent)" : undefined,
          }}
        >
          Stockout risk
        </Link>
        <Link
          href={buildHref(basePath, base, {
            dead_stock_only: deadOnly ? undefined : "1",
          })}
          className="ui-btn ui-btn-secondary"
          style={{
            padding: "0.35rem 0.65rem",
            fontSize: "0.8rem",
            borderColor: deadOnly ? "var(--accent)" : undefined,
          }}
        >
          Dead stock
        </Link>
      </div>

      {items.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>No SKUs match filters for the latest metric date.</p>
      ) : (
        <div className="ui-table-wrap">
          <table className="ui-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>On hand</th>
                <th>Cover (d)</th>
                <th>Aging (d)</th>
                <th>₹ at risk</th>
                {showReorderQty ? <th>Reorder qty</th> : null}
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              {items.map((row) => (
                <tr key={row.canonical_sku_id}>
                  <td>
                    <strong>{row.sku_code}</strong>
                  </td>
                  <td>{formatNum(row.on_hand, 0)}</td>
                  <td>{formatNum(row.days_of_cover)}</td>
                  <td>{formatNum(row.aging_days, 0)}</td>
                  <td>{formatInr(row.capital_at_risk)}</td>
                  {showReorderQty ? (
                    <td>{formatNum(row.reorder_qty, 0)}</td>
                  ) : null}
                  <td style={{ fontSize: "0.78rem" }}>
                    {row.stockout_risk ? (
                      <span className="ui-badge ui-badge-degraded">Stockout</span>
                    ) : null}{" "}
                    {row.dead_stock ? (
                      <span className="ui-badge ui-badge-muted">Dead</span>
                    ) : null}
                    {row.cogs_missing ? (
                      <span className="ui-badge ui-badge-failed">No COGS</span>
                    ) : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
