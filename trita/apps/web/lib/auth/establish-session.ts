import { isTritaApiReachable, wrongApiMessage } from "@/lib/api-health";
import { parseTritaApiError } from "@/lib/auth/api-errors";
import { TRITA_ONBOARDING_COOKIE, TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export type EstablishSessionResult = {
  access_token: string;
  tenant_id: string;
  onboarding_complete: boolean;
};

export type EstablishSessionOptions = {
  company_name?: string;
  email?: string;
};

const API_TIMEOUT_MS = 20_000;

async function exchangeToken(supabaseToken: string): Promise<Response> {
  return fetch(`${apiBaseUrl()}/v1/auth/exchange`, {
    method: "POST",
    headers: { Authorization: `Bearer ${supabaseToken}` },
    signal: AbortSignal.timeout(API_TIMEOUT_MS),
  });
}

async function registerTenant(
  supabaseToken: string,
  opts: EstablishSessionOptions
): Promise<Response> {
  return fetch(`${apiBaseUrl()}/v1/auth/register`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${supabaseToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      company_name: opts.company_name ?? undefined,
      email: opts.email ?? undefined,
    }),
    signal: AbortSignal.timeout(API_TIMEOUT_MS),
  });
}

/** Map Supabase session → Trita JWT; auto-register on first sign-in. */
export async function establishSession(
  supabaseAccessToken: string,
  opts: EstablishSessionOptions = {}
): Promise<EstablishSessionResult> {
  if (!(await isTritaApiReachable())) {
    throw new Error(wrongApiMessage());
  }

  let res = await exchangeToken(supabaseAccessToken);
  if (res.status === 403) {
    const reg = await registerTenant(supabaseAccessToken, opts);
    if (!reg.ok) {
      throw new Error(await parseTritaApiError(reg, "Register failed"));
    }
    res = await exchangeToken(supabaseAccessToken);
  }
  if (!res.ok) {
    throw new Error(await parseTritaApiError(res, "Exchange failed"));
  }
  const data = (await res.json()) as {
    access_token: string;
    tenant_id: string;
    onboarding_complete?: boolean;
  };
  return {
    access_token: data.access_token,
    tenant_id: data.tenant_id,
    onboarding_complete: Boolean(data.onboarding_complete),
  };
}

export function sessionCookiePayload(result: EstablishSessionResult) {
  return {
    token: {
      name: TRITA_TOKEN_COOKIE,
      value: result.access_token,
      maxAge: 8 * 3600,
    },
    onboarding: {
      name: TRITA_ONBOARDING_COOKIE,
      value: result.onboarding_complete ? "1" : "0",
      maxAge: 8 * 3600,
    },
  };
}
