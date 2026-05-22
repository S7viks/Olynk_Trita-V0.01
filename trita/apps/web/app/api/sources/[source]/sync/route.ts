import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

const ALLOWED = new Set(["unicommerce", "shiprocket", "razorpay"]);

export async function POST(
  _request: Request,
  context: { params: { source: string } }
) {
  const source = context.params.source.toLowerCase();
  if (!ALLOWED.has(source)) {
    redirect("/sources?error=unknown_connector");
  }
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/sources");
  }
  const res = await fetch(`${apiBaseUrl()}/v1/sources/${source}/sync`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    redirect(`/sources?error=${source}_sync_failed`);
  }
  redirect("/sources?synced=1");
}
