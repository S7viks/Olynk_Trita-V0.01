"""SKU metrics API (F-METRICS-001..004) — read-only from feat mart."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, HTTPException, Query, status

from trita_api.auth import TenantDep
from trita_api.db import database_url

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get("/sku")
def list_sku_metrics(
    ctx: TenantDep,
    sort: str = Query(default="days_of_cover", pattern="^(days_of_cover|aging_days|capital_at_risk|velocity_7d|sku_code)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    stockout_only: bool = False,
    dead_stock_only: bool = False,
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, object]:
    """Inventory list backing (F-UI-INVENTORY-LIST)."""
    direction = "ASC" if order == "asc" else "DESC"
    clauses = ["tenant_id = %s", "metric_date = (SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s)"]
    params: list[object] = [ctx.tenant_id, ctx.tenant_id]
    if stockout_only:
        clauses.append("stockout_risk = true")
    if dead_stock_only:
        clauses.append("dead_stock = true")
    where_sql = " AND ".join(clauses)
    sql = f"""
        SELECT
            canonical_sku_id, sku_code, on_hand, velocity_7d, velocity_30d,
            days_of_cover, aging_days, unit_cost, capital_at_risk, cogs_missing,
            stockout_risk, dead_stock, reorder_qty, metric_date
        FROM feat.sku_metrics_daily
        WHERE {where_sql}
        ORDER BY {sort} {direction} NULLS LAST
        LIMIT %s
    """
    params.append(limit)
    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Metrics mart unavailable: {exc}",
        ) from exc

    items = [
        {
            "canonical_sku_id": r[0],
            "sku_code": r[1],
            "on_hand": float(r[2]) if r[2] is not None else None,
            "velocity_7d": float(r[3]) if r[3] is not None else None,
            "velocity_30d": float(r[4]) if r[4] is not None else None,
            "days_of_cover": float(r[5]) if r[5] is not None else None,
            "aging_days": int(r[6]) if r[6] is not None else None,
            "unit_cost": float(r[7]) if r[7] is not None else None,
            "capital_at_risk": float(r[8]) if r[8] is not None else None,
            "cogs_missing": bool(r[9]),
            "stockout_risk": bool(r[10]),
            "dead_stock": bool(r[11]),
            "reorder_qty": float(r[12]) if r[12] is not None else None,
            "metric_date": r[13].isoformat() if r[13] else None,
        }
        for r in rows
    ]
    return {"tenant_id": str(ctx.tenant_id), "count": len(items), "items": items}


@router.get("/summary")
def metrics_summary(ctx: TenantDep) -> dict[str, object]:
    """Data Health / report aggregates (VA-14 backing)."""
    sql = """
        SELECT
            count(*) AS sku_count,
            count(*) FILTER (WHERE stockout_risk) AS stockout_risk_count,
            count(*) FILTER (WHERE dead_stock) AS dead_stock_count,
            count(*) FILTER (WHERE cogs_missing) AS cogs_missing_count,
            coalesce(sum(capital_at_risk), 0) AS capital_at_risk_total,
            max(metric_date) AS metric_date
        FROM feat.sku_metrics_daily
        WHERE tenant_id = %s
          AND metric_date = (
              SELECT max(metric_date) FROM feat.sku_metrics_daily WHERE tenant_id = %s
          )
    """
    try:
        with psycopg.connect(database_url(), autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (ctx.tenant_id, ctx.tenant_id))
                row = cur.fetchone()
                cur.execute(
                    "SELECT count(*) FROM gold.dim_sku WHERE tenant_id = %s",
                    (ctx.tenant_id,),
                )
                dim_sku_count = int(cur.fetchone()[0])
    except psycopg.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Metrics summary unavailable: {exc}",
        ) from exc

    if not row or row[0] is None:
        return {
            "tenant_id": str(ctx.tenant_id),
            "metric_date": None,
            "sku_count": 0,
            "dim_sku_count": dim_sku_count,
            "aligned": False,
        }

    sku_count = int(row[0])
    return {
        "tenant_id": str(ctx.tenant_id),
        "metric_date": row[5].isoformat() if row[5] else None,
        "sku_count": sku_count,
        "dim_sku_count": dim_sku_count,
        "aligned": sku_count == dim_sku_count,
        "stockout_risk_count": int(row[1]),
        "dead_stock_count": int(row[2]),
        "cogs_missing_count": int(row[3]),
        "capital_at_risk_total": float(row[4]),
    }
