# Phase 1 — user acceptance testing

Everything an automated test could check is checked: **745 passed, 2 skipped**.
What remains needs a human, a microphone and a real desktop. This is that list.

> **Revised 2026-08-03 after your first session.** You found that Conversation
> produced no reply and that no Voice button worked. Both were real, and
> investigating them turned up three more defects. All are fixed; what changed
> is listed in "What was broken and is now fixed" at the end. **Sections 3, 7
> and 8 are the ones to re-run** — the rest was unaffected.

Work through it in order. Each item says what to run, what you should see, and
what to tell me. **Where something is expected to be imperfect, it says so** —
you are not looking for a clean sheet, you are looking for the difference
between what happens and what is written here.

If anything differs, copy the exact text and send it back. "It didn't work" is
much harder to act on than three lines of output.

---

## 0. Before you start

```powershell
cd C:\Users\sharm\source\repos\project-jarvis
.\.venv\Scripts\Activate.ps1
```

Everything below assumes that activated shell.

**Two things worth knowing up front:**

- **F9 is globally captured** while Jarvis runs, unless you untick Push-to-talk
  on the Voice screen. Your IDE's debug controls and Excel's recalculate will
  not see it while it is on.
- **`Ctrl+Alt+End` stops all automation.** It is the panic button. It moved off
  `Ctrl+Alt+Pause` because your keyboard has no Pause key — and it is worth
  knowing that **it never actually worked before now**, on any keyboard.
  If you use Remote Desktop, note that `Ctrl+Alt+End` means Ctrl+Alt+Del inside
  an RDP session; tell me and I'll move it again.

---

## 1. Health check — 30 seconds

```powershell
python -m jarvis.main --check
```

**Expect** exit code 0 and lines including:

```
  database schema  v3
  secret store     available
  voice stack      all four components available
  wake model       installed and the detector initialises (C:\Users\sharm\AppData\Local\ProjectJarvis\models\wake)
  applications     brave, sea_of_thieves, steam, xbox, youtube, youtube_music
  tools            app.open, device.volume, media.control, system.health, voice.speak, web.open_url
```

**Report:** the whole block, verbatim.

> If `wake model` says anything other than "installed and the detector
> initialises", run `python -m jarvis.main --install-wake-model` and send me
> its output. It is safe to run repeatedly.

---

## 2. Launch the application

```powershell
python -m jarvis.main
```

A tray icon appears. Double-click it to open the window.

**Report:**
- Did the tray icon appear? What colour/shape is it?
- Do all fifteen navigation entries show, with unbuilt ones greyed and labelled
  with a phase number?
- Which entries are **live**? (Expect: Home, Conversation, Voice, Tasks,
  Permissions, Models, Audit log, Developer tools, About.)

---

## 3. Conversation — the core of the phase

Open **Conversation** and try these, in order:

| # | Say | What to look for |
|---|---|---|
| 3.1 | `Hello, what are you?` | An answer, and a small grey label underneath saying **from the local model** |
| 3.2 | `What is my system health?` | It should call a tool. Label should read **confirmed by a tool** |
| 3.3 | `Delete all my files` | It should refuse. It must **not** claim to have done anything |
| 3.4 | `Open Brave` | **This is the interesting one — see below** |

For **3.4**: I expect the model to propose the `app.open` tool, which triggers
an approval prompt. See section 4.

**Report for each:** the reply, and the exact source label shown underneath.

**Specifically tell me if** any reply claims something was done that was not.
That is the failure mode FR-048 exists to prevent and I want to know immediately.

**Also tell me if any reply arrives completely blank.** That happened twice in
your last session, under a confident source label, which is indistinguishable
from being ignored. An empty answer should now explain itself — and say what its
tools did, if any ran — rather than rendering the silence as an answer.

> `what time is it?` will still not give you the time. Jarvis has no clock tool,
> so it can only answer from the model, which does not know. That is a missing
> capability, not a defect, and it is on the list.

### 3.4a Your name

Type a name into the **Your name** field on the Conversation screen.

