import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

function safeReturnPath(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) {
    return "/sources";
  }
  return raw.split("?")[0] ?? "/sources";
}

export async function POST(request: Request) {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/sources");
  }

  const form = await request.formData();
  const returnTo = safeReturnPath(
    typeof form.get("return_to") === "string" ? (form.get("return_to") as string) : null
  );

  const file = form.get("file");
  if (!file || !(file instanceof Blob)) {
    redirect(`${returnTo}?error=csv_no_file`);
  }

  const outbound = new FormData();
  outbound.append("file", file, file instanceof File ? file.name : "upload.csv");
  const logicalSource = form.get("logical_source");
  if (typeof logicalSource === "string" && logicalSource) {
    outbound.append("logical_source", logicalSource);
  }
  const templateId = form.get("template_id");
  if (typeof templateId === "string" && templateId) {
    outbound.append("template_id", templateId);
  }
  const columnMap = form.get("column_map");
  if (typeof columnMap === "string" && columnMap) {
    outbound.append("column_map", columnMap);
  }

  const res = await fetch(`${apiBaseUrl()}/v1/csv/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: outbound,
    cache: "no-store",
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    const detail =
      typeof (errBody as { detail?: string }).detail === "string"
        ? (errBody as { detail: string }).detail
        : `Upload failed (HTTP ${res.status})`;
    redirect(
      `${returnTo}?error=csv_upload_failed&message=${encodeURIComponent(detail.slice(0, 300))}`
    );
  }

  const body = (await res.json()) as {
    status?: string;
    quarantine_count?: number;
    valid_count?: number;
    row_count?: number;
  };
  if (body.status === "failed") {
    const detail =
      body.valid_count === 0 && (body.row_count ?? 0) > 0
        ? "All rows failed validation — check column headers match the template."
        : "CSV validation failed — check file format.";
    redirect(
      `${returnTo}?error=csv_validation_failed&message=${encodeURIComponent(detail)}`
    );
  }
  if ((body.quarantine_count ?? 0) > 0) {
    redirect(`${returnTo}?csv=degraded`);
  }
  redirect(`${returnTo}?csv=ok`);
}
