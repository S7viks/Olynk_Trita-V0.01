import { sanitizeNextPath } from "@/lib/auth/sanitize-next";

const SESSION_TIMEOUT_MS = 25_000;

/** Browser: exchange Supabase access token for Trita session cookies. */
export type CompleteSessionInput = {
  accessToken: string;
  email?: string;
  company_name?: string;
};

export type CompleteSessionResult = {
  onboarding_complete: boolean;
};

export async function completeTritaSession(
  input: CompleteSessionInput
): Promise<CompleteSessionResult> {
  const res = await fetch("/api/auth/session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      access_token: input.accessToken,
      email: input.email,
      company_name: input.company_name,
    }),
    signal: AbortSignal.timeout(SESSION_TIMEOUT_MS),
  });
  const body = (await res.json().catch(() => ({}))) as {
    error?: string;
    onboarding_complete?: boolean;
  };
  if (!res.ok) {
    throw new Error(
      body.error ?? "We could not start your session. Please try again."
    );
  }
  return { onboarding_complete: Boolean(body.onboarding_complete) };
}

export function redirectAfterSession(
  onboarding_complete: boolean,
  nextPath = "/onboarding"
): void {
  const safeNext = sanitizeNextPath(nextPath);
  window.location.href = onboarding_complete
    ? safeNext === "/onboarding"
      ? "/"
      : safeNext
    : "/onboarding";
}
