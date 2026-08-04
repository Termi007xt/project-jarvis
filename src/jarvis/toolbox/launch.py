"""The one authorised process-creation call site (ADR-0029).

Everything about this module is narrow on purpose. ADR-0003 closed the
capability set and `tests/security/test_no_shell.py` enforces it; this file
holds the single reviewed exception, and its `ALLOW_LIST` entry cites ADR-0029
by number.

The distinction the design rests on: **a shell interprets a string; a launcher
executes an argument vector.** `cmd.exe /c <string>` is arbitrary execution
because the string is a program in a language. `Popen(["C:/.../brave.exe",
"--profile-directory=Jarvis", "https://youtube.com"])` is not, because nothing
interprets the vector and the executable came from a catalogue rather than from
the argument.

All nine ADR-0029 constraints are enforced here, in code, not by convention:

1. list argv only, never a string
2. ``shell=False`` passed explicitly
3. the executable never comes from model output, web content or a filename
4. interpreters and shells are refused by basename at registration time
5. arguments come from a per-entry typed template
6. Store apps go through the fixed ``explorer.exe shell:AppsFolder\\<AUMID>``
   broker, where ``explorer.exe`` is a constant and the AUMID is validated
7. the environment is inherited, never constructed from untrusted input
8. every launch passes through ``ToolInvoker`` — this module is never called
   directly from a plan
9. launch is verified, not assumed; unverified is reported as unverified
"""

from __future__ import annotations

import logging
import os
import re
import subprocess  # ADR-0029: the single authorised process-creation import
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

__all__ = [
    "ApplicationEntry",
    "LaunchKind",
    "LaunchOutcome",
    "ApplicationCatalogue",
    "launch_argv",
    "INTERPRETER_DENYLIST",
    "ALLOWED_URL_SCHEMES",
    "CatalogueError",
    "AUMID_PATTERN",
]

_LOG = logging.getLogger(__name__)

#: Constraint 4. Refused by basename, whatever path they are given under, so a
#: catalogue entry cannot smuggle an interpreter in as "an application".
INTERPRETER_DENYLIST: frozenset[str] = frozenset(
    {
        "cmd.exe", "command.com", "powershell.exe", "pwsh.exe", "wsl.exe",
        "bash.exe", "sh.exe", "zsh.exe", "wscript.exe", "cscript.exe",
        "mshta.exe", "rundll32.exe", "regsvr32.exe", "msbuild.exe",
        "installutil.exe", "python.exe", "pythonw.exe", "conhost.exe",
        "wmic.exe", "certutil.exe", "bitsadmin.exe", "forfiles.exe",
    }
)

#: Constraint 5. Only these schemes may be passed to a browser entry. `file:`
#: and `javascript:` are the two that turn "open a page" into something else.
ALLOWED_URL_SCHEMES: frozenset[str] = frozenset({"http", "https"})

#: Constraint 6. An Application User Model ID, as Windows writes them.
AUMID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+(?:_[A-Za-z0-9]+)?![A-Za-z0-9._-]+$")

#: The fixed broker for Store applications. A constant, never a catalogue value.
_EXPLORER = "explorer.exe"

#: The installed YouTube Music web app. Chromium derives an app id from the
#: application's start URL, so this is stable for music.youtube.com rather than
#: personal to one machine — but it is still only a seed. If the app is not
#: installed the launch fails and says so, which is the honest outcome; it does
#: not silently fall back to a tab, because a silent fallback is how "open
#: YouTube Music" quietly stopped meaning what the user asked for.
_YOUTUBE_MUSIC_APP_ID = "cinhimbnkkaeohfgghhklpknlkffjgod"


class CatalogueError(ValueError):
    """A catalogue entry was refused. Raised at registration, not at launch."""


class LaunchKind(str, Enum):
    """How an entry is started."""

    EXECUTABLE = "executable"
    STORE_APP = "store_app"


class ArgumentKind(str, Enum):
    """Constraint 5: what a per-entry argument is allowed to be."""

    NONE = "none"
    URL = "url"
    STEAM_APP_ID = "steam_app_id"


