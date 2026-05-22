import { ConnectShopify } from "@/components/connect-shopify";
import { ConnectorRm1Panel, ConnectorRm3Panel } from "@/components/connector-rm1-panel";
import { SourcesCsvBlock } from "@/components/sources-csv-block";
import { SourcesHealthTable } from "@/components/sources-health-table";
import { SourcesLegend } from "@/components/sources-legend";
import { SyncShopifyButton } from "@/components/sync-shopify";
import { fetchIntegrationsHealth } from "@/lib/trita-api";

export default async function SourcesPage({
  searchParams,
}: {
  searchParams: {
    shopify?: string;
    error?: string;
    synced?: string;
    detail?: string;
    csv?: string;
  };
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
  const csvOk = searchParams.csv === "ok";
  const csvDegraded = searchParams.csv === "degraded";
  const csvError =
    searchParams.error === "csv_upload_failed" ||
    searchParams.error === "csv_validation_failed";
  const tally = health?.integrations.find((i) => i.source === "tally");
  const delhivery = health?.integrations.find((i) => i.source === "delhivery");

  return (
    <section>
      <header className="page-header">
        <h1>Sources</h1>
        <p>
          Ten integrations with honest status badges — six production-grade at launch.
          Connect, sync, and upload CSV where applicable (F-UI-SOURCES).
        </p>
      </header>
      <SourcesLegend />

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

      {csvOk ? (
        <p
          style={{
            padding: "0.75rem 1rem",
            background: "var(--surface)",
            border: "1px solid var(--healthy)",
            borderRadius: 8,
          }}
        >
          CSV upload complete — check Tally row for valid and quarantine counts.
        </p>
      ) : null}

      {csvDegraded ? (
        <p
          style={{
            padding: "0.75rem 1rem",
            background: "var(--surface)",
            border: "1px solid var(--degraded)",
            borderRadius: 8,
          }}
        >
          CSV uploaded with quarantined rows — review detail on the Tally row.
        </p>
      ) : null}

      {csvError ? (
        <p style={{ color: "var(--failed)" }}>
          CSV upload failed — check file format or API logs.
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
          {isConnected ? (
            <form
              action="/api/sources/shopify/disconnect"
              method="post"
              style={{ marginTop: "1rem", display: "inline-block" }}
            >
              <input type="hidden" name="return_to" value="/sources" />
              <button
                type="submit"
                style={{
                  padding: "0.4rem 0.75rem",
                  fontSize: "0.85rem",
                  borderRadius: 6,
                  border: "1px solid var(--border)",
                  background: "transparent",
                  cursor: "pointer",
                  marginRight: "0.75rem",
                }}
              >
                Disconnect Shopify
              </button>
            </form>
          ) : (
            <ConnectShopify returnTo="/sources" />
          )}
          <ConnectorRm1Panel integrations={health.integrations} />
          <ConnectorRm3Panel integrations={health.integrations} />
          <SourcesCsvBlock
            title="Delhivery (CSV hub)"
            description="Shipment export via tpl_delhivery_shipments when API beta is not connected."
            healthKey="delhivery"
            integration={delhivery}
            label="Delhivery"
            logicalSource="delhivery"
            templateId="tpl_delhivery_shipments"
          />
          <SourcesCsvBlock
            title="Tally (CSV hub)"
            description="Unit cost and sales history from Tally exports."
            healthKey="tally"
            integration={tally}
            label="Tally"
            logicalSource="tally"
            hint="Auto-detects Tally stock or sales templates from headers."
          />
        </>
      ) : null}
    </section>
  );
}
