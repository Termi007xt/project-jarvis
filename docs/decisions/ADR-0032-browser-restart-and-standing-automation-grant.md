# ADR-0032: Jarvis closes and reopens the browser itself, and browser automation may hold a standing grant

- **Status:** **Accepted** — both halves decided by the project owner on 2026-08-05, in response to a recorded failing session
- **Date:** 2026-08-05
- **Deciders:** Project owner
- **PRD reference:** FR-048, FR-056, FR-090, §9.9, §11.1, §21 (Phase 2)
- **Phase:** 2

## Context

On 2026-08-05 the owner asked Jarvis to open YouTube and search for "best monitors". The full sequence is in `logs/audit.jsonl` and is worth reading as one story, because the first step is what broke the second:

| Local time | Event |
|---|---|
| 12:35:28 | `app.open(youtube)` launched `brave.exe` **without** a debugging port. Verified success. No search tool was called. |
| 12:36:24 | `youtube.search("best monitors")` was approved, then failed: *"Brave is already open, and a browser that is already running cannot be given an automation port"* |
| 12:37:36 | Identical failure |
| 12:38:30 | Owner quit Brave by hand. The same request then worked and read back 20 results. |
| 12:42:51 | `youtube.search("latest anime")` failed: `Page.goto: Target page, context or browser has been closed` |

Two decisions come out of it. They are recorded together because they were taken together and because each is unsatisfying without the other: fewer prompts on a capability that cannot complete its own work would just fail faster.

### The browser made its own next step impossible

`--remote-debugging-port` is a **startup** flag. A second `brave.exe` handed to a running instance forwards its command line and exits, so no port ever appears. `BraveCdpSession` refuses that case immediately and correctly (ADR-0031, and `tests/unit/test_browser_session.py` asserts it fails fast rather than waiting out a 20-second timeout that could only ever fail).

What was wrong is what came next. There are four ways to start Brave — `app.open`, `web.open_url`, `web.search` and the automation session — and only the last opens a port. So Jarvis opening YouTube for the owner is precisely what stopped Jarvis from searching it, and the only remedy was the owner alt-tabbing and quitting a browser **Jarvis had opened itself fifty-six seconds earlier**.

Jarvis knew the remedy and said so, four times, in language like *"Closing Brave briefly then reopening will restore your tabs and allow me to search for 'best monitors'. Would you like me to close it now, Sir?"* — and then had no capability to close anything. Told only that the browser was "unavailable", the model eventually improvised instructions for a human: *"I need you to manually quit Brave once from your taskbar or system tray (right-click → Quit)."*

That is ADR-0010's rule broken at the level of a whole capability. An offer Jarvis cannot honour is worse than an admission it cannot act, because the owner spends their attention acting on it.

### Four approvals in seven minutes, all discarded

The same log shows this, four times:

```
07:06:24 security   approval scope 'task' rejected for browser.automate_logged_in
         error: scope 'task' requires a task_id
07:06:24 permission approval allow for browser.automate_logged_in
```

The dialog offered **Allow for this task**, the owner chose it, and the engine threw it away — `ToolCall.task_id` was only ever set by the scheduler, so a request that came from *talking to Jarvis* carried none. The invocation ran once under a scope nobody had chosen, and the next sentence asked again.

So the owner met a permission prompt on every utterance, each one identical, each one answered the same way. Their own summary was *"permissions ... are kind of blockers"*. A prompt that appears that often is one nobody reads, which makes it worth less than the interruption costs.

## Options considered

### For the browser: how should "already running" be resolved?

**Option 1 — one owned session for every browser action.** Route `app.open`, `web.open_url`, `web.search` and the automation tools through a single session Jarvis always starts with a debugging port. "Open X" becomes a tab in it. The conflict disappears entirely because there is only ever one way to start the browser.
*Rejected by the owner.* It buys the cleanest lifecycle at the cost of leaving a CDP port open on the browser whenever Jarvis opened it at all, including for a plain "open YouTube" that needs no automation. That widens ADR-0031's session-scoped port to nearly all browser use.

**Option 2 — ask to restart, bundled into one approval.** Keep the launch paths as they are. When automation finds Brave running without a port, close it and reopen it — as one approved act, with the tabs restored. **Chosen.**
The port stays session-scoped exactly as ADR-0031 requires. The cost is a visible restart when the owner (or Jarvis) opened Brave the plain way first.

**Option 3 — drop CDP; just navigate to a search URL.** `youtube.search` becomes what `web.search` already is.
*Rejected.* It is genuinely simpler and it is what the owner's instinct suggested — *"it can literally just create url with the search parameters and go to that"* — but it loses reading results back and therefore "play the second video", which is the Phase 2 exit criterion.

