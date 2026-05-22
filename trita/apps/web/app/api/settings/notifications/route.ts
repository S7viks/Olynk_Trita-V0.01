import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function PATCH(request: Request) {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "Not signed in" }, { status: 401 });
  }

  const body = await request.json();
  const res = await fetch(`${apiBaseUrl()}/v1/settings/notifications`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  if (!res.ok) {
    return NextResponse.json(
      { error: text || "Update failed" },
      { status: res.status }
    );
  }
  return NextResponse.json(JSON.parse(text));
}
