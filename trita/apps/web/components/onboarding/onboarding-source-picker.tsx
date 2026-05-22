"use client";

import { OrbitCard } from "@/components/orbit/card";
import {
  ONBOARDING_SOURCES,
  type OnboardingSourceDef,
} from "@/lib/onboarding-sources";

type Props = {
  selected: string[];
  onChange: (ids: string[]) => void;
};

export function OnboardingSourcePicker({ selected, onChange }: Props) {
  function toggle(id: string) {
    const def = ONBOARDING_SOURCES.find((s) => s.id === id);
    if (!def || def.kind === "soon") return;
    if (selected.includes(id)) {
      onChange(selected.filter((x) => x !== id));
    } else {
      onChange([...selected, id]);
    }
  }

  return (
    <div className="mt-4 space-y-2">
      <p className="text-compact text-muted-foreground">
        Choose what you use today. Next step connects OAuth sources and uploads CSVs — you can add
        more later from Sources.
      </p>
      <ul className="space-y-2">
        {ONBOARDING_SOURCES.map((source) => (
          <SourceRow
            key={source.id}
            source={source}
            checked={selected.includes(source.id)}
            onToggle={() => toggle(source.id)}
          />
        ))}
      </ul>
      {selected.length === 0 ? (
        <p className="text-caption text-destructive">Select at least one source to continue.</p>
      ) : null}
    </div>
  );
}

function SourceRow({
  source,
  checked,
  onToggle,
}: {
  source: OnboardingSourceDef;
  checked: boolean;
  onToggle: () => void;
}) {
  const disabled = source.kind === "soon";
  const badge =
    source.kind === "oauth"
      ? "OAuth"
      : source.kind === "csv"
        ? "CSV upload"
        : "Soon";

  return (
    <li>
      <OrbitCard
        variant="glass"
        className={`!p-3 transition-colors ${checked ? "ring-2 ring-primary/40" : ""} ${disabled ? "opacity-60" : "cursor-pointer"}`}
      >
        <label
          className={`flex gap-3 ${disabled ? "cursor-not-allowed" : "cursor-pointer"}`}
        >
          <input
            type="checkbox"
            className="mt-1"
            checked={checked}
            disabled={disabled}
            onChange={onToggle}
          />
          <span className="min-w-0 flex-1">
            <span className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-bold">{source.label}</span>
              {source.recommended ? (
                <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-black uppercase tracking-wide text-primary">
                  Recommended
                </span>
              ) : null}
              <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold uppercase text-muted-foreground">
                {badge}
              </span>
            </span>
            <span className="mt-0.5 block text-caption text-muted-foreground">
              {source.description}
            </span>
          </span>
        </label>
      </OrbitCard>
    </li>
  );
}
