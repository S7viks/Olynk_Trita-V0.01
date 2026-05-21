"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_ITEMS } from "@/lib/nav";

export function AppNav() {
  const pathname = usePathname();

  return (
    <header
      style={{
        borderBottom: "1px solid var(--border)",
        background: "var(--surface)",
      }}
    >
      <nav
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.25rem 1rem",
          alignItems: "center",
          maxWidth: 960,
          margin: "0 auto",
          padding: "0.75rem 1.25rem",
        }}
      >
        <Link
          href="/sources"
          style={{
            fontWeight: 700,
            color: "var(--text)",
            marginRight: "0.5rem",
          }}
        >
          Trita
        </Link>
        {NAV_ITEMS.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{
                color: active ? "var(--text)" : "var(--muted)",
                fontWeight: active ? 600 : 400,
                fontSize: "0.9rem",
              }}
            >
              {item.label}
              {item.phase !== "0" && item.href !== "/sources" ? (
                <span
                  style={{
                    marginLeft: "0.35rem",
                    fontSize: "0.7rem",
                    color: "var(--muted)",
                  }}
                >
                  P{item.phase}
                </span>
              ) : null}
            </Link>
          );
        })}
        <form action="/api/auth/logout" method="post" style={{ marginLeft: "auto" }}>
          <button
            type="submit"
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--muted)",
              padding: "0.35rem 0.75rem",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: "0.85rem",
            }}
          >
            Sign out
          </button>
        </form>
      </nav>
    </header>
  );
}
