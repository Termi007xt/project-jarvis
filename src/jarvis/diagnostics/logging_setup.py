"""Structured application logging.

Separate from the audit log. The audit log records *what the agent did* and is a
user-facing, redacted, append-only record. This is ordinary diagnostic logging
for developers: it goes to ``logs/app.log`` and to the console.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

__all__ = ["configure_logging"]

_FORMAT = "%(asctime)s %(levelname)-8s %(threadName)-20s %(name)-38s %(message)s"


def configure_logging(
    log_path: Path,
    level: str = "INFO",
    *,
    console: bool = True,
    max_bytes: int = 2_000_000,
    backup_count: int = 3,
) -> logging.Logger:
    """Configure the root logger once. Idempotent."""
    root = logging.getLogger()
    if getattr(root, "_jarvis_configured", False):
        return root

    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    formatter = logging.Formatter(_FORMAT)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    root._jarvis_configured = True  # type: ignore[attr-defined]
    return root
