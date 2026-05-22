import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

/**
 * Start Shopify OAuth from the web app (Bearer from httpOnly cookie).
 * Replaces linking directly to API /dev/shopify (no JWT in browser).
 */
export async function GET(request: Request) {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/sources");
  }

  const url = new URL(request.url);
  const shop = url.searchParams.get("shop")?.trim();
  const returnTo = url.searchParams.get("return_to")?.trim() || "/onboarding";

  if (!shop) {
    redirect(
      `${returnTo}?shopify=error&message=${encodeURIComponent("Enter your Shopify store domain first.")}`
    );
  }

  const connectUrl = `${apiBaseUrl()}/v1/sources/shopify/connect?shop=${encodeURIComponent(shop)}&return_to=${encodeURIComponent(returnTo)}`;
  const res = await fetch(connectUrl, {
    method: "GET",
    redirect: "manual",
    headers: { Authorization: `Bearer ${token}` },
  });

  const location = res.headers.get("location");
  if ((res.status === 302 || res.status === 307) && location) {
    redirect(location);
  }

  redirect("/sources?error=shopify_connect_failed");
}
