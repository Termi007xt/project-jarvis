"""Shared fixtures.

Two rules every test obeys:

* **Isolated vault.** ``JARVIS_DATA_DIR`` points at a temporary directory, so no
  test ever touches the real ``%LOCALAPPDATA%``.
* **No external dependencies.** No test needs Ollama, a microphone, a GPU or the
  network. External boundaries are injected as fakes.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Qt must be told to run headlessly before PySide6 is imported anywhere.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REPO_ROOT = Path(__file__).resolve().parents[1]

from jarvis.config.paths import VaultPaths  # noqa: E402
from jarvis.config.schema import AppConfig  # noqa: E402
from jarvis.config.store import ConfigStore  # noqa: E402
from jarvis.core.audit.log import AuditLog  # noqa: E402
from jarvis.core.events.bus import EventBus  # noqa: E402
from jarvis.core.permissions.engine import PermissionEngine  # noqa: E402
from jarvis.core.tools.invoker import ToolInvoker  # noqa: E402
from jarvis.core.tools.ports import AutoApprovalPort, DenyingApprovalPort  # noqa: E402
from jarvis.core.tools.registry import ToolRegistry  # noqa: E402
from jarvis.runtime.core import JarvisCore  # noqa: E402
from jarvis.runtime.single_instance import SingleInstanceGuard  # noqa: E402
from jarvis.storage.database import Database  # noqa: E402
from jarvis.storage.migrations import migrate  # noqa: E402
from jarvis.tasks.locks import ResourceLockManager  # noqa: E402
from jarvis.tasks.scheduler import TaskScheduler  # noqa: E402
from jarvis.tasks.store import TaskStore  # noqa: E402


@pytest.fixture
def vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> VaultPaths:
    """An isolated data vault for one test."""
    root = tmp_path / "vault"
    monkeypatch.setenv("JARVIS_DATA_DIR", str(root))
    # Clear any inherited config overrides so tests see shipped defaults.
    for key in list(os.environ):
        if key.startswith("JARVIS__"):
            monkeypatch.delenv(key, raising=False)
    return VaultPaths.resolve(root).ensure()


@pytest.fixture
def config_store(vault: VaultPaths) -> ConfigStore:
    return ConfigStore(vault, env={})


@pytest.fixture
def config(config_store: ConfigStore) -> AppConfig:
    return config_store.load()


@pytest.fixture
def database(vault: VaultPaths) -> Iterator[Database]:
    db = Database(vault.db_path)
    migrate(db)
    yield db
    db.close()


@pytest.fixture
def events() -> EventBus:
    return EventBus()


@pytest.fixture
def audit(vault: VaultPaths, database: Database, events: EventBus) -> AuditLog:
    return AuditLog(
        vault.audit_log_path, database=database, event_bus=events, instance_id="test-instance"
    )


@pytest.fixture
def permissions(database: Database, audit: AuditLog, events: EventBus) -> PermissionEngine:
    return PermissionEngine(database, audit, events)


@pytest.fixture
def registry(audit: AuditLog, events: EventBus) -> ToolRegistry:
    return ToolRegistry(audit, events)


@pytest.fixture
def tasks(database: Database, audit: AuditLog, events: EventBus) -> TaskStore:
    return TaskStore(database, audit, events, instance_id="test-instance")


@pytest.fixture
def locks(database: Database, audit: AuditLog, events: EventBus) -> ResourceLockManager:
    return ResourceLockManager(database, "test-instance", audit, events)


@pytest.fixture
def invoker(
    registry: ToolRegistry,
    permissions: PermissionEngine,
    audit: AuditLog,
    locks: ResourceLockManager,
    events: EventBus,
    database: Database,
) -> Iterator[ToolInvoker]:
    tool_invoker = ToolInvoker(
        registry,
        permissions,
        audit,
        locks=locks,
        approvals=DenyingApprovalPort(),
        event_bus=events,
        database=database,
    )
    yield tool_invoker
    tool_invoker.shutdown(wait=False)


@pytest.fixture
def approving_invoker(
    registry: ToolRegistry,
    permissions: PermissionEngine,
    audit: AuditLog,
    locks: ResourceLockManager,
    events: EventBus,
    database: Database,
) -> Iterator[ToolInvoker]:
    """An invoker whose approval port says yes to anything below high risk."""
    tool_invoker = ToolInvoker(
        registry,
        permissions,
        audit,
        locks=locks,
        approvals=AutoApprovalPort(),
        event_bus=events,
        database=database,
    )
    yield tool_invoker
    tool_invoker.shutdown(wait=False)


@pytest.fixture
def scheduler(
    tasks: TaskStore, locks: ResourceLockManager, audit: AuditLog, events: EventBus
) -> Iterator[TaskScheduler]:
    sched = TaskScheduler(
        tasks, locks, audit=audit, event_bus=events, max_concurrent=2,
        poll_interval_seconds=0.02,
    )
    yield sched
    sched.stop(timeout_seconds=5.0)


@pytest.fixture
def core(vault: VaultPaths) -> Iterator[JarvisCore]:
    """A fully wired headless core with single-instance enforcement disabled."""
    instance = JarvisCore(
        vault,
        config_store=ConfigStore(vault, env={}),
        single_instance=SingleInstanceGuard(
            lock_file=vault.runtime_dir / "test.lock", force_lock_file=True
        ),
        enforce_single_instance=False,
        # Real speech models take tens of seconds to load and are not what any
        # test is checking. Worth recording *why* this is off rather than just
        # that it is: switching it on made a latent scheduler/recovery race
        # reproducible, so leaving it on would have let a start-up optimisation
        # decide whether the suite was green.
        preload_models=False,
    ).start()
    yield instance
    if instance.started:
        instance.shutdown("test teardown")


@pytest.fixture(scope="session")
def qapp():
    """One offscreen QApplication for the whole session."""
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def source_files() -> list[Path]:
    """Every Python source file in the shipped package."""
    return sorted((REPO_ROOT / "src" / "jarvis").rglob("*.py"))
