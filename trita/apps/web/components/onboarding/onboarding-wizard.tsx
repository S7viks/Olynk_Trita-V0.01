"use client";

import { useEffect, useState } from "react";

import { OnboardingConnectStep } from "@/components/onboarding/onboarding-connect-step";
import { OnboardingSourcePicker } from "@/components/onboarding/onboarding-source-picker";
import { OrbitButton } from "@/components/orbit/button";
import { OrbitCard } from "@/components/orbit/card";
import {
  DEFAULT_SELECTED_SOURCES,
  loadSelectedSourceIds,
  saveSelectedSourceIds,
} from "@/lib/onboarding-sources";
import type { OnboardingStatus } from "@/lib/trita-api";

const STEPS = [
  { id: 1, title: "Workspace", eyebrow: "Step 1 of 4" },
  { id: 2, title: "Your data sources", eyebrow: "Step 2 of 4" },
  { id: 3, title: "Connect & upload", eyebrow: "Step 3 of 4" },
  { id: 4, title: "Launch", eyebrow: "Step 4 of 4" },
] as const;

function initialStep(shopifyNotice?: string, csvNotice?: string): number {
  if (shopifyNotice === "connected" || csvNotice) return 3;
  return 1;
}

export function OnboardingWizard({
  initial,
  shopifyNotice,
  shopifyError,
  csvNotice,
  csvError,
}: {
  initial: OnboardingStatus;
  shopifyNotice?: string;
  shopifyError?: string;
  csvNotice?: string;
  csvError?: string;
}) {
  const [step, setStep] = useState(() => initialStep(shopifyNotice, csvNotice));
  const [company, setCompany] = useState(initial.display_name);
  const [status, setStatus] = useState(initial);
  const [selectedSources, setSelectedSources] = useState<string[]>(DEFAULT_SELECTED_SOURCES);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedSources(loadSelectedSourceIds());
  }, []);

  useEffect(() => {
    if (shopifyNotice === "connected" || shopifyError || csvNotice) {
      void refreshStatus();
    }
  }, [shopifyNotice, shopifyError, csvNotice]);

  async function saveProfile() {
    setBusy(true);
    setError(null);
    const res = await fetch("/api/onboarding/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_name: company.trim() }),
    });
    const body = await res.json().catch(() => ({}));
    setBusy(false);
    if (!res.ok) {
      setError((body as { error?: string }).error ?? "Save failed");
      return false;
    }
    setStatus(body as OnboardingStatus);
    return true;
  }

  async function refreshStatus() {
    const res = await fetch("/api/onboarding/status");
    if (res.ok) {
      setStatus((await res.json()) as OnboardingStatus);
    }
  }

  function onSourcesChange(ids: string[]) {
    setSelectedSources(ids);
    saveSelectedSourceIds(ids);
  }

  async function onNext() {
    if (step === 1) {
      if (!company.trim()) {
        setError("Company name is required.");
        return;
      }
      const ok = await saveProfile();
      if (ok) setStep(2);
      return;
    }
    if (step === 2) {
      if (selectedSources.length === 0) {
        setError("Select at least one data source.");
        return;
      }
      saveSelectedSourceIds(selectedSources);
      setStep(3);
      return;
    }
    if (step === 3) {
      await refreshStatus();
      setStep(4);
    }
  }

  async function onComplete() {
    setBusy(true);
    setError(null);
    const res = await fetch("/api/onboarding/complete", { method: "POST" });
    const body = await res.json().catch(() => ({}));
    setBusy(false);
    if (!res.ok) {
      setError((body as { error?: string }).error ?? "Could not finish onboarding");
      return;
    }
    window.location.href = "/";
  }

  return (
    <div className="mx-auto max-w-2xl animate-fade-in px-4 py-10 sm:px-6">
      <header className="mb-8">
        <p className="text-[10px] font-black uppercase tracking-[0.25em] text-primary">
          Setup · F-ONBOARD-001
        </p>
        <h1 className="mt-1 text-2xl font-black tracking-tight text-foreground">
          Welcome to Trita
        </h1>
        <p className="mt-2 max-w-lg text-compact text-muted-foreground">
          Tell us your brand, choose how you run inventory and orders, then connect or upload. Most
          teams finish in under a week.
        </p>
      </header>

      <div className="mb-6 flex gap-2">
        {STEPS.map((s) => (
          <div
            key={s.id}
            className={`h-1 flex-1 rounded-full ${step >= s.id ? "bg-primary" : "bg-muted"}`}
          />
        ))}
      </div>

      <OrbitCard>
        <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">
          {STEPS[step - 1].eyebrow}
        </p>
        <h2 className="mt-1 text-lg font-black">{STEPS[step - 1].title}</h2>

        {step === 1 ? (
          <div className="mt-4 space-y-3">
            <label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">
              Company / brand name
            </label>
            <input
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="e.g. Yoga Bar"
            />
            <p className="text-caption text-muted-foreground">
              Tenant slug: <code className="text-tiny">{status.slug}</code>
            </p>
          </div>
        ) : null}

        {step === 2 ? (
          <OnboardingSourcePicker selected={selectedSources} onChange={onSourcesChange} />
        ) : null}

        {step === 3 ? (
          <OnboardingConnectStep
            selectedIds={selectedSources}
            status={status}
            shopifyNotice={shopifyNotice}
            shopifyError={shopifyError}
            csvNotice={csvNotice}
            csvError={csvError}
          />
        ) : null}

        {step === 4 ? (
          <ul className="mt-4 space-y-2 text-compact text-muted-foreground">
            <li>
              You chose {selectedSources.length} source
              {selectedSources.length === 1 ? "" : "s"} — add or sync more anytime under Sources.
            </li>
            <li>Proactive feed and Decision Inbox unlock after setup.</li>
            <li>Inventory decisions stay suppressed when connectors are stale.</li>
          </ul>
        ) : null}

        {error ? (
          <p className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-caption text-destructive">
            {error}
          </p>
        ) : null}

        <div className="mt-6 flex flex-wrap gap-3">
          {step > 1 ? (
            <OrbitButton type="button" variant="ghost" onClick={() => setStep(step - 1)} disabled={busy}>
              Back
            </OrbitButton>
          ) : null}
          {step < 4 ? (
            <OrbitButton type="button" onClick={onNext} disabled={busy}>
              Continue
            </OrbitButton>
          ) : (
            <OrbitButton type="button" onClick={onComplete} disabled={busy}>
              {busy ? "Finishing…" : "Enter Trita"}
            </OrbitButton>
          )}
        </div>
      </OrbitCard>
    </div>
  );
}
