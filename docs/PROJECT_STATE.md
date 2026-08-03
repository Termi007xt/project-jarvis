# Project State

## Snapshot
- **Last updated:** 2026-08-04
- **Current branch:** `feat/PHASE-1-development`
- **HEAD commit:** `40fd50c` + uncommitted voice-behaviour fixes (round 6)
- **Active phase:** **Phase 1 — in user acceptance testing, round 6**
- **Overall status:** Amber, improving. `python -m pytest` → **907 passed,
  2 skipped** (Phase 0 baseline 386; 698 → 745 → 832 → 907). Nothing is blocked.

**Acceptance testing is running as rounds against real use**, each one reporting
defects that the unit suites did not catch. Rounds 1–5 are recorded in
`docs/phase-reports/PHASE-01-VOICE-FIRST.md` sections 10 and 11. Round 6
(2026-08-04) came from the owner's own list and covered four things:

1. **Emoji and formatting were being read out** — the phonemiser expands every
   character to its Unicode name, so "🦁" was spoken as "lion face".
   `speakable_text()` strips presentation before synthesis, and runs before
   redaction so markdown cannot hide a credential from the FR-034 patterns.
2. **Jarvis could not be interrupted**, for three independent reasons: an
   unreachable raised threshold (0.96 required), a self-echo test comparing a
   microphone level against our own output samples, and an emergency stop that
   never stopped speech. See the ADR-0028 amendment of 2026-08-04.
3. **It narrated instructions that spoke for themselves.** `audio.speak_replies`
   and `jarvis.audio.reply_policy` decide speak / cue / silent in code —
   deliberately not asked of the model, because that drift is invisible.
4. **"Open YouTube Music" opened a browser tab** rather than the installed web
   app. One catalogue entry, launched by app id; no new call site, so ADR-0029
   is untouched.

The owner's decision on the fifth item is recorded below: opening arbitrary
applications with first-use permission is **deferred**, not declined.

**The lesson, recorded so it changes behaviour:** every unit passed while the
product did not work, because nothing tested the *seam* between the GUI and the
engine. `tests/ui/test_conversation_screen.py` passed in full against a screen
that was completely non-functional. New wiring tests
(`tests/ui/test_conversation_wiring.py`, `tests/ui/test_voice_wiring.py`) assert
the connections, including a general rule: an enabled control either does
something or says why it cannot.

## Current Objective

**Phase 1 — voice-first local assistant.** Give Jarvis a voice: wire the audio
stack (wake phrase, push-to-talk, local STT, local TTS) to the Ollama-hosted
conversational model, ship the first six narrowly-scoped tools, and close the two
Phase 0 gaps that block any real interaction — the approval dialog and a
protected secret store. Nothing in this phase performs desktop or browser
automation beyond opening an approved application or URL.

Phase 1 is delivered as four ordered stages. The order is forced by dependency,
not preference: nothing requiring approval can run until stage 1 exists, and
voice is only useful once there is something to talk to.

| Stage | Contents | Work items | Status |
|---|---|---|---|
| 1 — Unblock | Approval dialog, DPAPI secret store, global hotkeys, startup-at-sign-in, `--require-healthy` | P1-SEC-01, P1-SEC-02, P1-UI-02, P1-COR-03 | **Done** |
| 2 — Converse | Ollama chat with structured tool calls, model routing, bounded context, source labelling, tool-grounded success, history and private session, Conversation screen | P1-LLM-01…03, P1-COR-01, P1-COR-02, P1-MEM-01…03, P1-UI-01 | **Done** |
| 3 — Voice | TTS (Kokoro), STT (faster-whisper), capture, ring buffer, VAD, full-duplex barge-in, wake detector and the Voice screen | P1-AUD-01…09 | **Done except per-user enrolment**, which is deferred; the shipped threshold is a measured default |
| 4 — Act | The six approved tools plus the one-time wake-model bootstrap | P1-APP-01, P1-BRW-01, P1-WIN-01, P1-UI-03 | **Done** |

**Delivery mode decided 2026-08-02:** continuous run to the end of the phase, no
intermediate approval checkpoints. Both blocking items were resolved during the
phase: **ADR-0029 was accepted** (with the direction that the exception must not
be broadened), and the **wake-word model was installed** through openWakeWord's
official API, measured, and documented.

### Deliberately deferred out of Phase 1

**P1-AUD-10** (Qwen3-TTS expressive worker, sized XL) is deferred. It is
`enabled: false` and `status: experimental` in `config/defaults.yaml`, it is the
product's first cross-Python-version process boundary, and `multiprocessing` is
denied by `tests/security/test_no_shell.py` — so it would consume the phase's
hardest engineering on a feature that ships turned off. Revisit alongside ADR-0015.

