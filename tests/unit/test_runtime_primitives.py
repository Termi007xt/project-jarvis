"""Single-instance guard, workers and schema migrations."""

from __future__ import annotations

import threading
import time

import pytest

from jarvis.runtime.single_instance import AlreadyRunningError, SingleInstanceGuard
from jarvis.runtime.workers import PeriodicWorker, Worker, WorkerSupervisor
from jarvis.storage.database import Database, DatabaseError
from jarvis.storage.migrations import (
    MIGRATIONS,
    SCHEMA_VERSION,
    applied_migrations,
    migrate,
    split_statements,
)


# =========================================================================
# Single instance (PRD FR-005)
# =========================================================================
def test_the_first_instance_acquires(tmp_path) -> None:
    guard = SingleInstanceGuard(lock_file=tmp_path / "i.lock", force_lock_file=True)
    assert guard.acquire()
    assert guard.acquired
    guard.release()


def test_a_second_instance_is_refused(tmp_path) -> None:
    lock = tmp_path / "i.lock"
    first = SingleInstanceGuard(lock_file=lock, force_lock_file=True)
    second = SingleInstanceGuard(lock_file=lock, force_lock_file=True)

    assert first.acquire()
    assert not second.acquire()

    first.release()
    assert second.acquire(), "the handle must be reusable once released"
    second.release()


def test_acquire_or_raise_explains_the_refusal(tmp_path) -> None:
    lock = tmp_path / "i.lock"
    first = SingleInstanceGuard(lock_file=lock, force_lock_file=True)
    first.acquire()

    second = SingleInstanceGuard(lock_file=lock, force_lock_file=True)
    with pytest.raises(AlreadyRunningError, match="already running"):
        second.acquire_or_raise()
    first.release()


def test_acquiring_twice_is_idempotent(tmp_path) -> None:
    guard = SingleInstanceGuard(lock_file=tmp_path / "i.lock", force_lock_file=True)
    assert guard.acquire()
    assert guard.acquire()
    guard.release()


def test_a_lock_file_from_a_dead_process_is_reclaimed(tmp_path) -> None:
    lock = tmp_path / "i.lock"
    lock.write_text("999999999", encoding="ascii")  # a pid that cannot exist

    guard = SingleInstanceGuard(lock_file=lock, force_lock_file=True)
    assert guard.acquire(), "a stale lock file must not wedge the application forever"
    guard.release()


def test_the_guard_works_as_a_context_manager(tmp_path) -> None:
    lock = tmp_path / "i.lock"
    with SingleInstanceGuard(lock_file=lock, force_lock_file=True) as guard:
        assert guard.acquired
    assert not lock.exists()


def test_release_removes_the_lock_file(tmp_path) -> None:
    lock = tmp_path / "i.lock"
    guard = SingleInstanceGuard(lock_file=lock, force_lock_file=True)
    guard.acquire()
    assert lock.exists()
    guard.release()
    assert not lock.exists()


# =========================================================================
# Workers (PRD NFR-003)
# =========================================================================
class _CountingWorker(Worker):
    def __init__(self, name: str = "counter") -> None:
        super().__init__(name)
        self.ticks = 0
        self.thread_name: str | None = None

    def work(self) -> None:
        self.thread_name = threading.current_thread().name
        while not self.wait(0.01):
            self.ticks += 1


def test_a_worker_runs_off_the_calling_thread() -> None:
    worker = _CountingWorker()
    worker.start()
    time.sleep(0.1)
    assert worker.running
    assert worker.thread_name != threading.current_thread().name
    assert worker.stop()
    assert not worker.running


def test_a_worker_stops_cooperatively() -> None:
    worker = _CountingWorker()
    worker.start()
    time.sleep(0.05)
    assert worker.stop(timeout_seconds=2.0)
    ticks = worker.ticks
    time.sleep(0.05)
    assert worker.ticks == ticks, "a stopped worker must do no further work"


def test_a_worker_that_raises_records_the_failure_rather_than_vanishing() -> None:
    class _Exploding(Worker):
        def work(self) -> None:
            raise RuntimeError("kaboom")

    worker = _Exploding("exploding")
    worker.start()
    time.sleep(0.1)
    assert isinstance(worker.failure, RuntimeError)


