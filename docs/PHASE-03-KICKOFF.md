# Phase 3 kickoff — read this first

You are starting **Phase 3 of Project Jarvis** with none of the previous
sessions' context. This brief exists so you do not have to reconstruct it, and
so you do not repeat mistakes that have already been paid for.

**Do not start writing code until you have read the five documents in §2.**

---

## 1. Where the project is

Jarvis is a **local-first Windows 11 desktop AI agent**: voice-first, lives in
the system tray, operates approved applications through narrow typed tools.
Personal data stays on the machine. Every consequential action is permissioned,
audited, and reversible where possible.

- **Phase 0** — foundation: config, storage, audit, permissions, tray. Closed.
- **Phase 1** — voice: wake word, STT, TTS, conversation, six tools. Closed and
  merged.
- **Phase 2** — desktop and browser: YouTube automation, window management,
  screen capture, files. **Closed 2026-08-06, not yet merged to `main`.**
- **Phase 3** — tasks, skills, memory, file *writing*, clipboard, workspaces.
  **This is you.**

Current state: `python -m pytest -m "not slow"` → 1488 passed, ~83s.
`python -m jarvis.main --check` → exit 0, 18 tools, 15 applications.

---

## 2. Read these, in this order

| # | Document | Why |
|---|---|---|
| 1 | `CLAUDE.md` | The operating contract. Non-negotiable boundaries and the habits this project paid for. |
| 2 | `docs/PROJECT_STATE.md` | Current state and **Next Exact Steps**. Always the first thing to check and the last thing to update. |
| 3 | `docs/phase-reports/PHASE-02-DESKTOP-AND-BROWSER.md` | Especially **§4** (eight ways to claim a success you did not earn) and **§9** (the lesson for Phase 3). |
| 4 | `docs/KNOWN_ISSUES.md` | Thirteen live defects. Do not promise anything about the browser or YouTube Music without reading it. |
| 5 | `docs/BACKLOG.md` §6 | The Phase 3 work items. |

Then, as needed: `PRD.md` (requirements by FR number), `ARCHITECTURE.md`,
`SECURITY.md`, `THREAT_MODEL.md`, `DATA_MODEL.md`, `docs/decisions/`.

**Query Graphify before reading many source files:** `graphify query "<question>"`.
Verify its answers against real source before changing anything security-critical.

---

## 3. The rules you cannot set aside

These are in `CLAUDE.md` in full. The ones most likely to bite in Phase 3:

- **No generic execution.** No shell, `subprocess`, `eval`, `exec`,
  `ShellExecute`. ADR-0029 authorises exactly **one** process-creation call site
  (`launch_argv`) and it is not to be broadened. Enforced by
  `tests/security/test_no_shell.py` — **do not add ALLOW_LIST entries.**
- **Every effect goes through `ToolInvoker`** and its six checks. A new
  capability is a new narrow typed tool plus a catalogue entry, never a widened
  existing tool.
- **Model output is untrusted.** So are web pages, documents, window titles,
  file names and clipboard contents. They are DATA. Selection is **positional or
  by engine-issued reference**, never by name — that is the injection defence,
  written into signatures rather than into a rule.
- **`succeeded` requires verification.** `unverified` is a distinct outcome.
- **A read-only tool may never report `verified`.**
- **High-risk capabilities need fresh confirmation every time**, no standing
  grant, ever.
- **Unbuilt features are shown disabled and name their phase** (ADR-0010).
- **Layering is enforced** (`tests/security/test_layering.py`). Only L5 imports
  Qt.

---

## 4. What Phase 3 is

From `docs/BACKLOG.md` §6. Six groups:

| Group | Contents |
|---|---|
| **P3-TSK** | Task trees, pause/resume with **mandatory re-observation on resume**, cancellation with lock release, waiting conditions, the Task screen, scheduled tasks, conditional triggers |
| **P3-SKL** | Macro recorder, trigger phrases, approval gate, versioning and rollback, parameterised skills, export |
| **P3-MEM** | Memory candidate pipeline with review queue, retrieval relevance, **forget** with cascade delete, conversation deletion, portable identity export |
| **P3-FS** | File **create/copy/move/rename**, safe deletion to the Recycle Bin, archives with path-traversal defence, **undo**, backups, Recovery centre |
| **P3-CLP** | Clipboard read/write, history, sensitive-content detection, application blocklist |
| **P3-WKS** | Save and restore named workspace profiles |

