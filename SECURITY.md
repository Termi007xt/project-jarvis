# Security Policy and Control Specification — Project Jarvis

**Status:** Draft, Phase 0 (foundation and safety architecture)
**Applies to:** Project Jarvis, a local-first Windows 11 desktop voice agent
**Companion document:** `THREAT_MODEL.md` (attacker modelling, STRIDE analysis, and abuse-case walkthroughs live there, not here)

This document is the security *policy and control specification* for Project Jarvis. It states what Jarvis must and must not do, which controls the architecture is required to implement, and how those controls are meant to interact. It does not attempt to model attackers, rank threats, or analyse specific attack chains — that analysis belongs in `THREAT_MODEL.md` and this document should be read alongside it.

Every normative statement below traces, wherever possible, to a numbered requirement in `PRD.md` (`FR-xxx` functional requirements, `NFR-xxx` non-functional requirements, `AT-xxx` acceptance tests, or a lettered/numbered section such as `§11.1`). Statements that do not trace to a specific requirement ID are policy synthesised from the PRD's stated principles and are marked as such.

---

## 1. Scope and security objectives

### 1.1 What Jarvis protects

Project Jarvis is designed around three protected interests, stated in `PRD.md` §2:

1. **User data locality** — the user owns their models, conversation history, memory, skills, settings, and exported identity package, and that data stays on the local machine unless the user explicitly directs it elsewhere (`PRD.md` §2, §4.1).
2. **Host integrity** — Jarvis must not degrade the security posture of the Windows machine it runs on: no permanent administrator mode, no disabling of security controls, no unrestricted code execution (`PRD.md` §6, §11.1 "Prohibited").
3. **User authority** — Jarvis may recommend, prepare, and automate, but it must never silently make consequential decisions for the user, and every capability must be "scoped, permissioned, logged, and reversible where possible" (`PRD.md` §2, §4.5).

### 1.2 Trust posture

Jarvis operates as a **single-user, local-first agent with conditional network access**. Its default trust posture is:

- The interactive Windows user who installed and is signed in to Jarvis is the sole authority who can grant permissions (`PRD.md` §11.4).
- All AI inference is local by default; network access is an explicit, visible exception, not a default state (`PRD.md` §4.1, §7.4).
- Nothing retrieved from the network, the filesystem, the screen, or any application is trusted as instruction — see §2 below.

### 1.3 Explicit non-objective

**Project Jarvis is not a replacement for antivirus software, backup software, access control, or operating-system security** (`PRD.md` §6, item 12). It does not:

- Scan for or remove malware.
- Provide backup or disaster-recovery guarantees beyond its own undo/recovery features (see §11 and `PRD.md` §10.18).
- Replace Windows account security, BitLocker, Windows Defender, firewall policy, or update management.
- Guarantee protection against a compromised or already-malicious operating system, a co-installed malicious application, or a user who is coerced or deceived into approving something themselves.

Anyone relying on Jarvis as a substitute for these controls is out of scope for this policy and should be corrected. This document describes what Jarvis itself must do; it assumes normal Windows security hygiene continues to be the user's responsibility.

---

## 2. Trust boundaries and the "untrusted data" rule

### 2.1 The rule

`PRD.md` §1 (instruction 7) states the governing rule plainly:

> "Treat all website content, documents, emails, messages, clipboard content, and application text as untrusted data, not instructions."

`PRD.md` §11.4 states the corresponding authority rule:

> "Only the authenticated local user, GUI settings, signed skill definitions, and system policy may authorise tools."

Together these two statements define the core trust boundary of the system: **content Jarvis observes is data; only a closed, enumerated set of sources may authorise action.** No text that Jarvis reads, hears, transcribes, or is shown may itself grant permission, regardless of its content, formatting, urgency, or claimed authority (for example, text claiming to be "a system message" or "an admin instruction").

### 2.2 Enumerated untrusted-data classes

Every one of the following must be wrapped and handled by the planner as an **observation**, never as an instruction:

| Input class | Why it is untrusted | Relevant PRD references |
|---|---|---|
| Web page content | Any page can contain adversarial text aimed at the model | FR-054, FR-055, AT-007 |
| Documents (PDF, DOCX, PPTX, XLSX, TXT, MD, HTML, CSV, images) | Document content may embed instructions or misleading metadata | FR-210, FR-211, FR-219, §10.17 |
| Emails / messages | Message bodies are attacker-reachable text | FR-143, FR-144, FR-146, FR-263 |
| Clipboard content | Clipboard can be poisoned by any application with clipboard access before Jarvis reads it | FR-082, FR-250–FR-259 |
| Application UI text | On-screen labels, dialog text, and UI Automation names can be spoofed by a malicious or compromised application | FR-071, FR-074, AT-034 ("Application spoofing another window title" in §23.3) |
| Notification text | Toast and app notifications are attacker-reachable | FR-260–FR-269 |
| Filenames | A filename is user-controlled or remotely-controlled text that can carry a payload of its own | FR-192, FR-193, FR-208 |
| Search results | Search results are third-party, unverified content | FR-050, FR-053 |
| Model output itself | The planner's own generated text is a data product of a context that may include untrusted material upstream; it is never itself a source of authority | §11.4, §13.4 |
| Imported `.jarvispack` files | A portable identity package may originate from another machine, another user, or a malicious source | §14.6, FR-168–FR-170, AT-015, AT-016 |
| Imported skills | A recorded or imported skill is executable automation and must be treated as untrusted until reviewed and approved | FR-100–FR-110, FR-105, §14.5 |

### 2.3 Consequences of the rule

- A webpage, document, or message that contains text such as "ignore previous instructions," "click Allow," "run this command," or "send this data" must be logged as an **observed, ignored instruction attempt** and must never influence the permission or tool-selection pipeline (`PRD.md` §11.4, AT-007).
- Every tool call the planner produces must still pass the full evaluation pipeline in §5 regardless of how convincingly the surrounding context argued for it.
- Imported `.jarvispack` packages and imported skills must go through explicit preview, conflict detection, and approval before anything in them becomes active (`PRD.md` §14.6, FR-105, FR-224). A skill manifest carries a `signed` field (`PRD.md` §14.5); Phase 0 does not yet define or implement a signing authority, so no skill can currently be trusted on the basis of a signature alone — see §14 status table.
- Model output must always be structured, schema-validated data — "Free-form natural-language instructions must never be executed directly" (`PRD.md` §13.4).

