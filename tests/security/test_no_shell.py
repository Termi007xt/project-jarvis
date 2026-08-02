"""The load-bearing security test (ADR-0003).

Phase 0 exit criterion: *no generic shell exists anywhere in the runtime*.

Detection is AST-based, not textual, so a docstring or a denylist pattern
mentioning "subprocess" does not trip it, while an actual call does. If this
test fails, the fix is to delete the offending call — not to widen the
allow-list. Widening it requires an ADR naming the exact call site and its
justification (ARCHITECTURE.md section 14).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: Modules that exist to start processes or evaluate code.
FORBIDDEN_MODULES: frozenset[str] = frozenset(
    {
        "subprocess",
        "commands",
        "popen2",
        "pty",
        "multiprocessing",
        "asyncio.subprocess",
    }
)

#: ``os`` functions that create a process or replace the current image.
FORBIDDEN_OS_FUNCTIONS: frozenset[str] = frozenset(
    {
        "system",
        "popen",
        "execv",
        "execve",
        "execvp",
        "execvpe",
        "execl",
        "execle",
        "execlp",
        "execlpe",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "startfile",
        "forkpty",
        "fork",
    }
)

#: Builtins that turn data into executable code.
FORBIDDEN_BUILTINS: frozenset[str] = frozenset({"eval", "exec", "compile"})

#: Win32 entry points that launch a process.
FORBIDDEN_WIN32_CALLS: frozenset[str] = frozenset(
    {
        "ShellExecuteW",
        "ShellExecuteA",
        "ShellExecuteExW",
        "ShellExecuteExA",
        "CreateProcessW",
        "CreateProcessA",
        "WinExec",
        "system",
    }
)

#: Explicitly allowed exceptions. Every entry must cite an ADR.
#:
#: There is exactly **one**, and ``test_the_allow_list_holds_at_most_one_entry``
#: keeps it that way, so a second exception cannot be added quietly alongside
#: the first. ADR-0029 authorises this call site under nine constraints and is
#: explicit that a second site is a new ADR, never another entry here.
ALLOW_LIST: dict[tuple[str, str], str] = {
    ("jarvis/toolbox/launch.py", "import subprocess"): (
        "ADR-0029: the single authorised process-creation call site, used to "
        "launch an application the user has already approved. List argv only, "
        "shell=False, executable chosen from the catalogue and never from model "
        "output, interpreters refused by basename, arguments typed per entry, "
        "environment inherited, always through ToolInvoker, launch verified."
    ),
}


def _relative(path: Path) -> str:
    parts = path.parts
    index = parts.index("jarvis")
    return "/".join(parts[index:])


def _findings(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []

    for node in ast.walk(tree):
        # import subprocess / import multiprocessing
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if alias.name in FORBIDDEN_MODULES or root in FORBIDDEN_MODULES:
                    found.append(f"line {node.lineno}: import {alias.name}")

        # from subprocess import run
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if module in FORBIDDEN_MODULES or root in FORBIDDEN_MODULES:
                found.append(f"line {node.lineno}: from {module} import ...")

        elif isinstance(node, ast.Call):
            func = node.func

            # eval(...) / exec(...) / compile(...)
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_BUILTINS:
                found.append(f"line {node.lineno}: {func.id}(...)")

            if isinstance(func, ast.Attribute):
                # os.system(...), os.popen(...), os.startfile(...)
                if (
                    isinstance(func.value, ast.Name)
                    and func.value.id == "os"
                    and func.attr in FORBIDDEN_OS_FUNCTIONS
                ):
                    found.append(f"line {node.lineno}: os.{func.attr}(...)")

                # ctypes.windll.shell32.ShellExecuteW(...) and friends
                if func.attr in FORBIDDEN_WIN32_CALLS:
                    found.append(f"line {node.lineno}: ...{func.attr}(...)")

            # shell=True anywhere
            for keyword in node.keywords:
                if (
                    keyword.arg == "shell"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ):
                    found.append(f"line {node.lineno}: shell=True")

    return found


def test_no_process_creation_or_dynamic_evaluation_in_runtime(source_files: list[Path]) -> None:
    """No shipped module may start a process or evaluate generated code."""
    violations: list[str] = []
    for path in source_files:
        module = _relative(path)
        for finding in _findings(path):
            if ALLOW_LIST.get((module, finding.split(":", 1)[1].strip())):
                continue
            violations.append(f"{module}: {finding}")

    assert not violations, (
        "Project Jarvis must contain no generic execution capability (ADR-0003).\n"
        "Found:\n  " + "\n  ".join(violations) + "\n\n"
        "Do not add these to ALLOW_LIST to make this pass. Remove the call, or "
        "raise an ADR that names the call site and its justification."
    )


def test_the_allow_list_holds_at_most_one_entry() -> None:
    """ADR-0029 authorises one call site. A second is a new ADR, not a row here.

    This is what stops "one reviewed exception" eroding into a list, which is
    the failure mode ADR-0029 names in its Negative consequences.
    """
    assert len(ALLOW_LIST) <= 1, (
        "Only one process-creation call site is authorised (ADR-0029). Adding "
        "another requires a new ADR and a re-examination of that one — never a "
        "second entry under its number.\n  " + "\n  ".join(
            f"{module}: {finding}" for module, finding in ALLOW_LIST
        )
    )
    for (module, finding), justification in ALLOW_LIST.items():
        assert "ADR-" in justification, f"{module} ({finding}) cites no ADR"
        assert module == "jarvis/toolbox/launch.py", (
            f"the authorised call site is jarvis/toolbox/launch.py, not {module}"
        )


def test_the_authorised_call_site_still_exists_and_is_the_only_one(
    source_files: list[Path],
) -> None:
    """The allow-list entry must describe reality, not a module that moved."""
    importers = {
        _relative(path)
        for path in source_files
        if any("subprocess" in finding for finding in _findings(path))
    }
    assert importers == {"jarvis/toolbox/launch.py"}, (
        "exactly one module may import subprocess, and it is the one ADR-0029 "
        f"names. Found: {sorted(importers)}"
    )


def test_the_scanner_actually_detects_violations(tmp_path: Path) -> None:
    """A guard on the guard: prove the detector is not vacuously passing."""
    offender = tmp_path / "jarvis" / "bad.py"
    offender.parent.mkdir(parents=True)
    offender.write_text(
        "import os\n"
        "import subprocess\n"
        "def go(cmd):\n"
        "    os.system(cmd)\n"
        "    subprocess.run(cmd, shell=True)\n"
        "    return eval(cmd)\n",
        encoding="utf-8",
    )
    findings = _findings(offender)
    joined = " ".join(findings)
    assert "import subprocess" in joined
    assert "os.system" in joined
    assert "shell=True" in joined
    assert "eval(...)" in joined


def test_scanner_ignores_mentions_in_strings_and_comments(tmp_path: Path) -> None:
    """The denylist module names these primitives in patterns; that must be fine."""
    innocent = tmp_path / "jarvis" / "good.py"
    innocent.parent.mkdir(parents=True)
    innocent.write_text(
        '"""We must never use subprocess, eval or os.system."""\n'
        "PATTERNS = ['shell', 'powershell', 'subprocess', 'eval']\n"
        "# os.system(x) would be forbidden here\n"
        "def safe():\n"
        "    return PATTERNS\n",
        encoding="utf-8",
    )
    assert _findings(innocent) == []


@pytest.mark.parametrize(
    "forbidden",
    ["run_shell", "execute_code", "run_powershell", "control_computer", "approve_all"],
)
def test_prohibited_tool_names_appear_nowhere_as_definitions(
    forbidden: str, source_files: list[Path]
) -> None:
    """No function or class in the runtime is named after a prohibited tool."""
    offenders: list[str] = []
    for path in source_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.lower() == forbidden:
                    offenders.append(f"{_relative(path)} line {node.lineno}")
    assert not offenders, f"'{forbidden}' is defined at: {offenders}"
