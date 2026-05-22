import {
  DecisionDetailPanel,
  InboxList,
  InboxTabs,
} from "@/components/decision-inbox";
import {
  fetchDecisionDetail,
  fetchInbox,
  fetchRejectReasons,
} from "@/lib/trita-api";

export default async function InboxPage({
  searchParams,
}: {
  searchParams: { tab?: string; id?: string; action?: string };
}) {
  const tab =
    searchParams.tab === "snoozed" || searchParams.tab === "done"
      ? searchParams.tab
      : "open";

  let list;
  let detail;
  let reasons: string[] = [];
  let error: string | null = null;

  try {
    list = await fetchInbox(tab);
    reasons = (await fetchRejectReasons()).reasons;
    if (searchParams.id) {
      detail = await fetchDecisionDetail(searchParams.id);
    }
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load inbox";
  }

  const actionBanner =
    searchParams.action === "approved"
      ? "Decision approved."
      : searchParams.action === "rejected"
        ? "Decision rejected."
        : searchParams.action === "snoozed"
          ? "Decision snoozed for 7 days."
          : null;

  return (
    <section>
      <h1 style={{ marginTop: 0 }}>Decision Inbox</h1>
      <p style={{ color: "var(--muted)", maxWidth: "42rem" }}>
        Inventory decisions from the deterministic engine — approve, reject with
        reason, or snooze. Max 7 new cards per rolling week (F-INBOX-001..004).
      </p>

      {actionBanner ? (
        <p
          style={{
            padding: "0.75rem 1rem",
            background: "var(--surface)",
            border: "1px solid var(--healthy)",
            borderRadius: 8,
          }}
        >
          {actionBanner}
        </p>
      ) : null}

      {error ? <p style={{ color: "var(--failed)" }}>{error}</p> : null}

      {list ? (
        <>
          <InboxTabs active={tab} />
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(240px, 1fr) minmax(320px, 2fr)",
              gap: "1.25rem",
              alignItems: "start",
            }}
          >
            <InboxList
              items={list.items}
              selectedId={searchParams.id ?? null}
              tab={tab}
            />
            {detail?.decision ? (
              <DecisionDetailPanel
                decision={detail.decision}
                rejectReasons={reasons}
              />
            ) : (
              <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                Select a card to view impact, evidence, and actions.
              </p>
            )}
          </div>
        </>
      ) : null}
    </section>
  );
}
