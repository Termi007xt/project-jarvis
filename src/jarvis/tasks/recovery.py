"""Crash recovery (PRD FR-006, NFR-010, NFR-011, AT-011).

On startup, work left behind by a dead runtime instance is made safe:

* tasks that were ``RUNNING`` or ``WAITING`` move to ``PAUSED`` and are marked
  ``recovered``;
* locks owned by a dead instance are released;
* nothing is resumed automatically.

The last point is the important one. Resuming blindly could repeat a
consequential external action that already happened — a message sent, a file
deleted — because the process died before it could record the result. A human
decides whether to continue (PRD NFR-011).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.common import to_iso, utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import TaskRecovered
from jarvis.storage.database import Database
from jarvis.tasks.locks import ResourceLockManager
from jarvis.tasks.states import TaskState
from jarvis.tasks.store import TaskStore

__all__ = ["RecoveryReport", "recover_interrupted_work", "register_instance", "close_instance"]

INTERRUPTED_REASON = "interrupted_by_restart"


@dataclass
class RecoveryReport:
    """What startup recovery changed. Shown to the user, not swallowed."""

    recovered_task_ids: list[str] = field(default_factory=list)
    reclaimed_locks: list[str] = field(default_factory=list)
    stale_instances: list[str] = field(default_factory=list)

    @property
    def clean_start(self) -> bool:
        return not (self.recovered_task_ids or self.reclaimed_locks)

    def describe(self) -> str:
        if self.clean_start:
            return "No interrupted work was found."
        parts = []
        if self.recovered_task_ids:
            parts.append(
                f"{len(self.recovered_task_ids)} interrupted task(s) were paused for review"
            )
        if self.reclaimed_locks:
            parts.append(f"{len(self.reclaimed_locks)} stale resource lock(s) were released")
        return "; ".join(parts) + "."


def register_instance(database: Database, instance_id: str, pid: int, app_version: str) -> None:
    """Record this launch so later launches can tell what died."""
    with database.transaction() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO runtime_instance (instance_id, pid, app_version, "
            "started_at, stopped_at) VALUES (?, ?, ?, ?, NULL)",
            (instance_id, pid, app_version, to_iso(utc_now())),
        )


def close_instance(database: Database, instance_id: str) -> None:
    """Mark a clean shutdown. An instance without this died unexpectedly."""
    with database.transaction() as connection:
        connection.execute(
            "UPDATE runtime_instance SET stopped_at = ? WHERE instance_id = ?",
            (to_iso(utc_now()), instance_id),
        )


def _live_instance_ids(database: Database, current_instance_id: str) -> list[str]:
    """Instances that never recorded a clean shutdown, excluding this one.

    Only the current instance is treated as live. Single-instance enforcement
    (PRD FR-005) guarantees no other Jarvis is running in this session, so any
    other open instance row belongs to a process that died.
    """
    rows = database.query_all(
        "SELECT instance_id FROM runtime_instance WHERE stopped_at IS NULL "
        "AND instance_id != ?",
        (current_instance_id,),
    )
    return [row["instance_id"] for row in rows]


def recover_interrupted_work(
    database: Database,
    store: TaskStore,
    locks: ResourceLockManager,
    current_instance_id: str,
    *,
    audit: AuditLog | None = None,
    event_bus: EventBus | None = None,
) -> RecoveryReport:
    """Make orphaned tasks and locks safe. Never resumes anything."""
    report = RecoveryReport()
    report.stale_instances = _live_instance_ids(database, current_instance_id)

    # 1. Tasks the previous instance was actively working on.
    for task in store.list([TaskState.RUNNING, TaskState.WAITING]):
        if task.instance_id == current_instance_id:
            continue
        previous_state = task.state
        store.transition(
            task.task_id,
            TaskState.PAUSED,
            reason=INTERRUPTED_REASON,
            actor="recovery",
            recovered=True,
            blocked_reason=(
                "The application restarted while this task was running. It has not "
                "been resumed automatically, because a step that was already taken "
                "must not be repeated. Review it before continuing."
            ),
            waiting_on="awaiting review after restart",
        )
        report.recovered_task_ids.append(task.task_id)

        if audit is not None:
            audit.record(
                AuditCategory.RECOVERY,
                f"paused interrupted task '{task.name}' after restart",
                actor="recovery",
                task_id=task.task_id,
                pre_state={
                    "state": previous_state.value,
                    "attempts": task.attempts,
                    "instance_id": task.instance_id,
                },
                result=TaskState.PAUSED.value,
            )
        if event_bus is not None:
            event_bus.publish(
                TaskRecovered(
                    source="recovery",
                    task_id=task.task_id,
                    previous_state=previous_state.value,
                    new_state=TaskState.PAUSED.value,
                    detail=INTERRUPTED_REASON,
                )
            )

    # 2. Locks whose owning instance is gone. Without this a crash while holding
    #    foreground_desktop would wedge every future automation task.
    report.reclaimed_locks = list(locks.reclaim_stale(live_instance_ids=[current_instance_id]))

    # 3. Close out the dead instance rows so the next launch does not re-report.
    if report.stale_instances:
        with database.transaction() as connection:
            for instance_id in report.stale_instances:
                connection.execute(
                    "UPDATE runtime_instance SET stopped_at = ? WHERE instance_id = ?",
                    (to_iso(utc_now()), instance_id),
                )

    if audit is not None and not report.clean_start:
        audit.record(
            AuditCategory.RECOVERY,
            f"startup recovery: {report.describe()}",
            actor="recovery",
            parameters={
                "recovered_tasks": report.recovered_task_ids,
                "reclaimed_locks": report.reclaimed_locks,
                "stale_instances": report.stale_instances,
            },
        )
    return report
