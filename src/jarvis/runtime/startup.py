"""Start at sign-in (PRD FR-002).

Uses the per-user `HKCU\\...\\CurrentVersion\\Run` key. Per-user is not an
implementation detail: the machine-wide equivalent needs administrator rights,
and Jarvis never asks for elevation (FR-003, ADR-0009).

Until packaging exists (Phase 6, ADR-0013) there is no executable to point at,
so the entry launches the current interpreter with ``-m jarvis.main``. That is
honest but fragile — it breaks if the virtual environment moves — and
:func:`describe` says so rather than leaving the user to discover it.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

__all__ = ["StartupRegistration", "available", "describe", "is_enabled", "set_enabled"]

_LOG = logging.getLogger(__name__)

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "ProjectJarvis"


@dataclass(frozen=True)
class StartupRegistration:
    enabled: bool
    command: str | None
    supported: bool
    note: str


def available() -> bool:
    """Only Windows has the Run key this uses."""
    return os.name == "nt"


def _startup_command() -> str:
    """The command Windows would run at sign-in.

    ``pythonw.exe`` rather than ``python.exe`` when it exists, so signing in does
    not flash a console window at the user.
    """
    interpreter = Path(sys.executable)
    windowless = interpreter.with_name("pythonw.exe")
    if windowless.exists():
        interpreter = windowless
    return f'"{interpreter}" -m jarvis.main'


def is_enabled() -> bool:
    if not available():
        return False
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
            value, _kind = winreg.QueryValueEx(key, _VALUE_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        _LOG.exception("could not read the startup registration")
        return False


def set_enabled(enabled: bool) -> StartupRegistration:
    """Add or remove the sign-in entry. Never requires administrator rights."""
    if not available():
        return describe()
    import winreg

    try:
        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _startup_command())
            else:
                try:
                    winreg.DeleteValue(key, _VALUE_NAME)
                except FileNotFoundError:
                    pass  # already absent; the requested state is the actual state
    except OSError as exc:
        _LOG.exception("could not change the startup registration")
        return StartupRegistration(
            enabled=is_enabled(),
            command=None,
            supported=True,
            note=f"Windows refused the change: {exc}",
        )
    return describe()


def describe() -> StartupRegistration:
    if not available():
        return StartupRegistration(
            enabled=False,
            command=None,
            supported=False,
            note="Starting at sign-in is a Windows feature and is unavailable here.",
        )
    enabled = is_enabled()
    return StartupRegistration(
        enabled=enabled,
        command=_startup_command() if enabled else None,
        supported=True,
        note=(
            "Runs for this Windows user only, so it never needs administrator "
            "rights. Until packaging lands (Phase 6) the entry starts this "
            "virtual environment's interpreter, so moving or deleting .venv "
            "will stop it working."
        ),
    )
