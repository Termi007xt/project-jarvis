# Project Jarvis — Implementation Backlog

**Document version:** 1.0
**Status:** Phase 0 baseline
**Companion documents:** [PRD.md](../PRD.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [SECURITY.md](../SECURITY.md), THREAT_MODEL.md (not yet written), DATA_MODEL.md (not yet written), [decisions/](decisions/)

This is the execution plan for Project Jarvis, phased as PRD §21 defines the
phases. It turns the product requirements (PRD §10, §19), the acceptance
tests (PRD §22) and the phase exit criteria (PRD §21) into a work item list
that can be tracked, reviewed and re-planned without re-deriving intent from
the PRD each time. It does not add scope the PRD does not contain, and it
does not estimate calendar time.

Component names used throughout match [ARCHITECTURE.md](../ARCHITECTURE.md)
exactly: `JarvisCore`, `ToolInvoker`, `PermissionEngine`, `TaskScheduler`,
`LockManager`, `EventBridge`, and the package names `jarvis.core`,
`jarvis.tasks`, `jarvis.audio`, `jarvis.automation`, `jarvis.llm`,
`jarvis.storage`, `jarvis.config`, `jarvis.ui`.

---

## 1. How to read this backlog

### 1.1 Work item IDs

Every work item has an ID of the form `P<phase>-<area>-<nn>`:

- `P<phase>` — the delivery phase from PRD §21: `P0` through `P6`.
- `<area>` — a three-letter code identifying the subsystem, from the table
  below.
- `<nn>` — a two-digit sequence number, unique within the phase and area. It
  does not imply execution order beyond what the `Depends on` column states.

Example: `P2-BRW-01` is the first browser-automation item in Phase 2.
`P1-AUD-03` is the third audio item in Phase 1.

### 1.2 Area codes

| Code | Area | Typical PRD source |
|------|------|---------------------|
| CFG | Configuration and storage foundation | §6.1 (see ARCHITECTURE), §14.1, §14.2, NFR-041, NFR-043 |
| COR | Core orchestration: event bus, tool contract/registry/invoker, runtime composition, single instance, emergency stop | §11, §12.2, §13 |
| SEC | Security, permissions, audit, threat-model review, adversarial safety testing | §11, §19.3, §23.3 |
| TSK | Task subsystem: state machine, locks, scheduler, checkpoints, scheduling and conditional automation | §10.11, §10.12, §10.25 |
| AUD | Audio: wake phrase, VAD, speech recognition, text-to-speech | §10.2, §10.3, §10.4 |
| LLM | Model management and routing | §10.5, §15 |
| APP | Application discovery, launch, lifecycle | §10.7 |
| WIN | Windows and application automation, window/desktop management, device and settings controls | §10.8, §10.19, §10.20 |
| BRW | Browser and media-site automation (Brave, YouTube, YouTube Music, AI websites) | §10.6, §10.9 |
| FS | Filesystem, document and media understanding, undo and recovery | §10.16, §10.17, §10.18 |
| CLP | Clipboard and text transformation | §10.21 |
| NTF | Notifications: Jarvis-originated and observed | §10.15, §10.22 |
| VIS | Screen context and vision fallback | §10.23 |
| WKS | Workspace and session save/restore | §10.24 |
| SKL | Skills and macros | §10.10 |
| MEM | Memory, personalisation, identity export/import | §10.14 |
| IDE | IDE-agent orchestration | §10.13 |
| UI | Interface: tray, main window, screens | §9 |
| PKG | Packaging, distribution, onboarding, productisation | §16, §17, §18 |
| DOC | Documentation artefacts | §21 |
| TST | Testing infrastructure and acceptance-test wiring | §22, §23 |
| OPS | Build, CI, release engineering | §21, NFR-023, NFR-024 |

### 1.3 Table columns

- **ID** — see §1.1.
- **Item** — a short description of the deliverable. Where an item bundles
  several closely related FRs, the bundling is deliberate: they share one
  component and one set of tests, and splitting them would not produce an
  independently shippable unit.
- **PRD refs** — the functional requirement (FR-xxx), non-functional
  requirement (NFR-xxx), acceptance test (AT-xxx) or section number that
  this item exists to satisfy. Every reference in this document was checked
  against the current text of `PRD.md`. Where an item has no FR of its own
  (foundation, glue, or GUI plumbing), the PRD section number is cited
  instead.
- **Depends on** — other work item IDs that must be `Done` (or, for
  same-phase parallel work, at least `Ready`) before this item can start.
  `—` means no in-backlog dependency.
- **Size** — effort, not time (the PRD forbids fabricated time estimates;
  see PRD §9.6, §27):
  - **S** — a single focused component or narrow tool, testable in
    isolation.
  - **M** — a component plus its integration points and tests; touches two
    or three modules.
  - **L** — a subsystem with multiple collaborating components,
    cross-cutting tests, and a non-trivial design decision.
  - **XL** — spans multiple subsystems or introduces a new worker/process
    boundary; expected to be split into sub-tasks during execution.
- **Status** — `Done`, `In progress`, `Ready`, `Blocked`, `Not started`.
  `Blocked` items name the blocker in the item description.

### 1.4 A note on the PRD's own numbering

PRD §10.4 contains a typographical slip: the requirement titled
"Multiple TTS providers" is printed as `R-035` rather than `FR-035` in the
source document, between `FR-034` and `FR-036`. This backlog cites it as
`FR-035` because the surrounding sequence makes the intended ID
unambiguous, and notes the discrepancy here rather than silently
correcting the PRD.

---

## 2. Cross-phase invariants

These rules apply to every work item in every phase, not only to the items
that introduce them. They are restated per phase only where a phase adds a
concrete mechanism for enforcing one.

1. **Every item ships with tests.** No work item is `Done` without an
   accompanying test at the appropriate level (unit, integration, security,
   UI, or acceptance — PRD §23, ARCHITECTURE §11). A feature with no test is
   not a completed backlog item, regardless of whether it demos.
2. **No item may introduce a generic execution primitive.** No work item,
   in any phase, may add a shell, script interpreter, or "do anything"
   tool. This is enforced structurally, not by review discipline: any tool
   name or call site that would violate it fails
   `tests/security/test_no_shell.py` and the tool-registry denylist (PRD
   §11.1 "Prohibited," §13.3, ARCHITECTURE §6.5).
3. **Every state-changing tool declares reversibility metadata.** Per
   FR-221, a tool that changes state must declare whether it is reversible,
   its rollback method, rollback expiry, required approval, and the
   information needed to restore prior state — at the point the tool is
   registered, not retrofitted later. This field exists on `ToolSpec` from
   Phase 0 (see P0-COR-02); every phase that adds a new state-changing tool
   must populate it.
4. **Every phase gate re-reviews THREAT_MODEL.md.** Before a phase is
   declared complete, the threat model is re-read against what the phase
   actually built, and any new attack surface (a new content source, a new
   automation target, a new external process) is either covered or recorded
   as an open risk. THREAT_MODEL.md does not yet exist (see P0-DOC-02); this
   invariant cannot be executed as a gate until it does, which is itself a
   Phase 0 exit risk (§3.5).
5. **No phase is complete until its PRD §21 exit criteria are
   demonstrated.** Not implemented, not merged — demonstrated, with an
   acceptance test or a recorded manual walkthrough tied to the specific
   exit-criterion sentence. Each phase section below reproduces its exit
   criteria verbatim from PRD §21 as a checklist for this purpose.

---

## 3. Phase 0 — Foundation and safety architecture

### 3.1 Goal

Build the parts of Jarvis that every later feature depends on and that
cannot be safely retrofitted: typed configuration, the permission and audit
boundary, the tool contract and invoker choke point, the task engine, and a
tray-and-window shell with no computer-control capability behind it at all.
Phase 0 exists specifically so that "no generic execution primitive" and
"every action is auditable" are structural properties of the codebase before
a single feature that could misuse them exists.

### 3.2 Exit criteria (PRD §21, verbatim)

- [ ] Application opens and sits in tray
- [ ] Settings persist
- [ ] Single-instance enforcement works
- [ ] Audit events are written
- [ ] Permission decisions are testable
- [ ] No generic shell exists anywhere in the runtime

### 3.3 Work items

| ID | Item | PRD refs | Depends on | Size | Status |
|----|------|----------|------------|------|--------|
| P0-CFG-01 | Layered typed configuration: defaults + user overrides + env, `extra="forbid"`, atomic writes | NFR-041 | — | M | Done |
| P0-CFG-02 | Vault path resolution: `%LOCALAPPDATA%` expansion, `JARVIS_DATA_DIR` relocation | §14.2, NFR-025 | P0-CFG-01 | S | Done |
| P0-CFG-03 | SQLite storage and versioned forward migrations, WAL, foreign keys | §14.1, NFR-043 | P0-CFG-02 | L | Done |
| P0-COR-01 | Typed event bus: subclass matching, thread-safe publish, handler isolation | NFR-041, §12.3 | P0-CFG-01 | M | Done |
| P0-COR-02 | Tool contract: `ToolSpec` with reversibility metadata (invariant §2.3) | §13.2, FR-221 | P0-COR-01 | M | Done |
| P0-COR-03 | Tool registry: denylist by identity and by pattern | §13.3, §6 non-goal 1 | P0-COR-02 | S | Done |
| P0-COR-04 | Tool invoker: six-step pipeline (allow-list, schema, permission, locks, approval, execute) | §13.4, §11.2 | P0-COR-03, P0-SEC-03, P0-TSK-03 | L | Done |
| P0-COR-05 | Model-resource `load_strategy: sequential` configuration stub | FR-039 (partial), §15.2 | P0-CFG-01 | S | Done |
| P0-COR-06 | Worker-thread supervision: off the Qt main thread, graceful stop | NFR-003, §12.2 | P0-COR-01 | M | Done |
| P0-COR-07 | Single-instance guard: named mutex, lock-file fallback | FR-005 | P0-CFG-02 | S | Done |
| P0-COR-08 | Emergency stop: cancel tasks, release locks, report what stopped | §11.3 | P0-COR-04, P0-TSK-03 | M | Done |
| P0-SEC-01 | Audit log with redaction: JSONL + SQLite dual sink, key/value redaction, truncation | §11.5, NFR-022 | P0-COR-01, P0-CFG-03 | M | Done |
| P0-SEC-02 | Capability catalogue: risk classification as data | §11.1 | — | S | Done |
| P0-SEC-03 | Permission engine: evaluation order, grant scopes, expiry, revocation, no `ALWAYS` for high risk | §11.1, §9.9 | P0-SEC-02 | L | Done |
| P0-TSK-01 | Task state machine: ten states, validated transition table | FR-122 | P0-CFG-03 | M | Done |
| P0-TSK-02 | Task store: persisted tasks, parent/child, retry count, evidence collection | FR-121, FR-132 | P0-TSK-01, P0-CFG-03 | L | Done |
| P0-TSK-03 | Resource locks: named, exclusive, persisted, all-or-nothing, stale reclamation | FR-124 | P0-CFG-03 | M | Done |
| P0-TSK-04 | Task scheduler: queue by priority/age, lock gating, cooperative pause/cancel | FR-120, FR-130 | P0-TSK-01, P0-TSK-02, P0-TSK-03 | L | Done |
| P0-TSK-05 | Crash recovery: interrupted tasks to `PAUSED(recovered=true)`, stale locks released | FR-006, NFR-010, NFR-011 | P0-TSK-02, P0-TSK-03 | M | Done |
| P0-LLM-01 | Ollama health check: loopback-only, offline-mode aware, timeout | §12.1, NFR-021, AT-001 | P0-CFG-01 | S | Done |
| P0-UI-01 | PySide6 tray (seven states) and main window (six live nav areas) | §9.1, §9.2, §9.3 | P0-COR-01, P0-CFG-01 | L | Done |
| P0-UI-02 | Accessibility baseline for the six live nav areas: tooltips, accessible names, no colour-only signal | NFR-030, NFR-031, NFR-033 | P0-UI-01 | S | In progress |
| P0-OPS-01 | CI workflow: unit, security, integration, UI, acceptance suites on every change | §21 (Phase 0 deliverable) | — | M | Done |
| P0-OPS-02 | Dependency and licence scanning gate in CI | NFR-023 | P0-OPS-01 | S | Not started |
| P0-TST-01 | Test harness: isolated vault per test via `JARVIS_DATA_DIR`, fakes at every external boundary | §23.1, §23.2, §23.3, NFR-042 | P0-OPS-01 | M | Done |
| P0-DOC-01 | Author SECURITY.md | §21 (Phase 0 deliverable) | — | M | Done |
| P0-DOC-02 | Author THREAT_MODEL.md | §21 (Phase 0 deliverable) | — | M | Not started |
| P0-DOC-03 | Author DATA_MODEL.md | §21 (Phase 0 deliverable) | — | M | Not started |

### 3.4 Tests to add in this phase

- `tests/unit/test_config_layering.py` — defaults + user + env merge order;
  `extra="forbid"` rejects unknown keys with a precise path.
- `tests/unit/test_permissions.py` — evaluation order (§11.1 short-circuit),
  `ALWAYS` rejected for `HIGH`/`PROHIBITED` risk, grant expiry and
  revocation.
- `tests/unit/test_tool_registry.py` — every name in PRD §13.3 "Prohibited
  broad tools" is rejected by identity; pattern denylist rejects invented
  variants such as `run_shell_v2`.
- `tests/unit/test_task_state_machine.py` — the full legal-transition table
  from ARCHITECTURE §6.7; every illegal transition raises.
- `tests/unit/test_locks.py` — all-or-nothing acquisition over a sorted lock
  set; stale-lock reclamation on startup.
- `tests/unit/test_redaction.py` — key-pattern and value-pattern redaction,
  truncation marker, clipboard content never stored in plaintext (forward
  test for FR-259, exercised for real in Phase 3).
- `tests/security/test_no_shell.py` — fails the build on `subprocess`,
  `os.system`, `os.popen`, `eval(`, `exec(`, `shell=True`, `ShellExecute`,
  `CreateProcess` anywhere in `src/`.
- `tests/security/test_layering.py` — L1–L5 import direction; `PySide6`
  imported only from `jarvis.ui`.
- `tests/integration/test_crash_recovery.py` — `RUNNING`/`WAITING` tasks
  from a dead instance become `PAUSED(recovered=true,
  blocked_reason="interrupted_by_restart")`.
- `tests/integration/test_migrations.py` — versioned forward migration
  applies cleanly; a database newer than the running binary is a hard
  startup failure (NFR-043).
- `tests/ui/test_tray_states.py` — seven tray states render under
  `QT_QPA_PLATFORM=offscreen` with distinct tooltip and accessible name.
- `tests/acceptance/test_at001_offline_privacy.py` — AT-001 becomes
  executable: in offline mode, the health checker returns
  `skipped(reason="offline_mode")` without opening a socket.

### 3.5 Risks and open questions for this phase

- THREAT_MODEL.md and DATA_MODEL.md are PRD §21 Phase 0 deliverables and do
  not yet exist. The cross-phase invariant that every phase gate re-reviews
  THREAT_MODEL.md (§2.4) cannot be executed until it is written; this
  should be treated as blocking the Phase 0 gate, not merely tracked as a
  documentation debt.
- The Ollama endpoint is unauthenticated by design (ARCHITECTURE §13, gap
  1); Jarvis can only avoid trusting it, not fix it. This is a permanent
  property, not something a later phase resolves.
- In-process isolation is not a security boundary through Phase 3
  (ARCHITECTURE §13, gap 2); a defect in a later worker can reach the
  vault. Process separation is deferred pending ADR-0004.
- The approval path has no UI yet, so nothing requiring `ASK` can run. This
  is intentional for Phase 0 (`DenyingApprovalPort` is the default) and is
  the first Phase 1 deliverable (P1-SEC-01).
- PRD open decision #2 (Python-only shell vs. native shell with Python
  workers) is recorded as resolved in favour of Python-first by ADR-0001,
  with reconsideration after Phase 3.

