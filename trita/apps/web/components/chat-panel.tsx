"use client";

import { useState } from "react";

type ChatResponse = {
  refused: boolean;
  refusal_code?: string;
  answer: string;
  evidence_refs: string[];
  source?: string;
};

export function ChatPanel() {
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResponse | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const body = (await res.json()) as ChatResponse & { detail?: string };
      if (!res.ok) {
        throw new Error(body.detail ?? `Chat failed (${res.status})`);
      }
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Chat failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <form onSubmit={onSubmit} style={{ marginBottom: "1rem" }}>
        <label className="ui-label" htmlFor="chat-message">
          Ask about inventory (SKU code, cover, Inbox, integrations)
        </label>
        <textarea
          id="chat-message"
          className="ui-textarea"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={4}
          style={{ maxWidth: "36rem" }}
          placeholder="e.g. What is stockout risk for YB-001?"
        />
        <div style={{ marginTop: "0.5rem" }}>
          <button
            type="submit"
            className="ui-btn ui-btn-primary"
            disabled={loading || !message.trim()}
          >
            {loading ? "Thinking…" : "Send"}
          </button>
        </div>
      </form>

      {error ? <p className="ui-alert ui-alert-error">{error}</p> : null}

      {result ? (
        <div
          className="ui-card"
          style={{
            borderColor: result.refused ? "var(--degraded)" : "var(--healthy)",
            maxWidth: "42rem",
          }}
        >
          {result.refused ? (
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--degraded)" }}>
              Refused ({result.refusal_code})
            </p>
          ) : (
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--muted)" }}>
              Source: {result.source ?? "unknown"}
            </p>
          )}
          <p style={{ margin: "0.75rem 0 0", whiteSpace: "pre-wrap", fontSize: "0.9rem" }}>
            {result.answer}
          </p>
          {result.evidence_refs?.length ? (
            <section style={{ marginTop: "1rem" }}>
              <h3 style={{ fontSize: "0.85rem", margin: "0 0 0.35rem" }}>Evidence</h3>
              <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.8rem" }}>
                {result.evidence_refs.map((ref) => (
                  <li key={ref}>
                    <code>{ref}</code>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
