import { ConnectShopify } from "@/components/connect-shopify";
import { SourcesHealthTable } from "@/components/sources-health-table";
import { SyncShopifyButton } from "@/components/sync-shopify";
import { fetchIntegrationsHealth } from "@/lib/trita-api";

export default async function SourcesPage({
  searchParams,
}: {
  searchParams: { shopify?: string; error?: string; synced?: string; detail?: string };
}) {
  let health;
  let error: string | null = null;
  try {
    health = await fetchIntegrationsHealth();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load health";
  }

  const shopify = health?.integrations.find((i) => i.source === "shopify");
  const isConnected = Boolean(shopify?.detail?.connected);
  const needsSync =
    isConnected &&
    (shopify?.status === "degraded" || shopify?.status === "disconnected");
  const connectedBanner =
    searchParams.shopify === "connected" && needsSync;
  const syncOk = searchParams.synced === "1";
  const connectError = searchParams.error === "shopify_connect_failed";
  const syncError =
    searchParams.error === "shopify_sync_failed" &&
    !(shopify?.status === "healthy" && shopify.detail?.events != null);

  return (
    <section>
      <h1 style={{ marginTop: 0 }}>Sources</h1>
      <p style={{ color: "var(--muted)", maxWidth: "42rem" }}>
        Integration health for connected systems. Phase 0 shows the real Shopify
        row only — no placeholder badges for other connectors.
      </p>

      {connectError ? (
        <p style={{ color: "var(--failed)" }}>
          Shopify connect failed — sign in again and ensure the API is running.
        </p>
      ) : null}

      {syncError ? (
        <p style={{ color: "var(--failed)" }}>
          Sync failed — check API logs (token, scopes, or empty store).
          {searchParams.detail ? (
            <span style={{ display: "block", fontSize: "0.85rem", marginTop: "0.35rem" }}>
              {searchParams.detail}
            </span>
          ) : null}
        </p>
      ) : null}

      {syncOk && shopify?.status === "healthy" ? (
        <p
          style={{
            padding: "0.75rem 1rem",
            background: "var(--surface)",
            border: "1px solid var(--healthy)",
            borderRadius: 8,
          }}
        >
          Sync complete — Shopify health is green.
        </p>
      ) : null}

      {connectedBanner ? (
        <p
          style={{
            padding: "0.75rem 1rem",
            background: "var(--surface)",
            border: "1px solid var(--degraded)",
            borderRadius: 8,
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: "0.75rem",
          }}
        >
          <span>
            Shopify is connected. Run sync once to pull data and mark health
            green.
          </span>
          <SyncShopifyButton />
        </p>
      ) : null}

      {error ? (
        <p style={{ color: "var(--failed)" }}>{error}</p>
      ) : health ? (
        <>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            Tenant {health.tenant_id}
          </p>
          <SourcesHealthTable integrations={health.integrations} />
        </>
      ) : null}

      {health ? (
        <>
          {isConnected && needsSync && !connectedBanner ? (
            <p style={{ marginTop: "1rem" }}>
              <SyncShopifyButton />
              <span style={{ marginLeft: "0.75rem", color: "var(--muted)", fontSize: "0.9rem" }}>
                Pull orders/inventory into raw (idempotent).
              </span>
            </p>
          ) : null}
          <ConnectShopify />
        </>
      ) : null}
    </section>
  );
}
