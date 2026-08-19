# Changelog

All notable changes to Project Jarvis are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — Phase 2: deterministic desktop and browser automation

In progress. Stage 0 (measure and unblock) is complete; no automation capability
has shipped yet.

### Added

- **Jarvis can photograph the screen, visibly** (`screen.capture`, FR-073,
  FR-271, FR-272). You are always shown that a capture is happening, and the
  notice is raised before the picture is taken rather than after. If nothing can
  show that notice, the tool does not exist at all — not a tool that captures
  quietly. Windows belonging to applications on the sensitive list are filled
  black before anything reaches disk, because the blocklist guards *automation*
  and cannot guard a camera pointed at the whole screen. Jarvis never chooses
  where the file goes: the path is composed inside the vault, so the tool cannot
  become a way to write a file anywhere else. Only the newest 20 captures are
  kept.
- **Jarvis can say what you are looking at** (`screen.active_window`, FR-270 in
  part). Which application is in front, and a reference so "close this" and
  "move this to the left" work without listing first. It states plainly that it
  **cannot read the contents** of the screen — that needs vision support planned
  for Phase 4, and a description assembled from a window title would be
  invention dressed as observation.
- **Jarvis can see and arrange your windows** (`window.list`, `window.arrange`,
  FR-240 … FR-243). Bring a window forward, minimise, maximise, restore, snap to
  a half, or move it exactly. Two tools rather than one, because reading which
  windows are open and taking the foreground away from what you are doing are
  different risks: listing is low and holds no lock, arranging is medium and
  owns the desktop first. A window is named by a reference the listing hands
  out, never by its title, so a window cannot retarget an action by renaming
  itself. Snapping works the geometry out from the real screen rather than from
  a guess. Only windows a person would recognise as open are listed — no caption,
  cloaked, tool, owned and zero-area windows are left out, filtered on Win32
  attributes rather than on a list of names that would be both incomplete and
  defeatable.
- **Jarvis can close an application, and stops when it objects** (`app.close`,
  FR-065, FR-066, AT-004). The request is the same one clicking the X sends, so
  an application with unsaved work does what it should: it puts a save prompt
  up. Jarvis notices structurally — a new dialog from the same process — and
  stops there, leaving the prompt for you. It deliberately does not read the
  dialog to decide, because that text is written by the application being
  closed, and a "Save changes?" prompt is the single place where believing what
  a window says about itself would cost the most.
- **Force-close exists, separately, and asks every time** (`app.force_close`,
  FR-067, AT-005). The first high-risk tool in the product: fresh confirmation
  every time, no standing grant ever. A refused normal close never escalates to
  it on its own, and there is no `force` flag on `app.close` — reaching it is a
  decision a person makes, which a separate tool requires and a parameter would
  not.
- **Automation refuses windows that should not be touched** (FR-079, FR-081,
  AT-031). Credential managers, the Windows consent and logon surfaces, and any
  window whose own title names a secret. The refusal keys on process identity,
  which comes from the operating system; a window title may only *add* a
  refusal and never remove one, or the way past the password-manager blocklist
  would be for the application to rename itself. Sensitive windows are still
  listed, with their titles withheld, so Jarvis can say why it will not act.
  Nothing is automated at all while Windows is showing a UAC prompt, the lock
  screen or Ctrl+Alt+Del.
- **Jarvis can close and reopen the browser itself** (`browser.restart`,
  ADR-0032). It had been offering to do this for some time — *"Closing Brave
  briefly then reopening will restore your tabs"* — with no capability behind
  the offer, so the only way forward was quitting Brave by hand. The browser is
  *asked* to close rather than killed, so Chromium writes its session out and the
  tabs come back; a browser that will not close (a page asking to confirm
  leaving) is reported as a failure rather than forced shut, because that prompt
  is yours to answer. Its own approval, deliberately not folded into the search
  tools: approving a search is not approving the loss of your windows.