---

## 4. Phase 1 — Voice-first local assistant

### 4.1 Goal

Give Jarvis a voice. This phase wires the audio stack (wake phrase,
push-to-talk, local STT, local TTS) to the Ollama-hosted conversational
model, ships the first six narrowly-scoped tools, and closes the two
Phase 0 gaps that block any real interaction: the approval dialog UI and a
protected secret store. Nothing in this phase performs desktop or browser
automation beyond opening an approved application or URL.

### 4.2 Exit criteria (PRD §21, verbatim)

**All five met, confirmed by user acceptance testing on 2026-08-04.**

- [x] "Jarvis" or configured fallback reliably starts a command in the test
      environment — the configured fallback **"Hey Jarvis"**, on the pretrained
      openWakeWord model. Bare "Jarvis" is not detected (0 of 4 measured) and is
      stated as such in the GUI. No false wakes over an extended period of
      normal conversation.
- [x] User can converse locally
- [x] User can open Brave, YouTube, YouTube Music, Xbox, and Sea of Thieves
      — YouTube Music opens as a browser tab rather than the installed web app;
      the criterion is that it opens, and it does. The app-id route is recorded
      as an open defect.
- [x] User can stop listening and stop all automation
- [x] No network is used in offline mode

### 4.3 Work items

| ID | Item | PRD refs | Depends on | Size | Status |
|----|------|----------|------------|------|--------|
| P1-AUD-01 | Wake-word detection (openWakeWord), configurable phrase, push-to-talk fallback | FR-010, FR-011, FR-018 | P0-COR-06 | L | **Done** — base model installed via `--install-wake-model`, never bundled; per-user enrolment deferred (ADR-0016) |
| P1-AUD-02 | Privacy-preserving in-memory ring buffer, visible/audible recording indicators | FR-012, FR-013, AT-002 | P1-AUD-01 | M | **Done** |
| P1-AUD-03 | Voice activity detection for command bounds; barge-in pause while speaking | FR-014, FR-015 | P1-AUD-01 | M | **Done** — shipping half duplex, which is the FR-015 wording; see the ADR-0028 amendment of 2026-08-04 |
| P1-AUD-04 | Microphone selection with test meter; ambient-noise calibration | FR-016, FR-017 | P1-AUD-01 | S | **Done** — wired to the service in the GUI-seam round; devices name their audio system |
| P1-AUD-05 | Local STT integration (faster-whisper), model selection, English-only mode | FR-020, FR-021, FR-022, FR-039A | P1-AUD-03 | L | **Done** |
| P1-AUD-06 | Transcript confirmation for low-confidence commands; wake-word stripping; no raw-audio retention by default | FR-023, FR-024, FR-025 | P1-AUD-05 | M | **Done** |
| P1-AUD-07 | Local TTS integration (Kokoro), voice selection, preview, rate/pitch/volume | FR-030, FR-031 | P0-COR-06 | L | **Done** |
| P1-AUD-08 | Voice licence metadata; provider-neutral `TtsProvider` interface | FR-032, FR-035 | P1-AUD-07 | S | **Done** |
| P1-AUD-09 | Progress speech without repeated interruption; sensitive-output filtering; stable voice identity | FR-033, FR-034, FR-036 | P1-AUD-07 | M | Partial — filtering and stable voice identity done, plus presentation stripping before synthesis; **progress speech not built** and carried to Phase 2 |
| P1-AUD-10 | Expressive TTS worker isolation prototype (Qwen3-TTS, Python 3.12, typed authenticated IPC), disabled by default | FR-037, FR-038 | P1-AUD-08 | XL | Deferred out of Phase 1 (multiprocessing denied; needs its own ADR) |
| P1-LLM-01 | Ollama conversational-model integration; structured tool-call output only | FR-040, §13.4 | P0-LLM-01 | L | **Done** |
| P1-LLM-02 | Model routing skeleton: separate profiles for conversation/vision/embedding/STT/TTS roles | FR-041 | P1-LLM-01 | M | **Done** |
| P1-LLM-03 | Bounded multi-turn conversation context | FR-042 | P1-LLM-01 | M | **Done** |
| P1-COR-01 | Hallucination-source labelling: model answer / retrieved fact / inference / tool result / uncertainty | FR-047 | P1-LLM-01 | M | **Done** |
| P1-COR-02 | Tool-grounded success enforcement in conversational responses | FR-048 | P1-COR-01, P0-COR-04 | M | **Done** |
| P1-COR-03 | Startup-at-sign-in setting | FR-002 | P0-CFG-01 | S | **Done** |
| P1-MEM-01 | Personality profile editor; humour-learning proposal flow (approval-gated) | FR-043, FR-044 | P1-LLM-01 | M | **Done** |
| P1-MEM-02 | Local conversation history storage; global and per-conversation disable | FR-045 | P1-LLM-01, P0-CFG-03 | M | **Done** |
| P1-MEM-03 | Private session mode: no permanent history or memory | FR-046, AT-014 | P1-MEM-02 | M | **Done** |
| P1-APP-01 | Application launcher: registry seed, `open_application`/`close_application`, launch verification | FR-060 (partial), FR-062 (partial), FR-063, FR-064, AT-003 | P0-COR-04 | L | **Done** — ADR-0029 accepted; `close_application` is high risk and deferred to Phase 2 |
| P1-BRW-01 | Basic Brave URL opening (`open_url`), no dedicated profile yet | §21 (Phase 1 deliverable) | P1-APP-01 | S | **Done** — plus `web.search`, added after the model produced malformed URLs |
| P1-WIN-01 | Media controls (play/pause/next/previous/stop/mute/volume) via Windows media APIs | FR-094 | P0-COR-04 | M | **Done** |
| P1-SEC-01 | Approval dialog UI wired to `ApprovalPort`, replacing `DenyingApprovalPort` for the interactive path | §11.2 | P0-COR-04, P0-UI-01 | L | **Done** |
| P1-SEC-02 | Secret store (DPAPI-backed) for the first stored secrets | NFR-022 | P0-CFG-02 | M | **Done** |
| P1-UI-01 | Conversation screen and Home screen live data | §9.4, §9.5 | P1-LLM-01, P1-MEM-02 | M | **Done** |
| P1-UI-02 | Global hotkey infrastructure; configurable emergency-stop hotkey wired to `JarvisCore` | §11.3 | P0-COR-08, P0-UI-01 | M | **Done** |
| P1-UI-03 | Windows toast notifications; spoken-notification configuration by event type | FR-180, FR-181 | P0-UI-01, P1-AUD-07 | M | **Done** — notifications ship; spoken-notification configuration by event type is not built (FR-181 carried to Phase 2) |

