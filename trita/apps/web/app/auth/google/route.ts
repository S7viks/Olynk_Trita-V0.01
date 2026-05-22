import { NextResponse, type NextRequest } from "next/server";

import {
  copySupabaseCookies,
  createRouteHandlerClient,
} from "@/lib/supabase/route-handler";

export async function GET(request: NextRequest) {
  const origin = request.nextUrl.origin;
  const next = request.nextUrl.searchParams.get("next") ?? "/onboarding";
  const redirectTo = `${origin}/auth/callback?next=${encodeURIComponent(next)}`;

  const cookieResponse = NextResponse.next({ request });
  const supabase = createRouteHandlerClient(request, cookieResponse);
  if (!supabase) {
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent("Supabase not configured")}`
    );
  }

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo,
      queryParams: { prompt: "select_account" },
    },
  });

  if (error || !data.url) {
    const message = error?.message ?? "Google sign-in could not start";
    return NextResponse.redirect(
      `${origin}/login?error=${encodeURIComponent(message)}`
    );
  }

  const googleRedirect = NextResponse.redirect(data.url);
  copySupabaseCookies(cookieResponse, googleRedirect);
  return googleRedirect;
}
