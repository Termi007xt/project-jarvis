# ADR-0019: Browser Profile Isolation

- **Status:** Open — decision required before Phase 2
- **Date:** 2026-08-01
- **Deciders:** Project owner
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

## Decision

Deferred. No option is selected yet. Option C is effectively ruled out by the existing commitment to Brave specifically, narrowing the real choice to A versus B, both of which can satisfy FR-056–FR-058 — the difference is isolation strength (B) versus native-profile fidelity (A).

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
