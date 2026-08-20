"""The Phase 2 browser tools, and the declarations they make about themselves.

AT-006's two utterances become two narrow typed tools. What is tested here is
mostly the *contract* — the shape of the parameters and the honesty of the
outcome — because that is what the invoker, the approval dialog and the planner
all read, and because Phase 1's lesson was that a tool can behave correctly while
declaring something that does not hold.
"""

from __future__ import annotations

import pytest

from jarvis.core.tools.contract import ToolContext, ToolFailure, Verification
from jarvis.tasks.locks import FOREGROUND_DESKTOP
from jarvis.toolbox.phase2_tools import (
    BrowserWorkspace,
    YouTubePlayInput,
    YouTubePlayTool,
    YouTubeSearchInput,
    YouTubeSearchTool,
)
from jarvis.toolbox.youtube import YouTubeAdapter

from tests.unit.test_youtube_adapter import FakePage, no_sleep


@pytest.fixture
def workspace() -> BrowserWorkspace:
    space = BrowserWorkspace()
    page = FakePage()
    page.player = {"playing": True, "video_id": "bbb222"}
    space.set_adapter(YouTubeAdapter(page=page, sleep=no_sleep))
    return space


# -- declarations ----------------------------------------------------------
@pytest.mark.parametrize("tool", [YouTubeSearchTool, YouTubePlayTool])
def test_a_browser_tool_owns_the_desktop(tool) -> None:
    """The stage 2 rule, now with something real to bind to."""
    assert FOREGROUND_DESKTOP in tool.spec.resource_locks
    assert "browser.automate_logged_in" in tool.spec.required_capabilities


def test_playing_takes_a_position_and_offers_no_way_to_name_a_title() -> None:
    """The injection defence, expressed as a tool signature.

    If a `title` or `query` parameter existed here, the model could be argued
    into filling it from page text, and a video that renames itself could
    redirect the action. There is no such parameter to fill.
    """
    fields = set(YouTubePlayInput.model_fields)
    assert fields == {"position"}


def test_the_play_description_tells_the_planner_that_second_means_one() -> None:
    """Off-by-one here is the difference between passing and failing AT-006."""
    description = YouTubePlayTool.spec.description.casefold()
    assert "second" in description and "position 1" in description


# -- behaviour -------------------------------------------------------------
def test_searching_reports_the_count_it_actually_read(workspace) -> None:
    tool = YouTubeSearchTool(workspace)
    execution = tool.run(ToolContext(), YouTubeSearchInput(query="RTX 5070"))

    assert execution.output.result_count == 3
    assert execution.verification is Verification.VERIFIED


def test_playing_the_second_video_is_verified_when_the_player_agrees(workspace) -> None:
    YouTubeSearchTool(workspace).run(ToolContext(), YouTubeSearchInput(query="RTX 5070"))
    execution = YouTubePlayTool(workspace).run(ToolContext(), YouTubePlayInput(position=1))

    assert execution.output.verified is True
    assert execution.verification is Verification.VERIFIED
    assert execution.output.video_id == "bbb222"


def test_a_click_the_player_cannot_confirm_is_unverified_not_failed() -> None:
    """Clicked and played are separate facts, and the tool must not merge them."""
    space = BrowserWorkspace()
    page = FakePage()
    page.player = None  # the player cannot be read
    space.set_adapter(YouTubeAdapter(page=page, sleep=no_sleep))

    YouTubeSearchTool(space).run(ToolContext(), YouTubeSearchInput(query="RTX 5070"))
    execution = YouTubePlayTool(space).run(ToolContext(), YouTubePlayInput(position=1))

    assert execution.output.clicked is True
    assert execution.verification is Verification.UNVERIFIED


def test_playing_without_a_session_names_the_missing_step() -> None:
    tool = YouTubePlayTool(BrowserWorkspace())
    with pytest.raises(ToolFailure) as raised:
        tool.run(ToolContext(), YouTubePlayInput(position=1))

    assert raised.value.code == "no_browser_session"


def test_playing_past_the_end_is_a_declared_failure(workspace) -> None:
    YouTubeSearchTool(workspace).run(ToolContext(), YouTubeSearchInput(query="RTX 5070"))

    with pytest.raises(ToolFailure) as raised:
        YouTubePlayTool(workspace).run(ToolContext(), YouTubePlayInput(position=9))

    assert raised.value.code == "no_such_result"
    assert raised.value.code in YouTubePlayTool.spec.failure_codes


def test_a_hostile_title_reaches_the_output_as_data(workspace) -> None:
    """Carried, not suppressed — hiding it would conceal the attack."""
    execution = YouTubeSearchTool(workspace).run(
        ToolContext(), YouTubeSearchInput(query="RTX 5070")
    )
    assert any("Ignore previous instructions" in title for title in execution.output.titles)
