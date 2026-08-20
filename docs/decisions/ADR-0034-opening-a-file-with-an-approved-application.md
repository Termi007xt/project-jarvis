# ADR-0034 — Opening a file with an approved application

- **Status:** Accepted
- **Date:** 2026-08-06
- **Extends:** ADR-0029 (approved application launch). Does **not** amend it.

## Context

P2-FS-05 asks for "open file (configured / default / user-selected app) with
verification". Stage 5 already finds files and points at them; opening one is
the obvious next thing, and the owner asked for it directly: *"it can open
files"*.

The obvious implementation is the forbidden one. Opening a file "with its
default application" on Windows means `ShellExecute`, and that is a **generic
execution primitive**: the program that runs is chosen by a registry association
the user's software can rewrite, from a file path that — however carefully
scoped — originated outside the product. `.hta`, `.lnk`, `.scr`, `.ps1` and
`.url` all have associations that run code. ADR-0003 forbids generic execution
and ADR-0029 authorises exactly one process-creation call site, with the
standing instruction that it is not to be broadened.

So the question is not "how do we call ShellExecute safely". It is whether
opening a file can be expressed as the thing this product already does: running
an **approved application** with a **fixed argument vector**.

## Decision

**A file is opened by handing its path to an application already in the
catalogue.** Nothing else. There is no default-application lookup, no registry
read, and no new process-creation call site — `launch_argv` remains the only
one.

Four constraints make the path argument safe, and they are enforced in
`launch.py` rather than at the call site:

1. **`ArgumentKind.FILE_PATH` is a new argument kind, not a relaxation.** An
   entry accepts a file path only if its catalogue definition says so, exactly
   as `ArgumentKind.URL` works today. Adding the kind does not make every entry
   accept paths.
2. **The path must be absolute and must already exist.** A relative path is
   resolved by the operating system against a working directory nobody here
   controls, and a path that does not exist is a request to create something.
3. **The path must not begin with `-` or `/`.** This is the whole of argv
   injection on Windows: a file named `--profile-directory=Jarvis` handed to a
   browser is not a file name any more, it is a flag. Refused rather than
   escaped, because escaping is a claim about a parser we do not own.
4. **The caller has already checked the scope.** `files.open` resolves the
   position through `FileScope` before the path is composed, so a path that
   reaches `launch_argv` came from a search inside folders the user approved.

**The application is named, or inferred from a short table, or the tool
refuses.** `.txt` opens in Notepad. An extension with no entry produces a
refusal that names what *is* possible (ADR-0010), rather than falling back to
"whatever Windows would do" — which is the primitive this ADR exists to avoid.

**The model still never handles a path.** `files.open` takes a position from
the last `files.find`, the same as `files.reveal`. The path exists only inside
the engine.

## Consequences

**Jarvis can open far fewer files than Windows can.** A `.docx` will not open
until Word is a catalogue entry. That is the intended shape: the set of things
that can be launched is a list the owner can read, not a registry.

**A hostile file name cannot become a flag or a program.** The two ways a path
turns into execution — an association that runs code, and a leading dash that
turns an argument into an option — are closed by construction rather than by
sanitising.

**`verify_process_names` does the verification.** "Opened" means the declared
process was observed, the same standard `app.open` already meets. A file handed
to an application that was *already running* verifies the process and not the
document, so that case is reported as `unverified` — the same honesty problem
as `app.open` with Brave already open, and the same answer.

**The extension table is a maintenance cost.** It is small, explicit and in one
place. A table that has to be edited is better than a lookup that is always
right and occasionally runs a screensaver.

## Alternatives considered

**`ShellExecute` with an extension denylist.** Rejected. A denylist of dangerous
extensions is a list of the ones we thought of, against a registry the user's
own software rewrites. It also silently becomes generic execution the first time
somebody installs a handler for something innocuous.

**`explorer.exe <path>`.** Rejected for the same reason wearing a disguise:
Explorer performs the association lookup, so the constant binary is a decoy and
the behaviour is identical to `ShellExecute`.

**Letting the model name the application.** Partially accepted — it may name an
`app_id` from the catalogue, which is a choice among approved entries. It may
never name a binary, which is ADR-0029 constraint 3 and is unchanged.

**Not building it.** Reasonable, and it was the state until the owner asked.
Finding a file and being unable to open it is a dead end for most of what the
filesystem stage is for.
