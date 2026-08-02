# Phase 0 — Foundation and Safety Architecture

- **Status:** Complete, awaiting user acceptance testing
- **Closed:** 2026-08-02
- **Final commit:** *not yet committed* — all Phase 0 work is uncommitted on `main` (see Uncommitted State)
- **PRD reference:** §21 "Phase 0 — Foundation and safety architecture"

---

## 1. Phase scope

Build the machinery every later capability must pass through, and **no
computer-control features at all**. Per PRD §21 the deliverables were:
repository and CI, architecture documents, data model, threat model, typed event
bus, tool schema, permission engine, audit log, task state machine,
configuration system, test harness, basic PySide6 shell and tray, Ollama health
check.

---

## 2. Requirements completed

### Exit criteria (PRD §21)

| Exit criterion | Status | Evidence |
|---|---|---|
| Application opens and sits in tray | Met | `tests/ui/test_shell.py`, plus a verified launch on the native Windows platform (tray visible, window opened, health task ran) |
| Settings persist | Met | `tests/acceptance::test_exit_2_*`, `tests/unit/test_config.py` |
| Single-instance enforcement works | Met | `tests/acceptance::test_exit_3_*`, `tests/unit/test_runtime_primitives.py` |
| Audit events are written | Met | `tests/acceptance::test_exit_4_*`, `tests/unit/test_audit_log.py` |
| Permission decisions are testable | Met | `tests/acceptance::test_exit_5_*`, `tests/unit/test_permission_engine.py` (44 tests) |
| No generic shell exists anywhere in the runtime | Met | `tests/security/test_no_shell.py` — AST scan of `src/`, plus a test proving the scanner detects real violations |

### Deliverables

Documents: `ARCHITECTURE.md` (722), `SECURITY.md` (598), `THREAT_MODEL.md` (487,
81 catalogued threats), `DATA_MODEL.md` (470), `docs/BACKLOG.md` (998),
`CHANGELOG.md`, `README.md`, ADR-0002 … ADR-0026 (26 ADRs total).

Code (`src/jarvis`, 53 files, 8,634 lines):

- **Configuration** — three layers (shipped defaults → user overrides → `JARVIS__*`
  env) into one frozen pydantic tree with `extra="forbid"`; only the diff from
  defaults persists; atomic writes.
- **Storage** — SQLite with WAL, foreign keys, per-thread connections, forward-only
  migrations. Schema version 1, ten tables.
- **Event bus** — frozen pydantic events, subclass matching, thread-safe publish,
  isolated handlers.
- **Audit log** — append-only JSONL (record of truth) plus a SQLite search index;
  full PRD §11.5 field set; redaction applied on the way in.
- **Permissions** — capability catalogue as data, 47 capabilities across four risk
  classes; five-step evaluation ladder; six grant scopes with expiry and revocation.
- **Tool pipeline** — `ToolSpec` covering all PRD §13.2 fields; registry allow-list
  with a two-layer prohibited guard; `ToolInvoker` implementing PRD §13.4's six
  checks.
- **Tasks** — ten-state machine with a validated transition table, durable store,
  checkpoints, evidence, exclusive resource locks, scheduler, crash recovery.
- **Runtime** — `JarvisCore` composition root, emergency stop, single-instance
  guard, worker supervisor, loopback-only Ollama health check.
- **UI** — tray with seven PRD §9.1 states, PRD §9.2 menu, fifteen PRD §9.3
  navigation areas (seven live), Qt event bridge.

CI: `.github/workflows/ci.yml` — tests on Windows and Linux × Python 3.11/3.12,
a separate security-invariants job, advisory dependency and licence review.

---

## 3. Requirements deferred

Deferred **by design** — Phase 0 explicitly excludes computer control:

| Area | Phase |
|---|---|
| Wake word, VAD, STT, TTS, conversation | 1 |
| Approval dialog UI | 1 |
| Secret store (ADR-0008) | 1 |
| Global emergency-stop hotkey | 1 |
| Application catalogue, UI Automation, browser automation, filesystem tools | 2 |
| Memory, skills, undo/recovery, clipboard, scheduling | 3 |
| Vision fallback, watchers, document understanding, notifications | 4 |
| IDE orchestration | 5 |
| Onboarding, installer, updates, packaging | 6 |

---

## 4. Important implementation details

1. **Layering is a tested invariant, not a convention.** Only the presentation
   layer may import PySide6, and no module may import a higher layer. The
   consequence: the entire engine is importable and testable with no Qt at all,
   and `python -m jarvis.main --check` runs headless.
2. **Tool machinery (L2) is separated from tool implementations (L3).**
   `jarvis.core.tools` holds the contract, registry and invoker; `jarvis.toolbox`
   holds the tools. The invoker reaches the lock manager through a protocol in
   `jarvis.core.tools.ports`, never by importing `jarvis.tasks`.
3. **`outcome` and `verification` are separate.** A tool that ran but could not
   confirm its effect is `succeeded` + `unverified`, which does **not** satisfy a
   task's success criteria (PRD FR-048, AT-018).