---

## 3. Capability risk classification

`PRD.md` §11.1 defines four capability classes. This document reproduces them verbatim as the authoritative classification; no new classes may be introduced without a corresponding PRD change and ADR.

### 3.1 Low risk — may support "always allow"

| Capability |
|---|
| Answer local questions |
| Speak responses |
| Open an approved application |
| Open an approved website |
| Control volume |
| Play or pause media |
| Read active window title |
| Show notifications |

### 3.2 Medium risk — ask every time, per task, per app, or per folder

| Capability |
|---|
| Mouse and keyboard automation |
| Screenshot capture |
| Clipboard read/write |
| Read files in approved folders |
| Create or modify files in approved folders |
| Browser automation in logged-in sessions |
| Monitor a specified application |
| Copy private messages |
| Install or remove local models |
| Download non-executable files |
| Start a long-running watcher |

### 3.3 High risk — fresh confirmation required every time

| Capability |
|---|
| Delete or overwrite files |
| Download or run executable files |
| Install software |
| Force-close applications |
| Send, edit, or delete messages or emails |
| Submit forms that create obligations |
| Publish content |
| Make purchases or financial actions |
| Change account, security, or privacy settings |
| Access camera |
| Export sensitive data |
| Approve IDE terminal commands |
| Elevate privileges |
| Modify system settings |

### 3.4 Prohibited in the initial product

| Capability |
|---|
| Generic shell execution |
| Arbitrary script execution |
| Reading passwords or private keys |
| Disabling antivirus or security controls |
| Credential theft or session extraction |
| CAPTCHA bypass |
| Stealth recording |
| Surveillance of other users |
| Permanent administrator operation |
| Autonomous financial transactions |
| Autonomous legal acceptance |
| Hidden remote control |

### 3.5 Class invariants

These invariants are binding on the implementation and must be checked by automated tests (`PRD.md` §23.1, §23.3):

1. **High-risk capabilities must not offer "always allow."** `PRD.md` §9.9 states this explicitly: "High-risk permissions must not offer 'always allow.'" The permission screen and the approval dialog (§5 below) must enforce this as a structural constraint, not a UI default that a user could otherwise reconfigure around.
2. **Prohibited capabilities are compile-time absent, not runtime-denied.** A prohibited capability must never exist as a callable tool that a permission check then rejects. It must not be registered, must not appear in the tool schema exposed to the model, and must not be reachable through any code path. See §4 for the enforcement mechanism.

---

## 4. The prohibited-capability list

### 4.1 Named prohibited tools

`PRD.md` §13.3 lists the following as **prohibited broad tools** — these tool identifiers, and any tool with equivalent effect regardless of name, must never be registered:

```
run_shell(command)
execute_code(code)
run_powershell(script)
delete_anything(path)
control_computer(goal)
approve_all()
search_entire_computer_without_scope(query)
read_all_files()
upload_any_file(path)
change_any_windows_setting(setting, value)
monitor_all_notifications()
capture_screen_continuously()
restore_everything()
```

### 4.2 Hard constraints

In addition to the named tools above, `PRD.md` §1 (instructions 4–6, 14) and §6 (non-goals) establish the following hard constraints, which apply for the lifetime of the product, not only Phase 0:

- No generic terminal, Command Prompt, PowerShell, WSL, or unrestricted shell tool may ever be exposed to the runtime agent (`PRD.md` §1 instruction 4; §6 item 1).
- No `cmd.exe` invocation path, no registry-write capability, and no arbitrary code execution tool of any kind.
- No permanent administrator mode; the application runs non-elevated by default (`PRD.md` §6 item 2, FR-003; see §6 of this document).
- No screenshot-based computer control in Phase 0 — Phase 0 delivers no computer-control features at all (`PRD.md` §21, Phase 0 scope: "No computer-control features yet"). Screenshot-driven vision fallback is a Phase 4 capability and remains subordinate to the deterministic-before-visual hierarchy even then (`PRD.md` §4.2, FR-074–FR-076).
- No silent memory creation — every new memory is either explicitly requested, proposed as a candidate for approval, temporary session context, or automatically retained operational state with a defined expiry (`PRD.md` §4.4, FR-160–FR-164).
- No autonomous self-modification — "learning" is limited to saved preferences, aliases, named workflows, learned selectors, saved memories, and outcome-based ranking; it explicitly excludes "autonomous retraining, hidden model-weight changes, or unreviewable self-modifying code" (`PRD.md` §7.2).

### 4.3 Enforcement strategy

Prohibition is enforced in layers, so that a single missed check cannot reintroduce a prohibited capability:

**(a) No such tool is ever registered.** The tool registry is a closed, explicit allow-list assembled from source-controlled tool definitions (`PRD.md` §13.2, tool contract). Prohibited tool identifiers, and generic "do-anything" tool shapes, are never written into the registry in the first place. There is no runtime code path by which `run_shell` or an equivalent could be added without a source change.

**(b) The tool registry rejects registration of denylisted ids and name patterns.** As a second, independent layer, tool registration itself must validate every candidate tool id and signature against a denylist of prohibited identifiers and name patterns (for example, names or descriptions implying unrestricted shell, unrestricted deletion, or unrestricted filesystem/computer access) before accepting it into the registry. This protects against a future contributor, plugin, or generated adapter accidentally reintroducing a prohibited shape under a new name.

**(c) An automated security test scans `src/` for prohibited primitives and fails the build.** A dedicated safety test (living under `tests/security/`, per the repository layout in `PRD.md` §20) must scan the `src/` tree for the presence of the following primitives and fail the build if any is found outside an explicitly reviewed and justified exception list:

- `subprocess` (any invocation form)
- `os.system`
- `os.popen`
- `eval(`
- `exec(`
- `shell=True`
- `ctypes.*ShellExecute` (and equivalent Win32 shell-execution calls)

