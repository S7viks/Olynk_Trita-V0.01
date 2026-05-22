import { type ButtonHTMLAttributes, forwardRef } from "react";

import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost";

const variants: Record<Variant, string> = {
  primary:
    "bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100",
  secondary:
    "border border-border bg-secondary text-foreground hover:bg-muted",
  ghost: "text-muted-foreground hover:bg-muted/60 hover:text-foreground",
};

export const OrbitButton = forwardRef<
  HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: Variant;
    fullWidth?: boolean;
  }
>(function OrbitButton(
  { className, variant = "primary", fullWidth, type = "button", ...props },
  ref
) {
  return (
    <button
      ref={ref}
      type={type}
      className={cn(
        "inline-flex h-9 items-center justify-center gap-2 rounded-md px-4 text-sm font-semibold transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50",
        "touch-target min-h-[44px] sm:min-h-9",
        variants[variant],
        fullWidth && "w-full",
        className
      )}
      {...props}
    />
  );
});
