# Phase 2 — Deterministic Desktop and Browser Automation

**Closed 2026-08-06.** Branch `feat/PHASE-2-development`.

Phase 2 gave Jarvis hands. It can drive a browser, arrange and close windows,
photograph the screen, and find, reveal and open files — each through a narrow
typed tool, behind the same six checks, with `succeeded` meaning something was
observed rather than attempted.

The engineering was not the hard part. **The hard part was honesty**, and this
report is mostly about that.

---

## 1. Delivery shape

Checkpoint after every stage, decided 2026-08-04 and deliberately not Phase 1's
continuous run. Six stages:

| Stage | Contents | Status |
|---|---|---|
| 0 — Measure and unblock | CDP attach measured, ADR-0019 confirmed, YouTube Music defect diagnosed | Done |
| 1 — Untrusted boundary | `jarvis.core.observations`, positional addressing, delimiter wrapping | Done |
| 2 — Input ownership | `foreground_desktop` lock, interruption watcher, secure-desktop refusal | Done |
| 3 — Browser | Jarvis profile, Playwright over CDP, YouTube search and indexed play, browser restart | Done |
| 4 — Windows | Discovery, arrange, close, force-close, capture, screen context | Done |
| 5 — Files | Known folders, scoped search, reveal, open with an approved application | Done |

**21 of 30 backlog items done, 4 partial, 5 not started.** The five are named in
§7 with reasons; none of them is "we forgot".

---

## 2. Exit criteria (PRD §21, Phase 2)

> *"Search RTX 5070 on YouTube and play the second video."*

Met, and it is two utterances because it is two tools — `youtube.search` returns
an indexed list and `youtube.play` takes a **position**. That is not an
implementation convenience. A page chooses its own titles, so a tool that
selected by title would let the page choose what "the second video" means.

`tests/acceptance/test_phase2_exit_criteria.py` asserts the criteria as
invariants over the registered tool set rather than as a story about one action,
so a tool added next month is covered by them.

---

## 3. What was built

**Browser** — a dedicated automation profile (ADR-0019), Playwright attaching
over CDP to a browser Jarvis launched (ADR-0031), DOM-first extraction into an
`ObservedList`, playback verified by reading the player back, CAPTCHA pause, and
`browser.restart` (ADR-0032) because Chromium cannot be given a debugging port
while it is already running.

**Windows** — `window.list` and `window.arrange`, addressed by an opaque
reference the listing mints; `app.close`, which asks the way clicking the X asks
and stops when the application raises a dialog; `app.force_close`, the product's
first high-risk tool, with fresh confirmation every time and no standing grant
ever; `screen.capture`, which does not exist unless something can show the user
it is happening; `screen.active_window`, which names the front window and says
plainly it cannot read the contents.

**Files** — Known Folder resolution through `SHGetKnownFolderPath`; a scoped,
bounded search; `files.reveal`; and `files.open`, which hands a path to an
**approved application** and never to the Windows default association
(ADR-0034).

**Safety** — a sensitive-application blocklist keyed on process identity; secure
desktop refusal; screen redaction that blacks out blocklisted windows *before*
anything reaches disk; and a path boundary that resolves before it compares.

---

## 4. The theme: eight ways to claim a success you did not earn

Every serious defect in this phase was the same mistake in different clothing —
**a check that could not distinguish "I did this" from "this was already true"**:

| What was reported | What was actually checked |
|---|---|
| "YouTube Music opened" | Brave was running — which it already was |
| "I brought it to the front" | The window was not minimised — which it was not |
| "MS Edge has been closed" | Edge was absent from a list that drops hidden windows |
| "MS Edge has been closed" (again) | A *window listing* had verified successfully |
| "…and playing the current song" | `app.open` had verified successfully |
| "I moved your IDE" | A window at that *position* had moved |
| "Wake model installed" | Files existed on disk |
| "Offline mode is on" | An environment variable was set |

The corrections are structural rather than case-by-case:

- **`succeeded` requires verification**, and `unverified` is a distinct outcome
  that never satisfies a success criterion.
- **A read-only tool can never report `verified`** — it changed nothing, so it
  has nothing to verify. Enforced at the invoker, the one place every effect
  passes through.
