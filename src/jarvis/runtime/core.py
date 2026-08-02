"""``JarvisCore`` — the composition root (ARCHITECTURE.md section 6.9).

Owns startup and shutdown ordering and nothing else. Imports no GUI code, so the
whole engine is importable and testable headlessly and the shell is a
replaceable adapter (ADR-0004).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jarvis import APP_VERSION
from jarvis.common import new_id
from jarvis.config.paths import VaultPaths
from jarvis.config.schema import AppConfig, NetworkMode
from jarvis.config.store import ConfigStore
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import (
    AppStarted,
    AppStopping,
    ConfigChanged,
    EmergencyStopCompleted,
    EmergencyStopRequested,
    HealthChecked,
    NetworkModeChanged,
)
from jarvis.core.permissions.engine import DefaultPolicy, PermissionEngine
from jarvis.core.permissions.models import Decision, GrantScope
from jarvis.core.secrets import SecretStore
from jarvis.core.tools.approvals import ApprovalQueue
from jarvis.core.tools.invoker import ToolCall, ToolInvoker
from jarvis.core.tools.ports import ApprovalPort
from jarvis.core.tools.registry import ToolRegistry
from jarvis.llm.conversation import ConversationEngine
from jarvis.llm.history import Conversation, ConversationStore
from jarvis.llm.ollama.chat import OllamaChatProvider
from jarvis.llm.ollama.health import OllamaHealth, OllamaHealthChecker
from jarvis.llm.personality import PersonalityStore
from jarvis.llm.routing import ModelRouter
from jarvis.runtime.single_instance import SingleInstanceGuard
from jarvis.runtime.workers import PeriodicWorker, WorkerSupervisor
from jarvis.storage.database import Database
from jarvis.storage.migrations import SCHEMA_VERSION, migrate
from jarvis.tasks.locks import ResourceLockManager
from jarvis.tasks.recovery import (
    RecoveryReport,
    close_instance,
    recover_interrupted_work,
    register_instance,
)
from jarvis.tasks.scheduler import TaskScheduler
from jarvis.tasks.states import TaskState
from jarvis.tasks.store import TaskStore
from jarvis.toolbox.system_health import HealthCheckRunner, SystemHealthTool

__all__ = ["JarvisCore", "CoreStatus", "EmergencyStopReport"]

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmergencyStopReport:
    """Exactly what was stopped (PRD section 11.3 requires telling the user)."""

    cancelled_task_ids: tuple[str, ...]
    released_locks: tuple[str, ...]
    stopped_workers: tuple[str, ...]
    denied_approvals: int = 0

    def describe(self) -> str:
        text = (
            f"Stopped: {len(self.cancelled_task_ids)} task(s), "
            f"{len(self.released_locks)} resource lock(s), "
            f"{len(self.stopped_workers)} worker(s)."
        )
        if self.denied_approvals:
            text += f" Denied {self.denied_approvals} pending approval(s)."
        return text


@dataclass(frozen=True)
class CoreStatus:
    running: bool
    instance_id: str
    app_version: str
    schema_version: int
    network_mode: str
    vault_root: str
    registered_tools: tuple[str, ...]
    active_tasks: int
    held_locks: tuple[str, ...]
    workers: tuple[str, ...]
    last_health: OllamaHealth | None
    recovery: RecoveryReport | None


class JarvisCore:
    """Everything except the user interface."""

    def __init__(
        self,
        paths: VaultPaths | None = None,
        *,
        config_store: ConfigStore | None = None,
        approvals: ApprovalPort | None = None,
        approval_timeout_seconds: float | None = None,
        single_instance: SingleInstanceGuard | None = None,
        enforce_single_instance: bool = True,
        session_id: str | None = None,
    ) -> None:
        self.paths = (paths or VaultPaths.resolve()).ensure()
        self.instance_id = new_id()
        self.session_id = session_id or new_id()

        self._config_store = config_store or ConfigStore(self.paths)
        # An injected port replaces the queue entirely (tests do this). Otherwise
        # the core owns a queue, which denies until a UI declares itself
        # connected — silence is never consent (ADR-0010).
        self._injected_approvals = approvals
        self._approval_timeout_seconds = approval_timeout_seconds
        self._enforce_single_instance = enforce_single_instance
        self._guard = single_instance or SingleInstanceGuard(
            lock_file=self.paths.runtime_dir / "single-instance.lock",
            force_lock_file=os.name != "nt",
        )

        self._started = False
        self._last_health: OllamaHealth | None = None
        self._recovery: RecoveryReport | None = None

        # Populated by start().
        self.config: AppConfig
        self.events: EventBus
        self.database: Database
        self.audit: AuditLog
        self.permissions: PermissionEngine
        self.registry: ToolRegistry
        self.approvals: ApprovalQueue | None = None
        self.secrets: SecretStore
        self.models: ModelRouter
        self.history: ConversationStore
        self.personality: PersonalityStore
        self.conversation: ConversationEngine
        self.invoker: ToolInvoker
        self.tasks: TaskStore
        self.locks: ResourceLockManager
        self.scheduler: TaskScheduler
        self.workers: WorkerSupervisor

    # -- startup -----------------------------------------------------------
    def start(self) -> "JarvisCore":
        if self._started:
            return self

        # 1-2. configuration
        self.config = self._config_store.load()

        # 3. single instance, before touching the database
        if self._enforce_single_instance:
            self._guard.acquire_or_raise()

        # 4. storage
        self.database = Database(self.paths.db_path)
        migrate(self.database)
        register_instance(self.database, self.instance_id, os.getpid(), APP_VERSION)

        # 5. events and audit
        self.events = EventBus()
        self.audit = AuditLog(
            self.paths.audit_log_path,
            database=self.database,
            event_bus=self.events,
            instance_id=self.instance_id,
            max_value_chars=self.config.logging.max_audit_value_chars,
            write_to_sqlite=self.config.logging.audit_to_sqlite,
        )

        # 6. permissions, tools
        self.permissions = PermissionEngine(
            self.database,
            self.audit,
            self.events,
            policy=DefaultPolicy(
                low=Decision(self.config.permissions.default_policy.low),
                medium=Decision(self.config.permissions.default_policy.medium),
                allow_always_for_low_risk=self.config.permissions.allow_always_for_low_risk,
                session_grant_ttl_seconds=self.config.permissions.session_grant_ttl_seconds,
            ),
        )
        self.registry = ToolRegistry(self.audit, self.events)
        self.secrets = SecretStore(self.database, self.audit)

        # 6b. the approval surface's queue (ADR-0027). It denies everything
        # until a user interface calls set_interactive(True).
        approval_port: ApprovalPort
        if self._injected_approvals is None:
            self.approvals = ApprovalQueue(
                audit=self.audit,
                event_bus=self.events,
                timeout_seconds=(
                    self._approval_timeout_seconds
                    if self._approval_timeout_seconds is not None
                    else self.config.ui.approval_timeout_seconds
                ),
            )
            approval_port = self.approvals
        else:
            approval_port = self._injected_approvals

        # 7. tasks and locks
        self.tasks = TaskStore(self.database, self.audit, self.events, self.instance_id)
        self.locks = ResourceLockManager(
            self.database, self.instance_id, self.audit, self.events
        )
        self.invoker = ToolInvoker(
            self.registry,
            self.permissions,
            self.audit,
            locks=self.locks,
            approvals=approval_port,
            event_bus=self.events,
            database=self.database,
        )
        self.scheduler = TaskScheduler(
            self.tasks,
            self.locks,
            audit=self.audit,
            event_bus=self.events,
            max_concurrent=self.config.tasks.max_concurrent,
            poll_interval_seconds=self.config.tasks.scheduler_poll_interval_seconds,
            lock_timeout_seconds=self.config.tasks.lock_acquire_timeout_seconds,
        )

        # 8. crash recovery, before anything is dispatched
        self._recovery = recover_interrupted_work(
            self.database,
            self.tasks,
            self.locks,
            self.instance_id,
            audit=self.audit,
            event_bus=self.events,
        )

        # 8b. conversation (Phase 1). The provider is constructed even when
        # Ollama is unreachable, so the Conversation screen can say why rather
        # than the feature simply being absent (ADR-0010).
        self.models = ModelRouter(self.config)
        self.history = ConversationStore(self.database, self.audit)
        self.personality = PersonalityStore(self.database, self.audit)
        self.personality.ensure_default()
        self.conversation = self._build_conversation_engine()

        # 9. Phase 0 tools, runners and bootstrap grants
        self.registry.register(SystemHealthTool(self.config, self.paths))
        self.scheduler.register_runner(HealthCheckRunner(self.invoker))
        self._seed_bootstrap_grants()

        # 10. workers, then the scheduler
        self.workers = WorkerSupervisor(self.events)
        interval = self.config.llm.ollama.health_check_interval_seconds
        if interval > 0:
            self.workers.add(
                PeriodicWorker(
                    "health",
                    interval_seconds=interval,
                    action=self.refresh_health,
                    event_bus=self.events,
                )
            )
        self.workers.start_all()
        self.scheduler.start()

        self._started = True
        self.audit.record(
            AuditCategory.LIFECYCLE,
            f"started {APP_VERSION} (instance {self.instance_id})",
            parameters={
                "vault_root": str(self.paths.root),
                "network_mode": self.config.network.mode.value,
                "schema_version": SCHEMA_VERSION,
                "recovery": self._recovery.describe() if self._recovery else None,
            },
        )
        self.events.publish(
            AppStarted(
                source="core",
                instance_id=self.instance_id,
                app_version=APP_VERSION,
                schema_version=SCHEMA_VERSION,
                vault_root=str(self.paths.root),
                network_mode=self.config.network.mode.value,
            )
        )
        return self

    def _build_conversation_engine(self) -> ConversationEngine:
        planner = self.models.resolve(ModelRole.CONVERSATION)
        provider = OllamaChatProvider(
            self.config.llm.ollama.base_url,
            planner.name,
            timeout_seconds=self.config.tasks.step_timeout_seconds,
            require_loopback=self.config.llm.ollama.require_loopback,
            network_mode=self.config.network.mode,
            context_length=planner.context_length,
        )
        return ConversationEngine(
            provider,
            self.invoker,
            history=self.history,
            personality=self.personality,
            registry=self.registry,
            session_id=self.session_id,
        )

    def start_conversation(
        self, title: str = "Conversation", *, private: bool = False
    ) -> Conversation:
        """Begin a conversation. A private one writes nothing (FR-046, AT-014)."""
        return self.history.start(
            title,
            persist=False if private else None,
            model=self.models.resolve(ModelRole.CONVERSATION).name,
        )

    def _seed_bootstrap_grants(self) -> None:
        """Grant the two strictly self-inspecting capabilities on first start.

        ``system.read_health`` and ``system.read_audit_log`` read Jarvis's own
        status and its own audit records. They touch nothing outside the
        application and are classified low risk, which PRD section 11.1 permits
        to carry "always allow".

        These are real, visible, revocable grants written through the normal
        engine, not a bypass: they appear in the Permissions screen and the user
        can revoke them. Without them Phase 0 could not report its own health,
        because no approval interface exists yet (ADR-0010).
        """
        for capability_id in ("system.read_health", "system.read_audit_log"):
            if any(
                grant.is_active() and grant.decision is Decision.ALLOW
                for grant in self.permissions.list_grants(capability_id)
            ):
                continue
            self.permissions.grant(
                capability_id,
                Decision.ALLOW,
                GrantScope.ALWAYS,
                created_by="system_default",
                reason=(
                    "Self-inspection of the application's own status. Low risk, "
                    "reads nothing outside Jarvis, and can be revoked in Permissions."
                ),
            )

    # -- shutdown ----------------------------------------------------------
    def shutdown(self, reason: str = "user requested shutdown") -> None:
        """Reverse of start, and idempotent."""
        if not self._started:
            self._guard.release()
            return
        self._started = False

        self.events.publish(AppStopping(source="core", instance_id=self.instance_id, reason=reason))

        if self.approvals is not None:
            self.approvals.set_interactive(False)
        self.scheduler.stop()
        self.workers.stop_all()
        self.invoker.shutdown(wait=False)

        released = self.locks.release_all_for_instance()
        self.permissions.revoke_session(self.session_id)

        self.audit.record(
            AuditCategory.LIFECYCLE,
            f"stopped: {reason}",
            parameters={"released_locks": list(released)},
        )

        close_instance(self.database, self.instance_id)
        self.database.checkpoint()
        self.database.close()
        self._guard.release()

    def __enter__(self) -> "JarvisCore":
        return self.start()

    def __exit__(self, *_exc: object) -> None:
        self.shutdown("context exit")

    # -- emergency stop (PRD 11.3) ----------------------------------------
    def emergency_stop(self, origin: str = "api") -> EmergencyStopReport:
        """Stop all automation without stopping the application."""
        self.events.publish(EmergencyStopRequested(source="core", origin=origin))  # type: ignore[arg-type]

        cancelled = self.scheduler.emergency_stop()
        released = self.locks.release_all_for_instance()
        stopped_workers = self.workers.stop_all(timeout_seconds=2.0)
        # A request still on screen would otherwise authorise work into a
        # runtime that has just been told to stop.
        denied = self.approvals.deny_all("emergency stop") if self.approvals else 0

        report = EmergencyStopReport(
            cancelled_task_ids=cancelled,
            released_locks=released,
            stopped_workers=stopped_workers,
            denied_approvals=denied,
        )
        self.audit.record(
            AuditCategory.SECURITY,
            f"emergency stop from {origin}: {report.describe()}",
            actor="user",
            parameters={
                "cancelled_tasks": list(cancelled),
                "released_locks": list(released),
                "stopped_workers": list(stopped_workers),
            },
        )
        self.events.publish(
            EmergencyStopCompleted(
                source="core",
                cancelled_task_ids=cancelled,
                released_locks=released,
                stopped_workers=stopped_workers,
            )
        )
        return report

    # -- configuration -----------------------------------------------------
    def set_setting(self, key_path: str, value: Any, actor: str = "user") -> AppConfig:
        """Change a setting, persist the override and announce it."""
        previous = self._config_store.effective_value(key_path)
        self.config = self._config_store.set(key_path, value)

        self.audit.record(
            AuditCategory.CONFIG,
            f"setting '{key_path}' changed",
            actor=actor,
            parameters={"key_path": key_path, "previous": previous, "current": value},
        )
        self.events.publish(
            ConfigChanged(source="core", key_path=key_path, previous=previous, current=value)
        )
        if key_path == "network.mode":
            self.events.publish(
                NetworkModeChanged(source="core", previous=str(previous), current=str(value))
            )
        return self.config

    def set_network_mode(self, mode: NetworkMode, actor: str = "user") -> AppConfig:
        return self.set_setting("network.mode", mode.value, actor=actor)

    @property
    def config_store(self) -> ConfigStore:
        return self._config_store

    # -- health ------------------------------------------------------------
    def refresh_health(self) -> OllamaHealth:
        """Check the local model runtime. Runs on a worker thread."""
        checker = OllamaHealthChecker(
            self.config.llm.ollama.base_url,
            timeout_seconds=self.config.llm.ollama.request_timeout_seconds,
            require_loopback=self.config.llm.ollama.require_loopback,
            network_mode=self.config.network.mode,
        )
        health = checker.check()
        self._last_health = health

        self.audit.record(
            AuditCategory.HEALTH,
            f"ollama health: {health.describe()}",
            result="reachable" if health.reachable else "unreachable",
            error=health.error,
        )
        self.events.publish(
            HealthChecked(
                source="core",
                component="ollama",
                healthy=health.reachable,
                detail=health.describe(),
                skipped_reason=health.skipped_reason,
            )
        )
        return health

    @property
    def last_health(self) -> OllamaHealth | None:
        return self._last_health

    # -- convenience -------------------------------------------------------
    def run_health_check_task(self) -> str:
        """Queue a health check through the task machinery. Returns the task id."""
        task = self.tasks.create(
            name="System health check",
            goal="Report the status of the local model runtime and the data vault.",
            runner_id=HealthCheckRunner.runner_id,
            payload={"session_id": self.session_id},
        )
        self.scheduler.submit(task)
        return task.task_id

    def invoke(self, call: ToolCall) -> Any:
        return self.invoker.invoke(call)

    @property
    def started(self) -> bool:
        return self._started

    @property
    def recovery(self) -> RecoveryReport | None:
        return self._recovery

    def status(self) -> CoreStatus:
        active = (
            len(self.tasks.list([TaskState.QUEUED, TaskState.RUNNING, TaskState.WAITING]))
            if self._started
            else 0
        )
        return CoreStatus(
            running=self._started,
            instance_id=self.instance_id,
            app_version=APP_VERSION,
            schema_version=SCHEMA_VERSION,
            network_mode=self.config.network.mode.value if self._started else "unknown",
            vault_root=str(self.paths.root),
            registered_tools=self.registry.tool_ids() if self._started else (),
            active_tasks=active,
            held_locks=(
                tuple(record.lock_name for record in self.locks.held()) if self._started else ()
            ),
            workers=self.workers.running_names() if self._started else (),
            last_health=self._last_health,
            recovery=self._recovery,
        )


def default_log_path(paths: VaultPaths) -> Path:
    return paths.app_log_path
