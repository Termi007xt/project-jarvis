# Phase 2 — what you need to test

A running list. **I add a section at the end of every stage and keep working** —
you are never blocking me, and I am never claiming a stage works because a suite
was green. Delivery mode decided 2026-08-04: checkpoints are recorded here, not
waited on.

Each item says **what to run**, **what you should see**, and **what to tell me**.
Where something is expected to be imperfect, it says so — you are not looking for
a clean sheet, you are looking for the difference between what happens and what
is written here.

If anything differs, copy the exact text back. "It didn't work" is much harder to
act on than three lines of output.

## Before you start

```powershell
cd C:\Users\sharm\source\repos\project-jarvis
.\.venv\Scripts\Activate.ps1
```

**Running the suite:** `python -m pytest` — bare. Do **not** add `-q`;
`pyproject.toml` already sets it, and two of them suppress the final `N passed`
line, which looks exactly like a truncated crash and is not one.

---

# Stage 0 — measure and unblock

**Status: complete.** Nothing in this stage was a feature; all of it produced
facts that later stages depend on. Three of the five items below are things only
you can do.

## 0.1 — Rotate the API key ⚠️ **do this first**

You pasted a live Google AI Studio key into a chat transcript. It has been used
once (to update the knowledge graph) and should now be treated as burned.

**Do:** AI Studio → delete the key named `JARVIS` → create a new one. Then set it
as a **user environment variable**, never in the repo:

```powershell
[Environment]::SetEnvironmentVariable('GEMINI_API_KEY', '<your new key>', 'User')
```

Open a **new** terminal afterwards for it to take effect.

**You should see:** `graphify . --update` works in a fresh terminal without you
passing anything.

**Tell me:** nothing, unless it fails.

> **Worth deciding separately:** graphify's semantic extraction sends your
> documents — ADRs, PROJECT_STATE, the phase plan — to Google. This repo is
> marked proprietary and pre-release. Fine if that is a considered choice; tell
> me if it is not, and we stop running the doc half.

## 0.2 — Sign into the Jarvis Brave profile

This is the one stage-0 action that stage 3 actually needs from you. The
automation profile is deliberately **not** your personal profile — that is FR-056,
and it is why a hostile web page cannot act as you against your email or bank.
The trade is that you sign it in once.

**Do:** open Brave → profile switcher (top right) → you should now see a **Jarvis**
profile that the spike created. Open it, and sign into YouTube (and anything else
you want Jarvis to be able to reach — *only* those things).

**You should see:** a separate, empty Brave profile. None of your extensions,
none of your history, signed out of everything until you sign in.

**Tell me:** whether the `Jarvis` profile appears in the switcher at all.

> The Phase 2 exit criterion does **not** need a login — YouTube search and
> playback work signed out. Sign in only for the experience you actually want.

## 0.3 — Re-run the browser measurement yourself (optional)

**Do:** **close every Brave window first** — this matters, see below — then:

```powershell
python tools\browser-lab\test_cdp_attach.py
python tools\browser-lab\test_playwright_attach.py
```

**You should see:**

- First script: `Option A ... -> cdp_open` and `Option B ... -> cdp_open`, ending
  `ADR-0019 Option A stands.`
- Second script: `ATTACHED. contexts=1`, then
  `STRUCTURED RESULT LIST: N x 'ytd-video-renderer'`, then a numbered list with
  `[1]` marked `<-- 'the second video'`.

**Why Brave must be closed:** a second `brave.exe` hands its command line to the
running instance and exits, so no debugging port opens — and a refused flag looks
identical to a handed-off launch. A measurement taken with Brave running is not
wrong, it is meaningless.

**Tell me:** the two result lines, if they differ from the above.

**Both scripts leave a Brave window open.** Close it when you are done. They are
research spikes in `tools/`, outside the product and outside the security policy.

## 0.4 — Read two decisions that are yours, not mine

**ADR-0019** — I recorded a consequence of your Option A choice that its own
decision criteria flagged and that I do not want you discovering later:

> The `Jarvis` profile lives at
> `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Jarvis` — **outside the
> vault.** So "delete all my data" will *not* reach it unless we delete that
> directory explicitly. I have written that in as a requirement on FR-057 and on
> any full-deletion path.

Option B would have satisfied this automatically by putting the profile in the
vault. You chose A for good reasons and A works; this is the price, stated.

**ADR-0018** — I have proposed **visible Brave search only, no API-key search
modes**, for Phase 2. Shipping no key-consuming code makes §18.3's "no shared API
keys" impossible to violate rather than merely enforced. It is marked *Proposed*,
not *Accepted* — say if you want the optional-key modes instead.

**Tell me:** whether you accept both, or want either reopened.

## 0.5 — Confirm the suite is green on your machine

**Do:**

```powershell
python -m pytest
python -m pytest tests\security
```

**You should see:** `916 passed, 2 skipped` and `177 passed, 1 skipped`.

**Tell me:** any number that differs.

---

## What stage 0 found, in one paragraph

I predicted your ADR-0019 Option A would be incompatible with browser automation,
because Chromium refuses remote debugging against its default user-data directory.
**That prediction was wrong** — Brave 151 opens the port under both options — so
your choice stands and the fallback was not needed. Playwright then attached to a
browser *we* launched, keeping process-creation call sites at exactly one, and a
YouTube results page came back as 13 index-addressable rows, which means "the
second video" is a *position* and a page cannot rename its way into redirecting
an action. Separately, the YouTube Music defect turned out to be three defects and
none of them was the app id — the worst being that the tool reported
`verified` success while only ever observing that Brave was already running.

---

## 0.6 — Expect Jarvis to say "unverified" more often, on purpose

A change landed at the end of stage 0 that you **will** notice, and it will look
like a regression. It is the opposite.

**Do:** with Brave already open, ask Jarvis to open YouTube, or Brave, or YouTube
Music.

**You should see:** a reply along the lines of *"YouTube Music was asked to start,
but brave.exe was already running before this action, so seeing it now is no
evidence the action did anything. Reporting this as unverified rather than as
success."*

**Why this is right:** the old behaviour reported `succeeded / verified` — a
confirmed success — while checking only that Brave was running, which it usually
already was. That check could not tell "my effect happened" from "something
unrelated was already true", so it returned success whether the app opened, a tab
opened, or nothing happened at all. That is exactly how "Open YouTube Music"
recorded verified success every time it opened a tab.

Confirming these launches honestly means observing a **window**, which is UI
Automation — stage 4 of this phase. Until then Jarvis says it does not know.

**Tell me:** if the wording is confusing in speech. It is deliberately explicit
and may be too long spoken aloud.

---

<!-- Stage 1 section is added here when stage 1 completes. -->
