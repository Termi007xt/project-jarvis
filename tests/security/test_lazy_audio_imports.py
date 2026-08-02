"""Audio dependencies stay optional and lazily imported (ADR-0010, NFR-014).

Decided 2026-08-02: the voice stack enters as an optional ``voice`` extra rather
than a core dependency. Kokoro and faster-whisper pull in torch and onnxruntime,
CI runs on Linux with no microphone or GPU, and ARCHITECTURE section 11 requires
that no test need any of them.

That only holds if nothing imports them at module scope. A single top-level
``import sounddevice`` in a provider would break ``import jarvis`` on a machine
without the extra, and the failure would surface as an unrelated crash at
start-up rather than as a named, honest unavailable state.

This is an AST test, so a docstring or a string literal naming a library does
not trip it, while a real import does.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

#: Optional at runtime. Present only when the ``voice`` extra is installed.
OPTIONAL_AUDIO_MODULES: frozenset[str] = frozenset(
    {
        "sounddevice",
        "soundfile",
        "faster_whisper",
        "kokoro",
        "openwakeword",
        "torch",
        "onnxruntime",
        "numpy",
        "misaki",
        "ctranslate2",
    }
)


def _module_name(path: Path) -> str:
    parts = path.with_suffix("").parts
    index = parts.index("jarvis")
    name = ".".join(parts[index:])
    return name[: -len(".__init__")] if name.endswith(".__init__") else name


def _module_scope_imports(path: Path) -> list[tuple[str, int]]:
    """Imports at module level only — imports inside a function are the point."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[str, int]] = []
    for node in tree.body:  # module scope, deliberately not ast.walk
        if isinstance(node, ast.Import):
            found.extend((alias.name.split(".")[0], node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((node.module.split(".")[0], node.lineno))
        elif isinstance(node, ast.If):
            # ``if TYPE_CHECKING:`` blocks never execute at runtime, but a
            # plain ``if`` at module scope does, so check its body too.
            for inner in ast.walk(node):
                if isinstance(inner, ast.Import):
                    found.extend(
                        (alias.name.split(".")[0], inner.lineno) for alias in inner.names
                    )
                elif isinstance(inner, ast.ImportFrom) and inner.module and inner.level == 0:
                    found.append((inner.module.split(".")[0], inner.lineno))
    return found


def test_no_module_imports_an_optional_audio_library_at_module_scope(
    source_files: list[Path],
) -> None:
    offenders: list[str] = []
    for path in source_files:
        for imported, line in _module_scope_imports(path):
            if imported in OPTIONAL_AUDIO_MODULES:
                offenders.append(f"{_module_name(path)} line {line}: imports {imported}")

    assert not offenders, (
        "Audio dependencies are an optional extra and must be imported inside "
        "the function that needs them, so the engine still imports with no "
        "voice stack installed and reports an honest unavailable state "
        "instead (ADR-0010, NFR-014).\n  " + "\n  ".join(offenders)
    )


def test_the_scanner_actually_detects_a_violation(tmp_path: Path) -> None:
    """A guard on the guard: prove the detector is not vacuously passing."""
    offender = tmp_path / "jarvis" / "bad.py"
    offender.parent.mkdir(parents=True)
    offender.write_text("import sounddevice\nfrom torch import nn\n", encoding="utf-8")

    found = {name for name, _line in _module_scope_imports(offender)}
    assert "sounddevice" in found
    assert "torch" in found


def test_an_import_inside_a_function_is_not_a_violation(tmp_path: Path) -> None:
    """The lazy pattern the rule is asking for must actually pass."""
    good = tmp_path / "jarvis" / "good.py"
    good.parent.mkdir(parents=True)
    good.write_text(
        "def load():\n    import sounddevice\n    return sounddevice\n", encoding="utf-8"
    )
    assert not [n for n, _ in _module_scope_imports(good) if n in OPTIONAL_AUDIO_MODULES]


def test_the_engine_imports_with_no_voice_stack_installed() -> None:
    """The property all of the above exists to protect."""
    import importlib

    for module in (
        "jarvis.audio",
        "jarvis.audio.availability",
        "jarvis.runtime.core",
        "jarvis.main",
    ):
        assert importlib.import_module(module) is not None


def test_availability_names_the_missing_component_rather_than_failing() -> None:
    from jarvis.audio.availability import describe_voice_stack

    status = describe_voice_stack()
    assert len(status.components) == 4
    for component in status.components:
        assert component.detail, f"{component.name} gives no reason for its state"
    if not status.fully_available:
        assert "voice" in status.summary() or "missing" in status.summary()


@pytest.mark.parametrize("extra", ["voice"])
def test_the_optional_extra_is_declared_in_pyproject(repo_root: Path, extra: str) -> None:
    text = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    assert f"{extra} = [" in text, (
        f"the '{extra}' optional-dependency group must exist so the install "
        "instruction the GUI prints is a real one"
    )