- **Browser automation can be allowed once instead of every time.** "Allow
  always" is now offered for it in the approval dialog (ADR-0032). Nothing is
  granted automatically — you still choose it, it appears on the Permissions
  screen, and you can revoke it there. Configured by name in
  `permissions.always_allowable_capabilities`; no other medium-risk capability
  is affected and high-risk ones can never be listed.

### Known limitations

- **Opening the browser wakes the owner's other tabs, and YouTube tabs among
  them start playing.** Playwright attaches to every page in the browser — ten
  of ten, measured — because it is built to drive a browser it owns, and
  ADR-0019 Option D points it at one in daily use. There is no option to narrow
  the attach, so this cannot be fixed above Playwright. The replacement is
  spiked and proven (`tools/browser-lab/test_single_tab_cdp.py`: one tab over
  raw CDP, three decoy videos left untouched) and deferred by the owner rather
  than allowed to hold up the phase. Search and play work correctly meanwhile.

### Fixed

- **"It was closed successfully" was not recognised as a claim that anything
  had been closed.** The check knew *"has been closed"* and *"is now closed"*
  and not the plain past passive, and knew *"successfully closed"* but not
  *"closed successfully"* — so the same sentence was hedged or waved through
  depending on how the model happened to phrase it. Both spellings are covered
  now. The bare present state, "MS Edge is closed", deliberately still is not:
  that is what a window listing legitimately reports, and hedging the answer to
  "what's open?" would teach the reader to skip the hedge.
- **The test suite spoke out loud and loaded the speech models to do it.** Three
  UI tests simulated a spoken command, which is answered aloud by design, and
  asserted on something else — so they ran all the way through Kokoro to the
  sound card, pulling torch into memory with it. No UI test opens the speakers
  now, enforced once for all of them rather than fixture by fixture.
- **A reply could claim an action was done on the strength of an unrelated
  listing.** Asked to close Microsoft Edge, Jarvis called `window.list`, saw
  Edge in the results, and answered "The MS Edge window has been closed
  successfully" — twice, marked *confirmed by a tool*, with Edge still open and
  no close tool ever called. The check that exists to stop exactly this asks
  whether any tool result was verified, and is sound only because read-only
  tools report *nothing to verify*; `window.list` declared itself read-only and
  reported *verified*, so verifying that it had listed some windows was read as
  licence to claim a window had been closed. A tool that changes nothing now has
  nothing to verify, enforced where every action passes through rather than
  tool by tool.
- **The model could describe an action instead of performing it.** Each round of
  tool calls now ends with a plain record of what changed, and in particular of
  what did not: individual tool results are each accurate and none of them can
  report an absence, which is the gap the false claim grew in.
- **Closing an application could report success while it was still open.**
  Closing Microsoft Edge with a tab that asks before leaving said *"Microsoft
  Edge has been closed"* — verified — with Edge still on screen. The check asked
  whether the window was still in the window list, but that list answers *would
  a person call this open*, and deliberately leaves out the invisible, the
  untitled and the cloaked; Chromium hides its window while it asks you to
  confirm, so it left the list while entirely alive. Closing now asks Windows
  whether the window still exists, which is a different question from whether it
  is still on screen. A window that exists but has gone off screen is reported
  as still running and possibly asking you something — never as closed, and
  never as "still open with nothing asking", because Chromium draws that prompt
  inside the page where nothing outside can see it.
- **Speech models reached the network on every spoken reply.** Kokoro loads its
  voice files through `huggingface_hub`, which revalidates cached files against
  the Hub, and it resolves voices at synthesis time — so a fully downloaded,
  local voice still produced a request to huggingface.co each time Jarvis spoke.
  Speech-to-text did the same once per load. Loading weights from disk alone is
  now the default in every network mode (`storage.speech_models_local_only`);
  the network is for downloading a model that is missing, never for confirming
  one already present.
- **The model store setting had never been applied.** `storage.huggingface_home`
  has named a directory inside the Jarvis data folder since Phase 1 and nothing
  read it, so the speech libraries used their own cache under the user profile.
  It is applied now. An `HF_HOME` you set yourself still wins.