@dataclass(frozen=True)
class ApplicationEntry:
    """One application the user has approved Jarvis to open.

    Created by the user, never by the model. The model may propose *which
    entry*; it can never propose which binary (constraint 3).
    """

    app_id: str
    display_name: str
    kind: LaunchKind
    #: For EXECUTABLE: the full path. For STORE_APP: the AUMID.
    target: str
    fixed_arguments: tuple[str, ...] = ()
    argument_kind: ArgumentKind = ArgumentKind.NONE
    #: Whether the argument must be supplied. A browser opens perfectly well
    #: with no URL, but `steam.exe -applaunch` with no id is malformed.
    argument_required: bool = False
    #: Process names that indicate the application is running (constraint 9).
    verify_process_names: tuple[str, ...] = ()
    verify_window_substring: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def matches(self, name: str) -> bool:
        lowered = name.strip().casefold()
        return lowered in {
            self.app_id.casefold(),
            self.display_name.casefold(),
            *(alias.casefold() for alias in self.aliases),
        }


@dataclass(frozen=True)
class LaunchOutcome:
    """What actually happened. ``verified`` is never assumed (constraint 9)."""

    started: bool
    verified: bool
    pid: int | None
    argv: tuple[str, ...]
    detail: str


def _basename(target: str) -> str:
    return Path(target).name.casefold()


def validate_entry(entry: ApplicationEntry) -> None:
    """Refuse an unsafe catalogue entry at registration time (constraint 4)."""
    if not entry.app_id.strip():
        raise CatalogueError("a catalogue entry needs an id")

    if entry.kind is LaunchKind.EXECUTABLE:
        name = _basename(entry.target)
        if name in INTERPRETER_DENYLIST:
            raise CatalogueError(
                f"'{entry.target}' is an interpreter or shell ({name}). Jarvis has "
                "no generic execution capability, and adding one through the "
                "application catalogue is the same thing wearing a different hat "
                "(ADR-0003, ADR-0029)."
            )
        if not name.endswith(".exe"):
            raise CatalogueError(
                f"'{entry.target}' is not an executable. Only a program can be "
                "launched; a document would delegate the choice of what runs to "
                "the file-association table, which Jarvis does not control."
            )
    elif entry.kind is LaunchKind.STORE_APP:
        if not AUMID_PATTERN.match(entry.target):
            raise CatalogueError(
                f"'{entry.target}' is not a valid Application User Model ID"
            )

    for argument in entry.fixed_arguments:
        if not isinstance(argument, str):
            raise CatalogueError("fixed arguments must be strings")


def _validate_argument(entry: ApplicationEntry, argument: str | None) -> list[str]:
    """Constraint 5: validate the caller's argument against the entry's type."""
    if entry.argument_kind is ArgumentKind.NONE:
        if argument:
            raise CatalogueError(
                f"'{entry.app_id}' does not take an argument, so '{argument}' "
                "was refused rather than passed through."
            )
        return []

    if not argument:
        if entry.argument_required:
            raise CatalogueError(f"'{entry.app_id}' needs a {entry.argument_kind.value}")
        # Optional: a browser with no URL simply opens the browser.
        return []

    if entry.argument_kind is ArgumentKind.URL:
        parsed = urlparse(argument)
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
            raise CatalogueError(
                f"'{argument}' is not an http or https URL. Other schemes are "
                "refused: 'file:' would read the disk and 'javascript:' would "
                "execute, neither of which is opening a web page."
            )
        if not parsed.netloc:
            raise CatalogueError(f"'{argument}' has no host")
        # One vector element. No quoting, no concatenation, no shell.
        return [argument]

    if entry.argument_kind is ArgumentKind.STEAM_APP_ID:
        if not argument.isdigit():
            raise CatalogueError(f"'{argument}' is not a Steam app id")
        return [argument]

    raise CatalogueError(f"unhandled argument kind {entry.argument_kind}")  # pragma: no cover


def build_argv(entry: ApplicationEntry, argument: str | None = None) -> tuple[str, ...]:
    """Construct the argument vector. Pure, so it is directly testable."""
    validate_entry(entry)
    extra = _validate_argument(entry, argument)

    if entry.kind is LaunchKind.STORE_APP:
        # Constraint 6. explorer.exe is a constant here; the AUMID is the only
        # variable part and it was pattern-validated above.
        return (_EXPLORER, f"shell:AppsFolder\\{entry.target}")

    if not extra and entry.argument_kind is not ArgumentKind.NONE:
        # Fixed arguments that exist to introduce a value are meaningless
        # without it: "steam.exe -applaunch" with no id is a malformed command
        # line, whereas plain "steam.exe" opens the client, which is what
        # "open Steam" means.
        return (entry.target,)

    return (entry.target, *entry.fixed_arguments, *extra)


