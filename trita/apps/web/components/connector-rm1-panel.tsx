import type { CSSProperties } from "react";

import { apiBaseUrl } from "@/lib/constants";
import type { IntegrationHealth } from "@/lib/trita-api";

const RM1_API = ["unicommerce", "shiprocket", "razorpay"] as const;

export function ConnectorRm1Panel({
  integrations,
}: {
  integrations: IntegrationHealth[];
}) {
  const apiBase = apiBaseUrl();

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <h2 style={{ fontSize: "1.1rem" }}>Connect more sources (RM-1)</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        API connectors: POST connect with credentials, then sync. Local dev: set{" "}
        <code>CONNECTOR_DEV_FIXTURES=1</code> and use{" "}
        <code>scripts/connect_rm1_fixtures.ps1</code>.
      </p>
      <ul style={{ listStyle: "none", padding: 0, margin: "1rem 0 0" }}>
        {integrations
          .filter((i) => RM1_API.includes(i.source as (typeof RM1_API)[number]))
          .map((row) => (
            <li
              key={row.source}
              style={{
                padding: "0.75rem 0",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <strong>{row.display_name ?? row.source}</strong>
              <span style={{ marginLeft: "0.5rem", color: "var(--muted)" }}>
                {row.status}
              </span>
              {row.detail?.connected ? (
                <form
                  action={`/api/sources/${row.source}/sync`}
                  method="post"
                  style={{ display: "inline", marginLeft: "0.75rem" }}
                >
                  <button type="submit" style={btnStyle}>
                    Run sync
                  </button>
                </form>
              ) : (
                <span style={{ marginLeft: "0.75rem", fontSize: "0.85rem" }}>
                  Connect via API:{" "}
                  <code>
                    POST {apiBase}/v1/sources/{row.source}/connect
                  </code>
                </span>
              )}
            </li>
          ))}
      </ul>
    </div>
  );
}

const btnStyle: CSSProperties = {
  padding: "0.4rem 0.75rem",
  background: "var(--accent)",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: "0.85rem",
};
