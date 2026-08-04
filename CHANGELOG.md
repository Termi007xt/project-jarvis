# Changelog

All notable changes to Project Jarvis are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — Phase 1: voice-first local assistant

Jarvis can now hold a conversation, hear you, speak back, and open the handful
of applications and websites you have approved. It still performs **no other
desktop or browser automation** — no clicking, typing, reading the screen or
touching your files.

### Added

- **Approval dialog.** Consequential actions can finally be authorised, which
  unblocks every capability beyond the two self-inspection grants. The prompt
  is anchored to the tray and does **not** take focus, so being asked never
  disturbs what you are doing. An unanswered request expires and is recorded as
  denied — silence is never taken as consent. Denials can be remembered per
  application, site or folder, and a waiting request is reachable from the tray
  and the Permissions screen without a mouse.
- **Local conversation.** A Conversation screen that talks to the local model.
  Every reply says where it came from — the model itself, a retrieved fact, an
  inference, a confirmed tool result, or an admission of uncertainty — and
  Jarvis will not tell you something was done unless a tool confirmed it.
- **Conversation history, with real controls.** History can be turned off
  globally or for one conversation, and deleted. A **private session** writes
  nothing to disk at all rather than writing and cleaning up afterwards.
- **A voice.** Kokoro `bm_george` for speech, faster-whisper `small` for
  listening, both running locally. Anything that looks like a password, key,
  card number or verification code is replaced with a description of what it
  was *before* Jarvis says it out loud.
- **Push-to-talk on F9** and an emergency-stop hotkey on `Ctrl+Alt+Pause`, both
  configurable. A combination another application already owns is reported as
  unavailable rather than silently doing nothing.
- **A Voice screen** showing which components are installed, which microphone is
  selected, and each voice's licence. It states the wake phrase literally and
  says plainly that single-word "Jarvis" is not available in this build.
- **Protected secret storage** using the Windows Data Protection API.
- **Start Jarvis at sign-in**, as a per-user setting that never needs
  administrator rights.
- **`--require-healthy`** for `--check`, when a caller needs an unreachable
  model runtime to be a failure rather than an honest report.
- **Opening approved applications and websites.** Brave, YouTube, YouTube Music,
  Xbox and Sea of Thieves, from a fixed catalogue. Jarvis chooses *which
  approved entry*, never which program — and it says an application opened only
  after it has seen the process running.
- **Media and volume keys**, and **desktop notifications**.
- **Jarvis speaks out loud.** Synthesis previously produced audio that nothing
  ever played. Speech is now audible, can be interrupted mid-sentence, and
  Jarvis reports how long it actually spoke for.
- **A one-time wake-word model installation**, `--install-wake-model`, which
  says exactly where the files go, is safe to repeat, and reports the model as
  installed only once the detector genuinely starts. The model is never bundled
  and is licensed for **non-commercial use only**.
- **The Voice screen's controls now work**: choosing a microphone, testing it
  with a live level meter, measuring the room, and previewing a voice. The list
  now names each device's audio system, so the same microphone appearing three
  times is finally something you can choose between.
- **A recording indicator.** The tray and the Voice screen both show whenever
  the microphone is open.
- **A listening switch.** Turn on "Start listening" and Jarvis waits for
  "Hey Jarvis", then transcribes what follows and answers it. It says plainly
  that the wake model is a shared one that has not been tuned to your voice.
- **Push-to-talk is now optional** and shows its key, so you can turn it off and
  use the wake phrase instead.
- **The Voice screen shows what it heard**, with a confidence figure, so a
  misheard word looks like a mishearing rather than a bad answer.
- **Your name.** Set it on the Conversation screen and it replaces "You" in the
  transcript, survives restarts, and is given to the model so Jarvis can address
  you properly. Leave it empty and nothing changes.
- **Audio cues.** Short tones for "I heard the wake phrase and I am recording",
  "I am working on it", and "that is done" — so Jarvis is legible from the tray
  without its window on screen. Turn them off with `audio.cues_enabled`.
