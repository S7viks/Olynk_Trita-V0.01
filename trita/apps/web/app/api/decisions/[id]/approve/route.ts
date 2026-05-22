import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function POST(
  _request: Request,
  context: { params: { id: string } }
) {
  const id = context.params.id;
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) redirect("/login?next=/inbox");

  const res = await fetch(`${apiBaseUrl()}/v1/decisions/${id}/approve`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!res.ok) {
    redirect(`/inbox?id=${id}&error=approve_failed`);
  }
  redirect(`/inbox?tab=done&id=${id}&action=approved`);
}
