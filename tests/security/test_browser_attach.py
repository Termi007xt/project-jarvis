"""ADR-0031: Playwright is a client of a browser we started, never a launcher.

`tests/security/test_no_shell.py` AST-scans `src/` for every primitive that can
start a process, and its `ALLOW_LIST` names exactly one authorised call site
(ADR-0029). That scan is the most load-bearing control in the repository — and it
has a blind spot that matters from Phase 2 onwards.

**It cannot see inside `site-packages`.** `playwright.chromium.launch()` and
`launch_persistent_context()` create browser processes from library code the scan
never reads. Calling either would give the product a second process-creation call
site while leaving `ALLOW_LIST` empty and the whole security suite green. The
invariant would be false and nothing would say so.

That is the Phase 1 defect class — a green suite compatible with a broken
product — pointed at the control the rest of the product's safety rests on. So
the rule is asserted here directly rather than trusted to review: Brave is
started through `jarvis.toolbox.launch.launch_argv` with a debugging port, and
Playwright attaches to it with `connect_over_cdp`.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "jarvis"

#: Playwright entry points that create a browser process. `connect_over_cdp` and
#: `connect` are deliberately absent — attaching is the whole point.
LAUNCHING_ATTRIBUTES = frozenset(
    {
        "launch",
        "launch_persistent_context",
        "launch_server",
    }
)

#: Passing an executable path to a driver is how a launch is aimed at a binary.
#: If this appears, something is choosing a program to run outside the catalogue.
LAUNCHING_KEYWORDS = frozenset({"executable_path", "executablePath"})


def _python_sources() -> list[Path]:
    return sorted(path for path in SRC.rglob("*.py") if "__pycache__" not in path.parts)


def test_the_product_ships_python_to_scan() -> None:
    """A scan over nothing passes trivially; make that impossible."""
    assert len(_python_sources()) > 40


@pytest.mark.parametrize("path", _python_sources(), ids=lambda p: p.name)
def test_playwright_is_never_asked_to_launch_a_browser(path: Path) -> None:
    """No `src/` module may call a Playwright API that starts a process."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        function = node.func
        if isinstance(function, ast.Attribute) and function.attr in LAUNCHING_ATTRIBUTES:
            # `launch` is a common enough word that this could bite an unrelated
            # method one day. The message says what to do about it rather than
            # leaving the next person to guess.
            pytest.fail(
                f"{path.relative_to(SRC.parent.parent)}:{node.lineno} calls "
                f"'.{function.attr}()'. If this is Playwright, it creates a "
                "second process-creation call site that "
                "tests/security/test_no_shell.py cannot see, because the Popen "
                "is in site-packages. Launch the browser through "
                "jarvis.toolbox.launch.launch_argv with a debugging port and "
                "attach with connect_over_cdp instead (ADR-0029, ADR-0031). If "
                "this call is unrelated to Playwright, rename it."
            )

        for keyword in node.keywords:
            if keyword.arg in LAUNCHING_KEYWORDS:
                pytest.fail(
                    f"{path.relative_to(SRC.parent.parent)}:{node.lineno} passes "
                    f"'{keyword.arg}'. Choosing which binary runs belongs to the "
                    "application catalogue, not to a driver argument "
                    "(ADR-0029 constraint 3)."
                )


def test_the_authorised_call_site_is_still_the_only_one() -> None:
    """ADR-0031 consumes ADR-0029's exception; it must not have widened it."""
    from tests.security.test_no_shell import ALLOW_LIST  # type: ignore[import-not-found]

    assert len(ALLOW_LIST) <= 1, (
        f"ALLOW_LIST has grown to {len(ALLOW_LIST)} entries. Browser automation "
        "was supposed to need none — it attaches to a browser launched through "
        "the existing site."
    )
