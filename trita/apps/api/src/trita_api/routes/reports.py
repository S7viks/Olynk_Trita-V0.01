"""Data Health report API (F-REPORT-HEALTH, VA-14)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from trita_api.auth import TenantDep
from trita_api.routes.identity import identity_stats
from trita_api.routes.integrations import integrations_health
from trita_api.routes.metrics import metrics_summary

router = APIRouter(prefix="/v1/reports", tags=["reports"])

_STATUS_RANK = {"failed": 0, "degraded": 1, "disconnected": 2, "healthy": 3}


@router.get("/health")
def data_health_report(ctx: TenantDep) -> dict[str, object]:
    """Aggregated Data Health for UI — counts from gold/feat only (no LLM math)."""
    integrations_body = integrations_health(ctx)
    integrations = list(integrations_body["integrations"])
    integrations.sort(
        key=lambda row: (
            _STATUS_RANK.get(str(row.get("status")), 9),
            str(row.get("source")),
        )
    )

    metrics = metrics_summary(ctx)
    identity = identity_stats(ctx)

    unhealthy = sum(
        1 for row in integrations if str(row.get("status")) != "healthy"
    )
    resolution = identity.get("resolution") or {}
    meets_va13 = bool(resolution.get("meets_va13"))

    return {
        "tenant_id": str(ctx.tenant_id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integrations": integrations,
        "metrics": metrics,
        "identity": identity,
        "summary": {
            "connectors_total": len(integrations),
            "connectors_unhealthy": unhealthy,
            "sku_mart_aligned": bool(metrics.get("aligned")),
            "resolution_meets_va13": meets_va13,
            "resolution_rate": resolution.get("resolution_rate"),
        },
    }
