# Project State

## Snapshot
- **Last updated:** 2026-08-02
- **Current branch:** `main`
- **HEAD commit:** `79037db` — Phase 0 committed; working tree clean
- **Active phase:** Phase 0 closed and user-accepted → **Phase 1 ready to start**
- **Overall status:** Green. 386/386 tests pass. Phase 0 acceptance testing passed. Nothing blocked.

## Current Objective
Begin **Phase 1 — voice-first local assistant**. All eleven open questions from
the Phase 0 handoff were answered on 2026-08-02 and are recorded below and in
ADR-0016, ADR-0027 and ADR-0028. **Phase 1 implementation has not started.**

Start with the **approval dialog**: it gates every capability beyond the two
self-inspection grants, so nothing else in Phase 1 can be exercised until it exists.

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

## In Progress
Nothing. Phase 1 has not begun.

## Blocked or Failing
Nothing is blocked and no test is failing.

**Known gap carried into Phase 1:** no wake-word model file exists on this
machine. This is now a deliberate design decision, not an omission — see
ADR-0016, per-user enrolment.

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
1. **Approval dialog** (`ApprovalPort` → Qt, tray-anchored, non-modal) per
   ADR-0027, with the timeout-as-denied path and the "Don't ask again" scoped
   deny. This unblocks every other capability.
2. **Obtain the pretrained openWakeWord "Hey Jarvis" base model** — none exists
   on this machine. Record provider, licence, size and install location per PRD
   §17.2. Then build enrolment on top of it: record samples → fit a personal
   verifier → **measure** → only then enable always-listening (ADR-0016, Path 1).
3. **Audio worker with full-duplex capture** per ADR-0028 — playback-aware gating
   first, then acoustic echo cancellation, with the half-duplex degradation path
   actually implemented.
4. **STT and TTS providers** behind the `SttProvider` / `TtsProvider` protocols,
   porting the verified settings from `tools/voice-lab/` (faster-whisper `small`,
   CPU, `int8`, `beam_size=1`, `vad_filter=True`; Kokoro `bm_george`, lang `b`,
   24 kHz).
5. **Add `--require-healthy`** to `jarvis.main` with a test.
6. **Global hotkeys**: F9 push-to-talk, `Ctrl+Alt+Pause` emergency stop, both
   configurable.

Phase 1 exit criteria are in `docs/BACKLOG.md` §4 and PRD §21.

## Uncommitted or Temporary State
Working tree is clean at `79037db`. New since that commit: ADR-0016 (rewritten),
ADR-0027, ADR-0028, and this file.

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
