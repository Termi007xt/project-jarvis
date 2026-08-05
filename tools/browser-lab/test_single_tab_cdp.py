"""Can Jarvis drive one tab without touching any of the others?

The spike behind replacing Playwright for the browser tools, run before any
product code is written.

**The problem it exists to solve.** `connect_over_cdp` attaches to every page in
the browser — measured at ten out of ten in `test_attach_cost.py`. Under
ADR-0019 Option D that browser is the owner's own, so attaching announces Jarvis
to every tab they have open. They reported the consequences twice: sleeping tabs
waking on 2026-08-05, then every open YouTube video playing at once. Neither is
something Jarvis code does; both are downstream of an attach that is browser-wide
by design. There is no Playwright option to narrow it.

Chromium's DevTools Protocol underneath is per-target. `PUT /json/new` creates a
tab and returns *that tab's* WebSocket URL, and a socket to it can drive that tab
and reach nothing else. No Node driver, no greenlets, and no thread affinity —
which is separately what produced the blank tab on 2026-08-05.

Four questions, and the last one is the whole point:

  1. Can we create a tab and drive it over one socket?
  2. Can we read a YouTube result list positionally?
  3. Can we play result N and verify it by reading the player back?
  4. **Are the browser's other tabs left completely alone?**

**What this does to your machine:** opens Brave in a scratch profile with three
decoy tabs, drives a fourth, and plays a video. Your own profile is never
opened. Sound will come out.

Run:  .\.venv\Scripts\python.exe tools\browser-lab\test_single_tab_cdp.py
"""

from __future__ import annotations

import json
import shutil
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.launch import launch_argv  # noqa: E402

BRAVE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
QUERY = "RTX 5070"
POSITION = 1  # "the second video"

#: Decoy tabs. If any of these moves, the approach has failed its main test.
DECOYS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def http_json(url: str, method: str = "GET") -> Any:
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=10.0) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body.strip() else None


