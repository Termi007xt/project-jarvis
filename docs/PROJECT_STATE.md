# Project State

## Snapshot
- **Last updated:** 2026-08-02
- **Current branch:** `main`
- **HEAD commit:** `7304363` — *predates all Phase 0 work; the entire phase is uncommitted*
- **Active phase:** Phase 0 complete → awaiting user acceptance testing before Phase 1
- **Overall status:** Green. 386/386 tests pass. Nothing blocked.

## Current Objective
Phase 0 (foundation and safety architecture) is implemented and verified. The
current objective is **user acceptance testing of Phase 0** and committing the
work. Phase 1 implementation has not started and must not start until acceptance
results are known.

## Verified Working
Confirmed by a passing test or direct observation on 2026-08-02:

- `python -m pytest` → **386 passed, 0 failed**, 89% statement coverage, three
  consecutive clean runs.
- `python -m jarvis.main --check` → prints status, exits 0.
- Tray application launches on the **native Windows platform**: tray icon
  visible, main window opens, health-check task completes end-to-end through the
  full invoker pipeline against live Ollama (v0.32.5, 4 models installed).
- Configuration persists across a full restart; only the diff from defaults is
  written to `user.yaml`.
- Single-instance enforcement refuses a second core.
- Audit records are written to `logs/audit.jsonl` and indexed in SQLite; a secret
  passed through the invoker does **not** appear in the log.
- Crash recovery pauses interrupted tasks, marks them `recovered`, reclaims stale
  locks, and never auto-resumes.
- Two tasks needing `foreground_desktop` never run together — one runs, one stays
  queued with a visible reason.
- A non-loopback Ollama endpoint is refused without opening a socket; offline
  mode makes no network request.
- No process-creation or dynamic-evaluation primitive exists anywhere in `src/`.

## Completed in Current Phase
All PRD §21 Phase 0 deliverables and all six exit criteria. Full detail in
`docs/phase-reports/PHASE-00-FOUNDATION.md`.

Summary: layered typed configuration; SQLite vault with migrations; typed event
bus; audit log with redaction; capability catalogue and permission engine; tool
contract, registry, prohibited guard and six-step invoker; ten-state task machine
with locks, checkpoints, scheduler and crash recovery; single-instance guard;
worker supervisor; Ollama health check; PySide6 tray and main window; CI;
26 ADRs; 5 architecture documents; 386 tests.

## In Progress
Nothing is partially implemented. The working tree is complete and coherent.

Awaiting: user acceptance test results (see the run-and-test guide the assistant
provided, and §"Next Exact Steps" below).

## Blocked or Failing
Nothing is blocked and no test is failing.

Two known non-blocking limitations that are *by design* for Phase 0:

- **No approval dialog exists**, so any capability requiring approval is denied.
  Only `system.read_health` and `system.read_audit_log` hold standing grants.
  This is the first Phase 1 deliverable.
- **A timed-out tool is abandoned, not killed** — Python cannot forcibly stop a
  thread. Reported honestly as `timed_out` / `unverified`.

## Tests and Quality Checks
- **Last successful:** `python -m pytest` → 386 passed (2026-08-02).
  Per suite: unit 201, security 97, integration 24, ui 26, acceptance 38.
- **Last failed:** none since the two scheduler-race fixes on 2026-08-01
  (`test_emergency_stop_*` and `test_the_task_state_machine_is_persistent` — both
  were test races against the live scheduler, now deterministic).
- **Not yet run:** GitHub Actions CI (the workflow is committed but has never
  executed); Linux; Python 3.12; `pip-audit`; multi-monitor / DPI variations;
  Windows startup registration (Phase 1).
- **Known test limitations:** no test needs Ollama, a microphone, a GPU or the
  network, so nothing here proves real-hardware behaviour. UI tests run
  offscreen. Coverage is lowest in `jarvis/ui/app.py` (46%) and
  `single_instance.py` (61%, Windows-mutex branch untested because the suite
  forces the lock-file path).

## Decisions Requiring Attention
Nine Phase 0 ADRs are Accepted. Sixteen remain open, gated by phase:

| Needed before | ADRs |
|---|---|
| Phase 2 | ADR-0018 search provider · ADR-0019 browser profile isolation · ADR-0023 adapter isolation |
| Phase 3 | ADR-0024 data-retention defaults |
| Phase 4 | ADR-0025 screenshot ceiling (default `task_only` accepted) |
| Phase 6 | ADR-0011 product name · ADR-0012 shell technology · ADR-0013 installer · ADR-0016 wake-word training · ADR-0020 skill signing · ADR-0021 encrypted sync · ADR-0022 MSIX · ADR-0026 code signing and updates |

Partially settled: ADR-0014 default voice (Kokoro `bm_george` accepted for
development; redistribution licensing open), ADR-0015 TTS providers, ADR-0017
embedding model (configured, not benchmarked).

**Nothing on this list blocks Phase 1.**

## Next Exact Steps
1. Run the Phase 0 acceptance tests and report results (see the guide provided
   with this handoff; covers the six exit criteria plus tray, permissions, audit,
   crash recovery, offline mode and the security invariants).
2. Commit Phase 0 on a branch — do not commit to `main` without asking. Suggested:
   `git switch -c phase-0/foundation` then a single coherent commit of the 40
   changed/untracked paths.
3. Decide the answers to the open questions raised in the acceptance guide
   (approval-dialog UX, wake-word strategy, STT/TTS asset availability, whether
   `--check` should exit non-zero when Ollama is unreachable).
4. Only then: begin Phase 1 with the approval dialog (`ApprovalPort` → Qt), since
   it gates every other capability.

## Uncommitted or Temporary State
- **The entire Phase 0 implementation is uncommitted.** `git status` shows
  ~40 changed/untracked paths: `src/`, `tests/`, `.github/`, `pyproject.toml`,
  all five architecture documents, `README.md`, `CHANGELOG.md`, `docs/BACKLOG.md`,
  ADR-0002 … ADR-0026, `graphify-out/`, plus modified `.gitignore` and
  `config/defaults.yaml`.
- **New in this handoff:** `CLAUDE.md`, `docs/PROJECT_STATE.md`,
  `docs/phase-reports/PHASE-00-FOUNDATION.md`, updated `.gitignore` and
  `.graphifyignore`.
- No temporary migrations or compatibility shims exist.
- No process needs to be running. Ollama is optional — the health check reports
  it as unreachable rather than failing.
- Scratch vaults created during verification live under the system temp
  directory, not in the repository.

## Relevant References
- **Requirements:** `PRD.md` §21 (phases), §22 (acceptance tests AT-001…AT-034)
- **Phase report:** `docs/phase-reports/PHASE-00-FOUNDATION.md`
- **Operating contract:** `CLAUDE.md`
- **Architecture:** `ARCHITECTURE.md` §12 (what exists today), §13 (known gaps)
- **Security:** `SECURITY.md` §14 (Phase 0 status table, reconciled with shipped code)
- **Threats:** `THREAT_MODEL.md` §6 (residual risks live in Phase 0)
- **Plan:** `docs/BACKLOG.md` (Phase 1 work items and exit criteria)
- **Graph:** `graphify-out/GRAPH_REPORT.md` — 121 communities; god nodes
  `JarvisCore` (100 edges), `EventBus` (76), `ToolCall` (71), `AuditLog` (70),
  `Database` (62). Graph verified fresh on 2026-08-02: 107 tracked files indexed,
  none modified since.