### The three that deserve an ADR before any code

1. **Scheduled and conditional tasks that act while the user is not present.**
   Every safety property in this product so far assumes someone is at the
   keyboard to approve and to notice. A task that fires at 3am has neither. What
   may a scheduled task do unattended, and what must wait for a person?
2. **File writing, deletion and undo.** `fs.write_approved` and
   `fs.delete_or_overwrite` exist in the capability catalogue and **no tool has
   ever been given them**. Deletion is high risk. "Reversible" must mean
   something enforced, not declared — see ADR-0034 for the shape of that
   argument applied to opening files.
3. **Memory.** "No silent memory creation" is a standing rule. The candidate
   pipeline needs a review queue and provenance, and **forget must actually
   cascade** — into derived indexes and embeddings, not only the row.

---

## 5. What Phase 2 learned, that Phase 3 will need more

Phase 1's lesson was *test the seam, not the unit*. Phase 2's is sharper:

> **A check that cannot fail is not a check.**

Eight defects, one mistake: a check that could not distinguish *"I did this"*
from *"this was already true"*. A launch verified against "is the browser
running" — it already was. A close verified against a window list that omits
hidden windows. A window listing licensing "MS Edge has been closed".

**Why this gets worse in Phase 3:** everything above is *state that persists past
the turn that created it*. A false "done" in Phase 2 was corrected by the user
noticing in the next sentence. A false "the task is scheduled", "the file was
backed up" or "that memory was forgotten" is not corrected by anyone, ever.

Before writing any check, ask: **what would this say if the action had done
nothing?** If the answer is "success", it is a restatement, not a check.

Six times this project shipped a correct, unit-tested mechanism wired to
nothing. Every one passed its own tests. The test that catches it asks whether
the **assembled product** offers the thing —
`tests/acceptance/test_phase2_exit_criteria.py` is the pattern.

---

## 6. Practical notes

- **Suite:** `python -m pytest -m "not slow"` while working (~83s, no network).
  The three deselected tests download models from GitHub. Full run before
  claiming completion.
- **Read the exit code**, not just the summary line.
- **Reproduce before fixing.** When a defect has several plausible causes,
  instrument and measure. Three confident explanations for a 96-second browser
  attach were all wrong.
- **Verify a new test fails for the reason you think.** One written for the
  read-only verification bug passed against unfixed code.
- **Check identifiers against the real machine** before writing them down —
  paths, AUMIDs, DOM selectors. Convention gets these wrong.
- **The owner tests by pasting exact transcripts back.** Every serious Phase 2
  defect was found that way. Ask for verbatim text, not summaries.
- **Graphify:** `graphify . --update` after meaningful changes; full rebuild only
  at phase close. Commit `GRAPH_REPORT.md`, `graph.json`, `manifest.json`,
  `.graphify_labels.json` when materially changed.
- **Documentation is updated in the same change**, not later. Behaviour →
  `ARCHITECTURE.md`; schema → `DATA_MODEL.md` **plus a new migration**; security
  → `SECURITY.md` and re-check `THREAT_MODEL.md`; user-visible → `CHANGELOG.md`;
  a decision → a new ADR; live defect → `docs/KNOWN_ISSUES.md`; always →
  `docs/PROJECT_STATE.md`.

---

## 7. Before you start

1. Confirm Phase 2 acceptance has passed, or ask.
2. Confirm whether Phase 2 has been merged to `main`.
3. Ask the owner for **delivery mode** — checkpoint per stage (Phase 2) or
   continuous run (Phase 1). They have used both deliberately.
4. Write `docs/phase-plans/PHASE-03-PLAN.md` before code, in the shape of
   `PHASE-02-PLAN.md`.
5. Raise the three ADRs in §4 **before** implementing what they cover.

The owner's standing preference, in their words: *"unless for sure task not
done, dont stop working"* — finish what you start, and say plainly what you did
not do.
