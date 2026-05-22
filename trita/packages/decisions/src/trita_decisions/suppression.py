"""Dedup + weekly cap (F-DEC-002)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

WEEKLY_CAP = 7
ROLLING_DAYS = 7


def count_cards_last_7_days(cur, tenant_id: UUID, *, as_of: datetime | None = None) -> int:
    since = (as_of or datetime.now(UTC)) - timedelta(days=ROLLING_DAYS)
    cur.execute(
        """
        SELECT count(*) FROM public.decisions
        WHERE tenant_id = %s AND created_at >= %s
        """,
        (tenant_id, since),
    )
    return int(cur.fetchone()[0])


def suppression_key_exists(cur, tenant_id: UUID, suppression_key: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM public.decisions
        WHERE tenant_id = %s AND suppression_key = %s
        LIMIT 1
        """,
        (tenant_id, suppression_key),
    )
    return cur.fetchone() is not None


def remaining_weekly_quota(cur, tenant_id: UUID) -> int:
    used = count_cards_last_7_days(cur, tenant_id)
    return max(0, WEEKLY_CAP - used)
