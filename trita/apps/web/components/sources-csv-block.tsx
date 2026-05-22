import { CsvUploadPanel } from "@/components/csv-upload-panel";
import type { IntegrationHealth } from "@/lib/trita-api";

type Props = {
  title: string;
  description: string;
  healthKey: string;
  integration?: IntegrationHealth;
  label: string;
  logicalSource: string;
  templateId?: string;
  hint?: string;
};

export function SourcesCsvBlock({
  title,
  description,
  healthKey,
  integration,
  label,
  logicalSource,
  templateId,
  hint,
}: Props) {
  const detail = integration?.detail ?? {};
  const connected = Boolean(detail.connected);
  const statusLine =
    typeof detail.file_name === "string" && detail.valid_count != null
      ? `CSV: ${detail.file_name} (${String(detail.valid_count)} rows)`
      : connected
        ? `${title} connected via CSV`
        : null;

  return (
    <div style={{ marginTop: "1.5rem" }}>
      <h2 style={{ fontSize: "1.1rem" }}>{title}</h2>
      <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>{description}</p>
      {integration ? (
        <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginTop: "0.35rem" }}>
          Status: {integration.status}
          {detail.quarantine_count != null
            ? ` · ${String(detail.quarantine_count)} quarantined`
            : ""}
        </p>
      ) : null}
      {connected && statusLine ? (
        <p
          style={{
            marginTop: "0.5rem",
            padding: "0.5rem 0.75rem",
            background: "var(--surface)",
            border: "1px solid var(--healthy)",
            borderRadius: 8,
            fontSize: "0.85rem",
          }}
        >
          {statusLine}
        </p>
      ) : null}
      {connected ? (
        <form
          action="/api/csv/reset"
          method="post"
          style={{ marginTop: "0.5rem", display: "inline-block" }}
        >
          <input type="hidden" name="return_to" value="/sources" />
          <input type="hidden" name="source" value={healthKey} />
          <button
            type="submit"
            style={{
              padding: "0.4rem 0.75rem",
              fontSize: "0.85rem",
              borderRadius: 6,
              border: "1px solid var(--border)",
              background: "transparent",
              cursor: "pointer",
            }}
          >
            Reset & re-upload
          </button>
        </form>
      ) : (
        <CsvUploadPanel
          label={label}
          logicalSource={logicalSource}
          templateId={templateId}
          returnTo="/sources"
          hint={hint}
        />
      )}
    </div>
  );
}