def test_a_periodic_worker_calls_its_action() -> None:
    calls = {"n": 0}

    def tick() -> None:
        calls["n"] += 1

    worker = PeriodicWorker("ticker", 0.02, tick)
    worker.start()
    time.sleep(0.15)
    worker.stop()
    assert calls["n"] >= 2


def test_one_bad_tick_does_not_kill_a_periodic_worker() -> None:
    calls = {"n": 0}

    def tick() -> None:
        calls["n"] += 1
        raise ValueError("this tick failed")

    worker = PeriodicWorker("ticker", 0.02, tick)
    worker.start()
    time.sleep(0.15)
    assert worker.running
    worker.stop()
    assert calls["n"] >= 2


def test_the_supervisor_starts_and_stops_in_order() -> None:
    supervisor = WorkerSupervisor()
    first = supervisor.add(_CountingWorker("first"))
    second = supervisor.add(_CountingWorker("second"))

    supervisor.start_all()
    time.sleep(0.05)
    assert set(supervisor.running_names()) == {"first", "second"}

    stopped = supervisor.stop_all()
    assert set(stopped) == {"first", "second"}
    assert not first.running and not second.running


def test_duplicate_worker_names_are_refused() -> None:
    supervisor = WorkerSupervisor()
    supervisor.add(_CountingWorker("only"))
    with pytest.raises(ValueError, match="already supervised"):
        supervisor.add(_CountingWorker("only"))


# =========================================================================
# Migrations (PRD NFR-043)
# =========================================================================
def test_migrations_apply_from_empty(tmp_path) -> None:
    db = Database(tmp_path / "fresh.db")
    assert db.user_version() == 0
    assert migrate(db) == SCHEMA_VERSION
    assert [row[0] for row in applied_migrations(db)] == [m.version for m in MIGRATIONS]
    db.close()


def test_migrating_twice_is_a_no_op(tmp_path) -> None:
    db = Database(tmp_path / "fresh.db")
    migrate(db)
    before = applied_migrations(db)
    assert migrate(db) == SCHEMA_VERSION
    assert applied_migrations(db) == before
    db.close()


def test_a_newer_schema_is_a_hard_startup_failure(tmp_path) -> None:
    """Best-effort reading a newer database could corrupt it (ADR-0002)."""
    db = Database(tmp_path / "future.db")
    migrate(db)
    db.set_user_version(SCHEMA_VERSION + 5)

    with pytest.raises(DatabaseError, match="newer than this build"):
        migrate(db)
    db.close()


def test_migration_versions_are_unique_and_ordered() -> None:
    versions = [m.version for m in MIGRATIONS]
    assert versions == sorted(versions)
    assert len(versions) == len(set(versions))


def test_foreign_keys_and_wal_are_enabled(database: Database) -> None:
    assert database.query_one("PRAGMA foreign_keys")[0] == 1
    assert database.query_one("PRAGMA journal_mode")[0].lower() == "wal"


def test_the_statement_splitter_rejects_compound_blocks() -> None:
    with pytest.raises(DatabaseError, match="BEGIN"):
        split_statements("CREATE TRIGGER t AFTER INSERT ON x BEGIN SELECT 1; END;")


def test_a_failed_migration_rolls_back(tmp_path) -> None:
    from jarvis.storage.migrations import Migration

    db = Database(tmp_path / "broken.db")
    broken = Migration(version=1, name="broken", sql="CREATE TABLE ok (a INT); NOT SQL AT ALL;")
    with pytest.raises(Exception):
        with db.transaction() as connection:
            for statement in split_statements(broken.sql):
                connection.execute(statement)
    assert db.query_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='ok'"
    ) is None
    db.close()


def test_every_phase_0_table_exists(database: Database) -> None:
    expected = {
        "schema_migration",
        "runtime_instance",
        "audit_event",
        "permission_grant",
        "task",
        "task_transition",
        "task_checkpoint",
        "task_evidence",
        "resource_lock",
        "tool_invocation",
    }
    present = {
        row["name"]
        for row in database.query_all("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert expected <= present
