import { SettingsForm } from "@/components/settings-form";
import { PageHeader } from "@/components/ui/page-header";
import {
  fetchNotificationSettings,
  fetchTenantContext,
} from "@/lib/trita-api";

export default async function SettingsPage() {
  let tenant;
  let settings;
  let error: string | null = null;
  try {
    tenant = await fetchTenantContext();
    settings = await fetchNotificationSettings();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load settings";
  }

  return (
    <section>
      <PageHeader
        title="Settings"
        description="Tenant context, notification preferences, and lead-time defaults (F-SETTINGS-001)."
      />
      {error ? <p className="ui-alert ui-alert-error">{error}</p> : null}
      {tenant && settings ? (
        <SettingsForm tenant={tenant} initial={settings} />
      ) : null}
    </section>
  );
}
