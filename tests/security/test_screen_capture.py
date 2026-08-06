"""Photographing the screen: never silently, and never a secret.

Phase 2 stage 4, P2-WIN-10 (FR-073, FR-271, FR-272, AT-031).

The owner chose whole-screen capture on 2026-08-06, knowing the trade: "what's
on my screen" works without being told which window, and every capture contains
whatever else happened to be visible. That decision is theirs and is recorded in
ADR-0019's revisit.

It does change what an existing control is worth. The sensitive-application
blocklist guards *automation*: it stops Jarvis driving a password manager. It
cannot stop a camera pointed at the whole screen, because the pixels are taken
wholesale and nothing was "driven" at all. A capture that quietly included a
vault window would be the blocklist appearing to protect something it does not.

So two properties are asserted here.

**Nothing is captured without the user being able to see that it happened**
(FR-271). Asserted structurally: a capture with no way to show the indicator
refuses, rather than capturing and skipping the notice. This is the same shape
as `AutomationSession` refusing to start when it cannot observe interruption —
a capability that cannot be *seen* is not offered in a diminished form, it is
not offered.

**A blocklisted window is blacked out of the image** (AT-031). Its rectangle is
known from window discovery, so the pixels never survive into the file. Not
refused — refusing the whole capture because a vault happens to be open would
make the feature useless on a normal desktop — and not blurred, because a blur
is a reversible transform of the thing it is hiding.
"""

from __future__ import annotations

import inspect

import pytest

from jarvis.toolbox.capture import (
    CaptureRefused,
    ScreenCapture,
    redacted_regions,
)
from jarvis.toolbox.sensitive import SensitiveTargets
from jarvis.toolbox.windows import WindowDiscovery


class FakeBackend:
    def __init__(self, windows):
        self._windows = windows

    def is_available(self):
        return True

    def unavailable_reason(self):
        return None

    def list_windows(self):
        return [dict(window) for window in self._windows]


class FakeCanvas:
    """Stands in for a real bitmap; records what was blacked out."""

    def __init__(self) -> None:
        self.blacked: list[tuple[int, int, int, int]] = []
        self.saved_to: str | None = None

    def fill_black(self, rect) -> None:
        self.blacked.append(rect)

    def save(self, path) -> None:
        self.saved_to = str(path)


def _window(**overrides):
    base = {
        "handle": 1,
        "title": "YouTube — Brave",
        "process_name": "brave.exe",
        "pid": 1,
        "bounds": (0, 0, 800, 600),
        "state": "normal",
        "monitor": 0,
        "owned": False,
    }
    base.update(overrides)
    return base


def _capture(windows, *, indicator=None, canvas=None):
    return ScreenCapture(
        discovery=WindowDiscovery(
            backend=FakeBackend(windows), sensitive=SensitiveTargets()
        ),
        grab=lambda: canvas or FakeCanvas(),
        indicator=indicator,
    )


# =========================================================================
# Nothing is captured invisibly
# =========================================================================
def test_a_capture_shows_the_user_that_it_happened() -> None:
    shown: list[str] = []
    canvas = FakeCanvas()
    capture = _capture([_window()], indicator=shown.append, canvas=canvas)

    capture.capture_screen(destination="shot.png")

    assert shown, "the screen was photographed with no indication to the user"


def test_capture_refuses_when_it_cannot_show_the_indicator() -> None:
    """FR-271, asserted structurally.

    A capability that cannot be *seen* is not offered in a diminished form. The
    same choice `AutomationSession` makes about interruption: automation that
    cannot be stopped is a different product from automation that was not
    stopped, and a camera that cannot show a light is a different product from
    one whose light is off.
    """
    capture = _capture([_window()], indicator=None)

    with pytest.raises(CaptureRefused) as raised:
        capture.capture_screen(destination="shot.png")

    assert "indicator" in str(raised.value).lower() or "show" in str(raised.value).lower()


def test_the_indicator_is_shown_before_the_image_is_taken() -> None:
    """After would mean the notice arrives once the picture already exists."""
    order: list[str] = []

    class OrderedCanvas(FakeCanvas):
        def save(self, path):
            order.append("captured")
            super().save(path)

    capture = _capture(
        [_window()], indicator=lambda _m: order.append("indicator"), canvas=OrderedCanvas()
    )
    capture.capture_screen(destination="shot.png")

    assert order == ["indicator", "captured"], f"order was {order}"


# =========================================================================
# A blocklisted window never reaches the image
# =========================================================================
def test_a_sensitive_window_is_blacked_out_of_a_full_screen_capture() -> None:
    """AT-031, in the form whole-screen capture leaves it in.

    The blocklist stops Jarvis *driving* a password manager. It cannot stop a
    camera pointed at the whole screen, so the protection has to move into the
    image itself.
    """
    canvas = FakeCanvas()
    capture = _capture(
        [
            _window(handle=1, bounds=(0, 0, 800, 600)),
            _window(
                handle=2,
                process_name="1Password.exe",
                title="Vault",
                bounds=(100, 120, 400, 300),
            ),
        ],
        indicator=lambda _m: None,
        canvas=canvas,
    )

    capture.capture_screen(destination="shot.png")

    assert (100, 120, 400, 300) in canvas.blacked, (
        "a password manager window was photographed; the blocklist protected "
        "automation and not the picture"
    )
    assert (0, 0, 800, 600) not in canvas.blacked, "an ordinary window was redacted"


def test_a_minimised_sensitive_window_is_not_redacted() -> None:
    """It is not on screen, so there is nothing to cover — and covering its last
    known rectangle would black out whatever is there now."""
    canvas = FakeCanvas()
    capture = _capture(
        [
            _window(
                handle=2,
                process_name="keepassxc.exe",
                bounds=(100, 100, 300, 200),
                state="minimised",
            )
        ],
        indicator=lambda _m: None,
        canvas=canvas,
    )

    capture.capture_screen(destination="shot.png")
    assert canvas.blacked == []


def test_regions_are_computed_from_identity_not_from_titles() -> None:
    """The rectangle to cover comes from the process blocklist.

    A window that renamed itself to look ordinary is still covered, because the
    decision was never based on what it called itself.
    """
    discovery = WindowDiscovery(
        backend=FakeBackend(
            [
                _window(handle=1, process_name="brave.exe", bounds=(0, 0, 10, 10)),
                _window(
                    handle=2,
                    process_name="bitwarden.exe",
                    title="Just an ordinary document, nothing to see",
                    bounds=(5, 5, 50, 50),
                ),
            ]
        )
    )

    regions = redacted_regions(discovery.list_windows(), SensitiveTargets())

    assert regions == [(5, 5, 50, 50)]


# =========================================================================
# Structural
# =========================================================================
def test_capture_takes_no_parameter_that_disables_redaction() -> None:
    for name in ("capture_screen", "capture_window"):
        signature = inspect.signature(getattr(ScreenCapture, name))
        forbidden = {"redact", "no_redact", "raw", "include_sensitive", "skip_indicator"}
        assert not forbidden & set(signature.parameters), (
            f"{name} can be asked to skip a control: {signature.parameters.keys()}"
        )
