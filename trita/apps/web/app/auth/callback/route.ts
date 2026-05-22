import { NextResponse, type NextRequest } from "next/server";

import { establishSession, sessionCookiePayload } from "@/lib/auth/establish-session";
import {
  copySupabaseCookies,
  createRouteHandlerClient,
} from "@/lib/supabase/route-handler";

export async function GET(request: NextRequest) {
  const { searchParams, origin } = request.nextUrl;
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/onboarding";

  if (!code) {
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent("Missing auth code")}`
    );
  }

  const cookieResponse = NextResponse.next({ request });
  const supabase = createRouteHandlerClient(request, cookieResponse);
  if (!supabase) {
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent("Supabase not configured")}`
    );
  }

  const { data, error } = await supabase.auth.exchangeCodeForSession(code);
  if (error || !data.session) {
    const isCancel =
      error?.message?.toLowerCase().includes("cancel") ||
      error?.message?.toLowerCase().includes("denied");
    const q = isCancel ? "oauth" : encodeURIComponent(error?.message ?? "Auth failed");
    return NextResponse.redirect(`${origin}/login?error=${q}`);
  }

  try {
    const meta = data.session.user.user_metadata as { company_name?: string } | undefined;
    const result = await establishSession(data.session.access_token, {
      email: data.session.user.email ?? undefined,
      company_name:
        typeof meta?.company_name === "string" ? meta.company_name : undefined,
    });
    const cookies = sessionCookiePayload(result);
    const dest = result.onboarding_complete ? "/" : next;
    const response = NextResponse.redirect(`${origin}${dest}`);
    copySupabaseCookies(cookieResponse, response);
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
    const message = err instanceof Error ? err.message : "Session exchange failed";
    return NextResponse.redirect(`${origin}/login?error=${encodeURIComponent(message)}`);
  }
}
