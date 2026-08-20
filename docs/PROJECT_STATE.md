# Project State

## Snapshot
- **Last updated:** 2026-08-06 (Phase 2 stage 5 — finding files; turn continuation)
- **Current branch:** `feat/PHASE-2-development`. Phase 1 **is already merged** —
  `main` is at `b9e73e0`, merge of PR #2.
- **Version:** `0.2.0.dev0`
- **Active phase:** **Phase 2 — deterministic desktop and browser automation.**
  **Stages 4 and 5 complete; phase closing.** 21 of 30 Phase 2 items done,
  4 partial, 5 not started (BRW-03/05/07/09, WIN-01 — deferred or
  descoped). Exit criteria: `tests/acceptance/test_phase2_exit_criteria.py`.
  Plan: `docs/phase-plans/PHASE-02-PLAN.md`. Work items: `docs/BACKLOG.md` §5.
- **Delivery mode:** **checkpoint after every stage** (decided 2026-08-04, and
  deliberately *not* Phase 1's continuous run — see the plan §2.1/§2.2).
- **Overall status:** Green. `python -m pytest` → **1488 passed, 4 skipped**,
  exit 0; `python -m pytest -m "not slow"` → **1488 passed, 3 deselected** in
  83s and opens no socket. `python -m jarvis.main --check` → exit 0, 17 tools,
  15 applications. Nothing is blocked. Awaiting the owner's acceptance testing:
  `docs/PHASE-02-ACCEPTANCE-TESTING.md` §4.12–§4.21, §5.1–§5.3 and
  **§C.1–§C.7 (the phase-closing list)**.

> **Running the suite:** `pyproject.toml` already sets `addopts = "-q"`. Do **not**
> add another `-q` — two of them suppress pytest's final `N passed` line, which
> looks alarmingly like a truncated crash and is not one. Run
> `python -m pytest` bare.

### Phase 1 is accepted

All five PRD §21 exit criteria met, confirmed by user acceptance on 2026-08-04.
The full record is `docs/phase-reports/PHASE-01-VOICE-FIRST.md` §13; the items
it did **not** close are carried explicitly in `docs/BACKLOG.md` §4.6.

Two acceptance findings did not pass and were handled rather than waved through:

- **Voice interruption does not work on this hardware.** The owner deferred
  investigating it. Deferring the investigation is not the same as leaving a
  false claim standing, so `audio.duplex_mode` ships as `half` — the
  degradation ADR-0028 named in advance, and the behaviour FR-015 permits in as
  many words for Phase 1. `Ctrl+Alt+End` and the tray's **Stop speaking** work.
- **"Open YouTube Music" opens a tab, not the installed app**, despite a
  correct and tested app-id vector. Deferred by the owner, carried in §4.6.

**Acceptance took six rounds, not one.** Each round found defects a green suite
had not, because the tests tested units and the product is seams. That is the
lesson worth carrying into Phase 2, where the seams get considerably wider.

### What the owner decided, and what is therefore not open

- **Arbitrary application launching with first-use permission: deferred, not
  declined** ("stability first", 2026-08-04). It needs its own ADR before any
  code — see §4.6 and Next Exact Steps.
- **ADR-0029 is not to be broadened.** One process-creation call site, one
  allow-list entry. Progressive web apps and Start-menu discovery both fit
  inside it as fixed argument vectors; neither is a reason to widen it.

**The lesson, recorded so it changes behaviour:** every unit passed while the
product did not work, because nothing tested the *seam* between the GUI and the
engine. `tests/ui/test_conversation_screen.py` passed in full against a screen
that was completely non-functional. New wiring tests
(`tests/ui/test_conversation_wiring.py`, `tests/ui/test_voice_wiring.py`) assert
the connections, including a general rule: an enabled control either does
something or says why it cannot.

## Current Objective

**Phase 1 — voice-first local assistant.** Give Jarvis a voice: wire the audio
stack (wake phrase, push-to-talk, local STT, local TTS) to the Ollama-hosted
conversational model, ship the first six narrowly-scoped tools, and close the two
Phase 0 gaps that block any real interaction — the approval dialog and a
protected secret store. Nothing in this phase performs desktop or browser
automation beyond opening an approved application or URL.

Phase 1 is delivered as four ordered stages. The order is forced by dependency,
not preference: nothing requiring approval can run until stage 1 exists, and
voice is only useful once there is something to talk to.

| Stage | Contents | Work items | Status |
|---|---|---|---|
| 1 — Unblock | Approval dialog, DPAPI secret store, global hotkeys, startup-at-sign-in, `--require-healthy` | P1-SEC-01, P1-SEC-02, P1-UI-02, P1-COR-03 | **Done** |
| 2 — Converse | Ollama chat with structured tool calls, model routing, bounded context, source labelling, tool-grounded success, history and private session, Conversation screen | P1-LLM-01…03, P1-COR-01, P1-COR-02, P1-MEM-01…03, P1-UI-01 | **Done** |
| 3 — Voice | TTS (Kokoro), STT (faster-whisper), capture, ring buffer, VAD, full-duplex barge-in, wake detector and the Voice screen | P1-AUD-01…09 | **Done except per-user enrolment**, which is deferred; the shipped threshold is a measured default |
| 4 — Act | The six approved tools plus the one-time wake-model bootstrap | P1-APP-01, P1-BRW-01, P1-WIN-01, P1-UI-03 | **Done** |

**Delivery mode decided 2026-08-02:** continuous run to the end of the phase, no
intermediate approval checkpoints. Both blocking items were resolved during the
phase: **ADR-0029 was accepted** (with the direction that the exception must not
be broadened), and the **wake-word model was installed** through openWakeWord's
official API, measured, and documented.

### Deliberately deferred out of Phase 1

**P1-AUD-10** (Qwen3-TTS expressive worker, sized XL) is deferred. It is
`enabled: false` and `status: experimental` in `config/defaults.yaml`, it is the
product's first cross-Python-version process boundary, and `multiprocessing` is
denied by `tests/security/test_no_shell.py` — so it would consume the phase's
hardest engineering on a feature that ships turned off. Revisit alongside ADR-0015.

## Verified Working
Confirmed by passing tests or direct observation:

- `python -m pytest` → **386 passed, 0 failed**, 89% statement coverage.
- `python -m jarvis.main --check` → prints status, exits 0.
- Tray application runs on the native Windows platform; health-check task
  completes end-to-end through the full invoker pipeline.
- **User acceptance testing of Phase 0 passed** (2026-08-02) — all nine groups:
  tray and window, live data screens, settings persistence, single instance,
  audit log, crash recovery, emergency stop and degraded states, security
  invariants, environment robustness.
- All three configured Ollama models are installed and reachable:
  `qwen3.5:9b-q4_K_M`, `qwen3-vl:8b-instruct-q4_K_M`, `qwen3-embedding:0.6b`.
- **faster-whisper `small` transcribes real microphone input correctly** —
  verified by the user via `tools/voice-lab/test_whisper.py`.
- **Kokoro `bm_george` synthesises correctly** — verified via
  `tools/voice-lab/test_kokoro.py`. This also implies espeak-ng is installed and
  working, since Kokoro requires it for English phonemisation.

## Completed in Current Phase

Phase 0 is complete and closed. See `docs/phase-reports/PHASE-00-FOUNDATION.md`.

**All four Phase 1 stages are implemented, tested and committed.** Highlights
that change what the product can do:

- **The approval dialog exists**, so capabilities beyond the two self-inspection
  grants can finally run. Tray-anchored and non-modal (ADR-0027), timing out as
  denied, with rememberable scoped denials and a keyboard route (NFR-030).
- **A DPAPI secret store** (ADR-0030), verified by asserting the plaintext is
  absent from the database, the audit log and the configuration file after a
  round trip.
- **Text conversation works against the local model.** Free text and structured
  tool calls are separate fields and nothing promotes one into the other; every
  proposal goes through the invoker's six checks; every reply is source-labelled
  and cannot claim a success no tool verified.
- **The voice stack is verified on this hardware**: Kokoro `bm_george`
  synthesised 5.35s of audio and faster-whisper `small` transcribed it back
  exactly. Redaction removed a key before synthesis. Six input devices enumerate.
- **Storage now uses `PRAGMA secure_delete`.** Deleted conversation history was
  previously still readable in the database file.
- **Six approved tools exist**, on the single process-creation call site
  ADR-0029 authorises. Brave, YouTube, YouTube Music, Xbox and Sea of Thieves
  are catalogued; interpreters, unapproved applications and non-http URLs are
  all refused; a launch is only `succeeded` once the process is observed.
- **The wake-word model installs in one command** and is measured: "Hey Jarvis"
  scores 0.994–0.998, bare "Jarvis" 0.268–0.464 and is not detected — which
  confirms FR-011 empirically rather than by assertion.

## In Progress

### 2026-08-06 — stage 5 opened: finding files

P2-FS-01, P2-FS-03 and P2-FS-06 shipped together, because the first two are
unsafe without the third. `files.find` searches the Windows Known Folders and
`files.reveal` opens Explorer with a result selected. Neither takes a path: the
model receives numbered results and hands a number back, which puts the
injection defence in the signature rather than in a check that has to be
remembered. Paths resolve before the boundary is compared, so `..`, environment
variables, symlinks and junctions are judged by destination rather than
spelling (`tests/security/test_file_scope.py`).

**Left out deliberately, not forgotten.** P2-FS-05 (open a file with an approved
application) needs a new catalogue argument kind — a file path passed to an
approved binary — which touches ADR-0029, the one process-creation rule
everything rests on. That wants its own ADR rather than a quiet extension.
P2-FS-04 (disambiguation dialog) is UI work. The browser stage remainder
(BRW-03/05/07/09) is untouched, and the YouTube Music targeting bug lives there.

**The suite was downloading models from the internet.** Three wake-word tests
call the real installer, which fetches from GitHub — the reason full-run timings
swung between 90 and 234 seconds. They are marked `slow`; `pytest -m "not slow"`
is 78s and opens no socket. Separately, the new turn tests were paying the real
one-second desktop settle three times over, which is now injected as zero.


### 2026-08-06 late — a turn now finishes its work (ADR-0033)

Three reports in one evening, one cause. The turn ended the moment the model
produced text instead of a tool call, so *"I'll close it for you"* ended it as
surely as closing it did. The owner's next message settled the design: asked
*"did you close it?"*, Jarvis looked and said *"Nope, it's still there"* — it
had the tool, the information and a system prompt telling it not to claim
things it had not done. What it lacked was any reason to carry on.

A turn now continues while its own reply describes work nothing did: a promise,
a completion claim nothing verified, or a claim about a *different* action than
the one performed. Bounded at 12 rounds and 3 follow-ups; when they run out the
reply says the work did not happen. Every follow-up still goes through
`ToolInvoker`'s six checks, so continuation creates no new path from a plan to
an effect.

The third shape came from *"YouTube Music is now open and playing the current
song"* — `app.open` verified, nothing that can play anything ever ran. "Did any
tool verify something?" answered yes. Claims are now matched against the tools
that could have produced them (`CLAIM_EVIDENCE`), and a verified tool the
mapping does not recognise is never contradicted, because it might be the one
that did the work.

**Known limits, recorded rather than discovered later:** `CLAIM_EVIDENCE` is a
closed list and every new tool needs an entry. This stops a turn ending on an
unkept promise; it cannot make the model choose the right tool, and a model that
cannot do the job now fails after three attempts instead of one.

### 2026-08-06 evening — the grounding check was sound and its premise was false

The owner asked Jarvis to close Microsoft Edge. The audit log is unambiguous:

```
13:58:29  window.list   succeeded verified   -- "MS Edge ... has been closed successfully"
13:59:24  window.list   succeeded verified   -- "MS Edge ... has been closed successfully!"
```

**No close tool ran in either turn**, and both replies were labelled *confirmed
by a tool*. Edge was open throughout. It took two corrections from the owner
before `app.close` was called at all, and a third before `app.force_close`.

`jarvis.llm.grounding` exists to stop precisely this and did not fire. Its rule
— a success claim needs a `verified` result — is safe *because a read-only tool
reports `not_applicable`*, having changed nothing to verify. `window.list`
declared `changes_state=False` and returned `VERIFIED`, so the premise failed
and "I verified that I listed your windows" licensed "I closed Edge".

`ToolInvoker` already enforced the mirror rule: a state-changing tool reporting
`not_applicable` is downgraded to `unverified`. The missing direction is now
enforced beside it — **a tool that changes nothing has nothing to verify** —
normalised at the invoker, because that is the single point every effect passes
through and a per-tool rule is one the next tool forgets. A useful side effect:
`verified` now means exactly "a state-changing tool confirmed its own effect",
which is a signal the rest of the engine can rely on.

The second half is the model narrating rather than acting, which no rule can
forbid. Each tool round now ends with a trusted record of what changed and, more
usefully, what did not: every individual tool message was accurate, and **none of
them could report an absence**. Whether it now calls the right tool on the first
ask is for the owner's next round (`docs/PHASE-02-ACCEPTANCE-TESTING.md` §4.17).

### 2026-08-06 — stage 4: a false `verified`, and two things that were wired to nothing

**The Edge close bug is the important one.** The owner closed Notepad (worked),
then closed Microsoft Edge with a media tab that prompts before leaving. Jarvis
reported *"Microsoft Edge has been closed"*, **verified**, and Edge was still on
screen.

`WindowController.close` decided by asking whether the window was still in
`WindowDiscovery.list_windows`. That list answers *would a person call this
open* — it drops the invisible, the untitled, the DWM-cloaked and the zero-area
ghosts, which is precisely the filter that turned a listing of eleven windows
into the owner's four. Chromium hides its frame while a close is pending
(`BrowserView::CanClose()`), so Edge left that list while entirely alive.

Reproduced before any fix, with Character Map standing in for Edge
(`tools/window-lab/test_close_verification_live.py`): `outcome=closed
verified=True` about a window with `exists=True visible=False`.

Fixed by separating the two questions. `WindowDiscovery.window_exists` asks
`IsWindow`; presentability stays in `list_windows`. A window that exists but is
off screen is a new outcome, `still_running`, rather than either of the existing
two — calling it `closed` was the bug, and calling it `still_open, nothing
asking` would be a confident claim about the case it is most often wrong about,
since Chromium draws its prompt inside the page where nothing can see it.

**Two more "built but unreachable".** This is now the fifth and sixth instance
of the pattern in this project:

- `screen.capture` (P2-WIN-10) existed as a fully tested core with no tool. It
  is now registered through `attach_shell`, so it exists only when something can
  show the capture indicator — the same choice `notify.show` makes, and a
  stronger one, because a capture nobody can see is the thing FR-271 forbids.
  `tests/unit/test_capture_tool_wiring.py` asserts the registered tool reaches
  the real GDI grab, not a stub.
- `storage.huggingface_home` had named a directory since Phase 1 and **nothing
  ever read it**. The owner's models were in the right place only because they
  had exported `HF_HOME` by hand.

**Speech models are local-only by default now.** The owner's log showed a
`HEAD https://huggingface.co/...` on the path of *every spoken reply*: Kokoro
resolves voice tensors at synthesis time and `huggingface_hub` revalidates
cached files. faster-whisper does the same once at load. Offline mode was the
wrong switch — the owner is not offline, they want the weights local — so
`storage.speech_models_local_only` (default on) pins the hubs in every network
mode. The network is for fetching a model that is missing, never for confirming
one already present.

While fixing it: the previous control was **partly ineffective and its test was
vacuous**. `huggingface_hub` reads `HF_HUB_OFFLINE` into `constants` at *import*,
not at model load, so setting it afterwards changed nothing — and the test
asserted only that the environment variable was set, which it always was. The
library is now updated in place and the test checks what the library believes.

**P2-WIN-11 shipped as the honest half of FR-270.** `screen.active_window` names
the window in front and says plainly that Jarvis cannot read what is inside it.
Describing contents needs a vision model (Phase 4); assembling a description
from the window title would be inventing, and the title is application-authored
text besides.

**Capture retention is bounded, not solved.** A full-screen BMP is ~15 MB, so
`prune_captures` keeps the newest 20. `privacy.screenshot_retention` describes
what the product should eventually do and is **not** implemented — named here so
the bound is not mistaken for the policy.

### 2026-08-05 — the session that found six defects, and what changed

The owner asked Jarvis to open YouTube and search "best monitors". The whole
sequence is in `logs/audit.jsonl` and it is the most useful thing in this
document, because the first step is what broke the second and the tests were
green throughout.

| Local | What the audit log records |
|---|---|
| 12:35:28 | `app.open(youtube)` launched Brave **without** a debugging port. Verified success. No search tool was called; the reply said *"Now searching for 'best monitors'"* anyway, labelled `[confirmed by a tool]` |
| 12:36:24 | `youtube.search` approved, then **failed**: *"Brave is already open… cannot be given an automation port"* |
| 12:37:36 | Identical failure. Jarvis asked the owner to quit Brave from the taskbar |
| 12:38:30 | Owner quit Brave by hand → launched with a port, attached in 2.5s, **20 results** |
| 12:39 | "Search a latest anime" → **no tool call at all**; the model just talked |
| 12:42:51 | `youtube.search` **failed**: `Page.goto: Target page, context or browser has been closed` |

Four approvals were requested and every one of them recorded
`approval scope 'task' rejected — scope 'task' requires a task_id`.

**Root cause, one sentence: nothing owns the browser's lifecycle.** Four code
paths start Brave and only one leaves it automatable, so Jarvis's own first
action made its second action impossible — and the only remedy was manual. Every
unit test passed because every unit was correct. This is the phase's recorded
lesson (*test the seam, not the unit*) reappearing one layer up: the seam is now
a **resource's lifecycle across tools**, not a wire between two components.

**What was fixed** (ADR-0032; tests in `tests/unit/test_browser_restart_and_tabs.py`
and `tests/unit/test_approval_scopes_that_stick.py`):

1. **`browser.restart` exists.** Jarvis had been *offering* to close and reopen
   Brave for some time with no capability behind the offer. `WM_CLOSE` to the
   visible windows, then poll until the process exits — asked, never killed, so
   Chromium saves its session and the tabs return. A browser that refuses is a
   declared failure, never a `TerminateProcess`. Its own capability: approving a
   search is not approving the loss of someone's windows.
2. **`browser_restart_required` is its own failure code.** Told only
   "unavailable", the model improvised instructions for a human. The tool
   description now names the code it answers and says not to do that.
3. **A closed tab is replaced.** `is_alive()` asked about the *browser*, which
   was fine; the cached tab had died and nothing looked at it. A live tab is
   still reused, so "play the second video" lands on the page the search read.
4. **`BrowserWorkspace` owns a thread.** Playwright's sync API is bound to its
   creating thread; the tool executor has four workers and abandons the *thread*
   on a timeout. Every recorded session ended with `greenlet.error: Cannot
   switch to a different thread` from `MainThread` — meaning teardown never ran
   and the debugging port was left open. Under ADR-0031 teardown is a security
   control, so this was the control silently not running, every single time.
5. **A conversation turn carries a task id**, so "Allow for this task" is
   honoured instead of discarded. And a general rule is now asserted: a scope
   the dialog offers must be one the engine can grant.
6. **Browser automation may be granted "always"** (owner decision, ADR-0032).
   Offered, never defaulted; one named capability; empty by default in code;
   high risk still never eligible. Recorded in `THREAT_MODEL.md` §6.1 as a
   **reduction in control**, not as a neutral convenience.
7. **Present-tense narration is hedged.** Nothing is ever under way when Jarvis
   speaks — a turn finishes its tools first — so "Now searching…" is false
   either way. This is why "did any tool verify anything" could not catch it:
   `app.open` had verified, honestly, something else entirely.

**Also fixed, small but real:** the searched tab came back in light mode because
Playwright emulates `prefers-color-scheme: light` on pages it creates.

**Verified outside the suite:** the new `ctypes` window enumeration was run
read-only against the live machine — `brave.exe` 31 processes / 1 visible
window, `explorer.exe` 1 / 10, a non-existent process 0 / 0.

**Not fixed, and worth knowing:** the browser lifecycle is still not unified.
ADR-0032 Option 1 would have routed every browser action through one automatable
session; the owner declined it, because it leaves a CDP port open whenever
Jarvis opens the browser at all. So "open YouTube" then "search it" still costs
a restart. Recorded in `ARCHITECTURE.md` §13 gap 5a.

### Phase 2, stage 0 — "measure and unblock"

Nothing in stage 0 is a feature; all of it gates something.
Plan: `docs/phase-plans/PHASE-02-PLAN.md` §5.

| Stage 0 item | Status |
|---|---|
| CDP spike part A — does Brave open a debugging port? | **Done.** Measured |
| `automation` optional extra with lazy imports | **Done.** Suite still green |
| CDP spike part B — Playwright attach + index-addressable results | **Done.** Measured |
| ADR-0018, ADR-0019, ADR-0023, ADR-0031 | **Done.** Recorded |
| YouTube Music defect | **Diagnosed and fixed.** See `docs/BACKLOG.md` §4.6.1 |

**Stage 0 is complete and was accepted by the owner on 2026-08-04.** Suite at
stage 0 close: **925 passed, 2 skipped** (916 at phase start).

**Stage 1 — the untrusted-content boundary — is complete.** Suite at stage 1
close: **1029 passed, 2 skipped.** Acceptance items are in
`docs/PHASE-02-ACCEPTANCE-TESTING.md`; none of them block stage 2.

**Stage 2 — automation foundations — is complete.** Suite at stage 2 close:
**1064 passed, 2 skipped.** **Nothing can move the pointer or press a key yet**
— stage 2 built the eyes and the permission to move, deliberately before any tool
that moves, because a lock retrofitted onto tools written without one is how
Phase 1's defect class reappears.

| Piece | Where | What it guarantees |
|---|---|---|
| Desktop-ownership rule | `tests/security/test_tool_specs_are_valid.py` | A tool declaring `input.automate` or `browser.automate_logged_in` without the `foreground_desktop` lock **fails the build**. A second test asserts those capability ids exist, so the rule cannot silently match nothing |
| `UserInputWatcher` | `jarvis/toolbox/desktop_input.py` | Tells our synthetic input from the user's, **exactly** — no time tolerance |
| `UiaInspector` | `jarvis/toolbox/uia.py` | Reads a window's controls. Read-only, asserted structurally. Element text leaves through `Observation`, addressed by position |
| `AutomationSession` | `jarvis/toolbox/automation.py` | The only way to get permission to move anything |

**Design notes worth not rediscovering:**

- **No grace window for input attribution.** The first `UserInputWatcher`
  compared timestamps with a 250ms tolerance; a test killed it, because a user
  grabbing the mouse 50ms after an automated click is the case that matters most
  and a tolerance swallows precisely that. The replacement records what the
  *system* reports immediately after our injection — anything later is not ours,
  with no tuning. Do not reintroduce a window.
- **One real-hardware risk is open**, recorded in the code: if Windows has not
  registered our injection when the baseline is read, our own input reads as the
  user's and automation pauses itself. It needs a real `SendInput` to measure,
  which arrives in stage 3. It fails in the safe direction.
- **Automation refuses to start when interruption cannot be observed.** Not a
  warning — a refusal, with the underlying cause passed through. Flagged to the
  owner as reversible if they would rather it ran anyway.
- **An accessible name is untrusted content.** A window can label a button
  "Cancel" and wire it elsewhere. UI text uses the *same* boundary as web
  content; there is no more-trusting path for desktop text.
- **A Phase 0 exit-criterion test was narrowed, not weakened.** It banned
  importing pywinauto/playwright anywhere in `src/`, while its own docstring said
  the rule was *module scope* — which would have banned the lazy-import pattern
  Phase 1 already relies on for the voice stack. Now scans `tree.body` like
  `test_lazy_audio_imports.py`, and carries a self-check proving it still bites.

### What stage 1 built, and the hole it found

Built **before** anything in this product can fetch a page, which is the ordering
the whole plan turns on: a defence written after the capability gets shaped to
fit whatever the capability happened to emit.

- **`jarvis.core.observations`** (L2) — `Observation`, `ObservedItem`,
  `ObservedList`. External content has one shape and no trusted variant. The type
  has no field for a capability, grant, risk level or tool id, so there is
  nothing a hostile page could populate.
- **`ChatMessage.from_observation()`** (L3) is the only route into a prompt and
  sets `untrusted=True` with no parameter to override it. It lives in L3, not on
  `Observation`, because L2 must not know about L3 —
  `tests/security/test_layering.py` caught the first attempt, which had the
  import hidden inside a function, and was right to.
- **`ObservedList.select(position)`** is positional only. No lookup by label,
  title or text exists, asserted structurally. **This is the control that carries
  the weight**; the delimiters are defence in depth and assume a cooperative
  model, this assumes nothing.
- **A real vulnerability, found and fixed.** The delimiters that quote untrusted
  content are fixed strings published in our own source, and content was embedded
  verbatim — so a page containing `<<<END_UNTRUSTED_OBSERVATION>>>` closed the
  quoted region early and everything after it read as trusted context. Shipped in
  Phase 0 and Phase 1; unexploitable only because nothing could read a page yet.
  Delimiters in observed content are now escaped, and left visible rather than
  stripped, so a breakout attempt is evidence rather than a silent disappearance.
  `ARCHITECTURE.md` §13 gap 4 called this strategy "specified but unexercised" —
  exercising it is what found the hole.
- **`tests/security/test_browser_attach.py`** fails the build if any module in
  `src/` calls a Playwright launch API or passes `executable_path`, and asserts
  `ALLOW_LIST` has not grown. `test_no_shell.py` AST-scans `src/` and cannot see
  into `site-packages`, so without this a Playwright launch would create a second
  process-creation call site with the suite still green (ADR-0031).

The three diagnosed defects are fixed: launches no longer verify themselves
against a process that was already running; the planner can see which
applications it may open, so it stops routing "open YouTube Music" to a URL; and
application names resolve however the model punctuates them. A **fourth** cause
surfaced during acceptance and is the leading explanation for the original
symptom — a launch that hands its command line to an already-running Brave
appears to open a tab rather than the app. It is unconfirmed, it is recorded in
§4.6.1, and `docs/PHASE-02-ACCEPTANCE-TESTING.md` §0.7 is the two-run test that
settles it.

### What stage 0 measured, on this machine, 2026-08-04

Both spikes live in `tools/browser-lab/` and are outside the product runtime and
outside the security policy, the same status `tools/voice-lab/` holds.

- **Brave 151 opens a CDP port under ADR-0019 Option A** (`--profile-directory=Jarvis`)
  **and** under Option B (`--user-data-dir=<temp>`). The plan predicted Option A
  would be refused; the prediction was wrong. Option A stands as the owner chose,
  and the pre-authorised Option B fallback is not needed.
- **`connect_over_cdp` attaches to a browser started by `launch_argv`.** Process-creation
  call sites in `src/` remain exactly **one**. ADR-0029 is consumed, not widened.
- **A YouTube result page yields 13 `ytd-video-renderer` rows in DOM order.**
  "The second video" is `results[1]` — a position, never a title match. This is
  the structural control stage 1 is built around, and it is now known available
  rather than assumed.
- **Re-measuring requires Brave to be closed first.** A second `brave.exe` hands
  its command line to the running instance and exits, so a refused flag and a
  handed-off launch are indistinguishable.
- Running the spike **created the `Jarvis` Brave profile**, which FR-056 wants
  anyway. The owner signs into it once for whatever Jarvis should reach; it is
  persistent. Decided 2026-08-04, recorded in ADR-0019.

## Blocked or Failing

Nothing is blocked.

### One intermittent failure, seen once, not yet explained

`tests/integration/test_core_lifecycle.py::test_a_completed_task_is_never_re_run_after_recovery`
failed **once** during Phase 2 stage 3 with:

```
InvalidTransitionError: cannot move a task from 'running' to 'running'.
```

It then passed three times in isolation and the full suite passed twice more, so
it is intermittent rather than broken, and it is **not** caused by the change
that was in flight when it appeared (adding an import and a failure code).

Recorded rather than shrugged off, because of what it implies: two things are
transitioning the same task, which means a race between the scheduler and
startup recovery. A recovery path that can re-enter a running task is exactly
the class of defect that stays invisible until it re-runs a consequential action
after a crash — and `test_a_completed_task_is_never_re_run_after_recovery` is
named for the property it would break.

**Do not chase it by re-running until green.** It needs the transition to be
made idempotent, or the recovery path to take the task lock the scheduler holds.
Reproduce with the full suite in a loop, not the single test.

### Known limitation, deferred by the owner: automation wakes their other tabs

**Symptom.** When Jarvis opens Brave and attaches, every other YouTube tab in
the browser wakes and starts playing, all audible at once. Opening Brave by hand
does not do this — the same tabs stay asleep. Reported 2026-08-05; the owner
chose to defer it rather than hold up stage 4: *"i dont want to spend too much
time on this, we can always look back on this later."*

**Cause, measured not guessed.** `connect_over_cdp` attaches to **every page in
the browser** — ten of ten in `tools/browser-lab/test_attach_cost.py`. Playwright
is designed to drive a browser it owns; ADR-0019 Option D points it at one the
owner is using, so attaching announces Jarvis to all their tabs. There is no
Playwright option to narrow the attach. Nothing in Jarvis touches those tabs,
which is why this cannot be fixed above Playwright.

The exact Chromium step from "woken" to "playing" is **not** established.
Autoplay is gated per origin on media engagement history, and a scratch profile
has none, so `tools/browser-lab/test_attach_side_effects.py` cannot reproduce it
and does not claim to. That gap does not affect the fix, because attaching to
those tabs at all is unnecessary.

**The fix is proven and not yet applied.**
`tools/browser-lab/test_single_tab_cdp.py` drives one tab over raw CDP —
`PUT /json/new` returns that tab's own WebSocket, which reaches it and nothing
else. Measured against real YouTube with three decoy videos open:

```
search rtx 5070   -> 5 results, read by position
play position 1   -> VERIFIED by video id
decoy tabs        -> still paused, currentTime=0, all three
```

It also removes the Node driver and Playwright's thread-affinity trap (the
2026-08-05 blank tab), and needs no synthetic click: read the id at position N
and navigate to it, which is *more* deterministic and keeps selection strictly
positional. `websocket-client` is installed; it is not yet in the `automation`
extra because no product code imports it.

