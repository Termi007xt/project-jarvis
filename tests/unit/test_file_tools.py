"""Finding a file and pointing at it (P2-FS-02, P2-FS-03, FR-191 … FR-193).

The security boundary is asserted in `tests/security/test_file_scope.py`. This
file is about the tools on top of it, and one property matters more than the
rest: **the model never handles a path.**

`files.find` takes words and returns numbered results; `files.reveal` takes one
of those numbers. A tool that accepted a path would work perfectly well and
would put the scope check in the position of being the only thing between an
injected instruction and the owner's private folders. A position cannot name a
file that was not already found inside the boundary — the defence is in the
signature rather than in a check that has to be remembered.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.core.tools.contract import ToolContext, ToolFailure
from jarvis.toolbox.files import FileScope, search_files
from jarvis.toolbox.phase2_file_tools import (
    FileFindInput,
    FileFindTool,
    FileRevealInput,
    FileRevealTool,
    FileWorkspace,
)


@pytest.fixture
def workspace(tmp_path: Path) -> FileWorkspace:
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "budget 2026.xlsx").write_text("x")
    (folder / "budget notes.txt").write_text("x")
    (folder / "holiday.jpg").write_text("x")
    return FileWorkspace(FileScope(roots=(folder,)))


def _find(workspace: FileWorkspace, query: str):
    return FileFindTool(workspace).run(ToolContext(), FileFindInput(query=query))


# =========================================================================
# Finding
# =========================================================================
def test_it_finds_by_the_words_a_person_would_say(workspace: FileWorkspace) -> None:
    result = _find(workspace, "budget")

    names = [file.name for file in result.output.files]
    assert "budget 2026.xlsx" in names
    assert "holiday.jpg" not in names


def test_results_are_numbered_from_zero(workspace: FileWorkspace) -> None:
    result = _find(workspace, "budget")

    assert [file.position for file in result.output.files] == list(
        range(len(result.output.files))
    )


def test_the_better_name_match_comes_first(tmp_path: Path) -> None:
    """Predictable beats clever. The user has to be able to guess the answer."""
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "notes about the budget process.txt").write_text("x")
    (folder / "budget.xlsx").write_text("x")
    workspace = FileWorkspace(FileScope(roots=(folder,)))

    result = _find(workspace, "budget")

    assert result.output.files[0].name == "budget.xlsx"


def test_finding_nothing_says_so_rather_than_failing(workspace: FileWorkspace) -> None:
    """An empty answer is an answer. A failure would read as something broken."""
    result = _find(workspace, "there is no such file")

    assert result.output.count == 0
    assert "nothing matching" in result.message


def test_a_search_reports_that_names_are_not_instructions(
    workspace: FileWorkspace,
) -> None:
    assert "not instructions" in _find(workspace, "budget").message


def test_searching_changes_nothing(workspace: FileWorkspace) -> None:
    """Read-only, and it says so — which is what stops a search licensing a
    claim that something was done."""
    assert FileFindTool.spec.changes_state is False
    assert _find(workspace, "budget").verification.value == "not_applicable"


# =========================================================================
# The model never handles a path
# =========================================================================
def test_neither_tool_accepts_a_path() -> None:
    """The defence written into the signature.

    With a path parameter, the only thing between an injected instruction and
    somebody's private folders is the scope check remembering to run. Without
    one, there is nothing to inject: a position can only name a file that a
    search already found inside the boundary.
    """
    forbidden = {"path", "file", "filename", "directory", "folder", "full_path"}
    for tool in (FileFindTool, FileRevealTool):
        fields = set(tool.spec.input_model.model_fields)
        assert not fields & forbidden, f"{tool.spec.tool_id} accepts a path: {fields}"


def test_revealing_before_searching_is_refused(workspace: FileWorkspace) -> None:
    with pytest.raises(ToolFailure) as raised:
        FileRevealTool(workspace).run(ToolContext(), FileRevealInput(position=0))

    assert raised.value.code == "nothing_searched"


def test_a_position_past_the_end_is_refused(workspace: FileWorkspace) -> None:
    """Not clamped to the last result. Clamping would reveal a file the user
    never asked about, and would look like it had worked."""
    _find(workspace, "budget")

    with pytest.raises(ToolFailure) as raised:
        FileRevealTool(workspace).run(ToolContext(), FileRevealInput(position=99))

    assert raised.value.code == "no_such_file"


def test_reveal_rechecks_the_scope_rather_than_trusting_the_search(
    workspace: FileWorkspace, tmp_path: Path
) -> None:
    """A position is only as safe as the list behind it.

    If the approved folders are narrowed between the search and the reveal, the
    remembered result is stale — and stale is exactly when a check matters.
    """
    _find(workspace, "budget")
    workspace.scope = FileScope(roots=(tmp_path / "somewhere-else",))

    with pytest.raises(ToolFailure) as raised:
        FileRevealTool(workspace).run(ToolContext(), FileRevealInput(position=0))

    assert raised.value.code == "no_such_file"


# =========================================================================
# Ranking, as a unit
# =========================================================================
def test_all_the_words_in_any_order(tmp_path: Path) -> None:
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "2026 budget final.xlsx").write_text("x")
    scope = FileScope(roots=(folder,))

    assert search_files("budget 2026", scope)


def test_the_search_is_bounded(tmp_path: Path) -> None:
    """A home directory is not a small place, and a hang looks like thinking."""
    folder = tmp_path / "many"
    folder.mkdir()
    for index in range(120):
        (folder / f"report {index}.txt").write_text("x")

    matches = search_files("report", FileScope(roots=(folder,)), limit=10)

    assert len(matches) == 10
