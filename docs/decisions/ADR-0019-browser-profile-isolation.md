# ADR-0019: Browser Profile Isolation

- **Status:** **Accepted — Option D, the owner's own profile.** Supersedes Option A and Option B, both tried on 2026-08-04. **This is a recorded departure from FR-056**; see "Revised again" below.
- **Date:** 2026-08-01, decided 2026-08-04
- **Deciders:** Project owner
- **Phase:** 2
- **PRD reference:** §25.9, FR-056–FR-058; also §12.1, `PROJECT_INPUTS.md` `automation.dedicated_browser_profile: Jarvis`
- **Decision required before:** Phase 2 (Brave dedicated profile is an explicit Phase 2 deliverable)

## Context

FR-056 requires browser automation use a dedicated "Jarvis" Brave profile by default, into which the user may log in to services. FR-057 requires the user be able to clear the Jarvis browser profile, cookies, and site permissions. FR-058 requires Jarvis pause and ask the user to complete CAPTCHAs or anti-bot challenges rather than attempt to bypass them (§11.1 additionally lists "CAPTCHA bypass" as a prohibited capability). `PROJECT_INPUTS.md` already fixes the *name* and existence of this profile (`dedicated_browser_profile: Jarvis`), and §12.1 fixes the general shape ("Dedicated persistent Brave profile," "DOM-first execution," "Visible browser by default"). What is not yet fixed is the *mechanism*: Brave exposes several distinct ways to isolate a profile, each with different guarantees around what Playwright can see, control, and — critically — what persists across restarts.

This matters more than an ordinary implementation detail because of what the profile will contain once FR-056 does what it says: a user who logs into email, shopping, or work services inside the "Jarvis" profile has placed live, authenticated sessions under this product's control. ARCHITECTURE.md §3 shows `Auto -->|Playwright, dedicated profile| Web`, and §6.4's permission engine treats `browser_profile:<name>` as a named lock resource — but the lock model governs *concurrent task access*, not the deeper question this ADR addresses: once automation runs inside a profile holding live logins, any defect, a successful prompt-injection attempt (the FR-054/§11.4 concern from ADR-0018), or an overly broad tool scope can act *as the logged-in user* against those services — sending messages, making purchases, changing settings — exactly the high-risk capability class §11.1 lists. The isolation mechanism is the last line of defence bounding what the automation worker can reach, not just which cookies belong to which task.

## Options considered

### Option A — Separate Brave profile directory (`--profile-directory`)
Use Chromium/Brave's own multi-profile feature (the same mechanism behind "Profile 1," "Profile 2" in the browser's own UI), pointed at a `Jarvis` profile inside the standard Brave user-data directory, launched via Playwright's `launch_persistent_context` or by driving the installed Brave binary directly.
**Pros:** closest to "the user's actual Brave" — extensions, Brave-specific features, and the visible browser chrome behave exactly as a manually opened profile would, which matters for FR-052/FR-058's visibility and CAPTCHA-pause requirements, since a genuinely normal browser window is what the user interacts with during a pause; "clear the Jarvis profile" (FR-057) maps directly onto Brave's own delete-profile flow.
**Cons:** shares the underlying Brave installation and update cadence/extension ecosystem with the user's own default profile — a marginally larger shared surface than a fully separate data directory; Playwright's official support is strongest for its own bundled Chromium or `--user-data-dir`-style launches, so driving Brave's own profile-directory switch through Playwright needs verification that automation hooks (CDP) attach correctly to a *named profile* rather than a fresh data directory.

