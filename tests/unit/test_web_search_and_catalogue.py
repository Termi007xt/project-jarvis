"""Searching, and opening an application that takes an optional argument.

Both come from a real session.

**The malformed search.** Asked to "search some new games coming in 2027",
the model built this URL itself and Google answered 400:

    https://www.google.com/search?q=latest%2Bupcoming%2Bvideogames+%3A2027&tbm=news

It had percent-encoded its own separators. `web.search` takes the words and
builds the URL here, so there is exactly one place that knows how to encode a
query and it is not the model.

**"open steam".** The entry declared a required app id because
`steam.exe -applaunch` with no id is malformed, so plain "open Steam" failed
and the model improvised a confusing explanation. Opening the client with no
argument is a perfectly ordinary request.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from jarvis.core.tools.contract import ToolContext, ToolFailure, Verification
from jarvis.toolbox.launch import (
    ApplicationCatalogue,
    ApplicationEntry,
    ArgumentKind,
    LaunchKind,
    LaunchOutcome,
    build_argv,
    default_catalogue,
)
from jarvis.toolbox.phase1_tools import SEARCH_ENGINES, WebSearchTool


@pytest.fixture
def catalogue() -> ApplicationCatalogue:
    return ApplicationCatalogue(
        (
            ApplicationEntry(
                app_id="brave",
                display_name="Brave",
                kind=LaunchKind.EXECUTABLE,
                target=r"C:\brave.exe",
                argument_kind=ArgumentKind.URL,
                verify_process_names=("brave.exe",),
            ),
        )
    )


def _search(catalogue, monkeypatch, **parameters):
    """Run the tool, capturing the URL instead of launching a browser."""
    captured: dict[str, str] = {}

    def fake_launch(entry, argument=None):
        captured["url"] = argument
        return LaunchOutcome(
            started=True, verified=True, pid=1, argv=(entry.target, argument or ""),
            detail="Brave is running",
        )

    monkeypatch.setattr("jarvis.toolbox.phase1_tools.launch", fake_launch)
    tool = WebSearchTool(catalogue)
    execution = tool.run(ToolContext(), WebSearchTool.spec.input_model(**parameters))
    return execution, captured["url"]


# -- the defect -------------------------------------------------------------
def test_a_plain_phrase_becomes_a_correctly_encoded_url(catalogue, monkeypatch) -> None:
    execution, url = _search(
        catalogue, monkeypatch, query="latest upcoming videogames 2027"
    )
    parsed = urlparse(url)
    assert parsed.scheme == "https"
    # Decoded back, the query is exactly what was asked for — no stray '+'
    # signs, no double encoding.
    assert parse_qs(parsed.query)["q"] == ["latest upcoming videogames 2027"]
    assert execution.verification is Verification.VERIFIED


def test_the_model_cannot_smuggle_its_own_encoding_through(catalogue, monkeypatch) -> None:
    """A query arriving pre-encoded must not be encoded again into nonsense."""
    _, url = _search(catalogue, monkeypatch, query="latest%2Bgames%3A2027")
    # Whatever it sent is treated as literal text, encoded once, and comes back
    # out as the same characters rather than a mangled query.
    assert parse_qs(urlparse(url).query)["q"] == ["latest%2Bgames%3A2027"]


@pytest.mark.parametrize(
    "query",
    [
        "cats & dogs",
        "what is 2+2",
        'quotes "and" things',
        "a/b?c=d",
        "emoji 🎮 games",
        "  padded  ",
    ],
)
def test_awkward_queries_survive_a_round_trip(catalogue, monkeypatch, query) -> None:
    _, url = _search(catalogue, monkeypatch, query=query)
    assert parse_qs(urlparse(url).query)["q"] == [query.strip()]


def test_a_url_is_not_a_search_query_but_is_still_handled_safely(
    catalogue, monkeypatch
) -> None:
    """The model sometimes passes a URL anyway. It becomes a search for it."""
    _, url = _search(catalogue, monkeypatch, query="https://example.com/x?y=1")
    assert url.startswith(tuple(t.split("{")[0] for t in SEARCH_ENGINES.values()))


# -- the engine is a closed set --------------------------------------------
def test_every_engine_is_https(catalogue) -> None:
    for template in SEARCH_ENGINES.values():
        assert template.startswith("https://")


def test_an_unknown_engine_is_refused(catalogue, monkeypatch) -> None:
    with pytest.raises(ToolFailure) as caught:
        _search(catalogue, monkeypatch, query="cats", engine="evil.example.com")
    assert caught.value.code == "unknown_engine"


def test_the_engine_cannot_be_a_url(catalogue, monkeypatch) -> None:
    """The model picks which approved engine, never where to send the query."""
    with pytest.raises(ToolFailure):
        _search(catalogue, monkeypatch, query="cats", engine="https://evil.example.com/?q=")


def test_a_missing_browser_is_reported_not_guessed(monkeypatch) -> None:
    with pytest.raises(ToolFailure) as caught:
        _search(ApplicationCatalogue(()), monkeypatch, query="cats")
    assert caught.value.code == "no_browser"


def test_the_tool_says_it_cannot_read_the_results(catalogue, monkeypatch) -> None:
    """It opens a page; it does not gain the ability to summarise one."""
    execution, _ = _search(catalogue, monkeypatch, query="cats")
    assert "cannot read the results" in execution.message


# -- "open steam" ----------------------------------------------------------
def test_steam_opens_with_no_app_id() -> None:
    entry = default_catalogue().get("steam")
    assert entry is not None
    argv = build_argv(entry)
    assert argv == (entry.target,), (
        "'open Steam' must open the client, not build a malformed command line"
    )


def test_steam_still_launches_a_game_when_given_an_id() -> None:
    entry = default_catalogue().get("steam")
    assert entry is not None
    assert build_argv(entry, "1172620") == (entry.target, "-applaunch", "1172620")


def test_a_non_numeric_steam_id_is_still_refused() -> None:
    from jarvis.toolbox.launch import CatalogueError

    entry = default_catalogue().get("steam")
    assert entry is not None
    with pytest.raises(CatalogueError):
        build_argv(entry, "1172620; calc.exe")


def test_a_browser_with_no_url_is_unaffected() -> None:
    entry = default_catalogue().get("brave")
    assert entry is not None
    assert build_argv(entry) == (entry.target,)


# -- "open YouTube Music" --------------------------------------------------
# Reported from real use: "it always opens youtube music as a tab in brave, and
# never the pwa i installed and pinned to my start menu". The catalogue entry
# was a URL handed to the browser, which is by definition a tab. An installed
# progressive web app has its own window and its own taskbar identity, and
# Chromium launches it by app id — a fixed argument vector, so this stays
# inside ADR-0029 with no new call site and no new argument kind.
def test_youtube_music_opens_the_installed_app_not_a_tab() -> None:
    entry = default_catalogue().get("youtube_music")
    assert entry is not None
    argv = build_argv(entry)

    assert any(part.startswith("--app-id=") for part in argv), (
        "YouTube Music is still being opened as an ordinary browser tab"
    )
    assert not any(part.startswith("http") for part in argv), (
        "a URL argument makes it a tab whatever else is passed"
    )


def test_the_app_id_and_profile_are_fixed_not_model_supplied() -> None:
    """ADR-0029 constraint 5: arguments come from the entry, never from text."""
    from jarvis.toolbox.launch import CatalogueError

    entry = default_catalogue().get("youtube_music")
    assert entry is not None
    assert entry.argument_kind is ArgumentKind.NONE
    # Refused outright rather than quietly dropped: an argument that goes
    # nowhere is indistinguishable from one that was honoured.
    with pytest.raises(CatalogueError):
        build_argv(entry, "https://example.com/evil")


def test_the_launcher_it_uses_is_not_an_interpreter() -> None:
    from jarvis.toolbox.launch import validate_entry

    entry = default_catalogue().get("youtube_music")
    assert entry is not None
    validate_entry(entry)  # raises if the basename is denylisted


def test_it_still_verifies_against_a_real_process() -> None:
    entry = default_catalogue().get("youtube_music")
    assert entry is not None
    assert entry.verify_process_names, "an unverifiable launch can only be 'unverified'"


def test_youtube_itself_is_still_a_tab() -> None:
    """Only the installed app changed; plain YouTube has no PWA here."""
    entry = default_catalogue().get("youtube")
    assert entry is not None
    assert any("youtube.com" in part for part in build_argv(entry))
