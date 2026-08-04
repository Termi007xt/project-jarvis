# ADR-0029: Launching approved applications — the one authorised process-creation call site

- **Status:** **Accepted** (decided 2026-08-02 by the project owner, who directed
  that the exception must not be broadened and no second process-creation call
  site may be added)
- **Date:** 2026-08-02
- **Deciders:** Project owner
- **PRD reference:** FR-060, FR-062, FR-063, FR-064, §21 (Phase 1 exit criteria), §13.3, AT-003
- **Phase:** 1

## Context

ADR-0003 closed the capability set: Project Jarvis has no generic execution path,
and `tests/security/test_no_shell.py` enforces it by AST-scanning `src/` for
every primitive that can start a process or evaluate code — `subprocess`,
`multiprocessing`, `os.system`, `os.popen`, the `os.exec*`/`os.spawn*` family,
`os.startfile`, `ShellExecuteW`/`ShellExecuteExW`, `CreateProcessW`, `WinExec`,
`eval`, `exec` and `compile`. Its `ALLOW_LIST` is empty. That test is the single
most load-bearing control in the repository and it fails the build, not a lint.

Phase 1 must nonetheless deliver, per PRD §21:

> Exit criterion: *User can open Brave, YouTube, YouTube Music, Xbox, and Sea of Thieves*

and AT-003:

> When the user says "Jarvis, open Sea of Thieves," the configured game launches
> and Jarvis verifies its process or window.

**There is no way to start a program on Windows without one of the denied
primitives.** Every documented route — `CreateProcess`, `ShellExecuteEx`, the
`IApplicationActivationManager` COM interface, `os.startfile`, `subprocess` —
ultimately creates a process, and the first four are named in the denylist
directly. This is not an oversight in the test; the test's own comment
anticipates this ADR:

> *"Explicitly allowed exceptions. Every entry must cite an ADR. Empty in Phase 0:
> nothing yet needs to start a process. Phase 1's approved-application launcher
> will add exactly one entry here, reviewed and recorded."*

So the question is not *whether* to permit process creation. It is how to permit
exactly enough of it to launch a catalogued application, and nothing more — in
particular, never enough to become the generic shell ADR-0003 exists to forbid.

The distinction that matters: **a shell interprets a string; a launcher executes
an argument vector.** `cmd.exe /c <string>` is arbitrary execution because the
string is a program in a language. `CreateProcess("C:\\...\\brave.exe",
["--profile-directory=Jarvis", "https://youtube.com"])` is not, because there is
no interpreter between the argument vector and the process, and because the
executable is chosen from a fixed catalogue rather than from the argument.

## Decision

**Authorise exactly one call site**, in a new module `jarvis.toolbox.launch`,
using `subprocess.Popen` with an argument **list** and `shell=False`. Nothing
else in `src/jarvis` may import `subprocess` or any other process primitive.

The call site is subject to all nine of the following constraints. Each is
enforced by a test, not by convention.

1. **List argv only, never a string.** The first argument to `Popen` must be a
   `list[str]`. A string command line would let the OS re-parse it, which is the
   quoting-injection hazard this constraint exists to remove.
2. **`shell=False` is passed explicitly**, never defaulted, so the intent is
   visible at the call site and greppable.
3. **The executable is never derived from model output, web content, a document,
   a filename, a transcript or any other untrusted source** (SECURITY.md §2). It
   comes from an application-catalogue entry keyed by a validated identifier. The
   model proposes *which catalogue entry*, never *which binary*.
4. **The executable is denylisted against interpreters and shells.** `cmd.exe`,
   `command.com`, `powershell.exe`, `pwsh.exe`, `wsl.exe`, `bash.exe`, `sh.exe`,
   `wscript.exe`, `cscript.exe`, `mshta.exe`, `rundll32.exe`, `regsvr32.exe`,
   `python.exe` and `conhost.exe` are refused by basename regardless of path.
   Adding a catalogue entry naming one of these is a registration-time error, not
   a runtime surprise.
5. **Arguments come from a per-entry typed template**, not from free text. A
   catalogue entry declares its argument shape (for example, a URL for a browser,
   or a Steam app id) and the value is validated against that type before it
   reaches the vector. A URL argument must parse as `http`/`https` and is passed
   as a single vector element.
6. **UWP and Store applications** (Xbox, and Sea of Thieves when installed from
   the Microsoft Store) are launched via the fixed broker
   `explorer.exe shell:AppsFolder\<AUMID>`, where the AUMID matches a strict
   pattern and comes from the catalogue. `explorer.exe` is a fixed constant in
   the code, never a catalogue value, and the AUMID is a single vector element.
   This route is used because Store applications have no launchable executable
   path; it is still one process, one argument vector, no interpreter.
7. **The environment is inherited, never constructed from untrusted input.** No
   `env=` built from parameters, so `PATH`-style redirection is not reachable.
8. **Every launch passes through `ToolInvoker`** and therefore through the
   allow-list, schema, permission, lock, approval and audit pipeline. There is no
   direct call path from a plan to `Popen`. `app.open_approved` and
   `web.open_approved_url` are both low risk with `scope_kind` set, so a user can
   scope a grant to one application or one URL host.
