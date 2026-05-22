import type { IntegrationHealth } from "@/lib/trita-api";

import { ConnectorApiPanel } from "./connector-api-panel";

const RM1_API = ["unicommerce", "shiprocket", "razorpay"] as const;

export function ConnectorRm1Panel({
  integrations,
}: {
  integrations: IntegrationHealth[];
}) {
  return (
    <ConnectorApiPanel
      integrations={integrations}
      sources={RM1_API}
      title="Connect more sources (RM-1)"
      hint="Production API connectors. Local dev: CONNECTOR_DEV_FIXTURES=1 and scripts/connect_rm1_fixtures.ps1."
    />
  );
}

export function ConnectorRm3Panel({
  integrations,
}: {
  integrations: IntegrationHealth[];
}) {
  return (
    <ConnectorApiPanel
      integrations={integrations}
      sources={["delhivery", "meta_ads", "google_ads"]}
      title="Beta connectors (RM-3)"
      hint="Delhivery logistics + Meta/Google ad spend for causal matrix. Use scripts/connect_rm3_fixtures.ps1 or POST connect with api_key."
    />
  );
}