import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

/** POST /v1/sources/shopify/sync — pull Shopify → raw, then refresh Sources. */
export async function POST() {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/sources");
  }

  const res = await fetch(`${apiBaseUrl()}/v1/sources/shopify/sync`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!res.ok) {
    const detail = (await res.text()).slice(0, 120);
    const q = new URLSearchParams({
      error: "shopify_sync_failed",
      ...(detail ? { detail } : {}),
    });
    redirect(`/sources?${q.toString()}`);
  }

  redirect("/sources?synced=1");
}
