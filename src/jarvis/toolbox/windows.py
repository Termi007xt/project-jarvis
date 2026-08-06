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
import secrets
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
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


#: Shell surfaces that are not windows in any sense a person means. Matched on
#: title *and* owning process together, so an ordinary File Explorer window —
#: also `explorer.exe` — is never caught by it.
_SHELL_WINDOWS: frozenset[tuple[str, str]] = frozenset(
    {
        ("program manager", "explorer.exe"),
        ("windows input experience", "textinputhost.exe"),
        ("windows shell experience host", "shellexperiencehost.exe"),
        ("windows default lock screen", "logonui.exe"),
    }
)


def is_shell_window(title: str, process_name: str) -> bool:
    """Whether this is the desktop itself rather than something on it."""
    return (title.strip().casefold(), process_name.strip().casefold()) in _SHELL_WINDOWS


#: Executables that host somebody else's application. For these the process
#: name identifies the container and says nothing about what is running in it,
#: so the window's own title is the only thing that names it.
_GENERIC_HOSTS: frozenset[str] = frozenset(
    {
        "applicationframehost.exe",
        "python.exe",
        "pythonw.exe",
        "javaw.exe",
        "java.exe",
        "electron.exe",
        "runtimebroker.exe",
    }
)

#: Where the executable name is simply not what anybody calls the application.
_APPLICATION_NAMES: dict[str, str] = {
    "explorer.exe": "File Explorer",
}


def friendly_application_name(process_name: str, title: str) -> str:
    """What to call this application when speaking to the owner.

    Reported 2026-08-05: the listing read out `WhatsApp.Root.exe`,
    `ApplicationFrameHost.exe` and every window's full title, where *"just
    application names are good"*.

    The process name stays the thing to match on — it comes from the OS and a
    window cannot change it — and this is only what to *say*. For most
    applications the executable is a good name once the extension and any
    packaging suffix are gone. For a generic host it is meaningless, and the
    title is the only thing identifying what is running there; the first clause
    of it, because titles carry documents and status after the name.
    """
    executable = Path(process_name.strip()).name
    known = _APPLICATION_NAMES.get(executable.casefold())
    if known:
        return known

    stem = executable[:-4] if executable.casefold().endswith(".exe") else executable

    if executable.casefold() in _GENERIC_HOSTS:
        # A redacted title must not be announced as though it were a name, so a
        # host whose title has been withheld falls back to the host itself.
        if title.strip() and title != SENSITIVE_TITLE_REDACTION:
            first = title.split(" - ")[0].split(" (")[0].split(" — ")[0]
            return first.strip() or stem
        return stem

    # `WhatsApp.Root` -> `WhatsApp`. A packaging suffix is not part of the name.
    return stem.split(".")[0] or stem


def is_user_facing(
    *,
    title: str,
    cloaked: bool,
    tool_window: bool,
    bounds: tuple[int, int, int, int],
) -> bool:
    """Whether a person would call this an open window.

    Reported 2026-08-05: eleven windows listed where the owner had four. The
    other seven were "Windows Input Experience", "Program Manager", an
    off-screen `ApplicationFrameHost` ghost and similar — none of which anybody
    thinks of as open, and all of which made the model choose between eleven
    candidates when there were four.

    Every test here is a Win32 attribute rather than a title. A skip list of
    names would be both incomplete and defeatable, and the properties that
    actually distinguish these are structural: no caption, DWM-cloaked (which is
    what UWP leaves behind when its window is not really there), a tool window,
    or no area at all.

    Ownership is deliberately *not* here. An owned window is a dialog, which is
    a real window that simply is not one you would "arrange" — and it is exactly
    what an application raises when it has unsaved work and is asked to close.
    Excluding it at this level would make that prompt invisible to the one piece
    of code that most needs to see it, so the distinction is drawn where it is
    used, in `WindowDiscovery.list_windows(include_dialogs=...)`.
    """
    if not title.strip():
        return False
    if cloaked or tool_window:
        return False
    _, _, width, height = bounds
    return width > 0 and height > 0


