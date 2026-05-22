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
  const days = Number(form.get("days") ?? "7") || 7;

  const res = await fetch(`${apiBaseUrl()}/v1/decisions/${id}/snooze`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ days }),
    cache: "no-store",
  });

  if (!res.ok) {
    redirect(`/inbox?id=${id}&error=snooze_failed`);
  }
  redirect(`/inbox?tab=snoozed&id=${id}&action=snoozed`);
}
