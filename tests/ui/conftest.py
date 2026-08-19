"""Nothing in the suite opens the speakers.

Reported by the owner on 2026-08-06: a full `python -m pytest` says *"the time
is four o'clock"* out loud three or four times, and eats memory doing it.

Both come from the same place. `tests/ui/test_voice_reply_behaviour.py` builds a
real `JarvisApplication`, and three of its tests simulate a **spoken** command —
which is answered aloud by policy, correctly. The tests that assert *what* is
spoken replace `speak_reply` with a recorder; the three that assert something
else (the window does not raise, the engine is reached, a cue plays) had no
reason to, and so went all the way through Kokoro to the sound card. Loading
Kokoro pulls in torch, which is most of the memory as well.

The `application` fixtures already say "no test opens the speakers" and enforced
it only for cues. This closes the gap for every UI test at once rather than
per fixture, because the next test to build an application will not remember.

Speech is recorded rather than dropped: a test that wants to assert on it can
read `voice.spoken`, and one that replaces `speak_reply` itself still works.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def never_open_the_speakers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stop `speak_reply` before it reaches synthesis, for every UI test.

    Patched on the class, so it applies to voice controllers built later in the
    test — which is the case that matters, since the application constructs its
    own and a fixture cannot reach in beforehand.
    """
    try:
        from jarvis.ui.voice_controller import VoiceController
    except Exception:  # pragma: no cover - no Qt available, nothing to silence
        return

    def record_instead_of_speaking(self, text: str) -> None:
        self.spoken = [*getattr(self, "spoken", []), text]

    monkeypatch.setattr(
        VoiceController, "speak_reply", record_instead_of_speaking, raising=False
    )
