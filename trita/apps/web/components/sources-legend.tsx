/** F-UI-SOURCES — honest connector tiers (no fake connected states). */

export function SourcesLegend() {
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "0.75rem 1.25rem",
        marginBottom: "1rem",
        fontSize: "0.85rem",
        color: "var(--muted)",
      }}
    >
      <span>
        <TierBadge label="Production" color="var(--healthy)" />
        RM-1 API sync
      </span>
      <span>
        <TierBadge label="CSV hub" color="var(--accent)" />
        Upload → validate → raw
      </span>
      <span>
        <StatusSwatch color="var(--healthy)" /> healthy
      </span>
      <span>
        <StatusSwatch color="var(--degraded)" /> degraded
      </span>
      <span>
        <StatusSwatch color="var(--disconnected)" /> not connected
      </span>
    </div>
  );
}

function TierBadge({ label, color }: { label: string; color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        marginRight: "0.35rem",
        padding: "0.1rem 0.45rem",
        borderRadius: 4,
        border: `1px solid ${color}`,
        color,
        fontSize: "0.75rem",
        fontWeight: 600,
      }}
    >
      {label}
    </span>
  );
}

function StatusSwatch({ color }: { color: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: color,
        marginRight: "0.35rem",
        verticalAlign: "middle",
      }}
    />
  );
}