- **The offline switch for speech models was read too late to work.**
  `huggingface_hub` captures it when the library is imported rather than when a
  model loads, so applying it afterwards changed nothing — and the test asserted
  only that the environment variable was set, which it always was. The library
  is now told directly, and the test checks what the library believes.
- **"Bring this window to the front" reported success without checking.** It
  confirmed only that the window was no longer minimised — which it usually was
  not — while Windows routinely refuses `SetForegroundWindow` from a process
  that does not already own the foreground. It now asks Windows which window
  actually has it, so an activate that did nothing is reported as unverified.
  The same shape as a launch reporting success because the browser was already
  running: a check that cannot tell "my effect happened" from "something
  unrelated was already true".
- **A turn that ran out of steps reported failure for actions that had already
  succeeded.** "Move WhatsApp to the left half" moved the window and then said
  *"stopped after 4 rounds of tool calls… nothing further was run"*, which reads
  as the action having failed. The bound stays — PRD FR-123 requires one — but
  the report now names what completed before saying it stopped, and collapses
  identical repeats, since a model retrying the same call is usually why the
  limit was reached. The limit itself is raised from 4 to 8: arranging two
  windows needs a listing, two arranges and a round to answer in, and four left
  no room for that.
- **Window listings read out executable names and full titles.** Each window now
  carries a plain application name — "WhatsApp" rather than `WhatsApp.Root.exe`,
  "File Explorer" rather than `explorer.exe` — and applications that merely host
  something else are named by their window instead. The executable is still what
  matching keys on; it is no longer what gets said.
- **Jarvis narrated commands that had already worked.** A finished action is
  self-evidencing, and the reply policy said so — but it read the reply for a
  question mark *before* applying that rule, and the model ends nearly every
  completed action with an offer ("Want me to check system status?"). One
  question mark was enough to turn "opened it" into four seconds of narration
  about a window already on screen. A question now earns speech only when no
  tool ran to answer it with, so a real clarification is still spoken and a
  conversational flourish is not.
- **"Open YouTube and search for X" opened YouTube and then could not search
  it.** Opening YouTube launched Brave without an automation port, which is
  precisely what stopped the search that followed — so Jarvis broke its own next
  step and then asked you to close a browser it had opened itself, 56 seconds
  earlier. It now restarts the browser instead of asking you to, and the tool
  descriptions steer a request that says what to do *after* opening straight to
  the tool that does the whole job.
- **"Allow for this task" was discarded every time you chose it.** The dialog
  offered it, the engine rejected it (`scope 'task' requires a task_id`) because
  only scheduled tasks carried an id and a spoken request did not — so the
  approval was silently downgraded to single use and you were asked again on the
  next sentence, four times in seven minutes on 2026-08-05. A conversation turn
  now carries its own task id, so one approval covers everything that request
  needs. A test walks the offered scopes and grants each one, so the dialog and
  the engine cannot drift apart again.
- **Closing a browser tab broke every later request** with "Target page, context
  or browser has been closed". Liveness was checked on the *browser*, which was
  fine; the single cached tab was what had died, and nothing looked at it. A
  closed tab is now replaced with a new one, and a live tab is still reused so
  "play the second video" lands on the page the search just read.
- **The tab Jarvis opened came back in light mode** among a window of dark ones,
  because Playwright emulates `prefers-color-scheme: light` on pages it creates.
  That emulation is now switched off.
- **Jarvis narrated actions it had not taken** — "Now searching for best
  monitors" while nothing had been searched, carrying the label "confirmed by a
  tool" because an unrelated tool had verified something else. Nothing is ever
  under way when Jarvis speaks: a turn runs its tools to completion first, so an
  action described as in progress is false either way, and is now rewritten to
  say what actually ran.
- **Searching YouTube stopped working once automation moved to the owner's own
  Brave profile.** A browser that is already running cannot be given an
  automation port — `--remote-debugging-port` only applies when Chromium starts,
  and a second `brave.exe` hands its command line to the running instance and
  exits. Automation previously drove a dedicated profile that was rarely already
  open, so this case was rare; pointing it at a profile the owner uses all day
  made it the normal case. Jarvis now checks before launching, so it answers in
  about a second instead of waiting 20s for a port that cannot appear, and says
  which two things actually resolve it.