### 4.4 Tests to add in this phase

- `tests/unit/test_wake_detector.py` — ring buffer never touches disk before
  a wake event; deleted after transcription unless diagnostics enabled.
- `tests/integration/test_stt_pipeline.py`, `test_tts_pipeline.py` — audio
  in, transcript/audio out, against recorded fixtures (no live microphone
  or GPU required per ARCHITECTURE §11).
- `tests/integration/test_ollama_tool_calling.py` — structured tool-call
  schema round-trips; free text never reaches the invoker.
- `tests/ui/test_approval_dialog.py` — dialog renders the PRD §11.2 field
  set and returns the outcome the invoker expects.
- `tests/acceptance/test_at002_wake_privacy.py` — AT-002.
- `tests/acceptance/test_at003_app_launch.py` — AT-003 (Sea of Thieves
  launch and verification).
- `tests/acceptance/test_at014_private_session.py` — AT-014.
- `tests/security/test_secret_store.py` — secrets never written to
  plaintext configuration or the audit log.

### 4.5 Risks and open questions for this phase

- Model-resource scheduling (FR-039) is configuration-only until a second
  heavy model exists (ARCHITECTURE §13, gap 6); it is not meaningfully
  exercised until Phase 4 adds the vision model.
- PRD open decisions #4–7 (default English voice, additional TTS provider
  options, custom "Jarvis" wake-word training, embedding model) are
  resolved provisionally by `PROJECT_INPUTS.md` (Kokoro `bm_george`,
  `faster-whisper small`) but remain open ADRs for the trained "Jarvis"
  wake word specifically — the development phrase is "Hey Jarvis"
  (PROJECT_INPUTS.md); "Jarvis" alone is the desired phrase but the GUI
  must not promise it works reliably (FR-011).
- FR-037/FR-038 (expressive TTS worker) is the first cross-Python-version
  process boundary in the product; its authentication and IPC contract is
  new territory and should get its own focused test pass before Phase 4
  adds a second GPU-resident model alongside it.
- Barge-in (FR-015) is explicitly partial in Phase 1 per the PRD wording
  ("Phase 1 may pause wake detection while Jarvis is speaking"); the full
  "Jarvis stop" interrupt phrase or global hotkey is not required to be
  reliable until later.

### 4.6 Carried into Phase 2 (closed 2026-08-04)

Phase 1 met all five exit criteria. These are the open items it did **not**
close, recorded here rather than left in a session transcript:

| Item | Origin | Note |
|---|---|---|
| Voice interruption does not work on real hardware | Acceptance 8.3 | Shipped as `duplex_mode: half`, which FR-015 permits and the GUI states. `Ctrl+Alt+End` and tray **Stop speaking** work. Needs a measurement, not a rewrite |
| "Open YouTube Music" opens a tab, not the installed app | Acceptance 5 | **Diagnosed 2026-08-04 from the audit log — it is three defects, and none of them is the app id.** See §4.6.1 |
| No time or date capability | Acceptance 3 | The most obvious question to ask a voice assistant, and it can only be answered from the model, which cannot know. A small verifiable tool |
| Arbitrary application launching with first-use permission | Owner request, 2026-08-04 | Deferred for stability. Needs its own ADR: Start-menu discovery as the executable source, approval on first use, persisted entries, a `.lnk` parser that runs nothing. ADR-0029 constraint 3 is preserved by construction |
| Progress speech during long work (FR-033) | P1-AUD-09 | Not built. Matters once Phase 2 has work long enough to report progress on |
| Spoken notifications by event type (FR-181) | P1-UI-03 | Notifications ship; choosing which are spoken does not |
| Per-user wake enrolment (ADR-0016 Path 1) | P1-AUD-01 | Measurement types, threshold fitting and the quality bar exist and are tested; the recording flow and personal verifier do not |
| Startup entry is named `pythonw.exe` | Acceptance 10 | Correct behaviour for a source checkout — there is no executable to name yet. Phase 6 packaging (ADR-0013, ADR-0022) resolves it |

### 4.6.1 "Open YouTube Music opens a tab" — diagnosed 2026-08-04

Recorded because the original hypothesis was wrong and a wrong hypothesis in a
backlog costs more than no hypothesis. This entry previously read *"likely the
profile directory or the app id."* All three candidate causes were checked
against the machine and eliminated:

- The installed PWA is `cinhimbnkkaeohfgghhklpknlkffjgod` — **identical** to
  `_YOUTUBE_MUSIC_APP_ID` in `jarvis/toolbox/launch.py`.
- It is installed under the `Default` profile, which is what the entry passes.
- The Start-menu shortcut's own target and arguments are **byte-for-byte
  identical** to the vector `build_argv` produces.

The catalogue entry is correct. What the audit log shows instead:

| # | Defect | Evidence | Where it is fixed |
|---|---|---|---|
| 1 | **The verification is vacuous.** The entry declares `verify_process_names=("brave.exe",)`, and Brave is usually already running, so `process_running` returns true whether or not an app window opened | Every `app.open` for YouTube Music recorded `succeeded / verified`, which proves nothing about the effect | Needs **window-level** verification, i.e. UI Automation. P2-WIN-08. Until then the entry must not claim `verified` |
| 2 | **The model called the wrong tool.** On acceptance day it invoked `web.open_url` with `https://music.youtube.com`. A URL handed to a browser opens a tab by definition; `app.open` was never involved | `2026-08-04T05:52:49 tool=web.open_url {"url": "https://music.youtube.com"} → succeeded/verified` | The tool schema does not tell the planner *which* applications exist, so it cannot know YouTube Music is openable as an app |
| 3 | **Alias and argument brittleness** | `{"application": "youtube-music"}` → `unknown_application`; `{"application": "YouTube Music", "argument": "Sunflower"}` → *"does not take an argument"* | Catalogue-driven valid values in the schema; an honest failure message that says what *can* be done |

Defect 1 is the one that matters beyond this feature. It is the third instance of
the same family — Phase 1 shipped `voice.speak` reporting verified success for a
silent room, and `app.open` reporting a launch it had not observed. **A tool that
verifies against a condition it does not control is not verifying.** The rule this
adds: a verification target must be able to distinguish "my effect happened" from
"something unrelated was already true."

---

## 5. Phase 2 — Deterministic desktop and browser automation

### 5.1 Goal

Give Jarvis hands, but only deterministic ones: UI Automation before
coordinates, DOM selectors before screen pixels, and a foreground-control
lock that is acquired before anything moves. This is the phase where
untrusted content first enters the system (web pages, YouTube search
results), so the prompt-injection defence designed in Phase 0 gets its
first real adversarial exercise. It is also where read-oriented filesystem
capability lands: resolving Known Folders, searching approved scopes, and
opening files with disambiguation. Mutating filesystem operations
(create/copy/move/delete) are deliberately deferred to Phase 3, once undo
and recovery exist to back them.

### 5.2 Exit criteria (PRD §21, verbatim)

- [ ] "Search RTX 5070 on YouTube and play the second video" works against
      defined test cases
- [ ] Application close never force-terminates without approval
- [ ] Browser actions use DOM selectors where available
- [ ] User mouse movement pauses automation
- [ ] "Open Downloads and open my latest resume PDF" works with correct
      ambiguity handling
- [ ] Jarvis can arrange two supported windows across selected monitors
- [ ] Screen capture is visibly indicated and respects application
      exclusions

### 5.3 Work items

