import { apiBaseUrl } from "@/lib/constants";

export type TritaHealth = { status: string; service: string };

/** True when the configured base URL is the Trita FastAPI (not another app on :8000). */
const HEALTH_TIMEOUT_MS = 5_000;

export async function isTritaApiReachable(base = apiBaseUrl()): Promise<boolean> {
  try {
    const res = await fetch(`${base}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS),
    });
    if (!res.ok) return false;
    const body = (await res.json()) as Partial<TritaHealth>;
    return body.service === "trita-api";
  } catch {
    return false;
  }
}

export function wrongApiMessage(base = apiBaseUrl()): string {
  return (
    `The server at ${base} is not the Trita API (expected GET /health → service: "trita-api"). ` +
    `Another process may be using port 8000. Stop it, then run .\\scripts\\start-api.ps1 from the repo root.`
  );
}
