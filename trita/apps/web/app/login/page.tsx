import { LoginForm } from "./login-form";

export default function LoginPage({
  searchParams,
}: {
  searchParams: { next?: string; error?: string };
}) {
  const next = searchParams.next ?? "/sources";
  return (
    <main
      style={{
        maxWidth: 420,
        margin: "4rem auto",
        padding: "0 1.25rem",
      }}
    >
      <h1 style={{ marginTop: 0 }}>Sign in to Trita</h1>
      <p style={{ color: "var(--muted)" }}>
        Supabase Auth when configured; local pilot uses Yoga Bar dev token.
      </p>
      {searchParams.error ? (
        <p style={{ color: "var(--failed)" }}>{searchParams.error}</p>
      ) : null}
      <LoginForm nextPath={next} />
    </main>
  );
}