- **`web.search`.** Searching by words rather than by URL, with Google (the
  default), DuckDuckGo or YouTube. Jarvis builds the address, so a query with
  spaces, symbols or a colon in it works. It says outright that it cannot read
  the results.
- **Stop speaking**, in the tray menu. It interrupts the sentence and does
  nothing else: no task is cancelled and no resource lock is released.
- **`audio.speak_replies`** — `always`, `when_useful` (the default) or `never`.

### Changed

- Deleted conversation history is now genuinely erased from the database file.
  Previously the rows were unlinked but their contents stayed readable in freed
  pages.
- The Home screen reports the voice stack, the secret store and the conversation
  engine, and no longer describes the build as Phase 0.
- **Push-to-talk is press-to-start, not hold-to-talk.** Windows reports only the
  key press for a global hotkey, so holding F9 never worked. Press it, speak,
  and it stops on its own when you stop talking.
- In **offline mode** the speech models are pinned to their local cache. Loading
  a voice or transcription model previously contacted the Hugging Face Hub,
  which was a network request from a component presented as entirely local.
- **Speaking to Jarvis no longer drags the window in front of what you were
  doing.** Speaking is meant to be the way to use Jarvis *without* the window;
  taking over the screen because someone spoke is the intrusion the non-modal
  approval panel exists to avoid.
- **A spoken question is now answered out loud**, and only when the answer is
  worth hearing. Questions are answered, problems and follow-up questions are
  always spoken, and an instruction that simply worked — "open Brave" — gets a
  short cue instead of a sentence about a window you can already see. A *typed*
  request is never answered aloud, whatever the setting says.
- **Emoji, formatting and web addresses are no longer read out.** The
  phonemiser expands every character to its Unicode name, so "Opening Brave 🦁"
  was spoken as "Opening Brave lion face", and a link was spelled out in full.
  The written transcript still shows every character; only the spoken copy is
  stripped, and a code block is announced rather than recited.
- **"Open YouTube Music" opens the app you installed**, not another browser tab.
- **Emergency stop now stops Jarvis talking**, from the tray, the Home screen
  and the hotkey. It cancelled tasks and released locks while continuing to
  speak over the silence it had just created.

### Fixed

- **Typing a message produced no reply at all.** The Conversation screen sent
  the message onto a worker that had already been destroyed, so nothing was ever
  asked of the model — and because nothing failed, nothing was reported.
- **"Thinking…" silently reverted to "Ready"** part-way through an answer.
- **Quitting while Jarvis was answering could kill the process outright.**
- **No button on the Voice screen did anything.** They were enabled and
  connected to nothing. Push-to-talk reported that the voice stack was
  unavailable while it was fully installed and working.
- **Jarvis claimed it had spoken when it had not.** `voice.speak` reported a
  confirmed success on the strength of having produced audio, while nothing
  played it. It now fails plainly if no sound reached the output device.
- **The emergency-stop hotkey never worked.** The key registered and the press
  was then dropped on its way to the application. It also moved off `Pause`,
  which many keyboards do not have, to **`Ctrl+Alt+End`**.
- **Push-to-talk never worked**, for the same reason. F9 was never the problem.
- **Desktop notifications from tools never appeared**, and the tool reported
  showing them anyway.
- **The recording indicator never lit**, so the microphone could open with
  nothing on screen saying so.
- **No microphone could be opened at all** on a machine whose default input is
  an MME device — which is most of them. Jarvis asked every device for settings
  only one kind of device accepts.
- **Asking Jarvis to say something failed outright** with an internal error: it
  reserved a lock by a name that does not exist.
- **Some questions came back completely blank**, under a confident source
  label, which is indistinguishable from being ignored. When the model returns
  nothing, Jarvis now says so — and says what its tools did, if they did
  anything — rather than rendering the silence as an answer.
