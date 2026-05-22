import { PageHeader } from "@/components/ui/page-header";
import { SkuMetricsTable } from "@/components/sku-metrics-table";
import { fetchSkuMetrics } from "@/lib/trita-api";

export default async function SkuAgingReportPage({
  searchParams,
}: {
  searchParams: Record<string, string | undefined>;
}) {
  const sort = searchParams.sort === "sku_code" ? "sku_code" : "capital_at_risk";
  const order = searchParams.order === "asc" ? "asc" : "desc";

  let data;
  let error: string | null = null;
  try {
    data = await fetchSkuMetrics({ sort, order, limit: 500 });
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load report";
  }

  return (
    <section>
      <PageHeader
        title="SKU aging"
        description="Capital at risk and aging days from feat.sku_metrics_daily — sorted by ₹ at risk descending (F-REPORT-AGING)."
      />
      {error ? <p className="ui-alert ui-alert-error">{error}</p> : null}
      {data ? (
        <SkuMetricsTable
          items={data.items}
          metricDate={data.items[0]?.metric_date ?? null}
          searchParams={{ sort, order }}
          basePath="/reports/aging"
        />
      ) : null}
    </section>
  );
}
