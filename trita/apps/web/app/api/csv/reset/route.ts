import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

const ALLOWED = new Set(["tally", "delhivery", "generic"]);

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
  const rawSource = form.get("source");
  const source =
    typeof rawSource === "string" ? rawSource.trim().toLowerCase() : "";
  if (!ALLOWED.has(source)) {
    redirect(`${returnTo}?error=csv_reset_invalid`);
  }

  const res = await fetch(`${apiBaseUrl()}/v1/csv/reset?source=${encodeURIComponent(source)}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail =
      typeof (body as { detail?: string }).detail === "string"
        ? (body as { detail: string }).detail
        : "Reset failed";
    redirect(`${returnTo}?error=csv_reset_failed&message=${encodeURIComponent(detail)}`);
  }

  redirect(`${returnTo}?csv=reset&source=${encodeURIComponent(source)}`);
}
