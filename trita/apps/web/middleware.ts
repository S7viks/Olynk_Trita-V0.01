import { type NextRequest, NextResponse } from "next/server";

import { TRITA_ONBOARDING_COOKIE, TRITA_TOKEN_COOKIE } from "./lib/constants";
import { updateSupabaseSession } from "./lib/supabase/middleware";

const AUTH_PATHS = ["/login", "/signup", "/forgot-password"];
const PUBLIC_PREFIXES = ["/api/auth", "/auth/callback", "/auth/google"];

function applyTritaAuth(request: NextRequest, base: NextResponse): NextResponse {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(TRITA_TOKEN_COOKIE)?.value;
  const onboardingDone = request.cookies.get(TRITA_ONBOARDING_COOKIE)?.value === "1";

  if (PUBLIC_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return base;
  }

  if (AUTH_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    if (token) {
      const dest = onboardingDone ? "/" : "/onboarding";
      const redirect = NextResponse.redirect(new URL(dest, request.url));
      base.cookies.getAll().forEach((c) => redirect.cookies.set(c.name, c.value));
      return redirect;
    }
    return base;
  }

  if (!token) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", pathname);
    const redirect = NextResponse.redirect(login);
    base.cookies.getAll().forEach((c) => redirect.cookies.set(c.name, c.value));
    return redirect;
  }

  if (!onboardingDone && pathname !== "/onboarding" && !pathname.startsWith("/api/")) {
    const redirect = NextResponse.redirect(new URL("/onboarding", request.url));
    base.cookies.getAll().forEach((c) => redirect.cookies.set(c.name, c.value));
    return redirect;
  }

  if (onboardingDone && pathname === "/onboarding") {
    const redirect = NextResponse.redirect(new URL("/", request.url));
    base.cookies.getAll().forEach((c) => redirect.cookies.set(c.name, c.value));
    return redirect;
  }

  return base;
}

export async function middleware(request: NextRequest) {
  const supabaseResponse = await updateSupabaseSession(request);
  return applyTritaAuth(request, supabaseResponse);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|favicon.svg).*)"],
};
