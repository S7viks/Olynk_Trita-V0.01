import Link from "next/link";

export default function HomePage() {
  return (
    <section>
      <h1 style={{ marginTop: 0 }}>Proactive feed</h1>
      <p style={{ color: "var(--muted)" }}>
        Decision Inbox and proactive cards ship in RM-2. For RM-0, connect data
        sources and verify integration health.
      </p>
      <p>
        <Link href="/sources">Open Sources →</Link>
      </p>
    </section>
  );
}
