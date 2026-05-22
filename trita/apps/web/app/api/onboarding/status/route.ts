import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function GET() {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "Not signed in" }, { status: 401 });
  }
  const res = await fetch(`${apiBaseUrl()}/v1/onboarding/status`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
