import { type HTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type Variant = "default" | "glass" | "glass-strong";

const variants: Record<Variant, string> = {
  default: "glass-strong",
  glass: "glass-card",
  "glass-strong": "glass-strong",
};

export function OrbitCard({
  className,
  variant = "default",
  ...props
}: HTMLAttributes<HTMLDivElement> & { variant?: Variant }) {
  return (
    <div
      className={cn("p-5 transition-colors duration-200", variants[variant], className)}
      {...props}
    />
  );
}
