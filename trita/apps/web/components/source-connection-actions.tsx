"use client";

import { useState } from "react";

import { OrbitButton } from "@/components/orbit/button";
import type { IntegrationHealth } from "@/lib/trita-api";

type Props = {
  healthKey: string;
  returnTo: string;
  connected: boolean;
  statusLine?: string;
  onActionComplete?: () => void;
};

export function SourceConnectionActions({
  healthKey,
  returnTo,
  connected,
  statusLine,
  onActionComplete,
}: Props) {
  const [busy, setBusy] = useState(false);

  if (!connected) return null;

  async function onDisconnect() {
    if (healthKey !== "shopify") return;
    setBusy(true);
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/api/sources/shopify/disconnect";
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "return_to";
    input.value = returnTo;
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
  }

  function onResetCsv() {
    setBusy(true);
    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/api/csv/reset";
    const source = document.createElement("input");
    source.type = "hidden";
    source.name = "source";
    source.value = healthKey;
    const ret = document.createElement("input");
    ret.type = "hidden";
    ret.name = "return_to";
    ret.value = returnTo;
    form.appendChild(source);
    form.appendChild(ret);
    document.body.appendChild(form);
    form.submit();
  }

  return (
    <div className="mt-3 rounded-md border border-emerald-200/80 bg-emerald-50/50 px-3 py-2 dark:border-emerald-900/50 dark:bg-emerald-950/30">
      {statusLine ? (
        <p className="text-caption font-semibold text-emerald-800 dark:text-emerald-300">
          {statusLine}
        </p>
      ) : (
        <p className="text-caption font-semibold text-emerald-800 dark:text-emerald-300">
          Connected
        </p>
      )}
      <div className="mt-2 flex flex-wrap gap-2">
        {healthKey === "shopify" ? (
          <OrbitButton
            type="button"
            variant="ghost"
            className="!h-8 !px-3 text-xs"
            disabled={busy}
            onClick={() => void onDisconnect()}
          >
            Disconnect
          </OrbitButton>
        ) : null}
        {healthKey === "tally" || healthKey === "delhivery" || healthKey === "generic" ? (
          <OrbitButton
            type="button"
            variant="ghost"
            className="!h-8 !px-3 text-xs"
            disabled={busy}
            onClick={onResetCsv}
          >
            Reset & re-upload
          </OrbitButton>
        ) : null}
        {onActionComplete ? (
          <OrbitButton
            type="button"
            variant="ghost"
            className="!h-8 !px-3 text-xs"
            disabled={busy}
            onClick={() => {
              onActionComplete();
              setBusy(false);
            }}
          >
            Refresh status
          </OrbitButton>
        ) : null}
      </div>
    </div>
  );
}

export function integrationConnected(
  integrations: IntegrationHealth[],
  healthKey: string
): { connected: boolean; line?: string } {
  const row = integrations.find((i) => i.source === healthKey);
  if (!row) return { connected: false };
  const detail = row.detail ?? {};
  const connected = Boolean(detail.connected);
  if (!connected) return { connected: false };

  const shop = typeof detail.shop_domain === "string" ? detail.shop_domain : null;
  const valid = detail.valid_count;
  const quarantine = detail.quarantine_count;
  const file = typeof detail.file_name === "string" ? detail.file_name : null;

  if (shop) return { connected: true, line: `Shopify: ${shop}` };
  if (file && valid != null) {
    const q =
      typeof quarantine === "number" && quarantine > 0 ? ` · ${quarantine} quarantined` : "";
    return { connected: true, line: `CSV: ${file} (${String(valid)} rows)${q}` };
  }
  if (valid != null) {
    return { connected: true, line: `${row.display_name ?? healthKey}: ${String(valid)} rows ingested` };
  }
  return { connected: true, line: `${row.display_name ?? healthKey} connected` };
}
