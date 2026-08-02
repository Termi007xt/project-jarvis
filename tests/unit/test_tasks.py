"""Task state machine, durable store, locks and scheduler (PRD FR-120 .. FR-133)."""

from __future__ import annotations

import threading
import time

import pytest

from jarvis.tasks.locks import ResourceLockManager
from jarvis.tasks.runner import TaskOutcome, TaskRunContext
from jarvis.tasks.states import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATES,
    InvalidTransitionError,
    TaskState,
    assert_transition,
    can_transition,
)
from jarvis.tasks.store import TaskNotFoundError, TaskStore


# =========================================================================
# State machine
# =========================================================================
def test_all_ten_prd_states_exist() -> None:
    """PRD FR-122."""
    expected = {
        "draft", "awaiting_approval", "queued", "running", "waiting",
        "paused", "blocked", "succeeded", "failed", "cancelled",
    }
    assert {state.value for state in TaskState} == expected


def test_terminal_states_have_no_outgoing_transitions() -> None:
    """A finished task is finished; a repeat is a new task."""
    for state in TERMINAL_STATES:
        assert ALLOWED_TRANSITIONS[state] == frozenset()


@pytest.mark.parametrize(
    ("start", "target"),
    [
        (TaskState.DRAFT, TaskState.QUEUED),
        (TaskState.QUEUED, TaskState.RUNNING),
        (TaskState.RUNNING, TaskState.SUCCEEDED),
        (TaskState.RUNNING, TaskState.PAUSED),
        (TaskState.PAUSED, TaskState.QUEUED),
        (TaskState.BLOCKED, TaskState.AWAITING_APPROVAL),
        (TaskState.WAITING, TaskState.RUNNING),
    ],
)
def test_legal_transitions_are_permitted(start: TaskState, target: TaskState) -> None:
    assert can_transition(start, target)
    assert_transition(start, target)


@pytest.mark.parametrize(
    ("start", "target"),
    [
        (TaskState.SUCCEEDED, TaskState.RUNNING),
        (TaskState.CANCELLED, TaskState.QUEUED),
        (TaskState.FAILED, TaskState.SUCCEEDED),
        (TaskState.DRAFT, TaskState.RUNNING),
        (TaskState.DRAFT, TaskState.SUCCEEDED),
        (TaskState.PAUSED, TaskState.SUCCEEDED),
    ],
)
def test_illegal_transitions_raise(start: TaskState, target: TaskState) -> None:
    assert not can_transition(start, target)
    with pytest.raises(InvalidTransitionError):
        assert_transition(start, target)


def test_a_task_cannot_be_marked_succeeded_without_running() -> None:
    """The most dangerous illegal transition gets its own test."""
    with pytest.raises(InvalidTransitionError):
        assert_transition(TaskState.DRAFT, TaskState.SUCCEEDED)


# =========================================================================
# Store
# =========================================================================
def test_a_created_task_persists(tasks: TaskStore, database) -> None:
    task = tasks.create("Test", "do a thing", "runner.x", required_locks=("clipboard",))
    reloaded = TaskStore(database).get(task.task_id)
    assert reloaded is not None
    assert reloaded.name == "Test"
    assert reloaded.required_locks == ("clipboard",)
    assert reloaded.state is TaskState.DRAFT


def test_missing_task_raises(tasks: TaskStore) -> None:
    with pytest.raises(TaskNotFoundError):
        tasks.require("nope")


def test_transitions_are_recorded_in_history(tasks: TaskStore) -> None:
    task = tasks.create("Test", "goal", "runner.x")
    tasks.transition(task.task_id, TaskState.QUEUED, reason="queued")
    tasks.transition(task.task_id, TaskState.RUNNING, reason="dispatched")

    history = tasks.transitions(task.task_id)
    assert [t.to_state for t in history] == [
        TaskState.DRAFT, TaskState.QUEUED, TaskState.RUNNING
    ]


def test_an_illegal_transition_is_refused_and_changes_nothing(tasks: TaskStore) -> None:
    task = tasks.create("Test", "goal", "runner.x")
    with pytest.raises(InvalidTransitionError):
        tasks.transition(task.task_id, TaskState.SUCCEEDED)
    assert tasks.require(task.task_id).state is TaskState.DRAFT