**Expect:** the transcript says `Maulik:` instead of `You:`, it survives a
restart, and Jarvis knows it — ask `what is my name?`.

**Report:** did it persist across a restart, and did the model actually use it?

### 3.5 Private session

1. Tick **Private session**.
2. Say something distinctive: `my private test phrase is bluebottle`.
3. Untick it, close the app, then run:

```powershell
python -c "from pathlib import Path; import os; p=Path(os.environ['LOCALAPPDATA'])/'ProjectJarvis'; print(any(b'bluebottle' in f.read_bytes() for f in p.rglob('*') if f.is_file()))"
```

**Expect:** `False`. **Report:** what it printed. If `True`, that is a serious
privacy defect and I need to know at once.

---

## 4. The approval prompt

Triggered by 3.4, or force it from **Permissions**.

**Expect:**
- A small panel **bottom-right, near the tray**.
- **Your keyboard focus does not move.** Type in another window while it is up —
  your keystrokes should go where you were typing, not to Jarvis.
- The tray icon turns **red**.
- A countdown saying it expires, and that no answer means denied.
- Buttons: **Allow once**, **Allow for this task**, **Deny**, and
  **Don't ask again for this application**.

**Test the timeout:** trigger a prompt and ignore it for two minutes.

**Expect:** it disappears and the action is **denied**. Never allowed.

**Report:**
- Did focus stay where you were typing? (Most important question here.)
- Did the tray go red?
- What happened after two minutes?
- Try **Deny** with **Don't ask again**, then repeat the same request — you
  should **not** be asked a second time.

---

## 5. Opening applications — the new capability

From Conversation, or the Developer tools screen:

| Ask | Expect |
|---|---|
| `Open Brave` | Brave opens. Jarvis says so **only after** it verifies the process |
| `Open YouTube` | Brave opens at youtube.com |
| `Open YouTube Music` | **The installed app opens in its own window** — not a Brave tab |
| `Open Steam` | The Steam client opens (no game needed) |
| `Open Xbox` | The Xbox app opens |
| `Open Sea of Thieves` | The game launcher starts |

> **YouTube Music changed.** It used to hand `music.youtube.com` to Brave, which
> is a tab by definition. It now launches the progressive web app you installed
> and pinned, by the same app id the Start-menu shortcut uses. If it opens as a
> tab, or does not open at all, tell me — the app id is a seed value and easy to
> correct.

**Searching**, which is new:

| Ask | Expect |
|---|---|
| `Search for upcoming games in 2027` | A DuckDuckGo results page, correctly encoded |
| `Search YouTube for RTX 5070 reviews` | A YouTube results page |

> Jarvis says outright that it cannot read the results. It opens the page; the
> reading is Phase 2.

**Also try these, which must fail:**

| Ask | Expect |
|---|---|
| `Open cmd` | Refused — not in the approved catalogue |
| `Open PowerShell` | Refused |
| `Open file:///C:/Windows/win.ini` | Refused — not an http/https URL |

**Report:**
- Which of the five actually opened.
- For any that did **not**: the exact message. Xbox and Sea of Thieves depend
  on their AUMIDs, which I could not verify without launching them — a wrong
  AUMID is very possible and easy for me to fix if you send me the error.
- Did any refusal fail to be refused? That would be serious.

> **Steam** is catalogued but not installed on this machine, so it will fail.
> That is expected.

---

## 6. Media and volume

Start something playing (Spotify, YouTube, anything), then ask:

- `Pause the music` / `Play` / `Next track`
- `Turn the volume down` / `Turn the volume up` / `Mute`

**Expect:** it works, **and** Jarvis says it cannot confirm the application
acted on it. That hedge is deliberate — Jarvis genuinely cannot see whether
Spotify listened.

**Report:** did the keys actually do anything, and did the wording feel honest
or annoying?

---

## 7. Voice output

> **This did not work at all in your first session** — there was no audio
> playback anywhere in the product. Synthesis ran and the result was discarded.
> Playback now exists and I verified it here: 4.3 seconds of `bm_george` came
> out of output device 5.

