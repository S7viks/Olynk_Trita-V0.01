import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { TRITA_ONBOARDING_COOKIE, TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function POST() {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "Not signed in" }, { status: 401 });
  }
  const res = await fetch(`${apiBaseUrl()}/v1/onboarding/complete`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  const text = await res.text();
  if (!res.ok) {
    return new NextResponse(text, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  }
  const response = new NextResponse(text, {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
  response.cookies.set(TRITA_ONBOARDING_COOKIE, "1", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 8 * 3600,
  });
  return response;
}
