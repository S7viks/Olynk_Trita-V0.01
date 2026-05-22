import Link from "next/link";

import { PageHeader } from "@/components/ui/page-header";

const REPORTS = [
  {
    href: "/reports/health",
    title: "Data Health",
    description:
      "Connectors, SKU mart alignment, resolution rate, stockout/dead-stock counts (F-REPORT-HEALTH).",
  },
  {
    href: "/reports/aging",
    title: "SKU aging",
    description: "₹ at risk and aging days — default sort capital_at_risk desc.",
  },
  {
    href: "/reports/dead-stock",
    title: "Dead stock",
    description: "SKUs flagged dead_stock on the latest metric date.",
  },
  {
    href: "/reports/reorder",
    title: "Reorder queue",
    description: "Stockout-risk SKUs with engine reorder_qty — cover ascending.",
  },
];

export default function ReportsPage() {
  return (
    <section>
      <PageHeader
        title="Reports"
        description="Deterministic reports from gold and feat marts — same numbers as the API, no LLM math."
      />
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          display: "grid",
          gap: "0.75rem",
        }}
      >
        {REPORTS.map((r) => (
          <li key={r.href}>
            <Link
              href={r.href}
              className="ui-card"
              style={{
                display: "block",
                textDecoration: "none",
                color: "inherit",
              }}
            >
              <strong style={{ fontSize: "1.05rem" }}>{r.title}</strong>
              <p style={{ margin: "0.35rem 0 0", color: "var(--muted)", fontSize: "0.9rem" }}>
                {r.description}
              </p>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
