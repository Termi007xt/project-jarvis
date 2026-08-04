"""FR-058: pause and ask, never solve. CAPTCHA bypass is prohibited (§11.1).

Phase 2 stage 3. This is a boundary, not a feature. `PRD.md` §11.1 lists CAPTCHA
bypass among the capabilities that have no implementation by design, so the only
correct behaviour when a challenge appears is to stop, hand the window to the
user, and wait — in a normal visible Brave window they can use with their own
mouse and keyboard, which is one of the reasons ADR-0019 chose a real browser
over a headless one.

**The asymmetry worth stating explicitly.** Challenge detection reads
page-supplied signals, and page-supplied signals are untrusted. That is fine
*here*, and only here, because of the direction they push: untrusted content
making Jarvis **more** cautious is safe, while untrusted content making it less
cautious is the whole prompt-injection problem. A page can stop automation by
pretending to be a CAPTCHA. It cannot start anything by pretending not to be
one — and a page that wanted automation to continue would simply not show a
challenge.
"""

from __future__ import annotations

import pytest

from jarvis.toolbox.captcha import (
    ChallengeDetected,
    challenge_in,
    describe_challenge,
)


# -- detection -------------------------------------------------------------
@pytest.mark.parametrize(
    "markup",
    [
        '<iframe src="https://www.google.com/recaptcha/api2/anchor"></iframe>',
        '<div class="h-captcha" data-sitekey="x"></div>',
        '<div id="cf-challenge-running">Checking your browser</div>',
        "<title>Just a moment...</title>",
        "<p>Our systems have detected unusual traffic from your computer network</p>",
        '<form id="captcha-form">',
    ],
)
def test_a_known_challenge_is_recognised(markup: str) -> None:
    assert challenge_in(markup) is not None


@pytest.mark.parametrize(
    "markup",
    [
        "<div>RTX 5070 review videos</div>",
        "<p>This video discusses captcha systems in web security</p>",
        "",
    ],
)
def test_ordinary_content_is_not_a_challenge(markup: str) -> None:
    """A false positive stops automation for no reason, so the bar matters.

    The second case is the one to get right: a page *about* CAPTCHAs is not a
    CAPTCHA, and matching the bare word would stop automation on any security
    article.
    """
    assert challenge_in(markup) is None


# -- what it does about it -------------------------------------------------
def test_the_challenge_is_raised_not_solved() -> None:
    """There is no solver, and no code path that continues past one."""
    with pytest.raises(ChallengeDetected) as raised:
        describe_challenge('<div class="h-captcha"></div>')

    message = str(raised.value).lower()
    assert "you" in message, "the message must hand the task to the user"


def test_the_message_says_what_to_do_and_that_jarvis_will_not_do_it() -> None:
    with pytest.raises(ChallengeDetected) as raised:
        describe_challenge('<iframe src="https://www.google.com/recaptcha/api2/anchor">')

    message = str(raised.value)
    assert "hcaptcha" not in message.lower()
    assert "recaptcha" in message.lower(), "name what was found"
    assert "will not" in message.lower() or "cannot" in message.lower()


def test_no_solving_or_bypassing_function_exists() -> None:
    """Structural, because this is a prohibited capability (§11.1).

    A helper that "just clicks the checkbox" is a CAPTCHA bypass regardless of
    what it is called, and it would be a route past a boundary the PRD says has
    no implementation.
    """
    import jarvis.toolbox.captcha as module

    forbidden = {
        name
        for name in dir(module)
        if not name.startswith("_")
        and any(verb in name.lower() for verb in ("solve", "bypass", "answer", "click", "defeat"))
    }
    assert not forbidden, f"{sorted(forbidden)} would be a CAPTCHA bypass"


def test_clean_content_passes_through_untouched() -> None:
    describe_challenge("<div>ordinary results</div>")  # must not raise