- **Restarting Jarvis no longer leaves browser automation dead until Brave is
  closed too.** A browser Jarvis started earlier is re-attached by recalling the
  port Chromium records in its own `DevToolsActivePort` file, confirmed live
  before it is trusted, since that file outlives a crash.
- **Quitting Jarvis no longer closes a browser it did not open.** Teardown always
  detaches, but only closes browsers Jarvis started itself.

### Security

- **Browser automation may now hold a standing grant, which is a real reduction
  in control and is recorded as one** (ADR-0032, `THREAT_MODEL.md`). Combined
  with ADR-0019's decision to drive the owner's own signed-in profile, an action
  a page induces runs as the signed-in user with no per-action confirmation. The
  defences that were already load-bearing become more so: results are selected by
  position and never by text, page content is quoted as untrusted, and an
  anti-bot challenge stops the session. Taken knowingly by the person whose
  accounts are at stake, after the trade-off was put in writing.
- **All browser work now runs on one owned thread.** Playwright's synchronous API
  is bound to the thread that created it, and the tool executor has four workers
  and abandons the thread — not the work — when a tool times out. Every recorded
  session ended with `greenlet.error: Cannot switch to a different thread` raised
  from the GUI thread during teardown, which means the browser was *not* being
  closed and the debugging port was left open. Teardown is a security control
  under ADR-0031, so a teardown that always raised was the control not running.
- **A browser could be left listening on a debugging port with Jarvis gone.**
  When a tool exceeds its timeout the invoker abandons the *future*, not the
  thread; an attach that completed afterwards was stored in a workspace that had
  already shut down, so nothing ever closed it. Observed on 2026-08-05, six
  seconds after the application exited. A session that finishes opening into a
  closed workspace is now closed immediately. ADR-0031 treats that teardown as a
  security control rather than tidiness, which makes this a leak of the control
  itself.
- **A web page could break out of the wrapper that quotes it.** Content observed
  from outside — pages, filenames, documents — is enclosed in delimiters that
  tell the model it is data and authorises nothing. Those delimiters are fixed
  strings published in the source, and the content was embedded verbatim, so a
  page containing the closing delimiter ended the quoted region early and
  anything it wrote after that point appeared to the model as trusted context.
  Delimiters in observed content are now escaped, and kept visible rather than
  stripped, so an attempt to break out shows up in the audit log instead of
  silently disappearing. Found by the test written for it, before any code in
  this product could fetch a page.
- **Observed content now has one shape and no trusted variant.** Everything read
  from outside becomes an `Observation`, which cannot express a capability, a
  grant, a risk level or a tool id, and which reaches the model through a single
  constructor that marks it untrusted with no way to override.
- **Choosing "the second video" is now a position, not a title.** Actions on
  observed lists resolve by ordinal, and there is no lookup by text at all, so a
  page cannot rename itself into redirecting an action. This is the control that
  does not depend on the model cooperating; the delimiters are defence in depth.

### Changed

- **Jarvis no longer claims it verified an application launch when it did not.**
  Opening an application whose process was *already running* — most often Brave,
  which almost everything opens through — now reports **unverified** rather than
  success, and says why. This will read as a regression and is the opposite: the
  old behaviour reported a confirmed success while observing nothing about its own
  effect, which is how "Open YouTube Music" recorded `succeeded / verified` every
  time it opened a browser tab instead of the app. Confirming these launches
  properly needs to observe a *window*, which arrives with UI Automation later in
  Phase 2. Until then Jarvis says it does not know, which by design does not
  satisfy a task's success criteria (FR-048, AT-018).

## [0.2.0.dev0] — 2026-08-04 — Phase 1: voice-first local assistant

**Phase 1 is closed.** All five PRD §21 exit criteria were met and confirmed by
user acceptance testing on 2026-08-04. What it did *not* close is listed under
Known limitations below and carried into Phase 2 in `docs/BACKLOG.md` §4.6 —
none of it silently.

