"""Finding windows: identity, position, state (FR-240, P2-WIN-08).

Phase 2 stage 4. The eyes for window management, in the same shape as
`jarvis.toolbox.uia`: **read-only**, injectable backend, and every piece of
application-authored text treated as untrusted. The hands arrive separately,
behind the `foreground_desktop` lock and behind `ToolInvoker`, because a module
that could both see and act would be a second route from a plan to an effect.

**A window title is untrusted content.** It is authored by whichever application
owns the window, and a window is free to call itself anything at all. So titles
leave here through `jarvis.core.observations`, carried as data and addressed by
position, exactly as web content does. There is deliberately no lookup by title:
that is what would let a window choose the target of an action by renaming
itself. A desktop window feels more trustworthy than a web page; it is not.

**A sensitive window is listed with its title withheld.** Hiding it entirely
would leave Jarvis unable to say why it will not act, which ADR-0010 forbids.
Showing the title would defeat the point — "Chase — personal banking" is exactly
what the blocklist exists to keep out of prompts and logs. So the window is
present, the identity is reported, and the title is replaced. Same choice as
password fields, and for the same reason: withhold the content, keep the
position, because positions are what actions address.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from jarvis.core.observations import ContentClass, ObservedItem, ObservedList
from jarvis.toolbox.sensitive import SensitiveTargets

__all__ = [
    "WindowInfo",
    "WindowState",
    "WindowDiscovery",
    "WindowBackend",
    "WindowsUnavailable",
    "Win32WindowBackend",
    "SENSITIVE_TITLE_REDACTION",
]

_LOG = logging.getLogger(__name__)

#: What replaces the title of a window on the sensitive list. Distinct from the
#: password-field marker so a log says which kind of thing was withheld.
SENSITIVE_TITLE_REDACTION = "[sensitive window — title withheld]"


class WindowsUnavailable(RuntimeError):
    """Windows cannot be enumerated here. Never raised for an empty desktop."""


class WindowState(str, Enum):
    """How a window is currently shown. Read from the OS, never inferred."""

    NORMAL = "normal"
    MINIMISED = "minimised"
    MAXIMISED = "maximised"

    @classmethod
    def parse(cls, raw: str) -> "WindowState":
        normalised = (raw or "").strip().casefold()
        # Both spellings, because the Win32 name is "minimized" and the rest of
        # this codebase is written in British English.
        if normalised in ("minimised", "minimized"):
            return cls.MINIMISED
        if normalised in ("maximised", "maximized"):
            return cls.MAXIMISED
        return cls.NORMAL


@dataclass(frozen=True)
class WindowInfo:
    """One top-level window, as the OS describes it.

    ``title`` is application-authored text: evidence, and what the user sees, but
    never a selector. ``index`` is what an action refers to.
    """

    index: int
    handle: int
    title: str
    process_name: str
    pid: int
    bounds: tuple[int, int, int, int]
    state: WindowState
    monitor: int = 0
    #: On the sensitive list. Actions against it are refused, and the title
    #: above has already been replaced.
    sensitive: bool = False

    @property
    def observed_handle(self) -> str:
        """What an action refers to. Derived from position, never from text."""
        return f"nth={self.index}"


class WindowBackend(Protocol):
    """What discovery needs from a windowing implementation."""

    def is_available(self) -> bool: ...

    def unavailable_reason(self) -> str | None: ...

    def list_windows(self) -> list[dict[str, Any]]: ...


class Win32WindowBackend:
    """The real backend, via ctypes. Windows only.

    Deliberately not a process-listing utility invoked as a subprocess — that
    would be a second process-creation site, which ADR-0029 forbids.
    """

    def is_available(self) -> bool:
        return self.unavailable_reason() is None

    def unavailable_reason(self) -> str | None:
        if os.name != "nt":
            return (
                "windows are a Windows facility and this is not Windows, so "
                "none can be listed here."
            )
        return None

    def list_windows(self) -> list[dict[str, Any]]:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        found: list[dict[str, Any]] = []
        names = _process_names_by_pid()

        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def visit(hwnd: int, _param: int) -> bool:
            # Visible top-level windows only. Chromium alone keeps a swarm of
            # hidden message-only windows, and listing those makes the count
            # meaningless without adding anything actionable.
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)

            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))

            found.append(
                {
                    "handle": int(hwnd),
                    "title": buffer.value,
                    "process_name": names.get(int(pid.value), ""),
                    "pid": int(pid.value),
                    "bounds": (
                        rect.left,
                        rect.top,
                        rect.right - rect.left,
                        rect.bottom - rect.top,
                    ),
                    "state": _state_of(user32, hwnd),
                    "monitor": 0,
                }
            )
            return True

        user32.EnumWindows(callback_type(visit), 0)
        return found


def _state_of(user32: Any, hwnd: int) -> str:
    if user32.IsIconic(hwnd):
        return "minimised"
    if user32.IsZoomed(hwnd):
        return "maximised"
    return "normal"


def _process_names_by_pid() -> dict[int, str]:
    """Executable names keyed by process id, via the tool-help snapshot."""
    if os.name != "nt":
        return {}
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_wchar * 260),
        ]

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return {}
    names: dict[int, str] = {}
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return names
        while True:
            names[int(entry.th32ProcessID)] = entry.szExeFile
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                return names
    finally:
        kernel32.CloseHandle(snapshot)


@dataclass
class WindowDiscovery:
    """Lists windows. Changes nothing.

    Deliberately has no `activate`, `move`, `close` or `find_by_title` — the
    first three are the acting half and live behind `ToolInvoker`; the last is
    the lookup that would let a window retarget an action by renaming itself.
    """

    backend: WindowBackend = field(default_factory=Win32WindowBackend)
    sensitive: SensitiveTargets = field(default_factory=SensitiveTargets)

    @property
    def available(self) -> bool:
        return self.backend.is_available()

    def unavailable_reason(self) -> str | None:
        return self.backend.unavailable_reason()

    def list_windows(self) -> list[WindowInfo]:
        """Every visible top-level window, in enumeration order.

        Raises `WindowsUnavailable` when the desktop cannot be read at all. A
        desktop that genuinely has no windows returns an empty list, which is a
        different answer and must stay distinguishable from the first.
        """
        if not self.backend.is_available():
            raise WindowsUnavailable(
                self.backend.unavailable_reason() or "windows cannot be listed here"
            )

        windows: list[WindowInfo] = []
        for index, entry in enumerate(self.backend.list_windows()):
            title = str(entry.get("title", ""))
            process_name = str(entry.get("process_name", ""))
            verdict = self.sensitive.check(process_name=process_name, window_title=title)
            windows.append(
                WindowInfo(
                    index=index,
                    handle=int(entry.get("handle", 0)),
                    # Replaced, not dropped: the position is what an action
                    # addresses, and the refusal still needs something to name.
                    title=title if verdict.allowed else SENSITIVE_TITLE_REDACTION,
                    process_name=process_name,
                    pid=int(entry.get("pid", 0)),
                    bounds=tuple(entry.get("bounds", (0, 0, 0, 0))),  # type: ignore[arg-type]
                    state=WindowState.parse(str(entry.get("state", "normal"))),
                    monitor=int(entry.get("monitor", 0)),
                    sensitive=not verdict.allowed,
                )
            )
        _LOG.debug("listed %d window(s)", len(windows))
        return windows

    def as_observed_list(self) -> ObservedList:
        """Hand the desktop onward as untrusted, positionally-addressed content."""
        windows = self.list_windows()
        return ObservedList(
            origin="windows:desktop",
            content_class=ContentClass.UI_TEXT,
            items=tuple(
                ObservedItem(
                    index=window.index,
                    label=window.title,
                    handle=window.observed_handle,
                )
                for window in windows
            ),
        )
