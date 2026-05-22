import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

function safeReturnPath(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) {
    return "/sources";
  }
  return raw.split("?")[0] ?? "/sources";
}

export async function POST(request: Request) {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/sources");
  }

  const form = await request.formData();
  const returnTo = safeReturnPath(
    typeof form.get("return_to") === "string" ? (form.get("return_to") as string) : null
  );

  const res = await fetch(`${apiBaseUrl()}/v1/sources/shopify/connection`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    redirect(`${returnTo}?shopify=error&message=${encodeURIComponent("Disconnect failed")}`);
  }

  redirect(`${returnTo}?shopify=disconnected`);
}