### For permissions: how much should one approval cover?

**Option A — fix "for this task" only.** One approval covers every tool call one request needs. Still prompts on each new request.
**Option B — that, plus "for this session".**
**Option C — allow a standing "always" grant for browser automation.** **Chosen**, with the trade-off put to the owner in writing beforehand: fewest interruptions, weakest standing control on a browser holding their live logins.

## Decision

### 1. `browser.restart` is a tool

A new narrow typed tool with its own capability (`browser.restart`, medium risk, phase 2) that closes the browser and reopens it attached.

**Its own capability, deliberately not folded into `youtube.search`.** An approval to search YouTube is not an approval to take someone's windows away. Burying a second effect inside a tool the user approved for a different one is the same widening ADR-0029 forbids for launching, and it would leave the approval dialog describing something other than what happens.

**The close is a request, never a kill.** `WM_CLOSE` is posted to Brave's visible top-level windows and the process is then polled until it exits. Chromium takes that as "quit", writes its session out, and restores those tabs — which is the whole difference between the promise Jarvis kept making and "Brave didn't shut down correctly". A browser that will not close (a page holding an unsaved-changes prompt) is a **failure with an explanation**, never an escalation to `TerminateProcess`: that prompt is the owner's to answer, and discarding their work to satisfy a search would be a far worse outcome than saying so.

No new process-creation call site is involved. Closing a window is `user32.PostMessageW`, and the reopen goes through `launch_argv` exactly as before, so **ADR-0029's single-call-site invariant is untouched**.

`browser_restart_required` is a distinct failure code from `browser_unavailable`, because this is the one browser failure with a known automatable remedy, and the tool's description names the code it answers and states plainly that the user must never be asked to close the browser themselves.

### 2. A named medium-risk capability may hold a standing grant

`DefaultPolicy.always_allowable_capabilities` lists capability ids that may be granted `ALWAYS` despite being medium risk. `config/defaults.yaml` names exactly one: `browser.automate_logged_in`.

Four properties make this an exception rather than a reclassification:

1. **It is offered, never defaulted.** The capability still evaluates to `ASK` until the owner picks "Allow always" in the dialog. It is then an ordinary grant — visible on the Permissions screen, revocable there, recorded in the audit log.
2. **It is named one capability at a time.** `fs.read_approved` and every other medium-risk capability are unaffected; `tests/unit/test_approval_scopes_that_stick.py` asserts they still refuse an `ALWAYS` grant.
3. **The code default is empty.** A fresh install has PRD §11.1's posture exactly. The decision lives in a configuration file the owner can edit or empty, not in a risk table.
4. **High risk is never eligible.** That check runs first and does not consult this list. PRD §9.9 and §11.1 are untouched.

### 3. A conversation turn is a task

`ConversationEngine` mints a task id per user turn and every tool call in that turn carries it. "Allow for this task" now covers the whole of what one request needs — restart the browser, then search — instead of being discarded.

**Per turn, not per conversation.** "For this task" quietly becoming "for as long as we keep talking" is the same defect pointing the other way.

A general rule falls out of this and is now asserted structurally: **a scope the dialog offers must be one the engine can grant.** `tests/unit/test_approval_scopes_that_stick.py` walks the offered-scope table and grants each entry, so the dialog and the engine cannot drift apart again.

## Consequences

**Accepted, and not claimed to be mitigated: a standing `browser.automate_logged_in` grant means browser automation runs without a prompt.** Combined with ADR-0019's decision to drive the owner's own signed-in profile, an action a page induces executes as the signed-in user against every service they are signed into, with no per-action confirmation. The compensating controls ADR-0019 already makes load-bearing become more load-bearing still: positional selection only (`tests/security/test_prompt_injection.py`), the untrusted-content boundary, and the CAPTCHA pause. This is recorded in `THREAT_MODEL.md` as an increase in residual risk, taken knowingly by the person whose accounts are at stake.

**Restarting the browser is visible and occasionally unwelcome.** It closes every window, including ones unrelated to what was asked. Tabs return; anything typed into a form and not submitted may not. The approval dialog names the reason, and the tool refuses rather than forcing a window that objects.

**The restart is not automatic.** The planner has to call it after seeing `browser_restart_required`, which costs a round of the four the conversation allows. Making the engine do it silently would be a second path from a plan to an effect, which the architecture does not have and should not grow.

## Related

ADR-0010 (an offered control either works or says why not), ADR-0019 (which profile automation drives, and the risk that choice accepted), ADR-0027 (the approval scope table this amends), ADR-0029 (untouched: no new process-creation call site), ADR-0031 (the session-scoped CDP port this preserves), PRD §9.9, §11.1, `THREAT_MODEL.md`, `SECURITY.md` §14.