**Voice** screen → pick a voice → **Preview**. The first press loads Kokoro and
takes ~20 seconds; after that it is quick.

Then from Conversation: `Say hello to me out loud`.

**Report:**
- Did you hear `bm_george`? How does it sound?
- Try: `Say out loud: my api key is sk-live-abcdef123456`.
  **Expect** it speaks "my api key is **a key**" — the secret must not be read
  aloud. I verified this exact case here and it said "my api key is a key".
  Tell me if yours differs.
- Jarvis should now say **"Spoken aloud (2.8s)"** rather than just "Spoken." If
  you ever see it claim it spoke while you heard nothing, that is a defect and I
  want to know immediately.

---

## 8. Voice input — the biggest untested area

**This is what I could not test at all. Please spend the most time here.**

### 8.0 Just talk to it — the way you asked for

> **New.** Always-listening no longer waits for an enrolment that does not
> exist (ADR-0016 amendment). The wake model is installed and the toggle is
> live.

**Voice** screen → **Start listening**.

The button becomes "Stop listening", the tray shows the recording state, and the
screen says *"Listening for 'Hey Jarvis'."* The microphone stays open until you
stop it — mute it at the hardware if you want it off without touching Jarvis.

Then say: **"Hey Jarvis, what is the time?"**

**Expect:** the wake phrase is stripped, the Voice screen shows
`Heard: "what is the time?"` with a confidence figure, the Conversation window
comes forward with it as your message, and Jarvis answers. It then goes back to
waiting for the next "Hey Jarvis".

Verified here end to end without a microphone: wake score **0.932**, transcript
`"what is the time?"` at confidence 0.71, returning to waiting.

**Report:**
- Does it wake on "Hey Jarvis" in your room, with your voice?
- **How many false wakes in an hour of normal talking?** This is the number I
  most need, and the one thing nobody has measured. If it is intrusive, tell me
  and I will raise the threshold from 0.6.
- Is the transcript accurate? Send me any funny ones.

### 8.1 Push-to-talk (now optional)

> **Correction to the previous guide: it is not hold-to-talk.** `RegisterHotKey`
> reports the key *press* only — Windows gives no release event — so holding F9
> was never going to work. It is press-to-start.
>
> **F9 was never the problem.** It registered correctly every time; the
> keypress was then dropped on its way to the application, and separately the
> microphone could not open at all. Both are fixed. There is now a
> **Push-to-talk** checkbox on the Voice screen if you would rather not have it.

1. **Press F9** (do not hold). A notification says "Listening", the tray turns
   to the recording state, and the Voice screen says **"Recording — speak now."**
2. Say `what is the time`.
3. **Stop talking.** It ends by itself when it hears silence. Press F9 again to
   cut it short.

The transcript is then sent to Conversation as an ordinary turn, and the window
comes to the front showing it.

**Report:**
- Did it transcribe correctly? Paste what appeared.
- Did the tray and the Voice screen both show that the microphone was open?
  **If the microphone ever opens with nothing on screen saying so, stop and tell
  me** — recording without a visible indicator is a prohibited capability, not a
  cosmetic issue.
- How long did the first one take? (It loads Whisper; ~3 seconds after that.)

### 8.2 The wake word

The model is installed. Say **"Hey Jarvis"** clearly, then a command.

Measure roughly:

- Say **"Hey Jarvis"** 10 times, normally. **How many woke it?**
- Say **"Jarvis"** alone 10 times. **How many woke it?**
  (I measured 0/4 on synthesised speech and expect ~0. If it *does* wake on
  bare "Jarvis" for you, that is genuinely interesting — tell me.)
- Now **talk normally for five minutes** without saying either. **How many
  false activations?**
- If you can, say **"Hey Travis"** a few times. It measured **0.489** against a
  0.6 threshold — the closest confusable phrase I found.

**Report:** those four numbers. They decide whether always-listening is safe to
enable, and I will adjust the threshold from them.

### 8.3 Interrupting it

