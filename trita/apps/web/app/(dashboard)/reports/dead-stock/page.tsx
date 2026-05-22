import { PageHeader } from "@/components/ui/page-header";
import { SkuMetricsTable } from "@/components/sku-metrics-table";
import { fetchSkuMetrics } from "@/lib/trita-api";

export default async function DeadStockReportPage({
  searchParams,
}: {
  searchParams: Record<string, string | undefined>;
}) {
  const sort = searchParams.sort === "capital_at_risk" ? "capital_at_risk" : "aging_days";
  const order = searchParams.order === "asc" ? "asc" : "desc";

  let data;
  let error: string | null = null;
  try {
    data = await fetchSkuMetrics({
      sort,
      order,
      dead_stock_only: true,
      limit: 500,
    });
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load report";
  }

  return (
    <section>
      <PageHeader
        title="Dead stock"
        description="SKUs flagged dead_stock on the latest metric date — sorted by aging (F-REPORT-DEAD)."
      />
      {error ? <p className="ui-alert ui-alert-error">{error}</p> : null}
      {data ? (
        <SkuMetricsTable
          items={data.items}
          metricDate={data.items[0]?.metric_date ?? null}
          searchParams={{ sort, order, dead_stock_only: "1" }}
          basePath="/reports/dead-stock"
        />
      ) : null}
    </section>
  );
}
