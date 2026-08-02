# Phase 1 — Voice-First Local Assistant

- **Status:** Stages 1–3 complete; **stage 4 not started and blocked**
- **Started:** 2026-08-02
- **Branch:** `feat/PHASE-1-development`
- **PRD reference:** §21 "Phase 1 — Voice-first local assistant"

This is a progress report, not a closing report. Phase 1 is **not** complete and
must not be recorded as such: two of its five exit criteria are unmet, and each
is unmet for a reason that is written down rather than worked around.

---

## 1. Delivery shape

Decided with the project owner on 2026-08-02, before implementation:

| Decision | Choice |
|---|---|
| Sequencing | Continuous run through the phase, no intermediate approval checkpoints |
| Audio dependencies | Optional `voice` extra with lazy imports, not core dependencies |
| Launcher security | Draft ADR-0029 up front for acceptance, rather than discovering the blocker mid-stage |

The phase was structured as four stages, ordered by dependency: nothing beyond
the two self-inspection grants could run until the approval dialog existed, and
voice is only useful once there is something to talk to.

---

## 2. Exit criteria (PRD §21, verbatim)

| Exit criterion | Status | Evidence |
|---|---|---|
| "Jarvis" or configured fallback reliably starts a command in the test environment | **Partially met** | Push-to-talk (F9) starts a command and is tested. Wake-phrase activation does **not** work: no openWakeWord base model exists (ADR-0016), which is reported honestly rather than faked. |
| User can converse locally | **Met for text** | Live turn against `qwen3.5:9b-q4_K_M`: the model answered, proposed a registered tool, the invoker ran it, and the reply came back source-labelled. Voice-driven conversation is not wired end to end. |
| User can open Brave, YouTube, YouTube Music, Xbox, and Sea of Thieves | **Not met — blocked** | Requires a process-creation call site. `tests/security/test_no_shell.py` denies every such primitive and its `ALLOW_LIST` is empty. **ADR-0029 must be accepted first.** |
| User can stop listening and stop all automation | **Met** | Emergency stop from the tray, the Home screen and the configurable `Ctrl+Alt+Pause` global hotkey; it also denies any pending approval. Listening stops and clears the ring buffer. |
| No network is used in offline mode | **Met** | Offline mode opens no socket, in the chat adapter as well as the health checker; AT-001 remains a structural property. |

---

## 3. What was built

**Stage 1 — unblock.** The approval dialog and its queue (ADR-0027): tray-anchored
and non-modal so asking never steals focus from the automation being asked about;
an unanswered request expires as **denied**; `answer()` refuses any scope the
request did not offer, so a UI defect cannot widen a high-risk grant; denials can
be remembered as scoped `DENY` grants. A DPAPI secret store (ADR-0030). Global
hotkeys on their own message-loop thread. Start-at-sign-in via the per-user `Run`
key. `--require-healthy`.

**Stage 2 — converse.** Ollama chat where free text and structured tool calls are
separate fields and nothing promotes one into the other. Model-role routing that
now *enforces* sequential loading rather than declaring it. Bounded context and
bounded tool rounds. FR-047 source labelling and FR-048 tool-grounded success,
enforced on the way out rather than requested of the model. History with global
and per-conversation disable, and private sessions that write nothing at all.
Personality profiles whose proposals change nothing until accepted.

**Stage 3 — voice.** Capture, the pre-wake ring buffer, VAD with room
calibration, faster-whisper transcription, Kokoro synthesis, the full-duplex
coordinator, and the Voice screen. Schema v2 and v3.

---

## 4. Important implementation details

1. **The ring buffer cannot write to disk.** It has no path parameter, no
   `open`, no serialisation, and a test AST-scans the module to keep it that
   way. FR-012 and AT-002 are structural rather than conditional.
2. **STT never takes a filename.** faster-whisper accepts one, which makes
   writing a temporary WAV per utterance the *convenient* implementation and a
   silent breach of FR-025. The in-memory array path is used and the module says
   why.
3. **Redaction happens before synthesis, not after.** Speaking a password is not
   recoverable by apologising (FR-034).
4. **A read-only tool result is a tool result, but never licenses a success
   claim.** `not_applicable` means nothing changed, so there was nothing to
   verify; the observation is real, but it cannot support "I opened Brave".
5. **The approval queue denies until a UI attaches.** Otherwise `--check` and the
   headless engine would wait out the full timeout for an answer nobody can give.
