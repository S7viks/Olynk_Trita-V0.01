"use client";

import { useRef, useState } from "react";

export function CsvUploadPanel({ sourceLabel }: { sourceLabel: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState(false);

  return (
    <form
      action="/api/csv/upload"
      method="post"
      encType="multipart/form-data"
      style={{ marginTop: "0.5rem" }}
      onSubmit={() => setPending(true)}
    >
      <input type="hidden" name="logical_source" value="tally" />
      <input
        ref={inputRef}
        type="file"
        name="file"
        accept=".csv,text/csv"
        required
        style={{ fontSize: "0.85rem", maxWidth: "100%" }}
      />
      <button
        type="submit"
        disabled={pending}
        style={{
          marginLeft: "0.75rem",
          padding: "0.4rem 0.75rem",
          background: "var(--accent)",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          cursor: pending ? "wait" : "pointer",
          fontSize: "0.85rem",
        }}
      >
        {pending ? "Uploading…" : `Upload ${sourceLabel} CSV`}
      </button>
      <p style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "0.35rem" }}>
        Auto-detects Tally templates or pass column map via API. Invalid rows go to
        quarantine.
      </p>
    </form>
  );
}
