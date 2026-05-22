import type { IntegrationHealth } from "@/lib/trita-api";

const STATUS_COLOR: Record<string, string> = {
  healthy: "var(--healthy)",
  degraded: "var(--degraded)",
  failed: "var(--failed)",
  disconnected: "var(--disconnected)",
};

function formatWhen(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function SourcesHealthTable({
  integrations,
}: {
  integrations: IntegrationHealth[];
}) {
  if (integrations.length === 0) {
    return (
      <p style={{ color: "var(--muted)" }}>
        No integration health rows yet. Connect Shopify and run sync.
      </p>
    );
  }

  return (
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
        {integrations.map((row) => (
          <tr key={row.source} style={{ borderBottom: "1px solid var(--border)" }}>
            <td style={{ padding: "0.75rem 1rem" }}>
              <span style={{ fontWeight: 600 }}>
                {(row as IntegrationHealth & { display_name?: string }).display_name ??
                  row.source}
              </span>
              <ConnectorTier mode={(row as IntegrationHealth & { mode?: string }).mode} />
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
              {formatWhen(row.last_sync_at)}
            </td>
            <td style={{ padding: "0.75rem 1rem", fontSize: "0.85rem" }}>
              {row.detail?.shop_domain ? (
                <span>{String(row.detail.shop_domain)}</span>
              ) : null}
              {row.detail?.message ? (
                <span style={{ display: "block", color: "var(--muted)" }}>
                  {String(row.detail.message)}
                </span>
              ) : null}
              {row.detail?.events != null ? (
                <span style={{ display: "block", color: "var(--muted)" }}>
                  {String(row.detail.events)} events
                  {row.detail.inserted != null
                    ? `, ${String(row.detail.inserted)} new`
                    : ""}
                </span>
              ) : null}
              {row.detail?.valid_count != null ? (
                <span style={{ display: "block", color: "var(--muted)" }}>
                  {String(row.detail.valid_count)} valid
                  {row.detail.quarantine_count != null
                    ? `, ${String(row.detail.quarantine_count)} quarantined`
                    : ""}
                </span>
              ) : null}
              {!row.detail?.shop_domain &&
              !row.detail?.message &&
              row.detail?.valid_count == null ? (
                <span style={{ color: "var(--muted)" }}>—</span>
              ) : null}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ConnectorTier({ mode }: { mode?: string }) {
  if (mode === "csv_hub") {
    return (
      <span
        style={{
          marginLeft: "0.5rem",
          fontSize: "0.7rem",
          padding: "0.1rem 0.35rem",
          borderRadius: 4,
          border: "1px solid var(--accent)",
          color: "var(--accent)",
        }}
      >
        CSV hub
      </span>
    );
  }
  return (
    <span
      style={{
        marginLeft: "0.5rem",
        fontSize: "0.7rem",
        padding: "0.1rem 0.35rem",
        borderRadius: 4,
        border: "1px solid var(--healthy)",
        color: "var(--healthy)",
      }}
    >
      Production
    </span>
  );
}