| ID | Item | PRD refs | Depends on | Size | Status |
|----|------|----------|------------|------|--------|
| P2-WIN-01 | Application catalogue: scan safe registries/Start menu, present for approval; manual mapping GUI | FR-060, FR-061, FR-062, FR-063 | P1-APP-01 | L | Not started |
| P2-WIN-02 | UI Automation inspector: accessible name, control type, automation ID, patterns | FR-071 | P0-COR-04 | L | Not started |
| P2-WIN-03 | Automation worker thread; pywinauto UIA backend integration | §12.2 | P0-COR-06 | XL | Not started |
| P2-WIN-04 | Input ownership: acquire `foreground_desktop` lock before mouse/keyboard | FR-077 | P2-WIN-03, P0-TSK-03 | M | Not started |
| P2-WIN-05 | User-interruption pause: mouse/keyboard activity pauses the task | FR-078, AT-008 | P2-WIN-04 | M | Not started |
| P2-WIN-06 | Secure-desktop and UAC-prompt avoidance; password-field avoidance | FR-079, FR-080 | P2-WIN-03 | M | Not started |
| P2-WIN-07 | Sensitive-application blocklist for automation and screenshot capture | FR-081, AT-031 | P2-WIN-03 | M | Not started |
| P2-WIN-08 | Window discovery: process, identity, title, UIA properties, monitor, state | FR-240 | P2-WIN-02 | M | Not started |
| P2-WIN-09 | Window actions: activate, minimise, maximise, restore, move, resize, snap, monitor placement | FR-241, FR-242, FR-243 | P2-WIN-08 | L | Not started |
| P2-WIN-10 | Screenshot capture scoped to window/monitor/region; visible capture indication | FR-073, FR-271, FR-272 | P2-WIN-03 | M | Not started |
| P2-WIN-11 | Active-window screen-context request (basic "what's on my screen") | FR-270 (partial) | P2-WIN-10, P1-LLM-01 | M | Not started |
| P2-APP-01 | Normal close before force; unsaved-work-dialog detection and pause | FR-065, FR-066, AT-004 | P2-WIN-02 | M | Not started |
| P2-APP-02 | Force-close: explicit confirmation required every time | FR-067, AT-005 | P2-APP-01 | S | Not started |
| P2-BRW-01 | Dedicated persistent "Jarvis" Brave automation profile | FR-056 | P1-BRW-01 | M | Not started |
| P2-BRW-02 | Playwright visible-browser integration; DOM-first execution | FR-072, §12.1 | P2-BRW-01 | XL | Not started |
| P2-BRW-03 | Browser session control: clear profile, cookies, site permissions | FR-057 | P2-BRW-01 | S | Not started |
| P2-BRW-04 | CAPTCHA / anti-bot pause-and-request-user | FR-058 | P2-BRW-02 | M | Not started |
| P2-BRW-05 | Internet research: search modes, explicit network indicator, sourced summaries | FR-050, FR-051, FR-053 | P2-BRW-02 | L | Not started |
| P2-BRW-06 | Untrusted web-content wrapping; prompt-injection adversarial test | FR-054, AT-007 | P2-BRW-02, P0-SEC-03 | L | Not started |
| P2-BRW-07 | AI website prompting adapter (Gemini/ChatGPT-class sites) | FR-055 | P2-BRW-01 | M | Not started |
| P2-BRW-08 | YouTube search and indexed result selection with verified playback | FR-090, FR-091, AT-006 | P2-BRW-02 | L | Not started |
| P2-BRW-09 | YouTube Music search; ambiguous-match clarifying question | FR-092, FR-093 | P2-BRW-08 | M | Not started |
| P2-FS-01 | Windows Known Folder resolution via Windows APIs | FR-190, AT-019 | P0-COR-04 | S | Not started |
| P2-FS-02 | File Explorer control: open/select/reveal/navigate/sort/filter | FR-191 | P2-FS-01 | M | Not started |
| P2-FS-03 | Local file search in approved scope; match ranking | FR-192, FR-193 | P2-FS-01 | L | Not started |
| P2-FS-04 | Ambiguous-file disambiguation dialog | FR-194, AT-020 | P2-FS-03 | M | Not started |
| P2-FS-05 | Open file (configured/default/user-selected app) with verification; worked example | FR-195, FR-207, FR-209, AT-021 | P2-FS-04 | M | Not started |
| P2-FS-06 | Filesystem tool scoping and path validation (symlinks, junctions, env vars) | FR-208, FR-204, AT-022 | P2-FS-01 | L | Not started |
| P2-COR-01 | Honest-completion enforcement exercised against real verifiable actions | FR-048 (continued), AT-018 | P1-COR-02, P2-APP-01, P2-FS-05 | M | Not started |
| P2-TST-01 | Phase 2 acceptance-test suite wiring | AT-004…AT-009, AT-018…AT-022, AT-031 | (all Phase 2 items) | M | Not started |

### 5.4 Tests to add in this phase

- `tests/integration/test_uia_automation.py` — element discovery and
  invocation against a fixture application.
- `tests/integration/test_browser_automation.py` — Playwright DOM
  selectors preferred over coordinates; visible by default.
- `tests/security/test_prompt_injection.py` — a fixture web page containing
  "ignore previous instructions" / "click Allow" is logged as untrusted
  content and never treated as authority (AT-007).
- `tests/acceptance/test_at004_safe_close.py`,
  `test_at005_force_close_approval.py`,
  `test_at006_youtube_selection.py`,
  `test_at008_user_interruption.py`,
  `test_at009_concurrent_resources.py` (single-automation-type case; full
  heterogeneous case deferred to Phase 4),
  `test_at018_honest_completion.py`,
  `test_at019_known_folder.py`,
  `test_at020_file_ambiguity.py`,
  `test_at021_file_opening.py`,
  `test_at022_folder_boundary.py`,
  `test_at031_screen_capture_exclusion.py`.
- `tests/unit/test_path_scoping.py` — path resolution correctly rejects
  traversal via symlink, junction, or `..` outside the approved root.

### 5.5 Risks and open questions for this phase

- This is the first phase where untrusted content (web pages) reaches the
  planner. ARCHITECTURE §13 gap 4 explicitly flags that the delimiter
  strategy is "specified but unexercised" until this point — AT-007 and
  `test_prompt_injection.py` are load-bearing for the whole product's
  safety story, not routine coverage.
- PRD open decision #8 (search provider options) and #9 (browser profile
  isolation method) must be resolved before P2-BRW-01/P2-BRW-05 can be
  finalised.
- AT-009 (concurrent resources) is only partially demonstrable in this
  phase: a single automation task type exists, so "two tasks require
  foreground control" can be shown with two instances of the same tool but
  not yet with heterogeneous task types. Full demonstration is a Phase 4
  exit criterion.
