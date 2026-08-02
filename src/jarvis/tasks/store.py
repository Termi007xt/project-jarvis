"""Durable task storage (ARCHITECTURE.md section 6.7).

State transitions are written inside a transaction together with their history
row, so the log and the current state cannot disagree. The audit record is
written after the transaction commits, because an audit entry describing a
transition that was rolled back would be a lie.
"""

from __future__ import annotations

import threading
from typing import Any, Iterable, Sequence

from jarvis.common import from_iso, json_dumps, json_loads, new_id, to_iso, utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import TaskCheckpointSaved, TaskCreated, TaskStateChanged
from jarvis.storage.database import Database
from jarvis.tasks.models import Task, TaskCheckpoint, TaskEvidence, TaskTransition
from jarvis.tasks.states import TaskState, assert_transition

__all__ = ["TaskStore", "TaskNotFoundError"]


class TaskNotFoundError(LookupError):
    """No task with that identifier exists."""


class TaskStore:
    """CRUD plus a validated state machine over the ``task`` tables."""

    def __init__(
        self,
        database: Database,
        audit: AuditLog | None = None,
        event_bus: EventBus | None = None,
        instance_id: str | None = None,
    ) -> None:
        self._database = database
        self._audit = audit
        self._events = event_bus
        self._instance_id = instance_id
        self._lock = threading.RLock()

    # -- creation ----------------------------------------------------------
    def create(
        self,
        name: str,
        goal: str,
        runner_id: str,
        *,
        parent_task_id: str | None = None,
        conversation_id: str | None = None,
        priority: int = 100,
        required_locks: Sequence[str] = (),
        payload: dict[str, Any] | None = None,
        max_retries: int = 3,
        state: TaskState = TaskState.DRAFT,
    ) -> Task:
        task = Task(
            name=name,
            goal=goal,
            runner_id=runner_id,
            parent_task_id=parent_task_id,
            conversation_id=conversation_id,
            priority=priority,
            required_locks=tuple(required_locks),
            payload=payload or {},
            max_retries=max_retries,
            state=state,
            instance_id=self._instance_id,
        )
        with self._lock, self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO task (
                    task_id, parent_task_id, conversation_id, name, goal, runner_id,
                    state, priority, required_locks_json, payload_json, attempts,
                    max_retries, waiting_on, blocked_reason, failure_code,
                    result_summary, recovered, instance_id, created_at, updated_at,
                    started_at, ended_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.parent_task_id,
                    task.conversation_id,
                    task.name,
                    task.goal,
                    task.runner_id,
                    task.state.value,
                    task.priority,
                    json_dumps(list(task.required_locks)),
                    json_dumps(task.payload),
                    task.attempts,
                    task.max_retries,
                    task.waiting_on,
                    task.blocked_reason,
                    task.failure_code,
                    task.result_summary,
                    int(task.recovered),
                    task.instance_id,
                    to_iso(task.created_at),
                    to_iso(task.updated_at),
                    to_iso(task.started_at),
                    to_iso(task.ended_at),
                ),
            )
            connection.execute(
                "INSERT INTO task_transition (transition_id, task_id, from_state, to_state, "
                "reason, occurred_at) VALUES (?, ?, ?, ?, ?, ?)",
                (new_id(), task.task_id, None, task.state.value, "created", to_iso(utc_now())),
            )

        if self._audit is not None:
            self._audit.record(
                AuditCategory.TASK,
                f"created task '{name}' in state {task.state.value}",
                task_id=task.task_id,
                conversation_id=conversation_id,
                parameters={
                    "runner_id": runner_id,
                    "required_locks": list(task.required_locks),
                    "goal": goal,
                },
            )
        if self._events is not None:
            self._events.publish(
                TaskCreated(
                    source="tasks",
                    task_id=task.task_id,
                    name=name,
                    runner_id=runner_id,
                    parent_task_id=parent_task_id,
                )
            )
        return task

    # -- reading -----------------------------------------------------------
    def get(self, task_id: str) -> Task | None:
        row = self._database.query_one("SELECT * FROM task WHERE task_id = ?", (task_id,))
        return self._row_to_task(row) if row is not None else None

    def require(self, task_id: str) -> Task:
        task = self.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"no task with id '{task_id}'")
        return task

    def list(
        self,
        states: Iterable[TaskState] | None = None,
        *,
        parent_task_id: str | None = None,
        instance_id: str | None = None,
        limit: int = 500,
    ) -> list[Task]:
        clauses: list[str] = []
        parameters: list[Any] = []
        if states is not None:
            state_values = [state.value for state in states]
            if not state_values:
                return []
            clauses.append(f"state IN ({','.join('?' * len(state_values))})")
            parameters.extend(state_values)
        if parent_task_id is not None:
            clauses.append("parent_task_id = ?")
            parameters.append(parent_task_id)
        if instance_id is not None:
            clauses.append("instance_id = ?")
            parameters.append(instance_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        parameters.append(int(limit))
        rows = self._database.query_all(
            f"SELECT * FROM task {where} ORDER BY priority ASC, created_at ASC LIMIT ?",
            parameters,
        )
        return [self._row_to_task(row) for row in rows]

    def transitions(self, task_id: str) -> list[TaskTransition]:
        rows = self._database.query_all(
            "SELECT * FROM task_transition WHERE task_id = ? ORDER BY occurred_at ASC, rowid ASC",
            (task_id,),
        )
        return [
            TaskTransition(
                transition_id=row["transition_id"],
                task_id=row["task_id"],
                from_state=TaskState(row["from_state"]) if row["from_state"] else None,
                to_state=TaskState(row["to_state"]),
                reason=row["reason"],
                occurred_at=from_iso(row["occurred_at"]),  # type: ignore[arg-type]
            )
            for row in rows
        ]

    # -- transitions -------------------------------------------------------
    def transition(
        self,
        task_id: str,
        to_state: TaskState,
        *,
        reason: str | None = None,
        actor: str = "system",
        **updates: Any,
    ) -> Task:
        """Move a task to a new state. Raises if the transition is illegal."""
        with self._lock:
            task = self.require(task_id)
            assert_transition(task.state, to_state)

            now = utc_now()
            fields: dict[str, Any] = dict(updates)
            fields["state"] = to_state
            fields["updated_at"] = now
            if to_state is TaskState.RUNNING and task.started_at is None:
                fields["started_at"] = now
            if to_state in (TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED):
                fields["ended_at"] = now
            if to_state is TaskState.RUNNING:
                fields.setdefault("waiting_on", None)
                fields["instance_id"] = self._instance_id

            updated = task.model_copy(update=fields)
            self._write(updated, transition_from=task.state, reason=reason)

        if self._audit is not None:
            self._audit.record(
                AuditCategory.TASK,
                f"task '{updated.name}' {task.state.value} -> {to_state.value}",
                actor=actor,
                task_id=task_id,
                conversation_id=updated.conversation_id,
                result=to_state.value,
                error=updated.failure_code,
                parameters={"reason": reason, "attempts": updated.attempts},
            )
        if self._events is not None:
            self._events.publish(
                TaskStateChanged(
                    source="tasks",
                    task_id=task_id,
                    from_state=task.state.value,
                    to_state=to_state.value,
                    reason=reason,
                )
            )
        return updated

    def update(self, task_id: str, **updates: Any) -> Task:
        """Change fields without moving state."""
        with self._lock:
            task = self.require(task_id)
            if "state" in updates:
                raise ValueError("use transition() to change state")
            updated = task.model_copy(update={**updates, "updated_at": utc_now()})
            self._write(updated, transition_from=None, reason=None)
        return updated

    def _write(
        self, task: Task, *, transition_from: TaskState | None, reason: str | None
    ) -> None:
        with self._database.transaction() as connection:
            connection.execute(
                """
                UPDATE task SET
                    parent_task_id = ?, conversation_id = ?, name = ?, goal = ?,
                    runner_id = ?, state = ?, priority = ?, required_locks_json = ?,
                    payload_json = ?, attempts = ?, max_retries = ?, waiting_on = ?,
                    blocked_reason = ?, failure_code = ?, result_summary = ?,
                    recovered = ?, instance_id = ?, updated_at = ?, started_at = ?,
                    ended_at = ?
                WHERE task_id = ?
                """,
                (
                    task.parent_task_id,
                    task.conversation_id,
                    task.name,
                    task.goal,
                    task.runner_id,
                    task.state.value,
                    task.priority,
                    json_dumps(list(task.required_locks)),
                    json_dumps(task.payload),
                    task.attempts,
                    task.max_retries,
                    task.waiting_on,
                    task.blocked_reason,
                    task.failure_code,
                    task.result_summary,
                    int(task.recovered),
                    task.instance_id,
                    to_iso(task.updated_at),
                    to_iso(task.started_at),
                    to_iso(task.ended_at),
                    task.task_id,
                ),
            )
            if transition_from is not None or reason is not None:
                connection.execute(
                    "INSERT INTO task_transition (transition_id, task_id, from_state, "
                    "to_state, reason, occurred_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        new_id(),
                        task.task_id,
                        transition_from.value if transition_from else None,
                        task.state.value,
                        reason,
                        to_iso(utc_now()),
                    ),
                )

    # -- checkpoints -------------------------------------------------------
    def save_checkpoint(
        self, task_id: str, label: str, state: dict[str, Any] | None = None
    ) -> TaskCheckpoint:
        with self._lock, self._database.transaction() as connection:
            row = connection.execute(
                "SELECT COALESCE(MAX(sequence), -1) AS seq FROM task_checkpoint WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            sequence = int(row["seq"]) + 1
            checkpoint = TaskCheckpoint(
                task_id=task_id, sequence=sequence, label=label, state=state or {}
            )
            connection.execute(
                "INSERT INTO task_checkpoint (checkpoint_id, task_id, sequence, label, "
                "state_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    checkpoint.checkpoint_id,
                    task_id,
                    sequence,
                    label,
                    json_dumps(checkpoint.state),
                    to_iso(checkpoint.created_at),
                ),
            )

        if self._events is not None:
            self._events.publish(
                TaskCheckpointSaved(
                    source="tasks",
                    task_id=task_id,
                    checkpoint_id=checkpoint.checkpoint_id,
                    sequence=sequence,
                    label=label,
                )
            )
        return checkpoint

    def latest_checkpoint(self, task_id: str) -> TaskCheckpoint | None:
        row = self._database.query_one(
            "SELECT * FROM task_checkpoint WHERE task_id = ? ORDER BY sequence DESC LIMIT 1",
            (task_id,),
        )
        return self._row_to_checkpoint(row) if row is not None else None

    def checkpoints(self, task_id: str) -> list[TaskCheckpoint]:
        rows = self._database.query_all(
            "SELECT * FROM task_checkpoint WHERE task_id = ? ORDER BY sequence ASC", (task_id,)
        )
        return [self._row_to_checkpoint(row) for row in rows]

    # -- evidence ----------------------------------------------------------
    def add_evidence(
        self,
        task_id: str,
        kind: str,
        summary: str,
        *,
        detail: dict[str, Any] | None = None,
        artefact_path: str | None = None,
    ) -> TaskEvidence:
        evidence = TaskEvidence(
            task_id=task_id,
            kind=kind,
            summary=summary,
            detail=detail,
            artefact_path=artefact_path,
        )
        with self._database.transaction() as connection:
            connection.execute(
                "INSERT INTO task_evidence (evidence_id, task_id, kind, summary, "
                "detail_json, artefact_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    evidence.evidence_id,
                    task_id,
                    kind,
                    summary,
                    json_dumps(detail) if detail is not None else None,
                    artefact_path,
                    to_iso(evidence.created_at),
                ),
            )
        return evidence

    def evidence(self, task_id: str) -> list[TaskEvidence]:
        rows = self._database.query_all(
            "SELECT * FROM task_evidence WHERE task_id = ? ORDER BY created_at ASC", (task_id,)
        )
        return [
            TaskEvidence(
                evidence_id=row["evidence_id"],
                task_id=row["task_id"],
                kind=row["kind"],
                summary=row["summary"],
                detail=json_loads(row["detail_json"]),
                artefact_path=row["artefact_path"],
                created_at=from_iso(row["created_at"]),  # type: ignore[arg-type]
            )
            for row in rows
        ]

    # -- row mapping -------------------------------------------------------
    @staticmethod
    def _row_to_task(row: Any) -> Task:
        data = dict(row)
        return Task(
            task_id=data["task_id"],
            parent_task_id=data["parent_task_id"],
            conversation_id=data["conversation_id"],
            name=data["name"],
            goal=data["goal"],
            runner_id=data["runner_id"],
            state=TaskState(data["state"]),
            priority=data["priority"],
            required_locks=tuple(json_loads(data["required_locks_json"]) or ()),
            payload=json_loads(data["payload_json"]) or {},
            attempts=data["attempts"],
            max_retries=data["max_retries"],
            waiting_on=data["waiting_on"],
            blocked_reason=data["blocked_reason"],
            failure_code=data["failure_code"],
            result_summary=data["result_summary"],
            recovered=bool(data["recovered"]),
            instance_id=data["instance_id"],
            created_at=from_iso(data["created_at"]),  # type: ignore[arg-type]
            updated_at=from_iso(data["updated_at"]),  # type: ignore[arg-type]
            started_at=from_iso(data["started_at"]),
            ended_at=from_iso(data["ended_at"]),
        )

    @staticmethod
    def _row_to_checkpoint(row: Any) -> TaskCheckpoint:
        data = dict(row)
        return TaskCheckpoint(
            checkpoint_id=data["checkpoint_id"],
            task_id=data["task_id"],
            sequence=data["sequence"],
            label=data["label"],
            state=json_loads(data["state_json"]) or {},
            created_at=from_iso(data["created_at"]),  # type: ignore[arg-type]
        )