9. **Launch is verified, not assumed** (FR-064, PRD FR-048). The tool reports
   `succeeded` only when the process or window is observed to exist; otherwise
   the outcome is `unverified`, which does not satisfy a task's success criteria.
   `Popen` returning without raising is not evidence that an application started.

`ALLOW_LIST` gains exactly one entry, citing this ADR by number. The existing
assertion message — "Do not add these to `ALLOW_LIST` to make this pass" — stays
exactly as it is, and a test asserts the allow-list has **at most one** entry, so
a second exception cannot be added quietly alongside the first.

### What this ADR does not authorise

Terminating processes, force-closing applications (`app.force_close` is high risk
and Phase 2), passing user or model text as an executable path, running installers
or downloaded content, elevation of any kind (ADR-0009 still holds), and
`multiprocessing` for the Qwen3-TTS worker (FR-037/FR-038) — which is a genuinely
different problem, needs its own ADR, and is deferred out of Phase 1.

## Options considered

**One narrowly-constrained `subprocess.Popen` call site** *(chosen)* — the
smallest primitive that can express "run this catalogued program with these
validated arguments", with no interpreter in the path. Cost: it is a real hole in
an otherwise absolute rule, and the rule's absoluteness was part of its value.

**`os.startfile` / `ShellExecuteExW`** — shorter code, and it handles URIs and
document types natively. Rejected: it delegates the choice of *what to run* to
the registry's file-association table, which is per-machine mutable state outside
Jarvis's control, so the program actually executed is decided by something Jarvis
does not own and cannot audit. `Popen` with an explicit executable is strictly
more predictable, and predictability is the property being bought here.

**`IApplicationActivationManager` COM activation for everything** — the officially
sanctioned route for Store applications and, unlike `ShellExecute`, not in the
denylist by name. Rejected as the *general* mechanism because it does not launch
ordinary Win32 executables at all, so it would be a second mechanism rather than a
replacement, and hand-rolled `ctypes` COM marshalling is materially more code to
get wrong than a `Popen` call for no additional safety. The `explorer.exe
shell:AppsFolder` broker in constraint 6 covers the same case with the primitive
already being authorised.

**Ship Phase 1 without a launcher** — honest, and it keeps `ALLOW_LIST` empty.
Rejected because it drops a stated PRD exit criterion and an acceptance test, and
because the launcher is the least dangerous consequential capability in the whole
product; deferring it does not avoid the decision, it only postpones it to a phase
where the surrounding automation makes the blast radius larger.

## Enforcement

Tests that must exist and pass before this ADR moves to Accepted:

- `tests/security/test_no_shell.py` — `ALLOW_LIST` contains **at most one** entry,
  and that entry names this ADR.
- The launcher refuses a catalogue entry whose executable basename is on the
  interpreter denylist, at registration time.
- The launcher raises rather than accepting a `str` command line — the argv-list
  invariant is asserted in code, not merely documented.
- `shell=True` appears nowhere in `src/` (already covered, and must stay covered).
- A model-supplied string cannot become the executable: a test drives a proposed
  tool call whose parameters contain a path and asserts the launched executable
  is still the catalogue's.
- A URL argument that is not `http`/`https` is rejected — in particular `file:`,
  `javascript:` and any custom scheme not declared by the catalogue entry.
- `tests/acceptance/test_at003_app_launch.py` — AT-003, launch plus verification,
  against a fake process probe so it needs no real game.

## Consequences

### Positive
The one capability Phase 1 needs is expressed in the narrowest primitive that can
express it, with the executable chosen by the user's catalogue rather than by the
model, by a filename, or by machine-global registry state. The rule stays testable
and the exception stays countable: one entry, one ADR, one call site.

### Negative
`tests/security/test_no_shell.py` is no longer an absolute statement, and "no
process creation anywhere" was easier to reason about and easier to defend than
"one reviewed exception". Every future reader of that file now has to understand
the exception before trusting the rule. The at-most-one-entry assertion is what
stops that from eroding into a list.

### Residual risk
An application in the catalogue can itself be a shell in disguise — a launcher
that accepts a command argument, or a game launcher with a scripting console. The
interpreter denylist catches the obvious names by basename, but it cannot catch a
renamed binary or a program that embeds an interpreter. The real control is that
catalogue entries are created by the user, not by the model, and that every launch
is permissioned and audited.

## Revisit when
A second process-creation site is proposed for any reason — that is a new ADR and
a re-examination of this one, never a second `ALLOW_LIST` entry under this ADR's
number. Also revisit if the `explorer.exe` broker proves unreliable for Store
applications, which would reopen the COM activation option.

## Related
ADR-0003 (closed capability set — the rule this ADR carves a single exception in),
ADR-0009 (no elevation — unchanged), ADR-0010 (honest degraded UI — an
unverifiable launch reports `unverified`, never `succeeded`), ADR-0027 (approval
dialog — the interface through which a launch is authorised), SECURITY.md §2
(untrusted data — why the executable can never come from model output),
PRD FR-060, FR-063, FR-064, AT-003.
