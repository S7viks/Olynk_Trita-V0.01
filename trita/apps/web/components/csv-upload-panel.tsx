"use client";

import { useRef, useState } from "react";

import { OrbitButton } from "@/components/orbit/button";

type Props = {
  label: string;
  logicalSource: string;
  templateId?: string;
  /** Where to redirect after upload (query params appended). */
  returnTo?: string;
  hint?: string;
};

export function CsvUploadPanel({
  label,
  logicalSource,
  templateId,
  returnTo = "/sources",
  hint,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState(false);

  return (
    <form
      action="/api/csv/upload"
      method="post"
      encType="multipart/form-data"
      className="mt-3"
      onSubmit={() => setPending(true)}
    >
      <input type="hidden" name="logical_source" value={logicalSource} />
      <input type="hidden" name="return_to" value={returnTo} />
      {templateId ? <input type="hidden" name="template_id" value={templateId} /> : null}
      <div className="flex flex-wrap items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          name="file"
          accept=".csv,text/csv"
          required
          className="max-w-full text-sm file:mr-2 file:rounded-md file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-sm"
        />
        <OrbitButton type="submit" disabled={pending}>
          {pending ? "Uploading…" : "Upload CSV"}
        </OrbitButton>
      </div>
      <p className="mt-2 text-caption text-muted-foreground">
        {hint ??
          `Maps to ${label}. Headers are auto-detected when possible; invalid rows go to quarantine.`}
      </p>
    </form>
  );
}
