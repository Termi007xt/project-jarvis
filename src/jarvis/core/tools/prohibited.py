"""The prohibited-capability guard (ADR-0003).

Defence in depth, layer 2 of 3:

1. no generic execution primitive is implemented anywhere in the runtime;
2. **this module** — the registry refuses to register anything that looks like
   one, by exact identity and by name pattern;
3. ``tests/security/test_no_shell.py`` scans ``src/`` for process-creation and
   dynamic-evaluation primitives and fails the build.

Layer 2 exists so that a future contributor cannot introduce ``run_shell_v2``
by accident. It is not the real guarantee — layers 1 and 3 are.
"""

from __future__ import annotations

import re

__all__ = [
    "PROHIBITED_TOOL_IDS",
    "PROHIBITED_NAME_PATTERNS",
    "ProhibitedToolError",
    "check_tool_id",
    "assert_tool_id_permitted",
    "why_prohibited",
]


class ProhibitedToolError(Exception):
    """Registration was refused because the tool is prohibited by policy."""


#: Verbatim from PRD section 13.3 "Prohibited broad tools", plus the shell and
#: interpreter names the PRD forbids in section 6.1 and section 11.1.
PROHIBITED_TOOL_IDS: frozenset[str] = frozenset(
    {
        # PRD 13.3
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
        # PRD 6.1 and 11.1
        "run_cmd",
        "run_command",
        "run_terminal",
        "run_wsl",
        "run_bash",
        "run_python",
        "run_script",
        "eval_expression",
        "exec_code",
        "spawn_process",
        "registry_write",
        "registry_edit",
        "elevate_permanently",
        "disable_antivirus",
        "disable_firewall",
        "bypass_captcha",
        "read_password",
        "read_private_key",
        "extract_cookies",
        "extract_credentials",
    }
)


#: Substring patterns matched against the whole tool id (dots included) and
#: against each dot-separated segment.
PROHIBITED_NAME_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("generic shell execution", re.compile(r"shell", re.IGNORECASE)),
    ("PowerShell execution", re.compile(r"power_?shell", re.IGNORECASE)),
    ("Command Prompt execution", re.compile(r"(^|[._])cmd([._]|$)", re.IGNORECASE)),
    ("terminal execution", re.compile(r"terminal", re.IGNORECASE)),
    ("WSL execution", re.compile(r"(^|[._])wsl([._]|$)", re.IGNORECASE)),
    ("bash execution", re.compile(r"(^|[._])(ba|z|k)?sh([._]|$)", re.IGNORECASE)),
    ("arbitrary code execution", re.compile(r"(^|[._])exec([._]|$)|execute_code", re.IGNORECASE)),
    ("dynamic evaluation", re.compile(r"(^|[._])eval([._]|$)", re.IGNORECASE)),
    ("subprocess creation", re.compile(r"subprocess|spawn_process|create_process", re.IGNORECASE)),
    ("arbitrary script execution", re.compile(r"run_script|execute_script", re.IGNORECASE)),
    ("unscoped or unbounded action", re.compile(r"arbitrary|unrestricted|any_file|all_files", re.IGNORECASE)),
    ("registry modification", re.compile(r"registry_(write|edit|set|delete)", re.IGNORECASE)),
    ("blanket approval", re.compile(r"approve_all|allow_all|auto_approve", re.IGNORECASE)),
    ("credential access", re.compile(r"(password|private_key|credential|cookie)s?_(read|get|extract|dump)", re.IGNORECASE)),
    ("security control tampering", re.compile(r"disable_(antivirus|firewall|smartscreen|uac|defender)", re.IGNORECASE)),
    ("anti-bot evasion", re.compile(r"(bypass|solve)_captcha", re.IGNORECASE)),
    ("continuous capture", re.compile(r"capture_screen_continuously|continuous_capture", re.IGNORECASE)),
)


def why_prohibited(tool_id: str) -> str | None:
    """Return the reason a tool id is prohibited, or ``None`` if it is allowed."""
    normalised = tool_id.strip().lower()
    if not normalised:
        return "empty tool id"

    bare = normalised.rsplit(".", 1)[-1]
    if normalised in PROHIBITED_TOOL_IDS or bare in PROHIBITED_TOOL_IDS:
        return "tool id appears on the prohibited-tool list (PRD section 13.3)"

    for reason, pattern in PROHIBITED_NAME_PATTERNS:
        if pattern.search(normalised):
            return f"tool id matches the prohibited pattern for {reason}"
    return None


def check_tool_id(tool_id: str) -> bool:
    """``True`` if the tool id may be registered."""
    return why_prohibited(tool_id) is None


def assert_tool_id_permitted(tool_id: str) -> None:
    reason = why_prohibited(tool_id)
    if reason is not None:
        raise ProhibitedToolError(
            f"refusing to register '{tool_id}': {reason}. "
            "Project Jarvis has no generic execution capability by design "
            "(ADR-0003). Add a narrow, typed tool for the specific action instead."
        )
