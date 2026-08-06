"""The real screen grab, via GDI (FR-073, P2-WIN-10).

Windows only, imported lazily, and deliberately dependency-free. Pillow would be
the obvious way to write the file and is not installed; adding it for one
`save()` call is a large dependency for a small job, and a hand-rolled *PNG*
encoder is the kind of thing that is subtly wrong in a way nothing here could
catch — there is no decoder available to check it against.

So the file is a BMP. Uncompressed and therefore large, which is a real cost and
the reason retention matters, but the format is four fixed-size headers and a
pixel array: verifiable by reading its own bytes back, which the tests do.

`fill_black` paints over a rectangle *before* anything is written to disk, so a
redacted region never exists in a file at all — see `jarvis.toolbox.capture` for
why that is the shape of the control.
"""

from __future__ import annotations

import ctypes
import logging
import os
import struct
from ctypes import wintypes
from pathlib import Path

__all__ = ["GdiCanvas"]

_LOG = logging.getLogger(__name__)

#: `GetSystemMetrics` indices for the virtual screen — all monitors together,
#: which is what "the whole screen" means on a multi-monitor desktop.
_SM_XVIRTUALSCREEN = 76
_SM_YVIRTUALSCREEN = 77
_SM_CXVIRTUALSCREEN = 78
_SM_CYVIRTUALSCREEN = 79

_SRCCOPY = 0x00CC0020
_DIB_RGB_COLORS = 0


class GdiCanvas:
    """A captured bitmap, held as 32-bit BGRA rows, top row first."""

    def __init__(self, pixels: bytearray, width: int, height: int, origin=(0, 0)) -> None:
        self._pixels = pixels
        self.width = width
        self.height = height
        #: Where this image sits in virtual-screen coordinates. Window bounds
        #: arrive in those, and on a multi-monitor desktop the top-left is
        #: frequently negative — subtracting the origin is what makes a
        #: redaction rectangle land where the window actually is.
        self.origin = origin

    # -- capture ----------------------------------------------------------
    @classmethod
    def of_virtual_screen(cls) -> "GdiCanvas":
        if os.name != "nt":  # pragma: no cover - guarded by the caller
            raise RuntimeError("GDI capture is Windows only")

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        user32.SetProcessDPIAware()

        left = user32.GetSystemMetrics(_SM_XVIRTUALSCREEN)
        top = user32.GetSystemMetrics(_SM_YVIRTUALSCREEN)
        width = user32.GetSystemMetrics(_SM_CXVIRTUALSCREEN)
        height = user32.GetSystemMetrics(_SM_CYVIRTUALSCREEN)

        screen_dc = user32.GetDC(0)
        memory_dc = gdi32.CreateCompatibleDC(screen_dc)
        bitmap = gdi32.CreateCompatibleBitmap(screen_dc, width, height)
        previous = gdi32.SelectObject(memory_dc, bitmap)
        try:
            if not gdi32.BitBlt(
                memory_dc, 0, 0, width, height, screen_dc, left, top, _SRCCOPY
            ):
                raise RuntimeError("the screen could not be copied")

            header = _BitmapInfoHeader()
            header.biSize = ctypes.sizeof(_BitmapInfoHeader)
            header.biWidth = width
            # Negative height asks GDI for a top-down image, so row 0 is the top
            # of the screen. Bottom-up is the BMP default and inverts every
            # rectangle we later paint.
            header.biHeight = -height
            header.biPlanes = 1
            header.biBitCount = 32
            header.biCompression = 0

            buffer = (ctypes.c_char * (width * height * 4))()
            if not gdi32.GetDIBits(
                memory_dc, bitmap, 0, height, buffer, ctypes.byref(header), _DIB_RGB_COLORS
            ):
                raise RuntimeError("the captured bitmap could not be read")
            pixels = bytearray(buffer)
        finally:
            gdi32.SelectObject(memory_dc, previous)
            gdi32.DeleteObject(bitmap)
            gdi32.DeleteDC(memory_dc)
            user32.ReleaseDC(0, screen_dc)

        _LOG.debug("captured %dx%d at (%d, %d)", width, height, left, top)
        return cls(pixels, width, height, origin=(left, top))

    # -- redaction --------------------------------------------------------
    def fill_black(self, rect: tuple[int, int, int, int]) -> None:
        """Paint a rectangle black, in place, before anything is saved.

        Clipped to the image, because a window may hang off the edge of the
        virtual screen and an unclipped write would corrupt neighbouring rows —
        which, for a redaction, would leave part of the thing being hidden
        visible somewhere else.
        """
        x, y, width, height = rect
        x -= self.origin[0]
        y -= self.origin[1]

        left = max(0, x)
        top = max(0, y)
        right = min(self.width, x + width)
        bottom = min(self.height, y + height)
        if right <= left or bottom <= top:
            return

        black = bytes(4 * (right - left))
        for row in range(top, bottom):
            start = (row * self.width + left) * 4
            self._pixels[start : start + len(black)] = black

    # -- writing ----------------------------------------------------------
    def save(self, path: str | os.PathLike[str]) -> None:
        """Write a 32-bit BMP. Four headers and the pixels, nothing clever."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        pixel_bytes = len(self._pixels)
        file_header = struct.pack(
            "<2sIHHI", b"BM", 14 + 40 + pixel_bytes, 0, 0, 14 + 40
        )
        info_header = struct.pack(
            "<IiiHHIIiiII",
            40,               # header size
            self.width,
            -self.height,     # top-down, matching how the pixels are held
            1,                # planes
            32,               # bits per pixel
            0,                # BI_RGB, uncompressed
            pixel_bytes,
            2835,             # ~72 DPI
            2835,
            0,
            0,
        )
        with open(destination, "wb") as handle:
            handle.write(file_header)
            handle.write(info_header)
            handle.write(bytes(self._pixels))


class _BitmapInfoHeader(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]
