"use client";

import { useCallback, useEffect, useState } from "react";

import { ConnectShopify } from "@/components/connect-shopify";
import { CsvUploadPanel } from "@/components/csv-upload-panel";
import { OrbitCard } from "@/components/orbit/card";
import {
  SourceConnectionActions,
  integrationConnected,
} from "@/components/source-connection-actions";
import { healthSourceForId, sourceById } from "@/lib/onboarding-sources";
import type { IntegrationHealth, OnboardingStatus } from "@/lib/trita-api";

type Props = {
  selectedIds: string[];
  status: OnboardingStatus;
  shopifyNotice?: string;
  shopifyError?: string;
  csvNotice?: string;
  csvError?: string;
};

export function OnboardingConnectStep({
  selectedIds,
  status,
  shopifyNotice,
  shopifyError,
  csvNotice,
  csvError,
}: Props) {
  const [integrations, setIntegrations] = useState<IntegrationHealth[]>([]);
  const [healthError, setHealthError] = useState<string | null>(null);

  const loadHealth = useCallback(async () => {
    try {
      const res = await fetch("/api/integrations/health", { cache: "no-store" });
      if (!res.ok) {
        setHealthError("Could not load connection status. Is Trita API running?");
        return;
      }
      const body = (await res.json()) as { integrations: IntegrationHealth[] };
      setIntegrations(body.integrations ?? []);
      setHealthError(null);
    } catch {
      setHealthError("Could not reach the API for connection status.");
    }
  }, []);

  useEffect(() => {
    void loadHealth();
  }, [loadHealth, shopifyNotice, csvNotice, status.shopify_connected]);

  const oauth = selectedIds.filter((id) => sourceById(id)?.kind === "oauth");
  const csv = selectedIds.filter((id) => sourceById(id)?.kind === "csv");

  return (
    <div className="mt-4 space-y-4">
      <p className="text-compact text-muted-foreground">
        Connect OAuth sources and upload CSV files for the sources you selected. Use disconnect or
        reset to start over.
      </p>

      {healthError ? <p className="text-caption text-destructive">{healthError}</p> : null}

      {csvNotice === "ok" ? (
        <p className="text-caption font-semibold text-emerald-700">
          CSV uploaded successfully. Upload another file or continue to launch.
        </p>
      ) : null}
      {csvNotice === "degraded" ? (
        <p className="text-caption text-amber-800">
          CSV uploaded with quarantined rows — review on Sources after launch.
        </p>
      ) : null}
      {csvError ? <p className="text-caption text-destructive">{csvError}</p> : null}

      {oauth.length > 0 ? (
        <section>
          <h3 className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">
            Connect (OAuth)
          </h3>
          {oauth.includes("shopify") ? (
            <div className="mt-2">
              <OrbitCard variant="glass" className="!p-4">
                <h4 className="text-sm font-black">Shopify</h4>
                {(() => {
                  const { connected, line } = integrationConnected(integrations, "shopify");
                  const isConnected =
                    connected || shopifyNotice === "connected" || status.shopify_connected;
                  return (
                    <>
                      {isConnected ? (
                        <SourceConnectionActions
                          healthKey="shopify"
                          returnTo="/onboarding"
                          connected
                          statusLine={line ?? "Shopify connected"}
                          onActionComplete={loadHealth}
                        />
                      ) : (
                        <>
                          <p className="mt-1 text-caption text-muted-foreground">
                            Live store orders and inventory (Phase 0 spine).
                          </p>
                          <ConnectShopify returnTo="/onboarding" />
                        </>
                      )}
                      {shopifyError ? (
                        <p className="mt-2 text-caption text-destructive">{shopifyError}</p>
                      ) : null}
                    </>
                  );
                })()}
              </OrbitCard>
            </div>
          ) : null}
        </section>
      ) : null}

      {csv.length > 0 ? (
        <section>
          <h3 className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">
            Upload data (CSV)
          </h3>
          <ul className="mt-2 space-y-3">
            {csv.map((id) => {
              const def = sourceById(id);
              const healthKey = healthSourceForId(id);
              if (!def?.csv || !healthKey) return null;
              const { connected, line } = integrationConnected(integrations, healthKey);
              return (
                <li key={id}>
                  <OrbitCard variant="glass" className="!p-4">
                    <h4 className="text-sm font-black">{def.label}</h4>
                    <p className="mt-1 text-caption text-muted-foreground">{def.csv.uploadHint}</p>
                    {connected ? (
                      <SourceConnectionActions
                        healthKey={healthKey}
                        returnTo="/onboarding"
                        connected
                        statusLine={line}
                        onActionComplete={loadHealth}
                      />
                    ) : (
                      <CsvUploadPanel
                        label={def.label}
                        logicalSource={def.csv.logicalSource}
                        templateId={def.csv.templateId}
                        returnTo="/onboarding"
                      />
                    )}
                  </OrbitCard>
                </li>
              );
            })}
          </ul>
        </section>
      ) : null}

      {oauth.length === 0 && csv.length === 0 ? (
        <p className="text-caption text-muted-foreground">
          No connectable sources selected — go back and pick at least one.
        </p>
      ) : null}
    </div>
  );
}
