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
      <header className="page-header">
        <h1>Decision Inbox</h1>
        <p>
          Inventory decisions from the deterministic engine — approve, reject with
          reason, or snooze. Max 7 new cards per rolling week (F-INBOX-001..004).
        </p>
      </header>

      {actionBanner ? (
        <p className="ui-alert ui-alert-success" style={{ marginBottom: "1rem" }}>
          {actionBanner}
        </p>
      ) : null}

      {error ? <p className="ui-alert ui-alert-error">{error}</p> : null}

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