## Verified Working
Confirmed by passing tests or direct observation:

- `python -m pytest` → **386 passed, 0 failed**, 89% statement coverage.
- `python -m jarvis.main --check` → prints status, exits 0.
- Tray application runs on the native Windows platform; health-check task
  completes end-to-end through the full invoker pipeline.
- **User acceptance testing of Phase 0 passed** (2026-08-02) — all nine groups:
  tray and window, live data screens, settings persistence, single instance,
  audit log, crash recovery, emergency stop and degraded states, security
  invariants, environment robustness.
- All three configured Ollama models are installed and reachable:
  `qwen3.5:9b-q4_K_M`, `qwen3-vl:8b-instruct-q4_K_M`, `qwen3-embedding:0.6b`.
- **faster-whisper `small` transcribes real microphone input correctly** —
  verified by the user via `tools/voice-lab/test_whisper.py`.
- **Kokoro `bm_george` synthesises correctly** — verified via
  `tools/voice-lab/test_kokoro.py`. This also implies espeak-ng is installed and
  working, since Kokoro requires it for English phonemisation.

## Completed in Current Phase

Phase 0 is complete and closed. See `docs/phase-reports/PHASE-00-FOUNDATION.md`.

**All four Phase 1 stages are implemented, tested and committed.** Highlights
that change what the product can do:

- **The approval dialog exists**, so capabilities beyond the two self-inspection
  grants can finally run. Tray-anchored and non-modal (ADR-0027), timing out as
  denied, with rememberable scoped denials and a keyboard route (NFR-030).
- **A DPAPI secret store** (ADR-0030), verified by asserting the plaintext is
  absent from the database, the audit log and the configuration file after a
  round trip.
- **Text conversation works against the local model.** Free text and structured
  tool calls are separate fields and nothing promotes one into the other; every
  proposal goes through the invoker's six checks; every reply is source-labelled
  and cannot claim a success no tool verified.
- **The voice stack is verified on this hardware**: Kokoro `bm_george`
  synthesised 5.35s of audio and faster-whisper `small` transcribed it back
  exactly. Redaction removed a key before synthesis. Six input devices enumerate.
- **Storage now uses `PRAGMA secure_delete`.** Deleted conversation history was
  previously still readable in the database file.
- **Six approved tools exist**, on the single process-creation call site
  ADR-0029 authorises. Brave, YouTube, YouTube Music, Xbox and Sea of Thieves
  are catalogued; interpreters, unapproved applications and non-http URLs are
  all refused; a launch is only `succeeded` once the process is observed.
- **The wake-word model installs in one command** and is measured: "Hey Jarvis"
  scores 0.994–0.998, bare "Jarvis" 0.268–0.464 and is not detected — which
  confirms FR-011 empirically rather than by assertion.

## In Progress

Nothing is part-built. The phase is code complete and awaiting user acceptance
testing — see `docs/PHASE-01-ACCEPTANCE-TESTING.md`.

## Blocked or Failing

Nothing is blocked and no test is failing. The three items recorded here earlier
in the phase have all been resolved: ADR-0029 was accepted, the audio stack was
installed as the optional `voice` extra, and the wake-word model was obtained.

**What is unproven rather than blocked** — the distinction matters:

1. **The false-wake rate is unmeasured.** Wake detection has been exercised by
   hand but not counted over a normal hour of talking, which is what decides the
   threshold and whether always-listening is safe to leave on.
2. **Barge-in self-trigger rate is unmeasured**, which ADR-0028 makes the gate
   on relying on it. Until 2026-08-04 it could not have been measured at all —
   the thresholds made acoustic barge-in unreachable. The honest half-duplex
   fallback is implemented for if it proves unreliable, and the keyboard routes
   do not depend on the measurement.
3. **The Xbox and Sea of Thieves AUMIDs are unverified.** They build the correct
   broker vector, but launching them would open windows on the user's desktop,
   so it belongs in acceptance testing.

## Tests and Quality Checks
- **Last successful:** `python -m pytest` → **907 passed, 2 skipped** (2026-08-04).
  The two skips are the non-Windows branches of the secret store, which cannot
  run on this platform by definition.
