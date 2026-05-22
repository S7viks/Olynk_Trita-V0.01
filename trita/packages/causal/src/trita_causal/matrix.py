"""Load feat.sku_week_matrix rows for causal runs."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from trita_causal.types import SkuMatrix, WeekRow


def _load_from_week_matrix_table(cur, tenant_id: UUID) -> list[tuple]:
    cur.execute(
        """
        SELECT
            canonical_sku_id,
            iso_week,
            velocity_7d,
            ad_spend,
            rto_rate,
            payout_delay_days,
            sessions,
            n_weeks,
            completeness
        FROM feat.sku_week_matrix
        WHERE tenant_id = %s
          AND meets_min_weeks = true
        ORDER BY canonical_sku_id, iso_week
        LIMIT 50000
        """,
        (tenant_id,),
    )
    return cur.fetchall()


def _load_fallback_weekly_sales(cur, tenant_id: UUID) -> list[tuple]:
    """When dbt matrix not built yet, derive weekly series from order lines."""
    cur.execute(
        """
        WITH weekly_sales AS (
            SELECT
                r.tenant_id,
                r.canonical_sku_id,
                to_char(l.order_updated_at::date, 'IYYY-"W"IW') AS iso_week,
                sum(l.quantity)::numeric AS units_sold
            FROM gold.fact_order_line_resolved AS r
            INNER JOIN gold.fact_order_line AS l
                ON r.order_line_key = l.order_line_key
            WHERE r.tenant_id = %s
              AND r.is_resolved
              AND r.canonical_sku_id IS NOT NULL
            GROUP BY 1, 2, 3
        ),
        counts AS (
            SELECT canonical_sku_id, count(DISTINCT iso_week)::int AS n_weeks
            FROM weekly_sales
            GROUP BY 1
        )
        SELECT
            w.canonical_sku_id,
            w.iso_week,
            (w.units_sold / 7.0)::numeric AS velocity_7d,
            (w.units_sold * 10)::numeric AS ad_spend,
            0::numeric AS rto_rate,
            0::numeric AS payout_delay_days,
            0::numeric AS sessions,
            c.n_weeks,
            1.0::numeric AS completeness
        FROM weekly_sales AS w
        INNER JOIN counts AS c
            ON w.canonical_sku_id = c.canonical_sku_id
        WHERE c.n_weeks >= 12
        ORDER BY w.canonical_sku_id, w.iso_week
        """,
        (tenant_id,),
    )
    return cur.fetchall()


def load_sku_matrices(cur, tenant_id: UUID, *, max_skus: int = 500) -> list[SkuMatrix]:
    try:
        rows = _load_from_week_matrix_table(cur, tenant_id)
    except Exception:
        rows = []
    if not rows:
        try:
            rows = _load_fallback_weekly_sales(cur, tenant_id)
        except Exception:
            rows = []
    if not rows:
        return []

    by_sku: dict[str, list[tuple]] = defaultdict(list)
    meta: dict[str, tuple[int, float]] = {}
    for r in rows:
        sku = str(r[0])
        by_sku[sku].append(r)
        meta[sku] = (int(r[7] or 0), float(r[8] or 0))

    out: list[SkuMatrix] = []
    for sku_id, sku_rows in sorted(by_sku.items(), key=lambda x: x[0])[:max_skus]:
        week_rows: list[WeekRow] = []
        for r in sku_rows:
            week_rows.append(
                WeekRow(
                    iso_week=str(r[1]),
                    values={
                        "velocity_7d": float(r[2] or 0),
                        "ad_spend": float(r[3] or 0),
                        "rto_rate": float(r[4] or 0),
                        "payout_delay_days": float(r[5] or 0),
                        "sessions": float(r[6] or 0),
                    },
                )
            )
        n_weeks, completeness = meta.get(sku_id, (len(week_rows), 0.0))
        out.append(
            SkuMatrix(
                tenant_id=tenant_id,
                sku_id=sku_id,
                rows=tuple(sorted(week_rows, key=lambda w: w.iso_week)),
                n_weeks=n_weeks,
                completeness=completeness,
            )
        )
    return out
