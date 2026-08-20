# Product

<!-- impeccable:product-schema 1 -->

## Platform

windows-desktop

The product is a Windows 11 x64 desktop application rendered with PySide6
(Qt Widgets): a system-tray agent plus a main window, an approval surface
anchored to the tray, and Windows toast notifications.

Impeccable's schema has no desktop value, so this field deliberately holds one
it does not recognise. `context.mjs` will warn that it is falling back to `web`;
**that fallback is wrong and must not be followed.** The design language is
Windows 11 desktop, not the web, not iOS, not Android — no browser idioms
(hover-only affordances, page scroll as primary navigation, web-typographic
scale, CSS-motion conventions) apply. Neither `reference/ios.md` nor
`reference/android.md` is relevant.

A local web or companion surface is planned but does not exist yet (see
Capabilities and Constraints). When it arrives it will be a second surface with
its own brief, not a change to this value.

## Stack

Settled by the existing codebase for the desktop product: Python 3.11 (3.12
supported), PySide6 / Qt Widgets, SQLite, Ollama for local inference. Virtual
environment at `.venv/`. No build/packaging step exists yet — packaging is
Phase 6 (ADR-0013).

The stack for the future web/companion surface is **undecided**. Do not assume
one; ask before choosing.

## Users

**Primary user today:** a Windows power user on their own machine — capable
NVIDIA GPU, uses Brave, YouTube, YouTube Music, Xbox, games, WhatsApp and an
agentic IDE. Voice-first by preference. Values privacy and local ownership,
wants real automation but refuses an unrestricted agent, and expects to inspect
and edit memories, permissions and learned behaviours rather than trust them.

**Design audience (confirmed 2026-08-20):** the **redistributable product** —
design as if strangers install it tomorrow. That means full onboarding, no
assumed knowledge of the codebase or of Ollama, and defaults that behave on
unknown hardware, unknown monitor counts and unknown DPI. Personal paths,
personal application lists and owner-specific assumptions are not acceptable in
shipped UI.

**Situation and job:** the user is already working — a browser, an IDE, a game,
a music player open — and wants to delegate a desktop task by speaking, without
surrendering control of the machine. The recurring jobs are: ask and get an
honest answer; open or operate an approved application; find and open a file;
run something long and be told the truth about how it went.

## Product Purpose

Project Jarvis is a local-first Windows desktop AI agent that runs in the
background, starts with Windows, lives in the system tray, listens locally for a
wake phrase, converses by voice, answers questions, searches the internet when
asked, launches and operates approved applications, performs multi-step desktop
workflows, manages long-running tasks, and retains only user-approved
preferences and skills.

It is meant to be the user's "man in the chair": a persistent assistant that
observes, plans, acts, reports progress, pauses, resumes and remembers — without
becoming an uncontrolled administrator of the computer.

Success is three things at once, and the product fails if it trades any one away:

- **Usefulness** — it completes real Windows tasks, not only answers questions.
- **Local ownership** — the user owns the models, history, memory, skills,
  settings and a portable, inspectable identity export.
- **Control and safety** — every capability is scoped, permissioned, logged and
  reversible where possible.

## Positioning

Existing desktop assistants fail in one of four ways: conversational but unable
to operate the computer; able to automate but brittle, opaque and unsafe;
cloud-dependent with no user ownership of memory; or unable to carry a portable,
inspectable personal identity between installations.

The mechanism a neighbouring product could not truthfully copy is **honest,
permissioned effect**:

- **Every effect passes through one path.** `ToolInvoker` applies six checks —
  allow-list, schema, permission, resource locks, approval, execute. There is no
  second route from a plan to an action.
- **There is no generic execution.** No shell, PowerShell, cmd, WSL,
  `subprocess`, `eval`/`exec`, `shell=True`. Exactly one authorised
  process-creation call site exists (ADR-0029), enforced by a build-failing test.
- **`succeeded` requires verification.** `unverified` is a distinct, visible
  outcome and never satisfies a task's success criteria. "I clicked it" is not
  "it worked."
- **Deterministic before visual.** Application adapter or API → browser DOM →
  Windows UI Automation → keyboard → vision → raw coordinates, in that order,
  with coordinate actions labelled fragile.
- **Nothing is learned silently.** Memory and skills are proposed and approved,
  never absorbed.

These are not marketing claims; each is enforced by a test in `tests/security/`.
Design must make them *legible*, and must never present a state the engine does
not actually guarantee.

