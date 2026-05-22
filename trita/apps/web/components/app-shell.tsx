"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { OrbitButton } from "@/components/orbit/button";
import { cn } from "@/lib/cn";
import { NAV_ITEMS } from "@/lib/nav";

const REPORT_LINKS = [
  { href: "/reports", label: "Overview", exact: true },
  { href: "/reports/health", label: "Data Health" },
  { href: "/reports/aging", label: "SKU aging" },
  { href: "/reports/dead-stock", label: "Dead stock" },
  { href: "/reports/reorder", label: "Reorder queue" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isReports = pathname.startsWith("/reports");

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 flex h-screen w-[220px] shrink-0 flex-col border-r border-border bg-card/90 backdrop-blur-sm">
        <Link
          href="/"
          className="border-b border-border px-5 py-4 font-black tracking-tighter text-foreground no-underline hover:no-underline"
        >
          <span className="block text-lg">OLYNK</span>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
            Trita
          </span>
        </Link>
        <nav className="flex-1 space-y-0.5 px-2 py-3" aria-label="Main">
          {NAV_ITEMS.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "block rounded-md px-3 py-2 text-sm no-underline transition-colors",
                  active
                    ? "border border-primary/20 bg-primary/10 font-semibold text-primary"
                    : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-border px-2 py-3 space-y-0.5">
          <Link
            href="/settings"
            className={cn(
              "block rounded-md px-3 py-2 text-sm no-underline",
              pathname === "/settings"
                ? "bg-primary/10 font-semibold text-primary"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            Settings
          </Link>
          <form action="/api/auth/logout" method="post" className="px-1 pt-1">
            <OrbitButton type="submit" variant="ghost" fullWidth className="justify-start text-caption">
              Sign out
            </OrbitButton>
          </form>
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <div className="border-b border-border/80 bg-gradient-to-b from-card/90 via-background/95 to-background px-6 py-3 lg:px-8">
          <p className="text-[10px] font-black uppercase tracking-[0.25em] text-muted-foreground">
            Third Observer · Inventory intelligence
          </p>
        </div>
        <main className="mx-auto max-w-6xl animate-fade-in px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {isReports ? (
            <nav className="mb-6 flex flex-wrap gap-2" aria-label="Reports">
              {REPORT_LINKS.map((link) => {
                const active = link.exact
                  ? pathname === link.href
                  : pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={cn(
                      "rounded-md border px-3 py-1.5 text-caption no-underline",
                      active
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border text-muted-foreground hover:bg-card"
                    )}
                  >
                    {link.label}
                  </Link>
                );
              })}
            </nav>
          ) : null}
          {children}
        </main>
      </div>
    </div>
  );
}
