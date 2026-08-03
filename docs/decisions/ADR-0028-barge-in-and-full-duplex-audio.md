# ADR-0028: Barge-in and full-duplex audio

- **Status:** Accepted (decided 2026-08-02)
- **Date:** 2026-08-02
- **Deciders:** Project owner
- **PRD reference:** FR-015, FR-010, FR-012, FR-013, §11.3
- **Phase:** 1

## Context

PRD FR-015 permits either behaviour: "Phase 1 **may** pause wake detection while
Jarvis is speaking. A later phase shall support 'Jarvis stop' or a global hotkey
to interrupt speech and automation."

The decision is to implement **barge-in immediately in Phase 1** rather than
taking the permitted half-duplex shortcut. Being able to interrupt an assistant
mid-sentence is the difference between a conversation and a monologue, and
retrofitting it later means rewriting the audio pipeline once it has dependants.

This has a real technical consequence that must be planned for rather than
discovered: the microphone stays open while text-to-speech is playing. Kokoro's
output leaves the speakers and re-enters the microphone. Without handling, Jarvis
hears itself, its own speech triggers the wake word or voice-activity detector,
and it interrupts itself in a loop.

## Decision

Implement full-duplex audio in Phase 1: capture continues during playback, and
wake-word detection plus voice-activity detection remain live while Jarvis
speaks. A detected wake phrase or speech onset during playback **stops playback
immediately** and begins capturing the new command.

Self-triggering is addressed in this order:

1. **Playback-aware gating (required).** The audio worker knows when it is
   speaking and which samples it emitted. Detections during playback are
   evaluated against that knowledge rather than accepted blindly. This is the
   minimum bar and is cheap.
2. **Acoustic echo cancellation (preferred).** Use the playback stream as a
   reference signal to subtract Jarvis's own voice from the captured audio.
   Windows provides AEC as part of its voice-capture processing; using the
   platform's is strongly preferred to writing one.
3. **Energy and similarity thresholds (fallback).** Raise the detection
   threshold during playback, and reject a detection whose audio closely matches
   what was just emitted.

If none of these achieves an acceptable self-trigger rate on the target hardware,
the honest fallback is to degrade to half-duplex — pause detection during
playback — **and say so in the GUI** (PRD NFR-014), not to ship a loop.

Barge-in is a distinct mechanism from emergency stop (PRD §11.3). Barge-in
interrupts *speech*; emergency stop halts *all automation* and releases every
lock. Barge-in must never be the only way to stop something consequential.

## Options considered

**Half-duplex (pause detection while speaking)** — explicitly permitted by
FR-015 and trivially avoids self-triggering, but the user cannot interrupt, and
the change later touches every audio consumer. Rejected.

**Full-duplex with AEC** *(chosen)* — natural interaction; cost is the echo
problem and a hardware-dependent tuning exercise.

**Hotkey-only interruption** — a global hotkey stops speech without any
always-open microphone. Simple and reliable, but it is not barge-in; it is a stop
button. Retained as a **complement**, not a substitute: the emergency-stop hotkey
already stops speech, and push-to-talk (F9, ADR-0027) gives a deterministic
interruption path when acoustic barge-in is unreliable.

## Enforcement

- A test must assert that starting playback does not stop capture.
- A test must assert that a detection attributed to Jarvis's own output does not
  trigger a wake event — a synthetic self-echo case.
- A test must assert that barge-in stops playback but does **not** release
  resource locks or cancel tasks, since that is emergency stop's job.
- The privacy rules do not relax: pre-wake audio stays in the in-memory ring
  buffer and is never written to disk (FR-012), and the recording indicator
  applies during barge-in capture exactly as elsewhere (FR-013).

## Consequences

### Positive
The assistant can be interrupted, which is what makes voice interaction tolerable
for anything longer than a sentence. The audio architecture is right from the
start rather than rewritten in Phase 4.

### Negative
Phase 1's audio worker is materially more complex than the half-duplex version
FR-015 would have allowed: concurrent capture and playback, a reference signal
path, and threshold tuning that is specific to the microphone, speakers and room.
Expect this to need real-hardware iteration that cannot be validated by unit tests.

### Residual risk
Self-triggering is a tuning problem, not a solved one. Open speakers at high
volume with a sensitive microphone can defeat cancellation. The measured
self-trigger rate must gate enabling barge-in by default, and the half-duplex
degradation path must actually be implemented rather than assumed unnecessary.

## Revisit when
Measured self-trigger rates are unacceptable on the target hardware, or Windows
AEC proves unavailable through the chosen capture library.

## Related
ADR-0016 (wake-word enrolment — the detector barge-in depends on),
ADR-0027 (push-to-talk F9 as the deterministic interruption path),
ADR-0015 (TTS providers — playback source), PRD FR-010, FR-012, FR-013, FR-015, §11.3.

---

## Amendment — 2026-08-04: the defences were tuned past the point of working

**Status:** Accepted. Recorded after the owner reported, from real use, "i am
not able to interrupt it for some reason."

The mechanism was never the problem. `jarvis.audio.playback.play` polls
`DuplexCoordinator.stop_requested` between 40 ms blocks, so an interruption
takes effect within one block of being requested. Nothing was requesting one.

**Defence 3 was a closed door, not a raised bar.** `PLAYBACK_SCORE_MULTIPLIER`
was 1.6. Against the shipped wake threshold of 0.6 that demanded a detection
score of 0.96 — a number openWakeWord effectively never produces. A raised
threshold has to stay reachable to be a threshold; at 1.6 acoustic barge-in
could not happen at all, and the code read as though it could. It is now 1.15.

**The echo comparison used two different instruments.** The self-echo test
measured our own *digital output samples* with `note_emitted_level` and rejected
any detection whose *microphone* level did not exceed it. Those are not the same
scale: a desk microphone hearing a person across a room is almost always quieter
than the RMS of a waveform on its way to the speakers, so the test rejected
genuine interruptions essentially every time while looking like a reasonable
heuristic.

The comparison is only meaningful between like and like. What the microphone
hears while Jarvis speaks and nobody else does *is* the echo floor, it is
measured with the same instrument on the same scale, and it is already
available — the pipeline sees every captured frame. `note_captured_level` now
records it per playback window, and a detection must exceed that floor by
`ECHO_MARGIN` (1.5) to be treated as somebody in the room. `note_emitted_level`
is kept for the measurement report and is no longer part of any decision.

### What this does not change

The gate stands: **the self-trigger rate is still unmeasured on real hardware**,
and nothing here claims otherwise. `describe_interruption` now states this on the
Voice screen rather than asserting that Jarvis is interruptible.

### What this adds

A keyboard route that does not depend on tuning at all. Acoustic barge-in needs
thresholds measured in a real room with real speakers; pressing a key does not,
and until the measurement exists the deterministic route is the one to trust:

- `Ctrl+Alt+End` (emergency stop) now interrupts speech **before** it stops the
  automation. It previously cancelled tasks and released locks while continuing
  to talk over the silence it had just created.
- **Stop speaking** in the tray menu interrupts speech and does nothing else.

The second is deliberately separate from emergency stop, for the reason this ADR
already gives: barge-in releases no locks and cancels no tasks, and conflating
"be quiet" with "stop everything" would make the quieter request destructive.
Acoustic barge-in additionally requires an open microphone, which means
listening turned on — a precondition that was not stated anywhere and is now
part of what the Voice screen reports.

Tests: `tests/unit/test_interruption.py`, `tests/ui/test_stop_speaking.py`.
