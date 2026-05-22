import { cn } from "@/lib/cn";

type Tone = "error" | "success" | "info";

const tones: Record<Tone, string> = {
  error: "border-destructive/30 bg-destructive/10 text-destructive",
  success:
    "border-emerald-600/30 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-400",
  info: "border-primary/25 bg-primary/5 text-foreground",
};

export function AuthAlert({
  tone = "error",
  children,
  className,
}: {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "rounded-lg border px-3 py-2.5 text-[13px] leading-snug",
        tones[tone],
        className
      )}
    >
      {children}
    </p>
  );
}
