import Link from "next/link";

import { ProactiveFeedActions, ProactiveFeedList } from "@/components/proactive-feed";
import { PageHeader } from "@/components/ui/page-header";
import { fetchProactiveFeed } from "@/lib/trita-api";

export default async function HomePage() {
  let feed;
  let error: string | null = null;
  try {
    feed = await fetchProactiveFeed();
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load proactive feed";
  }

  return (
    <section>
      <PageHeader
        title="Home"
        description="Proactive feed — threshold, velocity, causal, and sync triggers (F-PROACTIVE-001). Inbox-first when a decision is ready."
      >
        <Link href="/inbox" className="ui-btn ui-btn-primary" style={{ textDecoration: "none" }}>
          Open Decision Inbox
        </Link>
      </PageHeader>
      <ProactiveFeedActions />

      {error ? (
        <p className="ui-alert ui-alert-error">{error}</p>
      ) : (
        <>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            {feed?.count ?? 0} events · tenant {feed?.tenant_id}
          </p>
          <ProactiveFeedList items={feed?.items ?? []} />
        </>
      )}
    </section>
  );
}
