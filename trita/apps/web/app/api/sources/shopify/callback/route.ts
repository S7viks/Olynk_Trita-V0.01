import { redirect } from "next/navigation";

import { apiBaseUrl } from "@/lib/constants";

/**
 * Shopify Partner redirect target (port 3000).
 * Proxies to Trita API so OAuth works when API is not on :8000.
 */
export async function GET(request: Request) {
  const incoming = new URL(request.url);
  const api = new URL(`${apiBaseUrl()}/v1/sources/shopify/callback`);
  incoming.searchParams.forEach((value, key) => {
    api.searchParams.set(key, value);
  });

  const res = await fetch(api.toString(), { redirect: "manual" });
  const location = res.headers.get("location");
  if ((res.status === 302 || res.status === 307) && location) {
    redirect(location);
  }

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    redirect(
      `/onboarding?shopify=error&message=${encodeURIComponent(
        detail.slice(0, 200) || `API returned ${res.status}`
      )}`
    );
  }

  redirect("/onboarding?shopify=error&message=unexpected_callback_response");
}
