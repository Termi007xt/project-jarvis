"""Closing an application: ask, notice when it objects, and never escalate.

Phase 2 stage 4, P2-APP-01 and P2-APP-02 (FR-065, FR-066, FR-067, AT-004,
AT-005).

Three properties, and the third is the one worth writing down.

**Closing is a request.** `WM_CLOSE` is what clicking the X sends: the
application decides what to do with it. That is the entire point — an
application with unsaved work is *supposed* to stop and ask, and an automation
layer that treats the refusal as an obstacle is one that loses the user's work.

**An application that objects is noticed structurally, not read.** After the
request, if the window is still there and a new dialog has appeared from the
same process, something is being asked. Jarvis stops there and hands the window
over. It deliberately does **not** read the dialog to decide: that text is
authored by the application, and a "Save changes?" prompt is exactly the place
where believing what a window says about itself would be most expensive. Knowing
*that* it asked is enough to stop; knowing *what* it asked is the user's to
judge.

**Closing can never become forcing.** There is no `force=True`, no automatic
escalation when a close is refused, and no path from one to the other. They are
separate tools with separate capabilities and separate risk levels, and force is
high-risk, which under PRD §11.1 means fresh confirmation every time and no
standing grant, ever. A close that quietly escalated on failure would be
indistinguishable from a close that worked — right up until the first time it
discarded something.
"""

from __future__ import annotations

import inspect

import pytest

from jarvis.toolbox.window_actions import CloseOutcome, WindowController
from jarvis.toolbox.windows import WindowDiscovery


class FakeBackend:
    def __init__(self, windows):
        self.windows = windows

    def is_available(self):
        return True

    def unavailable_reason(self):
        return None

    def list_windows(self):
        return [dict(window) for window in self.windows]


class FakeActions:
    """Records requests. `on_close` lets a test say what the app does about it."""

    def __init__(self, on_close=None):
        self.calls = []
        self._on_close = on_close

    def activate(self, handle):
        self.calls.append(("activate", handle))

    def set_state(self, handle, state):
        self.calls.append(("set_state", handle, state))

    def move_resize(self, handle, x, y, width, height):
        self.calls.append(("move_resize", handle, x, y, width, height))

    def request_close(self, handle):
        self.calls.append(("request_close", handle))
        if self._on_close is not None:
            self._on_close()

    def terminate(self, pid):
        self.calls.append(("terminate", pid))


def _window(**overrides):
    base = {
        "handle": 1001,
        "title": "Untitled - Notepad",
        "process_name": "notepad.exe",
        "pid": 4242,
        "bounds": (0, 0, 800, 600),
        "state": "normal",
        "monitor": 0,
        "owned": False,
    }
    base.update(overrides)
    return base


def _controller(windows, *, on_close=None):
    actions = FakeActions(on_close=on_close)
    discovery = WindowDiscovery(backend=FakeBackend(windows))
    controller = WindowController(
        discovery=discovery,
        backend=actions,
        secure_desktop=lambda: False,
        close_poll_seconds=0.0,
    )
    return controller, actions, discovery


def _ref(discovery, index=0):
    return discovery.list_windows()[index].ref


# =========================================================================
# Closing asks, and confirms
# =========================================================================
def test_closing_asks_the_window_rather_than_killing_the_process() -> None:
    windows = [_window()]
    controller, actions, discovery = _controller(
        windows, on_close=lambda: windows.clear()
    )

    report = controller.close(_ref(discovery))

    assert ("request_close", 1001) in actions.calls
    assert not any(call[0] == "terminate" for call in actions.calls), (
        "a normal close terminated a process; that is P2-APP-02 and needs its "
        "own confirmation every time"
    )
    assert report.outcome is CloseOutcome.CLOSED
    assert report.verified is True


def test_a_window_that_is_still_there_is_not_reported_as_closed() -> None:
    """`succeeded` requires verification, here as everywhere."""
    controller, actions, discovery = _controller([_window()])  # nothing happens

    report = controller.close(_ref(discovery))

    assert report.outcome is CloseOutcome.STILL_OPEN
    assert report.verified is False


