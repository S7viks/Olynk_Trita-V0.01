import { cookies } from "next/headers";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "./constants";

export type IntegrationHealth = {
  source: string;
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

export async function fetchIntegrationsHealth(): Promise<IntegrationsHealthResponse> {
  const token = await getTritaAccessToken();
  if (!token) {
    throw new Error("Not signed in");
  }
  const res = await fetch(`${apiBaseUrl()}/v1/integrations/health`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Health API ${res.status}: ${text}`);
  }
  return res.json() as Promise<IntegrationsHealthResponse>;
}
