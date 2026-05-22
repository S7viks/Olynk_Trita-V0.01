import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { TRITA_TOKEN_COOKIE, apiBaseUrl } from "@/lib/constants";

export async function POST(request: Request) {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/sources");
  }

  const form = await request.formData();
  const file = form.get("file");
  if (!file || !(file instanceof Blob)) {
    redirect("/sources?error=csv_no_file");
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
    redirect("/sources?error=csv_upload_failed");
  }

  const body = (await res.json()) as { status?: string; quarantine_count?: number };
  if (body.status === "failed") {
    redirect("/sources?error=csv_validation_failed");
  }
  if ((body.quarantine_count ?? 0) > 0) {
    redirect("/sources?csv=degraded");
  }
  redirect("/sources?csv=ok");
}