def wait_for_port(port: int, timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            http_json(f"http://127.0.0.1:{port}/json/version")
            return True
        except (urllib.error.URLError, OSError, ValueError):
            time.sleep(0.25)
    return False


class Tab:
    """One Chromium tab, driven over its own WebSocket. Nothing else is reachable."""

    def __init__(self, ws_url: str) -> None:
        from websocket import create_connection

        # `suppress_origin` matters and is not a workaround. Chromium refuses a
        # DevTools socket that arrives with an `Origin` header, because that is
        # what a *web page* connecting would look like, and the alternative the
        # error suggests — `--remote-allow-origins=*` — would open the debugging
        # port to any page the browser loads. Sending no Origin says "not a web
        # page", which is true, and keeps the port closed to everything else.
        self._ws = create_connection(ws_url, timeout=30.0, suppress_origin=True)
        self._next_id = 0

    def send(self, method: str, **params: Any) -> Any:
        self._next_id += 1
        message_id = self._next_id
        self._ws.send(json.dumps({"id": message_id, "method": method, "params": params}))
        # Replies and events share the socket; ours is the one carrying our id.
        while True:
            message = json.loads(self._ws.recv())
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"{method} failed: {message['error']}")
                return message.get("result")

    def evaluate(self, expression: str) -> Any:
        result = self.send(
            "Runtime.evaluate",
            expression=expression,
            returnByValue=True,
            awaitPromise=True,
        )
        return result.get("result", {}).get("value")

    def navigate(self, url: str, timeout_seconds: float = 30.0) -> None:
        self.send("Page.navigate", url=url)
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self.evaluate("document.readyState") in ("interactive", "complete"):
                return
            time.sleep(0.1)
        raise TimeoutError(f"{url} did not load within {timeout_seconds:.0f}s")

    def close(self) -> None:
        try:
            self._ws.close()
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    profile = Path(tempfile.mkdtemp(prefix="jarvis-onetab-lab-"))
    port = free_port()
    launch_argv(
        (
            BRAVE, f"--user-data-dir={profile}", f"--remote-debugging-port={port}",
            "--no-first-run", "--no-default-browser-check", *DECOYS,
        )
    )
    if not wait_for_port(port):
        print("FAILED: no debugging port appeared")
        return 1

    print("=" * 70)
    print("Driving one tab over raw CDP, with three decoy tabs open")
    print("=" * 70)
    print("\nLetting the three decoy tabs settle...")
    time.sleep(18.0)

    before = http_json(f"http://127.0.0.1:{port}/json/list")
    decoy_ids = [t["id"] for t in before if t.get("type") == "page"]
    print(f"  decoy tabs: {len(decoy_ids)}")

    # 1. our own tab, created without attaching to anything else
    created = http_json(f"http://127.0.0.1:{port}/json/new?about:blank", method="PUT")
    tab = Tab(created["webSocketDebuggerUrl"])
    print(f"  created our own tab, and connected to it alone")

    try:
        # 2. read a result list, positionally
        search_url = (
            "https://www.youtube.com/results?search_query="
            + urllib.parse.quote_plus(QUERY)
        )
        print(f'\n1. "search {QUERY.lower()} on youtube"')
        tab.navigate(search_url)

        results = []
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            results = tab.evaluate(
                """(() => {
                    const rows = document.querySelectorAll('ytd-video-renderer');
                    return Array.from(rows).map(row => {
                        const a = row.querySelector('a#video-title');
                        const href = a ? a.getAttribute('href') || '' : '';
                        const m = href.match(/[?&]v=([^&]+)/);
                        return {
                            title: a ? (a.getAttribute('title') || '') : '',
                            video_id: m ? m[1] : ''
                        };
                    });
                })()"""
            ) or []
            if results:
                break
            time.sleep(0.5)

        print(f"   {len(results)} result(s):\n")
        for index, item in enumerate(results[:5]):
            marker = "  <-- 'the second video'" if index == POSITION else ""
            print(f"     [{index}] {item['title'][:56]}{marker}")

        if len(results) <= POSITION:
            print("\nFAILED: not enough results to play.")
            return 1

        # 3. play by position — by *navigating* to the id at that position.
        # Still strictly positional, and it needs no synthetic click at all.
        chosen = results[POSITION]
        print(f'\n2. "play the second video"  ->  position {POSITION}')
        tab.navigate(f"https://www.youtube.com/watch?v={chosen['video_id']}")

        state = None
        deadline = time.monotonic() + 25.0
        while time.monotonic() < deadline:
            state = tab.evaluate(
                """(() => {
                    const v = document.querySelector('video');
                    if (!v) return null;
                    const u = new URL(window.location.href);
                    return {
                        playing: !v.paused && !v.ended && v.currentTime > 0,
                        video_id: u.searchParams.get('v') || ''
                    };
                })()"""
            )
            if state and state.get("playing"):
                break
            time.sleep(0.5)

        verified = bool(
            state and state.get("playing") and state.get("video_id") == chosen["video_id"]
        )
        print(f"   expected : {chosen['video_id']!r}")
        print(f"   playing  : {state}")
        print(f"   VERIFIED : {verified}")

        # 4. THE POINT: were the decoys touched?
        print("\n3. Did anything happen to the three decoy tabs?\n")
        untouched = True
        for index, target_id in enumerate(decoy_ids):
            entry = next(
                (t for t in http_json(f"http://127.0.0.1:{port}/json/list")
                 if t["id"] == target_id),
                None,
            )
            if entry is None:
                print(f"     [{index}] GONE — the tab no longer exists")
                untouched = False
                continue
            # Read its state via its own socket, only to observe it.
            probe = Tab(entry["webSocketDebuggerUrl"])
            try:
                decoy = probe.evaluate(
                    """(() => {
                        const v = document.querySelector('video');
                        return v ? {paused: v.paused, t: v.currentTime} : null;
                    })()"""
                )
            finally:
                probe.close()
            moved = bool(decoy and not decoy["paused"])
            if moved:
                untouched = False
            print(
                f"     [{index}] {'PLAYING (bad)' if moved else 'still paused'}"
                f"   currentTime={decoy['t'] if decoy else '?'}"
            )

        print("\n" + "=" * 70)
        if verified and untouched:
            print("PASS: the second video played, verified by id, and not one of")
            print("the other tabs moved. This is what Playwright cannot do.")
        elif not untouched:
            print("FAIL: a decoy tab moved. Single-tab CDP is not isolating.")
        else:
            print("Playback not verified. Reported honestly, not as success.")
        print("=" * 70)
        return 0 if (verified and untouched) else 2
    finally:
        tab.close()
        try:
            http_json(f"http://127.0.0.1:{port}/json/close/{created['id']}")
        except Exception:  # noqa: BLE001
            pass
        for target_id in decoy_ids:
            try:
                http_json(f"http://127.0.0.1:{port}/json/close/{target_id}")
            except Exception:  # noqa: BLE001
                pass
        time.sleep(2.0)
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
