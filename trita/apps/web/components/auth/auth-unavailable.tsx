import Link from "next/link";

import { AuthLayout } from "@/components/auth/auth-layout";
import { AuthAlert } from "@/components/auth/auth-alert";

export function AuthUnavailable({ backHref = "/login" }: { backHref?: string }) {
  return (
    <AuthLayout
      title="Sign-in unavailable"
      subtitle="Authentication is not available on this environment right now."
    >
      <AuthAlert tone="info">
        If you are an operator setting up Trita, ensure Supabase URL and publishable key are set
        for this deployment. Otherwise, contact your workspace administrator.
      </AuthAlert>
      <p className="mt-4 text-center text-[13px]">
        <Link href={backHref} className="font-semibold text-primary hover:underline">
          Return to sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
