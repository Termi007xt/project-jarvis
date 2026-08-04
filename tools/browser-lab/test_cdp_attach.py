"""Does Brave accept remote debugging under ADR-0019 Option A?

Phase 2 stage 0. A research spike, outside the product runtime and outside the
security policy — the same status `tools/voice-lab/` holds.

**The question.** Phase 2 needs DOM-first browser automation. Playwright normally
launches the browser itself, which would be a second process-creation call site
and is refused (ADR-0029, one call site, not to be broadened). The alternative is
to launch Brave through the *existing* authorised call site with a debugging port
and have Playwright connect over CDP, making it a client rather than a launcher.

That only works if Brave actually opens the port. Chromium refuses
`--remote-debugging-port` when running against its **default user-data
directory** — a deliberate guard against cookie theft. ADR-0019 Option A
(`--profile-directory=Jarvis`) selects a profile *inside* the default user-data
directory, so it is expected to be refused. Option B (`--user-data-dir=<path>`)
is expected to work.

Both are measured here rather than argued about, and the result decides ADR-0019.

**What this does to your machine:** launches Brave up to twice, waits a few
seconds, and closes what it opened. Option B creates a throwaway profile
directory under the system temp folder and deletes it afterwards.

Run:  .\.venv\Scripts\python.exe tools\browser-lab\test_cdp_attach.py
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

# The spike measures the *real* launch path, not a parallel one. If this import
# breaks, the finding is about the product, not about the spike.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.launch import (  # noqa: E402
    ApplicationEntry,
    ArgumentKind,
    LaunchKind,
    build_argv,
    launch_argv,
    process_running,
)

VERIFY_TIMEOUT_SECONDS = 12.0
POLL_SECONDS = 0.25


def free_port() -> int:
    """An ephemeral port. ADR-0031 requires per-session, never a fixed one."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def brave_path() -> str:
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    return rf"{program_files}\BraveSoftware\Brave-Browser\Application\brave.exe"


def cdp_version(port: int, timeout_seconds: float) -> dict[str, str] | None:
    """Poll the CDP endpoint. Returns its banner, or None if it never opened."""
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError):
            time.sleep(POLL_SECONDS)
    return None


def measure(label: str, profile_arguments: tuple[str, ...]) -> dict[str, object]:
    """Launch Brave with the given profile flags and see if CDP answers."""
    port = free_port()
    entry = ApplicationEntry(
        app_id="brave_spike",
        display_name=f"Brave ({label})",
        kind=LaunchKind.EXECUTABLE,
        target=brave_path(),
        fixed_arguments=(*profile_arguments, f"--remote-debugging-port={port}"),
        argument_kind=ArgumentKind.NONE,
        verify_process_names=("brave.exe",),
    )

    argv = build_argv(entry)
    print(f"\n--- {label} ---")
    print(f"argv: {list(argv)}")

    if not Path(entry.target).exists():
        print(f"SKIPPED: Brave is not installed at {entry.target}")
        return {"label": label, "result": "brave_not_found", "port": port}

    try:
        pid = launch_argv(argv)
    except OSError as exc:
        print(f"FAILED to launch: {exc}")
        return {"label": label, "result": "launch_failed", "detail": str(exc)}

    banner = cdp_version(port, VERIFY_TIMEOUT_SECONDS)
    running = process_running(("brave.exe",))

    if banner is None:
        print(f"CDP DID NOT OPEN on 127.0.0.1:{port} within {VERIFY_TIMEOUT_SECONDS:.0f}s")
        print(f"  brave.exe running: {running}  (pid we started: {pid})")
        print("  -> remote debugging was refused, or Brave handed off to an")
        print("     already-running instance that has no debugging port.")
        return {"label": label, "result": "no_cdp", "port": port, "brave_running": running}

    print(f"CDP OPENED on 127.0.0.1:{port}")
    for key in ("Browser", "Protocol-Version", "webSocketDebuggerUrl"):
        if key in banner:
            value = banner[key]
            # The websocket URL is a live control channel. Do not print it whole.
            if key == "webSocketDebuggerUrl":
                value = value.split("/devtools/")[0] + "/devtools/<redacted>"
            print(f"  {key}: {value}")
    return {"label": label, "result": "cdp_open", "port": port, "browser": banner.get("Browser")}


def main() -> int:
    if os.name != "nt":
        print("This spike measures Brave on Windows. Nothing to do here.")
        return 0

    print("=" * 70)
    print("ADR-0019 / ADR-0031 spike: can Playwright attach without a second")
    print("process-creation call site?")
    print("=" * 70)
    print(
        "\nNOTE: an already-running Brave will make Option A ambiguous — a second\n"
        "brave.exe usually hands its command line to the existing instance and\n"
        "exits, so no port opens and the cause is indistinguishable from refusal.\n"
        "Close Brave before trusting an Option A 'no_cdp' result."
    )
    print(f"\nBrave already running: {process_running(('brave.exe',))}")

    findings = []

    # Option A — a named profile inside the DEFAULT user-data directory.
    findings.append(measure("Option A: --profile-directory=Jarvis", ("--profile-directory=Jarvis",)))

    # Option B — an entirely separate user-data directory.
    temp_profile = Path(tempfile.mkdtemp(prefix="jarvis-cdp-spike-"))
    try:
        findings.append(
            measure(
                "Option B: --user-data-dir=<temp>",
                (f"--user-data-dir={temp_profile}", "--profile-directory=Jarvis"),
            )
        )
    finally:
        # Best effort: Brave may still hold files open. A leftover temp
        # directory is noise, not a failure of the measurement.
        shutil.rmtree(temp_profile, ignore_errors=True)

    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)
    for finding in findings:
        print(f"  {finding['label']:<42} -> {finding['result']}")

    outcomes = {finding["label"]: finding["result"] for finding in findings}
    option_a = next((v for k, v in outcomes.items() if k.startswith("Option A")), None)
    option_b = next((v for k, v in outcomes.items() if k.startswith("Option B")), None)

    print()
    if option_a == "cdp_open":
        print("ADR-0019 Option A stands. The owner's choice is buildable as chosen.")
    elif option_b == "cdp_open":
        print("ADR-0019 Option A is refused; Option B works. The pre-authorised")
        print("fallback applies: record Option B with this measurement attached.")
    else:
        print("Neither option opened a CDP port. Do NOT fall back to letting")
        print("Playwright launch Brave — that is the second process-creation call")
        print("site ADR-0029 forbids. Stop and re-plan the attach mechanism.")

    print("\nClose any Brave windows this spike opened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
