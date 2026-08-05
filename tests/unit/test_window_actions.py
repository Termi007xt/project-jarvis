"""Moving windows: refused where it must be, and never assumed to have worked.

Phase 2 stage 4, P2-WIN-09 (FR-241, FR-242, FR-243). The acting half of window
management, separate from `WindowDiscovery` because a module that could both see
and act would be a second route from a plan to an effect.

The guards written in P2-WIN-06 and P2-WIN-07 exist. This is where they either
become real or become decoration — and this codebase has produced the second
outcome three times now: a correct mechanism, unit-tested, wired to nothing.
`always_listening` was gated on a flag that was permanently false; the browser
tools were registered against a workspace that could never open; the browser
thread existed and the tools drove Playwright from a different one. Every one
passed its own tests.

So the refusal tests here call the *action*, not the guard.

And `succeeded` requires verification. A window asked to maximise is not a
window that maximised — some refuse, some are owned by a process that ignores
the request. The state is read back, and a request that did not take effect is
`unverified`, which by design never satisfies a task's success criteria.
"""

from __future__ import annotations

import inspect

import pytest

from jarvis.toolbox.sensitive import SensitiveTargets
from jarvis.toolbox.window_actions import (
    SecureDesktopActive,
    SensitiveWindowRefused,
    WindowController,
)
from jarvis.toolbox.windows import WindowDiscovery, WindowState


class FakeBackend:
    def __init__(self, windows: list[dict]) -> None:
        self._windows = windows

    def is_available(self) -> bool:
        return True

    def unavailable_reason(self) -> str | None:
        return None

    def list_windows(self) -> list[dict]:
        return [dict(window) for window in self._windows]


class FakeActionBackend:
    """Records what was asked, and lets a test say it did not work."""

    def __init__(self, *, obeys: bool = True) -> None:
        self.calls: list[tuple] = []
        self.obeys = obeys

    def activate(self, handle: int) -> None:
        self.calls.append(("activate", handle))

    def set_state(self, handle: int, state: str) -> None:
        self.calls.append(("set_state", handle, state))

    def move_resize(self, handle: int, x: int, y: int, width: int, height: int) -> None:
        self.calls.append(("move_resize", handle, x, y, width, height))


def _desktop(windows: list[dict], *, sensitive: SensitiveTargets | None = None):
    return WindowDiscovery(
        backend=FakeBackend(windows),
        sensitive=sensitive or SensitiveTargets(),
    )


def _window(**overrides) -> dict:
    base = {
        "handle": 1001,
        "title": "YouTube — Brave",
        "process_name": "brave.exe",
        "pid": 4242,
        "bounds": (0, 0, 800, 600),
        "state": "normal",
        "monitor": 0,
    }
    base.update(overrides)
    return base


def _controller(windows, *, obeys=True, secure=False, sensitive=None):
    actions = FakeActionBackend(obeys=obeys)
    controller = WindowController(
        discovery=_desktop(windows, sensitive=sensitive),
        backend=actions,
        secure_desktop=lambda: secure,
    )
    return controller, actions


# =========================================================================
# The guards, exercised through the action rather than directly
# =========================================================================
def test_an_action_on_a_sensitive_window_is_refused() -> None:
    """AT-031, reached the way the product reaches it."""
    controller, actions = _controller(
        [_window(process_name="1Password.exe", title="Vault")]
    )

    with pytest.raises(SensitiveWindowRefused) as raised:
        controller.activate(0)

    assert not actions.calls, "the window was moved before the refusal"
    assert "1password" in str(raised.value).casefold()


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.activate(0),
        lambda c: c.set_state(0, WindowState.MAXIMISED),
        lambda c: c.move_resize(0, 10, 10, 400, 300),
    ],
)
def test_every_action_refuses_a_sensitive_window(call) -> None:
    """One guarded entry point and two unguarded ones is the usual shape."""
    controller, actions = _controller(
        [_window(process_name="keepassxc.exe", title="secrets")]
    )
    with pytest.raises(SensitiveWindowRefused):
        call(controller)
    assert not actions.calls


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.activate(0),
        lambda c: c.set_state(0, WindowState.MINIMISED),
        lambda c: c.move_resize(0, 0, 0, 100, 100),
    ],
)
def test_nothing_moves_while_the_secure_desktop_is_up(call) -> None:
    """FR-079. A UAC prompt is not a window to work around.

    Automation cannot reach the secure desktop anyway, which is exactly why
    this must be a stated refusal: silently doing nothing is indistinguishable
    from a bug, and ADR-0010 requires naming what is not possible.
    """
    controller, actions = _controller([_window()], secure=True)

    with pytest.raises(SecureDesktopActive):
        call(controller)
    assert not actions.calls


# =========================================================================
# Verification: asked is not done
# =========================================================================
def test_a_state_change_is_confirmed_by_reading_it_back() -> None:
    windows = [_window(state="normal")]
    actions = FakeActionBackend()
    discovery = _desktop(windows)

    # The backend "works": flip what discovery will report next.
    def set_state(handle: int, state: str) -> None:
        actions.calls.append(("set_state", handle, state))
        windows[0]["state"] = state

    actions.set_state = set_state  # type: ignore[method-assign]
    controller = WindowController(
        discovery=discovery, backend=actions, secure_desktop=lambda: False
    )

    report = controller.set_state(0, WindowState.MAXIMISED)

    assert report.verified is True
    assert report.state is WindowState.MAXIMISED