This is a static, build-time gate, not a runtime permission check — its purpose is to catch a prohibited primitive before it ever ships, consistent with `PRD.md` §23.3's adversarial test case "Model requests shell execution" and the acceptance requirement that no generic shell exists anywhere in the runtime (`PRD.md` §21, Phase 0 exit criteria).

---

## 5. Permission model

### 5.1 Decision types

`PRD.md` §9.9 defines the exhaustive set of permission decisions available in the GUI:

- Deny
- Ask every time
- Allow for this session
- Allow for this task
- Allow for a selected application
- Allow for a selected folder
- Always allow, only for low-risk capabilities

No other decision type may be added without a PRD change, and — per §3.5 above — "Always allow" must never be offered for a Medium, High, or Prohibited capability.

### 5.2 Scope dimensions

A permission grant is scoped along one or more of the following dimensions, matching the decision types above and the `Permission` / `Permission decision` entities in the data model (`PRD.md` §14.3):

| Dimension | Meaning | Typical expiry |
|---|---|---|
| Session | Valid for the current Jarvis session only | Ends when Jarvis exits or the user signs out |
| Task | Valid only for the originating task | Ends when the task reaches a terminal state (Succeeded, Failed, Cancelled) |
| Application | Valid only when acting on a named application | No automatic expiry; user-revocable |
| Folder | Valid only within a named folder scope | No automatic expiry; user-revocable |
| Always (low-risk only) | Persistent across sessions | No automatic expiry; user-revocable; unavailable for Medium/High/Prohibited |

### 5.3 Revocation

Permission grants must be revocable by the user at any time, including mid-task. `PRD.md` §23.3 names "User revokes permission mid-task" as a required adversarial safety test case, which implies that permission state must be re-checked at each tool invocation rather than cached for the lifetime of a task. A task that loses its permission mid-flight must stop before the next permissioned action and surface a blocked/paused state rather than continuing on stale authority.

### 5.4 Evaluation order

Every proposed tool invocation — regardless of which agent role produced it — must pass through the following ordered checks before any side effect occurs:

1. **Prohibited check** — is this tool identifier or shape on the prohibited/denylist? (Structural — see §4.3(a)/(b). In practice this check has already been satisfied at registration time, since a prohibited tool cannot exist in the registry; it is listed first here because it is the most fundamental gate.)
2. **Tool allow-list validation** — does this tool id exist in the registered tool registry at all?
3. **Schema validation** — does the proposed call match the tool's declared input schema (`PRD.md` §13.2)?
4. **Parameter validation** — do the individual parameter values satisfy the tool's semantic constraints (path is within an approved root, index is in range, target exists, and so on)?
5. **Permission grant lookup** — does an active, unrevoked permission grant exist that covers this tool, this scope, and this actor?
6. **Resource-lock evaluation** — are the resource locks this action requires (see FR-124: foreground desktop control, Brave automation profile, microphone command capture, speaker output, clipboard, application instance, folder scope, network connector) available or already held by the same task?
7. **User approval** — if the permission decision type requires it ("Ask every time," or no matching grant exists), present the approval dialog (§5.5) and block until the user responds.

This document sequences the prohibited check and the allow-list check ahead of schema and parameter validation as a defence-in-depth ordering — reject on identity before spending effort validating the shape of something that should never have been callable. `PRD.md` §13.4 defines a closely related pipeline specifically for validating model output ("JSON/schema validation, Permission evaluation, Resource-lock evaluation, Tool allow-list validation, Parameter validation, User approval where required"); the two are not in conflict — §13.4 describes the model-output-specific validation chain once a call has been proposed, while the ordering above is this document's full end-to-end specification including the registration-time prohibition gate. Implementers should treat `PRD.md` §13.4 as authoritative for the model-output validation chain and this section as the superset that also covers registration-time exclusion. Any future revision should reconcile the two into one explicit ordering rather than leaving the discrepancy unresolved.

### 5.5 Approval dialog

`PRD.md` §11.2 requires an approval dialog to show:

- Requested action
- Initiating user request
- Application and target
- Files, recipients, or destination
- Data involved
- Risk category
- Exact scope
- Whether it is reversible
- "Allow once"
- "Allow for this task," only where safe
- "Deny"
- "Stop task"

An approval dialog that omits any of these fields for an action where the field is applicable does not satisfy this policy.

---

## 6. Privilege and elevation policy

### 6.1 Non-admin by default

Jarvis shall run without administrator rights by default (FR-003). This is the default state of the installed application, not a mode the user must remember to select. `NFR-020` (least privilege) requires the application to use the minimum Windows privileges required for whatever it is currently doing.

### 6.2 Scoped elevation

When an action genuinely requires elevation, Jarvis must use a **separate, narrowly scoped elevated helper process** and must display the exact action that will run with elevated rights before the Windows UAC prompt appears (FR-004). Elevation is:

- Per-action, not persistent — the elevated helper performs one declared action and exits; it must not become a standing elevated service.
- Isolated from the main Jarvis Core process — the helper is a distinct process boundary (`PRD.md` §12.2 process model), not an in-process privilege escalation.
- Explicit — settings changes that require elevation route through this scoped elevation policy (FR-238, "Administrator boundary").

### 6.3 The secure desktop is off-limits

Jarvis must not interact with the Windows secure desktop or UAC prompts (FR-079). This means Jarvis may not programmatically click, dismiss, pre-fill, or otherwise automate a UAC consent dialog — the user must see and act on the genuine Windows elevation prompt themselves. This is a deliberate limit: it prevents Jarvis (or anything that has compromised Jarvis) from silently escalating privileges.

### 6.4 Consequences

- Jarvis must never claim it "elevated automatically" — any elevation always surfaces a real, user-visible UAC prompt tied to the specific declared action.
- A capability that would require standing administrator rights to implement reliably is out of scope until it can be redesigned around per-action scoped elevation.
- FR-237 further restricts what Jarvis may do even when a user is looking at security-related Settings pages: Jarvis may open such pages but must not autonomously disable antivirus, disable the firewall, disable SmartScreen, change account security, change authentication methods, change UAC, or disable encryption.

---

## 7. Process isolation and local IPC

### 7.1 Process model

`PRD.md` §12.2 defines five logical responsibilities, which may initially be modules within one packaged application but must remain interface-compatible with a future split into separate processes:

