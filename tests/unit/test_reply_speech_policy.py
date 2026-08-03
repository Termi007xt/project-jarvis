"""When Jarvis should open its mouth, and when a beep is the right answer.

Reported from real use:

    "i guess it only needs to speak when i ask it a question or when it has
     follow up questions/clarifications for me. friendly messages are good, but
     not when not required. like if i just say open brave, call tool and open,
     but dont need to speak."

The distinction is not "did a tool run" — asking "what's the volume?" runs a
tool and still deserves an answer out loud. It is whether the user asked for
*information* or issued an *instruction*. An instruction that worked is
self-evidencing: Brave is on the screen. Saying so is noise.

Three things always override the policy, because silence about them is a
failure mode rather than a courtesy: something went wrong, something is
unverified, or Jarvis needs an answer before it can continue.

The decision is made in code rather than asked of the model. A model that
decides whether to speak will drift, and the failure is invisible: nobody
notices the sentence that was not said.
"""

from __future__ import annotations

import pytest

from jarvis.audio.reply_policy import ReplyVoice, SpeakReplies, should_speak


class _Result:
    def __init__(self, succeeded: bool = True, tool_id: str = "app.open") -> None:
        self.succeeded = succeeded
        self.tool_id = tool_id


def _decide(**overrides) -> ReplyVoice:
    call = {
        "spoken_request": True,
        "policy": SpeakReplies.WHEN_USEFUL,
        "request": "open brave",
        "reply": "I have opened Brave for you.",
        "tool_results": (_Result(),),
        "ok": True,
    }
    call.update(overrides)
    return should_speak(**call)


# -- the case the user reported --------------------------------------------
def test_a_command_that_worked_gets_a_cue_not_a_sentence() -> None:
    assert _decide() is ReplyVoice.CUE


@pytest.mark.parametrize(
    "request_text",
    ["open brave", "play some music", "turn the volume up", "open youtube music"],
)
def test_instructions_are_not_narrated(request_text: str) -> None:
    assert _decide(request=request_text) is ReplyVoice.CUE


# -- questions are answered aloud ------------------------------------------
@pytest.mark.parametrize(
    "request_text",
    [
        "what time is it right now?",
        "what is the volume",
        "how loud is it",
        "is brave running",
        "can you hear me",
        "tell me what the volume is",
        "why did that fail",
        "who am i",
    ],
)
def test_questions_are_answered_out_loud(request_text: str) -> None:
    assert _decide(request=request_text) is ReplyVoice.SPEAK


def test_a_question_that_ran_a_tool_is_still_answered_out_loud() -> None:
    """"what's the volume?" runs device.volume and still deserves an answer."""
    assert (
        _decide(request="what is the volume?", tool_results=(_Result(tool_id="device.volume"),))
        is ReplyVoice.SPEAK
    )


def test_a_pure_conversation_turn_is_spoken() -> None:
    assert _decide(request="thanks", tool_results=()) is ReplyVoice.SPEAK


# -- the overrides ----------------------------------------------------------
def test_a_failure_is_always_spoken() -> None:
    assert _decide(ok=False, reply="") is ReplyVoice.SPEAK


def test_a_failed_tool_is_always_spoken() -> None:
    assert _decide(tool_results=(_Result(succeeded=False),)) is ReplyVoice.SPEAK


def test_a_follow_up_question_is_always_spoken() -> None:
    """Otherwise Jarvis waits silently for an answer nobody knows it wants."""
    assert (
        _decide(reply="Which of the two Brave profiles did you mean?")
        is ReplyVoice.SPEAK
    )


def test_an_empty_reply_is_not_spoken_as_silence() -> None:
    assert _decide(reply="   ") is ReplyVoice.CUE


# -- typing is not speaking -------------------------------------------------
def test_a_typed_request_is_never_answered_aloud() -> None:
    """You are already looking at the screen; do not talk over it."""
    for policy in SpeakReplies:
        assert should_speak(
            spoken_request=False,
            policy=policy,
            request="what time is it?",
            reply="Four o'clock.",
            tool_results=(),
            ok=True,
        ) is ReplyVoice.SILENT


# -- the setting ------------------------------------------------------------
def test_always_speaks_even_for_a_finished_instruction() -> None:
    assert _decide(policy=SpeakReplies.ALWAYS) is ReplyVoice.SPEAK


def test_never_stays_silent_even_for_a_failure() -> None:
    assert _decide(policy=SpeakReplies.NEVER, ok=False) is ReplyVoice.SILENT


def test_always_still_says_nothing_when_there_is_nothing_to_say() -> None:
    assert _decide(policy=SpeakReplies.ALWAYS, reply="") is ReplyVoice.CUE


def test_an_unknown_policy_value_speaks_rather_than_swallowing_the_reply() -> None:
    """A bad config value must not silently make Jarvis mute."""
    assert _decide(policy="nonsense") is ReplyVoice.SPEAK