Jarvis can now hold a conversation, hear you, speak back, and open the handful
of applications and websites you have approved. It still performs **no other
desktop or browser automation** — no clicking, typing, reading the screen or
touching your files.

### Added

- **Approval dialog.** Consequential actions can finally be authorised, which
  unblocks every capability beyond the two self-inspection grants. The prompt
  is anchored to the tray and does **not** take focus, so being asked never
  disturbs what you are doing. An unanswered request expires and is recorded as
  denied — silence is never taken as consent. Denials can be remembered per
  application, site or folder, and a waiting request is reachable from the tray
  and the Permissions screen without a mouse.
- **Local conversation.** A Conversation screen that talks to the local model.
  Every reply says where it came from — the model itself, a retrieved fact, an
  inference, a confirmed tool result, or an admission of uncertainty — and
  Jarvis will not tell you something was done unless a tool confirmed it.
- **Conversation history, with real controls.** History can be turned off
  globally or for one conversation, and deleted. A **private session** writes
  nothing to disk at all rather than writing and cleaning up afterwards.
- **A voice.** Kokoro `bm_george` for speech, faster-whisper `small` for
  listening, both running locally. Anything that looks like a password, key,
  card number or verification code is replaced with a description of what it
  was *before* Jarvis says it out loud.
- **Push-to-talk on F9** and an emergency-stop hotkey on `Ctrl+Alt+Pause`, both
  configurable. A combination another application already owns is reported as
  unavailable rather than silently doing nothing.
- **A Voice screen** showing which components are installed, which microphone is
  selected, and each voice's licence. It states the wake phrase literally and
  says plainly that single-word "Jarvis" is not available in this build.
- **Protected secret storage** using the Windows Data Protection API.
- **Start Jarvis at sign-in**, as a per-user setting that never needs
  administrator rights.
- **`--require-healthy`** for `--check`, when a caller needs an unreachable
  model runtime to be a failure rather than an honest report.
- **Opening approved applications and websites.** Brave, YouTube, YouTube Music,
  Xbox and Sea of Thieves, from a fixed catalogue. Jarvis chooses *which
  approved entry*, never which program — and it says an application opened only
  after it has seen the process running.
- **Media and volume keys**, and **desktop notifications**.
- **Jarvis speaks out loud.** Synthesis previously produced audio that nothing
  ever played. Speech is now audible, can be interrupted mid-sentence, and
  Jarvis reports how long it actually spoke for.
- **A one-time wake-word model installation**, `--install-wake-model`, which
  says exactly where the files go, is safe to repeat, and reports the model as
  installed only once the detector genuinely starts. The model is never bundled
  and is licensed for **non-commercial use only**.
- **The Voice screen's controls now work**: choosing a microphone, testing it
  with a live level meter, measuring the room, and previewing a voice. The list
  now names each device's audio system, so the same microphone appearing three
  times is finally something you can choose between.
- **A recording indicator.** The tray and the Voice screen both show whenever
  the microphone is open.
- **A listening switch.** Turn on "Start listening" and Jarvis waits for
  "Hey Jarvis", then transcribes what follows and answers it. It says plainly
  that the wake model is a shared one that has not been tuned to your voice.
- **Push-to-talk is now optional** and shows its key, so you can turn it off and
  use the wake phrase instead.
- **The Voice screen shows what it heard**, with a confidence figure, so a
  misheard word looks like a mishearing rather than a bad answer.
- **Your name.** Set it on the Conversation screen and it replaces "You" in the
  transcript, survives restarts, and is given to the model so Jarvis can address
  you properly. Leave it empty and nothing changes.
- **Audio cues.** Short tones for "I heard the wake phrase and I am recording",
  "I am working on it", and "that is done" — so Jarvis is legible from the tray
  without its window on screen. Turn them off with `audio.cues_enabled`.
- **`web.search`.** Searching by words rather than by URL, with Google (the
  default), DuckDuckGo or YouTube. Jarvis builds the address, so a query with
  spaces, symbols or a colon in it works. It says outright that it cannot read
  the results.
