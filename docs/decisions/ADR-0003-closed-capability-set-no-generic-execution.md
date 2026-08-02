# ADR-0003: A Closed Capability Set — No Generic Execution Primitive

- **Status:** Accepted
- **Date:** 2026-08-01
- **Deciders:** Project owner
- **PRD reference:** §1 item 4, §6.1, §11.1 "Prohibited", §13.3, §13.4
- **Phase:** 0

## Context

This is the most important decision in the project. Project Jarvis's entire
value proposition — "use my PC like me" (PRD §7.3) — is also its entire risk
surface. A locally-running agent that can be reached by voice or by a
compromised prompt and that has a general-purpose way to execute code or
shell commands is not a scoped assistant; it is a remote-code-execution
primitive with a friendly voice. The PRD is unambiguous about this: item 4 of
the instructions to the implementation agent reads "Never add a generic
terminal, Command Prompt, PowerShell, arbitrary-code-execution, or
unrestricted shell tool to the runtime agent" (PRD §1.4), Non-Goal 1 repeats
it (PRD §6.1: "Provide unrestricted terminal, shell, PowerShell, Command
Prompt, WSL, registry, or arbitrary-code execution to the LLM"), and the
capability catalogue lists "Generic shell execution" and "Arbitrary script
execution" as Prohibited, full stop, with no permission scope that can
re-admit them (PRD §11.1).

The forces in tension are real, not hypothetical: a shell escape hatch would
make every future feature trivially fast to build (why write a typed
`copy_file` tool when `shell("copy a b")` already exists?), and it would make
the model's job easier (LLMs are fluent at generating shell commands). Both
of those are exactly why it must not exist — they are arguments for
convenience, not for safety, and convenience is precisely what an
LLM-directed agent with standing permissions must not be optimised for.

## Options considered

### Option A — Closed, enumerated set of narrow typed tools (chosen)
**Pros:** The blast radius of any single tool is bounded and reviewable in
isolation; every tool has a declared risk category, permission requirement,
resource-lock set and verification method (PRD §13.2), so the permission
engine and audit log have something concrete to reason about; a security
reviewer can read the full list of things Jarvis can possibly do (PRD §13.3)
in one sitting.
**Cons:** Every new capability — however small — requires a new tool:
schema, risk classification, permission wiring, verification method, tests,
and review. This is measurably slower than giving the model a shell and a
prompt.

### Option B — A sandboxed generic shell (containerised, restricted user, allow-listed commands)
**Pros:** Would recover most of the velocity of a shell escape hatch while
notionally bounding the damage.
**Cons:** Sandboxing a shell well enough to trust it is a substantially
harder engineering problem than writing individual tools, and Windows lacks
the mature namespace/cgroup sandboxing Linux offers; a restricted-command
allow-list inside a shell is exactly a closed capability set again, just
implemented as string matching against a command line instead of as typed
function signatures — strictly worse, because string matching is easier to
smuggle past (quoting, environment expansion, `&&` chaining) than a schema
validator. Rejected: it does not actually avoid the problem, it reimplements
Option A badly.

### Option C — LLM-generated code, executed after human review
**Pros:** Maximum flexibility; the model could write exactly the automation
a novel request needs.
**Cons:** "Review" does not scale to voice-driven, low-friction interaction —
either every generated script gets a real security review (destroying the
product's responsiveness) or review degrades into a rubber-stamped approval
dialog (silently reintroducing arbitrary execution under a thin consent
veneer, which is the exact failure mode §11.1's Prohibited list exists to
prevent). Rejected.

## Decision

The agent's ability to affect the world is a closed, enumerated set of
narrow, typed tools — the permitted list in PRD §13.3 (`open_application`,
`read_text_file`, `uia_invoke`, `browser_click`, and so on). No generic
execution primitive exists anywhere in the runtime: no shell, no PowerShell,
no `cmd`, no WSL, no `subprocess`, no `eval`, no `exec`, no arbitrary code
execution, in any form, reachable from any tool, skill or configuration
path.

## Enforcement

Enforcement is deliberately layered, because no single layer is trusted
alone:

1. **No such implementation exists.** This is the primary guarantee. The
   codebase simply contains no code path that shells out or evaluates
   arbitrary text as code.
2. **The tool registry rejects registration two ways** (ARCHITECTURE.md
   §6.5): by exact denylisted identity — every name in PRD §13.3's
   "Prohibited broad tools" list (`run_shell`, `execute_code`,
   `run_powershell`, `control_computer`, `approve_all`, and the rest) is
   rejected outright — and by name pattern, so a contributor cannot dodge the
   identity check by registering `run_shell_v2` or `shell_helper`. Patterns
   include `shell`, `powershell`, `cmd`, `terminal`, `wsl`, `exec`, `eval`,
   `subprocess`, `arbitrary`, `registry_write`.
3. **`tests/security/test_no_shell.py` scans the entire `src/` tree** for
   `subprocess`, `os.system`, `os.popen`, `eval(`, `exec(`, `shell=True`,
   `ShellExecute` and `CreateProcess`, and fails the build if any appears —
   including in code that is not currently reachable, because "not currently
   wired up" is not a safety property worth relying on. This is the
   load-bearing layer: registry guards can be forgotten on a new code path,
   but the scan runs over everything, every build.

Any addition to the tool denylist exemptions requires an ADR and a named
reviewer (ARCHITECTURE.md §14); lifting the `test_no_shell.py` scan for any
call site requires an ADR that names the exact call site and its
justification, never a broadened exception pattern.

## Consequences

### Positive
- The set of things Jarvis can do is always answerable by reading a table,
  not by reasoning about what a model might be coaxed into generating.
- Every action is schema-validated, permission-checked and lock-checked
  before it runs (PRD §13.4), because every action necessarily goes through
  a `ToolSpec` — there is no path that skips this by being "just a script".
- Prompt injection (PRD §11.4) has a hard ceiling on impact: injected text
  can at most cause a legitimate tool to be proposed with attacker-chosen
  parameters, which still has to pass permission evaluation and — for
  medium/high risk — a fresh approval dialog. It can never grant a new
  category of action that does not already exist as a reviewed tool.

### Negative
- Feature velocity is genuinely slower than a shell-based agent. This is the
  cost, stated plainly, and it is accepted deliberately: the PRD's Non-Goal
  1 and §11.1 Prohibited list exist precisely because "slower but bounded"
  beats "fast but unrestricted computer control" for this product.
- Some legitimate user requests ("just run this command for me") are
  permanently out of scope for Version 1, not merely deferred, unless a
  narrowly typed tool is later built for that specific need.

### Residual risk
This does not solve the problem that a sufficiently large permitted tool set
could, in combination, approximate a shell (e.g. file read/write plus
document tools plus archive tools is already a fair amount of power). Each
individual tool is reviewed; the *composition* of many approved tools is not
formally analysed for emergent capability, and that is a standing review
responsibility rather than a solved problem. It also does not defend against
a reviewer approving a poorly scoped tool in the first place — the process
depends on the review being real, not just present.

## Revisit when

Phase 1 needs `os.startfile` to launch approved applications (PRD FR-060 ff.,
scenario E). This is a known, named future exception: it must arrive as a
**single reviewed, allow-listed call site**, recorded in its own follow-up
ADR describing exactly where it lives and why it cannot be reached with
attacker-controlled parameters — never by weakening `test_no_shell.py`'s
scan or broadening its exception list.

## Related
- ADR-0009 (scoped elevation via separate helper — the other place "more
  power than a normal tool" is handled, kept structurally separate from this
  decision).
- ARCHITECTURE.md §2 driver 1, §6.5 (tool contract and registry), §6.6 (tool
  invoker six-step pipeline), §11 (testing architecture), §14 (change
  control).
- PRD §13.3 (full permitted and prohibited tool lists).