- **Last failed:** none.
- **Verified outside the suite, on this machine:**
  - `python -m jarvis.main --check` → schema v3, secret store available, voice
    stack reported honestly, Ollama reachable, exit 0.
  - A live conversation turn against `qwen3.5:9b-q4_K_M`: the model answered,
    proposed a registered tool, the invoker ran it, and the reply came back
    correctly labelled.
  - Kokoro `bm_george` → 5.35s of audio; faster-whisper `small` transcribed that
    audio back **exactly**. FR-034 redaction removed a key before synthesis.
- **Not yet run:** GitHub Actions CI (workflow committed, never executed);
  Linux; Python 3.12; `pip-audit`.
- **Known limitations:** no test requires Ollama, a microphone, a GPU or the
  network, which is deliberate (ARCHITECTURE §11) but means the suite proves
  nothing about real-hardware audio; the smoke runs above are what covers that,
  and they are not automated. **Nothing has yet been tested with a real
  microphone end to end** — capture, wake, VAD and barge-in are exercised
  against synthetic frames only, and ADR-0028 is explicit that self-trigger
  rates need real-hardware iteration. Coverage is lowest in `jarvis/ui/app.py`
  and `single_instance.py`.

## Decisions Requiring Attention

### Settled 2026-08-02 — recorded, do not re-litigate

| # | Decision | Recorded in |
|---|---|---|
| 1 | Approval dialog scopes: Low = once/always/deny · Medium = once/task/deny · High = **once/deny only**. "Allow for this session" is not offered. | ADR-0027 |
| 2 | Denials are remembered on request: **"Don't ask again for this application / folder"** → a scoped `DENY` grant. No engine change needed. | ADR-0027 |
| 3 | Approval surface is **tray-anchored and non-modal** — must not steal focus during automation. Tray goes red while pending; unanswered requests **time out as denied**, never allowed. | ADR-0027 |
| 4 | Wake word: **per-user voice enrolment during onboarding.** User speaks their phrase, Jarvis trains a personal model, retrainable, multiple phrases supported. | ADR-0016 |
| 4a | Enrolment uses **Path 1** — pretrained base model + personal verifier. Path 2 (synthetic augmentation) deferred to after Phase 1. **Consequence: the Phase 1 phrase is "Hey Jarvis"**, because no pretrained base exists for bare "Jarvis". | ADR-0016 |
| 7 | `--check` keeps exit 0 when Ollama is unreachable; add a **`--require-healthy`** flag for non-zero. | this document |
| 8 | Push-to-talk hotkey is **F9**, bare, no modifier. Always-listening remains primary. | ADR-0027 |
| 9 | **Barge-in immediately** — full-duplex audio in Phase 1, not the half-duplex shortcut FR-015 permits. | ADR-0028 |
| 10 | Phase 1 runs **continuously to phase end**, with no intermediate approval checkpoints. | this document |
| 11 | Audio dependencies enter as an **optional `voice` extra with lazy imports**, not core dependencies. | this document, ADR-0010 |
| 12 | The application launcher gets **one authorised process-creation call site**, drafted up front rather than discovered mid-stage. | ADR-0029 |

### Awaiting acceptance — these gate code that is otherwise ready

| # | Item | Gates |
|---|---|---|
| A | **ADR-0029** — the single authorised `subprocess.Popen(argv_list, shell=False)` call site for launching approved applications, and the one `ALLOW_LIST` entry it adds to `tests/security/test_no_shell.py`. Written, status Proposed. | All of stage 4: P1-APP-01, P1-BRW-01. Phase 1 exit criterion 3. |
| B | **openWakeWord "Hey Jarvis" base model** — must be downloaded, and its provider, licence, size and install location recorded per PRD §17.2. | Stage 3's wake detector and enrolment (P1-AUD-01). Push-to-talk is unaffected and remains the fallback. |

**ADR-0030** resolves the "mechanism Open" status ADR-0008 left behind, selecting
DPAPI for the secret store. It is required before any settings field asks for a
credential.

### Two concerns raised but not yet answered

- **Bare F9 is a heavily used application key** (IDE debug controls, Excel
  recalculation, game bindings). A global hook on it will swallow F9 from every
  other application. PRD §11.3 requires the emergency-stop hotkey not to conflict
  with common shortcuts; the same reasoning applies here. Implement F9 as
  specified **and make it configurable**, then reassess after real use.
- **Wake-word enrolment is a genuine Phase 1 scope increase.** Even on Path 1 it
  adds a verifier-fitting step, an enrolment UI, sample storage with privacy
  rules, and a measurement harness.
- **Path 1 means Phase 1 ships "Hey Jarvis", not "Jarvis".** No pretrained base
  model exists for the bare word. FR-011 names "Jarvis" as the product default
  and explicitly forbids implying a "Hey Jarvis" model detects it — so the Voice
  screen must state the enrolled phrase truthfully and say that single-word
  detection needs the deferred Path 2 work. Do not quietly label it "Jarvis".

