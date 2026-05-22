"use client";

import { useState } from "react";

import { OrbitButton } from "@/components/orbit/button";
import { OrbitCard } from "@/components/orbit/card";
import { devShopHandle } from "@/lib/constants";
import { normalizeShopInput, shopHandleFromDomain } from "@/lib/shopify-shop";

type Props = {
  /** Web path after OAuth completes */
  returnTo?: string;
};

/**
 * Merchant enters their Shopify store domain; OAuth starts via web proxy (port 3000).
 */
export function ConnectShopify({ returnTo = "/onboarding" }: Props) {
  const placeholder = `${devShopHandle()}.myshopify.com`;
  const [shopInput, setShopInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  function onConnect() {
    setError(null);
    const domain = normalizeShopInput(shopInput);
    if (!domain) {
      setError(
        "Enter your Shopify store domain, e.g. your-brand.myshopify.com (from Shopify Admin → Settings)."
      );
      return;
    }
    const handle = shopHandleFromDomain(domain);
    const params = new URLSearchParams({
      shop: handle,
      return_to: returnTo,
    });
    window.location.assign(`/api/sources/shopify/connect?${params.toString()}`);
  }

  return (
    <OrbitCard variant="glass" className="!p-4">
      <h3 className="text-sm font-black">Connect Shopify</h3>
      <p className="mt-1 text-caption text-muted-foreground">
        Enter the <strong>myshopify.com</strong> domain for the store you want Trita to read. You
        will approve access in Shopify Admin.
      </p>

      <label className="mt-4 block text-[10px] font-black uppercase tracking-widest text-muted-foreground">
        Store domain
      </label>
      <input
        type="text"
        className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        placeholder={placeholder}
        value={shopInput}
        onChange={(e) => setShopInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            onConnect();
          }
        }}
        autoComplete="off"
        spellCheck={false}
      />
      <p className="mt-1 text-tiny text-muted-foreground">
        Examples: <code className="text-tiny">acme-brand.myshopify.com</code> or{" "}
        <code className="text-tiny">acme-brand</code>
      </p>

      {error ? (
        <p className="mt-2 text-caption text-destructive">{error}</p>
      ) : null}

      <OrbitButton type="button" className="mt-4" onClick={onConnect}>
        Connect Shopify
      </OrbitButton>
    </OrbitCard>
  );
}
