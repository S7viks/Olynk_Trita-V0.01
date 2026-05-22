import Link from "next/link";

export type FeedItem = {
  id: string;
  trigger_id: string;
  severity: string;
  title: string;
  body: string;
  payload: Record<string, unknown>;
  created_at: string | null;
};

const SEVERITY_COLOR: Record<string, string> = {
  alert: "var(--critical)",
  urgent: "var(--critical)",
  highlight: "var(--degraded)",
  info: "var(--muted)",
};

export function ProactiveFeedList({ items }: { items: FeedItem[] }) {
  if (items.length === 0) {
    return (
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
        No proactive events yet. Run{" "}
        <code>POST /v1/proactive/run-triggers</code> after metrics sync.
      </p>
    );
  }

  return (
    <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {items.map((item) => (
        <li
          key={item.id}
          style={{
            marginBottom: "0.75rem",
            padding: "0.85rem 1rem",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--surface)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "0.5rem",
              flexWrap: "wrap",
            }}
          >
            <strong style={{ fontSize: "0.95rem" }}>{item.title}</strong>
            <span
              style={{
                fontSize: "0.75rem",
                color: SEVERITY_COLOR[item.severity] ?? "var(--muted)",
                fontWeight: 600,
              }}
            >
              {item.trigger_id} · {item.severity}
            </span>
          </div>
          <p style={{ margin: "0.5rem 0 0", fontSize: "0.85rem", color: "var(--text)" }}>
            {item.body}
          </p>
          {item.created_at ? (
            <p style={{ margin: "0.35rem 0 0", fontSize: "0.75rem", color: "var(--muted)" }}>
              {item.created_at}
            </p>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export function ProactiveFeedActions() {
  return (
    <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
      <Link href="/inbox">Decision Inbox</Link> · <Link href="/chat">Chat</Link> ·{" "}
      <Link href="/sources">Sources</Link>
    </p>
  );
}