**What is left to do:** a `jarvis.toolbox.cdp` module and a `CdpPageDriver`
behind the existing `PageDriver` interface, then swap the session type. The
tools, the permission checks and the positional-selection guarantee are
unchanged. Budget one round of rough edges on real pages — it is code we own
rather than a library.

**Until then**, search and play work correctly on Playwright (verified end to
end across two calling threads, `tools/browser-lab/test_exit_criterion_threaded.py`).
The cost is the woken tabs, and it is loud rather than silent.

**Known defects carried into Phase 2** — all in `docs/BACKLOG.md` §4.6, none of
them silent in the product:

1. **Voice interruption does not work on real hardware.** Shipped as
   `duplex_mode: half`, which the GUI states plainly. Needs a measurement, not
   a rewrite: set `full` and count self-triggers.
2. **"Open YouTube Music" opens a browser tab.** The app-id vector matches the
   Start-menu shortcut and is unit-tested, so Brave is receiving it and not
   honouring it — most likely the profile directory or the app id differs from
   what the shortcut records.
3. **No time or date capability.** The most obvious thing to ask a voice
   assistant, answerable only from a model that cannot know.
4. **Progress speech (FR-033) and spoken notifications by event type (FR-181)**
   are not built. Both matter more once Phase 2 has work long enough to report
   progress on.

