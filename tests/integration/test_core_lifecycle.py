"""Full core lifecycle, crash recovery and settings durability."""

from __future__ import annotations

import time

import pytest

from jarvis.config.schema import NetworkMode
from jarvis.config.store import ConfigStore
from jarvis.core.events.types import AppStarted, AppStopping, EmergencyStopCompleted
from jarvis.runtime.core import JarvisCore
from jarvis.runtime.single_instance import AlreadyRunningError, SingleInstanceGuard
from jarvis.storage.database import Database
from jarvis.storage.migrations import SCHEMA_VERSION
from jarvis.tasks.locks import ResourceLockManager
from jarvis.tasks.states import TaskState
from jarvis.tasks.store import TaskStore


def _new_core(vault, **kwargs) -> JarvisCore:
    return JarvisCore(
        vault,
        config_store=ConfigStore(vault, env={}),
        single_instance=SingleInstanceGuard(
            lock_file=vault.runtime_dir / "test.lock", force_lock_file=True
        ),
        enforce_single_instance=kwargs.pop("enforce_single_instance", False),
        **kwargs,
    )


def wait_for(predicate, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def simulate_crash(instance: JarvisCore) -> None:
    """Kill the process the way a crash does: threads gone, nothing cleaned up.

    Deliberately *not* ``shutdown()``. Locks stay held, running tasks stay
    marked running, and the ``runtime_instance`` row keeps ``stopped_at NULL``
    — which is exactly the state the next launch has to recover from.
    """
    instance.scheduler.stop(timeout_seconds=2.0)
    instance.workers.stop_all(timeout_seconds=2.0)
    instance.invoker.shutdown(wait=False)
    instance.database.close()


# =========================================================================
# Startup and shutdown
# =========================================================================
def test_the_core_starts_and_reports_a_coherent_status(core: JarvisCore) -> None:
    status = core.status()
    assert status.running
    assert status.schema_version == SCHEMA_VERSION
    assert "system.health" in status.registered_tools
    assert "health" in status.workers
    assert core.scheduler.running


def test_startup_creates_the_whole_vault_layout(core: JarvisCore) -> None:
    for directory in core.paths.all_directories():
        assert directory.is_dir()
    assert core.paths.db_path.is_file()
    assert core.paths.audit_log_path.is_file()


def test_startup_and_shutdown_are_audited(core: JarvisCore) -> None:
    core.shutdown("test")
    summaries = [record["summary"] for record in core.audit.read_all()]
    assert any(s.startswith("started") for s in summaries)
    assert any(s.startswith("stopped") for s in summaries)


def test_startup_and_shutdown_publish_events(vault) -> None:
    started: list[AppStarted] = []
    stopping: list[AppStopping] = []

    instance = _new_core(vault)
    instance.start()
    instance.events.subscribe(AppStopping, stopping.append)
    instance.shutdown("test")

    # AppStarted is published during start, before a subscriber can attach, so
    # assert it reached the audit log instead.
    assert any("started" in r["summary"] for r in instance.audit.read_all())
    assert len(stopping) == 1
    assert started == []


def test_shutdown_is_idempotent(vault) -> None:
    instance = _new_core(vault).start()
    instance.shutdown("first")
    instance.shutdown("second")  # must not raise
    assert not instance.started


def test_shutdown_releases_every_lock(vault) -> None:
    instance = _new_core(vault).start()
    instance.locks.acquire("some-task", ["foreground_desktop", "clipboard"])
    instance.shutdown("test")

    database = Database(vault.db_path)
    remaining = database.query_all("SELECT * FROM resource_lock")
    database.close()
    assert remaining == []


def test_the_core_works_as_a_context_manager(vault) -> None:
    with _new_core(vault) as instance:
        assert instance.started
    assert not instance.started


def test_single_instance_enforcement_blocks_a_second_core(vault) -> None:
    """PRD FR-005."""
    guard_path = vault.runtime_dir / "shared.lock"
    first = JarvisCore(
        vault,
        config_store=ConfigStore(vault, env={}),
        single_instance=SingleInstanceGuard(lock_file=guard_path, force_lock_file=True),
        enforce_single_instance=True,
    ).start()
    try:
        second = JarvisCore(
            vault,
            config_store=ConfigStore(vault, env={}),
            single_instance=SingleInstanceGuard(lock_file=guard_path, force_lock_file=True),
            enforce_single_instance=True,
        )
        with pytest.raises(AlreadyRunningError):
            second.start()
    finally:
        first.shutdown("test")


# =========================================================================
# Settings persistence
# =========================================================================
def test_settings_persist_across_a_restart(vault) -> None:
    """Phase 0 exit criterion."""
    first = _new_core(vault).start()
    first.set_setting("ui.start_minimised_to_tray", False)
    first.set_network_mode(NetworkMode.OFFLINE)
    first.shutdown("test")

    second = _new_core(vault).start()
    try:
        assert second.config.ui.start_minimised_to_tray is False
        assert second.config.network.mode is NetworkMode.OFFLINE
    finally:
        second.shutdown("test")


def test_a_settings_change_is_audited_with_before_and_after(core: JarvisCore) -> None:
    core.set_setting("logging.level", "DEBUG")
    config_records = [r for r in core.audit.read_all() if r["category"] == "config"]
    assert config_records
    latest = config_records[-1]
    assert latest["parameters"]["key_path"] == "logging.level"
    assert latest["parameters"]["previous"] == "INFO"
    assert latest["parameters"]["current"] == "DEBUG"


# =========================================================================
# Crash recovery (PRD FR-006, NFR-010, NFR-011, AT-011)
# =========================================================================
def test_an_interrupted_task_reappears_paused_and_is_not_resumed(vault) -> None:
    first = _new_core(vault).start()
    # See the note in test_a_completed_task_is_never_re_run_after_recovery: a
    # live scheduler dispatches this task itself and races the transition below.
    first.scheduler.stop()
    task = first.tasks.create("Long job", "do a long thing", "system.health_check")
    first.tasks.transition(task.task_id, TaskState.QUEUED)
    first.tasks.transition(task.task_id, TaskState.RUNNING)
    first.locks.acquire(task.task_id, ["foreground_desktop"])

    simulate_crash(first)

    second = _new_core(vault).start()
    try:
        recovered = second.tasks.require(task.task_id)
        assert recovered.state is TaskState.PAUSED
        assert recovered.recovered is True
        assert "restart" in (recovered.blocked_reason or "")
        assert second.recovery is not None
        assert task.task_id in second.recovery.recovered_task_ids
    finally:
        second.shutdown("test")


def test_recovery_releases_locks_orphaned_by_a_crash(vault) -> None:
    first = _new_core(vault).start()
    task = first.tasks.create("Long job", "goal", "system.health_check")
    first.locks.acquire(task.task_id, ["foreground_desktop"])
    simulate_crash(first)

    second = _new_core(vault).start()
    try:
        assert "foreground_desktop" in second.recovery.reclaimed_locks
        assert second.locks.acquire("new-task", ["foreground_desktop"]) is not None
    finally:
        second.shutdown("test")


def test_a_completed_task_is_never_re_run_after_recovery(vault) -> None:
    """PRD NFR-011: no consequential action is repeated after a restart."""
    first = _new_core(vault).start()
    # Stop the scheduler before hand-driving the task's state. `system.health_check`
    # has a registered runner, so a live scheduler dispatches a QUEUED task itself
    # and moves it to RUNNING — and then this test's own transition to RUNNING
    # raises, intermittently, depending on which won. The product was right and
    # the test was racing it; this test is about *recovery*, not dispatch.
    first.scheduler.stop()
    task = first.tasks.create("Done", "goal", "system.health_check")
    first.tasks.transition(task.task_id, TaskState.QUEUED)
    first.tasks.transition(task.task_id, TaskState.RUNNING)
    first.tasks.transition(task.task_id, TaskState.SUCCEEDED)
    simulate_crash(first)

    second = _new_core(vault).start()
    try:
        assert second.tasks.require(task.task_id).state is TaskState.SUCCEEDED
        assert task.task_id not in second.recovery.recovered_task_ids
    finally:
        second.shutdown("test")


def test_a_clean_start_reports_nothing_to_recover(core: JarvisCore) -> None:
    assert core.recovery is not None
    assert core.recovery.clean_start
    assert "No interrupted work" in core.recovery.describe()


def test_recovery_is_audited(vault) -> None:
    first = _new_core(vault).start()
    # Third of the same family: a live scheduler dispatches this task itself.
    first.scheduler.stop()
    task = first.tasks.create("Long job", "goal", "system.health_check")
    first.tasks.transition(task.task_id, TaskState.QUEUED)
    first.tasks.transition(task.task_id, TaskState.RUNNING)
    simulate_crash(first)

    second = _new_core(vault).start()
    try:
        categories = [r["category"] for r in second.audit.read_all()]
        assert "recovery" in categories
    finally:
        second.shutdown("test")


# =========================================================================
# Emergency stop (PRD section 11.3)
# =========================================================================
def test_emergency_stop_cancels_tasks_releases_locks_and_reports(core: JarvisCore) -> None:
    task = core.tasks.create("Busy", "goal", "system.health_check")
    core.tasks.transition(task.task_id, TaskState.QUEUED)
    core.locks.acquire(task.task_id, ["foreground_desktop"])

    received: list[EmergencyStopCompleted] = []
    core.events.subscribe(EmergencyStopCompleted, received.append)

    report = core.emergency_stop(origin="tray")

    assert task.task_id in report.cancelled_task_ids
    assert "foreground_desktop" in report.released_locks
    assert not core.locks.is_held("foreground_desktop")
    assert len(received) == 1
    assert "Stopped:" in report.describe()

    # Cancellation is cooperative: a task the scheduler had already dispatched
    # stops at its next checkpoint rather than being killed mid-step (FR-125).
    assert wait_for(lambda: core.tasks.require(task.task_id).state is TaskState.CANCELLED)


def test_emergency_stop_is_audited_as_a_security_event(core: JarvisCore) -> None:
    core.emergency_stop(origin="hotkey")
    security = [r for r in core.audit.read_all() if r["category"] == "security"]
    assert any("emergency stop" in r["summary"] for r in security)


def test_emergency_stop_leaves_the_application_running(core: JarvisCore) -> None:
    core.emergency_stop()
    assert core.started, "emergency stop halts automation, not the application"


# =========================================================================
# The health check, end to end
# =========================================================================
def test_the_health_check_task_runs_through_the_whole_pipeline(core: JarvisCore) -> None:
    task_id = core.run_health_check_task()
    assert wait_for(lambda: core.tasks.require(task_id).is_terminal)

    task = core.tasks.require(task_id)
    assert task.state is TaskState.SUCCEEDED, task.result_summary
    assert core.tasks.checkpoints(task_id), "the runner must leave resume points"
    assert core.tasks.evidence(task_id), "success must be supported by evidence"


def test_the_health_check_is_permission_checked_like_anything_else(core: JarvisCore) -> None:
    task_id = core.run_health_check_task()
    assert wait_for(lambda: core.tasks.require(task_id).is_terminal)

    permission_records = [
        r
        for r in core.audit.read_all()
        if r["category"] == "permission" and r["capability_id"] == "system.read_health"
    ]
    assert permission_records, "no capability may bypass the permission engine"


def test_bootstrap_grants_are_visible_and_revocable(core: JarvisCore) -> None:
    grants = {g.capability_id: g for g in core.permissions.list_grants(active_only=True)}
    assert "system.read_health" in grants
    assert grants["system.read_health"].created_by == "system_default"

    assert core.permissions.revoke(grants["system.read_health"].grant_id)
    assert "system.read_health" not in {
        g.capability_id for g in core.permissions.list_grants(active_only=True)
    }


def test_offline_mode_makes_the_health_check_skip_the_network(vault) -> None:
    """PRD AT-001."""
    instance = _new_core(vault).start()
    try:
        instance.set_network_mode(NetworkMode.OFFLINE)
        health = instance.refresh_health()
        assert health.skipped
        assert "offline" in (health.skipped_reason or "")
    finally:
        instance.shutdown("test")


def test_a_task_store_from_another_connection_sees_the_same_state(core: JarvisCore) -> None:
    """SQLite is the single source of truth (ADR-0002)."""
    task = core.tasks.create("Shared", "goal", "system.health_check")
    other = TaskStore(Database(core.paths.db_path))
    assert other.get(task.task_id) is not None


def test_locks_are_visible_across_managers(core: JarvisCore) -> None:
    core.locks.acquire("task-a", ["clipboard"])
    other = ResourceLockManager(Database(core.paths.db_path), "other-instance")
    assert other.is_held("clipboard")
    assert other.acquire("task-b", ["clipboard"]) is None
