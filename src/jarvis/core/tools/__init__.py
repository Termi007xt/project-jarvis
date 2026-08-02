"""Tool contract, allow-list registry, prohibited guard and the invoker.

This package holds the *machinery*. Concrete tool implementations live in
``jarvis.toolbox`` (L3), because a tool implementation may need capability
modules that L2 must not import.
"""

from __future__ import annotations

from jarvis.core.tools.contract import (
    RetryPolicy,
    RollbackSpec,
    Tool,
    ToolContext,
    ToolExecution,
    ToolFailure,
    ToolOutcome,
    ToolResult,
    ToolSpec,
    Verification,
)
from jarvis.core.tools.invoker import ToolCall, ToolInvoker
from jarvis.core.tools.ports import (
    ApprovalOutcome,
    ApprovalPort,
    ApprovalRequest,
    AutoApprovalPort,
    DenyingApprovalPort,
    LockLease,
    LockPort,
)
from jarvis.core.tools.prohibited import (
    PROHIBITED_NAME_PATTERNS,
    PROHIBITED_TOOL_IDS,
    ProhibitedToolError,
    assert_tool_id_permitted,
    check_tool_id,
    why_prohibited,
)
from jarvis.core.tools.registry import ToolRegistrationError, ToolRegistry

__all__ = [
    "ApprovalOutcome",
    "ApprovalPort",
    "ApprovalRequest",
    "AutoApprovalPort",
    "DenyingApprovalPort",
    "LockLease",
    "LockPort",
    "PROHIBITED_NAME_PATTERNS",
    "PROHIBITED_TOOL_IDS",
    "ProhibitedToolError",
    "RetryPolicy",
    "RollbackSpec",
    "Tool",
    "ToolCall",
    "ToolContext",
    "ToolExecution",
    "ToolFailure",
    "ToolInvoker",
    "ToolOutcome",
    "ToolRegistrationError",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
    "Verification",
    "assert_tool_id_permitted",
    "check_tool_id",
    "why_prohibited",
]
