# Known issues

Every defect and limitation the owner has hit that is **not fixed**, plus the
ones that were worked around rather than solved. Requested 2026-08-06.

The point of this file is that a workaround stops looking like a workaround
after about a week. Each entry says when it appeared, what was actually done
about it, and whether it is still there — so "we handled that" can be checked
rather than remembered.

**Status vocabulary**

| Status | Means |
|---|---|
| **Open** | Still happens. Nothing between you and it. |
| **Mitigated** | Still there underneath; something reduces how often it bites. |
| **Worked around** | A different mechanism avoids it; the original is untouched. |
| **Deferred** | Understood and postponed by decision, not by neglect. |
| **Environmental** | Not the product. Recorded because it looked like the product. |

---

## 1. Opening the browser wakes every other tab, and YouTube tabs start playing

- **Found:** Phase 2, stage 3 (2026-08-05), by the owner: *"all other youtube
  tabs start playing too, and i hear all together"*.
- **Status:** **Open**, deferred by the owner.
- **Cause:** Playwright's `connect_over_cdp` attaches to **every page in the
  browser** — measured, ten of ten. It is built to drive a browser it owns, and
  ADR-0019 Option D points it at the owner's daily browser. There is no option
  to narrow the attach, so this cannot be fixed above Playwright.
- **What was done:** nothing to the product. The replacement is spiked and
  proven — `tools/browser-lab/test_single_tab_cdp.py` drives one tab over raw
  CDP and leaves three decoy videos untouched — and was deferred rather than
  allowed to hold up the phase.
- **To fix:** replace `PlaywrightPageDriver` with the single-tab CDP driver.
  The spike is the design; it needs productionising, not inventing.
- **Note:** opening Brave by hand does *not* do this. It is caused by the
  attach, not by Brave.

## 2. "YouTube Music" plays the wrong thing

- **Found:** Phase 2, stage 3 and again 2026-08-06: asked to play a song, Jarvis
  searched YouTube for the words *"youtube music"* and played the first result.
- **Status:** **Mitigated.** The common case works; the real bug is untouched.
- **Cause:** two different places wearing one name. `app.open` opens the YouTube
  Music **progressive web app**; `youtube.search` and `youtube.play` drive
  **youtube.com** over CDP. Nothing told the model they are not interchangeable,
  and the whole browser stack is hardcoded to YouTube's DOM
  (`ytd-video-renderer`, `a#video-title`).
- **What was done:** the tool descriptions now say which is which —
  `media.control` is named as the way to control an already-open player, and
  `youtube.play` says explicitly that it is *not* how to drive YouTube Music and
  that reaching for it causes a browser restart nobody asked for. That fixes
  *"play the current song"*. It does not give YouTube Music a search.
- **To fix:** P2-BRW-09 — a second site profile (search URL, result selector,
  title selector, player read) for `music.youtube.com`. **The selectors must be
  measured against the real page**, which means opening a browser on the owner's
  desktop; writing them from convention is the failure this project avoids
  elsewhere.

## 3. `play_pause` is a toggle, so "play" can pause

- **Found:** 2026-08-06, while fixing issue 2.
- **Status:** **Open**, minor.
- **Cause:** `media.control` sends the keyboard media key. There is one key for
  both, and nothing reports what the player was doing beforehand.
- **What was done:** said so in the tool description, so the model can warn
  rather than promise.
- **To fix:** read the current playback state first. Windows exposes it through
  the Global System Media Transport Controls, which is not wired up.

## 4. Voice interruption (barge-in) does not work on this hardware

- **Found:** Phase 1 acceptance (2026-08-04).
- **Status:** **Deferred** by the owner.
- **What was done:** `audio.duplex_mode` ships as `half` — the degradation
  ADR-0028 named in advance, and what FR-015 permits for Phase 1. Rather than
  leave a claim standing that the feature works. `Ctrl+Alt+End` and the tray's
  **Stop speaking** both work.

## 5. Wake-word enrolment is not built

- **Found:** Phase 1.
- **Status:** **Deferred** (ADR-0016).
- **What was done:** the shipped threshold is a **measured** default, not a
  guess: "Hey Jarvis" scores 0.994–0.998 and bare "Jarvis" 0.268–0.464 on this
  machine. The Settings control is shown disabled and names its phase, per
  ADR-0010, rather than being hidden or stubbed.

## 6. The wake word sometimes reaches the planner as part of the command

- **Found:** 2026-08-06 — *"H-Arvis Open MS Edge and Brave"*, which cost a whole
  turn to Jarvis asking what "H-Arvis" meant.
- **Status:** **Mitigated.**
- **Cause:** the stripper wanted both words of "Hey Jarvis" in order. What
  arrives is whatever faster-whisper made of a word said at a microphone.
- **What was done:** a near-miss of the name is now removed, at a similarity
  threshold that keeps "harvis" and rejects "jar" and "Java" — those are words,
  and eating them would eat the command. A different mishearing could still slip
  through; send the transcript if one does.

## 7. The model announces actions instead of taking them

- **Found:** repeatedly, 2026-08-06. *"I'll close it for you"*, and the turn
  ended.
- **Status:** **Mitigated** (ADR-0033), and cannot be fully solved here.
- **What was done:** a turn now continues while its own reply describes work
  nothing did — a promise, an unbacked completion claim, a claim about a
  *different* action than the one performed, an unresolved tool failure, or an
  empty reply. Bounded at 12 rounds and 3 consecutive unproductive pushes.
