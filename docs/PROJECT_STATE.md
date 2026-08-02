# Project State

## Snapshot
- **Last updated:** 2026-08-02
- **Current branch:** `feat/PHASE-1-development`
- **HEAD commit:** `df4a35b` — Phase 1 documentation baseline; working tree clean
- **Active phase:** **Phase 1 — voice-first local assistant, in progress**
- **Overall status:** Green. Phase 0 baseline re-verified on this branch:
  `python -m pytest` → **386 passed in 8.01s**, exit 0. Nothing blocked.

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

| Stage | Contents | Work items |
|---|---|---|
| 1 — Unblock | Approval dialog, DPAPI secret store, global hotkeys, startup-at-sign-in, `--require-healthy` | P1-SEC-01, P1-SEC-02, P1-UI-02, P1-COR-03 |
| 2 — Converse | Ollama chat with structured tool calls, model routing, bounded context, source labelling, tool-grounded success, history and private session, Conversation screen | P1-LLM-01…03, P1-COR-01, P1-COR-02, P1-MEM-01…03, P1-UI-01 |
| 3 — Voice | TTS (Kokoro) → STT (faster-whisper) → capture, ring buffer, VAD, full-duplex barge-in → wake word with per-user enrolment and measurement | P1-AUD-01…09 |
| 4 — Act | The six initial approved tools: open application, open URL, media control, volume control, speak, notify | P1-APP-01, P1-BRW-01, P1-WIN-01, P1-UI-03 |

**Delivery mode decided 2026-08-02:** continuous run to the end of the phase, no
intermediate approval checkpoints. Two exceptions are unavoidable and are named
in "Decisions Requiring Attention" below: ADR-0029 must be accepted before any
launcher code is written, and the wake-word base model must be obtained before
stage 3's wake detector can be built.

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
Phase 1 stage progress is tracked in the objective table above.

## In Progress
Phase 1, stage 1. See "Next Exact Steps".

## Blocked or Failing
No test is failing. Three things discovered on 2026-08-02 that the Phase 0
handoff did not record, each of which gates part of Phase 1:

1. **Process creation is denied build-wide, so the application launcher cannot
   be written yet.** `tests/security/test_no_shell.py` forbids `subprocess`,
   `os.startfile`, `ShellExecute*`, `CreateProcess*` and `multiprocessing`, and
   its `ALLOW_LIST` is empty. On Windows there is no way to launch Brave, Xbox or
   Sea of Thieves without one of them, so Phase 1 exit criterion 3 depends on
   **ADR-0029** being accepted first. The test file anticipated exactly this.
2. **The project virtual environment contains no audio stack.** `.venv` holds
   only PySide6, pydantic, PyYAML and pytest. faster-whisper, Kokoro, torch,
   sounddevice, soundfile and onnxruntime exist only in `tools/voice-lab/.venv`,
   which is a research spike outside the product runtime. Decided 2026-08-02:
   they enter as an **optional `voice` extra with lazy imports**, so CI, Linux
   and the hardware-free test rule in ARCHITECTURE §11 all still hold, and a
   missing provider produces an honest degraded state (ADR-0010, NFR-014).
3. **`openwakeword` is installed nowhere and no wake-word artefact exists.**
   Stage 3 cannot build a detector until the pretrained "Hey Jarvis" base model
   is obtained and its provider, licence, size and install location are recorded
   per PRD §17.2. Consistent with ADR-0016; restated here because it is a
   concrete acquisition task with a network download, not a code task.

## Tests and Quality Checks
- **Last successful:** `python -m pytest` → 386 passed (2026-08-02).
  Per suite: unit 201, security 97, integration 24, ui 26, acceptance 38.
- **Last failed:** none.
- **Not yet run:** GitHub Actions CI (workflow committed, never executed);
  Linux; Python 3.12; `pip-audit`.
- **Known limitations:** no test requires Ollama, a microphone, a GPU or the
  network, so nothing in the suite proves real-hardware audio behaviour. Phase 1
  will need on-hardware verification that unit tests cannot provide. Coverage is
  lowest in `jarvis/ui/app.py` (46%) and `single_instance.py` (61%, the
  Windows-mutex branch is untested because the suite forces the lock-file path).

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

**Stage 1 — unblock.** Nothing beyond the two self-inspection grants can run
until this exists.

1. **Approval dialog** (`ApprovalPort` → Qt, tray-anchored, non-modal) per
   ADR-0027: the PRD §11.2 field set, the offered-scope table by risk, the
   timeout-as-denied path, the "Don't ask again for this application / folder"
   scoped `DENY`, tray `BLOCKED` while pending, and a keyboard route to a pending
   request (NFR-030).
2. **DPAPI secret store** per ADR-0030, with `tests/security/test_secret_store.py`
   proving a secret never reaches plaintext configuration or the audit log.
3. **Global hotkey infrastructure**: `Ctrl+Alt+Pause` emergency stop and F9
   push-to-talk, both configurable, registered off the Qt thread, degrading
   honestly when a hotkey is already owned by another process.
4. **Startup-at-sign-in setting** (FR-002) and **`--require-healthy`** on
   `jarvis.main`, each with a test.

**Stage 2 — converse.** Ollama chat restricted to structured tool calls,
model-role routing, bounded multi-turn context, source labelling, tool-grounded
success, conversation history with global and per-conversation disable, private
session mode, and the live Conversation and Home screens.

**Stage 3 — voice.** TTS first (Kokoro `bm_george`, lang `b`, 24 kHz), then STT
(faster-whisper `small`, CPU, `int8`, `beam_size=1`, `vad_filter=True`), then
capture with the in-memory ring buffer, VAD and full-duplex barge-in per
ADR-0028, then the wake detector and per-user enrolment with measurement per
ADR-0016. Settings port from `tools/voice-lab/`, which is verified on hardware.

**Stage 4 — act.** The six initial approved tools from PRD §21: open approved
application, open approved website, media control, volume control, speak, notify.
Blocked on item A above.

Phase 1 exit criteria are in `docs/BACKLOG.md` §4 and PRD §21.

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