**Resolved during acceptance:** the false-wake rate — no false wakes over an
extended period of ordinary conversation, so the shipped 0.6 threshold stands
and always-listening is safe to offer as a switch.

## Tests and Quality Checks
- **Last successful:** `python -m pytest` → **907 passed, 2 skipped** (2026-08-04).
  The two skips are the non-Windows branches of the secret store, which cannot
  run on this platform by definition.
- **Last failed:** none.
- **Verified outside the suite, on this machine:**
  - `python -m jarvis.main --check` → schema v3, secret store available, voice
    stack reported honestly, Ollama reachable, exit 0.
  - A live conversation turn against `qwen3.5:9b-q4_K_M`: the model answered,
    proposed a registered tool, the invoker ran it, and the reply came back
    correctly labelled.
  - Kokoro `bm_george` → 5.35s of audio; faster-whisper `small` transcribed that
    audio back **exactly**. FR-034 redaction removed a key before synthesis.
- **Not yet run:** GitHub Actions CI (workflow committed, never executed);
  Linux; Python 3.12; `pip-audit`.
- **Known limitations:** no test requires Ollama, a microphone, a GPU or the
  network, which is deliberate (ARCHITECTURE §11) but means the suite proves
  nothing about real-hardware audio; the smoke runs above are what covers that,
  and they are not automated. **Nothing has yet been tested with a real
  microphone end to end** — capture, wake, VAD and barge-in are exercised
  against synthetic frames only, and ADR-0028 is explicit that self-trigger
  rates need real-hardware iteration. Coverage is lowest in `jarvis/ui/app.py`
  and `single_instance.py`.

