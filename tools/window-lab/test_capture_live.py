"""Does the screen grab produce a real image, with secrets really removed?

Phase 2 stage 4, P2-WIN-10. A research spike, outside the product runtime.

`tests/security/test_screen_capture.py` proves the *policy* against a fake
canvas: the indicator is shown first, sensitive rectangles are blacked out, and
a capture with no indicator refuses. It cannot prove that BitBlt returns pixels,
that the BMP is readable, or — the one that matters — that a redacted rectangle
is *actually black in the file*. A redaction that policy-tests approve of and
that leaves the pixels intact is worse than no redaction, because it is believed.

So this captures the real screen, redacts a rectangle, and reads the bytes back.

**What this does to your machine:** takes one screenshot of your desktop and
writes it to the scratch directory, then deletes it. Nothing is kept.

Run:  .\.venv\Scripts\python.exe tools\window-lab\test_capture_live.py
"""

from __future__ import annotations

import os
import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.capture_gdi import GdiCanvas  # noqa: E402


def main() -> int:
    if os.name != "nt":
        print("GDI capture is Windows only. Nothing to do here.")
        return 0

    print("=" * 68)
    print("Screen capture, and whether a redaction is really redacted")
    print("=" * 68)

    canvas = GdiCanvas.of_virtual_screen()
    print(f"\ncaptured {canvas.width}x{canvas.height} at origin {canvas.origin}")
    if canvas.width <= 0 or canvas.height <= 0:
        print("FAILED: the capture has no area.")
        return 1

    # A rectangle in the middle, in virtual-screen coordinates like a window's.
    box_x = canvas.origin[0] + canvas.width // 4
    box_y = canvas.origin[1] + canvas.height // 4
    box_w = canvas.width // 4
    box_h = canvas.height // 4
    canvas.fill_black((box_x, box_y, box_w, box_h))
    print(f"redacted a {box_w}x{box_h} rectangle at ({box_x}, {box_y})")

    destination = Path(tempfile.gettempdir()) / "jarvis-capture-lab.bmp"
    canvas.save(destination)
    size = destination.stat().st_size
    print(f"wrote {destination.name}: {size:,} bytes")

    failures = 0
    try:
        data = destination.read_bytes()

        if data[:2] != b"BM":
            print("  FAIL: not a BMP — Windows will not open this")
            failures += 1
        else:
            print("  OK  : BMP signature present")

        declared, offset = struct.unpack("<I", data[2:6])[0], struct.unpack("<I", data[10:14])[0]
        if declared != size:
            print(f"  FAIL: header says {declared:,} bytes, file is {size:,}")
            failures += 1
        else:
            print("  OK  : header size matches the file")

        width, height = struct.unpack("<ii", data[18:26])
        if width != canvas.width or height != -canvas.height:
            print(f"  FAIL: header says {width}x{height}, expected {canvas.width}x{-canvas.height}")
            failures += 1
        else:
            print(f"  OK  : dimensions {width}x{abs(height)}, top-down")

        # The one that matters. Sample the middle of the redacted box.
        sample_x = canvas.width // 4 + box_w // 2
        sample_y = canvas.height // 4 + box_h // 2
        index = offset + (sample_y * canvas.width + sample_x) * 4
        pixel = data[index : index + 3]
        if pixel != b"\x00\x00\x00":
            print(f"  FAIL: redacted area is {tuple(pixel)}, not black")
            failures += 1
        else:
            print("  OK  : the redacted area is black in the file")

        # And a pixel outside it should *not* be black, or we blacked out
        # everything and the test above proves nothing.
        outside = offset + (5 * canvas.width + 5) * 4
        if data[outside : outside + 3] == b"\x00\x00\x00":
            print("  WARN: the sampled pixel outside the box is also black.")
            print("        Probably a dark desktop; not conclusive either way.")
        else:
            print("  OK  : pixels outside the box survived, so it captured content")

        print("\n" + "=" * 68)
        print("PASS" if failures == 0 else f"{failures} check(s) failed")
        print("=" * 68)
        return 0 if failures == 0 else 2
    finally:
        destination.unlink(missing_ok=True)
        print(f"\ndeleted {destination}")


if __name__ == "__main__":
    raise SystemExit(main())
