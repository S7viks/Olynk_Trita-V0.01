import Link from "next/link";

import type { IntegrationHealth } from "@/lib/trita-api";

type Step = {
  id: string;
  day: string;
  title: string;
  description: string;
  href: string;
  done: boolean;
};

function isHealthy(source: string, integrations: IntegrationHealth[]): boolean {
  const row = integrations.find((i) => i.source === source);
  return row?.status === "healthy";
}

function isConnected(source: string, integrations: IntegrationHealth[]): boolean {
  const row = integrations.find((i) => i.source === source);
  return Boolean(row?.detail && (row.detail as { connected?: boolean }).connected);
}

export function OnboardingChecklist({
  integrations,
}: {
  integrations: IntegrationHealth[];
}) {
  const steps: Step[] = [
    {
      id: "shopify",
      day: "Day 0–1",
      title: "Connect Shopify",
      description: "Orders and storefront inventory into raw → gold.",
      href: "/sources",
      done: isHealthy("shopify", integrations) || isConnected("shopify", integrations),
    },
    {
      id: "unicommerce",
      day: "Day 1–2",
      title: "Connect Unicommerce",
      description: "Warehouse truth and committed stock.",
      href: "/sources",
      done: isHealthy("unicommerce", integrations) || isConnected("unicommerce", integrations),
    },
    {
      id: "tally",
      day: "Day 2–3",
      title: "Upload Tally CSV",
      description: "Unit cost on SKU via CSV hub.",
      href: "/sources",
      done: isHealthy("tally", integrations),
    },
    {
      id: "razorpay",
      day: "Day 3–4",
      title: "Razorpay + Shiprocket",
      description: "Payouts and shipments in the graph.",
      href: "/sources",
      done:
        (isHealthy("razorpay", integrations) || isConnected("razorpay", integrations)) &&
        (isHealthy("shiprocket", integrations) || isConnected("shiprocket", integrations)),
    },
    {
      id: "health",
      day: "Day 4",
      title: "Review Data Health",
      description: "Confirm resolution rate and connector freshness.",
      href: "/reports/health",
      done: integrations.filter((i) => i.status !== "healthy").length <= 2,
    },
    {
      id: "inbox",
      day: "Day 5–7",
      title: "First decision card",
      description: "Approve or reject with reason in the Inbox.",
      href: "/inbox",
      done: false,
    },
  ];

  const completed = steps.filter((s) => s.done).length;

  return (
    <div>
      <p style={{ color: "var(--muted)", marginBottom: "1rem" }}>
        {completed} of {steps.length} steps complete · F-ONBOARD-001
      </p>
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {steps.map((step) => (
          <li
            key={step.id}
            className="ui-card"
            style={{
              opacity: step.done ? 0.85 : 1,
              borderColor: step.done ? "var(--healthy)" : undefined,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
              <div>
                <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>{step.day}</span>
                <h3 style={{ margin: "0.25rem 0", fontSize: "1rem" }}>{step.title}</h3>
                <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--muted)" }}>
                  {step.description}
                </p>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                {step.done ? (
                  <span className="ui-badge ui-badge-healthy">Done</span>
                ) : (
                  <Link href={step.href} className="ui-btn ui-btn-primary" style={{ textDecoration: "none" }}>
                    Go →
                  </Link>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