## Decisions Requiring Attention

### Settled 2026-08-02 — recorded, do not re-litigate

| # | Decision | Recorded in |
|---|---|---|
| 1 | Approval dialog scopes: Low = once/always/deny · Medium = once/task/deny · High = **once/deny only**. "Allow for this session" is not offered. | ADR-0027 |
| 2 | Denials are remembered on request: **"Don't ask again for this application / folder"** → a scoped `DENY` grant. No engine change needed. | ADR-0027 |
| 3 | Approval surface is **tray-anchored and non-modal** — must not steal focus during automation. Tray goes red while pending; unanswered requests **time out as denied**, never allowed. | ADR-0027 |
| 4 | Wake word: **per-user voice enrolment during onboarding.** User speaks their phrase, Jarvis trains a personal model, retrainable, multiple phrases supported. | ADR-0016 |
| 4a | Enrolment uses **Path 1** — pretrained base model + personal verifier. Path 2 (synthetic augmentation) deferred to after Phase 1. **Consequence: the Phase 1 phrase is "Hey Jarvis"**, because no pretrained base exists for bare "Jarvis". | ADR-0016 |
| 7 | `--check` keeps exit 0 when Ollama is unreachable; add a **`--require-healthy`** flag for non-zero. | this document |
| 8 | Push-to-talk hotkey is **F9**, bare, no modifier. Always-listening remains primary. | ADR-0027 |
| 9 | **Barge-in immediately** — full-duplex audio in Phase 1, not the half-duplex shortcut FR-015 permits. | ADR-0028 |
| 10 | Phase 1 runs **continuously to phase end**, with no intermediate approval checkpoints. | this document |
| 11 | Audio dependencies enter as an **optional `voice` extra with lazy imports**, not core dependencies. | this document, ADR-0010 |
| 12 | The application launcher gets **one authorised process-creation call site**, drafted up front rather than discovered mid-stage. | ADR-0029 |

