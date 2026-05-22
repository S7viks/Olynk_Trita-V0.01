import { NextResponse } from "next/server";

import { TRITA_ONBOARDING_COOKIE, TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function POST() {
  if (process.env.NODE_ENV === "production") {
    return NextResponse.json({ error: "Dev login disabled in production" }, { status: 403 });
  }

  const res = await fetch(`${apiBaseUrl()}/dev/auth/token`, { method: "POST" });
  if (!res.ok) {
    const detail = await res.text();
    return NextResponse.json(
      { error: detail || "Dev token mint failed" },
      { status: res.status }
    );
  }

  const data = (await res.json()) as { access_token: string; tenant_id: string };
  const response = NextResponse.json({ ok: true, tenant_id: data.tenant_id });
  response.cookies.set(TRITA_TOKEN_COOKIE, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 8 * 3600,
  });
  response.cookies.set(TRITA_ONBOARDING_COOKIE, "1", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 8 * 3600,
  });
  return response;
}
