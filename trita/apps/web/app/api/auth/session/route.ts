import { NextResponse } from "next/server";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function POST(request: Request) {
  const body = (await request.json()) as { access_token?: string };
  const supabaseToken = body.access_token?.trim();
  if (!supabaseToken) {
    return NextResponse.json({ error: "access_token required" }, { status: 400 });
  }

  const res = await fetch(`${apiBaseUrl()}/v1/auth/exchange`, {
    method: "POST",
    headers: { Authorization: `Bearer ${supabaseToken}` },
  });
  if (!res.ok) {
    const detail = await res.text();
    return NextResponse.json(
      { error: detail || "Exchange failed" },
      { status: res.status }
    );
  }

  const data = (await res.json()) as { access_token: string };
  const response = NextResponse.json({ ok: true });
  response.cookies.set(TRITA_TOKEN_COOKIE, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 8 * 3600,
  });
  return response;
}
