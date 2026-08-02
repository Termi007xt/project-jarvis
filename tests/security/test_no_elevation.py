"""Non-administrator operation (PRD FR-003, NFR-020, ADR-0009).

Phase 0 must run entirely as a normal user. Nothing may request elevation, and
nothing may declare an elevated execution level in packaging metadata.
"""

from __future__ import annotations

import ast
from pathlib import Path

#: Win32 and shell entry points that trigger a UAC prompt.
ELEVATION_CALLS: frozenset[str] = frozenset(
    {
        "ShellExecuteW",
        "ShellExecuteA",
        "ShellExecuteExW",
        "ShellExecuteExA",
        "IsUserAnAdmin",
        "AdjustTokenPrivileges",
        "OpenProcessToken",
        "CreateProcessAsUserW",
        "CreateProcessWithLogonW",
        "LogonUserW",
    }
)

#: Strings that would request elevation via a manifest or a runas verb.
ELEVATION_STRINGS: tuple[str, ...] = (
    "requireAdministrator",
    "highestAvailable",
    "asAdmin",
    "runas",
)


def _relative(path: Path) -> str:
    parts = path.parts
    return "/".join(parts[parts.index("jarvis") :])


def test_no_module_requests_elevation(source_files: list[Path]) -> None:
    offenders: list[str] = []
    for path in source_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ELEVATION_CALLS:
                    offenders.append(f"{_relative(path)} line {node.lineno}: {node.func.attr}")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for needle in ELEVATION_STRINGS:
                    if node.value.strip() == needle:
                        offenders.append(
                            f"{_relative(path)} line {node.lineno}: literal '{needle}'"
                        )

    assert not offenders, (
        "Jarvis runs without administrator rights (PRD FR-003). Elevation, when it "
        "is eventually needed, goes through a separate scoped helper (ADR-0009).\n  "
        + "\n  ".join(offenders)
    )


def test_no_manifest_declares_an_elevated_execution_level(repo_root: Path) -> None:
    """Any packaging manifest must be asInvoker."""
    offenders: list[str] = []
    for pattern in ("**/*.manifest", "**/*.rc", "packaging/**/*.spec", "packaging/**/*.xml"):
        for path in repo_root.glob(pattern):
            if ".venv" in path.parts or "tools" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in ("requireAdministrator", "highestAvailable"):
                if needle in text:
                    offenders.append(f"{path.relative_to(repo_root)}: {needle}")
    assert not offenders, f"packaging must request asInvoker only: {offenders}"


def test_permanent_administrator_operation_is_a_prohibited_capability() -> None:
    from jarvis.core.permissions.catalogue import CAPABILITIES
    from jarvis.core.permissions.models import RiskLevel

    capability = CAPABILITIES["prohibited.permanent_admin"]
    assert capability.risk is RiskLevel.PROHIBITED


def test_elevation_is_high_risk_and_not_implemented_in_phase_0(core) -> None:
    from jarvis.core.permissions.catalogue import CAPABILITIES
    from jarvis.core.permissions.models import RiskLevel

    assert CAPABILITIES["system.elevate"].risk is RiskLevel.HIGH
    # No Phase 0 tool requires it.
    for spec in core.registry.specs():
        assert "system.elevate" not in spec.required_capabilities
