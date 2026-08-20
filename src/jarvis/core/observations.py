"""Observed content — the only shape external data may take (PRD §11.4).

Everything this product reads from outside itself arrives here first: web pages,
search results, screen text, filenames, document bodies, clipboard contents. All
of it is **untrusted by construction**. There is no trusted variant of this type
and no flag to set, because the control this replaces was a boolean that every
call site had to remember, and a control that holds until one call site forgets
is not a control.

The rule, stated once so the rest of the codebase can point at it:

    Observed content can inform a plan. It can never authorise a capability.

Three properties make that structural rather than aspirational:

1. **An `Observation` cannot express authority.** It has no field for a
   capability, a grant, a risk level or a tool id, so there is nothing for a
   page's content to populate even if it were parsed credulously.
2. **It reaches the model wrapped, always.** `ChatMessage.from_observation()` is
   the only way in, and it sets ``untrusted=True`` unconditionally. That
   constructor lives in `jarvis.llm` rather than here, because L2 must not know
   about L3 — the dependency points downward, and
   `tests/security/test_layering.py` enforces it even for imports hidden inside
   a function.
3. **Selection from an observed list is positional.** `ObservedList.select()`
   takes an ordinal. There is deliberately no lookup by label, so a page that
   can rename itself cannot change which element an action lands on. This is the
   property that carries the weight — the delimiter wrapping is defence in depth
   and assumes a cooperative model; this one does not assume anything about the
   model at all.

Layer note: this is L2 (`jarvis.core`) because both `jarvis.llm` and
`jarvis.toolbox` are L3 and both need it — the browser adapter produces
observations and the conversation consumes them.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from jarvis.common import utc_now
from jarvis.core.events.types import UntrustedContentObserved

__all__ = [
    "ContentClass",
    "Observation",
    "ObservedItem",
    "ObservedList",
]


class ContentClass(str, Enum):
    """Where an observation came from. Recorded, never used to grant anything."""

    WEB_PAGE = "web_page"
    WEB_SEARCH_RESULT = "web_search_result"
    SCREEN_TEXT = "screen_text"
    UI_TEXT = "ui_text"
    FILE_NAME = "file_name"
    DOCUMENT = "document"
    CLIPBOARD = "clipboard"
    TOOL_OUTPUT = "tool_output"


class Observation(BaseModel):
    """A piece of content from outside the trust boundary.

    Deliberately minimal. Every field it does *not* have is a field a hostile
    page cannot fill in.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    origin: str = Field(description="Where it was read from — a URL, window title or path.")
    content_class: ContentClass
    text: str = Field(description="The content itself. Data, in every context.")
    observed_at: datetime = Field(default_factory=utc_now)

    @property
    def byte_length(self) -> int:
        return len(self.text.encode("utf-8"))

    @property
    def source_label(self) -> str:
        """How this content is labelled wherever it is shown or quoted."""
        return f"observed: {self.content_class.value}"

    def as_event(self, task_id: str | None = None) -> UntrustedContentObserved:
        """Record *that* untrusted content arrived, never *what it said*."""
        return UntrustedContentObserved(
            source="observations",
            origin=self.origin,
            content_class=self.content_class.value,
            byte_length=self.byte_length,
            task_id=task_id,
        )


class ObservedItem(BaseModel):
    """One element of an observed, ordered list.

    ``label`` is attacker-controlled text and is carried as evidence — it is what
    the user sees and what an audit reader needs. ``handle`` is what an action
    uses, and it is derived from the *position*, never from the label.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int = Field(ge=0)
    label: str
    handle: str


class ObservedList(BaseModel):
    """An ordered list read from outside — search results, files, windows.

    The public surface is intentionally tiny. There is no `find_by_label`, no
    `search`, no `match`: adding one would let a page choose which element an
    action lands on by naming itself convincingly, which is precisely the attack
    `tests/security/test_prompt_injection.py` exists to prevent.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    origin: str
    content_class: ContentClass
    items: tuple[ObservedItem, ...] = ()

    def select(self, position: int) -> ObservedItem:
        """Select by ordinal. "The second video" is ``select(1)``.

        Negative and out-of-range positions raise rather than resolving to
        something else. Python would otherwise read ``-1`` as the last element,
        which is a quiet way for "the second video" to become "the last video"
        once a page changes length.
        """
        if position < 0 or position >= len(self.items):
            raise IndexError(
                f"position {position} is outside the {len(self.items)} observed "
                f"item(s) from {self.origin}"
            )
        return self.items[position]

    def as_observation(self) -> Observation:
        """The whole list as content for the planner. Labels stay data."""
        listing = "\n".join(f"[{item.index}] {item.label}" for item in self.items)
        return Observation(
            origin=self.origin,
            content_class=self.content_class,
            text=listing,
        )

    def __len__(self) -> int:
        return len(self.items)