- **Existence is not presentability.** Closing asks `IsWindow`, not "is it still
  in the list a person would call open".
- **A claim is checked against tools that could have produced it**, not against
  whether any tool verified anything.
- **The request is the specification.** The user's words are short, imperative
  and do not shift; the model's summary does. The turn checks what was asked
  against what actually ran.

---

## 5. A turn now finishes its work (ADR-0033)

The owner's session on 2026-08-06 produced the same complaint five times:
Jarvis announced an action instead of taking it, and the turn ended.

```
Sir: close MS edge
Jarvis: I'll close it for you.      <- the turn ended here
Sir: did you close it?
Jarvis: Nope, it's still there.     <- correct, and it could see that
```

That second exchange settled the design. **It knew.** It had the tool, the
information, and a system prompt already telling it not to claim what it had not
done. What it lacked was any reason to keep going.

A turn now continues while its own reply describes work nothing did — a promise,
an unbacked claim, a claim about a *different* action, an unresolved tool
failure, or an empty reply. Bounded at 12 rounds and 3 **consecutive
unproductive** pushes, so a long task is not punished for being long. A
**denied** permission is never retried: that is the user saying no.

---

## 6. Tests

| Suite | Result |
|---|---|
| `pytest -m "not slow"` | **1488 passed, 4 skipped, 3 deselected** (~83s, no network) |
| `pytest tests/security` | **485 passed, 3 skipped** (~7s) |
| `pytest` (full) | 1491 passed, 4 skipped — downloads wake models |
| `python -m jarvis.main --check` | exit 0, 18 tools, 15 applications |

Two suite defects were found by the owner noticing it was heavy: it was
**downloading models from GitHub** on every full run, and three UI tests were
**speaking out loud** through Kokoro to the sound card. Both fixed.

---

## 7. What was not built, and why

| Item | Reason |
|---|---|
| **P2-BRW-09** YouTube Music search | Deferred by the owner. Needs selectors *measured* against `music.youtube.com`; writing them from convention is the failure this project avoids elsewhere. |
| **P2-BRW-05** research with sourced summaries | Not started. A substantial feature, not a gap in something delivered. |
| **P2-BRW-07** AI-website prompting adapter | Not started, same. |
| **P2-BRW-03** clear browser profile | Not started. Small. |
| **P2-FS-04** disambiguation dialog | Not started. UI work. |
| **P2-WIN-01** catalogue scanning | Deferred by the owner in Phase 1; needs its own ADR before any code. |

Partial: **P2-WIN-02/03** (UIA inspector exists, not exposed as a tool),
**P2-FS-02** (reveal done; navigate/sort/filter not), **P2-BRW-04** (CAPTCHA
pause exists).

`docs/KNOWN_ISSUES.md` carries the thirteen live defects and limitations, with
the stage each appeared at and what was done about it.

---

## 8. Decisions taken during the phase

| ADR | Decision |
|---|---|
| **0019** (revisited) | Automation drives the owner's own browser profile; revisit closed 2026-08-06 with the whole-screen capture choice |
| **0031** | Playwright attaches to a browser Jarvis launched; it never launches one itself |
| **0032** | `browser.restart` exists, and browser automation may hold a standing grant |
| **0033** | A turn finishes its work before it answers |
| **0034** | A file is opened with an approved application, never a default association |

---

## 9. The lesson worth carrying into Phase 3

Phase 1's lesson was *test the seam, not the unit*. Phase 2 adds a sharper one:

> **A check that cannot fail is not a check.** Six times this phase, a correct,
> unit-tested mechanism was connected to nothing — and every one passed its own
> tests, because it worked perfectly in isolation against nothing.

The tests that caught these were always the same shape: *does the assembled
product actually offer this, and does the check it runs distinguish the case it
claims to?* Phase 3 introduces task trees, scheduled runs and memory — all of
which are **state that persists past the turn that created it**, where a false
"done" is not corrected by the user noticing in the next sentence.

---

## 10. Acceptance

The owner's closing test list is `docs/PHASE-02-ACCEPTANCE-TESTING.md` §C.1–C.7.
Every defect in §4 above was found by the owner pasting the exact sentence back;
none would have been found otherwise. That remains the single most valuable
thing they can do.