- **Stop speaking**, in the tray menu. It interrupts the sentence and does
  nothing else: no task is cancelled and no resource lock is released.
- **`audio.speak_replies`** — `always`, `when_useful` (the default) or `never`.

### Changed

- Deleted conversation history is now genuinely erased from the database file.
  Previously the rows were unlinked but their contents stayed readable in freed
  pages.
- The Home screen reports the voice stack, the secret store and the conversation
  engine, and no longer describes the build as Phase 0.
- **Push-to-talk is press-to-start, not hold-to-talk.** Windows reports only the
  key press for a global hotkey, so holding F9 never worked. Press it, speak,
  and it stops on its own when you stop talking.
- In **offline mode** the speech models are pinned to their local cache. Loading
  a voice or transcription model previously contacted the Hugging Face Hub,
  which was a network request from a component presented as entirely local.
- **Speaking to Jarvis no longer drags the window in front of what you were
  doing.** Speaking is meant to be the way to use Jarvis *without* the window;
  taking over the screen because someone spoke is the intrusion the non-modal
  approval panel exists to avoid.
- **A spoken question is now answered out loud**, and only when the answer is
  worth hearing. Questions are answered, problems and follow-up questions are
  always spoken, and an instruction that simply worked — "open Brave" — gets a
  short cue instead of a sentence about a window you can already see. A *typed*
  request is never answered aloud, whatever the setting says.
- **Emoji, formatting and web addresses are no longer read out.** The
  phonemiser expands every character to its Unicode name, so "Opening Brave 🦁"
  was spoken as "Opening Brave lion face", and a link was spelled out in full.
  The written transcript still shows every character; only the spoken copy is
  stripped, and a code block is announced rather than recited.
- **"Open YouTube Music" opens the app you installed**, not another browser tab.
- **Emergency stop now stops Jarvis talking**, from the tray, the Home screen
  and the hotkey. It cancelled tasks and released locks while continuing to
  speak over the silence it had just created.

### Fixed

- **Typing a message produced no reply at all.** The Conversation screen sent
  the message onto a worker that had already been destroyed, so nothing was ever
  asked of the model — and because nothing failed, nothing was reported.
- **"Thinking…" silently reverted to "Ready"** part-way through an answer.
- **Quitting while Jarvis was answering could kill the process outright.**
- **No button on the Voice screen did anything.** They were enabled and
  connected to nothing. Push-to-talk reported that the voice stack was
  unavailable while it was fully installed and working.
- **Jarvis claimed it had spoken when it had not.** `voice.speak` reported a
  confirmed success on the strength of having produced audio, while nothing
  played it. It now fails plainly if no sound reached the output device.
- **The emergency-stop hotkey never worked.** The key registered and the press
  was then dropped on its way to the application. It also moved off `Pause`,
  which many keyboards do not have, to **`Ctrl+Alt+End`**.
- **Push-to-talk never worked**, for the same reason. F9 was never the problem.
- **Desktop notifications from tools never appeared**, and the tool reported
  showing them anyway.
- **The recording indicator never lit**, so the microphone could open with
  nothing on screen saying so.
- **No microphone could be opened at all** on a machine whose default input is
  an MME device — which is most of them. Jarvis asked every device for settings
  only one kind of device accepts.
- **Asking Jarvis to say something failed outright** with an internal error: it
  reserved a lock by a name that does not exist.
- **Some questions came back completely blank**, under a confident source
  label, which is indistinguishable from being ignored. When the model returns
  nothing, Jarvis now says so — and says what its tools did, if they did
  anything — rather than rendering the silence as an answer.
- **Interrupting Jarvis mid-sentence never actually worked.** Three separate
  causes: the wake threshold during playback demanded a score of 0.96, which is
  effectively unreachable; the self-echo check compared the microphone's level
  against the volume of Jarvis's own audio data, which are not the same kind of
  measurement, and rejected real interruptions almost every time; and emergency
  stop did not stop speech at all. The Voice screen now also says plainly that
  speaking over Jarvis cannot interrupt it while the microphone is closed.
