"""The window tools are connected to a real desktop, or say why they are not.

This project has now shipped the same defect four times: a correct mechanism,
unit-tested, connected to nothing.

* `always_listening` was gated on `enrolled`, which is permanently false.
* `youtube.search` was registered against a workspace that could never open a
  browser.
* `BrowserWorkspace` owned a thread and the tools drove Playwright from another.
* `voice.speak` declared a resource lock that did not exist.

Every one passed its own unit tests, because every one *worked* — in isolation,
against nothing. So this file asserts the seam rather than the units: that the
registered tool reaches something that can act, that both tools share one
blocklist, and that a refusal survives the trip through the tool.
"""

from __future__ import annotations

import pytest

from jarvis.core.tools.contract import ToolContext, ToolFailure
from jarvis.toolbox.phase2_window_tools import (
    WindowArrangeAction,
    WindowArrangeInput,
    WindowArrangeTool,
    WindowListInput,
    WindowListTool,
)
from jarvis.toolbox.sensitive import SensitiveTargets
from jarvis.toolbox.window_actions import WindowController
from jarvis.toolbox.windows import SENSITIVE_TITLE_REDACTION, WindowDiscovery


class FakeBackend:
    def __init__(self, windows):
        self._windows = windows

    def is_available(self):
        return True

    def unavailable_reason(self):
        return None

    def list_windows(self):
        return [dict(window) for window in self._windows]


class FakeActions:
    def __init__(self):
        self.calls = []

    def activate(self, handle):
        self.calls.append(("activate", handle))

    def set_state(self, handle, state):
        self.calls.append(("set_state", handle, state))

    def move_resize(self, handle, x, y, width, height):
        self.calls.append(("move_resize", handle, x, y, width, height))


def _window(**overrides):
    base = {
        "handle": 1001,
        "title": "YouTube — Brave",
        "process_name": "brave.exe",
        "pid": 1,
        "bounds": (0, 0, 800, 600),
        "state": "normal",
        "monitor": 0,
    }
    base.update(overrides)
    return base


# =========================================================================
# The seam in the running application
# =========================================================================
def test_the_core_registers_the_window_tools(core) -> None:
    assert {"window.list", "window.arrange"} <= set(core.registry.tool_ids())


def test_the_core_gives_the_tools_something_that_can_actually_act(core) -> None:
    """The seam itself.

    Without a controller the arrange tool is registered, enabled, offered to the
    planner, and permanently inert — which reads as a working feature to every
    unit test and as a dead end to the user.
    """
    assert core.window_discovery is not None
    assert core.window_controller is not None
    assert core.window_controller.backend is not None, (
        "window.arrange is registered but has no backend, so it can never move "
        "anything"
    )


def test_the_controller_reads_the_same_desktop_the_listing_showed(core) -> None:
    """One discovery, not two.

    Two instances would drift: the listing the model was shown and the list the
    action indexes into would be different reads of a moving desktop, and the
    position would mean different windows in each.
    """
    assert core.window_controller.discovery is core.window_discovery


def test_the_listing_and_the_action_share_one_blocklist(core) -> None:
    """A window hidden from the list must not be arrangeable through the tool.

    Two blocklists is how a window ends up unlistable but movable — the guard
    present in one place and absent in the other, with nothing comparing them.
    """
    assert (
        core.window_controller.discovery.sensitive is core.window_discovery.sensitive
    )


# =========================================================================
# A refusal survives the trip through the tool
# =========================================================================
def _tools(windows, sensitive=None):
    discovery = WindowDiscovery(
        backend=FakeBackend(windows), sensitive=sensitive or SensitiveTargets()
    )
    actions = FakeActions()
    controller = WindowController(
        discovery=discovery, backend=actions, secure_desktop=lambda: False
    )
    return WindowListTool(discovery), WindowArrangeTool(controller), actions, discovery


def _first_ref(discovery) -> str:
    """Name a window the way the model does: by listing it first."""
    return discovery.list_windows()[0].ref


def test_arranging_a_sensitive_window_is_a_declared_failure() -> None:
    """Not a crash, and not a silent no-op."""
    _, arrange, actions, discovery = _tools([_window(process_name="1Password.exe")])

    with pytest.raises(ToolFailure) as raised:
        arrange.run(
            ToolContext(),
            WindowArrangeInput(
                window=_first_ref(discovery), action=WindowArrangeAction.MAXIMISE
            ),
        )

    assert raised.value.code == "sensitive_window"
    assert raised.value.code in WindowArrangeTool.spec.failure_codes
    assert not actions.calls, "the window moved before the refusal"


def test_the_listing_withholds_a_sensitive_title_at_the_tool_boundary() -> None:
    """The boundary the model actually reads, not the one inside discovery."""
    listing, _, _, _ = _tools([_window(process_name="bitwarden.exe", title="my vault")])

    execution = listing.run(ToolContext(), WindowListInput())

    assert "my vault" not in repr(execution.output)
    assert execution.output.windows[0].title == SENSITIVE_TITLE_REDACTION
    assert execution.output.windows[0].sensitive is True


def test_a_window_that_ignored_the_request_is_reported_unverified() -> None:
    """`succeeded` requires verification, all the way out through the tool."""
    from jarvis.core.tools.contract import Verification

    _, arrange, _, discovery = _tools([_window(state="normal")])

    execution = arrange.run(
        ToolContext(),
        WindowArrangeInput(
            window=_first_ref(discovery), action=WindowArrangeAction.MAXIMISE
        ),
    )

    assert execution.verification is Verification.UNVERIFIED
    assert execution.output.verified is False


# =========================================================================
# The input type refuses what it cannot do
# =========================================================================
def test_move_without_geometry_is_refused_at_the_schema() -> None:
    with pytest.raises(ValueError) as raised:
        WindowArrangeInput(window="win-abc", action=WindowArrangeAction.MOVE)
    assert "snap_left" in str(raised.value), "say what to use instead (ADR-0010)"


def test_geometry_on_a_non_move_action_is_refused() -> None:
    """Otherwise it is silently ignored, which reads as the action having worked."""
    with pytest.raises(ValueError):
        WindowArrangeInput(
            window="win-abc",
            action=WindowArrangeAction.MAXIMISE,
            x=0,
            y=0,
            width=10,
            height=10,
        )


def test_there_is_no_title_parameter() -> None:
    assert "title" not in WindowArrangeInput.model_fields
    assert "window" in WindowArrangeInput.model_fields
    assert "position" not in WindowArrangeInput.model_fields, (
        "a position is an index into a list that reorders; that is what moved "
        "the wrong window on 2026-08-05"
    )
