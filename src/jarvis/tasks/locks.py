"""Resource locks (PRD FR-124, section 7.1).

Only one task may hold a given named resource. The database primary key *is* the
mutual exclusion: one row per lock name, or no row.

Acquisition is all-or-nothing over a canonically sorted lock set, which is what
prevents two tasks deadlocking by taking the same locks in different orders.

Locks record the owning runtime instance, so a crash leaves an identifiable
stale row that startup recovery reclaims rather than a permanently wedged
resource.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from typing import Sequence

from jarvis.common import from_iso, to_iso, utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import LockAcquired, LockContended, LockReleased, StaleLockReclaimed
from jarvis.storage.database import Database
from jarvis.tasks.models import ResourceLockRecord

__all__ = ["ResourceLockManager", "LockSetLease", "KNOWN_LOCK_PREFIXES", "FOREGROUND_DESKTOP"]

#: The single most contended lock: at most one task may drive the mouse and
#: keyboard at a time (PRD section 7.1).
FOREGROUND_DESKTOP = "foreground_desktop"

#: Lock names are either an exact name or ``prefix:reference``.
KNOWN_LOCK_PREFIXES: frozenset[str] = frozenset(
    {
        "foreground_desktop",
        "browser_profile",
        "microphone_capture",
        "speaker_output",
        "clipboard",
        "application",
        "folder_scope",
        "network_connector",
    }
)


class LockSetLease:
    """A held set of locks. Release is idempotent."""

    __slots__ = ("owner_id", "lock_names", "_manager", "_released")

    def __init__(self, manager: "ResourceLockManager", owner_id: str, lock_names: tuple[str, ...]) -> None:
        self._manager = manager
        self.owner_id = owner_id
        self.lock_names = lock_names
        self._released = False

    def release(self) -> None:
        if not self._released:
            self._released = True
            self._manager.release(self.owner_id, self.lock_names)

    @property
    def released(self) -> bool:
        return self._released

    def __enter__(self) -> "LockSetLease":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.release()


def validate_lock_name(name: str) -> str:
    prefix = name.split(":", 1)[0]
    if prefix not in KNOWN_LOCK_PREFIXES:
        raise ValueError(
            f"unknown resource lock '{name}'. Known prefixes: "
            f"{sorted(KNOWN_LOCK_PREFIXES)}"
        )
    return name


class ResourceLockManager:
    """Exclusive, persisted, owner-attributed locks."""

    def __init__(
        self,
        database: Database,
        instance_id: str,
        audit: AuditLog | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._database = database
        self._instance_id = instance_id
        self._audit = audit
        self._events = event_bus
        self._lock = threading.RLock()

    @property
    def instance_id(self) -> str:
        return self._instance_id

    # -- acquisition -------------------------------------------------------
    def acquire(
        self, owner_id: str, lock_names: Sequence[str], timeout_seconds: float = 0.0
    ) -> LockSetLease | None:
        """Take the whole set or nothing. Returns ``None`` if unavailable."""
        if not lock_names:
            return LockSetLease(self, owner_id, ())

        ordered = tuple(sorted({validate_lock_name(name) for name in lock_names}))
        deadline = time.monotonic() + max(0.0, timeout_seconds)

        while True:
            with self._lock:
                acquired = self._try_acquire_all(owner_id, ordered)
            if acquired:
                if self._audit is not None:
                    self._audit.record(
                        AuditCategory.LOCK,
                        f"acquired locks {list(ordered)}",
                        task_id=owner_id,
                        parameters={"locks": list(ordered)},
                    )
                if self._events is not None:
                    self._events.publish(
                        LockAcquired(source="locks", task_id=owner_id, lock_names=ordered)
                    )
                return LockSetLease(self, owner_id, ordered)

            if time.monotonic() >= deadline:
                return None
            time.sleep(0.02)

    def _try_acquire_all(self, owner_id: str, ordered: tuple[str, ...]) -> bool:
        try:
            with self._database.transaction() as connection:
                for name in ordered:
                    row = connection.execute(
                        "SELECT task_id FROM resource_lock WHERE lock_name = ?", (name,)
                    ).fetchone()
                    if row is not None:
                        if row["task_id"] == owner_id:
                            continue  # reentrant for the same owner
                        if self._events is not None:
                            self._events.publish(
                                LockContended(
                                    source="locks",
                                    task_id=owner_id,
                                    lock_name=name,
                                    held_by_task_id=row["task_id"],
                                )
                            )
                        raise _Contended(name)
                    connection.execute(
                        "INSERT INTO resource_lock (lock_name, task_id, instance_id, acquired_at) "
                        "VALUES (?, ?, ?, ?)",
                        (name, owner_id, self._instance_id, to_iso(utc_now())),
                    )
            return True
        except _Contended:
            return False
        except sqlite3.IntegrityError:
            # Another thread inserted between the SELECT and the INSERT.
            return False

    # -- release -----------------------------------------------------------
    def release(self, owner_id: str, lock_names: Sequence[str] | None = None) -> tuple[str, ...]:
        """Release named locks, or every lock held by ``owner_id``."""
        with self._lock, self._database.transaction() as connection:
            if lock_names is None:
                rows = connection.execute(
                    "SELECT lock_name FROM resource_lock WHERE task_id = ?", (owner_id,)
                ).fetchall()
                names = tuple(sorted(row["lock_name"] for row in rows))
            else:
                names = tuple(sorted(set(lock_names)))
            for name in names:
                connection.execute(
                    "DELETE FROM resource_lock WHERE lock_name = ? AND task_id = ?",
                    (name, owner_id),
                )

        if names:
            if self._audit is not None:
                self._audit.record(
                    AuditCategory.LOCK,
                    f"released locks {list(names)}",
                    task_id=owner_id,
                    parameters={"locks": list(names)},
                )
            if self._events is not None:
                self._events.publish(
                    LockReleased(source="locks", task_id=owner_id, lock_names=names)
                )
        return names

    def release_all_for_instance(self, instance_id: str | None = None) -> tuple[str, ...]:
        """Release everything this runtime holds. Called during shutdown."""
        target = instance_id or self._instance_id
        with self._lock, self._database.transaction() as connection:
            rows = connection.execute(
                "SELECT lock_name FROM resource_lock WHERE instance_id = ?", (target,)
            ).fetchall()
            names = tuple(sorted(row["lock_name"] for row in rows))
            connection.execute("DELETE FROM resource_lock WHERE instance_id = ?", (target,))
        return names

    # -- recovery ----------------------------------------------------------
    def reclaim_stale(self, live_instance_ids: Sequence[str]) -> tuple[str, ...]:
        """Release locks whose owning runtime instance is gone (PRD FR-006).

        Without this, a crash while holding ``foreground_desktop`` would wedge
        every future automation task.
        """
        live = set(live_instance_ids) | {self._instance_id}
        with self._lock:
            held = self.held()
            stale = [record for record in held if record.instance_id not in live]
            if not stale:
                return ()
            with self._database.transaction() as connection:
                for record in stale:
                    connection.execute(
                        "DELETE FROM resource_lock WHERE lock_name = ?", (record.lock_name,)
                    )

        for record in stale:
            if self._audit is not None:
                self._audit.record(
                    AuditCategory.RECOVERY,
                    f"reclaimed stale lock '{record.lock_name}'",
                    actor="recovery",
                    task_id=record.task_id,
                    parameters={
                        "lock_name": record.lock_name,
                        "previous_instance_id": record.instance_id,
                    },
                )
            if self._events is not None:
                self._events.publish(
                    StaleLockReclaimed(
                        source="locks",
                        lock_name=record.lock_name,
                        previous_task_id=record.task_id,
                        previous_instance_id=record.instance_id,
                    )
                )
        return tuple(record.lock_name for record in stale)

    # -- inspection --------------------------------------------------------
    def held(self) -> tuple[ResourceLockRecord, ...]:
        rows = self._database.query_all(
            "SELECT lock_name, task_id, instance_id, acquired_at FROM resource_lock "
            "ORDER BY lock_name"
        )
        return tuple(
            ResourceLockRecord(
                lock_name=row["lock_name"],
                task_id=row["task_id"],
                instance_id=row["instance_id"],
                acquired_at=from_iso(row["acquired_at"]),  # type: ignore[arg-type]
            )
            for row in rows
        )

    def holder(self, lock_name: str) -> str | None:
        row = self._database.query_one(
            "SELECT task_id FROM resource_lock WHERE lock_name = ?", (lock_name,)
        )
        return row["task_id"] if row is not None else None

    def is_held(self, lock_name: str) -> bool:
        return self.holder(lock_name) is not None


class _Contended(Exception):
    """Internal signal that a lock in the set is taken."""

    def __init__(self, lock_name: str) -> None:
        super().__init__(lock_name)
        self.lock_name = lock_name
