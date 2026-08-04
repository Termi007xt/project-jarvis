"""Searching YouTube and playing a result (FR-090, FR-091, AT-006).

Phase 2 stage 3 — the phase's exit criterion: *"search RTX 5070 on youtube"*,
then *"play the second video"*. Two utterances, so search and play are separate
operations against a session that persists between them.

Three rules from earlier stages meet here, and none of them is negotiable:

**Results are observed content.** They come back as an `ObservedList`, so titles
are data and selection is by ordinal. "The second video" is `select(1)` — a
*position*. A page can title a video anything it likes, including something that
reads as an instruction, and it cannot change which element is clicked. Stage 0
measured that YouTube's results are index-addressable in DOM order; stage 1 built
the boundary; this is where the two meet.

**Titles are carried, not suppressed.** Stripping hostile-looking text would hide
an attack rather than defeat it, and would also throw away what the user needs to
see to know what they are about to play.

**A click is not a success.** `play()` returns a `PlaybackReport` that is
`verified` only when the player is read back, is actually playing, and is playing
*the video that was selected*. Reporting success because a click did not raise is
`started != running` — the defect that survived Phase 1 acceptance — in its third
costume. A page that reorders itself between reading and clicking produces
exactly that failure, and comparing the id is the only thing that catches it.

The page driver is injected, so this is fully testable headless and the real
Playwright-over-CDP attachment is a thin adapter above it (ADR-0031).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote_plus

from jarvis.core.observations import ContentClass, ObservedItem, ObservedList

__all__ = [
    "PageDriver",
    "PlaybackReport",
    "YouTubeAdapter",
    "YouTubeUnavailable",
    "SEARCH_URL_TEMPLATE",
    "DEFAULT_TIMEOUT_SECONDS",
]

_LOG = logging.getLogger(__name__)

#: One place knows how to encode a query, and it is not the model. Phase 1's
#: `web.search` exists because asking the model for a URL produced percent-encoded
#: separators that reached the user as a Google 400 page.
SEARCH_URL_TEMPLATE = "https://www.youtube.com/results?search_query={query}"

#: Every external interaction declares a timeout (CLAUDE.md).
DEFAULT_TIMEOUT_SECONDS = 20.0


class YouTubeUnavailable(RuntimeError):
    """The page could not be driven — a failure, never an unverified success."""


class PageDriver(Protocol):
    """The browser operations this adapter needs.

    Deliberately tiny, and deliberately positional: `click_result` takes an
    index, not a selector and not a title, so there is no way for this interface
    to be used to resolve an element from page-supplied text.
    """

    def goto(self, url: str, timeout_seconds: float) -> None: ...

    def results(self, timeout_seconds: float) -> list[dict[str, str]]: ...

    def click_result(self, position: int, timeout_seconds: float) -> None: ...

    def player_state(self, timeout_seconds: float) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class PlaybackReport:
    """What actually happened. `clicked` and `verified` are separate facts."""

    clicked: bool
    verified: bool
    position: int
    expected_video_id: str
    video_id: str | None
    title: str
    detail: str


class YouTubeAdapter:
    """Search YouTube, then play a result by position."""

    def __init__(
        self,
        page: PageDriver,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._page = page
        self._timeout = timeout_seconds
        self._results: ObservedList | None = None
        #: Ids kept alongside the observed list, so verification can compare
        #: what played against what was chosen. Not part of the observation:
        #: they are engine bookkeeping, not content shown to the planner.
        self._video_ids: tuple[str, ...] = ()

    @property
    def last_results(self) -> ObservedList:
        if self._results is None:
            raise RuntimeError("nothing has been searched for yet")
        return self._results

    # -- utterance one -------------------------------------------------
    def search(self, query: str) -> ObservedList:
        """Search, and return the results as untrusted, positional content."""
        url = SEARCH_URL_TEMPLATE.format(query=quote_plus(query.strip()))
        self._page.goto(url, self._timeout)

        raw = self._page.results(self._timeout)
        self._video_ids = tuple(str(entry.get("video_id", "")) for entry in raw)
        self._results = ObservedList(
            origin=url,
            content_class=ContentClass.WEB_SEARCH_RESULT,
            items=tuple(
                ObservedItem(
                    index=index,
                    label=str(entry.get("title", "")),
                    handle=f"nth={index}",
                )
                for index, entry in enumerate(raw)
            ),
        )
        _LOG.info("youtube search %r: %d result(s)", query, len(self._results))
        return self._results

    # -- utterance two -------------------------------------------------
    def play(self, position: int) -> PlaybackReport:
        """Play the result at `position`, and confirm that it is playing.

        `position` is an ordinal into the last search. It is never a title, so
        the labels on the page cannot influence what is played.
        """
        results = self.last_results  # raises if nothing was searched
        item = results.select(position)  # raises rather than wrapping
        expected_id = (
            self._video_ids[position] if position < len(self._video_ids) else ""
        )

        try:
            self._page.click_result(position, self._timeout)
        except Exception as exc:  # noqa: BLE001 - narrowed into our own type
            # A click that never landed is a *failure*. Calling it an unverified
            # success would let a task treat "nothing happened" as "something
            # might have happened", which is a strictly worse answer.
            raise YouTubeUnavailable(
                f"could not click result {position} ({item.label!r}): {exc}"
            ) from exc

        state = self._page.player_state(self._timeout)
        return self._report(position, item, expected_id, state)

    @staticmethod
    def _report(
        position: int,
        item: ObservedItem,
        expected_id: str,
        state: dict[str, Any] | None,
    ) -> PlaybackReport:
        base = dict(
            clicked=True, position=position, expected_video_id=expected_id, title=item.label
        )

        if state is None:
            return PlaybackReport(
                **base,
                verified=False,
                video_id=None,
                detail=(
                    "The result was clicked, but the player could not be read, so "
                    "whether anything is playing is unverified."
                ),
            )

        playing = bool(state.get("playing"))
        actual_id = str(state.get("video_id") or "") or None

        if not playing:
            return PlaybackReport(
                **base,
                verified=False,
                video_id=actual_id,
                detail="The result was clicked, but the player is not playing.",
            )

        if expected_id and actual_id != expected_id:
            # The page reordered between reading and clicking, or the click
            # landed elsewhere. Indistinguishable from success without this.
            return PlaybackReport(
                **base,
                verified=False,
                video_id=actual_id,
                detail=(
                    f"Something is playing, but it is {actual_id!r} and the video "
                    f"chosen at position {position} was {expected_id!r}. Reporting "
                    "this as unverified rather than as success."
                ),
            )

        return PlaybackReport(
            **base,
            verified=True,
            video_id=actual_id,
            detail=f"Playing result {position}: {item.label!r}.",
        )
