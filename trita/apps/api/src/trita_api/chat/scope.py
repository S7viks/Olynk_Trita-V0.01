"""Out-of-scope detection for inventory-only chat."""

from __future__ import annotations

import re

_OUT_OF_SCOPE = re.compile(
    r"(?i)\b("
    r"ad\s*strategy|advertis(e|ing)\s*strategy|marketing\s*plan|"
    r"facebook\s*ads|meta\s*ads\s*budget|legal\s*advice|lawyer|"
    r"tax\s*advice|hire\s*people|hr\s*policy|write\s*my\s*ads"
    r")\b"
)

_INVENTORY_HINT = re.compile(
    r"(?i)\b(reorder|stock|cover|inventory|sku|dead\s*stock|unicommerce|shopify\s*sync|"
    r"integration|data\s*health|inbox|decision)\b"
)


def is_out_of_scope(message: str) -> bool:
    return bool(_OUT_OF_SCOPE.search(message))


def mentions_inventory(message: str) -> bool:
    return bool(_INVENTORY_HINT.search(message))