@dataclass(frozen=True)
class WindowInfo:
    """One top-level window, as the OS describes it.

    ``title`` is application-authored text: evidence, and what the user sees, but
    never a selector. ``ref`` is what an action refers to.
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
    #: Owned by another window — which is what a dialog is. Used to notice that
    #: an application has asked something, never to read what it asked.
    owned: bool = False
    #: The opaque token an action names this window by. Bound to the handle, so
    #: it keeps meaning this window however the desktop reorders — see
    #: `WindowDiscovery.resolve`.
    ref: str = ""

    @property
    def observed_handle(self) -> str:
        """What an action refers to. Not derived from the title."""
        return self.ref or f"nth={self.index}"


class WindowBackend(Protocol):
    """What discovery needs from a windowing implementation."""

    def is_available(self) -> bool: ...

    def unavailable_reason(self) -> str | None: ...

    def list_windows(self) -> list[dict[str, Any]]: ...

    def window_exists(self, handle: int) -> bool: ...


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

            process_name = names.get(int(pid.value), "")
            bounds = (
                rect.left,
                rect.top,
                rect.right - rect.left,
                rect.bottom - rect.top,
            )
            if not is_user_facing(
                title=buffer.value,
                cloaked=_is_cloaked(hwnd),
                tool_window=bool(
                    user32.GetWindowLongW(hwnd, -20) & 0x00000080  # WS_EX_TOOLWINDOW
                ),
                bounds=bounds,
            ):
                return True
            if is_shell_window(buffer.value, process_name):
                return True

            found.append(
                {
                    "handle": int(hwnd),
                    "title": buffer.value,
                    "process_name": process_name,
                    "pid": int(pid.value),
                    "bounds": bounds,
                    "state": _state_of(user32, hwnd),
                    "monitor": 0,
                    # GW_OWNER. An owned window is a dialog: not something to
                    # arrange, and exactly what an application raises when it
                    # is asked to close with unsaved work.
                    "owned": bool(user32.GetWindow(hwnd, 4)),
                }
            )
            return True

        user32.EnumWindows(callback_type(visit), 0)
        return found

    def foreground_handle(self) -> int:
        """Which window has the foreground, according to Windows.

        A read, so it belongs with discovery rather than with the controller —
        and asked of the OS rather than inferred from enumeration order, because
        `EnumWindows` returns z-order and z-order is not focus.
        """
        if os.name != "nt":
            return 0
        import ctypes

        return int(ctypes.windll.user32.GetForegroundWindow())  # type: ignore[attr-defined]

    def window_exists(self, handle: int) -> bool:
        """Whether this is still a window at all — `IsWindow`, nothing else.

        A different question from "is it in `list_windows`", and the distinction
        is the whole of the 2026-08-06 close bug. That list answers *would a
        person call this open*, so it drops the invisible, the untitled, the
        cloaked and the zero-area — and an application that answers `WM_CLOSE`
        by hiding its window while it asks a question is dropped by it while
        being entirely alive. `IsWindow` asks the OS about the handle and knows
        nothing about presentation.

        Handle reuse can make this say "still there" about a recycled handle.
        That errs toward `unverified`, which is the safe direction: the failure
        it prevents is claiming something closed when it did not.
        """
        if os.name != "nt":
            return False
        import ctypes

        return bool(ctypes.windll.user32.IsWindow(handle))  # type: ignore[attr-defined]


def _is_cloaked(hwnd: int) -> bool:
    """Whether DWM is hiding this window.

    UWP applications leave `ApplicationFrameHost` windows behind that are
    visible by every ordinary test and are not on screen — the owner's listing
    on 2026-08-05 showed one at (-25600, -25600). Cloaking is the attribute that
    actually distinguishes them; position does not, because a legitimately
    off-screen window is a different thing.
    """
    try:
        import ctypes
        from ctypes import wintypes

        cloaked = ctypes.c_int(0)
        # DWMWA_CLOAKED = 14
        result = ctypes.windll.dwmapi.DwmGetWindowAttribute(  # type: ignore[attr-defined]
            wintypes.HWND(hwnd),
            14,
            ctypes.byref(cloaked),
            ctypes.sizeof(cloaked),
        )
        return result == 0 and cloaked.value != 0
    except Exception:  # noqa: BLE001 - an unanswerable probe means "not cloaked"
        return False


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
    #: Tokens minted for windows this discovery has listed, keyed by handle.
    #: Never exposed; `resolve` is the only way back out.
    _refs: dict[int, str] = field(default_factory=dict, repr=False)

    def _ref_for(self, handle: int) -> str:
        """The stable token for a window, minted on first sight.

        Stable across listings, so the model is not handed a new name for the
        same window every time it looks. Opaque, and never the raw handle: a
        handle is a number that could be guessed or incremented into a window
        that was never listed, whereas a token exists only because Jarvis
        listed the window it refers to.
        """
        existing = self._refs.get(handle)
        if existing is not None:
            return existing
        minted = f"win-{secrets.token_hex(4)}"
        self._refs[handle] = minted
        return minted

    def resolve(self, ref: str) -> int:
        """The handle a reference names, or a clear refusal.

        Both failures matter and are different. A token that was never minted
        means the caller invented one — the model naming a window it has not
        listed — and a token whose window has since closed means the desktop
        moved on. Neither may fall through to "whatever is there now", which is
        exactly how the wrong window got moved on 2026-08-05.
        """
        # `_refs` is keyed by handle, so search it by value: the map is small
        # (one entry per window seen this session) and this keeps one source of
        # truth rather than two dictionaries that can disagree.
        handle = next((h for h, token in self._refs.items() if token == ref), None)
        if handle is None:
            raise KeyError(
                f"'{ref}' is not a window Jarvis has listed. Call window.list "
                "first and use one of the references it returns."
            )
        if not any(window.handle == handle for window in self.list_windows()):
            self._refs.pop(handle, None)
            raise KeyError(
                "that window has been closed since it was listed, so nothing "
                "was done. Call window.list again to see what is open now."
            )
        return handle

    @property
    def available(self) -> bool:
        return self.backend.is_available()

    def unavailable_reason(self) -> str | None:
        return self.backend.unavailable_reason()

    def list_windows(self, *, include_dialogs: bool = False) -> list[WindowInfo]:
        """Every visible top-level window, in enumeration order.

        Dialogs are left out by default. They are real windows, but they are not
        what "what's open?" means and not things to arrange. `include_dialogs`
        is for the close path, which needs to notice that an application has
        raised one — see `WindowController.close`.

        Raises `WindowsUnavailable` when the desktop cannot be read at all. A
        desktop that genuinely has no windows returns an empty list, which is a
        different answer and must stay distinguishable from the first.
        """
        if not self.backend.is_available():
            raise WindowsUnavailable(
                self.backend.unavailable_reason() or "windows cannot be listed here"
            )

        windows: list[WindowInfo] = []
        entries = [
            entry
            for entry in self.backend.list_windows()
            if include_dialogs or not bool(entry.get("owned", False))
        ]
        for index, entry in enumerate(entries):
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
                    owned=bool(entry.get("owned", False)),
                    ref=self._ref_for(int(entry.get("handle", 0))),
                )
            )
        _LOG.debug("listed %d window(s)", len(windows))
        return windows

    def window_exists(self, handle: int) -> bool:
        """Does this window still exist? Not: is it still on screen.

        `list_windows` deliberately answers the second question — it is what
        "what's open?" means, and the filtering behind it is why a listing of
        eleven windows became the four the owner actually had. Using it for the
        first question is what made a close of Microsoft Edge report success
        while Edge was still there, asking whether to leave the page.

        A backend that cannot tell the two apart falls back to the list, which
        is the old behaviour and no worse; `Win32WindowBackend` can, and
        `tests/unit/test_close_before_force.py` asserts that it still does, so
        the fallback cannot quietly become the normal path.
        """
        probe = getattr(self.backend, "window_exists", None)
        if probe is not None:
            return bool(probe(handle))
        return any(
            window.handle == handle
            for window in self.list_windows(include_dialogs=True)
        )

    def foreground_window(self) -> WindowInfo | None:
        """The window the user is actually looking at, or None (FR-270).

        Returns None rather than guessing when nothing can be identified — the
        foreground may be a window the listing filters out, or the desktop
        itself. "I cannot tell" is a real answer and a better one than naming
        whatever happened to be first.
        """
        probe = getattr(self.backend, "foreground_handle", None)
        if probe is None:
            return None
        try:
            handle = int(probe())
        except Exception:  # noqa: BLE001 - an unanswerable probe means "unknown"
            return None
        if not handle:
            return None
        return next(
            (
                window
                for window in self.list_windows(include_dialogs=True)
                if window.handle == handle
            ),
            None,
        )

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