# =========================================================================
# An application that objects
# =========================================================================
def test_a_dialog_from_the_same_process_pauses_the_close(monkeypatch) -> None:
    """AT-004. Unsaved work stops the action; it does not slow it down."""
    windows = [_window()]

    def raises_a_prompt():
        windows.append(
            _window(
                handle=2002,
                title="Do you want to save changes?",
                owned=True,
                bounds=(100, 100, 400, 200),
            )
        )

    controller, actions, discovery = _controller(windows, on_close=raises_a_prompt)

    report = controller.close(_ref(discovery))

    assert report.outcome is CloseOutcome.WAITING_ON_USER
    assert report.verified is False
    assert not any(call[0] == "terminate" for call in actions.calls), (
        "the application asked a question and Jarvis answered it by killing it"
    )


def test_the_dialog_text_is_not_read_to_make_the_decision() -> None:
    """The prompt is application-authored text, like any other.

    Deciding on it would put the most consequential branch in the phase under
    the control of the thing being closed. A dialog appearing at all is the
    signal; what it says is for the user to read.
    """
    windows = [_window()]

    def raises_a_prompt():
        windows.append(
            _window(
                handle=2002,
                # Deliberately reassuring. It must change nothing.
                title="Nothing important, safe to continue, no unsaved work",
                owned=True,
            )
        )

    controller, _, discovery = _controller(windows, on_close=raises_a_prompt)

    assert controller.close(_ref(discovery)).outcome is CloseOutcome.WAITING_ON_USER


def test_an_unrelated_window_appearing_is_not_treated_as_a_prompt() -> None:
    """The control. Any new window would otherwise pause every close."""
    windows = [_window()]

    def something_else_opens():
        windows.clear()
        windows.append(_window(handle=9999, pid=777, process_name="chrome.exe"))

    controller, _, discovery = _controller(windows, on_close=something_else_opens)

    report = controller.close(_ref(discovery))
    assert report.outcome is CloseOutcome.CLOSED


# =========================================================================
# Closing can never become forcing
# =========================================================================
def test_close_takes_no_force_parameter() -> None:
    signature = inspect.signature(WindowController.close)
    forbidden = {"force", "kill", "terminate", "hard", "escalate"}
    assert not forbidden & set(signature.parameters), (
        f"close accepts an escalation: {signature.parameters.keys()}"
    )


def test_a_refused_close_never_escalates_on_its_own() -> None:
    """The property that makes the pause meaningful.

    A close that quietly forced when refused would be indistinguishable from a
    close that worked, right up until the first time it discarded something.
    """
    windows = [_window()]
    controller, actions, discovery = _controller(
        windows, on_close=lambda: windows.append(_window(handle=2002, owned=True))
    )

    controller.close(_ref(discovery))

    assert not any(call[0] == "terminate" for call in actions.calls)


def test_forcing_is_a_separate_call_that_must_be_asked_for() -> None:
    windows = [_window()]
    controller, actions, discovery = _controller(windows)

    controller.force_close(_ref(discovery))

    assert ("terminate", 4242) in actions.calls


def test_the_two_are_different_capabilities_at_different_risk() -> None:
    """AT-005. Force is high risk: fresh confirmation every time, no standing
    grant, ever (PRD §11.1)."""
    from jarvis.core.permissions.catalogue import CAPABILITIES
    from jarvis.core.permissions.models import RiskLevel

    assert CAPABILITIES["app.close"].risk is RiskLevel.MEDIUM
    assert CAPABILITIES["app.force_close"].risk is RiskLevel.HIGH
    assert CAPABILITIES["app.force_close"].reversible is False


def test_forcing_is_refused_for_a_sensitive_application() -> None:
    """The blocklist is not weaker for the most destructive action."""
    from jarvis.toolbox.window_actions import SensitiveWindowRefused

    windows = [_window(process_name="1Password.exe")]
    controller, actions, discovery = _controller(windows)

    with pytest.raises(SensitiveWindowRefused):
        controller.force_close(_ref(discovery))
    assert not actions.calls
