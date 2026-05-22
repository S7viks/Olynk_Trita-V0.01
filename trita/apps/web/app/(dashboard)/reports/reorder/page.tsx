import { PageHeader } from "@/components/ui/page-header";
import { SkuMetricsTable } from "@/components/sku-metrics-table";
import { fetchSkuMetrics } from "@/lib/trita-api";

export default async function ReorderQueueReportPage({
  searchParams,
}: {
  searchParams: Record<string, string | undefined>;
}) {
  const sort = searchParams.sort ?? "days_of_cover";
  const order = searchParams.order === "desc" ? "desc" : "asc";

  let data;
  let error: string | null = null;
  try {
    data = await fetchSkuMetrics({
      sort,
      order,
      stockout_only: true,
      limit: 500,
    });
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load report";
  }

  return (
    <section>
      <PageHeader
        title="Reorder queue"
        description="Stockout-risk SKUs with deterministic reorder_qty from the engine — lowest cover first (F-REPORT-REORDER)."
      />
      {error ? <p className="ui-alert ui-alert-error">{error}</p> : null}
      {data ? (
        <SkuMetricsTable
          items={data.items}
          metricDate={data.items[0]?.metric_date ?? null}
          searchParams={{ sort, order, stockout_only: "1" }}
          basePath="/reports/reorder"
          showReorderQty
        />
      ) : null}
    </section>
  );
}
