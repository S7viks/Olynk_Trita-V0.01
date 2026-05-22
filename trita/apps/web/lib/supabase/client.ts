import { createBrowserClient } from "@supabase/ssr";

type CookieToSet = {
  name: string;
  value: string;
  options?: {
    path?: string;
    maxAge?: number;
    sameSite?: "lax" | "strict" | "none";
    secure?: boolean;
  };
};

function parseDocumentCookies(): { name: string; value: string }[] {
  if (typeof document === "undefined" || !document.cookie) return [];
  return document.cookie.split("; ").flatMap((part) => {
    const eq = part.indexOf("=");
    if (eq < 0) return [];
    return [{ name: part.slice(0, eq), value: part.slice(eq + 1) }];
  });
}

export function createClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    return null;
  }
  return createBrowserClient(url, key, {
    cookies: {
      getAll() {
        return parseDocumentCookies();
      },
      setAll(cookiesToSet: CookieToSet[]) {
        cookiesToSet.forEach(({ name, value, options }) => {
          const parts = [
            `${name}=${value}`,
            `path=${options?.path ?? "/"}`,
          ];
          if (options?.maxAge != null) parts.push(`max-age=${options.maxAge}`);
          if (options?.sameSite) parts.push(`samesite=${options.sameSite}`);
          if (options?.secure) parts.push("secure");
          document.cookie = parts.join("; ");
        });
      },
    },
  });
}
