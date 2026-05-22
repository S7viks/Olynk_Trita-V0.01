import { InventorySkuTable } from "@/components/inventory-sku-table";
import { fetchSkuMetrics } from "@/lib/trita-api";

const VALID_SORT = new Set([
  "days_of_cover",
  "aging_days",
  "capital_at_risk",
  "velocity_7d",
  "sku_code",
]);

export default async function InventoryPage({
  searchParams,
}: {
  searchParams: {
    sort?: string;
    order?: string;
    stockout_only?: string;
    dead_stock_only?: string;
  };
}) {
  const sort = VALID_SORT.has(searchParams.sort ?? "")
    ? searchParams.sort!
    : "days_of_cover";
  const order = searchParams.order === "desc" ? "desc" : "asc";

  let data;
  let error: string | null = null;
  try {
    data = await fetchSkuMetrics({
      sort,
      order,
      stockout_only: searchParams.stockout_only === "1",
      dead_stock_only: searchParams.dead_stock_only === "1",
      limit: 500,
    });
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load inventory";
  }

  const metricDate = data?.items[0]?.metric_date ?? null;

  return (
    <section>
      <h1 style={{ marginTop: 0 }}>Inventory</h1>
      <p style={{ color: "var(--muted)", maxWidth: "42rem" }}>
        Read-only SKU list from <code>feat.sku_metrics_daily</code>. Sort by cover
        or aging; filter stockout and dead-stock flags (F-UI-INVENTORY-LIST).
      </p>
      {error ? (
        <p style={{ color: "var(--failed)" }}>{error}</p>
      ) : data ? (
        <InventorySkuTable
          items={data.items}
          metricDate={metricDate}
          searchParams={searchParams}
        />
      ) : null}
    </section>
  );
}