- **Searching the web produced a broken address.** The model was building and
  encoding search URLs itself; one came back from Google as an error. Jarvis
  builds them now.
- **"Open Steam" refused to open Steam**, because the entry insisted on a game
  to launch. With no game named, it opens the client.
- **Being asked to open an unapproved application produced invented
  instructions** pointing at a settings screen that does not exist.
- **A cue could leave an audio stream open** after the sound had finished, which
  in the worst case corrupted memory as the process exited.

### Known limitations

- **Wake-word detection is installed but always-listening stays off.** The
  pretrained "Hey Jarvis" model is measured and working; per-user enrolment is
  not built, and ADR-0016 does not permit always-listening without it.
  Single-word "Jarvis" is not detected — measured 0 of 4 attempts.
- **You cannot interrupt Jarvis by speaking.** Acceptance testing found voice
  interruption did not work on real hardware even after the thresholds that
  made it unreachable were repaired, so Jarvis ships in **half duplex**: wake
  detection pauses while it speaks, and the Voice screen says so rather than
  claiming otherwise. `Ctrl+Alt+End` and the tray's **Stop speaking** stop it
  immediately and always. `audio.duplex_mode: full` restores the other
  behaviour for anyone who wants to measure it.
- **"Open YouTube Music" still opens a browser tab** rather than the installed
  web app, despite launching by app id. Under investigation.
- **Jarvis has no clock.** It can only answer "what time is it?" from the model,
  which does not know. There is no time tool yet.
- **Only catalogued applications can be opened.** Naming one that is not in the
  catalogue is refused, and there is no in-application way to add one.
- **Jarvis does not speak while it works**, only when it finishes.
- **"Start at sign-in" appears as `pythonw.exe`** in Windows' startup list.
  Correct for a source checkout — there is no packaged executable to name until
  Phase 6.

---

## [0.1.0.dev0] — 2026-08-01 — Phase 0: foundation and safety architecture

The foundation every later capability has to pass through. **No
computer-control features**: no audio, no automation, no browser, no filesystem
tools, no screen capture, no clipboard.

### Documentation

- `ARCHITECTURE.md` — process and thread model, layering, the six-step control
  flow, extension points, and an honest statement of what exists today.
- `SECURITY.md` — security policy: trust boundaries, capability risk classes,
  the prohibited list and its enforcement, permission model, elevation policy,
  secrets, audit requirements, filesystem safety, supply chain.
- `THREAT_MODEL.md` — STRIDE plus LLM-agent-specific analysis; 81 catalogued
  threats, trust boundaries, actors, phase-gated mitigations, and the residual
  risks accepted for Phase 0.
- `DATA_MODEL.md` — the schema as built, entity definitions, retention,
  migration policy and export rules.
- `docs/BACKLOG.md` — phased implementation backlog for Phases 0–6 with
  requirement and acceptance-test coverage matrices.
- `docs/decisions/ADR-0002` … `ADR-0026` — the nine Phase 0 architectural
  decisions and the sixteen open decisions from PRD section 25.
- `README.md` — what this is, what it is not, and how to run it.

### Added — configuration and storage

- Layered configuration: shipped defaults, user overrides, environment
  overrides, validated into one frozen pydantic tree with `extra="forbid"`.
  Only the difference from defaults is persisted, and writes are atomic.
- `VaultPaths`: single point of Windows environment-variable expansion; the
  whole vault relocates via `--data-dir` or `JARVIS_DATA_DIR`.
- SQLite vault with WAL, foreign keys, per-thread connections and versioned
  forward-only migrations. A database newer than the running build is a hard
  startup failure.

### Added — core safety machinery

- Typed event bus: frozen pydantic events, subclass matching, thread-safe
  publish, isolated handlers.
- Audit log: append-only JSONL plus a SQLite search index, with the PRD section
  11.5 field set. Redaction happens on the way in, by field name and by value
  shape; clipboard, transcript and document text are described, never stored.
- Capability catalogue: PRD section 11.1 risk classification expressed as data.
- Permission engine: unknown denied, prohibited denied unconditionally, high
  risk always asks, scoped grants (once, session, task, application, folder,
  always) with expiry and revocation. `always` is low-risk only; high risk can
  never hold a standing allow.
