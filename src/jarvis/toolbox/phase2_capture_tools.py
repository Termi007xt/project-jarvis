"""The screen-capture tool (FR-073, FR-271, FR-272, P2-WIN-10).

Phase 2 stage 4. `jarvis.toolbox.capture` decides *what a capture is allowed to
contain*; this is the narrow typed tool that makes it reachable, and the two are
separate because the controls must hold however the tool is called.

**The model never names a file.** The destination is composed here, inside the
vault, from a timestamp. A tool that accepted a path would be a file-write
primitive wearing a camera's name — the model could aim it at a startup folder,
and "where does this image go" would become a question answered by untrusted
input. It also means deleting the vault deletes the pictures.

**Whole screen is the owner's recorded choice** (ADR-0019 revisit, 2026-08-06),
and the narrower one is still offered: passing a window reference photographs
just that window. Nothing here takes a title, for the same reason nothing else
in this phase does.

**Not registered without an indicator.** Following `notify.show`: a tool that
can never succeed looks like a defect rather than an absence (ADR-0010), so
without a shell to show the capture notice the tool is simply not there. The
capture core refuses independently if the indicator disappears later.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from jarvis.core.permissions.models import RiskLevel
from jarvis.core.tools.contract import (
    RetryPolicy,
    ToolContext,
    ToolExecution,
    ToolFailure,
    ToolSpec,
    Verification,
)
from jarvis.toolbox.capture import CaptureRefused, ScreenCapture
from jarvis.toolbox.windows import WindowsUnavailable

__all__ = ["ScreenCaptureTool", "register_capture_tool", "prune_captures"]

_LOG = logging.getLogger(__name__)

#: How many captures to keep. A full-screen 32-bit BMP is roughly 15MB, so an
#: unbounded folder fills a disk quietly — the kind of failure that shows up as
#: something else entirely, days later. Oldest are removed first.
CAPTURE_KEEP_COUNT = 20


def prune_captures(directory: Path, keep: int = CAPTURE_KEEP_COUNT) -> int:
    """Delete all but the newest ``keep`` captures. Returns how many went.

    A bound, not a retention policy. `privacy.screenshot_retention` describes
    what the product should eventually do (discard when the task ends, and so
    on); this only guarantees the folder cannot grow without limit, and is
    named as the interim measure in `docs/PROJECT_STATE.md` so it is not
    mistaken for the policy being implemented.
    """
    try:
        captures = sorted(
            (path for path in Path(directory).glob("capture-*.bmp") if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError:  # pragma: no cover - an unreadable folder is not a failure here
        _LOG.debug("could not list captures for pruning", exc_info=True)
        return 0

    removed = 0
    for path in captures[keep:]:
        try:
            path.unlink()
            removed += 1
        except OSError:  # pragma: no cover
            _LOG.debug("could not delete %s", path, exc_info=True)
    if removed:
        _LOG.info("pruned %d old capture(s), keeping %d", removed, keep)
    return removed


class ScreenCaptureInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    window: str | None = Field(
        default=None,
        max_length=64,
        description=(
            "Optional. The 'window' reference from window.list, to photograph "
            "just that window. Leave it out to capture the whole screen. "
            "Never a title."
        ),
    )


class ScreenCaptureOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: str
    path: str
    redacted_count: int
    detail: str


class ScreenCaptureTool:
    """Photograph the screen, visibly, with blocklisted windows blacked out."""

    spec = ToolSpec(
        tool_id="screen.capture",
        version="1.0.0",
        description=(
            "Take a picture of the screen and save it in the Jarvis vault. The "
            "user is always shown that a capture is happening. Give a 'window' "
            "reference from window.list to photograph one window; leave it out "
            "for the whole screen. Windows belonging to sensitive applications "
            "are blacked out of the image and cannot be captured at all."
        ),
        input_model=ScreenCaptureInput,
        output_model=ScreenCaptureOutput,
        risk=RiskLevel.MEDIUM,
        required_capabilities=("screen.capture",),
        # No foreground lock: capturing reads the screen and moves nothing, so
        # it does not contend with automation for the desktop.
        resource_locks=(),
        timeout_seconds=30.0,
        retry_policy=RetryPolicy(max_attempts=1),
        # It writes a file, so it is a state change — a reversible one, since
        # the image is in the vault and deleting the vault deletes it.
        changes_state=True,
        verification=(
            "Reports the file that was actually written, and how many sensitive "
            "windows were blacked out of it before it reached disk."
        ),
        failure_codes=(
            "capture_refused",
            "no_such_window",
            "windows_unavailable",
        ),
        reversible=True,
    )

    def __init__(self, capture: ScreenCapture, directory: Path) -> None:
        self._capture = capture
        self._directory = Path(directory)

    def _destination(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        return self._directory / f"capture-{stamp}.bmp"

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        assert isinstance(parameters, ScreenCaptureInput)
        destination = self._destination()

        try:
            if parameters.window:
                result = self._capture.capture_window(parameters.window, destination)
                scope = "window"
            else:
                result = self._capture.capture_screen(destination)
                scope = "screen"
        except CaptureRefused as exc:
            raise ToolFailure("capture_refused", str(exc)) from exc
        except KeyError as exc:
            raise ToolFailure("no_such_window", str(exc.args[0])) from exc
        except WindowsUnavailable as exc:
            raise ToolFailure("windows_unavailable", str(exc)) from exc

        prune_captures(self._directory)

        return ToolExecution(
            output=ScreenCaptureOutput(
                scope=scope,
                path=result.path,
                redacted_count=result.redacted_count,
                detail=result.detail,
            ),
            verification=Verification.VERIFIED,
            message=result.detail,
            evidence={"scope": scope, "redacted": result.redacted_count},
        )


def register_capture_tool(registry: object, capture: ScreenCapture, directory: Path) -> str | None:
    """Register `screen.capture`, but only if it can announce itself.

    Returns the tool id, or None when there is no indicator — in which case the
    tool is absent rather than present and always failing, which is the same
    choice `notify.show` makes about a missing shell.
    """
    if capture.indicator is None:
        _LOG.info(
            "screen.capture is not registered: nothing can show the user that a "
            "capture is happening, and Jarvis does not photograph the screen "
            "without that."
        )
        return None
    registry.register(ScreenCaptureTool(capture, directory))  # type: ignore[attr-defined]
    return ScreenCaptureTool.spec.tool_id
