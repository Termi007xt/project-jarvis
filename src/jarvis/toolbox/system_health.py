"""The one tool Phase 0 registers, and the task runner that uses it.

``system.health`` is read-only: it opens no file for writing, launches nothing
and changes no state. It exists so the whole six-step invoker pipeline —
allow-list, schema, permission, locks, approval, execute — has something real
to carry end to end, and so the Ollama health check reaches the GUI through the
same path every future capability will use.
"""

from __future__ import annotations

import platform
import shutil
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from jarvis.config.paths import VaultPaths
from jarvis.config.schema import AppConfig
from jarvis.core.permissions.models import RiskLevel
from jarvis.core.tools.contract import (
    RetryPolicy,
    ToolContext,
    ToolExecution,
    ToolFailure,
    ToolSpec,
    Verification,
)
from jarvis.llm.ollama.health import OllamaHealthChecker
from jarvis.tasks.runner import TaskOutcome, TaskRunContext
from jarvis.tasks.states import TaskState

__all__ = ["SystemHealthTool", "HealthCheckRunner", "HealthInput", "HealthOutput"]


class HealthInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    include_models: bool = Field(
        default=True, description="Also list the models installed in the local runtime."
    )


class HealthOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    ollama_reachable: bool
    ollama_version: str | None = None
    ollama_error: str | None = None
    ollama_skipped_reason: str | None = None
    installed_models: tuple[str, ...] = ()
    configured_models: tuple[str, ...] = ()
    missing_models: tuple[str, ...] = ()
    network_mode: str
    vault_root: str
    vault_free_bytes: int
    schema_version: int
    python_version: str
    summary: str


class SystemHealthTool:
    """Read-only status of the local model runtime and the data vault."""

    spec = ToolSpec(
        tool_id="system.health",
        version="1.0.0",
        description="Report the status of the local model runtime and the data vault.",
        input_model=HealthInput,
        output_model=HealthOutput,
        risk=RiskLevel.LOW,
        required_capabilities=("system.read_health",),
        resource_locks=(),
        timeout_seconds=30.0,
        retry_policy=RetryPolicy(max_attempts=1),
        changes_state=False,
        verification="Read-only: reports what it observed and nothing more.",
        redaction_keys=(),
        failure_codes=("vault_unreadable", "health_check_failed"),
        reversible=True,
    )

    def __init__(self, config: AppConfig, paths: VaultPaths) -> None:
        self._config = config
        self._paths = paths

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        # The invoker has already validated against spec.input_model.
        assert isinstance(parameters, HealthInput)
        try:
            usage = shutil.disk_usage(self._paths.root)
        except OSError as exc:
            raise ToolFailure("vault_unreadable", f"could not read the data vault: {exc}") from exc

        checker = OllamaHealthChecker(
            self._config.llm.ollama.base_url,
            timeout_seconds=self._config.llm.ollama.request_timeout_seconds,
            require_loopback=self._config.llm.ollama.require_loopback,
            network_mode=self._config.network.mode,
        )
        health = checker.check()

        configured = tuple(
            sorted(
                {
                    self._config.models.planner.name,
                    self._config.models.vision.name,
                    self._config.models.embeddings.name,
                }
            )
        )
        installed = health.models if parameters.include_models else ()
        # Ollama reports names like "qwen3:8b"; a configured name matches when it
        # is an exact or tag-prefix match.
        missing = (
            tuple(
                name
                for name in configured
                if not any(
                    installed_name == name or installed_name.startswith(f"{name}:")
                    for installed_name in installed
                )
            )
            if health.reachable and parameters.include_models
            else ()
        )

        output = HealthOutput(
            ollama_reachable=health.reachable,
            ollama_version=health.version,
            ollama_error=health.error,
            ollama_skipped_reason=health.skipped_reason,
            installed_models=installed,
            configured_models=configured,
            missing_models=missing,
            network_mode=self._config.network.mode.value,
            vault_root=str(self._paths.root),
            vault_free_bytes=usage.free,
            schema_version=self._config.schema_version,
            python_version=platform.python_version(),
            summary=health.describe(),
        )
        return ToolExecution(
            output=output,
            # Nothing changed, so there is nothing to verify (PRD FR-048).
            verification=Verification.NOT_APPLICABLE,
            message=health.describe(),
        )


class HealthCheckRunner:
    """Task runner that performs a health check through the tool invoker.

    Deliberately routed through the invoker rather than calling the tool
    directly: it proves the pipeline works, and it means the health check is
    permission-checked and audited exactly like everything else.
    """

    runner_id = "system.health_check"

    def __init__(self, invoker: object) -> None:
        self._invoker = invoker

    def run(self, context: TaskRunContext) -> TaskOutcome:
        from jarvis.core.tools.invoker import ToolCall  # local import keeps L3 tidy

        context.checkpoint("started", {"stage": "beginning health check"})
        if context.should_stop():
            return TaskOutcome(
                state=TaskState.BLOCKED,
                summary="stopped before the health check ran",
                blocked_reason="stop requested",
            )

        result = self._invoker.invoke(  # type: ignore[attr-defined]
            ToolCall(
                tool_id="system.health",
                parameters={"include_models": True},
                task_id=context.task.task_id,
                session_id=context.task.payload.get("session_id"),
                origin="system",
            ),
            cancel_event=context.cancel_event,
        )
        context.checkpoint("tool_returned", {"outcome": result.outcome.value})

        if not result.succeeded:
            return TaskOutcome(
                state=TaskState.FAILED,
                summary=result.message or "the health check could not be completed",
                failure_code=result.failure_code or "health_check_failed",
                retryable=False,
            )

        payload = result.output or {}
        context.add_evidence(
            "tool_result",
            payload.get("summary", "health check completed"),
            detail={
                "ollama_reachable": payload.get("ollama_reachable"),
                "network_mode": payload.get("network_mode"),
                "missing_models": payload.get("missing_models"),
            },
        )
        return TaskOutcome(
            state=TaskState.SUCCEEDED,
            summary=payload.get("summary", "health check completed"),
        )


def vault_free_bytes(root: Path) -> int:
    """Free space on the volume holding the vault (PRD NFR-006)."""
    return shutil.disk_usage(root).free
