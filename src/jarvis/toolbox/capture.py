"""Photographing the screen (FR-073, FR-271, FR-272, P2-WIN-10).

Phase 2 stage 4. The owner chose whole-screen capture on 2026-08-06, knowing the
trade: *"what's on my screen"* works without being told which window, and every
capture contains whatever else was visible. That decision is recorded in
ADR-0019's revisit; this module implements it and the two controls it needs.

**Nothing is captured invisibly.** A capture that cannot show the user it
happened does not happen. The indicator is a constructor dependency, not a
courtesy call the caller might forget — and it is shown *before* the image is
taken, because afterwards means the notice arrives once the picture already
exists. Same choice `jarvis.toolbox.automation` makes about interruption: a
capability that cannot be seen is not offered in a diminished form.

**A blocklisted window is blacked out of the image.** The sensitive-application
list guards *automation* — it stops Jarvis driving a password manager. It cannot
stop a camera pointed at the whole screen, because the pixels are taken wholesale
and nothing is being driven. So the protection moves into the image: every window
on the list has a known rectangle, and those rectangles are filled black before
anything is written to disk.

Blacked out rather than refused, because refusing a whole capture whenever a
vault happens to be open would make the feature useless on a real desktop. Black
rather than blurred, because a blur is a reversible transform of the thing it is
hiding.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from jarvis.toolbox.sensitive import SensitiveTargets
from jarvis.toolbox.windows import WindowDiscovery, WindowInfo, WindowState

__all__ = [
    "ScreenCapture",
    "CaptureRefused",
    "CaptureResult",
    "redacted_regions",
]

_LOG = logging.getLogger(__name__)


class CaptureRefused(RuntimeError):
    """The screen was not photographed, and the reason is not a failure."""


@dataclass(frozen=True)
class CaptureResult:
    """What was captured, and what was kept out of it."""

    path: str
    redacted_count: int
    detail: str


def redacted_regions(
    windows: Sequence[WindowInfo], sensitive: SensitiveTargets
) -> list[tuple[int, int, int, int]]:
    """Rectangles to fill black before the image is written.

    Decided from the process blocklist, so a window that renamed itself to look
    ordinary is still covered — the judgement was never based on what it calls
    itself.

    Minimised windows are skipped. They are not on screen, so there is nothing
    to cover, and painting over their last known rectangle would black out
    whatever is actually there now.
    """
    regions: list[tuple[int, int, int, int]] = []
    for window in windows:
        if window.state is WindowState.MINIMISED:
            continue
        verdict = sensitive.check(
            process_name=window.process_name, window_title=window.title
        )
        if not verdict.allowed:
            regions.append(tuple(window.bounds))  # type: ignore[arg-type]
    return regions


@dataclass
class ScreenCapture:
    """Takes pictures of the screen, visibly, with secrets left out."""

    discovery: WindowDiscovery
    #: Produces the raw image. Injected so the engine stays headless-testable.
    grab: Callable[[], Any]
    #: Shows the user that a capture is happening. **Required**; a capture with
    #: no way to announce itself is refused rather than taken quietly.
    indicator: Callable[[str], None] | None = None

    def capture_screen(self, destination: str | os.PathLike[str]) -> CaptureResult:
        """Photograph the whole screen (FR-073).

        Everything visible is included — that is what whole-screen capture
        means, and it is the owner's recorded choice — except windows on the
        sensitive list, which are filled black before anything is written.
        """
        return self._capture(destination, scope="the whole screen")

    def capture_window(self, ref: str, destination: str | os.PathLike[str]) -> CaptureResult:
        """Photograph one window, chosen by reference (FR-272).

        Narrower than a full screen and therefore the better default when the
        user has named something specific. The same redaction applies: a
        sensitive window overlapping the one asked for is still covered.
        """
        handle = self.discovery.resolve(ref)
        window = next(
            (w for w in self.discovery.list_windows() if w.handle == handle), None
        )
        if window is None:  # pragma: no cover - resolve has already checked
            raise CaptureRefused("that window has been closed since it was listed.")
        if window.sensitive:
            raise CaptureRefused(
                f"that window belongs to '{window.process_name}', which is on "
                "the sensitive-application list. Jarvis does not photograph it."
            )
        return self._capture(destination, scope=f"the {window.process_name} window")

    def _capture(
        self, destination: str | os.PathLike[str], *, scope: str
    ) -> CaptureResult:
        if self.indicator is None:
            raise CaptureRefused(
                "Jarvis will not photograph the screen without being able to "
                "show you that it is happening, and no capture indicator is "
                "connected in this build. Nothing was captured."
            )

        # Before the image exists, not after. A notice that arrives once the
        # picture has been taken is a record, not an indication.
        self.indicator(f"Jarvis is capturing {scope}.")

        windows = self.discovery.list_windows()
        regions = redacted_regions(windows, self.discovery.sensitive)

        canvas = self.grab()
        for region in regions:
            canvas.fill_black(region)
        canvas.save(destination)

        detail = f"captured {scope}."
        if regions:
            detail += (
                f" {len(regions)} sensitive window(s) were blacked out of the "
                "image; their contents were never written to disk."
            )
        _LOG.info("captured %s, %d region(s) redacted", scope, len(regions))
        return CaptureResult(
            path=str(destination), redacted_count=len(regions), detail=detail
        )


def gdi_screen_grab() -> Any:
    """The real capture, via GDI. Windows only, and imported lazily."""
    if os.name != "nt":  # pragma: no cover - the tool reports this honestly
        raise CaptureRefused(
            "screen capture is a Windows facility and this is not Windows."
        )
    from jarvis.toolbox.capture_gdi import GdiCanvas

    return GdiCanvas.of_virtual_screen()


def default_capture_directory(vault_root: Path) -> Path:
    """Where captures live. Inside the vault, so deletion reaches them."""
    return Path(vault_root) / "captures"