- Tool contract implementing PRD section 13.2 in full, including reversibility
  and rollback metadata.
- Prohibited-capability guard: denylist by exact identity and by name pattern.
- Tool invoker: the single choke point implementing PRD section 13.4's six
  checks, with bounded timeouts, bounded retries, declared failure codes, and a
  `succeeded` that requires verification.

### Added — tasks

- Ten-state task machine with an explicit, validated transition table; terminal
  states have no outgoing edges.
- Durable task store: tasks, transition history, checkpoints, evidence, task
  trees with cascade delete.
- Resource locks: exclusive, persisted, owner-attributed, all-or-nothing over a
  sorted set, with stale reclamation after a crash.
- Scheduler: queue, lock arbitration, bounded concurrency, cooperative pause
  and cancel, bounded retries. Tasks blocked on a lock stay queued with a
  visible reason.
- Crash recovery: interrupted tasks are paused and marked recovered, never
  auto-resumed; stale locks are released; everything is audited.

### Added — runtime and shell

- `JarvisCore`: composition root with defined startup and shutdown ordering,
  importing no GUI code.
- Emergency stop: cancels tasks, releases locks, stops workers and reports
  exactly what was stopped, leaving the application running.
- Single-instance guard: Windows named mutex, with a lock-file fallback that
  reclaims a file left by a dead process.
- Worker supervisor with cooperative stop; the periodic health check runs off
  the UI thread.
- Ollama health check: loopback-only, offline-mode aware, explicitly timed out.
- `system.health`: the one registered tool, read-only, routed through the full
  invoker pipeline.
- PySide6 tray with the seven PRD section 9.1 states, distinguished by shape and
  accessible text as well as colour, and the PRD section 9.2 menu. Unavailable
  entries are shown disabled and name the phase that delivers them.
- Main window with all fifteen PRD section 9.3 navigation areas; seven are live
  against real data and the rest state plainly that they are not implemented.
- Qt event bridge marshalling domain events onto the GUI thread.
- CLI: `--check`, `--data-dir`, `--log-level`, `--allow-multiple-instances`.

### Added — tests and CI

- 250+ tests across unit, security, integration, UI (offscreen Qt) and
  acceptance suites. Every test gets an isolated vault; none requires Ollama, a
  microphone, a GPU or the network.
- `tests/security/test_no_shell.py`: AST scan of the whole package for
  process-creation and dynamic-evaluation primitives; the build fails if one
  appears. Includes a test that the scanner itself detects violations.
- `tests/security/test_layering.py`: only the presentation layer may import Qt,
  and no module may import a higher layer.
- `tests/acceptance/`: one test per Phase 0 exit criterion from PRD section 21.
- GitHub Actions: tests on Windows and Linux across Python 3.11 and 3.12, a
  separate security-invariants job, and advisory dependency and licence review.

### Security

- No shell, Command Prompt, PowerShell, WSL or arbitrary-code execution exists
  anywhere in the runtime, enforced in three layers (ADR-0003).
- The application runs without administrator rights; nothing requests
  elevation, and a test enforces it.
- The local model endpoint must resolve to loopback or the adapter refuses and
  audits the refusal.
- Offline mode is enforced at the adapter boundary, not by caller discipline.
- The Phase 0 approval port denies by default: with no approval interface, a
  capability requiring approval simply cannot run.

### Known limitations

- No approval dialog exists yet, so only capabilities with a standing grant can
  run. Two self-inspection capabilities receive a visible, revocable bootstrap
  grant at first start.
- In-process isolation is not a security boundary (ADR-0004).
- A timed-out tool is abandoned, not killed; Python cannot forcibly stop a
  thread. The tool's own timeout remains the primary defence.
- Secret storage is deferred to Phase 1, when the first secret exists
  (ADR-0008).

[Unreleased]: https://example.invalid/compare/v0.1.0.dev0...HEAD
[0.1.0.dev0]: https://example.invalid/releases/tag/v0.1.0.dev0