| Process | Responsibilities |
|---|---|
| Jarvis Shell | PySide6 GUI, tray icon, user approvals, settings, task display, notifications, global hotkeys |
| Jarvis Core | Conversation orchestration, model routing, tool registry, permission evaluation, task planning, memory retrieval, audit logging |
| Audio Worker | Wake phrase, VAD, recording, STT, TTS playback, microphone state |
| Automation Worker | UI Automation, browser automation, mouse and keyboard, screenshots, application adapters, step verification |
| Task Scheduler | State machine, queue, locks, checkpoints, retry, pause/resume, watchers |

Audio and automation must run outside the GUI thread even in the single-process MVP form (`PRD.md` §12.2). This is both a reliability requirement (the GUI must stay responsive per NFR-003) and a security-relevant isolation boundary: a hang or crash in audio or automation processing must not silently disable approvals, the audit log, or the permission engine running in Core.

A concrete example of process isolation already specified in the PRD is the TTS worker: the Qwen3-TTS integration must run in a separate Python 3.12 environment, as a separate worker process, over typed authenticated local IPC, with explicit health checks, bounded startup time, and clean shutdown, and it must have **no direct access to Jarvis tools or permissions** (FR-038). This is the template for how any future isolated worker should be constrained: a worker converts one narrow input (text and style metadata, in the TTS case) into one narrow output (audio) and holds none of Core's authority.

### 7.2 Local communication requirements

Where Jarvis is split into multiple processes, `PRD.md` §12.3 requires:

- All internal interfaces use typed messages and schema validation.
- Binding only to loopback or Windows named pipes — never a general network interface.
- A per-installation authentication token generated locally, required on every request.
- No unauthenticated network port exposed, ever.
- Rejection of requests from non-local interfaces.
- Token rotation during reset.

`NFR-021` restates the outcome directly: local services must not accept remote connections by default. This is a hard requirement, not a configurable default a user could loosen without also changing the underlying architecture.

---

## 8. Secrets management

### 8.1 Storage

API keys, cookies, tokens, and credentials must be stored using **Windows-protected credential storage** — DPAPI or Windows Credential Manager — never in plaintext configuration files (`PRD.md` §18.3, NFR-022). This applies to every secret category the GUI allows the user to configure: search provider keys, optional cloud model keys, optional TTS provider keys, and optional integration tokens (`PRD.md` §18.3).

### 8.2 No shared secrets

The product must not ship with any shared API keys embedded in the installer or source (`PRD.md` §18.3). Every credential in use belongs to the individual user and is supplied by them during setup.

### 8.3 Exports

Secrets are excluded from the normal identity export path by default (FR-169). The `.jarvispack` package format explicitly excludes, in its normal export mode (`PRD.md` §14.6):

- API keys
- Cookies
- Login sessions
- OAuth refresh tokens
- Passwords
- Device-specific absolute paths (unless explicitly included)
- Private keys

A **separate, optional, passphrase-protected encrypted export** may include secrets, but only after an explicit warning to the user and only behind a passphrase the user supplies (FR-170). This is the sole path by which secrets may ever leave the local secret store in an exported artifact; the default export path must never be able to leak them by omission of a filter.

### 8.4 Passwords and payment data remain out of scope entirely

Independent of export handling, Jarvis must not read passwords, payment-card details, private keys, authentication codes, or password-manager content at all (`PRD.md` §6 item 8). This is a capture-time restriction, not merely an export-time redaction — the data must not be observed in the first place, not observed-then-filtered.

---

## 9. Audit logging requirements

### 9.1 Required fields

`PRD.md` §11.5 requires every consequential action to log:

- Timestamp
- Task ID
- Conversation ID
- Tool
- Parameters with secret redaction
- Permission decision
- Pre-action state
- Result
- Verification
- Error
- Screenshot reference if enabled

### 9.2 Handling requirements

- **Append-only.** The audit log is a durable record of what Jarvis did and why. Nothing in the design should allow a running Jarvis process (or the LLM it drives) to edit or remove a prior entry; the on-disk representation is a JSON-lines file (`logs/audit.jsonl` in the data layout at `PRD.md` §14.2), which is a natural append-only format. Only an explicit, user-initiated deletion action (§9.3) may remove audit history — the application itself never rewrites history in the course of normal operation.
- **Redaction of secrets.** Every tool declares redaction rules as part of its tool contract (`PRD.md` §13.2), and the audit log records "Parameters with secret redaction" rather than raw parameter values (`PRD.md` §11.5). Redaction happens before the record is written, not as a display-time filter over a fully-plaintext store.
- **User-viewable, searchable, exportable, and deletable.** `PRD.md` §11.5 requires audit logs to be "viewable, searchable, exportable, and user-deletable." Deletion of audit history is a user action, distinct from and not implied by any automatic retention policy.
- **Never plaintext secret or clipboard content.** FR-259 states this specifically for clipboard: "Audit logs shall record clipboard actions without storing sensitive clipboard content in plaintext." The same principle extends to every other secret-adjacent action class covered by §8: the audit log may record *that* an action touched a secret, a password field, or sensitive clipboard content, and the redacted shape of the parameters, but never the plaintext content itself.

### 9.3 Relationship to memory and export deletion

Deleting source material (a conversation, a memory, a document) should prompt the GUI to also offer deletion of memories and embeddings derived from it (FR-167). Audit log deletion is a related but distinct operation — the audit trail is a record of actions taken, not of derived knowledge, and its retention policy should be configured and reasoned about independently from the memory-deletion path described in `PRD.md` §10.14.

---

## 10. Data handling and retention

### 10.1 Local-first principle

Core inference, wake-word detection, speech recognition, memory, task state, and automation must work locally (`PRD.md` §4.1). Network access is permitted only for specific, user-visible purposes: internet search, opening websites, downloading user-selected models or voice packs, checking for application updates, using an optional user-configured external provider, or interacting with online services explicitly requested by the user. Every network-backed response must display a network indicator and the method used (FR-051).

### 10.2 Network mode taxonomy

`PRD.md` §7.4 defines three modes that the product must distinguish in its UI and behaviour:

