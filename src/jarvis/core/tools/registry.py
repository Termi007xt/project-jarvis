"""Tool registry — the allow-list (ARCHITECTURE.md section 6.5).

Registration is the *only* way a tool becomes callable, and the registry is the
only thing that can resolve a tool name to an implementation. The planner emits
a name and a parameter object; it never holds a callable.
"""

from __future__ import annotations

import threading

from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import ProhibitedCapabilityBlocked, ToolRegistered
from jarvis.core.permissions.catalogue import CAPABILITIES
from jarvis.core.permissions.models import RiskLevel
from jarvis.core.tools.contract import Tool, ToolSpec
from jarvis.core.tools.prohibited import ProhibitedToolError, assert_tool_id_permitted

__all__ = ["ToolRegistry", "ToolRegistrationError"]


class ToolRegistrationError(Exception):
    """A tool could not be registered."""


class ToolRegistry:
    """Holds every tool the runtime may call. Nothing else can."""

    def __init__(
        self,
        audit: AuditLog | None = None,
        event_bus: EventBus | None = None,
        catalogue: dict[str, object] | None = None,
    ) -> None:
        self._audit = audit
        self._events = event_bus
        self._catalogue = catalogue if catalogue is not None else CAPABILITIES
        self._tools: dict[str, Tool] = {}
        self._lock = threading.RLock()

    def register(self, tool: Tool) -> ToolSpec:
        spec = tool.spec

        # Layer 2 of the prohibited-capability guard (ADR-0003).
        try:
            assert_tool_id_permitted(spec.tool_id)
        except ProhibitedToolError as exc:
            if self._audit is not None:
                self._audit.record(
                    AuditCategory.SECURITY,
                    f"refused to register prohibited tool '{spec.tool_id}'",
                    actor="system",
                    tool_id=spec.tool_id,
                    error=str(exc),
                )
            if self._events is not None:
                self._events.publish(
                    ProhibitedCapabilityBlocked(
                        source="tool_registry",
                        identifier=spec.tool_id,
                        origin="registration",
                        detail=str(exc),
                    )
                )
            raise

        if spec.risk is RiskLevel.PROHIBITED:  # pragma: no cover - ToolSpec rejects this first
            raise ToolRegistrationError(
                f"tool '{spec.tool_id}' declares prohibited risk and cannot exist"
            )

        unknown = [
            capability_id
            for capability_id in spec.required_capabilities
            if capability_id not in self._catalogue
        ]
        if unknown:
            raise ToolRegistrationError(
                f"tool '{spec.tool_id}' requires capabilities absent from the "
                f"catalogue: {sorted(unknown)}"
            )

        prohibited_capabilities = [
            capability_id
            for capability_id in spec.required_capabilities
            if getattr(self._catalogue[capability_id], "risk", None) is RiskLevel.PROHIBITED
        ]
        if prohibited_capabilities:
            raise ToolRegistrationError(
                f"tool '{spec.tool_id}' requires prohibited capabilities: "
                f"{sorted(prohibited_capabilities)}"
            )

        # A tool must not understate its own risk relative to what it needs.
        declared_risks = [
            getattr(self._catalogue[capability_id], "risk") for capability_id in spec.required_capabilities
        ]
        order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
        highest = max(declared_risks, key=lambda risk: order[risk])
        if order[spec.risk] < order[highest]:
            raise ToolRegistrationError(
                f"tool '{spec.tool_id}' declares {spec.risk.value} risk but requires a "
                f"{highest.value}-risk capability"
            )

        with self._lock:
            if spec.tool_id in self._tools:
                raise ToolRegistrationError(f"tool '{spec.tool_id}' is already registered")
            self._tools[spec.tool_id] = tool

        if self._audit is not None:
            self._audit.record(
                AuditCategory.LIFECYCLE,
                f"registered tool {spec.tool_id} v{spec.version}",
                tool_id=spec.tool_id,
                risk=spec.risk.value,
                parameters={
                    "capabilities": list(spec.required_capabilities),
                    "locks": list(spec.resource_locks),
                    "changes_state": spec.changes_state,
                },
            )
        if self._events is not None:
            self._events.publish(
                ToolRegistered(
                    source="tool_registry",
                    tool_id=spec.tool_id,
                    version=spec.version,
                    risk=spec.risk.value,
                    changes_state=spec.changes_state,
                )
            )
        return spec

    def get(self, tool_id: str) -> Tool | None:
        with self._lock:
            return self._tools.get(tool_id)

    def spec(self, tool_id: str) -> ToolSpec | None:
        tool = self.get(tool_id)
        return tool.spec if tool is not None else None

    def tool_ids(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._tools))

    def specs(self) -> tuple[ToolSpec, ...]:
        with self._lock:
            return tuple(tool.spec for tool in self._tools.values())

    def describe_for_model(self) -> list[dict[str, object]]:
        """JSON schemas the planner is offered. Nothing outside this list exists."""
        return [spec.json_schema_for_model() for spec in sorted(self.specs(), key=lambda s: s.tool_id)]

    def __contains__(self, tool_id: object) -> bool:
        return isinstance(tool_id, str) and self.get(tool_id) is not None

    def __len__(self) -> int:
        with self._lock:
            return len(self._tools)
