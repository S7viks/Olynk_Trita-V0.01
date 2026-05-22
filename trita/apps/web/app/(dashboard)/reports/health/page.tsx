import { DataHealthReportView } from "@/components/data-health-report";
import { PageHeader } from "@/components/ui/page-header";
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
      <PageHeader
        title="Data Health"
        description="Connector freshness, graph alignment, and SKU metrics from gold and feat marts (VA-14)."
      />
      {error ? <p className="ui-alert ui-alert-error">{error}</p> : null}
      {report ? <DataHealthReportView report={report} /> : null}
    </section>
  );
}
