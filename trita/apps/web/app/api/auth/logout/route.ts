import { NextResponse } from "next/server";

import { TRITA_TOKEN_COOKIE } from "@/lib/constants";

export async function POST(request: Request) {
  const response = NextResponse.redirect(new URL("/login", request.url));
  response.cookies.set(TRITA_TOKEN_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
  return response;
}
