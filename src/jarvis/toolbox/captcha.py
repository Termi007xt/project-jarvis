"""Stopping at an anti-bot challenge, and handing it to the user (FR-058).

Phase 2 stage 3. This module is a **boundary, not a feature**. `PRD.md` §11.1
lists CAPTCHA bypass among the capabilities that have no implementation by
design, so there is deliberately nothing here that solves, clicks, answers or
works around a challenge — only something that notices one and stops.

`tests/unit/test_captcha_pause.py` asserts that structurally, because "just tick
the checkbox for the user" is a bypass whatever it is named, and it would be a
route past a boundary the PRD says is closed.

**Why reading untrusted page content is acceptable here.** Detection works from
markup, which is attacker-controlled, and everywhere else in this codebase that
would be a problem. The difference is the direction it can push. Untrusted
content making Jarvis *more* cautious is safe; untrusted content making it *less*
cautious is the entire prompt-injection problem. A hostile page can stop
automation by impersonating a CAPTCHA — which costs it nothing it could not
achieve by simply showing a real one — and it cannot start anything by
impersonating a clean page, because a clean page is what automation already
expects.

Pausing works because the browser is a real, visible Brave window the user can
take over with their own mouse and keyboard, which is one of the reasons
ADR-0019 chose the installed browser over a headless one.
"""

from __future__ import annotations

import re

__all__ = ["ChallengeDetected", "challenge_in", "describe_challenge", "CHALLENGE_SIGNATURES"]


class ChallengeDetected(RuntimeError):
    """An anti-bot challenge is on screen. Automation stops here."""


#: Markers for challenges, as a name and the pattern that finds it.
#:
#: These match *structure* — an element, a script host, an interstitial title —
#: rather than the bare word "captcha", which would stop automation on any
#: article about web security. A false positive is not harmless: it halts a task
#: the user asked for, and tells them to complete a challenge that is not there.
CHALLENGE_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("reCAPTCHA", re.compile(r"google\.com/recaptcha|g-recaptcha", re.I)),
    ("hCaptcha", re.compile(r"\bh-captcha\b|hcaptcha\.com", re.I)),
    ("Cloudflare", re.compile(r"cf-challenge|cf_chl_|<title>\s*just a moment", re.I)),
    ("Turnstile", re.compile(r"cf-turnstile|challenges\.cloudflare\.com", re.I)),
    ("unusual traffic", re.compile(r"unusual traffic from your computer", re.I)),
    ("a CAPTCHA form", re.compile(r"""id=["']?captcha[-_]?form""", re.I)),
)


def challenge_in(markup: str) -> str | None:
    """Name the challenge on the page, or ``None`` if there is not one."""
    if not markup:
        return None
    for name, pattern in CHALLENGE_SIGNATURES:
        if pattern.search(markup):
            return name
    return None


def describe_challenge(markup: str) -> None:
    """Raise if the page is a challenge. Returns nothing when it is not.

    Deliberately a raise rather than a boolean: a caller that ignores a returned
    ``True`` carries on into the challenge, whereas a caller that ignores an
    exception does not exist.
    """
    name = challenge_in(markup)
    if name is None:
        return
    raise ChallengeDetected(
        f"The site is showing a {name} check. Jarvis will not attempt to solve "
        "or work around one — that is a capability it does not have, by design. "
        "The browser window is yours: complete the check yourself, and then ask "
        "again."
    )
