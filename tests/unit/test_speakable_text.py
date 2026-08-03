"""What Jarvis says aloud is not the same string as what it writes down.

From a real session: the model answers with "Opening Brave for you 🦁 — here's
the link: **https://brave.com/download?ref=abc123**", and Kokoro's phonemiser
does exactly what it is built to do. It expands every character to its Unicode
name, so the room hears

    "lion face em dash here's the link asterisk asterisk h t t p s colon
     slash slash brave dot com slash download question mark ref equals a b c
     one two three"

None of that is speech. The transcript keeps every character; only the spoken
copy is stripped, so nothing is hidden from the person reading the screen.

Redaction (FR-034) is a separate concern and stays separate: this function is
about *legibility*, and it runs before redaction so a secret dressed up in
markdown cannot slip past the patterns.
"""

from __future__ import annotations

import pytest

from jarvis.audio.tts import redact_for_speech, speakable_text


# -- emoji ------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Opening Brave 🦁",
        "Done 👍",
        "Nice work! 🎉🎊",
        "Careful ⚠️",
        "All set ✅",
        "Family 👨‍👩‍👧‍👦 photo",  # zero-width joiner sequence
        "Wave 👋🏽",  # skin-tone modifier
        "Flag 🇬🇧",  # regional indicators
        "Keycap 1️⃣",
    ],
)
def test_no_emoji_survives(text: str) -> None:
    spoken = speakable_text(text)
    assert all(ord(character) < 0x2000 for character in spoken), spoken


def test_the_words_around_an_emoji_are_kept() -> None:
    assert speakable_text("Opening Brave 🦁 now") == "Opening Brave now"


def test_an_emoji_only_message_becomes_empty() -> None:
    """The caller decides what to do with nothing; this does not invent words."""
    assert speakable_text("🎉🎊👍") == ""


# -- markdown ---------------------------------------------------------------
def test_emphasis_markers_are_removed_not_spoken() -> None:
    assert speakable_text("that is **really** important") == "that is really important"
    assert speakable_text("that is *really* important") == "that is really important"
    assert speakable_text("that is __really__ important") == "that is really important"


def test_snake_case_words_keep_their_underscores() -> None:
    """Stripping every underscore would mangle identifiers the user asked about."""
    assert "speak_replies" in speakable_text("the setting is speak_replies")


def test_a_bullet_list_does_not_read_its_bullets() -> None:
    spoken = speakable_text("- open Brave\n- play music\n* and stop")
    assert "-" not in spoken
    assert "*" not in spoken
    assert "open Brave" in spoken and "play music" in spoken


def test_headings_lose_their_hashes() -> None:
    assert speakable_text("## What I did") == "What I did"


def test_inline_code_keeps_the_word_but_not_the_backticks() -> None:
    assert speakable_text("run `pytest` now") == "run pytest now"


def test_a_fenced_code_block_is_described_not_recited() -> None:
    spoken = speakable_text("Here it is:\n```python\nfor x in y:\n    print(x)\n```\nDone.")
    assert "print" not in spoken
    assert "code block" in spoken
    assert "Done." in spoken


# -- links and URLs ---------------------------------------------------------
def test_a_markdown_link_is_read_as_its_text() -> None:
    assert speakable_text("see [the docs](https://example.com/a/b)") == "see the docs"


def test_a_bare_url_is_read_as_its_host() -> None:
    spoken = speakable_text("opening https://music.youtube.com/watch?v=dQw4w9WgXcQ")
    assert "watch" not in spoken and "dQw4w9WgXcQ" not in spoken
    assert "music dot youtube dot com" in spoken


def test_a_host_drops_a_leading_www() -> None:
    assert "youtube dot com" in speakable_text("https://www.youtube.com/feed")
    assert "www" not in speakable_text("https://www.youtube.com/feed")


# -- whitespace and symbols -------------------------------------------------
def test_whitespace_is_collapsed() -> None:
    assert speakable_text("one\n\n\ntwo   three") == "one two three"


def test_ordinary_punctuation_is_left_alone() -> None:
    text = "It is 4 o'clock, and the answer is: yes — really?"
    assert speakable_text(text) == text


def test_plain_text_is_returned_unchanged() -> None:
    text = "The time is four o'clock."
    assert speakable_text(text) is not None
    assert speakable_text(text) == text


# -- order of operations ----------------------------------------------------
def test_a_secret_dressed_in_markdown_is_still_redacted() -> None:
    """Stripping runs first, so emphasis cannot hide a key from the patterns."""
    spoken, redacted = redact_for_speech(speakable_text("the key is **sk-abcdefgh12345678**"))
    assert redacted
    assert "sk-abcdefgh" not in spoken


def test_stripping_never_returns_none() -> None:
    assert speakable_text("") == ""