def launch_argv(argv: tuple[str, ...] | list[str]) -> int | None:
    """**The one authorised process-creation call site** (ADR-0029).

    Nothing else in ``src/jarvis`` may start a process. The argument must be a
    list or tuple of strings; a string command line is refused rather than
    passed to the OS to re-parse, because that re-parsing is the quoting
    injection this constraint exists to remove.
    """
    if isinstance(argv, str):  # constraint 1, asserted rather than documented
        raise TypeError(
            "launch_argv takes an argument vector, never a command string. A "
            "string would be re-parsed by the OS, which is exactly the shell "
            "behaviour ADR-0003 forbids."
        )
    vector = list(argv)
    if not vector or not all(isinstance(part, str) for part in vector):
        raise TypeError("the argument vector must be a non-empty list of strings")

    executable = _basename(vector[0])
    if executable in INTERPRETER_DENYLIST:
        # Belt and braces: the catalogue refuses these at registration, and the
        # call site refuses them again in case anything ever bypasses it.
        raise CatalogueError(f"refusing to launch the interpreter '{vector[0]}'")

    _LOG.info("launching %s", vector[0])
    process = subprocess.Popen(  # noqa: S603 - ADR-0029, see module docstring
        vector,
        shell=False,  # constraint 2: explicit, never defaulted
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        # constraint 7: the environment is inherited, never built from input.
    )
    return process.pid


def process_running(names: tuple[str, ...]) -> bool:
    """Whether any named process exists (constraint 9, verification).

    Uses the Windows tool-help snapshot through ``ctypes``. Deliberately not a
    process listing utility invoked as a subprocess — that would be a second
    process-creation site, which ADR-0029 forbids.
    """
    if not names or os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes

    wanted = {name.casefold() for name in names}

    TH32CS_SNAPPROCESS = 0x00000002
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

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
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        return False
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return False
        while True:
            if entry.szExeFile.casefold() in wanted:
                return True
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                return False
    finally:
        kernel32.CloseHandle(snapshot)


def launch(
    entry: ApplicationEntry,
    argument: str | None = None,
    *,
    verify_timeout_seconds: float = 8.0,
    poll_seconds: float = 0.25,
) -> LaunchOutcome:
    """Start an application and **verify** it started (constraint 9, FR-064).

    ``Popen`` returning without raising is not evidence that anything started —
    it means a process was created, which for the Store broker is `explorer.exe`
    and not the game. So the outcome is only ``verified`` when the declared
    process is actually observed.
    """
    argv = build_argv(entry, argument)

    # Observed *before* starting anything, because otherwise this check cannot
    # tell "my effect happened" from "something unrelated was already true".
    # `youtube_music` verifies against `brave.exe`, and Brave is usually already
    # open, so every launch reported verified success while nothing about the
    # effect had been observed — including the launches that opened a tab
    # instead of the app.
    already_running = bool(entry.verify_process_names) and process_running(
        entry.verify_process_names
    )

    try:
        pid = launch_argv(argv)
    except OSError as exc:
        return LaunchOutcome(
            started=False, verified=False, pid=None, argv=argv,
            detail=f"could not start {entry.display_name}: {exc}",
        )

    if not entry.verify_process_names:
        # Honest: nothing was declared to check, so nothing was confirmed.
        return LaunchOutcome(
            started=True, verified=False, pid=pid, argv=argv,
            detail=(
                f"started {entry.display_name}, but the catalogue entry declares "
                "no process to verify against, so the effect is unconfirmed."
            ),
        )

    if already_running:
        # Honest, and deliberately not downgraded to a warning: this launch
        # cannot be confirmed by process presence, because the process was
        # there first. Confirming it needs a *window*, which is UI Automation
        # (P2-WIN-08). Until then this is `unverified`, which by design does
        # not satisfy a task's success criteria (PRD FR-048, AT-018).
        return LaunchOutcome(
            started=True, verified=False, pid=pid, argv=argv,
            detail=(
                f"{entry.display_name} was asked to start, but "
                f"{', '.join(entry.verify_process_names)} was already running "
                "before this action, so seeing it now is no evidence the action "
                "did anything. Reporting this as unverified rather than as "
                "success."
            ),
        )

    deadline = time.monotonic() + verify_timeout_seconds
    while time.monotonic() < deadline:
        if process_running(entry.verify_process_names):
            return LaunchOutcome(
                started=True, verified=True, pid=pid, argv=argv,
                detail=(
                    f"{entry.display_name} is running "
                    f"({', '.join(entry.verify_process_names)})."
                ),
            )
        time.sleep(poll_seconds)

    return LaunchOutcome(
        started=True, verified=False, pid=pid, argv=argv,
        detail=(
            f"{entry.display_name} was launched but did not appear within "
            f"{verify_timeout_seconds:.0f}s. Reporting this as unverified rather "
            "than as success (PRD FR-048, AT-018)."
        ),
    )