### Awaiting acceptance — these gate code that is otherwise ready

| # | Item | Gates |
|---|---|---|
| A | **ADR-0029** — the single authorised `subprocess.Popen(argv_list, shell=False)` call site for launching approved applications, and the one `ALLOW_LIST` entry it adds to `tests/security/test_no_shell.py`. Written, status Proposed. | All of stage 4: P1-APP-01, P1-BRW-01. Phase 1 exit criterion 3. |
| B | **openWakeWord "Hey Jarvis" base model** — must be downloaded, and its provider, licence, size and install location recorded per PRD §17.2. | Stage 3's wake detector and enrolment (P1-AUD-01). Push-to-talk is unaffected and remains the fallback. |

**ADR-0030** resolves the "mechanism Open" status ADR-0008 left behind, selecting
DPAPI for the secret store. It is required before any settings field asks for a
credential.

### Two concerns raised but not yet answered

- **Bare F9 is a heavily used application key** (IDE debug controls, Excel
  recalculation, game bindings). A global hook on it will swallow F9 from every
  other application. PRD §11.3 requires the emergency-stop hotkey not to conflict
  with common shortcuts; the same reasoning applies here. Implement F9 as
  specified **and make it configurable**, then reassess after real use.
- **Wake-word enrolment is a genuine Phase 1 scope increase.** Even on Path 1 it
  adds a verifier-fitting step, an enrolment UI, sample storage with privacy
  rules, and a measurement harness.
