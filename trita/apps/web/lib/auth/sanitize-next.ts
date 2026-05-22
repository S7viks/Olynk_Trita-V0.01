const ALLOWED_PREFIXES = [
  "/",
  "/inbox",
  "/onboarding",
  "/sources",
  "/inventory",
  "/reports",
  "/chat",
  "/settings",
];

/** Prevent post-login redirect to chrome devtools paths or external URLs. */
export function sanitizeNextPath(raw: string | undefined): string {
  if (!raw) return "/";
  const path = raw.split("?")[0]?.trim() ?? "/";
  if (!path.startsWith("/") || path.startsWith("//") || path.includes("..")) {
    return "/";
  }
  if (path.includes(".well-known") || path.includes("\\")) {
    return "/";
  }
  const ok = ALLOWED_PREFIXES.some(
    (p) => path === p || (p !== "/" && path.startsWith(`${p}/`))
  );
  return ok ? path : "/";
}
