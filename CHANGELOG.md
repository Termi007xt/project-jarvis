# Changelog

All notable changes to Project Jarvis are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet. Phase 1 (voice-first local assistant) has not started; it is
awaiting review of Phase 0.

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
