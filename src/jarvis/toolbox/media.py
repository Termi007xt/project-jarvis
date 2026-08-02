"""Media and volume control (PRD FR-094, catalogue `media.playback_control`,
`device.control_volume`).

Sends the system media and volume **virtual keys** through `SendInput`. Two
things make this narrow rather than "keyboard automation", which is a separate
medium-risk capability that belongs to Phase 2:

* The key codes come from a **closed table** in this module. There is no path by
  which an arbitrary key can be injected — the tool's typed input is an enum of
  actions, not a key code.
* The keys are **system-global media keys**, not keystrokes aimed at a window.
  Nothing is focused, nothing is typed into an application.

`SendInput` is a user32 call through `ctypes`. It creates no process and is not
on the ADR-0003 denylist.
"""

from __future__ import annotations

import ctypes
import logging
import os
from ctypes import wintypes
from enum import Enum

__all__ = ["MediaAction", "VolumeAction", "send_media_key", "media_available"]

_LOG = logging.getLogger(__name__)

#: The closed table. Nothing outside it can ever be sent.
_VIRTUAL_KEYS: dict[str, int] = {
    "play_pause": 0xB3,   # VK_MEDIA_PLAY_PAUSE
    "next": 0xB0,         # VK_MEDIA_NEXT_TRACK
    "previous": 0xB1,     # VK_MEDIA_PREV_TRACK
    "stop": 0xB2,         # VK_MEDIA_STOP
    "mute": 0xAD,         # VK_VOLUME_MUTE
    "volume_up": 0xAF,    # VK_VOLUME_UP
    "volume_down": 0xAE,  # VK_VOLUME_DOWN
}

_KEYEVENTF_KEYUP = 0x0002
_INPUT_KEYBOARD = 1


class MediaAction(str, Enum):
    PLAY_PAUSE = "play_pause"
    NEXT = "next"
    PREVIOUS = "previous"
    STOP = "stop"


class VolumeAction(str, Enum):
    MUTE = "mute"
    UP = "volume_up"
    DOWN = "volume_down"


def media_available() -> bool:
    return os.name == "nt"


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", _KEYBDINPUT), ("padding", ctypes.c_byte * 32)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUTUNION)]


def send_media_key(action: str, repeat: int = 1) -> bool:
    """Send one media or volume key. Returns whether Windows accepted it.

    ``action`` must name an entry in the closed table above; anything else
    raises rather than being passed through as a key code.
    """
    virtual_key = _VIRTUAL_KEYS.get(action)
    if virtual_key is None:
        raise ValueError(
            f"'{action}' is not a media or volume action. Only "
            f"{sorted(_VIRTUAL_KEYS)} can be sent; this tool cannot inject "
            "arbitrary keystrokes (that is a Phase 2 capability with its own "
            "risk level)."
        )
    if not media_available():
        return False
    if not 1 <= repeat <= 20:
        raise ValueError("repeat must be between 1 and 20")

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    sent = 0
    for _ in range(repeat):
        for flags in (0, _KEYEVENTF_KEYUP):
            event = _INPUT(
                type=_INPUT_KEYBOARD,
                union=_INPUTUNION(
                    ki=_KEYBDINPUT(
                        wVk=virtual_key, wScan=0, dwFlags=flags, time=0,
                        dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)),
                    )
                ),
            )
            sent += user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(_INPUT))
    return sent == repeat * 2
