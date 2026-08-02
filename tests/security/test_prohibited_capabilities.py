"""The prohibited-capability guard (ADR-0003, PRD sections 11.1 and 13.3)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from jarvis.core.permissions.catalogue import CAPABILITIES, capabilities_by_risk
from jarvis.core.permissions.models import (
    Decision,
    GrantScope,
    PermissionRequest,
    ProhibitedCapabilityError,
    RiskLevel,
)
from jarvis.core.tools.contract import RetryPolicy, ToolExecution, ToolSpec, Verification
from jarvis.core.tools.prohibited import (
    PROHIBITED_TOOL_IDS,
    ProhibitedToolError,
    check_tool_id,
    why_prohibited,
)
from jarvis.core.tools.registry import ToolRegistrationError

#: Every prohibited broad tool named in PRD section 13.3.
PRD_PROHIBITED_TOOLS = [
    "run_shell",
    "execute_code",
    "run_powershell",
    "delete_anything",
    "control_computer",
    "approve_all",
    "search_entire_computer_without_scope",
    "read_all_files",
    "upload_any_file",
    "change_any_windows_setting",
    "monitor_all_notifications",
    "capture_screen_continuously",
    "restore_everything",
]


class _Params(BaseModel):
    pass


class _Result(BaseModel):
    ok: bool = True


def _tool(tool_id: str, capability: str = "system.read_health"):
    class _T:
        spec = ToolSpec(
            tool_id=tool_id,
            version="1.0.0",
            description="test",
            input_model=_Params,
            output_model=_Result,
            risk=RiskLevel.LOW,
            required_capabilities=(capability,),
            changes_state=False,
            verification="none",
            failure_codes=("failed",),
            retry_policy=RetryPolicy(max_attempts=1),
        )

        def run(self, context, parameters):
            return ToolExecution(output=_Result(), verification=Verification.NOT_APPLICABLE)

    return _T()


@pytest.mark.parametrize("tool_id", PRD_PROHIBITED_TOOLS)
def test_every_prd_prohibited_tool_is_rejected(tool_id: str) -> None:
    assert not check_tool_id(tool_id)
    assert tool_id in PROHIBITED_TOOL_IDS
    assert why_prohibited(tool_id) is not None


@pytest.mark.parametrize(
    "tool_id",
    [
        "system.run_shell",
        "shell.run",
        "windows.powershell_invoke",
        "os.cmd",
        "linux.wsl_run",
        "code.exec",
        "script.eval",
        "process.subprocess_run",
        "files.delete_anything",
        "settings.registry_write",
        "approvals.approve_all",
        "screen.capture_screen_continuously",
        "creds.password_read",
        "security.disable_antivirus",
        "web.bypass_captcha",
        "fs.read_any_file",
    ],
)
def test_prohibited_name_patterns_are_rejected(tool_id: str) -> None:
    """A future contributor cannot smuggle one in under a new name."""
    assert not check_tool_id(tool_id), f"'{tool_id}' should have been rejected"


@pytest.mark.parametrize(
    "tool_id",
    [
        "system.health",
        "app.open_approved",
        "fs.read_text_file",
        "browser.click_selector",
        "window.list_windows",
        "media.play_pause",
        "notify.show_toast",
        "clipboard.get_text",
    ],
)
def test_legitimate_narrow_tool_names_are_allowed(tool_id: str) -> None:
    """The guard must not block the narrow tools the product actually needs."""
    assert check_tool_id(tool_id), f"'{tool_id}' should be allowed: {why_prohibited(tool_id)}"


def test_registry_refuses_a_prohibited_tool(registry) -> None:
    with pytest.raises(ProhibitedToolError, match="no generic execution capability"):
        registry.register(_tool("system.run_shell"))
    assert len(registry) == 0


def test_registry_refuses_a_tool_requiring_a_prohibited_capability(registry) -> None:
    with pytest.raises(ToolRegistrationError, match="prohibited capabilities"):
        registry.register(_tool("system.sneaky", capability="prohibited.generic_shell"))


def test_registry_refuses_a_tool_requiring_an_unknown_capability(registry) -> None:
    with pytest.raises(ToolRegistrationError, match="absent from the"):
        registry.register(_tool("system.mystery", capability="not.a.real.capability"))


def test_registry_refuses_a_tool_that_understates_its_risk(registry) -> None:
    with pytest.raises(ToolRegistrationError, match="declares low risk"):
        registry.register(_tool("fs.sneaky_delete", capability="fs.delete_or_overwrite"))


def test_toolspec_cannot_declare_prohibited_risk() -> None:
    with pytest.raises(ValueError, match="prohibited risk"):
        ToolSpec(
            tool_id="system.bad",
            version="1.0.0",
            description="test",
            input_model=_Params,
            output_model=_Result,
            risk=RiskLevel.PROHIBITED,
            required_capabilities=("system.read_health",),
            changes_state=False,
            verification="none",
            failure_codes=("failed",),
        )


def test_prohibited_capability_is_always_denied_regardless_of_grants(permissions) -> None:
    """No grant, setting or approval can reach past the prohibited check."""
    evaluation = permissions.evaluate(
        PermissionRequest(capability_id="prohibited.generic_shell")
    )
    assert evaluation.decision is Decision.DENY
    assert not evaluation.requires_user_approval
    assert "prohibited" in evaluation.reason


def test_prohibited_capability_cannot_be_granted(permissions) -> None:
    with pytest.raises(ProhibitedCapabilityError):
        permissions.grant(
            "prohibited.generic_shell", Decision.ALLOW, GrantScope.ONCE, created_by="user"
        )
    assert permissions.list_grants("prohibited.generic_shell") == []


def test_unknown_capability_is_denied_not_implicitly_allowed(permissions) -> None:
    evaluation = permissions.evaluate(PermissionRequest(capability_id="made.up.capability"))
    assert evaluation.decision is Decision.DENY
    assert "unknown capability" in evaluation.reason


def test_catalogue_covers_every_prd_prohibited_class() -> None:
    """PRD section 11.1's prohibited list is represented in the catalogue."""
    prohibited = {c.capability_id for c in capabilities_by_risk(RiskLevel.PROHIBITED)}
    for expected in (
        "prohibited.generic_shell",
        "prohibited.arbitrary_script",
        "prohibited.read_secrets",
        "prohibited.disable_security",
        "prohibited.extract_credentials",
        "prohibited.captcha_bypass",
        "prohibited.stealth_recording",
        "prohibited.surveil_other_users",
        "prohibited.permanent_admin",
        "prohibited.autonomous_finance",
        "prohibited.autonomous_legal",
        "prohibited.hidden_remote_control",
    ):
        assert expected in prohibited


def test_no_tool_may_ever_be_registered_for_a_prohibited_capability(core) -> None:
    """In a fully wired runtime, nothing is registered against a prohibited class."""
    prohibited = {
        c.capability_id for c in CAPABILITIES.values() if c.risk is RiskLevel.PROHIBITED
    }
    for spec in core.registry.specs():
        assert not (set(spec.required_capabilities) & prohibited)
