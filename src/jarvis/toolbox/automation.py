"""Owning the desktop before moving anything (FR-077, FR-078, P2-WIN-03/04/05).

Phase 2 stage 2. The lock manager and the input watcher already exist on their
own, and on their own each is something a tool has to *remember* to use. This
project's record on "the tool has to remember" is not good: `voice.speak`
declared a lock name that did not exist and nobody noticed until a human tried to
speak; `app.open` verified itself against a process it had not started.

So an `AutomationSession` is not a helper that tools may use — it is the only
thing that hands out permission to move anything. It takes `foreground_desktop`,
arms the watcher, and returns a handle whose `step()` is the sole way to perform
an action. A tool cannot forget to take the lock, because without the session
there is no step to call.

Four properties are load-bearing, and each exists because the obvious
implementation gets it wrong:

1. **A busy desktop refuses.** Two tasks driving the pointer at once produce
   behaviour that is close to impossible to diagnose afterwards.
2. **The lock is released even when the body raises.** `ResourceLockManager`
   reclaims locks held by a *dead* runtime, but a live process holding one
   forever is not stale and never gets reclaimed — one crash mid-automation
   would disable automation until restart.
3. **Interruption is checked at the step boundary**, never mid-action, so the
   user never lands in a half-finished state.
4. **Automation that cannot be interrupted does not start.** Where the watcher
   cannot observe input, this refuses rather than running and hoping. That is
   the version that reads fine in a demo and is indefensible on a real desktop
   (ADR-0010).

This module moves nothing itself. It decides *whether* something may move, and
the actual pointer and keyboard work arrives as callables from the tools above
it — which keeps the effect inside `ToolInvoker`'s six checks rather than
alongside them.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol

from jarvis.tasks.locks import FOREGROUND_DESKTOP

__all__ = [
    "AutomationSession",
    "DesktopBusy",
    "UserTookOver",
    "LockManagerLike",
    "WatcherLike",
    "DEFAULT_LOCK_WAIT_SECONDS",
]

_LOG = logging.getLogger(__name__)

#: How long to wait for the desktop before giving up. Bounded, like every wait
#: in this codebase: an unbounded one turns a contended lock into a hang with no
#: explanation.
DEFAULT_LOCK_WAIT_SECONDS = 5.0


class DesktopBusy(RuntimeError):
    """Another task owns the desktop. Not an error in the caller."""


class UserTookOver(RuntimeError):
    """The user used the mouse or keyboard, so automation stopped (FR-078)."""


class LockManagerLike(Protocol):
    def acquire(self, owner_id: str, lock_names: Any, timeout_seconds: float = 0.0) -> Any: ...


class WatcherLike(Protocol):
    def unavailable_reason(self) -> str | None: ...

    def arm(self) -> None: ...

    def note_synthetic_input(self) -> None: ...

    def user_intervened(self) -> bool: ...


class AutomationSession:
    """Exclusive, interruptible ownership of the desktop, for one task."""

    def __init__(
        self,
        task_id: str,
        locks: LockManagerLike,
        watcher: WatcherLike,
        *,
        extra_locks: tuple[str, ...] = (),
        lock_wait_seconds: float = DEFAULT_LOCK_WAIT_SECONDS,
    ) -> None:
        self._task_id = task_id
        self._locks = locks
        self._watcher = watcher
        self._lock_names = (FOREGROUND_DESKTOP, *extra_locks)
        self._lock_wait_seconds = lock_wait_seconds
        self._lease: Any | None = None

    # -- lifecycle -----------------------------------------------------
    def __enter__(self) -> "AutomationSession":
        # Checked *before* taking the lock, so a refusal does not leave the
        # desktop held by a session that is about to fail.
        reason = self._watcher.unavailable_reason()
        if reason is not None:
            raise RuntimeError(
                f"Jarvis will not drive the desktop when it cannot tell that you "
                f"have taken over: {reason}"
            )

        lease = self._locks.acquire(
            self._task_id, self._lock_names, self._lock_wait_seconds
        )
        if lease is None:
            raise DesktopBusy(
                "another task is using the mouse and keyboard, so this one did "
                f"not start. Waited {self._lock_wait_seconds:.0f}s for "
                f"{list(self._lock_names)}."
            )

        self._lease = lease
        self._watcher.arm()
        _LOG.info("automation session %s owns %s", self._task_id, list(self._lock_names))
        return self

    def __exit__(self, *_exc: object) -> None:
        # Unconditional. A session that kept the lock after a failure would
        # wedge every later automation task, and a lock held by a live process
        # is never treated as stale.
        if self._lease is not None:
            self._lease.release()
            self._lease = None
            _LOG.info("automation session %s released the desktop", self._task_id)

    # -- doing something -----------------------------------------------
    def step(
        self,
        description: str,
        action: Callable[[str], Any],
        *,
        sends_input: bool = False,
    ) -> Any:
        """Perform one action, if the user has not taken over.

        ``sends_input`` must be true for anything that injects a keystroke or
        pointer event. A step that moves the pointer without declaring it leaves
        the watcher reading our own action as the user's, and the automation
        pauses itself for reasons nothing explains.
        """
        if self._lease is None:
            raise RuntimeError(
                "this step was attempted without owning the desktop; use the "
                "session as a context manager so the lock is taken first"
            )

        # At the boundary, never mid-action: stopping halfway through a click
        # or a keystroke leaves the desktop in a state nobody chose.
        if self._watcher.user_intervened():
            raise UserTookOver(
                f"you used the mouse or keyboard, so Jarvis stopped before "
                f"'{description}'. Nothing further was done."
            )

        result = action(description)

        if sends_input:
            # After the action, so the watcher's baseline includes it.
            self._watcher.note_synthetic_input()
        return result
