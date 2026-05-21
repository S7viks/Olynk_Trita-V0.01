export function SyncShopifyButton() {
  return (
    <form action="/api/sources/shopify/sync" method="post" style={{ display: "inline" }}>
      <button
        type="submit"
        style={{
          padding: "0.6rem 1.1rem",
          background: "var(--healthy)",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          fontWeight: 600,
          cursor: "pointer",
          fontSize: "0.95rem",
        }}
      >
        Run sync
      </button>
    </form>
  );
}
