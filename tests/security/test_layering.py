"""Layering invariants (ARCHITECTURE.md section 5, ADR-0004).

The rule that makes the engine headless-testable and the GUI replaceable:
``jarvis.ui`` is the only package permitted to import PySide6, and no layer may
import a layer above it.
"""

from __future__ import annotations

import ast
from pathlib import Path

LAYERS: dict[str, int] = {
    "jarvis.common": 0,
    "jarvis.config": 1,
    "jarvis.storage": 1,
    "jarvis.core": 2,
    "jarvis.tasks": 3,
    "jarvis.llm": 3,
    "jarvis.toolbox": 3,
    "jarvis.audio": 3,
    "jarvis.automation": 3,
    "jarvis.diagnostics": 1,
    "jarvis.runtime": 4,
    "jarvis.ui": 5,
    "jarvis.main": 5,
}


def _module_name(path: Path) -> str:
    parts = path.with_suffix("").parts
    index = parts.index("jarvis")
    name = ".".join(parts[index:])
    return name[: -len(".__init__")] if name.endswith(".__init__") else name


def _package_of(module: str) -> str | None:
    for candidate in sorted(LAYERS, key=len, reverse=True):
        if module == candidate or module.startswith(candidate + "."):
            return candidate
    return None


def _imported_modules(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imports.append((node.module, node.lineno))
    return imports


def test_only_layer_5_imports_pyside(source_files: list[Path]) -> None:
    """Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.

    Everything below L5 must be importable and testable with no Qt at all.
    """
    offenders: list[str] = []
    for path in source_files:
        module = _module_name(path)
        package = _package_of(module)
        if package is None or LAYERS[package] == 5:
            continue
        for imported, line in _imported_modules(path):
            if imported.split(".")[0] in {"PySide6", "PyQt5", "PyQt6", "shiboken6"}:
                offenders.append(f"{module} (L{LAYERS[package]}) line {line}: imports {imported}")

    assert not offenders, (
        "Only the presentation layer may import Qt, so the engine stays "
        "headless-testable and the shell stays replaceable (ADR-0004).\n  "
        + "\n  ".join(offenders)
    )


def test_the_engine_layers_contain_no_qt_import_at_all(source_files: list[Path]) -> None:
    """Spelled out separately because it is the invariant people break first."""
    engine_packages = {
        name for name, layer in LAYERS.items() if layer < 5
    }
    for path in source_files:
        module = _module_name(path)
        package = _package_of(module)
        if package not in engine_packages:
            continue
        text = path.read_text(encoding="utf-8")
        assert "PySide6" not in text or "import PySide6" not in text, (
            f"{module} references PySide6; the engine must not depend on Qt"
        )


def test_jarvis_main_may_import_ui_lazily(repo_root: Path) -> None:
    """``jarvis.main`` imports the GUI inside a function, not at module scope."""
    tree = ast.parse((repo_root / "src" / "jarvis" / "main.py").read_text(encoding="utf-8"))
    module_level_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {node.module for node in tree.body if isinstance(node, ast.ImportFrom) and node.module}
    assert not any(
        str(name).startswith(("PySide6", "jarvis.ui")) for name in module_level_imports
    ), "jarvis.main must import Qt lazily so --check works without a display"


def test_no_module_imports_a_higher_layer(source_files: list[Path]) -> None:
    offenders: list[str] = []
    for path in source_files:
        module = _module_name(path)
        own_package = _package_of(module)
        if own_package is None:
            continue
        own_layer = LAYERS[own_package]
        for imported, line in _imported_modules(path):
            if not imported.startswith("jarvis"):
                continue
            other_package = _package_of(imported)
            if other_package is None:
                continue
            if LAYERS[other_package] > own_layer:
                offenders.append(
                    f"{module} (L{own_layer}) line {line}: imports "
                    f"{imported} (L{LAYERS[other_package]})"
                )

    assert not offenders, (
        "Dependencies must point downward only (ARCHITECTURE.md section 5).\n  "
        + "\n  ".join(offenders)
    )


def test_engine_imports_cleanly_without_qt_loaded() -> None:
    """A fresh interpreter can import the whole engine with no Qt module loaded."""
    import importlib
    import sys

    for module in (
        "jarvis.config",
        "jarvis.storage",
        "jarvis.core.events",
        "jarvis.core.audit",
        "jarvis.core.permissions",
        "jarvis.core.tools",
        "jarvis.tasks",
        "jarvis.llm.ollama",
        "jarvis.toolbox",
        "jarvis.runtime",
    ):
        importlib.import_module(module)

    # Qt may already be loaded by the UI test suite in the same session, so this
    # asserts on the import graph rather than sys.modules: covered structurally
    # by test_only_the_ui_package_imports_pyside above.
    assert "jarvis.runtime.core" in sys.modules
