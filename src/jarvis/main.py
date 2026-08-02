"""Entry point.

    jarvis                 start the tray application
    jarvis --check         start the core headlessly, report status, exit
    jarvis --data-dir DIR  use a different data vault

The GUI is optional: ``--check`` exercises the whole engine without Qt, which is
what CI and a smoke test use.
"""

from __future__ import annotations

import argparse
import sys

from jarvis import APP_NAME, APP_VERSION
from jarvis.config.paths import VaultPaths
from jarvis.diagnostics.logging_setup import configure_logging
from jarvis.runtime.core import JarvisCore
from jarvis.runtime.single_instance import AlreadyRunningError

__all__ = ["main", "build_parser"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis",
        description=f"{APP_NAME} — local-first Windows desktop AI agent (Phase 0).",
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Data vault location. Defaults to %%LOCALAPPDATA%%\\ProjectJarvis.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Start the core headlessly, print a status report and exit.",
    )
    parser.add_argument(
        "--require-healthy",
        action="store_true",
        help=(
            "With --check, exit non-zero when the local model runtime is "
            "unreachable. Without it, an honest report of an unreachable "
            "runtime is still a successful self-check."
        ),
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override the configured log level.",
    )
    parser.add_argument(
        "--allow-multiple-instances",
        action="store_true",
        help="Development only. Skips the single-instance guard.",
    )
    return parser


def _run_check(core: JarvisCore, require_healthy: bool = False) -> int:
    from jarvis.audio.availability import describe_voice_stack

    status = core.status()
    health = core.refresh_health()
    voice = describe_voice_stack(core.config)
    print(f"{APP_NAME} {status.app_version}")
    print(f"  vault            {status.vault_root}")
    print(f"  database schema  v{status.schema_version}")
    print(f"  network mode     {status.network_mode}")
    print(f"  tools            {', '.join(status.registered_tools) or 'none'}")
    print(f"  runners          {', '.join(core.scheduler.runner_ids()) or 'none'}")
    print(f"  workers          {', '.join(status.workers) or 'none'}")
    print(f"  held locks       {', '.join(status.held_locks) or 'none'}")
    print(f"  active tasks     {status.active_tasks}")
    print(f"  recovery         {status.recovery.describe() if status.recovery else 'not run'}")
    print(f"  model runtime    {health.describe()}")
    print(f"  secret store     {'available' if core.secrets.available else 'unavailable'}")
    print(f"  voice stack      {voice.summary()}")
    print(f"  audit records    {core.audit.count()}")

    # An unreachable runtime reported honestly is still a successful
    # self-check; only a crash is a failure. --require-healthy is for callers
    # that need the stronger statement, such as a deployment gate.
    if require_healthy and not health.reachable:
        print(
            "  --require-healthy was given and the local model runtime is not "
            f"reachable: {health.error or health.skipped_reason or 'no detail'}",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    paths = VaultPaths.resolve(args.data_dir).ensure()
    configure_logging(paths.app_log_path, args.log_level or "INFO")

    try:
        core = JarvisCore(
            paths, enforce_single_instance=not args.allow_multiple_instances
        ).start()
    except AlreadyRunningError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.check:
        try:
            return _run_check(core, require_healthy=args.require_healthy)
        finally:
            core.shutdown("--check completed")

    try:
        from PySide6.QtWidgets import QApplication

        from jarvis.ui.app import JarvisApplication
    except ImportError as exc:  # pragma: no cover - PySide6 is a hard dependency
        core.shutdown("GUI unavailable")
        print(f"the graphical shell could not start: {exc}", file=sys.stderr)
        return 3

    app = QApplication.instance() or QApplication(sys.argv[:1])
    application = JarvisApplication(core, app)  # noqa: F841 - owns the tray lifetime
    try:
        return app.exec()
    finally:
        core.shutdown("application exited")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
