import Link from "next/link";

export default function ReportsPage() {
  return (
    <section>
      <h1 style={{ marginTop: 0 }}>Reports</h1>
      <p style={{ color: "var(--muted)", maxWidth: "42rem" }}>
        Deterministic reports from gold and feat marts. Inventory decision reports
        ship in RM-2.
      </p>
      <ul style={{ listStyle: "none", padding: 0, marginTop: "1.25rem" }}>
        <li style={{ marginBottom: "0.75rem" }}>
          <Link
            href="/reports/health"
            style={{
              display: "block",
              padding: "1rem 1.25rem",
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontWeight: 600,
            }}
          >
            Data Health
          </Link>
          <span
            style={{
              display: "block",
              marginTop: "0.35rem",
              fontSize: "0.9rem",
              color: "var(--muted)",
            }}
          >
            Connectors, SKU mart alignment, resolution rate, stockout/dead-stock
            counts (F-REPORT-HEALTH).
          </span>
        </li>
        <li style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          SKU aging, dead stock queue, reorder queue — RM-2 (F-REPORT-AGING,
          F-REPORT-DEAD, F-REPORT-REORDER).
        </li>
      </ul>
    </section>
  );
}
