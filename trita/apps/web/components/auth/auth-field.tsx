import { type InputHTMLAttributes, forwardRef, useId } from "react";

import { cn } from "@/lib/cn";

export const AuthField = forwardRef<
  HTMLInputElement,
  InputHTMLAttributes<HTMLInputElement> & {
    label: string;
    hint?: string;
    error?: string;
  }
>(function AuthField({ label, hint, error, className, id, ...props }, ref) {
  const autoId = useId();
  const fieldId = id ?? autoId;

  return (
    <div>
      <label
        htmlFor={fieldId}
        className="text-[10px] font-black uppercase tracking-widest text-muted-foreground"
      >
        {label}
      </label>
      <input
        ref={ref}
        id={fieldId}
        className={cn(
          "mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2.5 text-sm text-foreground",
          "placeholder:text-muted-foreground/70",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-primary/25",
          error && "border-destructive/50 focus:ring-destructive/20",
          className
        )}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${fieldId}-error` : hint ? `${fieldId}-hint` : undefined}
        {...props}
      />
      {hint && !error ? (
        <p id={`${fieldId}-hint`} className="mt-1 text-[11px] text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${fieldId}-error`} className="mt-1 text-[11px] text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
});