- **Interrupting Jarvis mid-sentence never actually worked.** Three separate
  causes: the wake threshold during playback demanded a score of 0.96, which is
  effectively unreachable; the self-echo check compared the microphone's level
  against the volume of Jarvis's own audio data, which are not the same kind of
  measurement, and rejected real interruptions almost every time; and emergency
  stop did not stop speech at all. The Voice screen now also says plainly that
  speaking over Jarvis cannot interrupt it while the microphone is closed.
- **Searching the web produced a broken address.** The model was building and
  encoding search URLs itself; one came back from Google as an error. Jarvis
  builds them now.
- **"Open Steam" refused to open Steam**, because the entry insisted on a game
  to launch. With no game named, it opens the client.
- **Being asked to open an unapproved application produced invented
  instructions** pointing at a settings screen that does not exist.
- **A cue could leave an audio stream open** after the sound had finished, which
  in the worst case corrupted memory as the process exited.

### Known limitations

- **Wake-word detection is installed but always-listening stays off.** The
  pretrained "Hey Jarvis" model is measured and working; per-user enrolment is
  not built, and ADR-0016 does not permit always-listening without it.
  Single-word "Jarvis" is not detected — measured 0 of 4 attempts.
- **Barge-in is unproven on real hardware.** Interrupting Jarvis by voice now
  has thresholds that can actually be met, but the rate at which it mistakes its
  own voice for yours has still not been measured, so it should not yet be
  relied upon. It also needs the microphone open, which means listening turned
  on. `Ctrl+Alt+End` and the tray's **Stop speaking** work in every state and
  are the routes to trust until that measurement exists.
- **Jarvis has no clock.** It can only answer "what time is it?" from the model,
  which does not know. There is no time tool yet.
- **Only catalogued applications can be opened.** Naming one that is not in the
  catalogue is refused, and there is no in-application way to add one.

---

## [0.1.0.dev0] — 2026-08-01 — Phase 0: foundation and safety architecture

The foundation every later capability has to pass through. **No
computer-control features**: no audio, no automation, no browser, no filesystem
tools, no screen capture, no clipboard.

### Documentation

- `ARCHITECTURE.md` — process and thread model, layering, the six-step control
  flow, extension points, and an honest statement of what exists today.
- `SECURITY.md` — security policy: trust boundaries, capability risk classes,
  the prohibited list and its enforcement, permission model, elevation policy,
  secrets, audit requirements, filesystem safety, supply chain.
- `THREAT_MODEL.md` — STRIDE plus LLM-agent-specific analysis; 81 catalogued
  threats, trust boundaries, actors, phase-gated mitigations, and the residual
  risks accepted for Phase 0.
- `DATA_MODEL.md` — the schema as built, entity definitions, retention,
  migration policy and export rules.
- `docs/BACKLOG.md` — phased implementation backlog for Phases 0–6 with
  requirement and acceptance-test coverage matrices.
- `docs/decisions/ADR-0002` … `ADR-0026` — the nine Phase 0 architectural
  decisions and the sixteen open decisions from PRD section 25.
- `README.md` — what this is, what it is not, and how to run it.

### Added — configuration and storage

- Layered configuration: shipped defaults, user overrides, environment
  overrides, validated into one frozen pydantic tree with `extra="forbid"`.
  Only the difference from defaults is persisted, and writes are atomic.
- `VaultPaths`: single point of Windows environment-variable expansion; the
  whole vault relocates via `--data-dir` or `JARVIS_DATA_DIR`.
- SQLite vault with WAL, foreign keys, per-thread connections and versioned
  forward-only migrations. A database newer than the running build is a hard
  startup failure.

### Added — core safety machinery

- Typed event bus: frozen pydantic events, subclass matching, thread-safe
  publish, isolated handlers.
- Audit log: append-only JSONL plus a SQLite search index, with the PRD section
  11.5 field set. Redaction happens on the way in, by field name and by value
  shape; clipboard, transcript and document text are described, never stored.
- Capability catalogue: PRD section 11.1 risk classification expressed as data.
- Permission engine: unknown denied, prohibited denied unconditionally, high
  risk always asks, scoped grants (once, session, task, application, folder,
  always) with expiry and revocation. `always` is low-risk only; high risk can
  never hold a standing allow.
