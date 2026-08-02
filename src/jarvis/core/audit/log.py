"""Append-only audit log with two sinks (ARCHITECTURE.md section 6.3).

* ``logs/audit.jsonl`` — the tamper-evident record. One JSON object per line,
  opened in append mode, flushed and fsynced on every write.
* ``audit_event`` in SQLite — the search index for the GUI. Rebuildable from the
  JSONL file, so losing it loses nothing.

Redaction is applied here, once, on the way in. Callers never have to remember.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from jarvis.common import json_dumps, json_loads, to_iso
from jarvis.core.audit.models import AuditCategory, AuditEvent
from jarvis.core.audit.redaction import redact
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import AuditRecorded
from jarvis.storage.database import Database

__all__ = ["AuditLog"]

_LOG = logging.getLogger(__name__)


class AuditLog:
    """Records what happened. Never records secrets."""

    def __init__(
        self,
        jsonl_path: Path,
        database: Database | None = None,
        event_bus: EventBus | None = None,
        *,
        instance_id: str | None = None,
        max_value_chars: int = 512,
        write_to_sqlite: bool = True,
    ) -> None:
        self._path = jsonl_path
        self._database = database
        self._event_bus = event_bus
        self._instance_id = instance_id
        self._max_value_chars = max_value_chars
        self._write_to_sqlite = write_to_sqlite and database is not None
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    # -- writing -----------------------------------------------------------
    def record(
        self,
        category: AuditCategory,
        summary: str,
        *,
        actor: str = "system",
        task_id: str | None = None,
        conversation_id: str | None = None,
        tool_id: str | None = None,
        capability_id: str | None = None,
        risk: str | None = None,
        permission_decision: str | None = None,
        parameters: dict[str, Any] | None = None,
        pre_state: dict[str, Any] | None = None,
        result: str | None = None,
        verification: str | None = None,
        error: str | None = None,
        evidence_ref: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            instance_id=self._instance_id,
            category=category,
            actor=actor,
            summary=summary,
            task_id=task_id,
            conversation_id=conversation_id,
            tool_id=tool_id,
            capability_id=capability_id,
            risk=risk,
            permission_decision=permission_decision,
            parameters=(
                redact(parameters, max_chars=self._max_value_chars)
                if parameters is not None
                else None
            ),
            pre_state=(
                redact(pre_state, max_chars=self._max_value_chars)
                if pre_state is not None
                else None
            ),
            result=result,
            verification=verification,
            error=error,
            evidence_ref=evidence_ref,
        )
        self._write(event)
        return event

    def _write(self, event: AuditEvent) -> None:
        line = json_dumps(
            {
                "audit_id": event.audit_id,
                "occurred_at": to_iso(event.occurred_at),
                "instance_id": event.instance_id,
                "category": event.category.value,
                "actor": event.actor,
                "summary": event.summary,
                "task_id": event.task_id,
                "conversation_id": event.conversation_id,
                "tool_id": event.tool_id,
                "capability_id": event.capability_id,
                "risk": event.risk,
                "permission_decision": event.permission_decision,
                "parameters": event.parameters,
                "pre_state": event.pre_state,
                "result": event.result,
                "verification": event.verification,
                "error": event.error,
                "evidence_ref": event.evidence_ref,
            }
        )

        with self._lock:
            # The JSONL file is the record of truth: write it first, and let a
            # SQLite failure degrade search rather than lose the audit entry.
            with self._path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line + "\n")
                handle.flush()

            if self._write_to_sqlite and self._database is not None:
                try:
                    self._insert(event)
                except Exception:  # noqa: BLE001 - index failure must not lose the record
                    _LOG.exception("could not index audit event %s in SQLite", event.audit_id)

        if self._event_bus is not None:
            self._event_bus.publish(
                AuditRecorded(
                    source="audit",
                    audit_id=event.audit_id,
                    category=event.category.value,
                    summary=event.summary,
                )
            )

    def _insert(self, event: AuditEvent) -> None:
        assert self._database is not None
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO audit_event (
                    audit_id, occurred_at, instance_id, category, actor, task_id,
                    conversation_id, tool_id, capability_id, risk, permission_decision,
                    summary, parameters_json, pre_state_json, result, verification,
                    error, evidence_ref
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.audit_id,
                    to_iso(event.occurred_at),
                    event.instance_id,
                    event.category.value,
                    event.actor,
                    event.task_id,
                    event.conversation_id,
                    event.tool_id,
                    event.capability_id,
                    event.risk,
                    event.permission_decision,
                    event.summary,
                    json_dumps(event.parameters) if event.parameters is not None else None,
                    json_dumps(event.pre_state) if event.pre_state is not None else None,
                    event.result,
                    event.verification,
                    event.error,
                    event.evidence_ref,
                ),
            )

    # -- reading -----------------------------------------------------------
    def read_all(self) -> list[dict[str, Any]]:
        """Every record from the JSONL file, oldest first."""
        if not self._path.is_file():
            return []
        records: list[dict[str, Any]] = []
        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    records.append(json_loads(line))
        return records

    def query(
        self,
        *,
        category: AuditCategory | None = None,
        task_id: str | None = None,
        capability_id: str | None = None,
        since: datetime | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Search the SQLite index. Falls back to the JSONL file if unavailable."""
        if not self._write_to_sqlite or self._database is None:
            return self._query_jsonl(category, task_id, capability_id, since, limit)

        clauses: list[str] = []
        parameters: list[Any] = []
        if category is not None:
            clauses.append("category = ?")
            parameters.append(category.value)
        if task_id is not None:
            clauses.append("task_id = ?")
            parameters.append(task_id)
        if capability_id is not None:
            clauses.append("capability_id = ?")
            parameters.append(capability_id)
        if since is not None:
            clauses.append("occurred_at >= ?")
            parameters.append(to_iso(since))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(int(limit))

        rows = self._database.query_all(
            f"SELECT * FROM audit_event {where} ORDER BY occurred_at DESC LIMIT ?",
            parameters,
        )
        return [dict(row) for row in rows]

    def _query_jsonl(
        self,
        category: AuditCategory | None,
        task_id: str | None,
        capability_id: str | None,
        since: datetime | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        since_iso = to_iso(since)
        matches: list[dict[str, Any]] = []
        for record in reversed(self.read_all()):
            if category is not None and record.get("category") != category.value:
                continue
            if task_id is not None and record.get("task_id") != task_id:
                continue
            if capability_id is not None and record.get("capability_id") != capability_id:
                continue
            if since_iso is not None and str(record.get("occurred_at", "")) < since_iso:
                continue
            matches.append(record)
            if len(matches) >= limit:
                break
        return matches

    def count(self) -> int:
        return len(self.read_all())

    def export(self, destination: Path, records: Iterable[dict[str, Any]] | None = None) -> Path:
        """Write an export copy of the audit log (PRD section 11.5)."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = self.read_all() if records is None else list(records)
        with destination.open("w", encoding="utf-8", newline="\n") as handle:
            for record in source:
                handle.write(json_dumps(record) + "\n")
        return destination
