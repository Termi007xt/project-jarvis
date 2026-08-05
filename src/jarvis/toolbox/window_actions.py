"""Moving windows (FR-241, FR-242, FR-243, P2-WIN-09).

Phase 2 stage 4, the acting half of window management. Separate from
`jarvis.toolbox.windows` on purpose: discovery is read-only and stays that way,
because a module that could both see and act would be a second route from a plan
to an effect.

**The guards run here, not only where they were written.** `SensitiveTargets`
and `secure_desktop_active` were built first, in P2-WIN-06 and P2-WIN-07, and
this codebase has now produced the same failure three times — a correct
mechanism, unit-tested, connected to nothing. Always-listening was gated on a
flag that could never be true; the browser tools were registered against a
workspace that could never open a browser; the browser thread existed while the
tools drove Playwright from a different one. Each passed its own tests. So every
entry point below re-checks, and `tests/unit/test_window_actions.py` exercises
the refusals *through the actions* rather than against the guard in isolation.

**Asked is not done.** A window told to maximise may not: some refuse, some
belong to a process that ignores the message, and Windows clamps geometry to
minimum sizes and to the work area. So every action reads the window back and
reports `verified` only when what was asked for is what is now true. Anything
else is `unverified`, which by design never satisfies a task's success criteria
(FR-048).

**A window is named by reference, not by position.** Positions were the original
design and were wrong for this: an index into a list that reorders whenever
anything moves. On 2026-08-05 *"move my code editor to the left half"* moved the
Jarvis window, because by the time the call arrived the position the model had
chosen meant something else — and the action then verified against the window it
really moved and reported success, truthfully, about the wrong thing.

A reference is an opaque token minted by `window.list` and bound to a window
handle. It means the same window however the desktop reorders, and it cannot be
forged: a model that has not listed a window has no token for it, and a window
cannot mint one for itself by changing its title. Nothing here takes a title, for
that last reason.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Callable, Protocol

from jarvis.toolbox.sensitive import secure_desktop_active
from jarvis.toolbox.windows import WindowDiscovery, WindowInfo, WindowState

__all__ = [
    "WindowController",
    "WindowActionReport",
    "WindowActionBackend",
    "Win32ActionBackend",
    "SecureDesktopActive",
    "SensitiveWindowRefused",
]

_LOG = logging.getLogger(__name__)


class SecureDesktopActive(RuntimeError):
    """Windows is showing a UAC prompt, the lock screen or Ctrl+Alt+Del."""


class SensitiveWindowRefused(RuntimeError):
    """The target is on the sensitive-application list (FR-081, AT-031)."""


@dataclass(frozen=True)
class WindowActionReport:
    """What was asked, and what is actually true afterwards."""

    ref: str
    action: str
    verified: bool
    state: WindowState
    bounds: tuple[int, int, int, int]
    detail: str


class WindowActionBackend(Protocol):
    """What the controller needs from a windowing implementation."""

    def activate(self, handle: int) -> None: ...

    def set_state(self, handle: int, state: str) -> None: ...

    def move_resize(self, handle: int, x: int, y: int, width: int, height: int) -> None: ...


class Win32ActionBackend:
    """The real backend, via ctypes. Windows only.

    Every call here is a *request* to the window, in the same sense that
    clicking a title bar button is. Nothing forces, nothing terminates: forcing
    is P2-APP-02 and needs its own confirmation every time.
    """

    _SHOW = {
        WindowState.NORMAL.value: 9,  # SW_RESTORE
        WindowState.MINIMISED.value: 6,  # SW_MINIMIZE
        WindowState.MAXIMISED.value: 3,  # SW_MAXIMIZE
    }

    def activate(self, handle: int) -> None:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        if user32.IsIconic(handle):
            user32.ShowWindow(handle, 9)  # SW_RESTORE
        user32.SetForegroundWindow(handle)

    def set_state(self, handle: int, state: str) -> None:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        user32.ShowWindow(handle, self._SHOW.get(state, 9))

    def move_resize(self, handle: int, x: int, y: int, width: int, height: int) -> None:
        import ctypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        # A maximised window ignores MoveWindow, so restore it first — otherwise
        # the call silently does nothing and the verification below would be the
        # only thing that noticed.
        if user32.IsZoomed(handle):
            user32.ShowWindow(handle, 9)  # SW_RESTORE
        user32.MoveWindow(handle, x, y, width, height, True)


@dataclass
class WindowController:
    """Acts on windows, by position, once the guards have allowed it."""

    discovery: WindowDiscovery
    backend: WindowActionBackend
    #: Injected so the refusal is testable without a real UAC prompt.
    secure_desktop: Callable[[], bool] = secure_desktop_active

    # -- guards -----------------------------------------------------------
    def _target(self, ref: str) -> WindowInfo:
        """Resolve a reference to a window, refusing before anything moves.

        Both checks run on every entry point. The secure desktop first, because
        while it is up nothing about the ordinary desktop can be acted on at
        all, and re-reading the window list would only produce a stale answer.
        """
        if self.secure_desktop():
            raise SecureDesktopActive(
                "Windows is showing a secure screen — a UAC prompt, the lock "
                "screen or Ctrl+Alt+Del. Nothing can be automated while it is "
                "up, and Jarvis will not try. Deal with the prompt and ask again."
            )

        handle = self.discovery.resolve(ref)
        window = next(
            (w for w in self.discovery.list_windows() if w.handle == handle), None
        )
        if window is None:  # pragma: no cover - resolve has already checked
            raise KeyError("that window has been closed since it was listed.")

        if window.sensitive:
            raise SensitiveWindowRefused(
                f"that window belongs to '{window.process_name}', which is on "
                "the sensitive-application list. Jarvis does not automate it. "
                "The list is editable in Settings; this cannot be approved at "
                "the time of asking."
            )
        return window

    def _reread(self, handle: int) -> WindowInfo | None:
        """The window as it is *now*, found by **handle**. Verification.

        By handle and never by position, because acting on a window reorders the
        list. `EnumWindows` returns z-order, so minimising the window at
        position 0 moves it down and position 0 becomes something else entirely.

        `tools/window-lab/test_window_actions_live.py` caught this against a
        real desktop on 2026-08-05: it opened its own Notepad window, minimised
        it, and then reported *"asked 'Antigravity IDE.exe' to become minimised"*
        — verifying against a window nobody had touched, and going on to move
        the IDE. A position is how a person names a window in a list they were
        just shown; it is not an identity, because the list does not hold still.
        """
        for window in self.discovery.list_windows():
            if window.handle == handle:
                return window
        return None

    # -- actions ----------------------------------------------------------
    def activate(self, ref: str) -> WindowActionReport:
        """Bring a window to the front (FR-241)."""
        window = self._target(ref)
        self.backend.activate(window.handle)
        after = self._reread(window.handle)
        if after is None:
            return self._vanished(ref, "activate", window)
        # Foreground is not readable from the window list, so this reports what
        # it can confirm — the window still exists and is no longer minimised —
        # rather than claiming a foreground change it has not observed.
        verified = after.state is not WindowState.MINIMISED
        return WindowActionReport(
            ref=ref,
            action="activate",
            verified=verified,
            state=after.state,
            bounds=after.bounds,
            detail=(
                f"brought '{after.process_name}' to the front."
                if verified
                else "the window was asked to come forward but is still minimised."
            ),
        )

    @staticmethod
    def _vanished(ref: str, action: str, window: WindowInfo) -> WindowActionReport:
        """The window closed while we were acting on it.

        Not found is not the same as did not work — it may well have worked and
        then been closed — but it is certainly not confirmation, and this phase
        only calls something verified when it has been read back.
        """
        return WindowActionReport(
            ref=ref,
            action=action,
            verified=False,
            state=window.state,
            bounds=window.bounds,
            detail=(
                f"'{window.process_name}' is gone — it was closed while the "
                "action was running, so the result could not be confirmed."
            ),
        )

    def set_state(self, ref: str, state: WindowState) -> WindowActionReport:
        """Minimise, maximise or restore (FR-242)."""
        window = self._target(ref)
        self.backend.set_state(window.handle, state.value)
        after = self._reread(window.handle)
        if after is None:
            return self._vanished(ref, f"set_state:{state.value}", window)
        verified = after.state is state
        return WindowActionReport(
            ref=ref,
            action=f"set_state:{state.value}",
            verified=verified,
            state=after.state,
            bounds=after.bounds,
            detail=(
                f"'{after.process_name}' is now {state.value}."
                if verified
                else (
                    f"asked '{after.process_name}' to become {state.value}, but it "
                    f"is {after.state.value}. Some windows refuse; reporting this "
                    "as unverified rather than as success."
                )
            ),
        )

    def move_resize(
        self, ref: str, x: int, y: int, width: int, height: int
    ) -> WindowActionReport:
        """Place a window (FR-243).

        Windows enforces minimum sizes and keeps windows within the work area,
        so the geometry that results is frequently not the geometry requested.
        That is a fact worth reporting rather than rounding up.
        """
        window = self._target(ref)
        self.backend.move_resize(window.handle, x, y, width, height)
        after = self._reread(window.handle)
        if after is None:
            return self._vanished(ref, "move_resize", window)
        verified = after.bounds == (x, y, width, height)
        return WindowActionReport(
            ref=ref,
            action="move_resize",
            verified=verified,
            state=after.state,
            bounds=after.bounds,
            detail=(
                f"placed '{after.process_name}' at {after.bounds}."
                if verified
                else (
                    f"asked for {(x, y, width, height)} but the window is at "
                    f"{after.bounds}. Windows clamps to minimum sizes and to the "
                    "work area; reporting where it actually is."
                )
            ),
        )


def screen_work_area() -> tuple[int, int, int, int]:
    """The usable desktop, excluding the taskbar. (0, 0, 0, 0) off Windows."""
    if os.name != "nt":
        return (0, 0, 0, 0)
    try:
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        # SPI_GETWORKAREA = 0x0030
        ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
            0x0030, 0, ctypes.byref(rect), 0
        )
        return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
    except Exception:  # noqa: BLE001
        _LOG.debug("could not read the work area", exc_info=True)
        return (0, 0, 0, 0)