| Mode | Behaviour |
|---|---|
| Offline mode | No network requests at all |
| Local assistant mode | Local model; network tools available only when explicitly invoked |
| Connected mode | Optional configured search or AI providers are available |

AT-001 requires that, given offline mode is enabled, a general question produces no network request at all — this is a testable acceptance criterion, not just a description.

**"No network requests at all" includes third-party libraries.** Found during Phase 1 verification: both Kokoro and faster-whisper resolve their weights through `huggingface_hub`, which contacts the Hub when a model is loaded — observed in a real run as *"You are sending unauthenticated requests to the HF Hub"*. That is a genuine remote request, made by a component the user reasonably believes is entirely local, and it bypassed every adapter written to honour offline mode. In offline mode the hub libraries are now pinned to their local cache (`jarvis.audio.model_hub`), so a model that has not been downloaded fails with a clear message rather than silently reaching out. Tests: `tests/security/test_offline_speech_models.py`.

The general lesson is recorded here deliberately: enforcing a network boundary in our own adapters is necessary but not sufficient, because a dependency can open a socket on our behalf. Any new dependency that loads a model or resource by name needs the same check.

### 10.3 Raw audio

- **Pre-wake:** before wake detection, audio may exist only in a short in-memory ring buffer and must not be written to disk (FR-012). AT-002 makes this testable: given listening is enabled but no wake phrase is detected, no microphone audio is written to disk.
- **Post-transcription:** raw command audio is deleted after transcription unless the user has explicitly enabled diagnostic retention (FR-025).

### 10.4 Screenshots

Screenshots used for automation are temporary by default (FR-278). The user may configure: no retention, retain until task completion, retain for diagnostics, or retain selected screenshots only. Screenshots are excluded from normal exports unless explicitly selected (FR-279). Screen capture is further scoped to the minimum necessary surface — a control, the active application, the active window, a selected region, or a selected monitor — with full-desktop capture requiring explicit approval (FR-271), and users may block capture for sensitive applications entirely (FR-273).

### 10.5 Telemetry

Default telemetry is off (`PRD.md` §18.5). If a user opts in, telemetry must exclude conversation content, exclude screenshots, exclude filenames and message content, be documented, be revocable, and local-only crash logs must remain supported as an alternative.

### 10.6 Complete data deletion

Users must be able to delete all local data (NFR-025). This is a hard requirement independent of the granular deletion controls elsewhere (conversation deletion, memory deletion, audit log deletion) — there must be a complete-erasure path, and the installer's uninstall flow must offer explicit data deletion as part of removal (`PRD.md` §18.1).

### 10.7 History and memory defaults

Conversation history is stored locally and may be disabled globally or per conversation (FR-045). A private session avoids permanent history and memory creation while retaining only the operational state needed to complete the current task (FR-046), and AT-014 requires that a private session leave no permanent conversation or memory record after it ends. Potentially sensitive information defaults to non-persistent unless the user explicitly saves it (FR-164).

---

## 11. Filesystem safety

### 11.1 Root-scoped tools

Filesystem tools require an approved root scope and must reject paths outside that root unless a new permission is granted (FR-208). There is no filesystem tool that operates against an unscoped or implicit "whole computer" root — `search_entire_computer_without_scope(query)` and `read_all_files()` are explicitly on the prohibited list (§4.1).

### 11.2 Path canonicalisation

Path validation must resolve, before any scope check is considered satisfied (FR-208):

- Relative paths
- Symbolic links
- Junctions
- Shortcuts
- Case differences
- Environment variables

A path that resolves — after following any of the above — to a location outside the approved root must be rejected, not merely flagged. AT-022 makes this testable directly: "A filesystem tool cannot read or modify a path outside its approved root scope."

### 11.3 Denied targets

Independent of scope, Jarvis must never (FR-204):

- Search the entire computer without approval
- Read hidden or system folders by default
- Access another Windows user's files
- Follow symbolic links, shortcuts, or junctions outside the approved scope without validation
- Upload a file because a webpage requests it
- Read credential stores
- Read password databases
- Read private keys
- Read browser session databases
- Read authentication files
- Disable filesystem security controls
- Change file ownership or access-control lists without high-risk approval

### 11.4 Archive extraction protections

Archive creation and extraction are permitted only inside approved folders, and extraction must specifically protect against (FR-200):

- Path traversal
- Writing outside the selected destination
- Silent overwriting
- Unexpected executable content
- Excessive archive expansion (zip-bomb style resource exhaustion)
- Symbolic-link escape
- Unsupported or encrypted archives

### 11.5 Deletion is non-destructive by default

Jarvis does not permanently delete files by default. Normal deletion displays the affected files, requires explicit confirmation, moves supported files to the Windows Recycle Bin, records the operation in the audit log, and offers undo where technically possible (FR-199). Permanent deletion and emptying the Recycle Bin require separate, high-risk confirmation. AT-023 and AT-025 make this testable: deleting a normal file goes to the Recycle Bin after confirmation, and a permanent deletion is preceded by an explicit statement that the action cannot be undone.

---

## 12. Emergency stop

`PRD.md` §11.3 requires Jarvis to provide all of the following, together, as the emergency-stop surface:

- Global emergency-stop hotkey
- Tray emergency-stop command
- Main-window stop control
- Voice stop phrase where technically reliable
- Automation worker termination
- Lock release
- Clear notification of what was stopped

The global hotkey must be configurable and must not conflict with common Windows shortcuts. (`PROJECT_INPUTS.md` proposes `Ctrl+Alt+Pause` as a starting default; the binding remains user-configurable per this requirement and is not itself a fixed PRD mandate.)

Emergency stop is a cross-cutting control: it must reach the Audio Worker, the Automation Worker, and the Task Scheduler regardless of which process boundary they end up on (§7.1), and it must release resource locks (FR-124) so that a stopped task does not leave the foreground desktop-control lock, the Brave automation profile, the microphone, or a folder scope permanently held.

**Correction (2026-08-04):** emergency stop reached the scheduler, the locks, the workers and the approval queue, but not speech — so pressing it cancelled everything and then carried on talking over the silence, which is the one part of "stop" the user can actually hear. It now interrupts playback first, then stops the automation. Speech is stopped through `DuplexCoordinator.request_barge_in`, which by ADR-0028 releases no locks and cancels no tasks, so the reverse operation is also available on its own: **Stop speaking** in the tray silences Jarvis without stopping any work. Conflating the two would make "be quiet" quietly destructive.

