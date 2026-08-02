"""Small shared primitives used across every layer.

Kept deliberately tiny: identifiers, UTC time and JSON helpers. Anything larger
belongs to a real module.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

__all__ = ["new_id", "utc_now", "to_iso", "from_iso", "json_dumps", "json_loads"]


def new_id() -> str:
    """A fresh opaque identifier. UUID4 hex, no dashes, stable length."""
    return uuid.uuid4().hex


def utc_now() -> datetime:
    """Timezone-aware current time. Never use ``datetime.utcnow()``."""
    return datetime.now(timezone.utc)


def to_iso(value: datetime | None) -> str | None:
    """Serialise to ISO-8601 with an explicit offset, or ``None``."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def from_iso(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp written by :func:`to_iso`."""
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def json_dumps(value: Any) -> str:
    """Deterministic JSON for storage and for the append-only audit log."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def json_loads(value: str | None) -> Any:
    if value is None or value == "":
        return None
    return json.loads(value)
