export function PlaceholderPage({
  title,
  phase,
  description,
}: {
  title: string;
  phase: string;
  description: string;
}) {
  return (
    <section>
      <h1 style={{ marginTop: 0 }}>{title}</h1>
      <p style={{ color: "var(--muted)" }}>{description}</p>
      <p
        style={{
          display: "inline-block",
          padding: "0.35rem 0.65rem",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 6,
          fontSize: "0.85rem",
        }}
      >
        Phase {phase} — not in RM-0 scope
      </p>
    </section>
  );
}