- **Path 1 means Phase 1 ships "Hey Jarvis", not "Jarvis".** No pretrained base
  model exists for the bare word. FR-011 names "Jarvis" as the product default
  and explicitly forbids implying a "Hey Jarvis" model detects it — so the Voice
  screen must state the enrolled phrase truthfully and say that single-word
  detection needs the deferred Path 2 work. Do not quietly label it "Jarvis".

### Still open, gated by later phases

| Needed before | ADRs |
|---|---|
| Phase 2 | ADR-0018 search provider · ADR-0019 browser profile isolation · ADR-0023 adapter isolation |
| Phase 3 | ADR-0024 data-retention defaults |
| Phase 4 | ADR-0025 screenshot ceiling (default `task_only` accepted) |
| Phase 6 | ADR-0011 product name · ADR-0012 shell technology · ADR-0013 installer · ADR-0020 skill signing · ADR-0021 encrypted sync · ADR-0022 MSIX · ADR-0026 code signing and updates |

Partially settled: ADR-0014 default voice (Kokoro `bm_george` accepted; public
redistribution licensing still open), ADR-0015 TTS providers, ADR-0017 embedding
model (configured, not benchmarked).

**Nothing on this list blocks Phase 1.**

## Next Exact Steps

**Start here (2026-08-06).** Stage 4 is code-complete and green (1279 passed, 2
skipped, exit 0), and **the owner has not yet exercised any of part 2**. This
phase has now found five times that a green suite says nothing about the seams,
so acceptance comes before anything new. In order:

