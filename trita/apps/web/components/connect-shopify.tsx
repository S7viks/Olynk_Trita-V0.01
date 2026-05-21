import { devShopHandle } from "@/lib/constants";

/** Single dev-store connect — shop from env, not a form (RM-1+: install URL / tenant settings). */
export function ConnectShopify() {
  const shop = devShopHandle();
  const connectHref = `/api/sources/shopify/connect?shop=${encodeURIComponent(shop)}`;

  return (
    <div
      style={{
        marginTop: "1.5rem",
        padding: "1rem",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 8,
      }}
    >
      <h2 style={{ margin: "0 0 0.5rem", fontSize: "1.1rem" }}>Connect Shopify</h2>
      <p style={{ margin: "0 0 1rem", color: "var(--muted)", fontSize: "0.9rem" }}>
        Opens OAuth for your Partner dev store ({shop}.myshopify.com), using this
        signed-in tenant. Configure the store via{" "}
        <code>SHOPIFY_DEV_SHOP_DOMAIN</code> or{" "}
        <code>NEXT_PUBLIC_SHOPIFY_DEV_SHOP</code> in <code>.env</code>.
      </p>
      <a
        href={connectHref}
        style={{
          display: "inline-block",
          padding: "0.6rem 1.1rem",
          background: "var(--accent)",
          color: "#fff",
          borderRadius: 6,
          fontWeight: 600,
          textDecoration: "none",
        }}
      >
        Connect Shopify
      </a>
    </div>
  );
}
