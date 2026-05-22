"""Chat message handler — grounded or refuse (F-CHAT-001)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from trita_api.chat.context import build_context_projection, resolve_sku_hint
from trita_api.chat.scope import is_out_of_scope, mentions_inventory


def _refuse(code: str, message: str, *, evidence_refs: list[str] | None = None) -> dict[str, Any]:
    return {
        "refused": True,
        "refusal_code": code,
        "answer": message,
        "evidence_refs": evidence_refs or [],
        "source": "policy",
    }


def _template_answer(projection: dict[str, Any], user_message: str) -> str:
    blocks = projection.get("blocks") or []
    if not blocks:
        return (
            "I only answer inventory questions grounded in your Trita graph. "
            "Connect sources and run metrics, then ask about a SKU code or open Inbox cards."
        )
    intro = "Here is what your tenant graph shows (deterministic metrics, not estimates):"
    body = "\n".join(f"• {b}" for b in blocks)
    if "reorder" in user_message.lower() and projection.get("sku_resolved"):
        return (
            f"{intro}\n{body}\n\n"
            "For reorder quantity, use the Decision Inbox recommendation (Tier 1) — "
            "I do not compute order quantities in chat."
        )
    return f"{intro}\n{body}"


def handle_chat_message(
    cur,
    *,
    tenant_id: UUID,
    message: str,
    integrity_suppressed: bool = False,
    integrity_source: str | None = None,
    use_llm: bool = True,
) -> dict[str, Any]:
    text = (message or "").strip()
    if not text:
        return _refuse("empty_message", "Please enter a question about inventory.")

    if is_out_of_scope(text):
        return _refuse(
            "out_of_scope",
            "I only help with inventory, SKU cover, reorder rationale, dead stock, "
            "reports, and integration freshness — not ads strategy or legal topics.",
        )

    if integrity_suppressed:
        return _refuse(
            "data_stale",
            f"Data integrity suppress is active ({integrity_source or 'connector'}). "
            "Resync sources before trusting inventory answers.",
            evidence_refs=["public.integration_health:latest"],
        )

    sku_hint = resolve_sku_hint(text)
    if sku_hint is None and not mentions_inventory(text):
        return _refuse(
            "needs_inventory_context",
            "Ask about a specific SKU code, stockout risk, dead stock, Data Health, or Inbox decisions.",
        )

    projection = build_context_projection(cur, tenant_id, sku_hint=sku_hint)
    if sku_hint and not projection.get("sku_resolved"):
        return _refuse(
            "sku_not_found",
            f"SKU '{sku_hint}' is not in your tenant graph for the latest metric date.",
        )

    if not projection.get("evidence_refs"):
        return _refuse(
            "no_evidence",
            "No grounded evidence available yet. Run ingest and dbt metrics first.",
        )

    evidence_refs = list(projection["evidence_refs"])

    if use_llm:
        try:
            from trita_api.llm_client import complete_draft

            prompt = (
                "Answer using ONLY the context below. Do not invent numbers. "
                "If context is insufficient, say what is missing.\n\n"
                f"Context:\n" + "\n".join(projection.get("blocks") or [])
                + f"\n\nUser: {text}"
            )
            llm = complete_draft(tenant_id=tenant_id, prompt=prompt, purpose="chat")
            answer = str(llm.get("text") or "")
            if llm.get("source") == "fallback" and llm.get("reason") == "inventory_numbers_in_output":
                answer = _template_answer(projection, text)
                source = "template"
            else:
                source = str(llm.get("source") or "litellm")
            return {
                "refused": False,
                "answer": answer,
                "evidence_refs": evidence_refs,
                "source": source,
                "context_blocks": projection.get("blocks"),
            }
        except Exception:
            pass

    return {
        "refused": False,
        "answer": _template_answer(projection, text),
        "evidence_refs": evidence_refs,
        "source": "template",
        "context_blocks": projection.get("blocks"),
    }
