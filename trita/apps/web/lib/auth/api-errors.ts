import { wrongApiMessage } from "@/lib/api-health";
import { apiBaseUrl } from "@/lib/constants";

export async function parseTritaApiError(
  res: Response,
  fallback: string
): Promise<string> {
  const text = await res.text();
  let detail: string | undefined;
  try {
    const body = JSON.parse(text) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === "string") detail = body.detail;
    else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      detail = body.detail.map((d) => d.msg).join("; ");
    }
  } catch {
    /* not JSON */
  }

  if (res.status === 404) {
    return wrongApiMessage(apiBaseUrl());
  }
  if (detail === "Not Found" && res.status === 404) {
    return wrongApiMessage(apiBaseUrl());
  }
  if (res.status === 502 || res.status === 503) {
    return "Cannot reach the Trita API. Start it with .\\scripts\\start-api.ps1 and check NEXT_PUBLIC_API_URL.";
  }
  if (detail) return detail;
  return text || `${fallback} (${res.status})`;
}