1. **Owner runs `docs/PHASE-02-ACCEPTANCE-TESTING.md` §4.12–§4.16.** §4.12 is
   the retry of their own Edge repro and is the one that matters: play something
   in Edge that prompts on close, ask Jarvis to close it, and confirm it never
   says "closed". §4.13 capture, §4.14 "what's on my screen", §4.15 the speech
   logs.

2. **Then close stage 4:** `graphify . --update`, phase notes, and the stage
   commit.

3. **Still open and deliberately not done:**
   - `privacy.screenshot_retention` is not implemented; captures are only
     bounded to the newest 20.
   - Reading screen *contents* needs a vision model — Phase 4 (P4-VIS-01).
   - The all-tabs-autoplay limitation under Playwright is still documented
     rather than fixed; the single-tab CDP replacement is spiked and proven but
     not applied.
   - Sensitive-application acceptance testing is deferred by the owner (they use
     none of those applications).

**The earlier stage-3 steps below are superseded by acceptance, not cancelled.**

---

### Superseded (2026-08-05)

The six fixes above are committed and the suite is green, but **none of the
browser path has been exercised end to end on real hardware since they landed**.
In order:

0. **Live-test the restart path.** With Brave open, ask for a YouTube search.
   Expect: `youtube.search` fails `browser_restart_required` → the planner calls
   `browser.restart` → one approval → Brave closes, reopens with tabs restored →
   the search runs. Watch for three specific things: whether the planner
   actually makes that second call (it has four rounds and has been observed to
   narrate instead of acting), whether the tabs really come back, and whether
   the new tab is dark. If the planner does not chain the calls, that is the
   next defect and it is a planner problem, not a browser one.

0a. **Then choose "Allow always"** at the approval prompt and confirm the next
   several requests do not ask again. Check the Permissions screen lists it and
   that revoking it there restores the prompt.

0b. **Close the tab mid-session** and search again — it should open a new one
   rather than failing.

**Stages 0, 1 and 2 are complete. The rest of stage 3 — the exit criterion —
follows.**

