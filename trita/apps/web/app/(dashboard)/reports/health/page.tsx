import Link from "next/link";

import { DataHealthReportView } from "@/components/data-health-report";
import { fetchDataHealthReport } from "@/lib/trita-api";

export default async function DataHealthReportPage() {
  let report;
  let error: string | null = null;
  try {
    report = await fetchDataHealthReport();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load report";
  }

  return (
    <section>
      <p style={{ margin: 0, fontSize: "0.9rem" }}>
        <Link href="/reports">← Reports</Link>
      </p>
      <h1 style={{ marginTop: "0.5rem" }}>Data Health</h1>
      <p style={{ color: "var(--muted)", maxWidth: "42rem" }}>
        Connector freshness, graph alignment, and SKU metrics from gold and feat
        marts — same numbers as <code>GET /v1/reports/health</code> (VA-14).
      </p>
      {error ? (
        <p style={{ color: "var(--failed)" }}>{error}</p>
      ) : report ? (
        <DataHealthReportView report={report} />
      ) : null}
    </section>
  );
}