---

## 13. Supply chain and release security

### 13.1 Dependency and licence scanning

Builds must include dependency and licence scanning (NFR-023). This is a build-time gate, and — per the Phase 0 deliverable list in `PRD.md` §21 ("Repository and CI") — belongs in the same CI pipeline as the prohibited-primitive scan described in §4.3(c).

### 13.2 Signed releases

Public installers and update packages must be signed (NFR-024). The update system must further support manual update checks, optional automatic update checks, signed update packages, release notes, rollback for failed updates, schema migrations, and compatibility checks for skills and packs (`PRD.md` §18.4).

### 13.3 No bundled shared credentials

As stated in §8.2, the product must not ship shared API keys (`PRD.md` §18.3). This extends to the installer and update channel: nothing in the release artifacts should embed a credential usable across all installations.

### 13.4 Redistribution of models, voices, and assets

`PRD.md` §1 (instruction 15) states the general rule: "Do not bundle third-party models, voices, logos, icons, or copyrighted assets unless their licences explicitly permit redistribution." `PRD.md` §17.3 makes this concrete for asset acquisition before public distribution — every download must show its provider, model or package name, licence, approximate size, install location, whether it can be redistributed, and a remove option (`PRD.md` §17.2) — and states explicitly:

> "Do not use Marvel character artwork, film audio, actor voice likenesses, or other protected branding without legal clearance."

This applies with equal force to voice cloning: `PRD.md` §6 (non-goals) states the product will not "clone a real person's voice without documented permission." Any experimental voice work (for example, exploratory scripts under `tools/`) that is not accompanied by documented permission or a redistribution-clear licence must never be treated as a candidate for bundling into a public release, and must not ship as a default or built-in voice profile.

User-imported assets (icons, voice packs, wake-word models, sound effects, personality profiles, skill packs, application mappings, custom prompts) must display licence and source fields in the GUI (`PRD.md` §17.4), and redistributable voice packs specifically must carry licence metadata, with user-imported voices remaining outside the installer unless redistribution is separately authorised (FR-032).

---

## 14. Security status (Phase 0 foundation plus Phase 1 stages 1–3)

This table states, honestly and conservatively, what security-relevant controls exist in this repository. It was verified against the committed code and a passing test suite (617 passed, 2 skipped), not against the target design. Rows marked `(Phase 1)` were added or promoted during Phase 1 stages 1–3; stage 4 has not been started.

No row should be read as "safe to rely on in production". Every control not marked `Implemented` is a stated intention, not a working safeguard. `Implemented` means the control exists in `src/jarvis`, is exercised by an automated test, and that test passes.

