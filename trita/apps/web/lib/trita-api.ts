import { cookies } from "next/headers";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "./constants";

export type IntegrationHealth = {
  source: string;
  display_name?: string;
  mode?: string;
  status: string;
  last_sync_at: string | null;
  freshness_sla_hours: number;
  detail: Record<string, unknown> | null;
  updated_at: string;
};

export type IntegrationsHealthResponse = {
  tenant_id: string;
  integrations: IntegrationHealth[];
};

export async function getTritaAccessToken(): Promise<string | null> {
  return cookies().get(TRITA_TOKEN_COOKIE)?.value ?? null;
}

async function tritaFetch<T>(path: string): Promise<T> {
  const token = await getTritaAccessToken();
  if (!token) {
    throw new Error("Not signed in");
  }
  const res = await fetch(`${apiBaseUrl()}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchIntegrationsHealth(): Promise<IntegrationsHealthResponse> {
  return tritaFetch<IntegrationsHealthResponse>("/v1/integrations/health");
}

export type MetricsSummary = {
  tenant_id: string;
  metric_date: string | null;
  sku_count: number;
  dim_sku_count: number;
  aligned: boolean;
  stockout_risk_count: number;
  dead_stock_count: number;
  cogs_missing_count: number;
  capital_at_risk_total: number;
};

export type SkuMetricRow = {
  canonical_sku_id: string;
  sku_code: string;
  on_hand: number | null;
  velocity_7d: number | null;
  velocity_30d: number | null;
  days_of_cover: number | null;
  aging_days: number | null;
  unit_cost: number | null;
  capital_at_risk: number | null;
  cogs_missing: boolean;
  stockout_risk: boolean;
  dead_stock: boolean;
  reorder_qty: number | null;
  metric_date: string | null;
};

export type SkuMetricsResponse = {
  tenant_id: string;
  count: number;
  items: SkuMetricRow[];
};

export type IdentityStats = {
  tenant_id: string;
  alias_count: number;
  resolution: {
    total_lines: number;
    resolved_lines: number;
    resolution_rate: number;
    meets_va13: boolean;
  };
  bridge: {
    order_keys: number;
    with_shipment: number;
    with_payment: number;
    with_both: number;
    full_bridge_rate: number;
  };
};

export type DataHealthReport = {
  tenant_id: string;
  generated_at: string;
  integrations: IntegrationHealth[];
  metrics: MetricsSummary;
  identity: IdentityStats;
  summary: {
    connectors_total: number;
    connectors_unhealthy: number;
    sku_mart_aligned: boolean;
    resolution_meets_va13: boolean;
    resolution_rate: number | null;
  };
};

export async function fetchDataHealthReport(): Promise<DataHealthReport> {
  return tritaFetch<DataHealthReport>("/v1/reports/health");
}

export async function fetchSkuMetrics(params: {
  sort?: string;
  order?: "asc" | "desc";
  stockout_only?: boolean;
  dead_stock_only?: boolean;
  limit?: number;
}): Promise<SkuMetricsResponse> {
  const q = new URLSearchParams();
  if (params.sort) q.set("sort", params.sort);
  if (params.order) q.set("order", params.order);
  if (params.stockout_only) q.set("stockout_only", "true");
  if (params.dead_stock_only) q.set("dead_stock_only", "true");
  if (params.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  return tritaFetch<SkuMetricsResponse>(`/v1/metrics/sku${qs ? `?${qs}` : ""}`);
}