- Maximum screenshot retention (PRD open decision #15) needs a default
  before P2-WIN-10 ships; PROJECT_INPUTS.md sets `screenshot_retention:
  task_only` as the working default.
- In-process isolation still applies (ARCHITECTURE §13 gap 2): a defect in
  the automation worker can reach the vault. This is the phase where that
  risk becomes concrete rather than theoretical, because the automation
  worker now does real things.

---

## 6. Phase 3 — Tasks, macros, and memory

### 6.1 Goal

Mature the task engine from a substrate into a user-facing system: pause
and resume with re-observation, checkpoints that survive a restart, and a
macro recorder that turns a demonstrated workflow into an approved,
versioned, exportable skill. This phase also gives the user control over
what Jarvis remembers (approval queue, provenance, forgetting with cascade
deletion) and introduces every state-changing filesystem operation
(create, copy, move, delete) — deliberately alongside undo, recovery, and
reversibility, not before them. Clipboard access, workspace profiles, and
scheduled/conditional automation round out the phase.

### 6.2 Exit criteria (PRD §21, verbatim)

- [ ] "Next bg" can be recorded, approved, replayed, edited, and exported
- [ ] Long tasks survive restart
- [ ] Deleted memories no longer appear in retrieval
- [ ] Export/import round-trip preserves approved identity data
- [ ] A reversible file rename can be undone and verified
- [ ] A workspace can be saved, exported, imported, and restored
- [ ] Scheduled tasks are visible, editable, pausable, and recover safely
      after restart

### 6.3 Work items

| ID | Item | PRD refs | Depends on | Size | Status |
|----|------|----------|------------|------|--------|
| P3-TSK-01 | Task tree (parent/subtask/dependency); bounded-plan validation with explicit stop conditions | FR-120, FR-121, FR-123 | P0-TSK-04, P1-LLM-01 | L | Not started |
| P3-TSK-02 | Pause/resume with mandatory state re-observation on resume | FR-125, FR-126, AT-010 | P3-TSK-01, P2-WIN-03 | M | Not started |
| P3-TSK-03 | Cancellation with lock release; checkpoint persistence across restart | FR-127, FR-128, AT-011 | P3-TSK-01, P0-TSK-05 | L | Not started |
| P3-TSK-04 | Waiting-task conditions, polling backoff, progress reporting, evidence, retry-limit display | FR-129, FR-130, FR-131, FR-132, FR-133 | P3-TSK-01 | L | Not started |
| P3-TSK-05 | Task screen live UI: all fields in §9.6 | §9.6 | P3-TSK-01…04 | M | Not started |
| P3-TSK-06 | Scheduled tasks: create/run/visibility; missed-run policy; computer-state conditions; run limits | FR-290, FR-292, FR-293, FR-294, FR-296, AT-032 | P3-TSK-03 | L | Not started |
| P3-TSK-07 | Conditional triggers; event deduplication; destructive-scheduled-action confirmation; quiet hours | FR-291, FR-297, FR-295, FR-298, FR-182, AT-033 | P3-TSK-06 | L | Not started |
| P3-TSK-08 | Schedule portability (export with device-specific data flagged for review) | FR-299, AT-034 (schedule aspect) | P3-TSK-06 | S | Not started |
| P3-SKL-01 | Macro recorder: voice/GUI start, semantic capture priority order | FR-100, FR-101, AT-012 | P2-WIN-02, P2-BRW-02 | XL | Not started |
| P3-SKL-02 | Naming and trigger phrases; generated-workflow review; dry run | FR-102, FR-103, FR-104 | P3-SKL-01 | M | Not started |
| P3-SKL-03 | Approval gate; versioning and rollback | FR-105, FR-106, FR-224 | P3-SKL-02 | M | Not started |
| P3-SKL-04 | Parameterised skills; preconditions, timeout, retry policy, verification; bounded failure recovery | FR-107, FR-108, FR-109 | P3-SKL-03 | L | Not started |
| P3-SKL-05 | Skill export, independently or inside a Jarvis identity package | FR-110, AT-012 | P3-SKL-03 | S | Not started |
| P3-MEM-01 | Memory candidate pipeline: review queue, approval UI, provenance | FR-160, FR-161, FR-162 | P1-MEM-02 | L | Not started |
| P3-MEM-02 | Memory retrieval relevance filter; sensitive-memory default-to-non-persistent | FR-163, FR-164 | P3-MEM-01 | M | Not started |
| P3-MEM-03 | Forget: cascade delete from active retrieval and derived indexes | FR-165, FR-167, AT-013 | P3-MEM-01 | M | Not started |
| P3-MEM-04 | Conversation deletion: message, conversation, date range, all history | FR-166 | P1-MEM-02 | M | Not started |
| P3-MEM-05 | Personality editor maturity; humour-learning approval flow completion | FR-043 (maturity), FR-044 (maturity) | P1-MEM-01 | S | Not started |
| P3-MEM-06 | Portable identity export/import baseline (`.jarvispack`); secret exclusion | FR-168, FR-169, FR-170, AT-015, AT-016 | P1-SEC-02, P3-MEM-01, P3-SKL-05 | XL | Not started |
| P3-FS-01 | File aliases; Safe Jarvis Workspace default location and permissions | FR-201, FR-205 | P2-FS-01 | M | Not started |
| P3-FS-02 | File create/copy/move/rename with conflict handling and boundary-crossing approval | FR-196, FR-197, FR-198 | P2-FS-06 | L | Not started |
| P3-FS-03 | Safe deletion to Recycle Bin; archive create/extract with path-traversal protection | FR-199, FR-200, AT-023 | P3-FS-02 | L | Not started |
| P3-FS-04 | Undo command; reversibility metadata exercised end to end; file-operation undo | FR-220, FR-221 (exercised), FR-223, AT-024 | P3-FS-02, P0-COR-02 | L | Not started |
| P3-FS-05 | File backups (configurable by type/folder/task/size/retention); settings rollback; task rollback plans | FR-222, FR-225, FR-226 | P3-FS-04 | M | Not started |
| P3-FS-06 | Irreversible-action warning; Recovery centre UI; rollback verification | FR-227, FR-228, FR-229, AT-025 | P3-FS-04, P3-FS-05 | M | Not started |
| P3-CLP-01 | Clipboard permissions and operations (read/replace/append/clear/paste-as-plain-text/snippets); automation clipboard use (FR-082) folded in | FR-250, FR-251, FR-252, FR-082 | P2-WIN-03, P0-SEC-03 | M | Not started |
| P3-CLP-02 | Clipboard history; sensitive-content detection and expiry | FR-253, FR-254, FR-255, AT-029 | P3-CLP-01 | M | Not started |
| P3-CLP-03 | Application blocklist; cross-application source/destination disclosure; task separation; audit redaction | FR-256, FR-257, FR-258, FR-259 | P3-CLP-01, P0-SEC-01 | M | Not started |
| P3-WKS-01 | Save current workspace as a named profile | FR-280, FR-281 | P2-WIN-09, P2-BRW-01 | M | Not started |
| P3-WKS-02 | Restore workspace; partial restoration on missing items; browser-tab restoration by URL | FR-282, FR-283, FR-284, AT-028 | P3-WKS-01 | L | Not started |
| P3-WKS-03 | Application-specific adapters; versioning; edit; portable import remapping; restoration safety guardrails | FR-285, FR-286, FR-287, FR-288, FR-289, AT-034 | P3-WKS-02 | L | Not started |

### 6.4 Tests to add in this phase

- `tests/unit/test_task_checkpoints.py`, `test_scheduler_backoff.py` —
  checkpoint round-trip; polling backoff never spins.
- `tests/unit/test_memory_cascade_delete.py` — deleting a memory removes it
  from retrieval and every derived index in the same transaction.
- `tests/unit/test_reversibility.py` — every registered state-changing tool
  in the Phase 3 tool set has non-empty reversibility metadata (invariant
  §2.3, enforced as a build-time assertion, not just a runtime check).
- `tests/integration/test_recycle_bin.py` — deleted files land in the
  Recycle Bin, not permanently removed, absent explicit high-risk
  confirmation.
- `tests/integration/test_export_import_roundtrip.py` — `.jarvispack`
  export/import preserves personality, memories, skills, aliases; contains
  no keys/cookies/tokens/credentials.
- `tests/acceptance/test_at010_pause_resume.py`,
  `test_at011_restart_recovery.py`,
  `test_at012_learned_macro.py`,
  `test_at013_memory_deletion.py`,
  `test_at015_export_portability.py`,
  `test_at016_secret_exclusion.py`,
  `test_at023_safe_deletion.py`,
  `test_at024_file_undo.py`,
  `test_at025_irreversible_warning.py`,
  `test_at028_window_layout.py`,
  `test_at029_clipboard_privacy.py`,
  `test_at032_missed_schedule.py`,
  `test_at033_conditional_dedup.py`,
  `test_at034_workspace_portability.py`.

### 6.5 Risks and open questions for this phase

- ARCHITECTURE §13 gap 5: `ALWAYS` grants have no automatic review. A
  periodic review prompt for low-risk always-allow grants is scoped to
  this phase per that gap note; if it slips, record it explicitly rather
  than letting it silently vanish from scope.
- PRD open decision #14 (data-retention defaults) needs resolving before
  P3-MEM-01 and P3-FS-05 backup retention defaults can be finalised.
- The macro recorder (P3-SKL-01) is the largest single item in the backlog
  by dependency count — it needs both a working UIA backend (Phase 2) and
  a working browser backend (Phase 2) to capture semantically, and its
  "priority order" fallback logic (UIA element → browser selector →
  keyboard shortcut → mouse action → coordinate anchor) is exactly the
  kind of thing that looks done at the happy path and breaks on the first
  real application.
- Undo (P3-FS-04) depends on reversibility metadata that was declared in
  Phase 0 but never exercised against a real rollback until now; expect
  the first real gaps in that metadata's design to surface here.

---

## 7. Phase 4 — Vision fallback and long-running workflows

### 7.1 Goal

Add the vision model as a fallback of last resort — only when UI Automation
and DOM access are insufficient — and use it to unlock the long-running,
document-heavy, multi-resource workloads that Phase 2's deterministic
automation cannot reach on its own: watcher tasks with per-item
checkpoints, local document and OCR understanding, folder and notification
watchers, and Windows device/settings control. This is also the phase
where genuinely concurrent, heterogeneous tasks first compete for locks, so
`LockManager` gets its first real multi-task exercise.

### 7.2 Exit criteria (PRD §21, verbatim)

- [ ] Vision is used only when deterministic methods fail
- [ ] Every visual click is verified
- [ ] Multiple tasks can run when their resources do not conflict
- [ ] Two foreground UI tasks are queued rather than run simultaneously
- [ ] Jarvis can summarise an approved PDF locally and reference relevant
      pages
- [ ] Folder and notification watchers remain visibly scoped and bounded
- [ ] Device and setting changes are verified after execution

### 7.3 Work items

| ID | Item | PRD refs | Depends on | Size | Status |
|----|------|----------|------------|------|--------|
| P4-LLM-01 | Model resource scheduler: sequential loading, VRAM checks, provider fallback across planner/vision/TTS | FR-039 | P1-LLM-02, P1-AUD-10, P0-COR-05 | L | Not started |
| P4-VIS-01 | Qwen3-VL model route; compatibility tests (screenshot input, element ID, coordinate grounding, structured output) | FR-041 (vision role), §15.4 | P4-LLM-01 | L | Not started |
| P4-VIS-02 | Screenshot grounding; UIA-plus-vision fusion; coordinate-only actions marked fragile | FR-074, FR-076 | P4-VIS-01, P2-WIN-02 | L | Not started |
| P4-VIS-03 | Vision action verification: timestamp, proposed target, confidence, bounds, post-action check | FR-075 | P4-VIS-02 | M | Not started |
| P4-VIS-04 | Visual advice-vs-action distinction; control confirmation; screen-change verification; error assistance | FR-274, FR-275, FR-276, FR-277 | P4-VIS-02 | L | Not started |
| P4-VIS-05 | Screen-context maturity: full capture-scope hierarchy, sensitive exclusions, retention policy, export exclusion | FR-270, FR-271, FR-272, FR-273, FR-278, FR-279 | P2-WIN-10, P2-WIN-11 | M | Not started |
| P4-TSK-01 | Watcher task type: per-item checkpoint, deduplication key | FR-140, FR-141, FR-142 | P3-TSK-04 | L | Not started |
| P4-TSK-02 | Message monitoring: explicit scope/duration/destination/retention; privacy limits; paste/submit separation; rate-limit respect | FR-143, FR-144, FR-145, FR-146 | P4-TSK-01 | L | Not started |
| P4-TSK-03 | WhatsApp scoped workflow prototype | §21 (Phase 4 deliverable) | P4-TSK-02, P2-WIN-03 | XL | Not started |
| P4-TSK-04 | Multi-task resource locking exercised with heterogeneous concurrent tasks | FR-124 (maturity), AT-009 | P0-TSK-03, P4-VIS-01, P2-BRW-02 | L | Not started |
| P4-FS-01 | Document processing core: read, summarise, search, answer, extract headings/points/metadata, compare | FR-210, FR-219, AT-026 | P2-FS-01 | XL | Not started |
| P4-FS-02 | Document format matrix (PDF/DOCX/PPTX/XLSX/TXT/MD/HTML/CSV); PDF classification | FR-211, FR-212 | P4-FS-01 | L | Not started |
| P4-FS-03 | Local OCR with machine-extraction disclosure | FR-213, AT-027 | P4-FS-02 | M | Not started |
| P4-FS-04 | Spreadsheet and presentation handling (list/read/search/summarise/compare, no silent overwrite) | FR-214, FR-215 | P4-FS-01 | L | Not started |
| P4-FS-05 | Image understanding; media metadata inspection | FR-216, FR-217, FR-218 | P4-VIS-01 | M | Not started |
| P4-FS-06 | Local file-content indexing; folder watchers | FR-206, FR-203 | P3-FS-01, P4-TSK-01 | L | Not started |
| P4-WIN-01 | Windows Settings navigation; audio-device management | FR-230, FR-231 | P2-WIN-02 | M | Not started |
| P4-WIN-02 | Bluetooth and network controls (no saved Wi-Fi password disclosure) | FR-232, FR-233 | P4-WIN-01 | M | Not started |
| P4-WIN-03 | Display controls; focus and interruption controls | FR-234, FR-235 | P4-WIN-01 | M | Not started |
| P4-WIN-04 | Power-state actions with fresh confirmation: lock/sign-out/restart/shutdown/sleep/hibernate | FR-236 | P4-WIN-01 | M | Not started |
| P4-WIN-05 | Security-settings boundary enforcement; scoped elevation helper; post-change verification | FR-237, FR-238, FR-239, FR-004 | P4-WIN-01 | XL | Not started |
| P4-WIN-06 | Virtual desktop support; advanced multi-monitor layout restoration | FR-244, FR-247, FR-249 | P2-WIN-09, P3-WKS-02 | L | Not started |
| P4-NTF-01 | Notification access and scope permissions (application/sender/type/period/task/keyword) | FR-260, FR-261 | P0-SEC-03 | M | Not started |
| P4-NTF-02 | Notification actions and restricted-action boundary (no silent reply/send/delete/approve) | FR-262, FR-263 | P4-NTF-01 | M | Not started |
| P4-NTF-03 | Notification examples, event deduplication, privacy, history; event-triggered tasks with failure fallback | FR-264, FR-265, FR-266, FR-267, FR-268, FR-269, AT-030 | P4-NTF-02 | L | Not started |

### 7.4 Tests to add in this phase

- `tests/integration/test_vision_grounding.py` — coordinate output against
  fixture screenshots; confidence and bounds present on every proposal.
- `tests/integration/test_document_extraction.py` — each supported format
  in FR-211 against fixture files; unsupported formats return an explicit
  explanation, never fabricated content.
- `tests/security/test_resource_locks_concurrent.py` — two heterogeneous
  tasks (one vision-driven UI task, one background document task) run
  concurrently; two foreground-lock tasks do not.
- `tests/acceptance/test_at009_concurrent_resources.py` (full,
  heterogeneous case — extends the Phase 2 single-type version),
  `test_at026_document_grounding.py`,
  `test_at027_ocr_disclosure.py`,
  `test_at030_notification_scope.py`.
- `tests/security/test_watcher_bounds.py` — every watcher declares scope,
  stop condition, and expiry; a watcher with none is rejected at
  registration.

### 7.5 Risks and open questions for this phase

- FR-004 (scoped elevation) and FR-238 (elevation for settings changes)
  are the first point in the backlog where an elevated helper process is
  plausibly required. ARCHITECTURE §4.2 records this interface as "not yet
  defined; ADR-0009." That ADR should be resolved before P4-WIN-05 starts,
  not discovered mid-implementation.
- Vision-driven automation is the first place a defect in the automation
  worker has a plausible path to acting on a misread screen; the
  pre-action/post-action verification in P4-VIS-03 is the control that
  makes this phase's "every visual click is verified" exit criterion true
  rather than aspirational.
- The WhatsApp scoped workflow prototype (P4-TSK-03) is named directly in
  PRD §21 but has no dedicated FR block; its permission surface (message
  monitoring, FR-143/144) is comparatively under-specified and will need
  scope decisions made and recorded as it is built, not inferred from the
  PRD after the fact.
- Notification-listener reliability varies by Windows application (some
  apps do not surface listenable notifications at all); FR-269 requires
  Jarvis to explain the limitation and fall back to a window/application
  watcher rather than silently doing nothing.

---

## 8. Phase 5 — IDE orchestration

### 8.1 Goal

Add a single, application-specific adapter for an agentic IDE (Google
Antigravity), scoped tightly enough that Jarvis can supervise it without
becoming a hidden shell. Everything destructive the IDE agent proposes —
terminal commands, package downloads, file deletion, writes outside the
approved workspace, elevation, credentials, network publication, git push,
deployment — routes back through the same `ToolInvoker` approval path as
every other high-risk action. This is deliberately the smallest phase in
the backlog: PRD §26 ("Ruthless Scope Guidance") is explicit that reliable
narrow coverage beats broad unreliable coverage, and IDE orchestration is
the PRD's own example of a single deep integration rather than a platform.

### 8.2 Exit criteria (PRD §21, verbatim)

- [ ] The React to-do-list reference scenario completes with checkpoints
- [ ] Jarvis never approves destructive IDE actions silently
- [ ] Completion includes evidence, not only an IDE message

### 8.3 Work items

| ID | Item | PRD refs | Depends on | Size | Status |
|----|------|----------|------------|------|--------|
| P5-IDE-01 | Antigravity adapter: launch and open | FR-150 | P1-APP-01 | L | Not started |
| P5-IDE-02 | Workspace creation via safe filesystem tool, scoped to an approved parent directory | FR-151 | P3-FS-01 | M | Not started |
| P5-IDE-03 | Prompt submission to the built-in IDE agent | FR-152 | P5-IDE-01 | M | Not started |
| P5-IDE-04 | Agent-status monitoring: messages, approval prompts, tests, completion indicators | FR-153 | P5-IDE-03, P2-WIN-02 | L | Not started |
| P5-IDE-05 | Permission boundary: no automatic approval of terminal/package/delete/write-outside-workspace/elevation/credential/publish/push/deploy | FR-154, AT-017 | P0-SEC-03, P5-IDE-04 | L | Not started |
| P5-IDE-06 | Follow-up prompts bounded by a user-configurable maximum attempt count | FR-155 | P5-IDE-03 | S | Not started |
| P5-IDE-07 | Completion verification: expected files plus IDE-reported build/test result, not "done" alone | FR-156 | P5-IDE-04 | M | Not started |
| P5-IDE-08 | No hidden shell delegation: adversarial test that the IDE integration cannot bypass Jarvis policy | FR-157 | P5-IDE-05, P0-COR-03 | M | Not started |
| P5-IDE-09 | Completion notification to the user | FR-156, FR-180 | P5-IDE-07, P1-UI-03 | S | Not started |
| P5-UI-01 | IDE orchestration status panel (Integrations / Tasks views) | §9.3 | P5-IDE-04 | M | Not started |
| P5-SEC-01 | Threat-model review: IDE-agent output treated as untrusted observation, never as authority | §11.4 | P5-IDE-04, P2-BRW-06 | M | Not started |
| P5-TST-01 | React to-do-list reference scenario acceptance test | §21 (Phase 5 exit) | (all Phase 5 items) | L | Not started |

### 8.4 Tests to add in this phase

- `tests/integration/test_antigravity_adapter.py` — launch, prompt
  submission, status monitoring against a fixture IDE surface.
- `tests/security/test_ide_permission_boundary.py` — every action in the
  FR-154 list is denied without fresh approval, individually.
- `tests/security/test_no_hidden_shell_via_ide.py` — the IDE integration
  cannot be used as an indirect route to a prohibited capability (FR-157).
- `tests/acceptance/test_at017_ide_permission.py` — AT-017.
- `tests/acceptance/test_phase5_react_todo_scenario.py` — the reference
  scenario end to end, asserting checkpoints and evidence-backed
  completion, not just a final status.

### 8.5 Risks and open questions for this phase

- FR-153 (agent monitoring) and FR-156 (completion verification) both
  depend on the IDE surfacing legible status in its UI; if Antigravity's
  UI changes in a way that breaks the observer, this phase inherits the
  same coordinate/DOM fragility problem Phase 2 solved for browsers and
  desktop apps generally — treat the Antigravity adapter as another
  UI-Automation-first integration, not a special case.
- FR-157 ("no hidden shell delegation") is a genuinely adversarial
  property: an agentic IDE is, by construction, a tool that can execute
  code. The boundary Jarvis owns is what it will *ask* the IDE agent to do
  and what it will *auto-approve* on the IDE agent's behalf — P5-IDE-08's
  test needs to specifically try to smuggle a prohibited action through
  the IDE prompt, not just check the adapter's own tool list.
- This phase has no dedicated memory, skill, or export work; if a later
  phase wants IDE workflows to be recordable as skills, that is new scope
  not currently in the PRD and should go through the brainstorming/ADR
  process rather than being added here implicitly.

---

## 9. Phase 6 — Productisation

### 9.1 Goal

Turn a working engine into a product a new Windows user can install,
configure, and trust without reading source code: hardware-aware
onboarding, a signed installer, a model/voice/application manager, an
update system with rollback, and the licensing, privacy, and documentation
work that a public release requires. This phase does not add new
automation capability; it makes every capability built in Phases 0–5
discoverable, configurable, and safe to hand to someone else's machine.

### 9.2 Exit criteria (PRD §21, verbatim)

- [ ] A new Windows user can install, select models, configure voice, map
      apps, and run the initial test without editing code
- [ ] No shared secrets ship with the product
- [ ] User data can be completely exported and deleted
- [ ] Installer passes malware and dependency review
- [ ] Upgrade preserves the user's Jarvis identity

### 9.3 Work items

| ID | Item | PRD refs | Depends on | Size | Status |
|----|------|----------|------------|------|--------|
| P6-PKG-01 | First-run onboarding wizard, steps 1–9: explain local processing, permissions, Ollama detection, model recommendation, storage requirements, download approval, microphone select/test, wake phrase, "Hey Jarvis" fallback | §16 (items 1–9), §15.1 | P4-LLM-01, P1-AUD-01 | XL | Not started |
| P6-PKG-02 | Onboarding wizard, steps 10–18: voice select/preview, Brave profile creation, application discovery, startup config, emergency-stop hotkey, default permission policy review, safe test sequence, `.jarvispack` import offer | §16 (items 10–18) | P6-PKG-01, P2-BRW-01, P2-WIN-01 | L | Not started |
| P6-LLM-01 | Model manager GUI: install/remove, per-role selection, context length, temperature/reasoning, test tool-calling, test vision, disk/VRAM usage, idle-unload timeout | §15.3 | P4-LLM-01 | L | Not started |
| P6-AUD-01 | Voice manager GUI maturity: pack management, licence display | FR-031, FR-032 | P1-AUD-08 | M | Not started |
| P6-APP-01 | Application discovery wizard and manual mapping GUI, full maturity | FR-061, FR-062 | P2-WIN-01 | M | Not started |
| P6-PKG-03 | Signed Windows x64 installer: per-user install, uninstall entry, data preservation on update, explicit deletion on uninstall, repair, offline install | §18.1 | — | XL | Not started |
| P6-PKG-04 | Model distribution wizard in installer: hardware detection, licence display, custom Ollama model names | §18.2 | P6-PKG-03, P6-LLM-01 | L | Not started |
| P6-SEC-01 | Secrets/API-key configuration UI backed by Windows-protected storage | §18.3 | P1-SEC-02 | M | Not started |
| P6-PKG-05 | Update system: manual/automatic check, signed packages, release notes, rollback, schema migration, skill/pack compatibility checks | §18.4 | P6-PKG-03 | XL | Not started |
| P6-PKG-06 | Privacy and telemetry controls: opt-in only, excludes conversation/screenshots/filenames, revocable, local-only crash logs | §18.5 | — | M | Not started |
| P6-DOC-01 | User documentation, third-party attribution, open-source licence notices | §17.3 | — | L | Not started |
| P6-PKG-07 | Import/export wizard maturity: preview, conflict detection, selective import, remapping, duplicate handling, rollback | §14.6 | P3-MEM-06 | L | Not started |
| P6-PKG-08 | Plugin/adapter SDK groundwork | §21 (Phase 6 deliverable) | P0-COR-03 | L | Not started |
| P6-SEC-02 | Crash recovery and diagnostics surfaced in GUI | §21 (Phase 6 deliverable) | P0-TSK-05 | M | Not started |
| P6-OPS-01 | Release checklist; dependency/licence scanning gate hardened; code-signing pipeline | NFR-023, NFR-024 | P0-OPS-02 | L | Not started |
| P6-UI-01 | Remaining main-window nav areas reach live-data parity (Applications, Models, Voice, Integrations, History, Import/Export, Developer tools, About/updates) | §9.3 | P0-UI-01, P6-LLM-01, P6-AUD-01 | L | Not started |
| P6-DOC-02 | Privacy policy; EULA/terms if applicable; support and issue-reporting process | §17.3 | — | M | Not started |
| P6-TST-01 | Definition-of-Done checklist verification run (all 24 items) | §27 | (all phases) | L | Not started |
| P6-TST-02 | Compatibility matrix testing: monitors, DPI (100/125/150/200%), light/dark theme, Brave versions, Windows 11 builds, GPU variants, mic/headset combinations | §23.5 | (all phases) | L | Not started |
| P6-UI-02 | Accessibility audit, final pass, across all fifteen nav areas | NFR-030, NFR-031, NFR-032, NFR-033 | P0-UI-02, P6-UI-01 | M | Not started |
| P6-UI-03 | Storage-usage visibility panel (models, history, screenshots, logs, exports) | NFR-006 | P6-UI-01 | S | Not started |

### 9.4 Tests to add in this phase

- `tests/integration/test_installer.py` (or an external installer-test
  harness) — clean-machine install, repair, uninstall with data-deletion
  option.
- `tests/integration/test_update_rollback.py` — a failed update rolls back
  cleanly; schema migration runs as part of update.
- `tests/security/test_no_shared_secrets.py` — the shipped artefact
  contains no embedded API keys, tokens, or credentials of any kind.
- `tests/acceptance/test_dod_checklist.py` — walks PRD §27's 24 items and
  asserts each is either demonstrated by an existing acceptance test or
  explicitly checked here.
- `tests/ui/test_compatibility_matrix.py` (parametrised) — DPI and theme
  variants render without clipping or unreadable contrast.

### 9.5 Risks and open questions for this phase

- PRD open decisions #1 (final product name), #3 (installer technology),
  #10 (public plugin signing policy), #12 (MSIX as primary format), and
  #16 (code-signing and update infrastructure) must all be resolved before
  P6-PKG-03/04/05 can be finalised; none has a working default in
  `PROJECT_INPUTS.md` the way the model and voice choices do.
- "Upgrade preserves the user's Jarvis identity" (exit criterion) is only
  as strong as the schema-migration and `.jarvispack` round-trip work done
  in Phase 0 (P0-CFG-03) and Phase 3 (P3-MEM-06); this phase should not
  need to re-solve data preservation, only prove it across a real
  installer-driven upgrade.
- The plugin/adapter SDK (P6-PKG-08) is listed as a Phase 6 deliverable in
  PRD §21 but PRD open decision #13 (in-process vs. isolated plugins) is
  unresolved; scope this item as groundwork and interface stability, not
  as a full third-party plugin ecosystem, unless that decision is made
  first.
- Malware and dependency review (exit criterion) is an external gate, not
  something this backlog can mark `Done` unilaterally; P6-OPS-01 should
  produce the evidence package that review consumes, but the review
  outcome itself is outside engineering's control.

---

## 10. Requirement coverage matrix

Every FR range from PRD §10.1–§10.25 and every NFR group from §19.1–§19.5
appears exactly once below.

| FR/NFR range | Area | Phase | Backlog items |
|---|---|---|---|
| FR-001 … FR-007 (§10.1 Application lifecycle) | Core orchestration | 0 | P0-COR-06, P0-COR-07, P0-COR-08, P0-TSK-05 (FR-004 flagged, see below) |
| FR-010 … FR-018 (§10.2 Wake phrase and audio input) | Audio | 1 | P1-AUD-01 … P1-AUD-04 |
| FR-020 … FR-025 (§10.3 Speech recognition) | Audio | 1 | P1-AUD-05, P1-AUD-06 |
| FR-030 … FR-039A (§10.4 Voice output) | Audio | 1, 4 | P1-AUD-07 … P1-AUD-10; P4-LLM-01 |
| FR-040 … FR-048 (§10.5 Conversation and personality) | Model routing / Core orchestration | 1 | P1-LLM-01 … P1-LLM-03, P1-COR-01, P1-COR-02 |
| FR-050 … FR-058 (§10.6 Internet research and external AI websites) | Browser | 2 | P2-BRW-01, P2-BRW-03 … P2-BRW-07 |
| FR-060 … FR-067 (§10.7 Application discovery and launching) | Applications | 1, 2, 6 | P1-APP-01; P2-WIN-01, P2-APP-01, P2-APP-02; P6-APP-01 |
| FR-070 … FR-082 (§10.8 Windows and application automation) | Windows automation | 2, 3, 4 | P2-WIN-02 … P2-WIN-07; P3-CLP-01; P4-VIS-02, P4-VIS-03 |
| FR-090 … FR-095 (§10.9 YouTube and YouTube Music) | Browser / Windows automation | 1, 2 | P1-WIN-01; P2-BRW-08, P2-BRW-09 |
| FR-100 … FR-110 (§10.10 Macro and skill learning) | Skills | 3 | P3-SKL-01 … P3-SKL-05 |
| FR-120 … FR-133 (§10.11 Task planning and execution) | Tasks | 0, 2, 3 | P0-TSK-01 … P0-TSK-05; P2-WIN-04, P2-WIN-05; P3-TSK-01 … P3-TSK-04 |
| FR-140 … FR-146 (§10.12 Repetitive and monitoring workflows) | Tasks | 4 | P4-TSK-01, P4-TSK-02, P4-TSK-03 |
| FR-150 … FR-157 (§10.13 IDE-agent orchestration) | IDE orchestration | 5 | P5-IDE-01 … P5-IDE-08 |
| FR-160 … FR-170 (§10.14 Memory and personalisation) | Memory | 3 | P3-MEM-01 … P3-MEM-06 |
| FR-180 … FR-183 (§10.15 Notifications) | Notifications / Interface | 1, 3 | P1-UI-03; P3-TSK-07 |
| FR-190 … FR-209 (§10.16 File Explorer and Local File Operations) | Filesystem | 2, 3, 4 | P2-FS-01 … P2-FS-06; P3-FS-01; P4-FS-06 |
| FR-210 … FR-219 (§10.17 Local Document and Media Understanding) | Filesystem | 4 | P4-FS-01 … P4-FS-05 |
| FR-220 … FR-229 (§10.18 Undo, Recovery, and Rollback) | Core orchestration / Filesystem | 0, 3 | P0-COR-02 (FR-221 metadata declared); P3-FS-04 … P3-FS-06 |
| FR-230 … FR-239 (§10.19 Windows Settings and Device Controls) | Windows automation | 4 | P4-WIN-01 … P4-WIN-05 (FR-004/FR-238 elevation flagged, see below) |
| FR-240 … FR-249 (§10.20 Window, Desktop, and Workspace Management) | Windows automation / Workspace | 2, 3, 4 | P2-WIN-08, P2-WIN-09; P3-WKS-01 … P3-WKS-03; P4-WIN-06 |
| FR-250 … FR-259 (§10.21 Clipboard and Text Transformation) | Clipboard | 3 | P3-CLP-01 … P3-CLP-03 |
| FR-260 … FR-269 (§10.22 Notification Observation and Event Triggers) | Notifications | 4 | P4-NTF-01 … P4-NTF-03 |
| FR-270 … FR-279 (§10.23 Screen Context and Visual Assistance) | Vision / screen context | 2, 4 | P2-WIN-10, P2-WIN-11; P4-VIS-01, P4-VIS-04, P4-VIS-05 |
| FR-280 … FR-289 (§10.24 Application Session and Workspace Restoration) | Workspace | 3, 4 | P3-WKS-01 … P3-WKS-03; P4-WIN-06 |
| FR-290 … FR-299 (§10.25 Scheduling and Conditional Automation) | Tasks | 3 | P3-TSK-06 … P3-TSK-08 |
| NFR-001 … NFR-006 (§19.1 Performance) | Cross-cutting | 0, 1, 4, 6 | P0-COR-06; P1-AUD-01 … P1-AUD-10 (latency); P4-LLM-01; P6-UI-03 |
| NFR-010 … NFR-014 (§19.2 Reliability) | Tasks / Core orchestration | 0, 1, 2 | P0-TSK-02, P0-TSK-05; P1-AUD-01 … P1-AUD-10 (degradation); P2-COR-01 |
| NFR-020 … NFR-025 (§19.3 Security) | Security | 0, 1, 3, 6 | P0-SEC-01 … P0-SEC-03, P0-OPS-02; P1-SEC-02; P3-MEM-06; P6-PKG-03, P6-PKG-05, P6-PKG-06 |
| NFR-030 … NFR-033 (§19.4 Accessibility) | Interface | 0 … 6 (formally audited in 6) | P0-UI-02; P6-UI-02 |
| NFR-040 … NFR-043 (§19.5 Maintainability) | Core orchestration | 0, 2 | P0-CFG-03, P0-COR-01 … P0-COR-04; P2-WIN-01 (modular adapters) |

### 10.1 Flagged requirements

- **FR-004 Scoped elevation.** No phase in PRD §21 explicitly delivers an
  elevated-action helper process; ARCHITECTURE §4.2 records its interface
  as "not yet defined; ADR-0009." It is provisionally attached to
  P4-WIN-05 (Windows Settings changes are the first plausible consumer,
  via FR-238), but this is this backlog's judgement call, not a PRD
  instruction. If no Phase 0–6 feature ends up genuinely requiring
  elevation, FR-004's mechanism may remain interface-only through Version
  1 — that outcome should be recorded as a deliberate scope decision (an
  ADR), not discovered as a silent gap during Phase 6 sign-off.
- **FR-039 TTS resource scheduling.** Split across Phase 1 (isolated-worker
  groundwork, FR-038) and Phase 4 (the scheduler cannot prevent unsafe
  *simultaneous* loading of a vision model that does not exist until then).
  This is a legitimate two-phase requirement, not a gap, but is called out
  because the FR reads as a single unit in the PRD.

---

## 11. Acceptance test coverage

All 34 acceptance tests from PRD §22.

| AT id | Description (abridged) | Phase it becomes testable | Backlog item |
|---|---|---|---|
| AT-001 | Offline mode: no network request for a general question | 0 | P0-LLM-01 |
| AT-002 | No microphone audio written to disk before wake detection | 1 | P1-AUD-02 |
| AT-003 | "Open Sea of Thieves" launches and is verified | 1 | P1-APP-01 |
| AT-004 | Unsaved-work dialog pauses the close action | 2 | P2-APP-01 |
| AT-005 | Force-close requires fresh confirmation | 2 | P2-APP-02 |
| AT-006 | Second YouTube video selected and verified | 2 | P2-BRW-08 |
| AT-007 | Webpage instructions ignored and logged as untrusted | 2 | P2-BRW-06 |
| AT-008 | Mouse movement pauses GUI automation | 2 | P2-WIN-05 |
| AT-009 | Two foreground-lock tasks: one runs, one queues | 4 (partial in 2) | P4-TSK-04 (P2-TST-01 for the single-type case) |
| AT-010 | Paused task retains checkpoint; resume re-observes | 3 | P3-TSK-02 |
| AT-011 | Interrupted long task recoverable without repeating actions | 3 | P3-TSK-03 |
| AT-012 | Recorded macro inactive until approved; export/import works | 3 | P3-SKL-01, P3-SKL-05 |
| AT-013 | Deleted memory and its derived index not retrieved | 3 | P3-MEM-03 |
| AT-014 | Private session leaves no permanent record | 1 | P1-MEM-03 |
| AT-015 | `.jarvispack` restores identity on another machine with remapping | 3 | P3-MEM-06 |
| AT-016 | Normal export contains no secrets | 3 | P3-MEM-06 |
| AT-017 | Antigravity delete/high-risk request pauses for user | 5 | P5-IDE-05 |
| AT-018 | Unverifiable result reported as blocked/failed, not completed | 2 | P2-COR-01 |
| AT-019 | Downloads Known Folder resolved via Windows API | 2 | P2-FS-01 |
| AT-020 | Three plausible resumes: user asked to select | 2 | P2-FS-04 |
| AT-021 | Selected PDF opens in configured app, window verified | 2 | P2-FS-05 |
| AT-022 | Filesystem tool cannot read/modify outside approved root | 2 | P2-FS-06 |
| AT-023 | Deleted file moves to Recycle Bin after confirmation | 3 | P3-FS-03 |
| AT-024 | Jarvis-performed rename reversed and verified | 3 | P3-FS-04 |
| AT-025 | Permanent deletion states it cannot be undone, beforehand | 3 | P3-FS-06 |
| AT-026 | PDF answer identifies source document and page/section | 4 | P4-FS-01 |
| AT-027 | OCR text labelled machine-generated and potentially inaccurate | 4 | P4-FS-03 |
| AT-028 | Saved two-monitor workspace restores correctly, reports gaps | 3 | P3-WKS-02 |
| AT-029 | Likely passwords/auth codes not retained in clipboard history | 3 | P3-CLP-02 |
| AT-030 | Notification watcher scoped to one app does not read others | 4 | P4-NTF-03 |
| AT-031 | Capture refused for a blocked sensitive application | 2 | P2-WIN-07 |
| AT-032 | Missed scheduled task follows its configured policy | 3 | P3-TSK-06 |
| AT-033 | Single file-creation event produces one task instance | 3 | P3-TSK-07 |
| AT-034 | Imported workspace requests path/monitor/app remapping | 3 | P3-WKS-03 |

No acceptance test maps to Phase 6 as its primary demonstration phase.
Phase 6's own exit criteria (installer, secrets, data deletion, malware
review, identity-preserving upgrade — PRD §21) are not expressed as
numbered acceptance tests in PRD §22; they are covered instead by
P6-TST-01 (Definition-of-Done checklist) and P6-TST-02 (compatibility
matrix).

