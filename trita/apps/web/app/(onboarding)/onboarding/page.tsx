import { redirect } from "next/navigation";

import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard";
import { TRITA_ONBOARDING_COOKIE, TRITA_TOKEN_COOKIE } from "@/lib/constants";
import { fetchOnboardingStatus } from "@/lib/trita-api";
import { cookies } from "next/headers";

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export default async function OnboardingPage({
  searchParams,
}: {
  searchParams?: {
    shopify?: string;
    message?: string;
    csv?: string;
    error?: string;
    source?: string;
  };
}) {
  const token = cookies().get(TRITA_TOKEN_COOKIE)?.value;
  if (!token) {
    redirect("/login?next=/onboarding");
  }
  if (cookies().get(TRITA_ONBOARDING_COOKIE)?.value === "1") {
    redirect("/");
  }

  let status;
  try {
    status = await fetchOnboardingStatus();
  } catch {
    redirect("/login?next=/onboarding");
  }

  if (status.onboarding_complete) {
    redirect("/");
  }

  return (
    <OnboardingWizard
      initial={status}
      shopifyNotice={searchParams?.shopify}
      shopifyError={searchParams?.message}
      csvNotice={searchParams?.csv}
      csvError={
        searchParams?.message
          ? safeDecode(searchParams.message)
          : searchParams?.error === "csv_upload_failed"
            ? "CSV upload failed — check file format and API logs."
            : searchParams?.error === "csv_validation_failed"
              ? "CSV validation failed — headers or required columns did not match."
              : searchParams?.error === "csv_no_file"
                ? "Choose a CSV file before uploading."
                : searchParams?.error === "csv_reset_failed"
                  ? "Could not reset CSV data."
                  : undefined
      }
    />
  );
}