def test_running_records_a_start_time_and_terminal_records_an_end(tasks: TaskStore) -> None:
    task = tasks.create("Test", "goal", "runner.x")
    tasks.transition(task.task_id, TaskState.QUEUED)
    running = tasks.transition(task.task_id, TaskState.RUNNING)
    assert running.started_at is not None

    done = tasks.transition(task.task_id, TaskState.SUCCEEDED)
    assert done.ended_at is not None


def test_checkpoints_are_sequential_and_durable(tasks: TaskStore) -> None:
    task = tasks.create("Test", "goal", "runner.x")
    tasks.save_checkpoint(task.task_id, "step-1", {"index": 1})
    tasks.save_checkpoint(task.task_id, "step-2", {"index": 2})

    checkpoints = tasks.checkpoints(task.task_id)
    assert [c.sequence for c in checkpoints] == [0, 1]
    assert tasks.latest_checkpoint(task.task_id).state == {"index": 2}


def test_evidence_is_recorded(tasks: TaskStore) -> None:
    task = tasks.create("Test", "goal", "runner.x")
    tasks.add_evidence(task.task_id, "file_exists", "the file was created", detail={"path": "x"})
    evidence = tasks.evidence(task.task_id)
    assert len(evidence) == 1
    assert evidence[0].kind == "file_exists"


def test_task_trees_are_supported(tasks: TaskStore) -> None:
    """PRD FR-121."""
    parent = tasks.create("Parent", "goal", "runner.x")
    child = tasks.create("Child", "goal", "runner.x", parent_task_id=parent.task_id)
    assert [t.task_id for t in tasks.list(parent_task_id=parent.task_id)] == [child.task_id]


def test_deleting_a_parent_cascades_to_children(tasks: TaskStore, database) -> None:
    parent = tasks.create("Parent", "goal", "runner.x")
    child = tasks.create("Child", "goal", "runner.x", parent_task_id=parent.task_id)
    with database.transaction() as connection:
        connection.execute("DELETE FROM task WHERE task_id = ?", (parent.task_id,))
    assert tasks.get(child.task_id) is None


# =========================================================================
# Locks
# =========================================================================
def test_a_lock_is_exclusive(locks: ResourceLockManager) -> None:
    assert locks.acquire("task-a", ["foreground_desktop"]) is not None
    assert locks.acquire("task-b", ["foreground_desktop"]) is None


def test_lock_acquisition_is_all_or_nothing(locks: ResourceLockManager) -> None:
    """A partial acquisition would deadlock two tasks against each other."""
    locks.acquire("task-a", ["clipboard"])
    assert locks.acquire("task-b", ["foreground_desktop", "clipboard"]) is None
    assert not locks.is_held("foreground_desktop"), "no lock should have been taken"


def test_releasing_frees_the_lock(locks: ResourceLockManager) -> None:
    lease = locks.acquire("task-a", ["foreground_desktop"])
    lease.release()
    assert locks.acquire("task-b", ["foreground_desktop"]) is not None


def test_release_is_idempotent(locks: ResourceLockManager) -> None:
    lease = locks.acquire("task-a", ["clipboard"])
    lease.release()
    lease.release()
    assert not locks.is_held("clipboard")


def test_a_lock_is_reentrant_for_the_same_owner(locks: ResourceLockManager) -> None:
    assert locks.acquire("task-a", ["clipboard"]) is not None
    assert locks.acquire("task-a", ["clipboard"]) is not None


def test_unknown_lock_names_are_rejected(locks: ResourceLockManager) -> None:
    with pytest.raises(ValueError, match="unknown resource lock"):
        locks.acquire("task-a", ["make_believe_lock"])


def test_prefixed_lock_names_are_accepted(locks: ResourceLockManager) -> None:
    assert locks.acquire("task-a", ["application:brave", "folder_scope:C:/tmp"]) is not None


def test_locks_persist_and_record_their_owner(locks: ResourceLockManager) -> None:
    locks.acquire("task-a", ["speaker_output"])
    held = locks.held()
    assert held[0].lock_name == "speaker_output"
    assert held[0].task_id == "task-a"
    assert held[0].instance_id == "test-instance"


def test_stale_locks_from_a_dead_instance_are_reclaimed(database, audit, events) -> None:
    """PRD FR-006: a crash while holding a lock must not wedge the resource."""
    dead = ResourceLockManager(database, "dead-instance", audit, events)
    dead.acquire("task-a", ["foreground_desktop"])

    live = ResourceLockManager(database, "live-instance", audit, events)
    reclaimed = live.reclaim_stale(live_instance_ids=["live-instance"])
    assert reclaimed == ("foreground_desktop",)
    assert live.acquire("task-b", ["foreground_desktop"]) is not None


