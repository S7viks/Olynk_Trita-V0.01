import Link from "next/link";

export function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <p className="auth-brand">Trita</p>
        <p className="auth-tagline">Third Observer · OLynk</p>
        <h1 style={{ margin: "0 0 0.5rem", fontSize: "1.35rem" }}>{title}</h1>
        {subtitle ? (
          <p style={{ color: "var(--muted)", fontSize: "0.9rem", margin: "0 0 1.25rem" }}>
            {subtitle}
          </p>
        ) : null}
        {children}
        {footer ? (
          <div style={{ marginTop: "1.25rem", fontSize: "0.9rem", color: "var(--muted)" }}>
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function AuthFooterLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link href={href} style={{ color: "var(--accent)" }}>
      {children}
    </Link>
  );
}