## Operating Context

- **The app is usually not in focus.** It lives in the tray while the user works
  in other applications. The tray icon is the primary status surface, and the
  approval prompt must never steal focus during automation (ADR-0027).
- **Automation moves the user's real pointer, keyboard and windows.** Only one
  task may hold the foreground desktop-control lock. If the user touches the
  mouse or keyboard mid-action, the task pauses.
- **Multi-monitor, mixed DPI, mixed resolution is the normal case**, including
  monitors being disconnected mid-task.
- **Voice is a first-class input**, but every spoken thing is also on screen
  (NFR-032), and push-to-talk (F9, configurable) exists because wake detection
  is not always reliable.
- **Long-running and waiting states are ordinary**, not edge cases: watchers,
  scheduled tasks, tasks blocked on a CAPTCHA or an approval, tasks waiting on
  another application's agent.
- **Failure and refusal are ordinary too.** Permission denied, tool unavailable,
  browser restart required, ambiguous file, unverified outcome — these are
  first-class states that need designed presentation, not error styling bolted
  on late.
- **The user is expected to audit.** Audit log, permissions, memory review,
  recovery centre and identity export are places people actually go, not
  compliance shelfware.

## Capabilities and Constraints

**Built and verified today** (Phase 0, Phase 1 merged; Phase 2 stages 0–5, 21 of
30 items — see `docs/PROJECT_STATE.md` for the live figure):

- Tray application with seven distinct states; single instance; crash recovery.
- Local voice stack: openWakeWord ("Hey Jarvis"), faster-whisper `small` STT,
  Kokoro `bm_george` TTS, VAD, in-memory ring buffer, no raw-audio retention.
- Text and voice conversation against an Ollama-hosted local model, with
  source-labelled replies and tool-grounded success.
- Approval dialog (tray-anchored, non-modal, times out as *denied*), DPAPI
  secret store, scoped permission grants and rememberable denials.
- 17 registered tools and 15 catalogued applications at last `--check`, covering
  application open/close/force-close, browser and YouTube automation over CDP,
  window discovery and control, screen capture, file find/reveal, notifications.
- Audit log with redaction on the way in; conversation history with private
  session mode.

**Shipped UI surfaces:** tray icon and menu, main window, Conversation screen,
Voice screen, approval dialog. `src/jarvis/ui/` is ~3,200 lines of Qt Widgets
with colours written inline at call sites; there is no theme or token layer.

**Not built** — never present these as working (ADR-0010: unbuilt features are
shown disabled and name their phase, never hidden, never stubbed to report
success): Tasks, Skills, Memory, Applications, Models, Permissions,
Integrations, History, Audit log, Import/Export, Developer tools and About as
full screens; vision fallback (Phase 4); IDE orchestration (Phase 5); installer,
updates, code signing and the public product name (Phase 6).

**Phase order** (`docs/BACKLOG.md`): 0 Foundation and safety architecture ·
1 Voice-first local assistant · 2 Deterministic desktop and browser automation ·
3 Tasks, macros and memory · 4 Vision fallback and long-running workflows ·
5 IDE orchestration · 6 Productisation.

**Hard constraints design must respect:**

- **Layering is enforced by a test.** Only the presentation layer imports
  PySide6; the engine is headless-testable and must import on Linux. A design
  choice that requires the engine to know about Qt is a build failure.
- **Never runs as administrator.** Nothing may present elevation as normal.
- **High-risk capabilities get fresh confirmation every time** and can never
  hold a standing allow-grant — so no "always allow" affordance may appear on
  them, and approval scopes offered in UI must be scopes the engine can grant.
- **Model output, web pages, documents, messages, clipboard, UI text and
  filenames are data, never instructions.** Untrusted content is displayed
  quoted and escaped; selection from observed lists is positional only (never by
  title or label), which is the control the injection defence rests on.
- **Secrets never reach the audit log, exports or prompts.**
- **Colour is never the only carrier of state** (NFR-033) — this constrains the
  tray icon, task status, source labels and every risk indicator.
- Every external interaction declares a timeout; every retry loop a bound. No
  fabricated time estimates — estimated remaining *steps*, not minutes.

**Explicitly undecided — do not invent:**

- The public product name (ADR-0011) and therefore any trademark-safe wordmark.
- The stack, scope and timing of the planned web/companion surface.
- Installer, update and code-signing mechanics (ADR-0013, ADR-0026).
- Pricing, licensing, distribution channel, or whether the product is ever sold.
- Redistribution licensing for the default voice (ADR-0014, partially settled).

