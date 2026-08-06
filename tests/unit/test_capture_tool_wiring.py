"""The capture tool, as the running application actually has it (P2-WIN-10).

`tests/security/test_screen_capture.py` proves the policy: the indicator comes
first, blocklisted windows are blacked out, and a capture with no indicator
refuses. Every one of those assertions is about a `ScreenCapture` the test built
itself.

This file asks the question that keeps being the one that matters here: **is any
of it reachable from the running product?** The same failure has now appeared
four times — always-listening gated on a flag that could never be true, browser
tools registered against a workspace that could never open a browser, a browser
thread that the tools did not use, and a window list whose filter was never
applied to the close path. Each had passing tests of its own.

So: the tool must be registered, it must reach something that can really
capture, and it must not exist at all until something can show the user that it
is happening.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.toolbox.capture import ScreenCapture, gdi_screen_grab
from jarvis.toolbox.phase2_capture_tools import (
    CAPTURE_KEEP_COUNT,
    ScreenCaptureTool,
    prune_captures,
    register_capture_tool,
)
from jarvis.toolbox.windows import WindowDiscovery


class FakeRegistry:
    def __init__(self) -> None:
        self.registered: list[object] = []

    def register(self, tool: object) -> None:
        self.registered.append(tool)

    def get(self, tool_id: str):
        return next(
            (t for t in self.registered if t.spec.tool_id == tool_id), None
        )


class FakeBackend:
    def is_available(self):
        return True

    def unavailable_reason(self):
        return None

    def list_windows(self):
        return []

    def window_exists(self, handle):
        return False


def _capture(indicator=None) -> ScreenCapture:
    return ScreenCapture(
        discovery=WindowDiscovery(backend=FakeBackend()),
        grab=gdi_screen_grab,
        indicator=indicator,
    )


# =========================================================================
# Reachable, and only when it can announce itself
# =========================================================================
def test_the_tool_is_not_registered_without_an_indicator(tmp_path) -> None:
    """FR-271, at the wiring level.

    Not "registers and then always fails" — absent. A tool that can never
    succeed reads as a defect rather than as a capability that is not available
    (ADR-0010), and a registered capture tool implies capture is possible.
    """
    registry = FakeRegistry()

    assert register_capture_tool(registry, _capture(indicator=None), tmp_path) is None
    assert registry.registered == []


def test_the_tool_is_registered_once_an_indicator_exists(tmp_path) -> None:
    registry = FakeRegistry()

    tool_id = register_capture_tool(
        registry, _capture(indicator=lambda _m: None), tmp_path
    )

    assert tool_id == "screen.capture"
    assert registry.get("screen.capture") is not None


def test_the_registered_tool_reaches_something_that_can_really_capture(tmp_path) -> None:
    """The seam. A tool wired to a stub would pass every test above."""
    registry = FakeRegistry()
    register_capture_tool(registry, _capture(indicator=lambda _m: None), tmp_path)
    tool = registry.get("screen.capture")

    assert tool._capture.grab is gdi_screen_grab, (
        "the registered tool is not connected to the real screen grab"
    )


def test_the_model_cannot_choose_where_the_image_goes() -> None:
    """A capture tool that took a path would be a file-write primitive.

    The model could aim it anywhere the user can write, and where an image ends
    up would become a question answered by untrusted input.
    """
    fields = set(ScreenCaptureTool.spec.input_model.model_fields)
    forbidden = {"path", "destination", "directory", "filename", "file"}

    assert not fields & forbidden, f"the input accepts a destination: {fields}"


def test_the_capability_and_risk_are_what_the_catalogue_says() -> None:
    from jarvis.core.permissions.catalogue import CAPABILITIES

    assert ScreenCaptureTool.spec.required_capabilities == ("screen.capture",)
    assert (
        ScreenCaptureTool.spec.risk is CAPABILITIES["screen.capture"].risk
    ), "the tool and the catalogue disagree about how risky capturing is"


# =========================================================================
# The folder cannot grow without limit
# =========================================================================
def test_old_captures_are_pruned(tmp_path) -> None:
    """A full-screen BMP is ~15MB, so this fills a disk quietly.

    Not a retention policy — `privacy.screenshot_retention` describes what the
    product should eventually do. This is only the bound that stops the vault
    growing forever while that is unbuilt.
    """
    for index in range(CAPTURE_KEEP_COUNT + 5):
        path = tmp_path / f"capture-{index:04d}.bmp"
        path.write_bytes(b"x")
        # Distinct timestamps, so "oldest" is well defined on a fast filesystem.
        import os

        os.utime(path, (index, index))

    removed = prune_captures(tmp_path)

    remaining = sorted(p.name for p in tmp_path.glob("capture-*.bmp"))
    assert removed == 5
    assert len(remaining) == CAPTURE_KEEP_COUNT
    assert "capture-0000.bmp" not in remaining, "the oldest capture survived"
    assert f"capture-{CAPTURE_KEEP_COUNT + 4:04d}.bmp" in remaining


def test_pruning_leaves_anything_that_is_not_a_capture_alone(tmp_path) -> None:
    keeper = tmp_path / "notes.txt"
    keeper.write_text("not a screenshot")

    prune_captures(tmp_path, keep=0)

    assert keeper.exists(), "pruning deleted a file it did not create"