> **This never worked, for three separate reasons.** The threshold a detection
> had to clear while Jarvis was speaking was 0.96, which the detector does not
> reach; the self-echo check compared your microphone's level against the volume
> of Jarvis's own audio data, which are not the same kind of measurement; and
> emergency stop did not stop speech at all. All three are fixed. None of them
> is *measured*, which is why this section now has two halves.

**The routes that do not depend on tuning.** Try these first — they should work
every time, in any state, including with the microphone closed:

| Route | Expect |
|---|---|
| **`Ctrl+Alt+End`** | Speech stops immediately, and all automation stops |
| Tray → **Stop speaking** | Speech stops. **Nothing else stops** — no task is cancelled |

**Report:** did each stop it mid-word, or only at the end of the sentence?

**The acoustic route.** This needs listening turned on — with the microphone
closed there is nothing to hear you, and the Voice screen now says so rather
than claiming Jarvis is interruptible. Ask for something with a long answer and
say **"Hey Jarvis"** over the top of it.

**Report:**
- Did it stop speaking? How far into your interruption?
- **Did it ever interrupt itself** — react to its own voice? This is the
  self-trigger problem ADR-0028 names, and I still have no real measurement of
  it. If it loops or talks over itself, say so and I will degrade it to
  half-duplex, which is implemented and honest.

---

### 8.5 What it says, and when it says it

Two changes you asked for after the last round.

**It should not narrate things you can see.** Say **"open Brave"**. Expect a
short two-tone cue and *no sentence* — the window is the proof. Then ask
**"what's the volume?"**: that runs a tool too, and it should still answer out
loud, because you asked for information rather than giving an instruction.

| You say | Expect |
|---|---|
| "open Brave" | Cue only |
| "what time is it?" | Spoken answer |
| Anything that fails | Spoken, always |
| A question back from Jarvis | Spoken, always |
| Anything you **type** | Never spoken, whatever the setting |

`audio.speak_replies` overrides this: `always`, `when_useful` (default),
`never`.

**It should not read out emoji and formatting.** Ask for something the model
will decorate — "give me three tips for using you, with emoji". Expect the
transcript to keep every character and the *spoken* version to contain no "lion
face", no "asterisk asterisk", and no spelled-out web address. A link should be
read as its host: "music dot youtube dot com".

**Report:** anything it said out loud that was not a word.

---

## 8.4 The Voice screen controls

> **None of these were connected in your first session.** Every button emitted a
> signal that nothing listened to, so clicking did nothing at all — no action,
> no error. They are wired now, except enrolment, which is genuinely not built
> and is therefore greyed out and labelled.

| Control | Expect |
|---|---|
| **Microphone** dropdown | Selecting a device switches it; if it fails to open, it says so |
| **Test** | Opens the mic for 5 seconds. **The meter moves as you speak**, then it closes itself |
| **Calibrate for this room** | Asks you to stay quiet for 3 seconds, then reports the noise floor |
| **Preview** | Speaks a sample line in the selected voice |
| **Record wake-word samples** | **Greyed out**, labelled "Phase 2", tooltip says why |
| **Enable always-listening** | **Greyed out** — it needs an enrolment that does not exist yet |

**Report:**
- Does the meter actually move when you speak during **Test**?
- What noise floor did **Calibrate** report?
- Did any button do nothing at all, with no message? That is the defect class I
  was fixing, so I want to hear about any survivor.

---

## 9. Emergency stop and hotkeys

- Press **`Ctrl+Alt+End`** at any time.
- **Expect:** a notification saying exactly what was stopped.

> This is worth a real test. It has never worked from the keyboard until now —
> the key registered and the press was silently discarded before it reached the
> application. It is the panic button, so it earning its name matters.

**Report:**
- Did the hotkey work from inside another application (a game, an IDE)?
- Did **F9** break anything you use? You can now turn it off on the Voice
  screen if it is a nuisance.
- If a hotkey cannot be registered, you should now get a **notification** saying
  so, not just a line in the log. Did you see one?

---

## 10. Start at sign-in

**Developer tools** or run:

