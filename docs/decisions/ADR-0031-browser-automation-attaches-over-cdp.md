# ADR-0031: Browser automation attaches over CDP — Playwright is a client, never a launcher

- **Status:** **Proposed** — for acceptance at the Phase 2 stage 0 checkpoint
- **Date:** 2026-08-04
- **Deciders:** Project owner (mechanism delegated to the implementer on 2026-08-04, "whichever will work best and most accurate")
- **PRD reference:** FR-052, FR-056, FR-072, §12.1, §21 (Phase 2 exit criteria)
- **Phase:** 2

## Context

Phase 2 requires DOM-first browser automation: selectors before pixels, a visible browser by default (FR-052), driving the dedicated Brave profile ADR-0019 fixes. Playwright is the tool ARCHITECTURE.md §3 and PRD §12.1 already name for this.

**Playwright's normal mode of operation starts a browser process.** `launch()` and `launch_persistent_context()` both create one. ADR-0029 authorises exactly one process-creation call site in the entire product — `launch_argv` in `jarvis/toolbox/launch.py` — and the project owner's direction when accepting it was explicit: the exception must not be broadened and no second call site may be added.

So the obvious implementation is not available, and the reason it is unavailable deserves stating precisely, because the constraint is easy to satisfy on paper while breaking in substance.

### The part that makes this worse than an ordinary rule

`tests/security/test_no_shell.py` enforces ADR-0003 and ADR-0029 by **AST-scanning `src/`**. It is the most load-bearing control in the repository and it fails the build rather than a lint.

It cannot see inside `site-packages`. If the product called `playwright.chromium.launch_persistent_context(executable_path=brave)`, a process would be created by code the scanner never reads. The `ALLOW_LIST` would stay empty, the security suite would stay green, and the single-call-site invariant would be false. The suite would report exactly the same thing whether the invariant held or not.

That is the Phase 1 defect class — a green suite compatible with a broken product — applied to the repository's most important control. A decision that relies on remembering not to call a function is not a control; it needs to be structural.

## Options considered

### Option A — Playwright launches Brave
Use `launch_persistent_context(executable_path=...)`, the best-documented and most reliable Playwright path.
**Pros:** simplest; Playwright's native use case; fewest attachment surprises; the library manages browser lifetime.
**Cons:** creates a second process-creation call site in substance while leaving the AST scan green, which makes it worse than an openly declared exception rather than better. Directly contrary to the owner's direction on ADR-0029. Rejected.

### Option B — We launch Brave; Playwright connects over CDP
Brave is started through the existing `launch_argv` with a `--remote-debugging-port` argument supplied by a catalogue entry. Playwright attaches with `connect_over_cdp`.
**Pros:** the product's process-creation surface is unchanged — still exactly one call site, still the one ADR-0029 reviewed; Playwright becomes a client of a browser the product owns; the browser is launched by the same audited, validated, interpreter-denylisted path as every other application, so the launch is permissioned and verified like any other; ADR-0019's chosen profile mechanism is expressed as ordinary catalogue arguments.
**Cons:** a CDP port is an unauthenticated local control channel — any local process that can reach it can drive that browser, including one holding live logins. Playwright's connect path is less exercised than its launch path. Browser lifetime becomes the product's responsibility rather than the library's.

### Option C — Playwright's bundled Chromium
**Cons:** contradicts PRD §12.1's committed "dedicated persistent Brave profile" and ADR-0019, which selected a Brave profile specifically. Already ruled out there. Rejected.

## Decision

**Option B.** Brave is launched through `jarvis.toolbox.launch.launch_argv`; Playwright attaches over CDP and never launches anything.

The framing worth keeping: this is **not a broadening of ADR-0029**. It is a demonstration that the single authorised call site is sufficient for browser automation. That is the more useful thing to have on the record, because it means the next capability that wants to start a process has a worked example of how to do so without a new exception.

### Constraints, enforced in code rather than by convention

1. **The debugging port is never fixed.** An ephemeral port is chosen per session. A well-known port would be a standing, predictable control channel on the user's browser.
2. **Loopback only.** Never `--remote-debugging-address=0.0.0.0`. The port must not be reachable off the machine.
3. **Session-scoped.** The port opens when a browser automation task starts and the browser is closed when the task ends. There is no long-lived listening browser.
4. **`browser_profile:jarvis` is held for the session's lifetime** through the existing `ResourceLockManager`, so two tasks cannot share one debugging channel.
5. **The port never reaches the model, the audit log's recorded parameters, or an export.** It is infrastructure, not a tool argument the planner chooses.
6. **Playwright is never asked to launch.** `launch`, `launch_persistent_context` and `executable_path` do not appear in `src/`. This is asserted by a test in `tests/security/`, so the rule fails the build rather than relying on review.

### How a per-session port survives ADR-0029 constraint 5

Constraint 5 requires that arguments come from a per-entry typed template rather than from arbitrary caller input. A debugging port is expressed as a new `ArgumentKind`, validated as an integer in the ephemeral range — structurally the same as `ArgumentKind.STEAM_APP_ID`, which is validated as digits. The catalogue entry fixes *what kind of argument the entry accepts*; the engine supplies the value; the model never sees or supplies it. Constraint 3 is untouched: the model still names an entry, never a binary and never a port.

## Measurement

Taken on the target machine, 2026-08-04, by `tools/browser-lab/test_cdp_attach.py`:

| Configuration | Result |
|---|---|
| `brave.exe --profile-directory=Jarvis --remote-debugging-port=<ephemeral>` | **CDP opened.** `Chrome/151.0.7922.71`, protocol 1.3 |
| `brave.exe --user-data-dir=<temp> --profile-directory=Jarvis --remote-debugging-port=<ephemeral>` | **CDP opened.** Same build |

This ADR was written expecting the first row to fail — Chromium refuses remote debugging against its default user-data directory, and ADR-0019 Option A selects a profile inside it. The expectation was wrong for Brave 151, and the measurement is recorded rather than the expectation.

`tools/browser-lab/test_playwright_attach.py` covers the second half — that `connect_over_cdp` attaches to a browser started this way and that a result list is addressable by index.

## Consequences

**Residual risk, accepted and not claimed to be solved:** while an automation session is live, a local process running as the same user can reach the CDP port and drive the browser. The mitigations above bound the window and the reachability; they do not remove the risk. It is bounded by the same trust assumption the product already makes — a local attacker running as the user can also read the vault. It is recorded in `THREAT_MODEL.md` rather than treated as closed.

**Browser lifetime becomes the product's responsibility.** A crashed automation task must not leave a browser listening on a debugging port. The session teardown path is therefore not optional cleanup; it is a security control, and the existing stale-lock reclamation in `ResourceLockManager` is the model for recovering it after a crash.

**FR-058's CAPTCHA pause is unaffected.** The user interacts with an ordinary visible Brave window using their normal mouse and keyboard. Attaching over CDP does not introduce the automation banner that a Playwright-launched browser shows, which is a small unplanned benefit for ADR-0019 criterion 3.

## Related

ADR-0003 (closed capability set), ADR-0029 (the single authorised process-creation call site — this ADR consumes it and does not widen it), ADR-0019 (which profile the browser opens), ADR-0023 (the adapter driving this stays in-process), ARCHITECTURE.md §3, §11, §13 gap 2, `tests/security/test_no_shell.py`.
