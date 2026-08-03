# Phase 1 — Voice-First Local Assistant

- **Status:** All four stages implemented. **Awaiting user acceptance testing.**
- **Started:** 2026-08-02
- **Branch:** `feat/PHASE-1-development`
- **PRD reference:** §21 "Phase 1 — Voice-first local assistant"

This is a progress report, not a closing report. The code is complete and the
automated suite is green (**698 passed, 2 skipped**), but Phase 1 must not be
recorded as closed until the checks only a human can perform have been done —
above all speaking to a real microphone, which nothing in this report covers.

**What changed since the previous revision:** ADR-0029 was accepted, so stage 4
was built; the wake-word model bootstrap was added and the model installed and
measured on this machine.

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
| "Jarvis" or configured fallback reliably starts a command in the test environment | **Met in principle, unproven by voice** | The model is installed and the detector initialises. Measured against synthesised speech, "Hey Jarvis" scores 0.994–0.998 and unrelated speech ~0.000. **Nobody has yet spoken into a real microphone**, so "reliably" is not established. Push-to-talk (F9) is the verified route and registers live. |
| User can converse locally | **Met for text; voice loop not joined end to end** | Live turn against `qwen3.5:9b-q4_K_M`: the model answered, proposed a registered tool, the invoker ran it, and the reply came back source-labelled. Speech-in → answer → speech-out is not wired as one loop. |
| User can open Brave, YouTube, YouTube Music, Xbox, and Sea of Thieves | **Built and unit-verified; not launched for real** | All five are catalogued and build the correct argument vector; Brave is found at its real path on this machine. AT-003 passes against a fake process probe. No application has actually been launched, deliberately — that opens windows on the user's desktop. |
| User can stop listening and stop all automation | **Met** | Emergency stop from the tray, the Home screen and the `Ctrl+Alt+Pause` global hotkey, which **registered successfully on real Win32**. It cancels tasks, releases locks, stops workers and denies pending approvals. |
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

**Stage 4 — act.** The six approved tools, on the single authorised
process-creation call site ADR-0029 permits, plus the one-time wake-model
bootstrap.

---

## 3A. The wake-word model

**Nothing is bundled.** ADR-0016 chose per-user enrolment partly to avoid
redistributing a trained artefact, and the pretrained openWakeWord models carry
a **non-commercial** licence besides. The model is fetched once, by explicit
user action, through the library's own official API.