- **What is still true:** this stops a turn *ending* on an unkept promise. It
  cannot make the model choose the right tool. A model that cannot do the job
  now fails honestly after three attempts instead of one — a better failure, not
  a success.

## 8. Detecting a false success claim relies on a list of phrases

- **Found:** four times in one day, each time a new spelling: "was closed" after
  "has been closed" was covered; "closed successfully" after "successfully
  closed"; "let me **use** the search tool" where a known action verb was
  expected; "It's already playing" past all of them.
- **Status:** **Mitigated**, and the limitation is structural.
- **What was done:** the fourth escape ended the approach. The turn now checks
  the **user's request** against which tools actually ran, because the request
  is short, imperative and does not shift its wording. The phrase lists remain
  as a backstop only.
- **What is still true:** a closed list has a next gap. If Jarvis claims
  something it did not do, **send the sentence verbatim** — both escapes were
  found that way and neither would have been found otherwise.

## 9. Screenshot retention is a bound, not a policy

- **Found:** 2026-08-06, when capture shipped.
- **Status:** **Open.**
- **What was done:** the newest 20 captures are kept, so the folder cannot grow
  without limit. A full-screen BMP is roughly 15 MB.
- **What is missing:** `privacy.screenshot_retention` describes what the product
  should do — discard when the task ends, and so on — and is **not implemented**.
  The bound must not be mistaken for the policy.

## 10. Captures are large uncompressed bitmaps

- **Found:** 2026-08-06.
- **Status:** **Open**, by choice.
- **Why:** Pillow is not installed, and a hand-rolled PNG encoder is exactly the
  kind of thing that is subtly wrong in a way nothing available could catch. BMP
  is four fixed headers and a pixel array, verifiable by reading its own bytes
  back — which the live lab does.

## 11. One test is flaky

- **Found:** 2026-08-06. `test_the_task_state_machine_is_persistent` failed once
  in a full run and passed in isolation and in three further full runs.
- **Status:** **Open.**
- **Cause:** the test reopens a core whose scheduler can dispatch the queued task
  before the assertion reads it. A race in the *test*, not in the product.
- **What was done:** written down rather than re-run until green.

## 12. The full test suite downloads models from the internet

- **Found:** 2026-08-06, when the owner noticed the suite was heavy.
- **Status:** **Worked around.**
- **Cause:** three wake-word tests call the real installer, which fetches from
  GitHub. It is why full-run timings swung between 90 and 234 seconds.
- **What was done:** marked `slow`. `pytest -m "not slow"` runs in ~78 seconds
  and opens no socket. The full run still downloads.

## 13. Windows bugchecks on this machine

- **Found:** 3–6 August 2026. Four crashes: `0x7E` and `0x3B` (both
  `c0000005`), `PFN_LIST_CORRUPT`, then `UNEXPECTED_STORE_EXCEPTION`.
- **Status:** **Environmental**, owner handling it.
- **Why it is here:** a run of the test suite returned `0xC0000005` with no
  failure summary during that window, which looks exactly like a product defect.
  It did not reproduce across three subsequent clean runs. No WHEA errors were
  logged at all, and the DDR5 is on an EXPO profile at 6000 — that pattern is
  memory instability, and three of the four crashes predate the code that was
  being blamed.

---

## Resolved, kept for the record

These were real and are fixed. They are listed because each one was a *class* of
mistake this project keeps making, and the pattern is more useful than the fix.

| Issue | Stage | What it really was |
|---|---|---|
| `app.close` reported a verified success on an open Edge | 2 / stage 4 | Verifying with a list built for a different purpose — "is it presentable" answered instead of "does it exist" |
| A window listing licensed a claim that something had been closed | 2 / stage 4 | A read-only tool reporting `verified`, which the grounding layer read as licence for any success claim |
| A verified `app.open` licensed "and playing the current song" | 2 / stage 4 | "Did *any* tool verify something" was the wrong question; one had |
| Jarvis spoke a HF Hub request on every spoken reply | 2 / stage 4 | Kokoro resolves voices at synthesis time and the hub revalidates cached files |
| `storage.huggingface_home` was never applied | 1 → fixed 2 | Configuration that only worked if you already knew to export `HF_HOME` |
| The offline switch was read too late to work | 2 | `huggingface_hub` captures it at import; the test asserted only the env var |
| The test suite spoke out loud | 2 | Three UI tests simulated a *spoken* command, which is answered aloud by design |
| "Move my IDE to the left" moved the Jarvis window | 2 / stage 4 | Addressing windows by position in a list that reorders when you act on it |
| Eleven windows listed where the owner had four | 2 / stage 4 | No filter for cloaked, tool, zero-area and caption-less windows |
| "Bring to the front" reported success without checking | 2 / stage 4 | Confirmed only that the window was not minimised |
| "Open YouTube Music" opened a tab, not the app | 1 → fixed 2 | The app id was right; the launcher was handing a URL to the browser |
| A launch reported success because Brave was already running | 2 / stage 0 | A check that cannot tell "my effect happened" from "this was already true" |

**The pattern worth naming:** eight of these are the same mistake — something
reported success it had not earned, because the check it ran could not tell the
difference between "I did this" and "this was already true". That is why
`succeeded` requires verification here, and why `unverified` is a distinct
outcome rather than a soft failure.