def test_concurrent_acquisition_yields_exactly_one_winner(locks: ResourceLockManager) -> None:
    winners: list[str] = []
    barrier = threading.Barrier(8)
    lock = threading.Lock()

    def contend(index: int) -> None:
        barrier.wait()
        if locks.acquire(f"task-{index}", ["foreground_desktop"]) is not None:
            with lock:
                winners.append(f"task-{index}")

    threads = [threading.Thread(target=contend, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(winners) == 1, f"exactly one task may hold the foreground lock, got {winners}"


# =========================================================================
# Scheduler
# =========================================================================
class RecordingRunner:
    def __init__(self, runner_id: str, outcome: TaskOutcome | None = None, hold: float = 0.0):
        self.runner_id = runner_id
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls = 0
        self._outcome = outcome or TaskOutcome(state=TaskState.SUCCEEDED, summary="done")
        self._hold = hold

    def run(self, context: TaskRunContext) -> TaskOutcome:
        self.calls += 1
        self.started.set()
        context.checkpoint("started")
        if self._hold:
            self.release.wait(self._hold)
        if context.should_stop():
            context.checkpoint("stopping")
        return self._outcome


def wait_for(predicate, timeout: float = 5.0, interval: float = 0.02) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False


def test_a_queued_task_runs_to_success(scheduler, tasks) -> None:
    scheduler.register_runner(RecordingRunner("runner.ok"))
    scheduler.start()
    task = tasks.create("Test", "goal", "runner.ok")
    scheduler.submit(task)

    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.SUCCEEDED)
    assert tasks.require(task.task_id).result_summary == "done"


def test_submitting_without_a_registered_runner_is_refused(scheduler, tasks) -> None:
    from jarvis.tasks.scheduler import SchedulerError

    task = tasks.create("Test", "goal", "runner.missing")
    with pytest.raises(SchedulerError, match="no runner registered"):
        scheduler.submit(task)


def test_two_tasks_needing_the_same_lock_do_not_run_together(scheduler, tasks) -> None:
    """PRD section 7.1 and AT-009: one runs, the other stays queued."""
    runner = RecordingRunner("runner.hold", hold=1.5)
    scheduler.register_runner(runner)
    scheduler.start()

    first = tasks.create("First", "goal", "runner.hold", required_locks=("foreground_desktop",))
    second = tasks.create("Second", "goal", "runner.hold", required_locks=("foreground_desktop",))
    scheduler.submit(first)
    assert runner.started.wait(5.0)
    scheduler.submit(second)

    time.sleep(0.3)
    assert tasks.require(first.task_id).state is TaskState.RUNNING
    queued = tasks.require(second.task_id)
    assert queued.state is TaskState.QUEUED
    assert "waiting for resource lock" in (queued.waiting_on or "")

    runner.release.set()
    assert wait_for(lambda: tasks.require(second.task_id).state is TaskState.SUCCEEDED, 10.0)


def test_tasks_with_disjoint_locks_run_concurrently(scheduler, tasks) -> None:
    runner = RecordingRunner("runner.hold", hold=0.6)
    scheduler.register_runner(runner)
    scheduler.start()

    a = tasks.create("A", "goal", "runner.hold", required_locks=("clipboard",))
    b = tasks.create("B", "goal", "runner.hold", required_locks=("speaker_output",))
    scheduler.submit(a)
    scheduler.submit(b)

    assert wait_for(
        lambda: tasks.require(a.task_id).state is TaskState.RUNNING
        and tasks.require(b.task_id).state is TaskState.RUNNING
    )
    runner.release.set()


def test_pause_is_cooperative_and_lands_at_a_checkpoint(scheduler, tasks) -> None:
    """PRD FR-125."""
    runner = RecordingRunner("runner.hold", hold=2.0)
    scheduler.register_runner(runner)
    scheduler.start()

    task = tasks.create("Test", "goal", "runner.hold")
    scheduler.submit(task)
    assert runner.started.wait(5.0)

    scheduler.pause(task.task_id)
    runner.release.set()
    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.PAUSED, 10.0)


