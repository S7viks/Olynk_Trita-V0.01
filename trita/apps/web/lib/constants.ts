export const TRITA_TOKEN_COOKIE = "trita_access_token";

export function apiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
  // Server-side fetch: avoid localhost vs 127.0.0.1 mismatch on Windows.
  return raw.replace(/\/$/, "").replace(/\/\/localhost\b/i, "//127.0.0.1");
}

/** Partner dev store handle (mock app), e.g. tritabyolynk — not the pilot brand's live shop. */
export function devShopHandle(): string {
  const raw =
    process.env.NEXT_PUBLIC_SHOPIFY_DEV_SHOP ??
    process.env.NEXT_PUBLIC_SHOPIFY_DEV_SHOP_DOMAIN ??
    "tritabyolynk";
  return raw.replace(/\.myshopify\.com$/i, "").trim();
}