def test_a_window_that_ignored_the_request_is_unverified_not_succeeded() -> None:
    """Some windows refuse, and reporting that as success is the lie FR-048 bans."""
    controller, actions = _controller([_window(state="normal")], obeys=False)

    report = controller.set_state(0, WindowState.MAXIMISED)

    assert actions.calls, "the request was never made"
    assert report.verified is False
    assert "maximised" in report.detail.casefold()


def test_a_move_is_confirmed_against_the_bounds_actually_reported() -> None:
    windows = [_window(bounds=(0, 0, 800, 600))]
    actions = FakeActionBackend()

    def move_resize(handle, x, y, width, height):
        actions.calls.append(("move_resize", handle, x, y, width, height))
        windows[0]["bounds"] = (x, y, width, height)

    actions.move_resize = move_resize  # type: ignore[method-assign]
    controller = WindowController(
        discovery=_desktop(windows), backend=actions, secure_desktop=lambda: False
    )

    report = controller.move_resize(0, 100, 50, 640, 480)

    assert report.verified is True
    assert report.bounds == (100, 50, 640, 480)


def test_a_move_that_landed_somewhere_else_is_unverified() -> None:
    """Windows clamp to minimum sizes and to the work area. That is a fact to
    report, not one to round up into success."""
    windows = [_window(bounds=(0, 0, 800, 600))]
    actions = FakeActionBackend()

    def move_resize(handle, x, y, width, height):
        actions.calls.append(("move_resize", handle, x, y, width, height))
        windows[0]["bounds"] = (x, y, 300, 200)  # clamped by the OS

    actions.move_resize = move_resize  # type: ignore[method-assign]
    controller = WindowController(
        discovery=_desktop(windows), backend=actions, secure_desktop=lambda: False
    )

    report = controller.move_resize(0, 100, 50, 10, 10)

    assert report.verified is False
    assert report.bounds == (100, 50, 300, 200)


# =========================================================================
# A position names a window once; after that, identity is the handle
# =========================================================================
def test_verification_follows_the_window_not_the_position() -> None:
    """Found by `tools/window-lab/test_window_actions_live.py`, 2026-08-05.

    `EnumWindows` returns windows in z-order, so acting on one *reorders the
    list*. Minimising the window at position 0 dropped it down the order, and
    re-reading position 0 then described an entirely different window — the
    live run reported "asked 'Antigravity IDE.exe' to become minimised" about a
    Notepad window it had opened itself, and went on to move the IDE.

    A position is how a *person* names a window in a list they were just shown.
    It is not an identity, because the list is not stable. Once resolved, every
    subsequent step has to use the handle, or the verification is describing
    something other than the thing that was acted on — and "succeeded" would be
    reported against the wrong window entirely.
    """
    windows = [
        _window(handle=1, process_name="notepad.exe", title="Untitled", state="normal"),
        _window(handle=2, process_name="ide.exe", title="editor", state="maximised"),
    ]
    actions = FakeActionBackend()

    def set_state(handle: int, state: str) -> None:
        actions.calls.append(("set_state", handle, state))
        for entry in windows:
            if entry["handle"] == handle:
                entry["state"] = state
        # Acting on it sends it to the back of the z-order, exactly as Windows
        # does. Position 0 is now a different window.
        windows.append(windows.pop(0))

    actions.set_state = set_state  # type: ignore[method-assign]
    controller = WindowController(
        discovery=_desktop(windows), backend=actions, secure_desktop=lambda: False
    )

    report = controller.set_state(0, WindowState.MINIMISED)

    assert actions.calls == [("set_state", 1, "minimised")], "acted on the wrong window"
    assert report.verified is True, (
        "the window did minimise, but verification read whatever had moved into "
        "position 0 and reported failure against a window nobody touched"
    )
    assert report.state is WindowState.MINIMISED


def test_a_window_that_vanished_during_the_action_is_unverified() -> None:
    """Closed mid-action. Not found is not the same as did not work, but it is
    certainly not confirmation, so it cannot be `verified`."""
    windows = [_window(handle=1)]
    actions = FakeActionBackend()

    def set_state(handle: int, state: str) -> None:
        actions.calls.append(("set_state", handle, state))
        windows.clear()

    actions.set_state = set_state  # type: ignore[method-assign]
    controller = WindowController(
        discovery=_desktop(windows), backend=actions, secure_desktop=lambda: False
    )

    report = controller.set_state(0, WindowState.MAXIMISED)
    assert report.verified is False
    assert "gone" in report.detail.casefold() or "closed" in report.detail.casefold()


# =========================================================================
# Positional addressing
# =========================================================================
def test_a_position_past_the_end_is_refused_clearly() -> None:
    controller, actions = _controller([_window()])
    with pytest.raises(IndexError) as raised:
        controller.activate(5)
    assert "5" in str(raised.value)
    assert not actions.calls


def test_no_action_accepts_a_title() -> None:
    """Structural. A title parameter is how a window retargets an action."""
    for name in ("activate", "set_state", "move_resize"):
        signature = inspect.signature(getattr(WindowController, name))
        assert "title" not in signature.parameters, f"{name} takes a title"
        assert "position" in signature.parameters, f"{name} is not positional"
