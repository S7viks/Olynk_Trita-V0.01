import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function POST(request: Request) {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not signed in" }, { status: 401 });
  }

  const body = await request.json();
  const res = await fetch(`${apiBaseUrl()}/v1/chat/message`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