### Still open, gated by later phases

| Needed before | ADRs |
|---|---|
| Phase 2 | ADR-0018 search provider · ADR-0019 browser profile isolation · ADR-0023 adapter isolation |
| Phase 3 | ADR-0024 data-retention defaults |
| Phase 4 | ADR-0025 screenshot ceiling (default `task_only` accepted) |
| Phase 6 | ADR-0011 product name · ADR-0012 shell technology · ADR-0013 installer · ADR-0020 skill signing · ADR-0021 encrypted sync · ADR-0022 MSIX · ADR-0026 code signing and updates |

Partially settled: ADR-0014 default voice (Kokoro `bm_george` accepted; public
redistribution licensing still open), ADR-0015 TTS providers, ADR-0017 embedding
model (configured, not benchmarked).

**Nothing on this list blocks Phase 1.**

## Next Exact Steps

1. **The false-wake count.** Listening on, an hour of normal talking, how many
   times did it wake by mistake? This is the outstanding measurement and it
   decides two things: whether the 0.6 threshold stays, and whether
   always-listening is safe to leave on — which is also the precondition for
   acoustic barge-in, since a closed microphone cannot hear an interruption.

2. **Measure barge-in self-triggering**, now that the thresholds can actually be
   met. ADR-0028 makes this the gate on relying on barge-in. If the rate is
   unacceptable, degrade to half-duplex and say so in the GUI — that path is
   implemented, not assumed unnecessary. Until then the keyboard routes
   (`Ctrl+Alt+End`, tray **Stop speaking**) are the ones to trust, and the Voice
   screen says exactly that.

3. **A time tool.** "What time is it?" can currently only be answered by the
   model, which does not know. It is the most obvious thing to ask a voice
   assistant and the answer is a small, verifiable tool.

4. **Arbitrary application launching with first-use permission** — deferred by
   the owner on 2026-08-04 ("stability first"), not declined. It needs its own
   ADR before any code: Start-menu discovery as the source of executables
   (machine state, never model output), an approval on first use, persisted
   entries, a `.lnk` parser that runs no shortcut, and care around the
   `powershell.exe` entry every Start menu contains. ADR-0029 constraint 3 is
   preserved by construction — the model still names an *entry*, never a binary.
   Progressive web apps come free with it: they are ordinary fixed vectors.

5. **Per-user wake enrolment (ADR-0016 Path 1).** The measurement types,
   threshold fitting and quality bar exist and are tested; the recording flow
   and the personal verifier do not.

Phase 1 exit criteria are in `docs/BACKLOG.md` §4 and PRD §21. Of the five:
"no network in offline mode" and "stop listening and stop all automation" are
met and tested; "converse locally" is met for text; and the wake-phrase and
application-launch criteria are **built and unit-verified but not yet proven by
a human**, which is exactly what acceptance testing settles.

## Uncommitted or Temporary State
Phase 1 work is in progress on `feat/PHASE-1-development`, branched from
`df4a35b`. Nothing is stubbed to report false success; every unbuilt screen and
menu entry still names its phase (ADR-0010).

No temporary migrations or compatibility shims. No process needs to be running;
Ollama is optional. `tools/voice-lab/` and `tools/qwen-tts-lab/` are research
spikes outside the product runtime and are **not** covered by the security policy.

## Relevant References
- **Requirements:** `PRD.md` §21 (phases), §22 (AT-001…AT-034), §10.2–10.5 (Phase 1 FRs)
- **Phase 0 record:** `docs/phase-reports/PHASE-00-FOUNDATION.md`
- **Operating contract:** `CLAUDE.md`
- **Phase 1 decisions:** ADR-0016, ADR-0027, ADR-0028
- **Architecture:** `ARCHITECTURE.md` §8 (extension points — the protocols Phase 1 fills), §12, §13
- **Security:** `SECURITY.md` §14 (status table)
- **Threats:** `THREAT_MODEL.md` §5.4 (voice threats), §6 (Phase 0 residual risks)
- **Plan:** `docs/BACKLOG.md` §4 (Phase 1 work items)
- **Verified voice spikes:** `tools/voice-lab/test_whisper.py`, `tools/voice-lab/test_kokoro.py`
- **Graph:** `graphify-out/GRAPH_REPORT.md` — 121 communities; god nodes
  `JarvisCore` (100), `EventBus` (76), `ToolCall` (71), `AuditLog` (70), `Database` (62)
