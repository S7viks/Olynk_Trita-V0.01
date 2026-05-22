/** Normalize merchant shop input to *.myshopify.com for OAuth. */
export function normalizeShopInput(raw: string): string | null {
  let shop = raw.trim().toLowerCase();
  if (!shop) return null;

  shop = shop.replace(/^https?:\/\//, "");
  shop = shop.split("/")[0]?.split("?")[0] ?? "";
  if (!shop) return null;

  if (!shop.includes(".")) {
    shop = `${shop}.myshopify.com`;
  }

  if (!/^[a-z0-9][a-z0-9-]*\.myshopify\.com$/.test(shop)) {
    return null;
  }

  return shop;
}

/** Shop handle without .myshopify.com (for API ?shop= query). */
export function shopHandleFromDomain(domain: string): string {
  return domain.replace(/\.myshopify\.com$/i, "");
}
