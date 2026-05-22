export type SourceKind = "oauth" | "csv" | "soon";

export type OnboardingSourceDef = {
  id: string;
  label: string;
  kind: SourceKind;
  description: string;
  recommended?: boolean;
  csv?: {
    logicalSource: string;
    templateId?: string;
    uploadHint: string;
  };
};

/** Sources merchants can opt into during onboarding (F-ONBOARD-001). */
export const ONBOARDING_SOURCES: OnboardingSourceDef[] = [
  {
    id: "shopify",
    label: "Shopify",
    kind: "oauth",
    recommended: true,
    description: "Orders, products, and inventory from your live store (OAuth).",
  },
  {
    id: "tally_stock",
    label: "Tally — stock / unit cost",
    kind: "csv",
    description: "COGS and closing stock from Tally export.",
    csv: {
      logicalSource: "tally",
      templateId: "tpl_tally_stock",
      uploadHint: "Stock item export with SKU, rate, and closing balance.",
    },
  },
  {
    id: "tally_sales",
    label: "Tally — sales vouchers",
    kind: "csv",
    description: "Historical sales lines when Shopify history is incomplete.",
    csv: {
      logicalSource: "tally",
      templateId: "tpl_tally_sales",
      uploadHint: "Sales voucher export with item, voucher no, qty, and date.",
    },
  },
  {
    id: "delhivery",
    label: "Delhivery — shipments",
    kind: "csv",
    description: "Shipment status and AWB tracking export.",
    csv: {
      logicalSource: "delhivery",
      templateId: "tpl_delhivery_shipments",
      uploadHint: "Delhivery shipment CSV with AWB and status columns.",
    },
  },
  {
    id: "generic_orders",
    label: "Other — orders CSV",
    kind: "csv",
    description: "Amazon, marketplaces, or internal order exports.",
    csv: {
      logicalSource: "generic",
      templateId: "tpl_generic_orders",
      uploadHint: "Any orders file with SKU, order id, qty, and date columns.",
    },
  },
  {
    id: "unicommerce",
    label: "Unicommerce",
    kind: "soon",
    description: "WMS inventory sync — connect from Sources after launch.",
  },
  {
    id: "razorpay",
    label: "Razorpay",
    kind: "soon",
    description: "Payout reconciliation — connect from Sources after launch.",
  },
];

const STORAGE_KEY = "trita_onboarding_sources";

export const DEFAULT_SELECTED_SOURCES = ["shopify", "tally_stock"];

export function loadSelectedSourceIds(): string[] {
  if (typeof window === "undefined") return DEFAULT_SELECTED_SOURCES;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SELECTED_SOURCES;
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return DEFAULT_SELECTED_SOURCES;
    const valid = new Set(ONBOARDING_SOURCES.map((s) => s.id));
    const ids = parsed.filter((id): id is string => typeof id === "string" && valid.has(id));
    return ids.length > 0 ? ids : DEFAULT_SELECTED_SOURCES;
  } catch {
    return DEFAULT_SELECTED_SOURCES;
  }
}

export function saveSelectedSourceIds(ids: string[]): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
}

export function sourceById(id: string): OnboardingSourceDef | undefined {
  return ONBOARDING_SOURCES.find((s) => s.id === id);
}

/** Integration health API `source` key for connection status / reset. */
export function healthSourceForId(id: string): string | null {
  const def = sourceById(id);
  if (!def) return null;
  if (def.kind === "oauth") return "shopify";
  if (id.startsWith("tally")) return "tally";
  return def.csv?.logicalSource ?? null;
}