4. **Crash recovery never auto-resumes.** Interrupted tasks move to `PAUSED` with
   `recovered=true`; a human decides whether to continue, because a step already
   taken must not be repeated (PRD NFR-011).
5. **Bootstrap grants are real grants.** `system.read_health` and
   `system.read_audit_log` receive an `ALWAYS` low-risk grant at first start,
   written through the normal engine, visible in the Permissions screen and
   revocable. Without them Phase 0 could not report its own health, because no
   approval interface exists yet.
6. **Migrations execute statement-by-statement.** `executescript` implicitly
   commits, which would defeat the all-or-nothing transaction around a migration.

---

## 5. Tests executed

Command: `python -m pytest` — **386 passed, 0 failed** (verified 2026-08-02,
three consecutive clean runs). Coverage 89% statements / 130 partial branches.

| Suite | Tests |
|---|---|
| `tests/unit` | 201 |
| `tests/security` | 97 |
| `tests/integration` | 24 |
| `tests/ui` (offscreen Qt) | 26 |
| `tests/acceptance` | 38 |

Also verified outside the suite:

- `python -m jarvis.main --check` reports status and exits 0.
- The tray application launches on the **native Windows platform**: tray icon
  visible, main window opens, and a health-check task completes end-to-end
  through the full invoker pipeline against a live Ollama (v0.32.5, 4 models).

Not run: CI on GitHub (never executed — the workflow is committed but unproven),
Linux, and Python 3.12.

---

## 6. Known limitations

1. **No approval dialog**, so only capabilities holding a standing grant can run.
   The Phase 0 `ApprovalPort` denies by default.
2. **A timed-out tool is abandoned, not killed.** Python cannot forcibly stop a
   thread; the tool's own timeout is the primary defence and the invoker's is a
   backstop. Reported honestly as `timed_out` / `unverified`.
3. **In-process isolation is not a security boundary** (ADR-0004).
4. **Emergency stop has no global hotkey** — tray and window only.
5. **Dependency scanning is advisory**, not blocking.
6. **Folder-scope path canonicalisation is partial**: relative paths, environment
   variables and case are handled; junctions, symlinks and 8.3 short names are a
   Phase 2 filesystem concern.
7. **The `AutoApprovalPort` test double exists in shipped code** (`ports.py`). It
   refuses high-risk approvals, but it must never be wired into a running app.

---

## 7. Security review

Enforced and tested:

- No process-creation or dynamic-evaluation primitive anywhere in `src/`
  (`subprocess`, `os.system`, `os.popen`, `exec*`, `spawn*`, `startfile`, `fork`,
  `eval`, `exec`, `compile`, `shell=True`, `ShellExecute`, `CreateProcess`).
- No prohibited tool can be registered — by exact identity and by name pattern.
- No tool may require a prohibited capability, or understate its own risk.
- High-risk capabilities cannot hold an allow-grant broader than single-use.
- `always` allow is restricted to low risk.
- Nothing requests elevation; no packaging manifest declares
  `requireAdministrator` or `highestAvailable`.
- Secrets do not reach the audit log — verified end-to-end by passing a secret
  through the invoker and asserting it is absent from `audit.jsonl`.
- A non-loopback model endpoint is refused **without opening a socket**.
- Offline mode makes no network request at all (PRD AT-001).

Residual risks accepted for Phase 0: the Ollama endpoint is unauthenticated by
design (ADR-0007); in-process isolation is not a security boundary (ADR-0004);
`%LOCALAPPDATA%` NTFS ACLs against other local users are unverified
(THREAT_MODEL.md T-052); dependency supply chain is advisory only.

---

## 8. Relevant ADRs

Accepted in this phase: ADR-0002 (SQLite SSOT), ADR-0003 (closed capability set —
the most important), ADR-0004 (single process, thread isolation), ADR-0005 (typed
event bus), ADR-0006 (layered configuration), ADR-0007 (Ollama loopback
boundary), ADR-0008 (secret storage deferred), ADR-0009 (scoped elevation
policy), ADR-0010 (honest degraded UI).

Open, gated by later phases: ADR-0011 … ADR-0026. See
`docs/PROJECT_STATE.md` → Decisions Requiring Attention.

---

## 9. Entry conditions for Phase 1

Before Phase 1 implementation begins:

1. **User acceptance testing of Phase 0 is complete** and the results are known.
2. **Phase 0 work is committed.** The entire phase is currently uncommitted.
3. **ADR-0018 (search provider) and ADR-0019 (browser profile isolation)** are
   not required for Phase 1 but must be resolved before Phase 2.
4. The **approval dialog** is the first Phase 1 deliverable — it gates every
   capability beyond the two self-inspection grants.
5. Model, wake-word and voice assets must be present locally: Ollama with the
   configured planner model, an openWakeWord "Hey Jarvis" model, a
   faster-whisper `small` model, and Kokoro `bm_george`.

---

## 10. Corrections

*None. Add dated corrections here if a later discovery invalidates a statement
above; do not silently edit the record.*
