import { LoginPageClient } from "@/components/auth/login-form";
import { sanitizeNextPath } from "@/lib/auth/sanitize-next";

export default function LoginPage({
  searchParams,
}: {
  searchParams: { next?: string; error?: string };
}) {
  const next = sanitizeNextPath(searchParams.next);
  return <LoginPageClient nextPath={next} error={searchParams.error} />;
}