- Tool contract implementing PRD section 13.2 in full, including reversibility
  and rollback metadata.
- Prohibited-capability guard: denylist by exact identity and by name pattern.
- Tool invoker: the single choke point implementing PRD section 13.4's six
  checks, with bounded timeouts, bounded retries, declared failure codes, and a
  `succeeded` that requires verification.

### Added — tasks

- Ten-state task machine with an explicit, validated transition table; terminal
  states have no outgoing edges.
- Durable task store: tasks, transition history, checkpoints, evidence, task
  trees with cascade delete.
- Resource locks: exclusive, persisted, owner-attributed, all-or-nothing over a
  sorted set, with stale reclamation after a crash.
- Scheduler: queue, lock arbitration, bounded concurrency, cooperative pause
  and cancel, bounded retries. Tasks blocked on a lock stay queued with a
  visible reason.
- Crash recovery: interrupted tasks are paused and marked recovered, never
  auto-resumed; stale locks are released; everything is audited.

### Added — runtime and shell

- `JarvisCore`: composition root with defined startup and shutdown ordering,
  importing no GUI code.
- Emergency stop: cancels tasks, releases locks, stops workers and reports
  exactly what was stopped, leaving the application running.
- Single-instance guard: Windows named mutex, with a lock-file fallback that
  reclaims a file left by a dead process.
- Worker supervisor with cooperative stop; the periodic health check runs off
  the UI thread.
- Ollama health check: loopback-only, offline-mode aware, explicitly timed out.
- `system.health`: the one registered tool, read-only, routed through the full
  invoker pipeline.
- PySide6 tray with the seven PRD section 9.1 states, distinguished by shape and
  accessible text as well as colour, and the PRD section 9.2 menu. Unavailable
  entries are shown disabled and name the phase that delivers them.
- Main window with all fifteen PRD section 9.3 navigation areas; seven are live
  against real data and the rest state plainly that they are not implemented.
- Qt event bridge marshalling domain events onto the GUI thread.
- CLI: `--check`, `--data-dir`, `--log-level`, `--allow-multiple-instances`.

### Added — tests and CI

- 250+ tests across unit, security, integration, UI (offscreen Qt) and
  acceptance suites. Every test gets an isolated vault; none requires Ollama, a
  microphone, a GPU or the network.
- `tests/security/test_no_shell.py`: AST scan of the whole package for
  process-creation and dynamic-evaluation primitives; the build fails if one
  appears. Includes a test that the scanner itself detects violations.
- `tests/security/test_layering.py`: only the presentation layer may import Qt,
  and no module may import a higher layer.
- `tests/acceptance/`: one test per Phase 0 exit criterion from PRD section 21.
- GitHub Actions: tests on Windows and Linux across Python 3.11 and 3.12, a
  separate security-invariants job, and advisory dependency and licence review.

### Security

- No shell, Command Prompt, PowerShell, WSL or arbitrary-code execution exists
  anywhere in the runtime, enforced in three layers (ADR-0003).
- The application runs without administrator rights; nothing requests
  elevation, and a test enforces it.
- The local model endpoint must resolve to loopback or the adapter refuses and
  audits the refusal.
- Offline mode is enforced at the adapter boundary, not by caller discipline.
- The Phase 0 approval port denies by default: with no approval interface, a
  capability requiring approval simply cannot run.

### Known limitations

- No approval dialog exists yet, so only capabilities with a standing grant can
  run. Two self-inspection capabilities receive a visible, revocable bootstrap
  grant at first start.
- In-process isolation is not a security boundary (ADR-0004).
- A timed-out tool is abandoned, not killed; Python cannot forcibly stop a
  thread. The tool's own timeout remains the primary defence.
- Secret storage is deferred to Phase 1, when the first secret exists
  (ADR-0008).

[Unreleased]: https://example.invalid/compare/v0.1.0.dev0...HEAD
[0.1.0.dev0]: https://example.invalid/releases/tag/v0.1.0.dev0
