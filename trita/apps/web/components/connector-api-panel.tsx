import type { CSSProperties } from "react";

import { apiBaseUrl } from "@/lib/constants";
import type { IntegrationHealth } from "@/lib/trita-api";

export function ConnectorApiPanel({
  integrations,
  sources,
  title,
  hint,
}: {
  integrations: IntegrationHealth[];
  sources: readonly string[];
  title: string;
  hint: string;
}) {
  const apiBase = apiBaseUrl();

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <h2 style={{ fontSize: "1.1rem" }}>{title}</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{hint}</p>
      <ul style={{ listStyle: "none", padding: 0, margin: "1rem 0 0" }}>
        {integrations
          .filter((i) => sources.includes(i.source))
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
                  Connect:{" "}
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
