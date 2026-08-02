"""Global hotkeys (PRD section 11.3, FR-018, ADR-0027).

Two hotkeys exist in Phase 1: the emergency stop (`Ctrl+Alt+Pause`) and
push-to-talk (`F9`). Both are configurable, which matters more than it looks:
PRD section 11.3 requires the emergency-stop hotkey not to conflict with common
Windows shortcuts, and bare F9 is heavily used by IDEs, Excel and games. A global
hook swallows that key from every other application, so being able to change it
is the mitigation.

Implementation notes that are not incidental:

* `RegisterHotKey` binds to the **calling thread**, and `WM_HOTKEY` arrives on
  that thread's message queue. So registration and the message loop must happen
  on the same thread, and it cannot be the Qt thread — a blocking `GetMessage`
  loop there would freeze the interface.
* Registration fails when another process already owns the combination. That is
  an ordinary, expected outcome, not an error to swallow: it is reported so the
  GUI can say which hotkey is unavailable and why (ADR-0010, NFR-014).
* `MOD_NOREPEAT` is always set. Without it, holding the key repeats the action,
  and an emergency stop that fires forty times is not better than one.
* Callbacks are dispatched on the hotkey thread. Anything touching the GUI must
  marshal itself across; anything slow blocks the next hotkey.
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Callable

__all__ = [
    "Hotkey",
    "HotkeyBinding",
    "GlobalHotkeys",
    "parse_hotkey",
    "HotkeyError",
    "available",
]

_LOG = logging.getLogger(__name__)

# Win32 modifier bits (winuser.h).
_MOD_ALT = 0x0001
_MOD_CONTROL = 0x0002
_MOD_SHIFT = 0x0004
_MOD_WIN = 0x0008
_MOD_NOREPEAT = 0x4000

_WM_HOTKEY = 0x0312
_WM_QUIT = 0x0012

_MODIFIER_NAMES: dict[str, int] = {
    "ctrl": _MOD_CONTROL,
    "control": _MOD_CONTROL,
    "alt": _MOD_ALT,
    "shift": _MOD_SHIFT,
    "win": _MOD_WIN,
    "super": _MOD_WIN,
    "meta": _MOD_WIN,
}

#: Virtual-key codes for the keys a hotkey may reasonably use. Deliberately a
#: closed table: an unrecognised key name is a configuration error with a clear
#: message, not a silently unregistered hotkey.
_VIRTUAL_KEYS: dict[str, int] = {
    "backspace": 0x08, "tab": 0x09, "clear": 0x0C, "enter": 0x0D, "return": 0x0D,
    "pause": 0x13, "capslock": 0x14, "escape": 0x1B, "esc": 0x1B, "space": 0x20,
    "pageup": 0x21, "pagedown": 0x22, "end": 0x23, "home": 0x24,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "printscreen": 0x2C, "insert": 0x2D, "delete": 0x2E,
    "numlock": 0x90, "scrolllock": 0x91,
    **{str(digit): 0x30 + digit for digit in range(10)},
    # Lower-cased, because lookups happen after the input is lower-cased.
    **{chr(code).lower(): code for code in range(0x41, 0x5B)},  # A-Z
    **{f"f{index}": 0x6F + index for index in range(1, 25)},  # F1-F24
}


class HotkeyError(ValueError):
    """A hotkey string could not be understood."""


def available() -> bool:
    """Global hotkeys are a Windows facility in this build."""
    return os.name == "nt"


@dataclass(frozen=True)
class Hotkey:
    """A parsed combination, ready for ``RegisterHotKey``."""

    modifiers: int
    virtual_key: int
    text: str

    def __str__(self) -> str:
        return self.text


def parse_hotkey(text: str) -> Hotkey:
    """Parse ``"Ctrl+Alt+Pause"`` or ``"F9"``. Raises :class:`HotkeyError`."""
    if not text or not text.strip():
        raise HotkeyError("a hotkey needs at least one key")

    parts = [part.strip().lower() for part in text.split("+") if part.strip()]
    if not parts:
        raise HotkeyError(f"'{text}' is not a usable hotkey")

    modifiers = 0
    key_name: str | None = None
    for part in parts:
        if part in _MODIFIER_NAMES:
            modifiers |= _MODIFIER_NAMES[part]
            continue
        if key_name is not None:
            raise HotkeyError(
                f"'{text}' names more than one non-modifier key "
                f"('{key_name}' and '{part}')"
            )
        key_name = part

    if key_name is None:
        raise HotkeyError(f"'{text}' is only modifiers; it needs a key as well")

    virtual_key = _VIRTUAL_KEYS.get(key_name)
    if virtual_key is None:
        raise HotkeyError(
            f"'{key_name}' is not a key this build can bind. Supported keys are "
            f"A-Z, 0-9, F1-F24 and the named keys "
            f"({', '.join(sorted(k for k in _VIRTUAL_KEYS if len(k) > 1 and not k.startswith('f')))})."
        )

    canonical = "+".join(
        [name for name, bit in (("Ctrl", _MOD_CONTROL), ("Alt", _MOD_ALT),
                                ("Shift", _MOD_SHIFT), ("Win", _MOD_WIN))
         if modifiers & bit]
        + [key_name.upper() if len(key_name) == 1 else key_name.capitalize()]
    )
    return Hotkey(modifiers=modifiers | _MOD_NOREPEAT, virtual_key=virtual_key, text=canonical)


@dataclass
class HotkeyBinding:
    """One requested hotkey and what actually became of it."""

    name: str
    requested: str
    action: Callable[[], None]
    hotkey: Hotkey | None = None
    registered: bool = False
    error: str | None = None
    _identifier: int = field(default=0, repr=False)

    def describe(self) -> str:
        if self.registered and self.hotkey is not None:
            return f"{self.name}: {self.hotkey} — active"
        return f"{self.name}: {self.requested} — unavailable ({self.error})"


class GlobalHotkeys:
    """Registers hotkeys on a dedicated thread and dispatches their actions.

    Off Windows, and in tests, this reports itself unavailable and registers
    nothing. It never pretends a hotkey works.
    """

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = enabled and available()
        self._bindings: dict[str, HotkeyBinding] = {}
        self._by_identifier: dict[int, HotkeyBinding] = {}
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()
        self._stopping = threading.Event()
        self._lock = threading.RLock()
        self._next_identifier = 1

    @property
    def available(self) -> bool:
        return self._enabled

    def add(self, name: str, combination: str, action: Callable[[], None]) -> HotkeyBinding:
        """Declare a hotkey. Parsing happens now; registration happens at start."""
        binding = HotkeyBinding(name=name, requested=combination, action=action)
        try:
            binding.hotkey = parse_hotkey(combination)
        except HotkeyError as exc:
            binding.error = str(exc)
        if not self._enabled and binding.error is None:
            binding.error = "global hotkeys are only available on Windows"
        with self._lock:
            binding._identifier = self._next_identifier  # noqa: SLF001
            self._next_identifier += 1
            self._bindings[name] = binding
        return binding

    def start(self) -> None:
        """Run the registration and message loop on its own thread."""
        if not self._enabled or self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name="jarvis-hotkeys", daemon=True
        )
        self._thread.start()
        # Bounded: a hotkey thread that never becomes ready must not hang start-up.
        self._ready.wait(timeout=5.0)

    def stop(self, timeout_seconds: float = 2.0) -> None:
        self._stopping.set()
        thread, thread_id = self._thread, self._thread_id
        if thread is None:
            return
        if thread_id is not None:
            import ctypes

            ctypes.windll.user32.PostThreadMessageW(  # type: ignore[attr-defined]
                thread_id, _WM_QUIT, 0, 0
            )
        thread.join(timeout=timeout_seconds)
        self._thread = None
        self._thread_id = None

    # -- observation -------------------------------------------------------
    def bindings(self) -> tuple[HotkeyBinding, ...]:
        with self._lock:
            return tuple(self._bindings.values())

    def binding(self, name: str) -> HotkeyBinding | None:
        with self._lock:
            return self._bindings.get(name)

    def unavailable(self) -> tuple[HotkeyBinding, ...]:
        """Hotkeys the user asked for that are not actually working."""
        return tuple(b for b in self.bindings() if not b.registered)

    def trigger(self, name: str) -> bool:
        """Invoke a binding's action directly. The test and menu route."""
        binding = self.binding(name)
        if binding is None:
            return False
        binding.action()
        return True

    # -- the thread --------------------------------------------------------
    def _run(self) -> None:  # pragma: no cover - requires a Windows message loop
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32  # type: ignore[attr-defined]
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()  # type: ignore[attr-defined]

        with self._lock:
            bindings = list(self._bindings.values())
        for binding in bindings:
            if binding.hotkey is None:
                continue
            ok = user32.RegisterHotKey(
                None, binding._identifier, binding.hotkey.modifiers,  # noqa: SLF001
                binding.hotkey.virtual_key,
            )
            if ok:
                binding.registered = True
                self._by_identifier[binding._identifier] = binding  # noqa: SLF001
            else:
                binding.error = (
                    f"another application already owns {binding.hotkey}. "
                    "Choose a different combination in Settings."
                )
                _LOG.warning("could not register hotkey %s", binding.describe())

        self._ready.set()

        message = wintypes.MSG()
        try:
            while not self._stopping.is_set():
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result in (0, -1):
                    break
                if message.message == _WM_HOTKEY:
                    self._dispatch(int(message.wParam))
        finally:
            for binding in bindings:
                if binding.registered:
                    user32.UnregisterHotKey(None, binding._identifier)  # noqa: SLF001
                    binding.registered = False

    def _dispatch(self, identifier: int) -> None:  # pragma: no cover - see above
        binding = self._by_identifier.get(identifier)
        if binding is None:
            return
        try:
            binding.action()
        except Exception:  # noqa: BLE001 - one bad action must not kill the loop
            _LOG.exception("hotkey action for %s raised", binding.name)
