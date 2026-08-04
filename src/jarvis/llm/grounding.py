"""Where an answer came from, and what counts as done (PRD FR-047, FR-048).

Two separate honesty rules live here because they are easy to conflate:

**FR-047 — source labelling.** Every claim Jarvis makes is one of five things:
the model's own answer, a retrieved fact, an inference, a tool result, or an
admission of uncertainty. A model answer stated as though it were a tool result
is the specific failure this exists to prevent.

**FR-048 — tool-grounded success.** A conversational reply may only say an
action succeeded when a tool actually verified it. ``succeeded`` plus
``unverified`` is not success (PRD AT-018); it is a tool that ran and could not
confirm its effect, and the reply has to say so.

Neither rule can be enforced by asking the model nicely. Both are enforced here,
on the way out, against the tool results the invoker actually produced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

__all__ = [
    "SourceLabel",
    "GroundedClaim",
    "GroundingReview",
    "review_response",
    "SUCCESS_PHRASES",
]


class SourceLabel(str, Enum):
    """PRD FR-047's five categories, and nothing outside them."""

    MODEL_ANSWER = "model_answer"
    RETRIEVED_FACT = "retrieved_fact"
    INFERENCE = "inference"
    TOOL_RESULT = "tool_result"
    UNCERTAINTY = "uncertainty"

    @property
    def display(self) -> str:
        return {
            SourceLabel.MODEL_ANSWER: "from the local model",
            SourceLabel.RETRIEVED_FACT: "from a retrieved fact",
            SourceLabel.INFERENCE: "inferred",
            SourceLabel.TOOL_RESULT: "confirmed by a tool",
            SourceLabel.UNCERTAINTY: "uncertain",
        }[self]


#: Phrases that assert an action was completed. Deliberately conservative: a
#: false positive costs a hedged sentence, a false negative lets Jarvis claim a
#: success it never verified.
SUCCESS_PHRASES: tuple[str, ...] = (
    r"\bi(?:'ve| have)? (?:opened|launched|started|closed|sent|deleted|created|saved|played)\b",
    r"\bis now (?:open|running|playing|closed|paused|muted)\b",
    r"\bhas been (?:opened|launched|started|closed|sent|deleted|created|saved)\b",
    # "Done." as a whole statement, not the word "done" inside a sentence such
    # as "the wrong thing to have done". Anchored to a sentence boundary, since
    # the bare word is far too common to treat as a completion claim.
    r"(?:^|[.!?]\s+|\n)(?:done|all set|that'?s done|completed successfully)\b[.!\s]*$",
    r"\bsuccessfully \w+ed\b",
)

_SUCCESS_PATTERN = re.compile("|".join(SUCCESS_PHRASES), re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class GroundedClaim:
    """One statement and the label that must accompany it."""

    text: str
    label: SourceLabel
    evidence: str | None = None

    def render(self) -> str:
        if self.label is SourceLabel.MODEL_ANSWER:
            return self.text
        return f"{self.text} ({self.label.display})"


@dataclass(frozen=True)
class GroundingReview:
    """The verdict on a proposed reply."""

    text: str
    label: SourceLabel
    claims_success: bool
    verified_by_tool: bool
    amended: bool
    note: str | None = None

    @property
    def honest(self) -> bool:
        """True when nothing in the reply overstates what actually happened."""
        return not self.claims_success or self.verified_by_tool


def claims_completion(text: str) -> bool:
    """Whether a reply asserts that something was done."""
    return bool(_SUCCESS_PATTERN.search(text or ""))


def _verification_of(result: object) -> str:
    """The verification value of a succeeded result; empty if it did not succeed."""
    if not getattr(result, "succeeded", False):
        return ""
    return str(getattr(getattr(result, "verification", None), "value", ""))


def review_response(
    text: str,
    *,
    tool_results: tuple[object, ...] = (),
    retrieved: bool = False,
    uncertain: bool = False,
) -> GroundingReview:
    """Label a reply and stop it claiming an unverified success.

    ``tool_results`` are ``ToolResult`` objects from the invoker. Two different
    questions are asked of them, and conflating the two is the mistake this
    function exists to avoid:

    * **What is the source?** A succeeded read-only tool reports
      ``not_applicable`` — nothing changed, so there was nothing to verify — and
      what it returned is still a real observation, not a guess. It counts as a
      tool result for FR-047 labelling.
    * **May the reply claim an action happened?** Only a ``verified`` result
      supports that. A read-only tool cannot confirm that anything was done, so
      ``not_applicable`` never licenses a success claim (FR-048, AT-018).
    """
    verified = any(_verification_of(result) == "verified" for result in tool_results)
    observed = any(
        _verification_of(result) in ("verified", "not_applicable") for result in tool_results
    )
    ran_a_tool = bool(tool_results)

    if uncertain:
        label = SourceLabel.UNCERTAINTY
    elif observed:
        label = SourceLabel.TOOL_RESULT
    elif retrieved:
        label = SourceLabel.RETRIEVED_FACT
    elif ran_a_tool:
        # A state-changing tool ran and could not confirm its effect. That is
        # not a tool result in the FR-047 sense; it is at best an inference.
        label = SourceLabel.INFERENCE
    else:
        label = SourceLabel.MODEL_ANSWER

    asserts_success = claims_completion(text)
    if asserts_success and not verified:
        amended = _hedge(text, ran_a_tool)
        return GroundingReview(
            text=amended,
            label=label,
            claims_success=True,
            verified_by_tool=False,
            amended=True,
            note=(
                "the reply claimed an action was completed, but no tool verified "
                "it. Rewritten to say what is actually known (PRD FR-048, AT-018)."
            ),
        )

    return GroundingReview(
        text=text,
        label=label,
        claims_success=asserts_success,
        verified_by_tool=verified,
        amended=False,
    )


def _hedge(text: str, ran_a_tool: bool) -> str:
    """Replace an unverified success claim with what is actually known."""
    if ran_a_tool:
        return (
            "I could not confirm that, so I am not going to say it worked. "
            "The action ran but its effect could not be verified. "
            f"What I was going to say was: {text.strip()}"
        )
    return (
        "I have not actually done that — no tool ran, so nothing changed on "
        f"your computer. What I can tell you is: {text.strip()}"
    )