1. **Stage 3 order:** P2-BRW-01 (the Jarvis profile — it already exists on the
   machine, created by the stage 0 spike) → P2-BRW-02 (Playwright over CDP,
   DOM-first, visible by default) → **P2-BRW-08, the exit criterion** →
   P2-BRW-04 (CAPTCHA pause) → P2-BRW-03 (clear profile) → P2-BRW-09.

2. **Every browser action runs inside an `AutomationSession`**
   (`jarvis/toolbox/automation.py`). It is the only thing that hands out
   permission to move anything, and a step that injects input must pass
   `sends_input=True` or the watcher will read our own action as the user's and
   pause the task for no visible reason.

3. **Stage 3 consumes stage 1's boundary; do not build a second one.** The
   browser adapter produces `ObservedList` / `Observation`
   (`jarvis.core.observations`) and selects by ordinal. If a `find_by_title` or
   similar appears anywhere, the injection defence has been undone —
   `tests/security/test_prompt_injection.py` asserts structurally that no such
   method exists. Stage 0 measured that YouTube results are index-addressable
   (13 × `ytd-video-renderer` in DOM order), so this is known to work.

4. **Do not let Playwright launch a browser.** Enforced by
   `tests/security/test_browser_attach.py` (ADR-0031), but worth knowing rather
   than discovering: launch through `jarvis.toolbox.launch.launch_argv` with a
   `--remote-debugging-port` and attach with `connect_over_cdp`.

5. **The first tool that moves the pointer settles an open measurement.** The
   `UserInputWatcher` baseline may be read before Windows registers our
   injection, making automation pause on its own action. Watch for automation
   stopping with no user cause, and measure it against a real `SendInput`.

6. **`succeeded` still requires verification.** Clicking the second result and
   reporting success is `started ≠ running` wearing a new hat: playback is
   `unverified` until player state is read back and the video id matches.

7. **Deferred to stage 6, deliberately:** the time/date tool (gates nothing) and
   the application-catalogue work (P2-WIN-01, behind its own ADR — Start-menu
   discovery as the executable source, approval on first use, a `.lnk` parser
   that runs nothing, care around the `powershell.exe` shortcut every Start menu
   contains).

8. **Outstanding for the owner, not blocking:** `docs/PHASE-02-ACCEPTANCE-TESTING.md`
   §0.7 is the two-run test that would confirm the leading cause of the original
   YouTube Music tab (Brave closed → app; Brave running → tab). One observation
   settles it, and if it holds it changes how the Phase 2 application catalogue
   must verify itself.

6. **Graphify is stale and cannot update without an LLM API key.** `graphify .
   --update` exits reporting `no LLM API key found`; 17 changed docs need
   semantic extraction, including ADR-0027…ADR-0031 and this document. Set
   `GEMINI_API_KEY` (or `ANTHROPIC_API_KEY`/`OPENAI_API_KEY`) as a **user
   environment variable — never in the repo** — then re-run. `--code-only` was
   deliberately not used: it may prune the existing doc nodes from a committed
   `graph.json`. Nothing in the Phase 2 plan depends on the graph.

### Carry these habits into Phase 2

- **Test the seam, not just the unit.** Six acceptance rounds all found the same
  class of defect: components that worked, connected to nothing. The rule that
  caught them is worth restating — an enabled control either does something or
  says why it cannot.
- **Read the exit code.** A UI suite reported every assertion passing and
  returned `0xC0000374`.
- **Write the test named after the defect**, in the words the defect was
  reported in. Every regression test added this phase is readable as an account
  of what went wrong.

## Uncommitted or Temporary State
Nothing uncommitted. Phase 1 is merged into `main` (`b9e73e0`, PR #2). Phase 2
work is on `feat/PHASE-2-development`. Nothing is stubbed to report false
success; every unbuilt screen and menu entry still names its phase (ADR-0010).

**Environment changes made during stage 0**, so a fresh checkout is not
surprised by them:

- `pip install -e ".[automation]"` was run, adding playwright 1.62.0,
  pywinauto 0.6.9, comtypes, pywin32, pyee and greenlet to `.venv`. Required to
  run `tools/browser-lab/test_playwright_attach.py`.
- `playwright install` was **not** run and must not be. The product drives the
  user's real Brave, never a bundled Chromium (ADR-0019, ADR-0031).
- A **`Jarvis` Brave profile now exists** at
  `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Jarvis`, created by the
  spike. It is empty and signed out. Note it lives **outside the vault**, so
  FR-057 and any full-deletion path must delete it explicitly — recorded as a
  requirement in ADR-0019.

No temporary migrations or compatibility shims. No process needs to be running;
Ollama is optional. `tools/voice-lab/` and `tools/qwen-tts-lab/` are research
spikes outside the product runtime and are **not** covered by the security policy.

## Relevant References
- **Requirements:** `PRD.md` §21 (phases), §22 (AT-001…AT-034), §10.2–10.5 (Phase 1 FRs)
- **Phase 0 record:** `docs/phase-reports/PHASE-00-FOUNDATION.md`
- **Operating contract:** `CLAUDE.md`
- **Phase 1 decisions:** ADR-0016, ADR-0027, ADR-0028
- **Architecture:** `ARCHITECTURE.md` §8 (extension points — the protocols Phase 1 fills), §12, §13
- **Security:** `SECURITY.md` §14 (status table)
- **Threats:** `THREAT_MODEL.md` §5.4 (voice threats), §6 (Phase 0 residual risks)
- **Plan:** `docs/BACKLOG.md` §4 (Phase 1 work items)
- **Verified voice spikes:** `tools/voice-lab/test_whisper.py`, `tools/voice-lab/test_kokoro.py`
- **Graph:** `graphify-out/GRAPH_REPORT.md` — 121 communities; god nodes
  `JarvisCore` (100), `EventBus` (76), `ToolCall` (71), `AuditLog` (70), `Database` (62)