| | |
|---|---|
| Install | `python -m jarvis.main --install-wake-model` (or the Voice screen button) |
| Remove | `python -m jarvis.main --uninstall-wake-model` |
| Location | `%LOCALAPPDATA%\ProjectJarvis\models\wake\` |
| Files | `hey_jarvis_v0.1.onnx`, `melspectrogram.onnx`, `embedding_model.onnx`, `silero_vad.onnx` |
| Source | `openwakeword.utils.download_models`, official release assets |
| Framework | **ONNX** on Windows, passed explicitly — the library defaults to tflite |
| Provider | openWakeWord (dscripka), pretrained release v0.5.1 |
| **Licence** | **CC BY-NC-SA 4.0 — non-commercial.** Must not be included in any commercial or public distribution without resolving licensing first, either by obtaining different terms or by training a replacement. |

Installation is idempotent, shows the destination path, and is gitignored.
`--check` reports the model as installed **only after the detector actually
initialises**; files present but unloadable is reported as a failure and the
install command exits non-zero.

### Measured detection (synthesised speech, not a microphone)

Kokoro `bm_george` audio fed straight into the detector. This says nothing
about this room or this microphone — it answers the FR-011 question.

| Set | Scores | Detected at 0.6 |
|---|---|---|
| "Hey Jarvis" (6 phrasings) | 0.994 – 0.998 | 6/6 |
| Bare "Jarvis" (4 phrasings) | 0.268 – 0.464 | **0/4** |
| Unrelated speech (5) | 0.000 – 0.002 | 0/5 |
| Near-miss "Hey Travis" | **0.489** | 0/1 |

Two conclusions, both acted on:

1. **Bare "Jarvis" does not work, empirically.** FR-011's prohibition on
   implying otherwise is now backed by measurement rather than by assertion.
   The Voice screen says so; the phrase remains "Hey Jarvis".
2. **The default threshold was raised from 0.5 to 0.6.** "Hey Travis" at 0.489
   left only 0.011 of margin. 0.6 keeps every genuine utterance — the weakest
   was 0.994 — and roughly doubles the margin against the closest confusable
   phrase.

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

`python -m pytest` → **698 passed, 2 skipped** (Phase 0 baseline: 386 passed).
The two skips are the non-Windows branches of the secret store.

Verified outside the suite, on this machine:

- `python -m jarvis.main --check` → schema v3, secret store available, **all
  four voice components available**, wake detector initialising, six
  applications catalogued, Ollama reachable, exit 0.
- A live conversation turn against the configured planner model.
- Kokoro `bm_george` synthesised 5.35 s of audio; faster-whisper `small`
  transcribed that audio back **exactly**; FR-034 redaction removed a key before
  synthesis; six input devices enumerated.
- Wake-model install, re-install (idempotent) and detection measurement.
- **Stage 4 on real hardware:** Brave found at its real path with the right
  argv; Store AUMIDs producing the correct broker vector; process verification
  distinguishing a running process from a bogus one; volume down/up and
  play/pause accepted by Windows; an unapproved application and a `file:` URL
  both refused; emergency stop reporting what it stopped; startup-at-sign-in
  writing and removing the per-user `Run` entry; and **both `Ctrl+Alt+Pause`
  and `F9` registering live on Win32**.

**Not run:** GitHub Actions CI, Linux, Python 3.12, `pip-audit`, any test using
a real microphone, and any actual application launch (deliberately — it opens
windows on the user's desktop, so it belongs in user acceptance testing).

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

These are what stands between "implemented" and "accepted". None is hidden in
the GUI: each surfaces as an honest degraded state.

1. **Nothing has been spoken into a real microphone.** This is the single
   largest gap. Capture, wake detection, VAD and barge-in are exercised against
   synthetic frames and synthesised speech only. Until someone talks to it, the
   word "reliably" in exit criterion 1 is not earned.
2. **Barge-in self-trigger rate is unmeasured.** ADR-0028 makes that
   measurement the gate on relying on barge-in. The hooks exist
   (`DuplexCoordinator.measurement_summary`); the tuning exercise has not been
   done, and the honest half-duplex fallback is implemented for when it is.
3. **Per-user enrolment is not built.** The measurement types, the threshold
   fitting and the quality bar exist and are tested; the recording flow and the
   personal verifier do not. The shipped threshold (0.6) is a measured default,
   not a personal one.
4. ~~**The voice loop is not joined end to end.**~~ **Resolved 2026-08-03** —
   see section 11. Microphone → transcript → planner is now one path, and the
   loop was verified without a microphone by feeding synthesised speech through
   the pipeline: `capturing_command → transcribing → off`, transcript
   `"What is the time?"` at confidence 0.75.
5. ~~**The Voice screen reports but does not drive.**~~ **Resolved 2026-08-03**
   — see section 11. This was worse than recorded here: the controls were
   *enabled* and connected to nothing, which ADR-0010 forbids outright.
6. **No application has actually been launched.** Deliberate: it opens windows
   on the user's desktop. The vectors are verified, the process probe works, and
   AT-003 passes against a fake.
7. **Media and volume report `unverified`, correctly.** Whether Spotify acted on
   a play/pause key is not observable from here, so it is not claimed.
8. **Kokoro downloads a spaCy model (`en_core_web_sm`, ~12.8 MB) on first use.**
   Observed during verification. A runtime network download that needs
   recording under PRD §17.2 alongside the wake-word model.
9. **The wake model is non-commercially licensed** (CC BY-NC-SA 4.0). Fine for
   personal use; a blocker for any public or commercial distribution, and
   recorded as such in ADR-0016's neighbourhood, the CLI, the Voice screen and
   `.gitignore`.
10. **P1-AUD-10 (Qwen3-TTS worker) is deferred**, with the project owner's
    agreement: it needs a cross-Python-version process boundary,
    `multiprocessing` is denied, and it ships disabled. Kokoro `bm_george`
    remains the working provider.

---

## 8. Decisions taken during the phase

| # | Item | Outcome |
|---|---|---|
| A | **ADR-0029** — the single authorised process-creation call site | **Accepted** by the project owner, who directed that the exception must not be broadened. Two tests enforce that: the allow-list holds at most one entry, and exactly one module imports `subprocess`. |
| B | **openWakeWord "Hey Jarvis" model** | **Installed** via the official API, measured, and documented. Never bundled or committed. |
| C | **Qwen3-TTS (P1-AUD-10)** | **Deferred** out of Phase 1 with the owner's agreement. |

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

**2026-08-03 — this report overstated Phase 1.** The project owner's first
acceptance session found that the Conversation screen produced no reply and that
no button on the Voice screen did anything. Both were real. Investigating them
found four more defects, two of which are honesty failures of the kind this
project treats as more serious than crashes.

The common thread is a testing gap, not a coding one. Every unit under the GUI
was tested and passed. **Nothing tested the seam between them**, so a screen
that emitted a signal into the void and an engine that was never called both
looked healthy. `tests/ui/test_conversation_screen.py` passed in full while the
screen was completely non-functional.

The specific claim to withdraw: section 4 reported the voice stack as working on
the strength of the providers working. Speaking was never audible, because
**there was no audio playback anywhere in the product**.

---

## 11. Post-review defects found and fixed (2026-08-03)

| # | Defect | Root cause | Regression test |
|---|---|---|---|
| 1 | Conversation produced no reply, no GPU load and no log line | `ConversationWorker` was a local with no parent QObject; PySide6 destroyed it when `send_message` returned. The thread started, emitted `started`, and the receiver no longer existed. Nothing raised, so nothing was logged | `test_conversation_wiring.py::test_sending_a_message_actually_reaches_the_engine` |
| 2 | "Thinking…" reverted to "Ready" mid-turn | The 2-second window refresh called `set_availability`, re-enabling input and overwriting the status | `::test_a_turn_in_flight_is_not_re_enabled_by_a_refresh` |
| 3 | Quitting during a reply took the process down natively (`0xC0000409`), not by exception | Shutdown never waited for the conversation thread | `::test_quitting_mid_turn_stops_the_thread_rather_than_abandoning_it` |
| 4 | No Voice screen control did anything; F9 always answered "not available on this machine" while the stack was fully installed | `JarvisApplication.voice` was never assigned, and the panel's signals had no receivers. Enabled controls wired to nothing — an ADR-0010 violation | `test_voice_wiring.py::test_every_enabled_button_on_the_voice_screen_has_a_receiver` |
| 5 | **`voice.speak` reported "Spoken." as `verified` while the room stayed silent** | No playback existed. `VoiceService.speak` synthesised audio and returned it; its docstring said "Playback is the shell's job" and no shell ever did it | `tests/unit/test_speak_tool.py::test_audio_that_was_never_played_is_a_failure_not_a_success` |
| 6 | Offline mode still made a network request | Kokoro and faster-whisper resolve weights through `huggingface_hub`, which contacts the Hub on load. Observed as "You are sending unauthenticated requests to the HF Hub" — a real remote request from a component presented as local, contrary to AT-001 | `tests/security/test_offline_speech_models.py` |

**Defect 5 is the most serious.** A tool reporting `verified` success for
something that did not happen is the exact failure FR-048 exists to prevent, and
it reached the transcript wearing a "confirmed by a tool" label. It survived
because the tool's tests asserted it returned successfully, never that it
produced sound.

### What was added

- `jarvis.audio.playback` — the missing half of the stack. Interruptible
  between 40 ms blocks, which is what `DuplexCoordinator.stop_requested` was
  already documented as expecting ("polled by the playback loop"). Bounded at
  300 s. Reports seconds actually written to the device.
- `jarvis.ui.voice_controller` — joins the service to the shell: push-to-talk,
  the level meter, the recording indicator, device selection, microphone test,
  calibration and voice preview. Audio-thread callbacks only ever emit Qt
  signals; blocking work runs on daemon threads joined with a bound at shutdown.
- `jarvis.audio.model_hub` — pins the speech model hubs to their local cache in
  offline mode.
- Frame observers on `VoicePipeline`, and listener attachment after
  construction, because the service is built before there is a shell to hand
  commands to.

### Verified on real hardware

- **Playback**: 4.3 s of `bm_george` through output device 5. Redaction holds
  aloud — "my api key is sk-live-abcdef123456" was spoken as "my api key is a
  key".
- **The voice loop**, without opening the microphone: synthesised speech pushed
  through the pipeline as capture would deliver it gave
  `capturing_command → transcribing → off` and the transcript
  `"What is the time?"` at confidence 0.75, in 3.2 s.
- **Conversation through the GUI path**: a real reply from `qwen3.5:9b-q4_K_M`
  in the transcript, labelled `from the local model`.

### Correction to the acceptance guide

Push-to-talk was documented as "hold F9". It never could be: `RegisterHotKey`
delivers the press only, with no release event. It is press-to-start, and speech
ends on silence via the voice activity detector.

**Suite after these fixes: 745 passed, 2 skipped** (was 698). Security: 168
passed, 1 skipped.
