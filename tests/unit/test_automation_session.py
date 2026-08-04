"""FR-077 / FR-078 / AT-008: nothing moves without owning the desktop.

Phase 2 stage 2, the piece that makes the other two mean something. The lock and
the interruption watcher already exist separately; on their own, each is
something a tool has to remember to use, and "the tool has to remember" is what
this project has repeatedly found does not hold.

An `AutomationSession` is the only way to get permission to move anything. It
takes `foreground_desktop`, arms the watcher, and gives back a handle. Without
the handle there is no step to run, so a tool cannot forget the lock — it can
only fail to acquire one.

The behaviours that matter, and why each one is here rather than assumed:

- Refusing to start when the lock is held. Two tasks driving the pointer at once
  produce garbage that is near-impossible to diagnose afterwards.
- Releasing the lock when the body raises. A crash mid-automation that kept the
  lock would wedge every future automation task until the process restarted.
- Stopping when the user takes over, at the *step boundary*, so a half-finished
  action is never left mid-flight.
- Refusing to start at all when interruption cannot be observed. Automation that
  cannot be interrupted is a different product from automation that was not.
"""

from __future__ import annotations

import pytest

from jarvis.tasks.locks import FOREGROUND_DESKTOP
from jarvis.toolbox.automation import (
    AutomationSession,
    DesktopBusy,
    UserTookOver,
)


class FakeLocks:
    """Enough of ResourceLockManager to test acquisition and release."""

    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.held: set[str] = set()
        self.released: list[str] = []

    def acquire(self, owner_id, lock_names, timeout_seconds=0.0):
        if not self.available:
            return None
        self.held.update(lock_names)
        return _Lease(self, tuple(lock_names))


class _Lease:
    def __init__(self, manager: FakeLocks, names: tuple[str, ...]) -> None:
        self._manager = manager
        self.lock_names = names
        self.released = False

    def release(self) -> None:
        self.released = True
        self._manager.held.difference_update(self.lock_names)
        self._manager.released.extend(self.lock_names)


class FakeWatcher:
    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.armed = False
        self.intervene_after: int | None = None
        self._asked = 0

    def unavailable_reason(self):
        return None if self.available else "cannot observe input here"

    def arm(self) -> None:
        self.armed = True

    def note_synthetic_input(self) -> None:
        pass

    def user_intervened(self) -> bool:
        self._asked += 1
        if self.intervene_after is None:
            return False
        return self._asked > self.intervene_after


@pytest.fixture
def locks() -> FakeLocks:
    return FakeLocks()


@pytest.fixture
def watcher() -> FakeWatcher:
    return FakeWatcher()


def make_session(locks, watcher, **kwargs) -> AutomationSession:
    return AutomationSession(
        task_id="task-1", locks=locks, watcher=watcher, **kwargs
    )


# -- owning the desktop ----------------------------------------------------
def test_a_session_takes_the_foreground_lock(locks, watcher) -> None:
    with make_session(locks, watcher):
        assert FOREGROUND_DESKTOP in locks.held


def test_the_lock_is_released_when_the_session_ends(locks, watcher) -> None:
    with make_session(locks, watcher):
        pass
    assert FOREGROUND_DESKTOP not in locks.held
    assert FOREGROUND_DESKTOP in locks.released


def test_the_lock_is_released_even_when_the_body_raises(locks, watcher) -> None:
    """A crash that kept the lock would wedge all future automation.

    `ResourceLockManager` can reclaim a lock left by a dead *process*, but a
    live process holding one forever is not stale and is never reclaimed.
    """
    with pytest.raises(ValueError):
        with make_session(locks, watcher):
            raise ValueError("something went wrong mid-automation")

    assert FOREGROUND_DESKTOP not in locks.held


def test_a_busy_desktop_refuses_rather_than_waiting_forever(watcher) -> None:
    busy = FakeLocks(available=False)
    with pytest.raises(DesktopBusy):
        with make_session(busy, watcher):
            pytest.fail("the body must not run when the desktop is not ours")


# -- the user taking over --------------------------------------------------
def test_the_watcher_is_armed_when_the_session_starts(locks, watcher) -> None:
    with make_session(locks, watcher):
        assert watcher.armed


def test_a_step_runs_while_the_user_is_quiet(locks, watcher) -> None:
    performed = []
    with make_session(locks, watcher) as session:
        session.step("click search", performed.append)
    assert performed == ["click search"]


def test_the_user_taking_over_stops_the_next_step(locks, watcher) -> None:
    """AT-008. Checked at the step boundary, never mid-action."""
    watcher.intervene_after = 1
    performed = []

    with pytest.raises(UserTookOver):
        with make_session(locks, watcher) as session:
            session.step("first", performed.append)
            session.step("second", performed.append)
            session.step("third", performed.append)

    assert performed == ["first"], "the step after the interruption must not run"


def test_the_lock_is_released_when_the_user_takes_over(locks, watcher) -> None:
    """Otherwise interrupting automation once would disable it permanently."""
    watcher.intervene_after = 0

    with pytest.raises(UserTookOver):
        with make_session(locks, watcher) as session:
            session.step("anything", lambda _: None)

    assert FOREGROUND_DESKTOP not in locks.held


def test_a_step_reports_that_it_produced_input(locks, watcher) -> None:
    """Every injected event must be declared, or the watcher blames the user.

    A step that moves the pointer without saying so leaves the watcher treating
    our own action as an interruption, and the automation pauses itself.
    """
    recorded = []
    watcher.note_synthetic_input = lambda: recorded.append(True)  # type: ignore[method-assign]

    with make_session(locks, watcher) as session:
        session.step("click", lambda _: None, sends_input=True)

    assert recorded, "a step that sends input must tell the watcher"


# -- honesty ---------------------------------------------------------------
def test_automation_refuses_to_start_when_it_cannot_be_interrupted(locks) -> None:
    """ADR-0010, and the strongest of the safety properties here.

    If the user cannot stop it, it does not start. Running anyway and hoping
    would be the version of this that reads fine in a demo and is indefensible
    on a real desktop.
    """
    deaf = FakeWatcher(available=False)

    with pytest.raises(RuntimeError) as raised:
        with make_session(locks, deaf):
            pytest.fail("the body must not run")

    message = str(raised.value).lower()
    assert "taken over" in message, "say what it is unable to notice"
    assert "cannot observe input here" in message, (
        "and pass the underlying reason through rather than swallowing it — "
        "'automation is unavailable' with no cause is the kind of message that "
        "sends someone reading source code to find out why"
    )
    assert FOREGROUND_DESKTOP not in locks.held, "and it must not hold the lock either"


def test_a_step_outside_a_session_is_refused(locks, watcher) -> None:
    """There is no way to act without having taken the desktop first."""
    session = make_session(locks, watcher)
    with pytest.raises(RuntimeError):
        session.step("click", lambda _: None)
