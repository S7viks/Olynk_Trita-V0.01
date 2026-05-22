import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function POST(
  request: Request,
  context: { params: { id: string } }
) {
  const id = context.params.id;
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) redirect("/login?next=/inbox");

  const form = await request.formData();
  const reason_enum = String(form.get("reason_enum") ?? "").trim();
  const reason_text = String(form.get("reason_text") ?? "").trim() || null;

  if (!reason_enum) {
    redirect(`/inbox?id=${id}&error=reject_reason_required`);
  }

  const res = await fetch(`${apiBaseUrl()}/v1/decisions/${id}/reject`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ reason_enum, reason_text }),
    cache: "no-store",
  });

  if (!res.ok) {
    redirect(`/inbox?id=${id}&error=reject_failed`);
  }
  redirect(`/inbox?tab=done&id=${id}&action=rejected`);
}
