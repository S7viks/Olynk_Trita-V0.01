import { NextResponse } from "next/server";

import { establishSession, sessionCookiePayload } from "@/lib/auth/establish-session";

export async function POST(request: Request) {
  const body = (await request.json()) as {
    access_token?: string;
    company_name?: string;
    email?: string;
  };
  const supabaseToken = body.access_token?.trim();
  if (!supabaseToken) {
    return NextResponse.json({ error: "access_token required" }, { status: 400 });
  }

  try {
    const result = await establishSession(supabaseToken, {
      company_name: body.company_name,
      email: body.email,
    });
    const cookies = sessionCookiePayload(result);
    const response = NextResponse.json({
      ok: true,
      tenant_id: result.tenant_id,
      onboarding_complete: result.onboarding_complete,
    });
    response.cookies.set(cookies.token.name, cookies.token.value, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: cookies.token.maxAge,
    });
    response.cookies.set(cookies.onboarding.name, cookies.onboarding.value, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: cookies.onboarding.maxAge,
    });
    return response;
  } catch (err) {
    const message = err instanceof Error ? err.message : "Session failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