def test_a_queued_task_pauses_immediately(scheduler, tasks) -> None:
    scheduler.register_runner(RecordingRunner("runner.ok"))
    task = tasks.create("Test", "goal", "runner.ok")
    scheduler.submit(task)  # not started: the scheduler is not running
    paused = scheduler.pause(task.task_id)
    assert paused.state is TaskState.PAUSED


def test_resume_requeues_a_paused_task(scheduler, tasks) -> None:
    runner = RecordingRunner("runner.ok")
    scheduler.register_runner(runner)
    task = tasks.create("Test", "goal", "runner.ok")
    scheduler.submit(task)
    scheduler.pause(task.task_id)

    scheduler.resume(task.task_id)
    assert tasks.require(task.task_id).state is TaskState.QUEUED
    scheduler.start()
    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.SUCCEEDED)


def test_cancel_releases_locks_and_stops_the_task(scheduler, tasks, locks) -> None:
    """PRD FR-127."""
    runner = RecordingRunner("runner.hold", hold=2.0)
    scheduler.register_runner(runner)
    scheduler.start()

    task = tasks.create("Test", "goal", "runner.hold", required_locks=("foreground_desktop",))
    scheduler.submit(task)
    assert runner.started.wait(5.0)

    scheduler.cancel(task.task_id)
    runner.release.set()
    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.CANCELLED, 10.0)
    assert not locks.is_held("foreground_desktop")


def test_cancelling_a_terminal_task_is_a_no_op(scheduler, tasks) -> None:
    scheduler.register_runner(RecordingRunner("runner.ok"))
    scheduler.start()
    task = tasks.create("Test", "goal", "runner.ok")
    scheduler.submit(task)
    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.SUCCEEDED)

    result = scheduler.cancel(task.task_id)
    assert result.state is TaskState.SUCCEEDED


def test_a_retryable_failure_is_retried_up_to_the_bound(scheduler, tasks) -> None:
    """PRD FR-133 and NFR-012."""
    runner = RecordingRunner(
        "runner.flaky",
        outcome=TaskOutcome(
            state=TaskState.FAILED, summary="nope", failure_code="transient", retryable=True
        ),
    )
    scheduler.register_runner(runner)
    scheduler.start()

    task = tasks.create("Test", "goal", "runner.flaky", max_retries=2)
    scheduler.submit(task)

    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.FAILED, 10.0)
    final = tasks.require(task.task_id)
    assert final.attempts == 3, "one initial attempt plus two retries"
    assert runner.calls == 3


def test_a_non_retryable_failure_is_not_retried(scheduler, tasks) -> None:
    runner = RecordingRunner(
        "runner.bad",
        outcome=TaskOutcome(
            state=TaskState.FAILED, summary="permanent", failure_code="boom", retryable=False
        ),
    )
    scheduler.register_runner(runner)
    scheduler.start()

    task = tasks.create("Test", "goal", "runner.bad", max_retries=5)
    scheduler.submit(task)
    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.FAILED)
    assert runner.calls == 1


def test_a_runner_exception_becomes_a_failed_task_not_a_crash(scheduler, tasks) -> None:
    class Exploding:
        runner_id = "runner.explode"

        def run(self, context):
            raise RuntimeError("kaboom")

    scheduler.register_runner(Exploding())
    scheduler.start()
    task = tasks.create("Test", "goal", "runner.explode")
    scheduler.submit(task)

    assert wait_for(lambda: tasks.require(task.task_id).state is TaskState.FAILED)
    assert tasks.require(task.task_id).failure_code == "runner_exception"


def test_a_runner_may_only_report_permitted_outcomes() -> None:
    for forbidden in (TaskState.RUNNING, TaskState.QUEUED, TaskState.CANCELLED, TaskState.DRAFT):
        with pytest.raises(ValueError, match="a runner may only report"):
            TaskOutcome(state=forbidden)


def test_emergency_stop_cancels_everything_active(scheduler, tasks) -> None:
    """PRD section 11.3."""
    scheduler.register_runner(RecordingRunner("runner.ok"))
    first = tasks.create("A", "goal", "runner.ok")
    second = tasks.create("B", "goal", "runner.ok")
    scheduler.submit(first)
    scheduler.submit(second)

    stopped = scheduler.emergency_stop()
    assert set(stopped) == {first.task_id, second.task_id}
    assert tasks.require(first.task_id).state is TaskState.CANCELLED
    assert tasks.require(second.task_id).state is TaskState.CANCELLED
