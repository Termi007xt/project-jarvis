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