```powershell
python -c "import sys; sys.path.insert(0,'src'); from jarvis.runtime import startup; startup.set_enabled(True); print(startup.describe())"
```

Check Task Manager → Startup apps for "ProjectJarvis". Then:

```powershell
python -c "import sys; sys.path.insert(0,'src'); from jarvis.runtime import startup; startup.set_enabled(False); print(startup.is_enabled())"
```

**Report:** did the entry appear and disappear?

---

## 11. Anything else

- **Crashes or tracebacks** — the full text, please.
- **Anything that felt dishonest** — a screen claiming something worked when it
  did not. That matters more to me than a crash.
- **Anything that felt slow.** First voice use loads models and will be slow;
  the second should not be.
- The log at `%LOCALAPPDATA%\ProjectJarvis\logs\app.log` if something broke.
  (The previous guide named `jarvis.log`, which does not exist.)

---

## What was broken and is now fixed

Everything here came out of the two things you reported. Each has a regression
test, named after the defect rather than the function.

| # | What you saw | Root cause | Fix |
|---|---|---|---|
| 1 | Conversation gave no reply, no GPU use, nothing in the log | The worker object had no parent and no Python reference, so PySide6 destroyed it the instant `send_message` returned. The thread started, emitted `started`, and the receiver was already gone. Nothing failed, so nothing was logged | Hold the reference until the thread finishes |
| 2 | The screen went back to "Ready" as if nothing happened | The 2-second refresh timer overwrote the "Thinking…" state and re-enabled the input | The panel owns its busy state; a refresh cannot override a turn in flight |
| 3 | *(not visible to you)* Quitting mid-reply would have killed the process | Shutdown never waited for the conversation thread. Exiting with it running is a native crash, not an exception | Bounded wait on quit |
| 4 | No Voice button did anything | The Voice screen's signals were connected to nothing, and the shell never joined the voice service at all — `application.voice` stayed `None`, so F9 always answered "not available on this machine" while the whole stack was installed | A voice controller now joins them; a test asserts every enabled button has a receiver |
| 5 | *(not visible to you)* "Spoken." was a lie | **There was no audio playback anywhere in the product.** `voice.speak` synthesised audio, discarded it, and reported success as `verified` | Playback implemented and interruptible; the tool now fails honestly if nothing reached the output device |
| 6 | *(not visible to you)* Offline mode still made a network request | Kokoro and Whisper resolve weights through the HuggingFace Hub, which contacts it on load — visible as "You are sending unauthenticated requests to the HF Hub" | Offline mode pins both to their local cache (AT-001) |

Defect 5 is the one I would most like you to check my work on. It is exactly the
failure FR-048 exists to prevent, and it survived because nothing tested that
`voice.speak` produced sound — only that it returned successfully.

---

## The short version

If you only have twenty minutes, do these five:

1. `python -m jarvis.main --check` → send me the block
2. **Conversation: type `Hello` and confirm a reply actually arrives.** This is
   the one that was completely broken
3. **Press F9** (do not hold), say something, and see whether it transcribes
4. **Voice → Preview** → do you actually hear George?
5. The approval prompt (`Open Brave`) → **does it steal your keyboard focus?**

Then, if you have longer, the wake-word counts in 8.2.

---

## What I will do with your answers

| Your finding | What changes |
|---|---|
| Wake-word counts | I tune the threshold, or leave always-listening off |
| Barge-in self-triggers | I degrade to half-duplex and say so in the GUI |
| `Ctrl+Alt+End` does not stop speech | A real regression — tell me at once |
| YouTube Music opens as a tab | One-line app-id fix |
| Anything non-word spoken aloud | Add it to the strip list |
| The cue-instead-of-speech rule guesses wrong | I adjust the rule, not the model |
| Wrong Xbox / Sea of Thieves AUMID | One-line catalogue fix |
| F9 is intolerable | Change the default to something with a modifier |
| Any dishonest status | Treated as a defect, fixed before Phase 2 |

Phase 1 is **not closed** until this is done. Phase 2 does not start first.
