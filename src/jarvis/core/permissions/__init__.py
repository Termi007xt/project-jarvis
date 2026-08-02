"""Permission model, capability catalogue and evaluation engine."""

from __future__ import annotations

from jarvis.core.permissions.catalogue import (
    CAPABILITIES,
    capabilities_by_risk,
    capability,
    capability_ids,
)
from jarvis.core.permissions.engine import DefaultPolicy, PermissionEngine
from jarvis.core.permissions.models import (
    Capability,
    Decision,
    GrantScope,
    PermissionError,
    PermissionEvaluation,
    PermissionGrant,
    PermissionRequest,
    ProhibitedCapabilityError,
    RiskLevel,
)

__all__ = [
    "CAPABILITIES",
    "Capability",
    "Decision",
    "DefaultPolicy",
    "GrantScope",
    "PermissionEngine",
    "PermissionError",
    "PermissionEvaluation",
    "PermissionGrant",
    "PermissionRequest",
    "ProhibitedCapabilityError",
    "RiskLevel",
    "capabilities_by_risk",
    "capability",
    "capability_ids",
]