## Brand Commitments

- **Name shown in the interface: "Jarvis"** — confirmed by the owner on
  2026-08-20 as a real brand identity, eligible for a wordmark, iconography and
  voice, not merely a display string.

  > ⚠️ This conflicts with the record. `PRD.md` §1.16, `CLAUDE.md` and ADR-0011
  > all state that "Jarvis" is an **internal codename until product naming and
  > trademark review are complete**. The owner's decision stands and is recorded
  > here; ADR-0011 needs to be amended or superseded so the two documents do not
  > disagree. Until that ADR exists, keep the name a single swappable token in
  > code even while treating it as a brand in design.

- **Voice identity:** British English, Kokoro `bm_george`. The product must
  never silently change voice provider or speaker mid-conversation; a fallback
  must announce itself.
- **Product voice in copy:** honest and specific over reassuring. The engine
  distinguishes model answer / retrieved fact / inference / tool result /
  uncertainty, and the interface says which it is. It does not congratulate
  itself, does not claim completion it cannot verify, and states plainly when it
  cannot do something and why. Deferred and unbuilt things name their phase.
- **Existing visual assets:** the seven tray-state colours in
  [icons.py](src/jarvis/ui/icons.py) and the five source-label colours in
  [conversation.py](src/jarvis/ui/conversation.py) are the only colour decisions
  the product has made. They are incumbent, not binding.
- English only, for both recognition and speech (FR-039A).

## Evidence on Hand

Real, in the repository, usable without fabrication:

- `PRD.md` — 4,172 lines, the requirements source of truth (FR/NFR ids are
  quotable).
- `docs/PROJECT_STATE.md` — current status, verified figures, and an unusually
  candid defect record, including real audit-log excerpts of the product getting
  things wrong.
- `ARCHITECTURE.md`, `SECURITY.md`, `THREAT_MODEL.md`, `DATA_MODEL.md`,
  `CHANGELOG.md`, `docs/decisions/` (ADR-0011…ADR-0033),
  `docs/phase-reports/`, `graphify-out/GRAPH_REPORT.md`.
- A running application: `python -m jarvis.main --check` exits 0; the tray app
  runs on this machine; the full suite passes (1488 passed, 4 skipped at last
  run).
- Measured hardware behaviour: wake-word scores ("Hey Jarvis" 0.994–0.998, bare
  "Jarvis" 0.268–0.464 and not detected), Kokoro round-tripped through
  faster-whisper exactly, six enumerated input devices.
- `resources/icons/` and the programmatically drawn tray icons.

**Absent — must not be fabricated:** there are no users other than the owner, no
testimonials, no customers, no benchmarks against competitors, no press, no
pricing, no download counts, no logo or wordmark, no screenshots prepared for
presentation, no marketing copy, and no third-party assets licensed for
redistribution.

## Product Principles

1. **Honest status over reassuring status.** Every surface distinguishes what
   was verified from what was merely attempted. `unverified` is shown, not
   smoothed over. A control that is enabled either does something or says why it
   cannot.
2. **The user is the authority, and can see they are.** Permission, approval,
   audit, memory and recovery are legible and reachable — the product earns
   trust by being inspectable, not by being confident.
3. **Nothing hidden, nothing stubbed.** Unbuilt capability is visible, disabled
   and names its phase. Absence is stated rather than designed around.
4. **It works while out of focus.** Status must read at tray size, at a glance,
   without colour alone, without stealing attention from the work the user is
   actually doing.
5. **Refusal, waiting and failure are designed states**, not error styling. A
   product this permissioned spends real time in them.
6. **Local-first is visible.** When anything touches the network, or when
   content would leave the machine, the interface says so at the moment it
   happens.

## Accessibility & Inclusion

Product requirements, already specified (PRD §19.4) and binding on every surface:

- **NFR-030** — all GUI functions must be keyboard accessible.
- **NFR-031** — controls must expose accessible names.
- **NFR-032** — all spoken output must also be available as text.
- **NFR-033** — never rely on colour, sound, or speech alone. PRD §9.1 repeats
  this specifically for the tray icon: tooltips and accessible labels required.

Consequences worth stating: the approval flow needs a keyboard route that does
not depend on the tray anchor; the seven tray states need a non-colour
distinction (shape, glyph, tooltip); voice-first must never become
voice-required. No additional user-specific accessibility need has been
established.