---

## 12. Deferred and explicitly out of scope

### 12.1 PRD §6 non-goals (permanent, not phase-deferred)

The PRD states these will not be true of "the first production versions."
They are not backlog items to schedule later; they are constraints every
phase above already respects, restated here for completeness:

1. No unrestricted terminal, shell, PowerShell, Command Prompt, WSL,
   registry, or arbitrary-code execution for the LLM.
2. No permanent administrator operation.
3. No bypass of login prompts, UAC, CAPTCHAs, two-factor authentication,
   protected media, anti-cheat systems, or application security controls.
4. No guarantee of automating every Windows application.
5. No guarantee of reliable coordinate-based automation across
   monitor/DPI/layout/language/application-version changes.
6. No continuous fine-tuning of the LLM from private conversations.
7. No cloning of a real person's voice without documented permission.
8. No reading of passwords, payment-card details, private keys,
   authentication codes, or password-manager content.
9. No approval of destructive IDE-agent commands without fresh user
   confirmation.
10. No sending, posting, deleting, purchasing, transferring money,
    submitting forms, or publishing content without the required approval
    policy.
11. No multiple independent mouse-and-keyboard tasks running simultaneously
    in the same interactive Windows session.
12. Jarvis does not replace antivirus, backup, access control, or
    operating-system security.