6. **Audio dependencies are optional and lazily imported**, enforced by an AST
   test, so the engine still imports on Linux with no voice stack.

---

## 5. Tests executed

`python -m pytest` → **617 passed, 2 skipped** (Phase 0 baseline: 386 passed).
The two skips are the non-Windows branches of the secret store.

Verified outside the suite, on this machine:

- `python -m jarvis.main --check` → schema v3, secret store available, voice
  stack reported honestly, Ollama reachable, exit 0.
- A live conversation turn against the configured planner model.
- Kokoro `bm_george` synthesised 5.35 s of audio; faster-whisper `small`
  transcribed that audio back **exactly**; FR-034 redaction removed a key before
  synthesis; six input devices enumerated.

**Not run:** GitHub Actions CI, Linux, Python 3.12, `pip-audit`, and any test
using a real microphone.

---

## 6. Defects found and fixed during the phase

Four were found by running things rather than by reading code, which is the
reason they are listed separately:

1. **Deleted history was still readable in the database file.** SQLite `DELETE`
   unlinks a row but leaves its bytes in free pages. `PRAGMA secure_delete` is
   now on. Found by asserting AT-014 against the vault's raw bytes.
2. **The wake detector was never reset after a detection**, so the frames that
   produced it kept scoring high and one utterance woke Jarvis repeatedly.
3. **A read-only tool result was labelled "inference"**, understating a real
   observation. Found by running a live turn.
4. **The completion detector matched the bare word "done"**, so the model's
   correct refusal of "delete all my files" was prefixed with a confusing
   disclaimer. Also found by running a live turn.

Two pre-existing Phase 0 defects were also fixed: `split_statements` stripped SQL
comments *after* splitting on `;`, so a semicolon inside a comment fed English
prose to SQLite; and an acceptance test compared the JSONL record of truth against
the SQLite index across two reads while a worker was still writing.

---

## 7. Known limitations

1. **No wake-word model exists**, so wake activation does not work. Everything
   around it is built and reports the absence honestly, including the path it
   expects. Push-to-talk is the route (ADR-0027).
2. **Per-user enrolment is not built.** The measurement types and the quality
   bar exist and are tested; the recording flow and verifier fitting do not.
3. **Barge-in is unmeasured on real hardware.** ADR-0028 makes the measured
   self-trigger rate the gate on relying on it. The hooks exist; the tuning
   exercise has not been done, and barge-in must not be called reliable yet.
4. **Nothing has been tested with a real microphone end to end.** Capture, wake,
   VAD and barge-in are exercised against synthetic frames only.
5. **The Voice screen reports but does not yet drive.** Its signals exist; test
   meter, calibration and preview are not connected to `VoiceService`.
6. **No tools were added in this phase.** `system.health` is still the only
   registered tool, so the approval dialog is exercised by tests rather than by
   a real capability.
7. **Kokoro downloads a spaCy model on first use.** Observed during
   verification. This is a runtime network download and needs recording under
   PRD §17.2 alongside the wake-word model.
8. **P1-AUD-10 (Qwen3-TTS worker) is deferred out of Phase 1**: it needs a
   cross-Python-version process boundary, `multiprocessing` is denied, and it
   ships disabled.

---

## 8. Blocking decisions

| # | Item | Blocks |
|---|---|---|
| A | **ADR-0029** — the single authorised process-creation call site. Status **Proposed**. | All of stage 4's launcher work; PRD exit criterion 3; AT-003 |
| B | **openWakeWord "Hey Jarvis" base model** — must be obtained and its provider, licence, size and install location recorded (PRD §17.2). | Wake activation; enrolment; exit criterion 1 |

---

## 9. Relevant ADRs

Written in this phase: **ADR-0029** (approved-application launch, *Proposed*),
**ADR-0030** (secret store mechanism — DPAPI, *Accepted*, resolving ADR-0008's
"mechanism Open").

Implemented from earlier decisions: ADR-0027 (approval and activation),
ADR-0028 (barge-in and full-duplex, partially — the measurement gate is
outstanding), ADR-0016 (wake-word enrolment, partially — the base model is
missing), ADR-0010 (honest degraded UI, throughout).

---

## 10. Corrections

*None. Add dated corrections here if a later discovery invalidates a statement
above; do not silently edit the record.*
