"""Single-instance enforcement (PRD FR-005).

Only one interactive Jarvis may run per Windows user session. Two instances
would fight over the microphone, the foreground desktop lock and the SQLite
vault.

Windows uses a named mutex in the ``Local\\`` namespace, which is per-session by
design — exactly the scope the requirement asks for, and it needs no
administrator rights. Other platforms use an exclusive lock file so the test
suite and development on non-Windows hosts still work.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import TracebackType

__all__ = ["SingleInstanceGuard", "AlreadyRunningError", "DEFAULT_MUTEX_NAME"]

DEFAULT_MUTEX_NAME = "Local\\ProjectJarvis.SingleInstance"

_ERROR_ALREADY_EXISTS = 183
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_STILL_ACTIVE = 259


def _process_is_alive(pid: int) -> bool:
    """Is a process with this id currently running?

    ``os.kill(pid, 0)`` is the POSIX idiom, but on Windows a non-existent pid
    raises a generic ``OSError`` rather than ``ProcessLookupError``, so a stale
    lock file would never be reclaimed. Windows therefore uses ``OpenProcess``
    plus ``GetExitCodeProcess``.

    When liveness cannot be determined, the answer is "alive": refusing to start
    is safer than two instances fighting over the vault.
    """
    if pid <= 0:
        return False

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False  # no such process, or it is gone
        try:
            exit_code = wintypes.DWORD()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return exit_code.value == _STILL_ACTIVE
            return True
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except OSError:
        return True
    return True


class AlreadyRunningError(RuntimeError):
    """Another instance already holds the single-instance handle."""


class SingleInstanceGuard:
    """Acquire once at startup; release at shutdown.

    ``acquired`` is the only thing callers should test. Failure to acquire is
    not an error condition to work around — it means another Jarvis owns this
    session.
    """

    def __init__(
        self,
        name: str = DEFAULT_MUTEX_NAME,
        lock_file: Path | None = None,
        *,
        force_lock_file: bool = False,
    ) -> None:
        self._name = name
        self._lock_file = lock_file
        self._use_mutex = os.name == "nt" and not force_lock_file
        self._handle: int | None = None
        self._fd: int | None = None
        self._acquired = False

    @property
    def acquired(self) -> bool:
        return self._acquired

    @property
    def name(self) -> str:
        return self._name

    # -- acquisition -------------------------------------------------------
    def acquire(self) -> bool:
        if self._acquired:
            return True
        self._acquired = self._acquire_mutex() if self._use_mutex else self._acquire_lock_file()
        return self._acquired

    def acquire_or_raise(self) -> "SingleInstanceGuard":
        if not self.acquire():
            raise AlreadyRunningError(
                "Project Jarvis is already running in this Windows session. "
                "Use the tray icon to open the existing instance."
            )
        return self

    def _acquire_mutex(self) -> bool:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        kernel32.CreateMutexW.restype = wintypes.HANDLE

        handle = kernel32.CreateMutexW(None, True, self._name)
        last_error = ctypes.get_last_error()
        if not handle:
            return False
        if last_error == _ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        self._handle = handle
        return True

    def _acquire_lock_file(self) -> bool:
        if self._lock_file is None:
            raise ValueError("a lock_file path is required when not using a named mutex")
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            # O_EXCL makes creation atomic: whoever creates the file wins.
            fd = os.open(self._lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            if self._reclaim_stale_lock_file():
                try:
                    fd = os.open(self._lock_file, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                except FileExistsError:
                    return False
            else:
                return False
        os.write(fd, str(os.getpid()).encode("ascii"))
        self._fd = fd
        return True

    def _reclaim_stale_lock_file(self) -> bool:
        """Remove a lock file whose owning process is gone."""
        assert self._lock_file is not None
        try:
            recorded = int(self._lock_file.read_text(encoding="ascii").strip() or 0)
        except (OSError, ValueError):
            return False
        if recorded <= 0 or recorded == os.getpid():
            return False
        if _process_is_alive(recorded):
            return False
        try:
            self._lock_file.unlink()
            return True
        except OSError:
            return False

    # -- release -----------------------------------------------------------
    def release(self) -> None:
        if not self._acquired:
            return
        if self._handle is not None:
            import ctypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
            kernel32.ReleaseMutex(self._handle)
            kernel32.CloseHandle(self._handle)
            self._handle = None
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
            if self._lock_file is not None:
                try:
                    self._lock_file.unlink()
                except OSError:
                    pass
        self._acquired = False

    # -- context manager ---------------------------------------------------
    def __enter__(self) -> "SingleInstanceGuard":
        return self.acquire_or_raise()

    def __exit__(
        self,
        _type: type[BaseException] | None,
        _value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        self.release()