### Option B — Separate `--user-data-dir` entirely, distinct from the user's normal Brave installation
Point Brave at an entirely separate user-data directory under the vault (`ProjectJarvis\browser\brave-profile\`, exactly as ARCHITECTURE.md/PRD §14.2's suggested vault layout already shows).
**Pros:** the strongest filesystem-level separation from the user's personal browsing profile — a defect that reads or writes browser-profile files cannot reach the user's actual personal Brave data at all; matches the vault layout already documented, so "the profile lives in the vault, is relocatable with it, and is fully deletable with it" falls out of the existing vault design for free; "clear the profile" (FR-057) becomes "delete this directory."
**Cons:** Brave/Chromium launched against a foreign user-data-dir sometimes shows a "not your default browser" or first-run interstitial the automation needs to dismiss reliably; extensions and any user customisation of their normal Brave are not inherited (a pro for isolation, a con for convenience if the user expected customisations to carry over).

### Option C — Playwright's own persistent context against bundled Chromium (not the installed Brave)
Use `playwright.chromium.launch_persistent_context()` with Playwright's bundled Chromium rather than the actual Brave executable.
**Pros:** best-documented, most reliable Playwright automation surface — this is Playwright's native use case, with the fewest CDP-attachment surprises.
**Cons:** directly contradicts §12.1's explicit "Dedicated persistent Brave profile" and `PROJECT_INPUTS.md`'s `dedicated_browser_profile: Jarvis` — the product has already committed to Brave specifically (plausibly for its ad/tracker-blocking defaults, which matter for a browser the agent controls), so silently substituting bundled Chromium would be a PRD deviation requiring its own justification.

## Revised again 2026-08-04 — Option D: the owner's own profile

**Decision.** Automation drives the owner's existing Brave profile (`Default`). No dedicated profile, no separate user-data directory.

**This departs from FR-056**, which requires a dedicated "Jarvis" profile. It is recorded here as a deliberate, owner-made exception rather than an oversight, and FR-056 should be read as unmet until this is revisited.

### Why the owner chose it

Both isolated options were built and used. Each produced a worse experience than the requirement anticipated:

- **Option A** collided with Chromium's single-instance model (below), so automation failed whenever their own Brave was open.
- **Option B** worked, but produced **two browser windows and two sets of logins** — "open YouTube" ran through the Phase 1 launcher into their personal profile while "search YouTube" ran through the automation session into the isolated one. The isolation read as a malfunction rather than a protection.

The owner asked directly what the worst case was and what would cause it, was given the answer below in writing, and reaffirmed the choice.

### The risk, stated plainly, because it is now accepted rather than mitigated

Browser session cookies are **ambient authority**: the browser attaches them to every request, and a site cannot tell an action taken by automation from one taken by the user. The approval dialog governs whether Jarvis may automate the browser; it cannot govern what an individual click means to a logged-in service.

The concrete failure is: text that Jarvis *reads* — a video description, a comment, a search result, a page it was asked to summarise — induces the planner to propose an action, and that action executes as the signed-in user. Against a dedicated profile the blast radius is whatever the user deliberately signed that profile into. Against their own profile it is every service they have ever signed into, including ones they have forgotten.

**Today the exposure is small**, because the only automation tools are `youtube.search` and `youtube.play`, and `play` takes an ordinal rather than anything a page controls. The exposure is not static: it grows with every tool added in stages 4–5 and in Phases 3 and 5.

### What this makes load-bearing

Isolation was the one control that did not depend on the model behaving. Removing it promotes the remaining controls from defence-in-depth to primary defence, and they should be treated accordingly:

1. **Positional selection** (`ObservedList.select`) — the only structural control left. No tool may resolve an action target from page-supplied text. `tests/security/test_prompt_injection.py` enforces this and must not be relaxed.
2. **No tool may take a free-form URL or selector from the model** and then *act* on the resulting page. Navigation the user can see is one thing; automated interaction on an arbitrary model-chosen page is another, and it is now the specific thing that must not be built.
3. **Medium-risk approval stays medium-risk.** ADR-0027 gives `browser.automate_logged_in` once/task/deny and no standing allow. That restriction is now doing more work than when it was written, and must not be widened to "always" as a convenience.
4. **This decision is revisited before stage 4 ships screen capture and filesystem reads**, and again before any tool that clicks an arbitrary element.

### Option D's own cost, which the owner accepts

Chromium's single-instance model still applies: with their Brave already running, a launch is handed to the existing process and no debugging port opens, so automation reports that it could not open the browser. Closing Brave first remains necessary. Option D removes the two-window confusion; it does not remove that.

---

## Revised 2026-08-04 — Option A was tried and replaced by Option B

Option A was chosen, built, and used. It failed in ordinary daily use, for a reason no test could have caught and the stage 0 measurement did not cover.

**What happened.** The owner ran the Phase 2 exit criterion with their personal Brave already open. Jarvis opened YouTube *in their personal profile* and a blank tab in the Jarvis profile; the next attempt failed outright with "the browser did not open its automation port". Retrying eventually worked, then failed again later.

**Why.** `--profile-directory` selects a profile inside the user's existing Brave user-data directory, and a Chromium user-data directory is served by **one browser process**. Launching Brave while the user's own Brave is running therefore does not start a new process at all — the command line is handed to the existing one, which opens a tab and exits. No debugging port is opened, because the process that would have opened it never started.

This is a property of Chromium's single-instance model, not a defect in Jarvis, and it is not fixable within Option A. The stage 0 spike missed it because it correctly closed Brave first — which is exactly the condition that hides this failure.

**Option B does not have the problem.** A separate `--user-data-dir` is a separate singleton, so it gets its own browser process and coexists with whatever the user has open. Stage 0 had already measured that CDP attaches under Option B.

**Option B also satisfies criterion 4, which Option A could not.** The profile now lives in the vault (`<vault>/browser/brave-profile/`), so a full data-deletion request reaches it by construction (§14.2, NFR-025) instead of requiring FR-057 to remember a directory outside the vault. The requirement recorded below against Option A is therefore met structurally rather than by discipline.

**What it costs.** The Jarvis profile no longer appears in Brave's own profile switcher, so signing it into a service means letting Jarvis open the browser and signing in there. Any logins already placed in the Option A profile do not carry over and must be redone once.

The Option A analysis is kept below rather than deleted, because the reasoning that chose it was sound on the evidence available, and the evidence that overturned it — a person using the product normally — is worth recording as the thing that settled it.

## Decision

~~**Option A** — a dedicated `Jarvis` profile inside the existing Brave user-data directory, selected with `--profile-directory=Jarvis`.~~ **Superseded, same day, by Option B.** Original reasoning retained below.

Option C was already ruled out by the existing commitment to Brave specifically. The choice between A and B was settled on two grounds: the owner's preference for the profile to be a first-class citizen of their own Brave installation, and a measurement that removed the only technical objection to it.

### The measurement that decided criterion 1

Criterion 1 required that Playwright attach CDP to the chosen mechanism against the actually-installed Brave binary, *verified empirically*. The concern was concrete: Chromium refuses `--remote-debugging-port` against its default user-data directory as an anti-cookie-theft guard, and Option A selects a profile inside exactly that directory — so Option A was expected to be incompatible with the CDP-attach approach ADR-0031 depends on. The owner pre-authorised falling back to Option B on that basis.

`tools/browser-lab/test_cdp_attach.py` measured both, on the target machine, 2026-08-04:

| Option | Result |
|---|---|
| A — `--profile-directory=Jarvis` | **CDP opened.** `Chrome/151.0.7922.71`, protocol 1.3 |
| B — `--user-data-dir=<temp>` | **CDP opened.** Same build |

The expectation was wrong. Brave 151 opens the port under both, so criterion 1 does not discriminate and Option A stands as chosen. The Option B fallback is not needed and is recorded here as a known-working alternative rather than a pending decision.

The measurement is only valid with **no Brave instance already running**: a second `brave.exe` hands its command line to the existing instance and exits, so Option A would report "no port" whether the flag was refused or merely handed off. Any re-measurement must close Brave first.

### What Option A costs, recorded rather than discovered later

**Criterion 4 is not satisfied by construction, and this is the real price.** Option B would have placed the profile inside the vault, so a full data-deletion request (§14.2, NFR-025) would reach it automatically. Option A places it at `%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Jarvis`, **outside the vault**. Two consequences follow, and both are now requirements rather than observations:

1. **FR-057 "clear the Jarvis browser profile" must explicitly delete that directory.** It cannot be satisfied by deleting the vault.
2. **Any full-data-deletion path must know the profile exists and remove it too**, or a user who asks Jarvis to delete everything will silently retain browser cookies and live sessions outside the vault.

**Criterion 5 remains a required test, not an assumption.** Chromium profiles have separate cookie jars, so the `Jarvis` profile should not inherit the personal profile's sessions — but "should" is what criterion 5 exists to reject. P2-BRW-01 ships with a test that signs into a service in one profile and asserts the other is unauthenticated.

### Login posture, decided with the same breath

The owner asked whether the automation browser would carry their existing logins. It will not, and that is the point of FR-056. **Decided 2026-08-04: the isolated profile stands, and the owner signs into the `Jarvis` profile once for whichever services they want Jarvis to reach.** The profile is persistent, so this is a one-time action, and Option A makes it convenient because the profile appears in Brave's own profile switcher.

The alternative — pointing automation at the personal `Default` profile — was considered and rejected. Phase 2 is the phase in which untrusted web content first reaches the planner, and browser automation executes as whoever the profile is authenticated as. Under `Default`, a successful injection acts against every service the user is signed into. Under `Jarvis`, it acts against only what the user deliberately granted. The Phase 2 exit criterion needs no login at all.

## Decision criteria

1. Playwright reliably attaches automation (CDP) to the chosen mechanism against the actually-installed Brave binary on the target hardware, verified empirically.
2. FR-057's "clear cookies, profile, site permissions" is implementable as a bounded, verifiable operation (ideally: delete/recreate a directory) rather than requiring driving Brave's own settings UI.
3. FR-058's CAPTCHA pause hands control to the user in a window they can directly interact with using their normal mouse/keyboard, with no automation-imposed friction (e.g. remote-debugging banners) making the CAPTCHA harder than in an ordinary browser.
4. The chosen mechanism's data lives inside the relocatable, deletable vault (§14.2, NFR-025) so a full data-deletion request actually reaches the browser profile — Option B satisfies this by construction; Option A requires confirming Brave's per-profile directory can be relocated into or symlinked from the vault path.
5. Isolation is verified to actually prevent the automation profile from silently inheriting the user's personal Brave session/cookies — a concrete test (log into a test service in the personal profile, confirm the Jarvis profile is not authenticated) should gate this decision regardless of which option is chosen.

## Consequences

### If Option B (separate user-data-dir under the vault) is chosen
Isolation and deletability both fall out of the existing vault design with minimal new code — ARCHITECTURE.md already treats `browser/brave-profile/` as vault-relative. The main engineering cost is handling Brave's first-run-against-a-fresh-profile behaviour cleanly so the first CAPTCHA-pause or first login is not preceded by an unrelated interstitial.

### Deferral cost
Moderate. Nothing in Phase 0–1 depends on this, but Phase 2's exit criteria explicitly include "Brave dedicated profile" as a deliverable, so it must close before Phase 2 exit. Because this profile will accumulate live logins once built, retrofitting a *different* isolation mechanism after users have already authenticated under the first one means asking them to log in again — a bounded but real migration cost, cheaper to avoid by deciding once.

## Related

ADR-0018 (search provider — FR-052/FR-055 execute inside this profile), ADR-0020 (skill signing — recorded skills that replay browser actions inherit this profile's trust boundary), ARCHITECTURE.md §3, §6.4, §11.1, PRD §14.2, NFR-025.
