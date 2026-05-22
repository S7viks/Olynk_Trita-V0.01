/** F-UI-NAV — seven primary routes per docs/context/product-surfaces.md */

export type NavItem = {
  href: string;
  label: string;
  phase: string;
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", phase: "2" },
  { href: "/inbox", label: "Decision Inbox", phase: "2" },
  { href: "/sources", label: "Sources", phase: "1" },
  { href: "/inventory", label: "Inventory", phase: "1" },
  { href: "/reports", label: "Reports", phase: "1" },
  { href: "/chat", label: "Chat", phase: "3" },
  { href: "/settings", label: "Settings", phase: "2" },
];