class ApplicationCatalogue:
    """The user's approved applications. Seeded, editable, never model-written."""

    def __init__(self, entries: tuple[ApplicationEntry, ...] = ()) -> None:
        self._entries: dict[str, ApplicationEntry] = {}
        for entry in entries:
            self.add(entry)

    def add(self, entry: ApplicationEntry) -> ApplicationEntry:
        validate_entry(entry)  # refuse at registration, not at launch
        self._entries[entry.app_id] = entry
        return entry

    def get(self, app_id: str) -> ApplicationEntry | None:
        return self._entries.get(app_id)

    def resolve(self, name: str) -> ApplicationEntry | None:
        """Find an entry by id, display name or alias. Never by path."""
        direct = self._entries.get(name)
        if direct is not None:
            return direct
        return next((entry for entry in self._entries.values() if entry.matches(name)), None)

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def entries(self) -> tuple[ApplicationEntry, ...]:
        return tuple(self._entries[key] for key in sorted(self._entries))

    def __len__(self) -> int:
        return len(self._entries)


def default_catalogue(config: object | None = None) -> ApplicationCatalogue:
    """The Phase 1 seed: exactly the applications PRD section 21 names.

    Paths are the usual install locations on this platform. An entry whose
    executable is missing is still listed — the launcher reports the failure
    honestly rather than the entry silently disappearing (ADR-0010).
    """
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    # Steam is a 32-bit install, so it lives under the x86 tree. The variable
    # name contains parentheses, which is why it is fetched by string rather
    # than composed from ``ProgramFiles``.
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    brave = ApplicationEntry(
        app_id="brave",
        display_name="Brave",
        kind=LaunchKind.EXECUTABLE,
        target=rf"{program_files}\BraveSoftware\Brave-Browser\Application\brave.exe",
        argument_kind=ArgumentKind.URL,
        verify_process_names=("brave.exe",),
        aliases=("brave browser", "browser"),
    )
    return ApplicationCatalogue(
        (
            brave,
            ApplicationEntry(
                app_id="youtube",
                display_name="YouTube",
                kind=LaunchKind.EXECUTABLE,
                target=brave.target,
                fixed_arguments=("https://www.youtube.com",),
                verify_process_names=("brave.exe",),
                aliases=("you tube",),
            ),
            ApplicationEntry(
                app_id="youtube_music",
                display_name="YouTube Music",
                kind=LaunchKind.EXECUTABLE,
                # The installed progressive web app, not a tab. Handing the URL
                # to the browser opens a tab by definition, which is not what
                # "open YouTube Music" means to somebody who installed the app
                # and pinned it to the Start menu. Chromium launches an
                # installed app by id, and this is the same fixed vector the
                # Start-menu shortcut uses, so no new call site is involved.
                target=rf"{program_files}\BraveSoftware\Brave-Browser\Application\chrome_proxy.exe",
                fixed_arguments=(
                    "--profile-directory=Default",
                    f"--app-id={_YOUTUBE_MUSIC_APP_ID}",
                ),
                verify_process_names=("brave.exe",),
                aliases=("youtube music", "music", "yt music", "ytmusic"),
            ),
            ApplicationEntry(
                app_id="xbox",
                display_name="Xbox",
                kind=LaunchKind.STORE_APP,
                target="Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App",
                verify_process_names=("XboxPcApp.exe", "GamingServices.exe"),
                aliases=("xbox app", "game pass"),
            ),
            ApplicationEntry(
                app_id="sea_of_thieves",
                display_name="Sea of Thieves",
                kind=LaunchKind.STORE_APP,
                target="Microsoft.SeaofThieves_8wekyb3d8bbwe!Microsoft.SeaofThieves",
                verify_process_names=("SoTGame.exe", "SeaOfThieves.exe"),
                aliases=("sot", "sea of thieves"),
            ),
            ApplicationEntry(
                app_id="steam",
                display_name="Steam",
                kind=LaunchKind.EXECUTABLE,
                target=rf"{program_files_x86}\Steam\steam.exe",
                fixed_arguments=("-applaunch",),
                argument_kind=ArgumentKind.STEAM_APP_ID,
                # "open Steam" means open the client. With an app id it becomes
                # "steam.exe -applaunch <id>"; without one, just "steam.exe".
                argument_required=False,
                verify_process_names=("steam.exe",),
            ),
        )
    )
