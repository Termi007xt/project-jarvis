"""Check the instruction against what happened, not the summary (ADR-0033).

Every earlier attempt at this read the model's reply, and the reply kept finding
new ways to be slippery:

* "has been closed" was caught, "was closed" was not;
* "successfully closed" was caught, "closed successfully" was not;
* a known action verb was needed, so "let me **use** the search tool" was not;
* and finally, on 2026-08-06:

      Sir: open YouTube music and play whatever song is currently in the queue.
      Jarvis: YouTube Music is now open ... It's already playing the current
              song. The application shows as running with process ID 4760.

  `app.open` had verified. Nothing that can play anything had run. A contraction
  and the word "already" were enough to slip every pattern watching the reply.

Four patches to the same guess is the point at which the guess is wrong. The
owner's request does not slip: it is short, it is imperative, and it said
"play". So the request is the specification, and the question is whether
anything that could carry out each part of it was even called.

**Attempted, not succeeded.** `app.close` that ran and came back unverified
because Edge raised a dialog has been attempted, and the honest answer is to say
so — not to close it again while the owner is reading the prompt. Retrying is
what `_unresolved_failure` is for, and only for outcomes worth retrying.
"""

from __future__ import annotations

from jarvis.core.tools.contract import Verification
from jarvis.llm.conversation import outstanding_requests


class _Ran:
    def __init__(self, tool_id: str, verification=Verification.VERIFIED) -> None:
        self.tool_id = tool_id
        self.verification = verification
        self.succeeded = verification is not Verification.FAILED
        self.outcome = "succeeded" if self.succeeded else "failed"
        self.message = ""


# =========================================================================
# The case the owner reported
# =========================================================================
def test_opening_something_is_not_playing_it() -> None:
    outstanding = outstanding_requests(
        "open YouTube music and play whatever song is currently loaded in the queue",
        [_Ran("app.open")],
    )

    assert "play" in outstanding
    assert "open" not in outstanding, "opening it really did happen"


def test_both_halves_of_a_two_part_request_are_tracked() -> None:
    """"Open YouTube and search for Godzilla" is two things, not one."""
    request = "open YouTube and search for Godzilla"

    assert outstanding_requests(request, [_Ran("app.open")]) == ("search",)
    assert outstanding_requests(
        request, [_Ran("app.open"), _Ran("youtube.search")]
    ) == ()


# =========================================================================
# It must not become a retry loop
# =========================================================================
def test_an_attempt_that_could_not_be_verified_still_counts_as_attempted() -> None:
    """The line that keeps this safe.

    `app.close` came back unverified because Edge put a "leave site?" dialog up.
    That is a complete answer — the owner has something to respond to. Treating
    it as outstanding would close it again while they were reading the prompt.
    """
    outstanding = outstanding_requests(
        "close MS Edge", [_Ran("app.close", Verification.UNVERIFIED)]
    )

    assert outstanding == ()


def test_a_question_is_not_an_instruction() -> None:
    """"Can you close a window?" asks what Jarvis can do. Answering it is a
    complete turn, and acting on it would be answering a different question."""
    assert outstanding_requests("can you close a window?", []) == ()
    assert outstanding_requests("what can you open?", []) == ()


def test_conversation_asks_for_nothing() -> None:
    assert outstanding_requests("what's good bro?", []) == ()
    assert outstanding_requests("thanks, that worked", []) == ()


def test_a_failed_attempt_is_left_to_the_failure_check() -> None:
    """Two mechanisms, one job each.

    A tool that ran and failed is handled by `_unresolved_failure`, which knows
    which outcomes are worth another try and — crucially — that a *denied*
    permission is never one of them. Reporting it here as well would retry
    refusals, which is the one behaviour that would make Jarvis unpleasant.
    """
    outstanding = outstanding_requests(
        "play the song", [_Ran("youtube.play", Verification.FAILED)]
    )

    assert outstanding == ()


# =========================================================================
# The wake word must not reach the planner
# =========================================================================
def test_a_misheard_wake_word_is_removed_from_the_command() -> None:
    """Reported by the owner on 2026-08-06.

        Sir: H-Arvis Open MS Edge and Brave
        Jarvis: ... I notice you mentioned "H-Arvis" and "Open MS Edge and
                Brave" - it seems there may have been some text mixed together.
                Could you clarify what you'd like me to do?

    The wake word reached the planner as part of the instruction and the model
    quite reasonably tried to make sense of it, spending a whole turn asking
    about a word the owner never said. The exact-match strip wanted both words
    of "Hey Jarvis" in order; what arrives is whatever the recogniser made of a
    word said at a microphone.
    """
    from jarvis.audio.stt import strip_wake_phrase

    for heard in (
        "H-Arvis Open MS Edge and Brave",
        "Harvis open MS Edge",
        "Jarvis, open MS Edge",
        "Hey Jarvis open MS Edge",
        "hey, jarvis open MS Edge",
    ):
        assert strip_wake_phrase(heard, "Hey Jarvis").lower().startswith("open"), (
            f"the wake word survived in {heard!r}"
        )


def test_an_ordinary_word_that_looks_a_bit_like_it_survives() -> None:
    """"jar" and "Java" are words. Stripping them would eat the command."""
    from jarvis.audio.stt import strip_wake_phrase

    assert strip_wake_phrase("jar of coffee on the desk", "Hey Jarvis").startswith("jar")
    assert strip_wake_phrase("Java is installed", "Hey Jarvis").startswith("Java")
    assert strip_wake_phrase("open the jar", "Hey Jarvis") == "open the jar"


def test_a_second_mention_of_the_name_is_kept() -> None:
    """Only the leading wake is a wake. The rest is what was said."""
    from jarvis.audio.stt import strip_wake_phrase

    assert (
        strip_wake_phrase("Hey Jarvis, remind me to say hey Jarvis", "Hey Jarvis")
        == "remind me to say hey Jarvis"
    )