### 12.2 Deferred beyond Version 1

These are named in the PRD as optional, later-phase-trigger, or open
decisions that this backlog does not commit to any of Phases 0–6:

- **Process separation for the TTS worker and elevated-action helper.**
  ARCHITECTURE §4.2 defines both as protocol boundaries today
  (`TtsProvider`, and an undefined elevation interface pending ADR-0009)
  but their promotion to genuinely separate OS processes is
  trigger-based, not scheduled.
- **Native (Rust/Tauri) shell.** ADR-0001 defers this explicitly, with
  reconsideration only after Phase 3, and only if a measured requirement
  (startup latency, idle memory, packaging reliability, crash isolation,
  update requirements, Windows integration limits) cannot reasonably be
  met in Python. It is not adopted for theoretical performance alone.
- **Optional encrypted sync or backup** (PRD open decision #11) — no
  phase above implements cross-device sync.
- **MSIX as the primary distribution format** (PRD open decision #12) —
  Phase 6 ships a signed installer; MSIX is explicitly "optional later"
  per PRD §12.1.
- **Public plugin signing policy and a full third-party plugin
  marketplace** (PRD open decision #10) — Phase 6 delivers SDK groundwork
  only (P6-PKG-08).
- **Dedicated credential-provider integration for password fields**
  (FR-080) — explicitly named in the PRD as "a future dedicated
  credential-provider integration," separately approved; not scheduled in
  Phases 0–6.
- **IDE-agent adapters beyond Google Antigravity** — FR-150 says
  "beginning with Google Antigravity as an application-specific
  integration"; no other IDE adapter is scheduled.
- **A trained, distributable "Jarvis" wake-word model as the default.**
  PROJECT_INPUTS.md records the development phrase as "Hey Jarvis" and
  "Jarvis" as the desired phrase; FR-011 requires the GUI not to promise
  reliability it has not earned. Training and distributing a dedicated
  "Jarvis" model is PRD open decision #6, unresolved.
- **Multiple simultaneous foreground-control tasks.** This is not a
  temporary limitation to lift later — PRD §7.1 and non-goal #11 make it
  an architectural constraint of the product, permanent by design.