| Control | Required by | Phase 0 status | Notes |
|---|---|---|---|
| Typed event bus | PRD §21 (Phase 0 deliverable) | Implemented | `jarvis.core.events`. Frozen pydantic events, subclass matching, thread-safe publish, isolated handlers. Tests: `tests/unit/test_event_bus.py`. |
| Tool schema / tool contract | PRD §13.2, §21 | Implemented | `jarvis.core.tools.contract.ToolSpec` carries the full §13.2 field set including reversibility and rollback metadata. Tests: `tests/acceptance/test_phase0_exit_criteria.py`. |
| Permission engine (decision types, evaluation order) | PRD §9.9, §11, §21 | Implemented | `jarvis.core.permissions`. Unknown denied, prohibited denied unconditionally, high risk always asks, scoped grants with expiry and revocation; `always` is low-risk only. Tests: `tests/unit/test_permission_engine.py`. |
| Prohibited-capability guard (registry denylist + static `src/` scan) | PRD §13.3, §23.3, §21 | Implemented | All three layers. `jarvis.core.tools.prohibited` denies by identity and by name pattern; `tests/security/test_no_shell.py` AST-scans the package and fails the build; a dedicated CI job runs `tests/security` separately. |
| Audit log (append-only, redaction, viewable/searchable/exportable/deletable) | PRD §11.5, §21 | Implemented | `jarvis.core.audit`. Append-only JSONL plus a SQLite search index, full §11.5 field set, redaction applied on the way in, viewable in the Audit log screen. Tests: `tests/unit/test_audit_log.py`, `tests/security/test_secret_redaction.py`. |
| Resource locks | PRD FR-124, §7.1, §21 | Implemented | `jarvis.tasks.locks`. Exclusive, persisted, owner-attributed, all-or-nothing over a sorted set, with stale reclamation after a crash. Tests: `tests/unit/test_tasks.py`. |
| Task state machine | PRD FR-122, §21 | Implemented | `jarvis.tasks`. All ten states with a validated transition table; terminal states have no outgoing edges; durable in SQLite. Tests: `tests/unit/test_tasks.py`. |
| Configuration system | PRD §21 | Implemented | `jarvis.config`. Three layers merged into one frozen pydantic tree with `extra="forbid"`; only overrides are persisted; writes are atomic. Tests: `tests/unit/test_config.py`. |
| Test harness | PRD §21, NFR-042 | Implemented | 745 tests across `tests/unit`, `tests/security`, `tests/integration`, `tests/ui` and `tests/acceptance`. Every test gets an isolated vault; none requires Ollama, audio, a GPU or the network. **Phase 1 exposed a gap this count hides:** every unit passed while the product did not work, because nothing tested the seam between the GUI and the engine. `tests/ui/test_conversation_wiring.py` and `tests/ui/test_voice_wiring.py` now assert the connections, including the rule that an enabled control either does something or says why it cannot. |
| Single-instance guard | PRD FR-005, §21 (exit criterion) | Implemented | `jarvis.runtime.single_instance`. Windows named mutex in the `Local\` namespace, with a lock-file fallback that reclaims a file left by a dead process. Tests: `tests/unit/test_runtime_primitives.py`. |
| Non-admin default operation | PRD FR-003, NFR-020 | Implemented | Nothing requests elevation, and `tests/security/test_no_elevation.py` AST-scans for elevation entry points and checks packaging manifests for `requireAdministrator`/`highestAvailable`. Now an enforced invariant, not merely an absence. |
| PySide6 tray shell | PRD §21 | Implemented | `jarvis.ui`. Seven §9.1 tray states distinguished by shape and accessible text as well as colour; §9.2 menu with unavailable entries disabled and labelled by phase; fifteen §9.3 navigation areas, seven live. Tests: `tests/ui/test_shell.py` (offscreen). |
| Ollama health check | PRD §21 | Implemented | `jarvis.llm.ollama.health`. Loopback-only (a non-loopback endpoint is refused without opening a socket), offline-mode aware, explicitly timed out. Tests: `tests/unit/test_ollama_health.py`. |
| Crash recovery / task durability | PRD FR-006, NFR-010, NFR-011 | Implemented (baseline) | `jarvis.tasks.recovery`. Interrupted tasks are paused and marked `recovered`, never auto-resumed; stale locks reclaimed; all audited. Watcher and long-workflow durability remain Phase 3/4. Tests: `tests/integration/test_core_lifecycle.py`. |
| Tool invoker six-step pipeline | PRD §13.4 | Implemented | `jarvis.core.tools.invoker`. Allow-list, schema, permission, locks, approval, execute — the single choke point. Bounded timeouts and retries; `succeeded` requires verification. Tests: `tests/unit/test_tool_invoker.py`. |
| Approval dialog and queue | PRD §11.2, ADR-0027, ADR-0010 | Implemented (Phase 1) | `jarvis.core.tools.approvals.ApprovalQueue` plus `jarvis.ui.approval`. Tray-anchored and non-modal so asking never steals focus from the automation being asked about; an unanswered request expires as **denied**, never allowed; `answer()` refuses any scope the request did not offer, so a UI defect cannot widen a high-risk grant; a denial can be remembered as a scoped `DENY`. Tests: `tests/unit/test_approval_queue.py`, `tests/ui/test_approval_dialog.py`. |
| Layering enforcement (engine has no Qt dependency) | ADR-0004 | Implemented | `tests/security/test_layering.py` fails the build if any module below the presentation layer imports Qt, or if any module imports a higher layer. |
| Emergency stop | PRD §11.3 | Implemented (Phase 1) | `JarvisCore.emergency_stop` cancels tasks, releases locks, stops workers, denies any pending approval, and reports exactly what was stopped. Reachable from the tray, the Home screen and the configurable global hotkey (`jarvis.runtime.hotkeys`). A hotkey another process already owns is reported as unavailable and now also raises a notification, rather than only a log line. **Correction (2026-08-03):** this entry previously claimed the hotkey route worked, and it did not. The key registered correctly and its callback was marshalled with `QTimer.singleShot` from the hotkey thread, which silently does nothing — a timer cannot be created on a thread Qt did not start. The panic button was unreachable from the keyboard for the whole of Phase 1. Now a queued signal, with `tests/ui/test_cross_thread_marshalling.py` asserting the press reaches the core. The default binding also moved off `Pause`, which many keyboards do not have. |
| Wake phrase, VAD, ring buffer, push-to-talk | PRD FR-010–FR-018, §21 (Phase 1) | Partial (Phase 1) | The pipeline, ring buffer, VAD and push-to-talk are implemented; the pre-wake buffer has **no file-handling code at all**, so FR-012 and AT-002 are structural. Tests: `tests/acceptance/test_at002_wake_privacy.py`. **Wake detection itself is not active**: no openWakeWord base model is present, which is reported honestly and leaves push-to-talk as the route (ADR-0016). Per-user enrolment and its measurement are not built. |
| Local speech recognition (STT), no raw-audio retention | PRD FR-020–FR-025, §21 (Phase 1) | Implemented (Phase 1) | `jarvis.audio.stt`. Transcription takes audio in memory and never a path, so raw command audio does not reach disk; the wake phrase is stripped before the command travels; low-confidence commands are flagged for confirmation. Verified on hardware: faster-whisper `small` transcribed Kokoro output exactly. |
| Local text-to-speech, sensitive-output filtering | PRD FR-030–FR-034, §21 (Phase 1) | Implemented (Phase 1) | `jarvis.audio.tts` and `jarvis.audio.playback`. Kokoro `bm_george` verified audible on this machine (4.3 s through the default output device). Secret-shaped text is replaced with a description of what it was **before** synthesis (FR-034) — verified aloud: "my api key is sk-live-abcdef123456" was spoken as "my api key is a key". Presentation stripping (`speakable_text`) runs **before** redaction, so markdown around a credential cannot hide it from the patterns; the strip removes emoji, formatting and URL machinery only, never words, and the written transcript is unaffected. Every voice carries licence metadata marked non-redistributable while ADR-0014 is unresolved (FR-032). |
| Spoken output is not claimed unless it happened | PRD FR-048, AT-018 | Implemented (Phase 1) | **Regression.** `voice.speak` returned `verification=verified` and the message "Spoken." as soon as synthesis produced audio, while no playback existed anywhere in the product — a tool-confirmed success for a silent room, which then reached the transcript labelled "confirmed by a tool". The tool now requires a playback report showing audio reached the output device, and fails with `playback_failed` otherwise. Tests: `tests/unit/test_speak_tool.py`. |
| Offline mode covers third-party model loading | PRD AT-001, §7.4 | Implemented (Phase 1) | **Regression.** Kokoro and faster-whisper resolve weights through `huggingface_hub`, which contacted the Hub on load despite offline mode. `jarvis.audio.model_hub` pins them to the local cache when offline, re-applied on every mode change because the switch is read at load time. Tests: `tests/security/test_offline_speech_models.py`. |
| Recording indicator | PRD FR-013, §11.1 (prohibited: recording without a visible indicator) | Implemented (Phase 1) | `CaptureSession` calls an indicator on start and stop; the shell now supplies one (`jarvis.ui.voice_controller`), so the tray shows the recording state and the Voice screen says "Recording — speak now." Previously the hook existed and **nothing was attached to it**, so capture could have started with nothing on screen. Tests: `tests/ui/test_voice_wiring.py`. |
| Full-duplex audio and barge-in | PRD FR-015, ADR-0028 | Partial (Phase 1) | `jarvis.audio.duplex`. Playback never stops capture; barge-in stops speech and releases no locks and cancels no tasks; the half-duplex degradation path is implemented. **Correction (2026-08-04):** this entry described defence 3 as working, and it could not fire. The score multiplier of 1.6 against a 0.6 threshold demanded 0.96, which openWakeWord effectively never produces, and the self-echo test compared a *microphone* level against the RMS of our own *output samples* — different instruments, different scales — so it rejected genuine interruptions whenever the room was quieter than the waveform, which is the normal case. The multiplier is now 1.15 and the baseline is the level the microphone itself measured during playback (`note_captured_level`). **Self-trigger rates are still not measured on real hardware**, which ADR-0028 requires before barge-in is relied upon, and the Voice screen says so. The keyboard routes (`Ctrl+Alt+End`, tray **Stop speaking**) do not depend on any of this. Tests: `tests/unit/test_interruption.py`, `tests/ui/test_stop_speaking.py`. |
| Expressive TTS worker isolation | PRD FR-037, FR-038 | Deferred (post-Phase 1) | Qwen3-TTS is `enabled: false` and `status: experimental`. It needs a cross-Python-version process boundary, and `multiprocessing` is denied by `tests/security/test_no_shell.py`, so it requires its own ADR. |
| Protected secret storage (DPAPI) | PRD §18.3, NFR-022, ADR-0030 | Implemented (Phase 1) | `jarvis.core.secrets`. DPAPI-protected values with unencrypted metadata beside them; ciphertext bound to the secret's name by entropy; no API returns more than one plaintext. Verified by byte-level assertions that the plaintext appears in neither `jarvis.db`, `audit.jsonl` nor `user.yaml`. Unavailable, and says so, off Windows. Tests: `tests/security/test_secret_store.py`. |
| Deletion actually deletes | PRD FR-045, FR-167, AT-013, AT-014 | Implemented (Phase 1) | `PRAGMA secure_delete` is on. Without it SQLite leaves deleted row bytes in free pages, so deleted conversation history remained readable in the vault file. Asserted by reading the vault back as bytes in `tests/acceptance/test_at014_private_session.py`. |
| Model output is never authority | PRD §11.4, §13.4, FR-040 | Implemented (Phase 1) | `ChatResponse` keeps free text and structured tool calls in separate fields and nothing promotes one into the other; a reply containing text that looks like a tool call produces no proposal. Every proposal passes the full invoker pipeline; every tool result returns to the model wrapped as an untrusted observation. Tests: `tests/integration/test_ollama_tool_calling.py`. |
| Optional audio dependencies stay optional | ADR-0010, NFR-014 | Implemented (Phase 1) | No module imports sounddevice, torch, faster-whisper, Kokoro or openWakeWord at module scope, so the engine imports on Linux with no voice stack and names what is missing instead. Enforced by `tests/security/test_lazy_audio_imports.py`. |
| Browser automation, dedicated Brave profile | PRD FR-056–FR-058, §21 (Phase 2) | Deferred (Phase 2) | Not in Phase 0 scope. |
| Windows UI Automation / desktop control, foreground-lock | PRD FR-070–FR-082, FR-077, §21 (Phase 2) | Deferred (Phase 2) | Not in Phase 0 scope. |
| Filesystem tools (root scoping, path canonicalisation) | PRD FR-204, FR-208, §21 (Phase 2) | Deferred (Phase 2) | Not in Phase 0 scope; policy defined in §11 of this document. |
| Archive extraction protections | PRD FR-200, §21 (Phase 2/3) | Deferred (Phase 2) | Not in Phase 0 scope. |
| Screen capture scoping, screenshot retention | PRD FR-073, FR-271, FR-278, §21 (Phase 2/4) | Deferred (Phase 2) | Not in Phase 0 scope. |
| Vision fallback | PRD FR-074–FR-076, §21 (Phase 4) | Deferred (Phase 4) | Not in Phase 0 scope. |
| Clipboard controls, sensitive-content exclusion | PRD FR-250–FR-259, §21 (Phase 3) | Deferred (Phase 3) | Not in Phase 0 scope. |
| Notification observation, scoping | PRD FR-260–FR-269, §21 (Phase 4) | Deferred (Phase 4) | Not in Phase 0 scope. |
| Approved-application launching | PRD FR-060, FR-063, FR-064, AT-003 | **Not implemented — gated on ADR-0029** | Every process-creation primitive is denied build-wide by `tests/security/test_no_shell.py`, whose `ALLOW_LIST` is empty. There is no way to launch an application on Windows without one, so ADR-0029 must be accepted before any launcher code exists. Until then Phase 1 exit criterion 3 is unmet, and that is recorded rather than worked around. |
| Elevation helper process | PRD FR-004, §21 | Deferred (policy accepted, ADR-0009) | `PRD.md` §21 does not explicitly assign the scoped elevation helper to a numbered phase deliverable; it must be built before any feature that requires elevation ships, whichever phase that turns out to be. Flagged as a PRD scheduling gap. |
| Signed installer / update packages | PRD NFR-024, §18.1, §18.4, §21 (Phase 6) | Deferred (Phase 6) | Not in Phase 0 scope. |
| Dependency and licence scanning (CI gate) | PRD NFR-023, §21 (Phase 0, "Repository and CI") | Partial | `.github/workflows/ci.yml` runs `pip-audit` and `pip-licenses` on every push, currently **advisory** (`continue-on-error`). Becomes blocking before the first public build (ADR-0026). |

---

## 15. Reporting security issues

Project Jarvis is currently pre-release, single-user software with no public distribution, no installed base, and no established security disclosure process.

Until a formal process is published:

- Report suspected security issues by filing an issue in this repository's issue tracker.
- Do not assume any coordinated-disclosure timeline, bug-bounty programme, or dedicated security contact exists yet — none is currently established.
- Because the product is not yet publicly distributed, there is no public-disclosure policy to follow; treat any finding as internal until this section is revised alongside a public release (`PRD.md` §21, Phase 6).

This section must be revisited and replaced with a real disclosure process before Phase 6 (Productisation) ships a signed installer to any user other than the developer.
