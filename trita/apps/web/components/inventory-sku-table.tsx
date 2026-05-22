import type { SkuMetricRow } from "@/lib/trita-api";

import { SkuMetricsTable } from "./sku-metrics-table";

export function InventorySkuTable({
  items,
  metricDate,
  searchParams,
}: {
  items: SkuMetricRow[];
  metricDate: string | null;
  searchParams: {
    sort?: string;
    order?: string;
    stockout_only?: string;
    dead_stock_only?: string;
  };
}) {
  return (
    <SkuMetricsTable
      items={items}
      metricDate={metricDate}
      searchParams={searchParams}
      basePath="/inventory"
    />
  );
}
