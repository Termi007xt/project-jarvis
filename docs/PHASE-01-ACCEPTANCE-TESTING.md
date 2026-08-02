# Phase 1 — user acceptance testing

Everything an automated test could check is checked: **698 passed, 2 skipped**.
What remains needs a human, a microphone and a real desktop. This is that list.

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

- **F9 is now globally captured** while Jarvis runs. Your IDE's debug controls
  and Excel's recalculate will not see it. That is expected, and it is why the
  key is configurable — tell me if it is intolerable.
- **`Ctrl+Alt+Pause` stops all automation.** It is the panic button. Nothing in
  this phase can do much damage, but use it if anything feels wrong.

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
| `Open YouTube Music` | Brave opens at music.youtube.com |
| `Open Xbox` | The Xbox app opens |
| `Open Sea of Thieves` | The game launcher starts |

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

**Voice** screen → pick a voice → **Preview**.

Then from Conversation: `Say hello to me out loud`.

**Report:**
- Did you hear `bm_george`? How does it sound?
- Try: `Say out loud: my api key is sk-live-abcdef123456`.
  **Expect** it speaks "my api key is **a key**" — the secret must not be read
  aloud. Tell me exactly what it said.

---

## 8. Voice input — the biggest untested area

**This is what I could not test at all. Please spend the most time here.**

### 8.1 Push-to-talk (the verified route)

Hold **F9**, say `what is the time`, release.

**Report:** did it transcribe correctly? Was the transcript accurate?

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

### 8.3 Barge-in (expected to be imperfect)

Ask something with a long answer, and **interrupt it by speaking** while it
talks.

**Report:**
- Did it stop speaking?
- **Did it ever interrupt itself** — react to its own voice? This is the
  self-trigger problem ADR-0028 names, and I have no real measurement of it.
  If it loops or talks over itself, say so and I will degrade it to half-duplex,
  which is implemented and honest.

---

## 9. Emergency stop and hotkeys

- Press **`Ctrl+Alt+Pause`** at any time.
- **Expect:** a notification saying exactly what was stopped.

**Report:**
- Did the hotkey work from inside another application (a game, an IDE)?
- Did **F9** break anything you use? Be honest — it is a global hook and I
  expect this to be the most annoying decision in the phase.

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
- The log at `%LOCALAPPDATA%\ProjectJarvis\logs\jarvis.log` if something broke.

---

## The short version

If you only have twenty minutes, do these five:

1. `python -m jarvis.main --check` → send me the block
2. Conversation 3.2 and 3.3 → does it label sources and refuse honestly?
3. The approval prompt → **does it steal your keyboard focus?**
4. `Open Brave` → does it open, and does Xbox/Sea of Thieves work?
5. Wake word 8.2 → the four counts

---

## What I will do with your answers

| Your finding | What changes |
|---|---|
| Wake-word counts | I tune the threshold, or leave always-listening off |
| Barge-in self-triggers | I degrade to half-duplex and say so in the GUI |
| Wrong Xbox / Sea of Thieves AUMID | One-line catalogue fix |
| F9 is intolerable | Change the default to something with a modifier |
| Any dishonest status | Treated as a defect, fixed before Phase 2 |

Phase 1 is **not closed** until this is done. Phase 2 does not start first.
