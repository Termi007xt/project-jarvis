# Graph Report - .  (2026-08-20)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 5203 nodes · 10352 edges · 287 communities (202 shown, 85 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 1172 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `12816206`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TaskState
- ScreenCapture
- WindowController
- TaskScheduler
- test_playback.py
- windows.py
- test_tasks.py
- test_interruption.py
- ApplicationCatalogue
- test_automation_session.py
- pipeline.py
- test_grounding_and_history.py
- Option B: Per-Stream Retention Defaults with Expiry
- FileScope
- FileWorkspace
- VoicePipeline
- AudioChunk
- test_application_launch.py
- test_close_before_force.py
- VoicePanel
- test_browser_restart_and_tabs.py
- types.py
- test_web_search_and_catalogue.py
- ConversationPanel
- JarvisApplication
- EventBus
- Database
- WindowDiscovery
- ToolCall
- tts.py
- test_user_interruption.py
- YouTubeSearchTool
- launch.py
- BrowserWorkspace
- test_phase0_exit_criteria.py
- test_window_actions.py
- AuditLog
- MainWindow
- test_window_addressing.py
- test_the_turn_finishes_the_job.py
- test_reply_speech_policy.py
- SensitiveTargets
- browser.py
- test_config.py
- main_window.py
- PlaywrightPageDriver
- ConfigStore
- JarvisTrayIcon
- stt.py
- ApprovalPanel
- system_health.py
- YouTubeAdapter
- permissions/models.py
- OllamaChatProvider
- tests/conftest.py
- ObservedList
- ApprovalQueue
- llm/conversation.py
- JarvisCore
- test_wake_install.py
- CaptureSession
- DuplexCoordinator
- test_permission_engine.py
- test_empty_model_reply.py
- schema.py
- test_read_only_tools_prove_nothing.py
- test_window_tool_wiring.py
- test_conversation_wiring.py
- BraveCdpSession
- ToolInvoker
- AppConfig
- redact
- approvals.py
- ConversationEngine
- PersonalityStore
- core.py
- speakable_text
- registry.py
- VoiceService
- test_secret_store.py
- VoiceController
- FakeBackend
- test_screen_capture.py
- VaultPaths
- test_tool_specs_are_valid.py
- test_voice_reply_behaviour.py
- test_offline_speech_models.py
- PermissionEngine
- describe_voice_stack
- youtube.py
- test_close_verification_live.py
- test_phase2_exit_criteria.py
- RingBuffer
- TtsProvider
- test_the_request_is_the_specification.py
- test_prompt_injection.py
- test_approval_dialog.py
- app.py
- SingleInstanceGuard
- test_injection_corpus.py
- Capability Risk Classes
- Observation
- test_at003_app_launch.py
- grounding.py
- ConversationStore
- OllamaHealthChecker
- test_hotkeys_and_startup.py
- test_cross_thread_marshalling.py
- test_turn_reports_what_ran.py
- test_stop_speaking.py
- test_voice_wiring.py
- Phased Delivery Plan (Phase 0-6)
- OpenWakeWordDetector
- tools/__init__.py
- test_no_shell.py
- test_prohibited_capabilities.py
- audio/capture.py
- apply_network_policy
- GlobalHotkeys
- PageDriver
- test_approval_scopes_that_stick.py
- Worker
- .start
- Local Wake Phrase Detection
- test_lazy_audio_imports.py
- test_runtime_primitives.py
- .play_cue
- unbacked_claims
- _new_core
- test_layering.py
- Jarvis Core
- ADR-0003: A Closed Capability Set — No Generic Execution Primitive
- phase2_tools.py
- QWidget
- test_at014_private_session.py
- test_ollama_tool_calling.py
- main
- On-Demand Narrowly Scoped Elevated Helper Process
- SQLite (jarvis.db) Canonical Transactional Store
- jarvis.core.events In-Process Publish/Subscribe Bus
- NetworkMode
- engine.py
- tools/ports.py
- _PermissionsPanel
- DyingSession
- Phase 2: Deterministic Desktop and Browser Automation
- Closed Enumerated Set of Narrow Typed Tools
- ._record
- Jarvis Core (Orchestration)
- claims_completion
- media.py
- WindowBackend
- .__init__
- offerable_scopes_for
- OllamaHealth
- startup.py
- PywinautoBackend
- test_browser_attach.py
- ConfigStore
- Project Jarvis (Windows Local AI Desktop Agent)
- hotkeys.py
- PeriodicWorker
- Model Resource Scheduler (VRAM Arbitration)
- denial_options_for
- WorkerSupervisor
- WindowActionBackend
- Path
- test_no_elevation.py
- configure_logging
- .set_setting
- AutoApprovalPort
- .emergency_stop_from_hotkey
- FakeSounddevice
- ADR-0034: File Opening Policy
- ADR-0008: Secret Storage Deferred to Phase 1
- ADR-0013: Installer Technology
- Never Claim Unverified Success
- generate_voice_sample
- .describe
- Arc Reactor Visual Motif
- .__init__
- HotkeyBinding
- DenyingApprovalPort Default Implementation
- never_open_the_speakers
- Memory Candidate Review Pipeline
- single_instance.py
- .send_message
- Brave Browser
- ADR-0029: Launching Approved Applications
- .__init__
- .__init__
- ToolResult
- test_whisper.py
- .calibrate_from
- test_the_library_itself_is_told_not_only_the_environment
- .describe_interruption
- YouTubeUnavailable
- ._persist_setting
- test_enabling_then_disabling_leaves_no_entry
- ADR-0016: Custom "Jarvis" Wake Word
- ADR-0033: Turn Continuation Policy
- InstallReport
- model_validator
- vault_free_bytes
- fake_ollama
- test_a_browser_tool_owns_the_desktop
- CI dependency and licence review job
- CI headless self-check step (jarvis.main --check)
- EventBridge
- P2-WIN-04: Input Ownership
- espeak-ng Pronunciation Backend
- Target Hardware Profile
- Phase 0 Scope Statement
- core/__init__.py
- llm/__init__.py
- test_an_unparseable_hotkey_is_reported_not_raised
- QT_QPA_PLATFORM=offscreen in CI
- CI security-invariants job
- CI test job (Windows + Ubuntu, Python 3.11/3.12)
- Any
- ApprovalPort
- BaseModel
- Shipped Defaults
- Conversation
- ConversationEngine
- Audit JSONL File
- Jarvis SQLite Database
- ADR-0018: Search Provider
- ADR-0023: Adapter Isolation
- ADR-0031: Browser Attachment Policy
- Phase 1 — User Acceptance Testing
- Phase 0 Report — Foundation and Safety Architecture
- DuplexCoordinator
- Browser wakes other tabs
- model_validator
- project-jarvis
- Automation Safety Defaults
- faster-whisper Speech Recognition
- Privacy Defaults (telemetry off, no raw audio)
- Qwen3-TTS Expressive Provider (deferred)
- Rust Deferred Until After Phase 3
- Wake Word Policy (Hey Jarvis now, Jarvis desired)
- Windows SAPI Fallback Voice
- Protocol
- QWidget
- How to Add a Capability
- RingBuffer
- SourceLabel
- AudioChunk
- AudioChunk
- Enum
- str
- AudioChunk
- AudioChunk
- Capability
- RiskLevel
- AuditLog
- Database
- EventBus
- RiskLevel
- ConfigStore
- NetworkMode
- VaultPaths
- Exception
- Path
- RuntimeError
- ValueError
- ApplicationCatalogue
- QObject
- WINDOWS_ONLY
- fixture
- NetworkMode
- AudioChunk
- AudioChunk
- parametrize
- AudioChunk
- ApplicationCatalogue
- ToolExecution
- ToolInvoker
- Turn
- Verification
- VoiceActivityDetector
- VoiceStackStatus
- WakeEvent

## God Nodes (most connected - your core abstractions)
1. `JarvisCore` - 99 edges
2. `ToolCall` - 74 edges
3. `AudioChunk` - 72 edges
4. `WindowDiscovery` - 72 edges
5. `JarvisApplication` - 64 edges
6. `WindowController` - 61 edges
7. `Database` - 59 edges
8. `DuplexCoordinator` - 55 edges
9. `EventBus` - 54 edges
10. `BrowserWorkspace` - 53 edges

## Surprising Connections (you probably didn't know these)
- `test_availability_names_the_missing_component_rather_than_failing()` --calls--> `describe_voice_stack()`  [INFERRED]
  tests/security/test_lazy_audio_imports.py → src/jarvis/audio/availability.py
- `test_an_empty_name_falls_back_to_you()` --calls--> `ConversationPanel`  [INFERRED]
  tests/ui/test_voice_reply_behaviour.py → src/jarvis/ui/conversation.py
- `test_setting_the_name_programmatically_does_not_re_emit()` --calls--> `ConversationPanel`  [INFERRED]
  tests/ui/test_voice_reply_behaviour.py → src/jarvis/ui/conversation.py
- `test_environment_override_is_not_persisted()` --calls--> `ConfigStore`  [EXTRACTED]
  tests/unit/test_config.py → src/jarvis/config/store.py
- `test_environment_values_are_parsed_as_yaml_scalars()` --calls--> `ConfigStore`  [EXTRACTED]
  tests/unit/test_config.py → src/jarvis/config/store.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Phase 2 Automation Tools** — changelog_window_arrange, changelog_window_list, changelog_app_close, changelog_app_force_close, changelog_browser_restart [EXTRACTED 1.00]
- **Phase 2 Security Controls** — docs_backlog_p2_brw_06, docs_backlog_p2_win_04, docs_backlog_p2_win_05, changelog_app_force_close [INFERRED 0.90]
- **Jarvis Runtime Components** — architecture_md_jarvis_shell, architecture_md_jarvis_core, architecture_md_audio_worker, architecture_md_automation_worker, architecture_md_task_scheduler, architecture_md_data_vault [EXTRACTED 1.00]
- **Tool Execution Pipeline** — architecture_md_tool_invoker, architecture_md_permission_engine, architecture_md_lock_manager, architecture_md_audit_log [EXTRACTED 1.00]
- **Security and Safety Framework** — security_md_untrusted_data_rule, threat_model_md_stride, architecture_md_permission_engine, architecture_md_audit_log [INFERRED 0.80]
- **Browser Automation Security Boundary** — docs_decisions_adr_0019, docs_decisions_adr_0032 [EXTRACTED 0.95]
- **Data Persistence Layer** — data_model_md_jarvis_db, data_model_md_audit_jsonl [EXTRACTED 0.85]
- **Phase 1 Security Architecture** — docs_decisions_adr_0027_approval_and_activation_interaction_model_md, docs_decisions_adr_0029_approved_application_launch_md, docs_decisions_adr_0030_secret_store_mechanism_md [EXTRACTED 0.90]
- **Phase 2 Browser Automation Strategy** — docs_decisions_adr_0031_browser_automation_attaches_over_cdp_md, docs_phase_plans_phase_02_plan_md [EXTRACTED 0.95]
- **Six-Role Agent Pipeline (Converse, Plan, Execute, Observe, Verify, Curate)** — prd_conversation_agent, prd_planner, prd_executor, prd_observer, prd_verifier, prd_memory_curator [EXTRACTED 1.00]
- **Jarvis Process Model (Shell, Core, Audio, Automation, Scheduler)** — prd_jarvis_shell, prd_jarvis_core, prd_audio_worker, prd_automation_worker, prd_task_scheduler_process, prd_local_ipc [EXTRACTED 1.00]
- **Guardrail and Permission Stack** — prd_capability_risk_classes, prd_approval_design, prd_audit_log, prd_prompt_injection_defence, prd_emergency_stop, prd_prohibited_broad_tools, prd_structured_model_output [EXTRACTED 1.00]
- **TTS Provider Stack and GPU Resource Arbitration** — docs_decisions_adr_0015_additional_tts_providers_ttsprovider_interface, docs_decisions_adr_0014_default_english_voice_kokoro_bm_george, docs_decisions_adr_0014_default_english_voice_windows_sapi_fallback, docs_decisions_adr_0015_additional_tts_providers_qwen3_tts_isolated_worker, docs_decisions_adr_0015_additional_tts_providers_model_resource_scheduler, docs_decisions_adr_0017_embedding_model_qwen3_embedding_0_6b [EXTRACTED 1.00]
- **Artefact Trust and Provenance Chain** — docs_decisions_adr_0026_code_signing_and_updates_signature_verification_before_execution, docs_decisions_adr_0026_code_signing_and_updates_ov_manual_updates, docs_decisions_adr_0020_plugin_and_skill_signing_signed_manifest_field, docs_decisions_adr_0020_plugin_and_skill_signing_jarvispack_import, docs_decisions_adr_0022_msix_distribution_msix_secondary_channel, docs_decisions_adr_0014_default_english_voice_redistribution_licensing_gap [INFERRED 0.85]
- **Vault Data Lifecycle and Exposure Control** — docs_decisions_adr_0024_data_retention_defaults_per_stream_defaults, docs_decisions_adr_0024_data_retention_defaults_cascade_on_expiry, docs_decisions_adr_0025_screenshot_retention_task_only_default, docs_decisions_adr_0021_encrypted_sync_and_backup_secret_exclusion_rule, docs_decisions_adr_0021_encrypted_sync_and_backup_portable_identity_export, docs_decisions_adr_0017_embedding_model_rebuildable_derived_index [EXTRACTED 1.00]
- **Arc Reactor Icon Composition (chassis + core + emissive palette)** — resources_icons_jarvis_icon, resources_icons_jarvis_icon_circular_chassis, resources_icons_jarvis_icon_triangular_core, resources_icons_jarvis_icon_cyan_glow_palette [EXTRACTED 1.00]
- **Windows Shell Asset Readiness Constraints** — resources_icons_jarvis_icon, resources_icons_jarvis_icon_transparent_alpha_canvas, resources_icons_jarvis_icon_circular_chassis, resources_icons_jarvis_icon_product_brand_identity [INFERRED 0.75]
- **Phase 0 Structural Enforcement Mechanisms (Tests and Schema Guards)** — docs_decisions_adr_0003_closed_capability_set_no_generic_execution_test_no_shell_scan, docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_test_layering, docs_decisions_adr_0006_layered_configuration_override_only_persistence_extra_forbid, docs_decisions_adr_0002_sqlite_single_source_of_truth_schema_version_startup_check, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_no_elevation_manifest_check [INFERRED 0.85]
- **Process-Separation Promotion Path and Its Triggers** — docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_single_process_worker_threads, docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_process_promotion_triggers, docs_decisions_adr_0001_python_first_rust_deferred_qwen3_tts_worker, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_scoped_helper_process, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_helper_ipc_discipline, docs_decisions_adr_0001_python_first_rust_deferred_typed_ipc [EXTRACTED 1.00]
- **Open Phase 6 Productisation Decisions** — docs_decisions_adr_0011_public_product_name_adr, docs_decisions_adr_0012_shell_technology_for_first_public_build_adr, docs_decisions_adr_0013_installer_technology_adr, docs_decisions_adr_0013_installer_technology_msix_sequencing_dependency, docs_decisions_adr_0011_public_product_name_trademark_screen_criteria [EXTRACTED 1.00]

## Communities (287 total, 85 thin omitted)

### Community 0 - "TaskState"
Cohesion: 0.06
Nodes (55): from_iso(), json_dumps(), json_loads(), new_id(), Any, datetime, Small shared primitives used across every layer. Kept deliberately tiny:…, A fresh opaque identifier. UUID4 hex, no dashes, stable length. (+47 more)

### Community 1 - "ScreenCapture"
Cohesion: 0.04
Nodes (55): CaptureRefused, CaptureResult, default_capture_directory(), _BitmapInfoHeader, GdiCanvas, PathLike, The real screen grab, via GDI (FR-073, P2-WIN-10). Windows only, imported…, Paint a rectangle black, in place, before anything is saved. Clipped to the… (+47 more)

### Community 2 - "WindowController"
Cohesion: 0.08
Nodes (53): AppCloseInput, AppCloseOutput, AppCloseTool, AppForceCloseInput, AppForceCloseTool, _close_execution(), _guarded(), BaseModel (+45 more)

### Community 3 - "TaskScheduler"
Cohesion: 0.05
Nodes (36): One unit of work with a durable state machine., Task, Any, BaseModel, Enum, Protocol, str, What a task actually does. Runners are the extension point that later phases… (+28 more)

### Community 4 - "test_playback.py"
Cohesion: 0.05
Nodes (56): _as_float_array(), default_output_device(), play(), playback_available(), playback_unavailable_reason(), PlaybackReport, Audio playback (PRD FR-030, FR-033, ADR-0028). The missing half of the voice…, Decode the chunk's bytes into the float32 mono array a stream wants. (+48 more)

### Community 5 - "windows.py"
Cohesion: 0.05
Nodes (43): CloseOutcome, CloseReport, Enum, str, Moving windows (FR-241, FR-242, FR-243, P2-WIN-09). Phase 2 stage 4, the acting…, What was asked of a window, and what it did about it., The real backend, via ctypes. Windows only. Every call here is a *request* to…, Which window actually has the foreground, according to Windows. (+35 more)

### Community 6 - "test_tasks.py"
Cohesion: 0.06
Nodes (47): Release everything this runtime holds. Called during shutdown., Exclusive, persisted, owner-attributed locks., ResourceLockManager, CRUD plus a validated state machine over the ``task`` tables., TaskStore, Task state machine, durable store, locks and scheduler (PRD FR-120 .. FR-133)., A partial acquisition would deadlock two tasks against each other., PRD FR-006: a crash while holding a lock must not wedge the resource. (+39 more)

### Community 7 - "test_interruption.py"
Cohesion: 0.08
Nodes (31): configured_duplex_mode(), The voice service: one object that owns the whole audio stack (L3). Built even…, Read ``audio.duplex_mode``, degrading rather than over-claiming. Anything…, _detection(), _frame(), Interrupting Jarvis mid-sentence — why it never worked, and what fixed it.…, A loud synthesised waveform must not raise the bar for the user., A shout during one reply must not deafen Jarvis for the next. (+23 more)

### Community 8 - "ApplicationCatalogue"
Cohesion: 0.11
Nodes (45): ApplicationCatalogue, ArgumentKind, CatalogueError, launch(), LaunchKind, Enum, str, Start an application and **verify** it started (constraint 9, FR-064).… (+37 more)

### Community 9 - "test_automation_session.py"
Cohesion: 0.06
Nodes (39): AutomationSession, DesktopBusy, LockManagerLike, Any, Protocol, RuntimeError, Owning the desktop before moving anything (FR-077, FR-078, P2-WIN-03/04/05).…, Perform one action, if the user has not taken over. ``sends_input`` must be… (+31 more)

### Community 10 - "pipeline.py"
Cohesion: 0.06
Nodes (37): ActivationRoute, CommandHeard, _join(), ListeningState, Enum, str, The voice loop (PRD sections 10.2 to 10.4, ADR-0027, ADR-0028). One place where…, F9 released. Transcribe what was captured. (+29 more)

### Community 11 - "test_grounding_and_history.py"
Cohesion: 0.05
Nodes (50): ChatProvider, ConversationStore, PersonalityStore, Label a reply and stop it claiming an unverified success. ``tool_results`` are…, review_response(), FakeResult, Source labelling, tool-grounded success, history and personality. PRD FR-045,…, AT-018: never report completed when it could not be verified. (+42 more)

### Community 12 - "Option B: Per-Stream Retention Defaults with Expiry"
Cohesion: 0.05
Nodes (55): ADR-0014: Default English Voice, espeak-ng GPL-Family Licensing Consideration, Kokoro bm_george Default Voice, Per-Download Provider and Licence Disclosure, Voice Pack Redistribution Licensing Gap, Windows SAPI Emergency Fallback, ADR-0015: Additional TTS Providers, Model Resource Scheduler (FR-039) (+47 more)

### Community 13 - "FileScope"
Cohesion: 0.07
Nodes (52): as_observed_list(), FileMatch, FileScope, ObservedList, The folders the user has approved. Nothing outside them is reachable., One file the search found. ``name`` is untrusted content., Find files whose names match, inside the approved scope only. Bounded twice, by…, Hand results onward as untrusted, positionally-addressed content. File names… (+44 more)

### Community 14 - "FileWorkspace"
Cohesion: 0.08
Nodes (41): PermissionError, PathRefused, The path is outside everything the user has approved., FileFindInput, FileFindOutput, FileFindTool, FileOpenInput, FileOpenOutput (+33 more)

### Community 15 - "VoicePipeline"
Cohesion: 0.07
Nodes (31): Begin waiting for the wake phrase, if enrolment allows it., Stop, and forget everything held. Nothing survives in memory., F9 pressed. Capture a command without a wake phrase (FR-018)., One captured frame. Called from the audio thread., Only ever enabled after enrolment has been measured (ADR-0016)., Capture in, commands out. Owns the listening state machine., VoicePipeline, NullWakeDetector (+23 more)

### Community 16 - "AudioChunk"
Cohesion: 0.06
Nodes (34): Cue, cue_audio(), _faded(), Short audio cues, so Jarvis is legible without looking at the screen. The…, The cues this build makes, and what each one means., Render one cue, or None if numpy is unavailable or the name is unknown. Never…, Taper both ends, or the tone starts and stops with a click., Record how loud Jarvis's own output was. Reported, not compared. (+26 more)

### Community 17 - "test_application_launch.py"
Cohesion: 0.06
Nodes (43): ApplicationEntry, build_argv(), _normalise_name(), One application the user has approved Jarvis to open. Created by the user,…, Fold the separators a model guesses between, and nothing else. "youtube-music",…, Refuse an unsafe catalogue entry at registration time (constraint 4)., Constraint 5: validate the caller's argument against the entry's type., Construct the argument vector. Pure, so it is directly testable. (+35 more)

### Community 18 - "test_close_before_force.py"
Cohesion: 0.06
Nodes (36): The real backend, via ctypes. Windows only. Deliberately not a process-listing…, Which window has the foreground, according to Windows. A read, so it belongs…, Whether this is still a window at all — `IsWindow`, nothing else. A different…, Win32WindowBackend, _controller(), FakeActions, FakeBackend, Closing an application: ask, notice when it objects, and never escalate. Phase… (+28 more)

### Community 19 - "VoicePanel"
Cohesion: 0.05
Nodes (30): QWidget, Always show the exact destination path, installed or not., State the phrase literally. Never label it 'Jarvis' (FR-011)., Show what has been measured. Never imply more than that., Listening needs the wake model and a microphone — nothing more. ADR-0016…, Show the transcript, so a misheard word is visibly a mishearing., Say plainly whether the microphone is open (PRD FR-013)., True if anything on this screen implies bare "Jarvis" works. FR-011 forbids… (+22 more)

### Community 20 - "test_browser_restart_and_tabs.py"
Cohesion: 0.05
Nodes (39): Exception, quit_browser(), Close the browser gracefully and confirm it actually exited. Returns whether it…, BrowserRestartTool, Close Brave and reopen it ready for automation (ADR-0032). This exists because…, _context(), FakePage, _FakeSession (+31 more)

### Community 21 - "types.py"
Cohesion: 0.07
Nodes (39): LookupError, AppStarted, AppStopping, AuditRecorded, ConfigChanged, EmergencyStopCompleted, EmergencyStopRequested, Event (+31 more)

### Community 22 - "test_web_search_and_catalogue.py"
Cohesion: 0.05
Nodes (47): default_catalogue(), The Phase 1 seed: exactly the applications PRD section 21 names. Paths are the…, PRD section 21: Brave, YouTube, YouTube Music, Xbox, Sea of Thieves., Otherwise a launch could only ever be reported as unverified., A composed path with '..' in it resolved somewhere nonsensical., Defect 2: the model called `web.open_url` for "open YouTube Music". Both tools…, Defect 3: "play Sunflower on YouTube Music" failed with only a refusal.…, test_an_unsupported_argument_says_what_can_be_done_instead() (+39 more)

### Community 23 - "ConversationPanel"
Cohesion: 0.06
Nodes (30): ConversationPanel, ConversationWorker, _escape(), QObject, QWidget, The Conversation screen (PRD section 9.5, FR-045, FR-046, FR-047). Two things…, Enable or disable input, and say exactly why when disabled. The window…, Persisted, so it survives a restart; blank falls back to "You". (+22 more)

### Community 24 - "JarvisApplication"
Cohesion: 0.05
Nodes (20): Event, QObject, JarvisApplication, Runs on the audio thread, so it only queues work onto the GUI one., Runs on the Qt main thread, courtesy of the bridge., Answered from the Permissions screen rather than the panel., Derive the tray state from what the runtime is actually doing., Stop the in-flight turn's thread before the process goes away. Exiting with it… (+12 more)

### Community 25 - "EventBus"
Cohesion: 0.07
Nodes (28): E, EventBus, In-process typed event bus (ADR-0005). Deliberately not a message broker: no…, Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe., Thread-safe publish/subscribe with subclass matching., Receive ``event_type`` and every subclass of it., Deliver to every matching handler. Returns the number invoked. Handler…, Subscription (+20 more)

### Community 26 - "Database"
Cohesion: 0.08
Nodes (29): Connection, Cursor, datetime, Row, Conversation history and private sessions (PRD FR-045, FR-046, AT-014). A…, StoredMessage, Database, DatabaseError (+21 more)

### Community 27 - "WindowDiscovery"
Cohesion: 0.09
Nodes (31): ObservedList, Lists windows. Changes nothing. Deliberately has no `activate`, `move`, `close`…, The stable token for a window, minted on first sight. Stable across listings,…, The handle a reference names, or a clear refusal. Both failures matter and are…, Every visible top-level window, in enumeration order. Dialogs are left out by…, Does this window still exist? Not: is it still on screen. `list_windows`…, The window the user is actually looking at, or None (FR-270). Returns None…, Hand the desktop onward as untrusted, positionally-addressed content. (+23 more)

### Community 28 - "ToolCall"
Cohesion: 0.10
Nodes (45): RetryPolicy, A proposed action. Comes from the planner, the GUI, a skill or a schedule., ToolCall, allow(), make_tool(), Params, BaseModel, RiskLevel (+37 more)

### Community 29 - "tts.py"
Cohesion: 0.06
Nodes (24): Load the speech models now, so the first command is not the slow one. Both…, build_tts_provider(), KokoroTtsProvider, NullTtsProvider, prepare_for_speech(), Text to speech (PRD FR-030 to FR-034, ADR-0014, ADR-0015). Kokoro `bm_george`…, Make text legible aloud, then remove anything secret-shaped. Order matters:…, No voice available. Says why, and never pretends to speak. (+16 more)

### Community 30 - "test_user_interruption.py"
Cohesion: 0.06
Nodes (31): last_user_input_tick_ms(), monotonic_tick_ms(), Noticing that the user has taken the desktop back (FR-078, AT-008). Phase 2…, Start watching from now. Forgets anything observed before., Record that *we* just sent input, so it is not read as the user's. Call this…, Whether the user has touched the desktop since `arm()`. Raises rather than…, A millisecond tick from the same family as Win32's `GetTickCount`., When Windows last saw any input, or ``None`` where it cannot be asked. Uses… (+23 more)

### Community 31 - "YouTubeSearchTool"
Cohesion: 0.09
Nodes (40): Search YouTube in the dedicated profile and read back the results., Play a result by position, and confirm it is actually playing., Register the browser tools. Returns what was registered., register_phase2_tools(), YouTubePlayInput, YouTubePlayTool, YouTubeSearchInput, YouTubeSearchTool (+32 more)

### Community 32 - "launch.py"
Cohesion: 0.07
Nodes (38): _basename(), launch_argv(), LaunchOutcome, process_running(), The one authorised process-creation call site (ADR-0029). Everything about this…, What actually happened. ``verified`` is never assumed (constraint 9)., Whether any named process exists (constraint 9, verification). Uses the Windows…, FR-048 and AT-018: launched is not the same as running. (+30 more)

### Community 33 - "BrowserWorkspace"
Cohesion: 0.06
Nodes (28): BrowserWorkspace, Close the browser and release the thread. Safe to call twice., Inject an adapter directly. Used by tests and by an open session., Open a session, and hand it back only if it is still wanted.…, Whether the browser we attached to is still there. Reported from real use,…, The adapter, opening the browser if it is not already open. Opening happens on…, Open *and* still alive. A dead session must not report as open., Shut the browser down. Idempotent, and safe to call during teardown. Not… (+20 more)

### Community 34 - "test_phase0_exit_criteria.py"
Cohesion: 0.05
Nodes (35): AppConfig, Phase 0 exit criteria and hard constraints. One test (or small group) per…, The tool set stays small and low risk. Phase 0 registered exactly one tool.…, Two tools exist only when something can show the user what happened.…, PRD FR-048: succeeded requires verification, so it must be declared., PRD section 13.4: free-form text can never be executed., A scan that was just narrowed must be shown to still detect something. The…, PRD section 4.4: nothing may silently become permanent memory. (+27 more)

### Community 35 - "test_window_actions.py"
Cohesion: 0.11
Nodes (33): _controller(), _desktop(), FakeActionBackend, FakeBackend, parametrize, Moving windows: refused where it must be, and never assumed to have worked.…, The reference for the nth window, the way `window.list` hands it out. Tests…, AT-031, reached the way the product reaches it. (+25 more)

### Community 36 - "AuditLog"
Cohesion: 0.09
Nodes (28): Audit logging and secret redaction., AuditLog, Any, datetime, Path, Every record from the JSONL file, oldest first., Search the SQLite index. Falls back to the JSONL file if unavailable., Write an export copy of the audit log (PRD section 11.5). (+20 more)

### Community 37 - "MainWindow"
Cohesion: 0.07
Nodes (29): QMainWindow, MainWindow, Navigation shell over live core state., Closing the window leaves Jarvis running in the tray (PRD FR-001)., test_the_window_says_plainly_when_nothing_is_waiting(), test_conversation_is_a_live_area_not_a_phase_placeholder(), test_the_home_screen_reports_the_voice_stack_honestly(), fixture (+21 more)

### Community 38 - "test_window_addressing.py"
Cohesion: 0.09
Nodes (31): is_shell_window(), is_user_facing(), Whether a person would call this an open window. Reported 2026-08-05: eleven…, Whether this is the desktop itself rather than something on it., FakeActions, FakeBackend, Naming a window so that the name still means it when the action runs. Three…, Otherwise the model is handed a new name for the same thing each time. (+23 more)

### Community 39 - "test_the_turn_finishes_the_job.py"
Cohesion: 0.13
Nodes (34): ChatResponse, _conversation(), _engine(), _proposal(), A turn does not end on a promise (FR-048, FR-123, ADR-0033). Reported by the…, The whole point. The model said it would; the turn makes it., Done, Sir" with no tool is the same failure wearing the other tense., The same case, end to end: it must not stop after opening. (+26 more)

### Community 40 - "test_reply_speech_policy.py"
Cohesion: 0.09
Nodes (36): Enum, parametrize, _asks_something(), When a spoken request deserves a spoken answer (PRD FR-030, FR-048). Answering…, The user-facing setting, ``audio.speak_replies``., What the shell should do with a finished reply., Decide how a finished turn should sound. ``spoken_request`` is the whole reason…, ReplyVoice (+28 more)

### Community 41 - "SensitiveTargets"
Cohesion: 0.07
Nodes (33): What automation must refuse to touch (FR-079, FR-080, FR-081, AT-031). Phase 2…, The blocklist. Refuses; never grants. Both lists are configurable, because what…, Decide whether this window may be automated or captured. Process first and by…, Blank the contents of password fields, keeping every position (FR-080). In…, Whether Windows has switched to a secure desktop (FR-079). A UAC prompt, the…, Whether a target may be automated or captured, and what decided it., redact_password_fields(), secure_desktop_active() (+25 more)

### Community 42 - "browser.py"
Cohesion: 0.07
Nodes (32): ApplicationEntry, Path, brave_user_data_dir(), browser_windows(), BrowserNeedsRestart, BrowserUnavailable, _cdp_banner(), close_window() (+24 more)

### Community 43 - "test_config.py"
Cohesion: 0.07
Nodes (25): Configuration layer (L1). Must not import anything above L1., expand_path(), find_defaults_config(), _platform_default_root(), Data-vault path resolution. This is the *only* module permitted to expand…, Locate the shipped ``defaults.yaml``. Order: ``JARVIS_DEFAULTS_CONFIG`` env…, Expand ``%VARS%``, ``$VARS`` and ``~`` then normalise to an absolute path., Path (+17 more)

### Community 44 - "main_window.py"
Cohesion: 0.12
Nodes (32): ArgumentParser, install_wake_model(), installed_files(), is_installed(), missing_files(), model_directory(), Path, One-time wake-word model installation (ADR-0016, PRD section 17.2). **No wake-… (+24 more)

### Community 45 - "PlaywrightPageDriver"
Cohesion: 0.09
Nodes (21): RuntimeError, BrowserThreadViolation, PlaywrightPageDriver, Any, `PageDriver` against a real page. Positional throughout. Note what is absent:…, Refuse, legibly, rather than fail illegibly somewhere else later.…, Undo Playwright's own emulation, so this looks like the owner's tab. Playwright…, The page, replaced if the owner closed it. Reported 2026-08-05 as *"the YouTube… (+13 more)

### Community 46 - "ConfigStore"
Cohesion: 0.12
Nodes (23): _atomic_write(), ConfigError, ConfigStore, deep_merge(), _delete_by_path(), _env_overrides(), _get_by_path(), _parse_env_value() (+15 more)

### Community 47 - "JarvisTrayIcon"
Cohesion: 0.07
Nodes (21): ActivationReason, QAction, QMenu, QSystemTrayIcon, JarvisTrayIcon, QObject, Colour, shape, tooltip and accessible name all change together., Enable the keyboard route and say how many are waiting. (+13 more)

### Community 48 - "stt.py"
Cohesion: 0.07
Nodes (23): AudioChunk, build_stt_provider(), diagnostic_audio_path(), FasterWhisperSttProvider, _letters(), NullSttProvider, Path, Speech to text (PRD FR-020 to FR-025). faster-whisper `small`, CPU, `int8`,… (+15 more)

### Community 49 - "ApprovalPanel"
Cohesion: 0.10
Nodes (19): PendingApproval, One unanswered request. Mutable, unlike everything on the event bus., ApprovalController, ApprovalPanel, Decision, GrantScope, QObject, QWidget (+11 more)

### Community 50 - "system_health.py"
Cohesion: 0.12
Nodes (28): BaseModel, Enum, Exception, str, The tool contract (PRD section 13.2). A *tool* is the only way the agent…, Per-invocation context handed to a tool. Carries no ambient authority., What a tool returns on success., Raised by a tool to report a declared failure. The code must be declared. (+20 more)

### Community 51 - "YouTubeAdapter"
Cohesion: 0.09
Nodes (26): Search YouTube, then play a result by position., YouTubeAdapter, adapter(), FakePage, no_sleep(), page(), fixture, AT-006: "search RTX 5070 on YouTube", then "play the second video". Phase 2… (+18 more)

### Community 52 - "permissions/models.py"
Cohesion: 0.09
Nodes (30): Capability, RiskLevel, _c(), capabilities_by_risk(), capability(), capability_ids(), The capability catalogue — PRD section 11.1 expressed as data. Risk…, Permission model, capability catalogue and evaluation engine. (+22 more)

### Community 53 - "OllamaChatProvider"
Cohesion: 0.09
Nodes (25): _as_int(), _neutralise_delimiters(), OllamaChatProvider, Any, Ollama chat completion (PRD FR-040, section 13.4, ADR-0007). Inherits the two…, Read only the structured field. Never parse prose for an action., Describe one registered tool in the format Ollama expects. Built from the…, The instruction that accompanies every wrapped observation. (+17 more)

### Community 54 - "tests/conftest.py"
Cohesion: 0.15
Nodes (33): ResourceLockManager, TaskScheduler, TaskStore, approving_invoker(), audit(), config(), config_store(), core() (+25 more)

### Community 55 - "ObservedList"
Cohesion: 0.09
Nodes (25): ContentClass, ObservedItem, ObservedList, BaseModel, Enum, str, Observed content — the only shape external data may take (PRD §11.4).…, One element of an observed, ordered list. ``label`` is attacker-controlled text… (+17 more)

### Community 56 - "ApprovalQueue"
Cohesion: 0.13
Nodes (28): ApprovalQueue, Called whenever the pending set changes. Used by the tray., Holds requests between the thread that needs an answer and the user. Implements…, make_request(), fixture, RiskLevel, queue(), The approval queue (ADR-0027). The timeout path is the security-critical one… (+20 more)

### Community 57 - "llm/conversation.py"
Cohesion: 0.09
Nodes (26): ChatMessage, _describe_result(), _exhaustion_message(), Any, Conversation, The conversation engine (PRD FR-040, FR-042, FR-047, FR-048, section 13.4).…, An identity for one spoken or typed request. "Allow for this task" was offered…, Send one proposal through the invoker. Never around it. (+18 more)

### Community 58 - "JarvisCore"
Cohesion: 0.09
Nodes (24): RecoveryReport, JarvisCore, Everything except the user interface., Let the shell supply what only it can: notifications, and the light.…, Open Brave on the dedicated Jarvis profile, attached over CDP. The browser is…, Reverse of start, and idempotent., Queue a health check through the task machinery. Returns the task id., Full core lifecycle, crash recovery and settings durability. (+16 more)

### Community 59 - "test_wake_install.py"
Cohesion: 0.11
Nodes (29): slow, make_files(), Path, The wake-model bootstrap (ADR-0016, PRD section 17.2). No test here downloads…, A corrupt download must not be reported as ready (ADR-0010)., The command's exit code reflects usability, not download success., Hey Travis" measured 0.489, so 0.5 left almost no margin., ONNX on Windows; the library's own default is tflite. (+21 more)

### Community 60 - "CaptureSession"
Cohesion: 0.08
Nodes (20): CaptureSession, An open microphone. Frames arrive on the audio thread. Use as a context manager…, The settings to try, best first, for whichever device was chosen. A WASAPI…, parametrize, Opening the microphone must match the device's host API (PRD FR-016). Windows…, ADR-0028 defence 2 — echo cancellation is why WASAPI is preferred., FR-013 in reverse: the indicator must not survive a failed start., Windows' default was MME, which gives no echo cancellation. (+12 more)

### Community 61 - "DuplexCoordinator"
Cohesion: 0.04
Nodes (52): BargeInReport, DuplexCoordinator, DuplexMode, PlaybackWindow, datetime, Enum, str, Full-duplex audio and barge-in (ADR-0028, PRD FR-015, section 11.3). ADR-0028… (+44 more)

### Community 62 - "test_permission_engine.py"
Cohesion: 0.10
Nodes (28): PermissionRequest, A question put to the permission engine. Contains no side effects., parametrize, Permission evaluation (PRD sections 9.9 and 11.1, ARCHITECTURE.md 6.4)., A user who denied something should not be asked again in the same scope., PRD 11.1: fresh confirmation every time., PRD 9.9: high-risk permissions must not offer 'always allow'., test_a_deny_grant_outranks_an_allow_grant() (+20 more)

### Community 63 - "test_empty_model_reply.py"
Cohesion: 0.11
Nodes (24): _describe_silence(), What to say when the model returned no words at all. It happens: a small model…, Conversation, One conversation, persisted or not., _conversation(), _engine(), NoopInvoker, parametrize (+16 more)

### Community 64 - "schema.py"
Cohesion: 0.12
Nodes (28): AudioConfig, _Base, ConversationLanguageConfig, DefaultPermissionPolicy, LanguageConfig, LlmConfig, LoggingConfig, ModelProfile (+20 more)

### Community 65 - "test_read_only_tools_prove_nothing.py"
Cohesion: 0.09
Nodes (28): _Empty, _Listing, OverclaimingReadOnlyTool, BaseModel, ToolExecution, Verification, Listing something is not doing something (FR-047, FR-048, AT-018). Reported by…, The invariant, at the one place every effect passes through. The mirror of the… (+20 more)

### Community 66 - "test_window_tool_wiring.py"
Cohesion: 0.09
Nodes (27): _context(), _first_ref(), The window tools are connected to a real desktop, or say why they are not. This…, ADR-0010: name what is not possible. "What's on my screen" is a question about…, The foreground may be the desktop, or a window the listing filters out. Naming…, The blocklist is the same one the listing and the actions use., The seam itself. Without a controller the arrange tool is registered, enabled,…, One discovery, not two. Two instances would drift: the listing the model was… (+19 more)

### Community 67 - "test_conversation_wiring.py"
Cohesion: 0.11
Nodes (24): One user request and everything that came of it., Turn, application(), ExplodingEngine, FakeEngine, _pump(), fixture, The wiring between the Conversation screen and the engine. The panel tests… (+16 more)

### Community 68 - "BraveCdpSession"
Cohesion: 0.10
Nodes (20): BraveCdpSession, A Brave we started, attached to over CDP, and close when done. Used as a…, Whether the browser we attached to is still running. Attached is not alive: the…, Opening the browser session: fail fast, say why, and never leak a port. All…, ADR-0031: the port is a control channel, not diagnostic detail., `DevToolsActivePort` survives a crash, so it is a hint, not a fact., Ending a Jarvis session must not take the user's tabs with it. Re-attaching…, The other half: what Jarvis started, Jarvis closes (ADR-0031). (+12 more)

### Community 69 - "ToolInvoker"
Cohesion: 0.15
Nodes (15): ApprovalRequest, AuditCategory, Any, BaseModel, ToolContext, ToolExecution, Verification, Make "don't ask again" stick, as a scoped DENY grant (ADR-0027). No engine… (+7 more)

### Community 70 - "AppConfig"
Cohesion: 0.10
Nodes (16): field_validator, AppConfig, The whole validated configuration tree., ModelRole, str, Which configured model profile a request should use (PRD FR-041)., ModelBusyError, ModelRouter (+8 more)

### Community 71 - "redact"
Cohesion: 0.11
Nodes (26): classify_content(), is_content_key(), is_secret_key(), Any, Secret redaction for the audit log (PRD section 11.5, FR-259). Redaction…, Return a copy of ``value`` safe to persist in the audit log. Mappings,…, Describe a value without reproducing it. Used where the *shape* of user content…, Redact secret-looking substrings, then bound the length. (+18 more)

### Community 72 - "approvals.py"
Cohesion: 0.11
Nodes (18): ApprovalRequested, ApprovalResolved, A tool is waiting on the user. The tray must make this impossible to miss.…, Decision, GrantScope, The approval queue — step 5 of the invoker pipeline, made answerable. ADR-0027…, Declare whether a user interface is actually connected. Until one is, queueing…, Block the calling thread until answered, or until the request expires. Called… (+10 more)

### Community 73 - "ConversationEngine"
Cohesion: 0.12
Nodes (21): ConversationEngine, Runs one turn: prompt, model, tools, grounding, reply., str, PRD FR-047's five categories, and nothing outside them., SourceLabel, ChatResponse, What a provider returned. ``text`` is for the user. ``tool_calls`` is for the…, EchoParams (+13 more)

### Community 74 - "PersonalityStore"
Cohesion: 0.15
Nodes (16): Formality, Humour, PersonalityProfile, PersonalityProposal, PersonalityStore, ProposalStatus, AuditLog, Enum (+8 more)

### Community 75 - "core.py"
Cohesion: 0.10
Nodes (24): DirEntry, PathLike, CoreStatus, EmergencyStopReport, ``JarvisCore`` — the composition root (ARCHITECTURE.md section 6.9). Owns…, Exactly what was stopped (PRD section 11.3 requires telling the user)., Runtime composition (L4). Wires L1-L3 together; imports no GUI code., default_scope() (+16 more)

### Community 76 - "speakable_text"
Cohesion: 0.11
Nodes (27): Match, A URL read aloud in full is unbearable; the host is the useful part., Strip what a phonemiser would recite rather than say (PRD FR-030). Presentation…, speakable_text(), _spoken_host(), parametrize, What Jarvis says aloud is not the same string as what it writes down. From a…, Stripping runs first, so emphasis cannot hide a key from the patterns. (+19 more)

### Community 77 - "registry.py"
Cohesion: 0.12
Nodes (18): ProhibitedCapabilityBlocked, A prohibited tool or capability was requested. Always a security signal., ToolRegistered, Any, Protocol, Schema the planner sees. Free-form text can never reach the invoker., What an implementation must provide., Everything a tool declares about itself. (+10 more)

### Community 78 - "VoiceService"
Cohesion: 0.09
Nodes (8): CommandHeard, No enrolment has been run in this build, so nothing has passed., Whether anything can actually be heard. Speaking depends on it., Attach the recording indicator (PRD FR-013). Capture may not start without…, Close the microphone and forget everything buffered., Where a finished spoken command goes. Nothing listened before., Owns the providers, the pipeline and the capture session., VoiceService

### Community 79 - "test_secret_store.py"
Cohesion: 0.14
Nodes (26): SecretStore, fixture, skipif, WINDOWS_ONLY, The secret store (ADR-0030, PRD 18.3, NFR-022, FR-169, AT-016). The assertions…, Never partial, never best-effort plaintext., Lifting a value under a different name must not decrypt it., Degrading to weaker protection would be worse than refusing (ADR-0010). (+18 more)

### Community 80 - "VoiceController"
Cohesion: 0.08
Nodes (9): QObject, Silence Jarvis now. Returns whether there was anything to silence., Start or stop waiting for the wake phrase, on the user's say-so., Transcription blocks for seconds, so never on the GUI thread., Switch microphone. Reopens the stream if one is already open., ADR-0010: name the phase rather than pretending or failing quietly., Stop listening and let the workers finish, with a bound., Owns everything that connects the Voice screen and F9 to the service. (+1 more)

### Community 81 - "FakeBackend"
Cohesion: 0.11
Nodes (18): Reads windows. Changes nothing. Deliberately has no `click`, `invoke`, `type`…, UiaInspector, FakeBackend, inspector(), fixture, FR-071: reading the UI Automation tree, before anything can act on it. Phase 2…, The desktop version of the web attack, and the same defence. A window can name…, Stage 2 builds eyes. Hands arrive with the worker, behind the lock. If an… (+10 more)

### Community 82 - "test_screen_capture.py"
Cohesion: 0.13
Nodes (17): _capture(), FakeBackend, FakeCanvas, Photographing the screen: never silently, and never a secret. Phase 2 stage 4,…, FR-271, asserted structurally. A capability that cannot be *seen* is not…, After would mean the notice arrives once the picture already exists., AT-031, in the form whole-screen capture leaves it in. The blocklist stops…, It is not on screen, so there is nothing to cover — and covering its last known… (+9 more)

### Community 83 - "VaultPaths"
Cohesion: 0.14
Nodes (5): Path, Instance-scoped files such as the single-instance lock., Create the vault layout. Idempotent., Every path the application is allowed to write to, derived from one root., VaultPaths

### Community 84 - "test_tool_specs_are_valid.py"
Cohesion: 0.11
Nodes (24): Every registered tool's declared contract must actually be usable.…, The invoker validates locks before doing anything. Prove it passes., CLAUDE.md: every external interaction declares a timeout., FR-048: `succeeded` requires verification, so it must be described., The invoker rejects an undeclared code, turning a handled failure into a crash,…, A capability the catalogue has never heard of can never be granted., Every spec the real core registers, plus the shell-only ones., A lock name the manager rejects makes the tool permanently unusable. (+16 more)

### Community 85 - "test_voice_reply_behaviour.py"
Cohesion: 0.12
Nodes (17): application(), FakeEngine, _pump(), fixture, How Jarvis behaves when it was spoken to, and who it thinks you are. From a…, Typing means you are looking at the screen. Do not talk over it., Otherwise a voice failure is completely silent and invisible., It did this every time, including from the tray with nothing open. (+9 more)

### Community 86 - "test_offline_speech_models.py"
Cohesion: 0.13
Nodes (23): fixture, hub_is_offline(), What the environment says. See `hub_library_is_offline` for the truth., clean_environment(), FakeConfig, Offline mode must silence the speech model hubs too (PRD AT-001). The Ollama…, It was configuration in name only. `storage.huggingface_home` has named a…, Several gigabytes of downloads are not moved behind someone's back. (+15 more)

### Community 87 - "PermissionEngine"
Cohesion: 0.18
Nodes (11): PermissionEvaluation, PermissionGrant, PermissionRequest, PermissionEngine, Decision, GrantScope, Evaluates capability requests against persisted grants., Record a permission decision. Validates the permission model first. (+3 more)

### Community 88 - "describe_voice_stack"
Cohesion: 0.16
Nodes (14): _capture_status(), ComponentStatus, describe_voice_stack(), module_available(), Path, What of the voice stack is actually usable right now (ADR-0010, NFR-014). Audio…, Report each component's real state, reading configuration when given., True if ``module`` could be imported, without importing it. (+6 more)

### Community 89 - "youtube.py"
Cohesion: 0.12
Nodes (20): challenge_in(), ChallengeDetected, describe_challenge(), RuntimeError, Stopping at an anti-bot challenge, and handing it to the user (FR-058). Phase 2…, An anti-bot challenge is on screen. Automation stops here., Name the challenge on the page, or ``None`` if there is not one., Raise if the page is a challenge. Returns nothing when it is not. Deliberately… (+12 more)

### Community 90 - "test_close_verification_live.py"
Cohesion: 0.16
Nodes (15): _is_cloaked(), Whether DWM is hiding this window. UWP applications leave…, _attributes(), _class_name(), experiment_a(), experiment_b(), _find(), HidesInsteadOfClosing (+7 more)

### Community 91 - "test_phase2_exit_criteria.py"
Cohesion: 0.09
Nodes (22): parametrize, Phase 2 exit criteria (P2-COR-01, P2-TST-01). The checklist for closing the…, The seam, at phase level. This project has shipped a correct mechanism wired to…, The exception, and it is deliberate. `screen.capture` is absent headless…, The injection defence, written into the signatures rather than a rule. Every…, ADR-0010, at phase level: name what is not possible. Reading a file's contents,…, A limitation that stops being written down stops being known. Each of these was…, FR-048. A tool that changes something must say how it knows it worked. (+14 more)

### Community 92 - "RingBuffer"
Cohesion: 0.10
Nodes (9): datetime, Forget everything held. Called whenever listening stops., Everything ever accepted, so a test can prove discarding happened., A bounded, in-memory window of the most recent audio. Thread-safe: the capture…, Append audio, discarding whatever falls out of the window., Everything currently held, as one chunk. Does not clear the buffer., The held frames individually, for a consumer that wants to keep going., Snapshot and clear, for when a wake event promotes it to a command. (+1 more)

### Community 93 - "TtsProvider"
Cohesion: 0.09
Nodes (10): Protocol, A selectable voice, with the licence metadata FR-032 requires., Streams frames in, yields a wake event when the phrase is heard., Audio in, transcript out. Local by default (PRD FR-020)., Text in, audio out. Local by default (PRD FR-030)., SttProvider, SynthesisResult, TtsProvider (+2 more)

### Community 94 - "test_the_request_is_the_specification.py"
Cohesion: 0.13
Nodes (20): outstanding_requests(), Actions the user asked for that nothing has even attempted. **Attempted**, not…, _Ran, Check the instruction against what happened, not the summary (ADR-0033). Every…, Reported by the owner on 2026-08-06. Sir: H-Arvis Open MS Edge and Brave…, jar" and "Java" are words. Stripping them would eat the command., Only the leading wake is a wake. The rest is what was said., Open YouTube and search for Godzilla" is two things, not one. (+12 more)

### Community 95 - "test_prompt_injection.py"
Cohesion: 0.10
Nodes (20): The only route from observed content into a prompt. ``untrusted`` is set here,…, parametrize, AT-007: web content can inform a plan; it can never authorise a capability.…, The delimiters are known, published strings. A page can contain them. If…, The audit log and GUI learn that untrusted data arrived, not what it said., Nothing about observed content can name a capability or an approval. An…, AT-006 and AT-007 meet here. "Play the second video" must resolve by ordinal.…, The structural control, asserted structurally. If any method resolved an item… (+12 more)

### Community 96 - "test_approval_dialog.py"
Cohesion: 0.21
Nodes (21): _buttons(), make_request(), panel(), _pending(), fixture, RiskLevel, queue(), The approval surface (PRD section 11.2, ADR-0027). Runs offscreen. What is… (+13 more)

### Community 97 - "app.py"
Cohesion: 0.12
Nodes (14): QColor, QIcon, The Qt application: wires the core to the tray and the main window. Everything…, Enum, str, Tray state icons, drawn programmatically. Two reasons not to ship image files:…, PRD section 9.1 tray states., A non-colour distinguishing mark (PRD NFR-033). (+6 more)

### Community 99 - "SingleInstanceGuard"
Cohesion: 0.12
Nodes (10): BaseException, Path, Remove a lock file whose owning process is gone., Acquire once at startup; release at shutdown. ``acquired`` is the only thing…, SingleInstanceGuard, test_a_lock_file_from_a_dead_process_is_reclaimed(), test_a_second_instance_is_refused(), test_acquire_or_raise_explains_the_refusal() (+2 more)

### Community 100 - "test_injection_corpus.py"
Cohesion: 0.13
Nodes (19): ContentClass, Observations Core, _hostile_list(), ObservedList, parametrize, The same attack, everywhere it can arrive (AT-007, P2-BRW-06).…, The control that actually holds: a label is not a way to choose. Everything…, A handle is minted by the engine, never taken from the content. If a label… (+11 more)

### Community 101 - "Capability Risk Classes"
Cohesion: 0.13
Nodes (20): Approval Dialog Design, Consequential-Action Audit Log, Capability Risk Classes, Conversation Agent Role, Filesystem Tool Root Scoping, IDE-Agent Orchestration, jarvis.db SQLite Single Source of Truth, Windows Known Folder Resolution (+12 more)

### Community 102 - "Observation"
Cohesion: 0.12
Nodes (12): Observation, A piece of content from outside the trust boundary. Deliberately minimal. Every…, How this content is labelled wherever it is shown or quoted., Record *that* untrusted content arrived, never *what it said*., ChatProvider, ChatRole, Any, Enum (+4 more)

### Community 103 - "test_at003_app_launch.py"
Cohesion: 0.12
Nodes (18): The tool invoker — the single choke point (ARCHITECTURE.md section 6.6). PRD…, catalogue(), launching_invoker(), fixture, parametrize, AT-003 — "Jarvis, open Sea of Thieves" launches it and verifies it. > When the…, AT-018: unverified is a distinct outcome, not a quiet success., ADR-0029 constraint 8: no direct path from a plan to Popen. (+10 more)

### Community 104 - "grounding.py"
Cohesion: 0.10
Nodes (17): claims_in_progress(), GroundedClaim, GroundingReview, _hedge(), _hedge_in_progress(), _hedge_promise(), Enum, Where an answer came from, and what counts as done (PRD FR-047, FR-048). Two… (+9 more)

### Community 105 - "ConversationStore"
Cohesion: 0.14
Nodes (8): ConversationStore, AuditLog, Begin a conversation. ``persist=False`` is a private session., Stop recording this conversation, and erase what was recorded. Per-conversation…, Turns for a live conversation, from memory; otherwise from storage., Remove a conversation and its turns. Messages cascade., Creates conversations and records turns, when recording is permitted., Global history control (PRD FR-045). Affects new conversations.

### Community 106 - "OllamaHealthChecker"
Cohesion: 0.15
Nodes (15): OllamaHealthChecker, Exception, Checks the local model runtime. Blocking; call it from a worker thread., Ollama adapter boundary rules (ADR-0007, PRD AT-001)., PRD NFR-013: every external interaction has a timeout., A remote 'local' endpoint would ship every prompt off the machine., Turning the check off is possible, but must be a deliberate configuration., test_a_non_loopback_endpoint_is_refused_without_opening_a_socket() (+7 more)

### Community 107 - "test_hotkeys_and_startup.py"
Cohesion: 0.13
Nodes (17): parse_hotkey(), Parse ``"Ctrl+Alt+Pause"`` or ``"F9"``. Raises :class:`HotkeyError`., parametrize, skipif, Global hotkeys and start-at-sign-in (PRD section 11.3, FR-018, FR-002). Parsing…, PRD section 11.3 and config/defaults.yaml agree on this combination., FR-018 and ADR-0027 specify bare F9, with no modifier., An emergency stop that fires forty times is not better than one. (+9 more)

### Community 108 - "test_cross_thread_marshalling.py"
Cohesion: 0.17
Nodes (18): application(), _FakeReport, _from_a_plain_thread(), _pump(), fixture, Work handed to the GUI thread from a non-Qt thread must actually arrive.…, The tool reported success for a notification that never appeared., Any new QTimer.singleShot in the shell must be on the GUI thread. Checked by… (+10 more)

### Community 109 - "test_turn_reports_what_ran.py"
Cohesion: 0.13
Nodes (15): AlwaysProposing, _ask(), A turn that ran out of steps still has to say what it did. Reported from real…, The control: when nothing ran, saying nothing ran is correct., Put my IDE on the left and Settings on the right" is not exotic. It needs a…, A model that never stops asking for tools — the exhaustion case., Every invocation works, and says so., Run one turn, the way the shell does. (+7 more)

### Community 110 - "test_stop_speaking.py"
Cohesion: 0.13
Nodes (15): application(), fixture, Making Jarvis shut up — the route that does not depend on tuning. Reported from…, ADR-0028: barge-in is not emergency stop, and conflating them is exactly how…, The tray entry exists whether or not Kokoro is installed., Put the pipeline into the state it is in while Kokoro plays., Silencing speech must not have replaced what it already did., _Report (+7 more)

### Community 111 - "test_voice_wiring.py"
Cohesion: 0.12
Nodes (17): _pump(), The Voice screen's controls must be connected, or honestly disabled. Every…, Recording without a visible indicator is a prohibited capability., Without one, capture could start with nothing on screen., The pipeline transcribed commands that had no listener at all., ``application.voice`` stayed None, so push-to-talk always refused., It reported "not available on this machine" while fully installed., The rule: enabled means connected. Disabled means it says why. (+9 more)

### Community 112 - "Phased Delivery Plan (Phase 0-6)"
Cohesion: 0.15
Nodes (18): Google Antigravity IDE Adapter, Application Catalogue and Aliases, Automation Worker, Dedicated Jarvis Brave Profile, Phased Delivery Plan (Phase 0-6), Deterministic Before Visual (Automation Hierarchy), Local Document Understanding, Executor Role (+10 more)

### Community 113 - "OpenWakeWordDetector"
Cohesion: 0.16
Nodes (8): build_wake_detector(), OpenWakeWordDetector, Path, openWakeWord over a pretrained base model, with a personal threshold., Applied after enrolment measurement chooses one., Highest score this frame produced across the loaded models., Yield an event whenever a frame crosses the threshold., Construct the configured detector, or a Null one that explains itself.

### Community 114 - "tools/__init__.py"
Cohesion: 0.18
Nodes (16): Tool contract, allow-list registry, prohibited guard and the invoker. This…, assert_tool_id_permitted(), check_tool_id(), ProhibitedToolError, Exception, The prohibited-capability guard (ADR-0003). Defence in depth, layer 2 of 3: 1.…, Return the reason a tool id is prohibited, or ``None`` if it is allowed., ``True`` if the tool id may be registered. (+8 more)

### Community 115 - "test_no_shell.py"
Cohesion: 0.20
Nodes (17): _findings(), parametrize, Path, The load-bearing security test (ADR-0003). Phase 0 exit criterion: *no generic…, No shipped module may start a process or evaluate generated code., ADR-0029 authorises one call site. A second is a new ADR, not a row here. This…, The allow-list entry must describe reality, not a module that moved., A guard on the guard: prove the detector is not vacuously passing. (+9 more)

### Community 116 - "test_prohibited_capabilities.py"
Cohesion: 0.14
Nodes (16): _Params, BaseModel, The prohibited-capability guard (ADR-0003, PRD sections 11.1 and 13.3)., No grant, setting or approval can reach past the prohibited check., PRD section 11.1's prohibited list is represented in the catalogue., In a fully wired runtime, nothing is registered against a prohibited class., _Result, test_catalogue_covers_every_prd_prohibited_class() (+8 more)

### Community 117 - "audio/capture.py"
Cohesion: 0.19
Nodes (15): capture_available(), default_input_device(), frames_from_bytes(), host_api_names(), list_devices(), Microphone capture and playback (PRD FR-016, FR-013, ADR-0028). ``sounddevice``…, The best input to open, preferring WASAPI over the system default. Windows…, Match device names across host APIs, which truncate them differently. (+7 more)

### Community 118 - "apply_network_policy"
Cohesion: 0.21
Nodes (16): _apply_model_store(), apply_network_policy(), _clear_mark(), _local_only(), _mark_set_here(), _marked(), model_store_directory(), Path (+8 more)

### Community 119 - "GlobalHotkeys"
Cohesion: 0.14
Nodes (8): GlobalHotkeys, Registers hotkeys on a dedicated thread and dispatches their actions. Off…, Run the registration and message loop on its own thread., Invoke a binding's action directly. The test and menu route., The tray and the tests need a route that does not need a real keypress., test_a_binding_can_be_triggered_directly(), test_bindings_are_addressable_by_name(), test_starting_a_disabled_manager_is_a_no_op()

### Community 120 - "PageDriver"
Cohesion: 0.15
Nodes (8): PageDriver, PlaybackReport, Any, Protocol, Search, and return the results as untrusted, positional content., Play the result at `position`, and confirm that it is playing. `position` is an…, The browser operations this adapter needs. Deliberately tiny, and deliberately…, What actually happened. `clicked` and `verified` are separate facts.

### Community 121 - "test_approval_scopes_that_stick.py"
Cohesion: 0.11
Nodes (16): _NullProvider, An approval the owner gave must survive to the next sentence. From…, The owner's decision, read back from the file that records it. Asserted against…, A grant the owner can never reach is a grant they do not have., The blast radius, held to one capability. PRD 11.1 puts medium risk at "ask…, PRD 9.9 and 11.1, untouched. Not a UX preference, and not negotiable., Whoever turned it on can turn it off, and the default stays conservative. The…, The rule, asserted directly rather than one scope at a time. This is the test… (+8 more)

### Community 122 - "Worker"
Cohesion: 0.15
Nodes (6): ABC, BaseException, A named background thread with a cooperative stop., Signal and wait. Returns ``True`` when the thread actually stopped., Run until :attr:`stop_requested`. Check it often., Worker

### Community 123 - ".start"
Cohesion: 0.15
Nodes (10): AuditLog, Database, EventBus, LockPort, PermissionEngine, ApprovalPort, Conversation, Begin a conversation. A private one writes nothing (FR-046, AT-014). (+2 more)

### Community 124 - "Local Wake Phrase Detection"
Cohesion: 0.16
Nodes (16): Audio Worker, English-Only Language Policy, faster-whisper STT Engine, First-Run Onboarding Wizard, .jarvispack Portable Identity Package, Local Speech-to-Text, Local Text-to-Speech, openWakeWord Model Runtime (+8 more)

### Community 125 - "test_lazy_audio_imports.py"
Cohesion: 0.20
Nodes (15): _module_name(), _module_scope_imports(), parametrize, Path, Audio dependencies stay optional and lazily imported (ADR-0010, NFR-014).…, The property all of the above exists to protect., Imports at module level only — imports inside a function are the point., A guard on the guard: prove the detector is not vacuously passing. (+7 more)

### Community 126 - "test_runtime_primitives.py"
Cohesion: 0.15
Nodes (11): _CountingWorker, Single-instance guard, workers and schema migrations., test_a_worker_runs_off_the_calling_thread(), test_a_worker_stops_cooperatively(), test_acquiring_twice_is_idempotent(), test_duplicate_worker_names_are_refused(), test_every_phase_0_table_exists(), test_foreign_keys_and_wal_are_enabled() (+3 more)

### Community 127 - ".play_cue"
Cohesion: 0.15
Nodes (6): Play a short tone. Never blocks, never raises onto the caller., Remember a worker so shutdown can wait for it, without hoarding., Say an answer aloud, off the GUI thread., F9. Press to start, and again to cut it short. ``RegisterHotKey`` reports the…, Collect a few seconds of room tone, then set the threshold., Thread

### Community 128 - "unbacked_claims"
Cohesion: 0.14
Nodes (10): Actions the reply claims that no tool capable of them ever verified. "Any tool…, unbacked_claims(), FailThenSucceed, _Failure, Reported by the owner on 2026-08-06, and the sharpest of the three. Sir: open…, The mapping is a closed list, so it must not conclude from ignorance. A…, Fails the first call to a tool and succeeds afterwards., _Result (+2 more)

### Community 129 - "_new_core"
Cohesion: 0.16
Nodes (15): _new_core(), Phase 0 exit criterion., PRD NFR-011: no consequential action is repeated after a restart., Kill the process the way a crash does: threads gone, nothing cleaned up.…, simulate_crash(), test_a_completed_task_is_never_re_run_after_recovery(), test_an_interrupted_task_reappears_paused_and_is_not_resumed(), test_offline_mode_makes_the_health_check_skip_the_network() (+7 more)

### Community 130 - "test_layering.py"
Cohesion: 0.26
Nodes (14): _imported_modules(), _module_name(), _package_of(), Path, Layering invariants (ARCHITECTURE.md section 5, ADR-0004). The rule that makes…, A fresh interpreter can import the whole engine with no Qt module loaded., Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.…, Spelled out separately because it is the invariant people break first. (+6 more)

### Community 131 - "Jarvis Core"
Cohesion: 0.14
Nodes (14): Audio Worker, Audit Log, Automation Worker, Data Vault, Jarvis Core, Jarvis Shell, Lock Manager, Ollama (+6 more)

### Community 132 - "ADR-0003: A Closed Capability Set — No Generic Execution Primitive"
Cohesion: 0.15
Nodes (16): One SQLite Connection Per Thread, ADR-0003: A Closed Capability Set — No Generic Execution Primitive, No Generic Execution Primitive, os.startfile Named Future Allow-Listed Exception, tests/security/test_no_shell.py Source Tree Scan, Tool Registry Identity and Pattern Denylist, ADR-0004: Single Process, Thread Isolation for Phases 0–3, Layering Rule: Core Packages Must Not Import PySide6 (+8 more)

### Community 133 - "phase2_tools.py"
Cohesion: 0.26
Nodes (9): BrowserRestartInput, BrowserRestartOutput, BaseModel, ToolContext, ToolExecution, The Phase 2 browser tools (FR-090, FR-091, AT-006). Two narrow typed tools,…, Run `function(adapter, *args)` on the browser's own thread. **This is the…, YouTubePlayOutput (+1 more)

### Community 134 - "QWidget"
Cohesion: 0.26
Nodes (7): NavArea, _NotImplementedPanel, QWidget, A heading, a refresh button and a read-only text area., Says exactly what is missing and when it arrives. Never a fake screen., _TablePanel, _TextPanel

### Community 135 - "test_at014_private_session.py"
Cohesion: 0.18
Nodes (13): parametrize, AT-014 — a private session produces no permanent record after it ends. Asserted…, Everything the vault has written, as raw bytes., A control: prove the byte search would have found it if written., Privacy is not the same as invisibility: the event is auditable., test_a_normal_session_is_recorded_so_the_test_above_means_something(), test_a_private_conversation_is_marked_private_to_the_user(), test_a_private_session_leaves_no_record_anywhere() (+5 more)

### Community 136 - "test_ollama_tool_calling.py"
Cohesion: 0.22
Nodes (13): _decode(), history(), Any, fixture, parametrize, Structured tool calls, and nothing else, reach the invoker (PRD FR-040, 13.4).…, The whole point: text is never scanned for actions., test_a_response_with_no_message_is_an_error_not_an_empty_answer() (+5 more)

### Community 137 - "main"
Cohesion: 0.29
Nodes (8): free_port(), http_json(), main(), Any, Can Jarvis drive one tab without touching any of the others? The spike behind…, One Chromium tab, driven over its own WebSocket. Nothing else is reachable., Tab, wait_for_port()

### Community 138 - "On-Demand Narrowly Scoped Elevated Helper Process"
Cohesion: 0.22
Nodes (13): ADR-0001: Python-First Implementation with Rust Deferred, Python 3.11 + PySide6 Implementation Stack, Qwen3-TTS Isolated Python 3.12 Worker, Rust/Tauri Native Shell Deferred Past Phase 3, Authenticated Typed IPC for Future Shell, Process-Separation Promotion Triggers, Helper IPC Discipline (Named Pipe or Loopback, Rotating Token), No Interaction with the Windows Secure Desktop or UAC Prompt (+5 more)

### Community 139 - "SQLite (jarvis.db) Canonical Transactional Store"
Cohesion: 0.23
Nodes (13): ADR-0002: SQLite as the Single Source of Truth, Large Binary Artefacts Stored on Disk, Referenced by Path, Derived Rebuildable Stores Hold No Unique Information, SQLite (jarvis.db) Canonical Transactional Store, WAL Mode Concurrent Readers, ADR-0005: An In-Process Typed Event Bus, Bus Is Notification, Not System of Record, ADR-0006: Layered Configuration with Override-Only Persistence (+5 more)

### Community 140 - "jarvis.core.events In-Process Publish/Subscribe Bus"
Cohesion: 0.20
Nodes (11): Versioned Forward-Only Migrations, Full ORM (SQLAlchemy) Rejected for Phase 0, Schema-Version Startup Check (Newer DB is Hard Failure), jarvis.core.events In-Process Publish/Subscribe Bus, Frozen Pydantic Event Models with Subclass Matching, Per-Handler Exception Isolation, ConfigChanged Runtime Event, pydantic extra="forbid" Loud Typo Failure (+3 more)

### Community 141 - "NetworkMode"
Cohesion: 0.15
Nodes (5): NetworkMode, Enum, str, _FakeResponse, Any

### Community 142 - "engine.py"
Cohesion: 0.20
Nodes (8): _canonical_folder(), DefaultPolicy, _folder_contains(), Permission evaluation (ARCHITECTURE.md section 6.4). The engine answers one…, Fallback decisions when no grant matches. High risk is fixed at ASK., Normalise a folder scope reference for prefix comparison. Phase 0 handles…, test_medium_risk_cannot_default_to_allow(), test_session_grants_get_a_ttl()

### Community 143 - "tools/ports.py"
Cohesion: 0.19
Nodes (9): ApprovalPort, LockLease, LockPort, Protocol, Ports the tool invoker depends on, so ``jarvis.core`` stays free of Qt and of…, A held set of resource locks., All-or-nothing acquisition of a declared lock set (PRD FR-124)., Return a lease, or ``None`` if the whole set could not be taken. (+1 more)

### Community 146 - "Phase 2: Deterministic Desktop and Browser Automation"
Cohesion: 0.17
Nodes (12): app.close, app.force_close, files.find, files.reveal, Phase 2: Deterministic Desktop and Browser Automation, Project Jarvis, screen.active_window, screen.capture (+4 more)

### Community 147 - "Closed Enumerated Set of Narrow Typed Tools"
Cohesion: 0.21
Nodes (12): Closed Enumerated Set of Narrow Typed Tools, Emergent Capability From Tool Composition (Residual Risk), Hard Ceiling on Prompt Injection Impact, Sandboxed Generic Shell Rejected, ToolSpec Typed Tool Contract, Thread Isolation Is Not a Security Boundary (Gap 2), Ollama Endpoint Squatting (Unmitigated Residual Risk), Local Authenticating Proxy for Ollama Not Adopted (+4 more)

### Community 148 - "._record"
Cohesion: 0.15
Nodes (6): DuplexMode, Open the microphone. Returns False, honestly, if it cannot., Synthesise **and play**, then report what actually came out. Synthesis alone…, Choose the microphone (PRD FR-016). Reopens an open stream., Cut playback short. Speech only — never locks, never tasks. The deterministic…, Listen for the wake phrase. Returns (started, why not). ADR-0016 originally…

### Community 149 - "Jarvis Core (Orchestration)"
Cohesion: 0.23
Nodes (12): Emergency Stop, Jarvis Core (Orchestration), Jarvis Shell (GUI Process), Authenticated Loopback IPC, PySide6 Desktop Shell Toolkit, Python 3.11 as V1 Implementation Language, Resource Lock Model, Task Checkpoints and Durability (+4 more)

### Community 150 - "claims_completion"
Cohesion: 0.23
Nodes (12): claims_completion(), Whether a reply asserts that something was done, or is being done., parametrize, Now searching" asserts an action as firmly as "I searched". `SUCCESS_PHRASES`…, The control. Hedging a question would make Jarvis unusable to talk to., test_a_present_tense_claim_is_a_completion_claim(), test_completion_claims_are_recognised(), test_done_as_a_whole_statement_is_still_a_completion_claim() (+4 more)

### Community 151 - "media.py"
Cohesion: 0.27
Nodes (11): _INPUT, _INPUTUNION, _KEYBDINPUT, media_available(), MediaAction, Enum, str, Media and volume control (PRD FR-094, catalogue `media.playback_control`,… (+3 more)

### Community 152 - "WindowBackend"
Cohesion: 0.17
Nodes (7): _process_names_by_pid(), Any, Protocol, What discovery needs from a windowing implementation., Executable names keyed by process id, via the tool-help snapshot., _state_of(), WindowBackend

### Community 153 - ".__init__"
Cohesion: 0.18
Nodes (5): GlobalHotkeys, QApplication, Connect the voice service to the Voice screen and to push-to-talk., The keyboard route to a waiting request (PRD NFR-030)., Emergency stop and push-to-talk, both configurable. Hotkey callbacks arrive on…

### Community 154 - "offerable_scopes_for"
Cohesion: 0.18
Nodes (11): offerable_scopes_for(), RiskLevel, The allow-scopes the dialog may offer, per the ADR-0027 table. Low offers…, PRD 9.9 and 11.1: fresh confirmation every time., The engine still supports SESSION; the dialog deliberately does not., test_a_prohibited_capability_is_offered_nothing(), test_allow_for_this_session_is_never_offered(), test_high_risk_is_offered_single_use_only() (+3 more)

### Community 155 - "OllamaHealth"
Cohesion: 0.20
Nodes (8): is_loopback_url(), OllamaHealth, True when the URL's host is a loopback address or resolves only to one., The result of one check. Never claims health it did not observe., Ollama adapter. Phase 0 implements only the health check., parametrize, test_loopback_urls_are_recognised(), test_non_loopback_urls_are_rejected()

### Community 156 - "startup.py"
Cohesion: 0.36
Nodes (10): available(), describe(), is_enabled(), Start at sign-in (PRD FR-002). Uses the per-user…, Only Windows has the Run key this uses., The command Windows would run at sign-in. ``pythonw.exe`` rather than…, Add or remove the sign-in entry. Never requires administrator rights., set_enabled() (+2 more)

### Community 157 - "PywinautoBackend"
Cohesion: 0.22
Nodes (4): Any, PywinautoBackend, The real backend. Windows only, and behind the `automation` extra. Imported…, Read one window's controls. Raises `UiaUnavailable` when the tree cannot be…

### Community 158 - "test_browser_attach.py"
Cohesion: 0.22
Nodes (10): parametrize, Path, _python_sources(), ADR-0031: Playwright is a client of a browser we started, never a launcher.…, A scan over nothing passes trivially; make that impossible., No `src/` module may call a Playwright API that starts a process., ADR-0031 consumes ADR-0029's exception; it must not have widened it., test_playwright_is_never_asked_to_launch_a_browser() (+2 more)

### Community 159 - "ConfigStore"
Cohesion: 0.22
Nodes (8): ConfigStore, SingleInstanceGuard, default_log_path(), ApprovalPort, Path, test_exit_3_a_second_instance_is_refused(), test_the_task_state_machine_is_persistent(), VaultPaths

### Community 160 - "Project Jarvis (Windows Local AI Desktop Agent)"
Cohesion: 0.27
Nodes (10): Connected Mode (Optional External Providers), Honest Task Status, Local First, Not Local Only, Offline Mode, One Action, One Verification, Project Jarvis (Windows Local AI Desktop Agent), Task Completion Evidence, Tool-Grounded Success Claims (+2 more)

### Community 161 - "hotkeys.py"
Cohesion: 0.20
Nodes (8): available(), Hotkey, HotkeyError, ValueError, Global hotkeys (PRD section 11.3, FR-018, ADR-0027). Two hotkeys exist in Phase…, A hotkey string could not be understood., Global hotkeys are a Windows facility in this build., A parsed combination, ready for ``RegisterHotKey``.

### Community 162 - "PeriodicWorker"
Cohesion: 0.22
Nodes (5): PeriodicWorker, Calls a function on an interval until stopped., Sleep, but wake immediately on stop. Returns ``True`` if stopping., test_a_periodic_worker_calls_its_action(), test_one_bad_tick_does_not_kill_a_periodic_worker()

### Community 163 - "Model Resource Scheduler (VRAM Arbitration)"
Cohesion: 0.31
Nodes (9): Kokoro TTS Provider, Model Resource Scheduler (VRAM Arbitration), Per-Role Model Routing, Ollama Local Model Runtime, Piper TTS Provider, qwen3:8b Planner/Conversation Model, Qwen3-TTS Expressive Provider, qwen3-vl Vision Model Route (+1 more)

### Community 164 - "denial_options_for"
Cohesion: 0.22
Nodes (9): denial_options_for(), Capability, Don't ask again" options, when the capability has a meaningful target. A…, The button must not overstate what a remembered denial covers., test_a_folder_scoped_capability_offers_a_folder_denial(), test_a_url_capability_says_site_rather_than_application(), test_an_application_scoped_capability_offers_to_remember_the_denial(), test_nothing_is_offered_for_a_capability_with_no_scope_kind() (+1 more)

### Community 165 - "WorkerSupervisor"
Cohesion: 0.22
Nodes (4): Starts and stops workers in a defined order., Stop in reverse order. Returns the names that stopped cleanly., WorkerSupervisor, test_the_supervisor_starts_and_stops_in_order()

### Community 166 - "WindowActionBackend"
Cohesion: 0.22
Nodes (3): Protocol, What the controller needs from a windowing implementation., WindowActionBackend

### Community 167 - "Path"
Cohesion: 0.22
Nodes (9): parametrize, Path, Screenshot-based computer control is still out of scope. Phase 1 legitimately…, No autonomous self-modification: every write path targets the vault., PRD section 25 lists sixteen open decisions., test_an_adr_exists_for_every_prd_open_decision(), test_no_screenshot_or_input_automation_module_exists(), test_required_documents_and_config_exist() (+1 more)

### Community 168 - "test_no_elevation.py"
Cohesion: 0.31
Nodes (6): Path, Non-administrator operation (PRD FR-003, NFR-020, ADR-0009). Phase 0 must run…, Any packaging manifest must be asInvoker., _relative(), test_no_manifest_declares_an_elevated_execution_level(), test_no_module_requests_elevation()

### Community 169 - "configure_logging"
Cohesion: 0.29
Nodes (6): Logger, Diagnostics: application logging and, later, crash reporting., configure_logging(), Path, Structured application logging. Separate from the audit log. The audit log…, Configure the root logger once. Idempotent.

### Community 170 - ".set_setting"
Cohesion: 0.29
Nodes (4): NetworkMode, Any, AppConfig, Change a setting, persist the override and announce it.

### Community 171 - "AutoApprovalPort"
Cohesion: 0.18
Nodes (10): AutoApprovalPort, Decision, GrantScope, Test double. Never wire this into a running application. Guarded so a mistake…, echo_invoker(), Low may be always, medium may be per-task, high is single use only., test_a_broader_approval_scope_is_persisted_as_a_grant(), test_a_scoped_capability_offers_to_remember_the_denial() (+2 more)

### Community 172 - ".emergency_stop_from_hotkey"
Cohesion: 0.29
Nodes (3): Runs on the GUI thread, whatever thread pressed the key., F9. Press to start speaking, press again to cut it short. Not hold-to-talk:…, Interrupt speech, and nothing else (ADR-0028). Deliberately not routed through…

### Community 173 - "FakeSounddevice"
Cohesion: 0.25
Nodes (4): fake_sounddevice(), FakeSounddevice, fixture, Refuses the wrong settings exactly as PortAudio does.

### Community 174 - "ADR-0034: File Opening Policy"
Cohesion: 0.29
Nodes (7): files.open, ADR-0027: Approval Dialog Scopes, ADR-0029: Authorised Process Creation, ADR-0034: File Opening Policy, Project State (2026-08-02), Automation Session, Launch Utility

### Community 175 - "ADR-0008: Secret Storage Deferred to Phase 1"
Cohesion: 0.38
Nodes (7): ADR-0008: Secret Storage Deferred to Phase 1, jarvis.core.audit.redaction Defence-in-Depth Backstop, Windows Credential Manager CredWrite/CredRead (Candidate Mechanism), DPAPI CryptProtectData via ctypes (Candidate Mechanism), Encrypted SQLite Table with DPAPI-Wrapped Key (Candidate Mechanism), No Secret Store Implemented in Phase 0, Secrets Excluded From Normal Exports

### Community 176 - "ADR-0013: Installer Technology"
Cohesion: 0.29
Nodes (7): No Elevation Manifest Security Check (asInvoker), Application Never Runs Permanently as Administrator, ADR-0013: Installer Technology, Installer Choice Sequenced Behind the MSIX Decision, NSIS (Candidate Installer), Per-User Install with No UAC Elevation, WiX Toolset MSI (Candidate Installer)

### Community 177 - "Never Claim Unverified Success"
Cohesion: 0.29
Nodes (7): Never Claim Unverified Success, Programmatically Drawn QPainter Tray Icons, ADR-0011: Public Product Name, "Jarvis" as Internal Codename Only, public_product_name Configuration Value, Rename Before Public Release (Leaning Option), Trademark and Identifier Availability Criteria

### Community 178 - "generate_voice_sample"
Cohesion: 0.38
Nodes (6): ndarray, generate_voice_sample(), main(), normalise_audio(), Path, Convert Kokoro output into a one-dimensional NumPy array.

### Community 179 - ".describe"
Cohesion: 0.29
Nodes (3): OllamaHealth, Stop all automation without stopping the application., Check the local model runtime. Runs on a worker thread.

### Community 180 - "Arc Reactor Visual Motif"
Cohesion: 0.52
Nodes (7): Jarvis Application Icon (Arc Reactor Mark), Arc Reactor Visual Motif, Circular Metallic Chassis Ring, Cyan-on-White Emissive Palette, Jarvis Product Brand Identity, Transparent Alpha Square Canvas, Inverted Triangular Glowing Core

### Community 181 - ".__init__"
Cohesion: 0.29
Nodes (5): AuditLog, Capability, Database, EventBus, The catalogue entry, or ``None`` if it is not a declared capability.

### Community 182 - "HotkeyBinding"
Cohesion: 0.33
Nodes (4): HotkeyBinding, One requested hotkey and what actually became of it., Declare a hotkey. Parsing happens now; registration happens at start., Hotkeys the user asked for that are not actually working.

### Community 184 - "DenyingApprovalPort Default Implementation"
Cohesion: 0.33
Nodes (6): ADR-0007: Ollama Loopback-Only Trust Boundary, Loopback-Only Base URL Enforcement at the Adapter, Offline Mode Enforced at the Adapter Boundary, DenyingApprovalPort Default Implementation, Inno Setup (Candidate Installer), Uninstall-Time Data Deletion Must Be Opt-In

### Community 185 - "never_open_the_speakers"
Cohesion: 0.33
Nodes (5): MonkeyPatch, never_open_the_speakers(), fixture, Nothing in the suite opens the speakers. Reported by the owner on 2026-08-06: a…, Stop `speak_reply` before it reaches synthesis, for every UI test. Patched on…

### Community 186 - "Memory Candidate Review Pipeline"
Cohesion: 0.33
Nodes (6): Bounded Definition of Learning, Memory Candidate Review Pipeline, Memory Record Schema, No Silent Learning, Editable Personality Profile, Private Session Mode

### Community 187 - "single_instance.py"
Cohesion: 0.33
Nodes (5): AlreadyRunningError, _process_is_alive(), Single-instance enforcement (PRD FR-005). Only one interactive Jarvis may run…, Is a process with this id currently running? ``os.kill(pid, 0)`` is the POSIX…, Another instance already holds the single-instance handle.

### Community 188 - ".send_message"
Cohesion: 0.33
Nodes (3): A spoken command becomes an ordinary conversation turn. The window is…, One live conversation at a time, created on first use., Run one turn on a worker thread; the model call blocks.

### Community 189 - "Brave Browser"
Cohesion: 0.40
Nodes (5): Brave Browser, browser.restart, ADR-0019: Browser Profile Isolation, ADR-0032: Browser Automation Permissions, Phase 2 Acceptance Testing

### Community 190 - "ADR-0029: Launching Approved Applications"
Cohesion: 0.40
Nodes (5): ADR-0029: Launching Approved Applications, ADR-0030: Secret Store Mechanism, ADR-0031: Browser Automation Attaches Over CDP, Phase 2 Plan — Deterministic Desktop and Browser Automation, Phase 1 Report — Voice-First Local Assistant

### Community 191 - ".__init__"
Cohesion: 0.40
Nodes (3): AuditLog, Path, Re-pin the model hubs after a network-mode change (AT-001).

### Community 192 - ".__init__"
Cohesion: 0.40
Nodes (3): AuditLog, datetime, EventBus

### Community 193 - "ToolResult"
Cohesion: 0.40
Nodes (3): The invoker's typed answer. Success requires verification., True only when the tool ran *and* confirmed its effect., ToolResult

### Community 194 - "test_whisper.py"
Cohesion: 0.70
Nodes (4): list_audio_devices(), main(), record_audio(), transcribe_audio()

### Community 196 - "test_the_library_itself_is_told_not_only_the_environment"
Cohesion: 0.50
Nodes (4): hub_library_is_offline(), What ``huggingface_hub`` itself believes, or None if it is not loaded. The…, The assertion the old test was missing, and the reason it was missing it. This…, test_the_library_itself_is_told_not_only_the_environment()

### Community 198 - "YouTubeUnavailable"
Cohesion: 0.50
Nodes (3): RuntimeError, The page could not be driven — a failure, never an unverified success., YouTubeUnavailable

### Community 200 - "test_enabling_then_disabling_leaves_no_entry"
Cohesion: 0.50
Nodes (4): WINDOWS_ONLY, Runs against the real per-user Run key, and cleans up after itself., test_enabling_then_disabling_leaves_no_entry(), test_the_startup_command_points_at_an_interpreter_that_exists()

### Community 201 - "ADR-0016: Custom "Jarvis" Wake Word"
Cohesion: 0.67
Nodes (3): ADR-0016: Custom "Jarvis" Wake Word, ADR-0027: Approval Dialog and Activation Interaction Model, ADR-0028: Barge-in and Full-Duplex Audio

### Community 202 - "ADR-0033: Turn Continuation Policy"
Cohesion: 0.67
Nodes (3): ADR-0033: Turn Continuation Policy, Jarvis LLM Grounding, Model announces actions instead of taking them

### Community 205 - "vault_free_bytes"
Cohesion: 0.67
Nodes (3): Path, Free space on the volume holding the vault (PRD NFR-006)., vault_free_bytes()

### Community 206 - "fake_ollama"
Cohesion: 0.67
Nodes (3): fake_ollama(), fixture, Replace urlopen so no test ever touches a real socket.

### Community 207 - "test_a_browser_tool_owns_the_desktop"
Cohesion: 0.67
Nodes (3): parametrize, The stage 2 rule, now with something real to bind to., test_a_browser_tool_owns_the_desktop()

## Ambiguous Edges - Review These
- `Arc Reactor Visual Motif` → `Cyan-on-White Emissive Palette`  [AMBIGUOUS]
  resources/icons/jarvis_icon.png · relation: references
- `"Jarvis" as Internal Codename Only` → `ADR-0012: Shell Technology for the First Public Build`  [AMBIGUOUS]
  docs/decisions/ADR-0011-public-product-name.md · relation: conceptually_related_to

## Knowledge Gaps
- **78 isolated node(s):** `openWakeWord Model Runtime`, `faster-whisper STT Engine`, `Per-Download Provider and Licence Disclosure`, `Expired Screenshot Evidence Must Degrade Honestly`, `Project Jarvis (local-first Windows desktop AI agent)` (+73 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **85 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Arc Reactor Visual Motif` and `Cyan-on-White Emissive Palette`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `"Jarvis" as Internal Codename Only` and `ADR-0012: Shell Technology for the First Public Build`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `JarvisCore` connect `JarvisCore` to `_new_core`, `QWidget`, `test_at014_private_session.py`, `ApplicationCatalogue`, `FileWorkspace`, `_PermissionsPanel`, `JarvisApplication`, `.__init__`, `ToolCall`, `ConfigStore`, `BrowserWorkspace`, `test_phase0_exit_criteria.py`, `MainWindow`, `Path`, `.set_setting`, `main_window.py`, `.describe`, `tests/conftest.py`, `ToolInvoker`, `ConversationEngine`, `core.py`, `test_phase2_exit_criteria.py`, `app.py`, `.start`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `ToolCall` connect `ToolCall` to `test_read_only_tools_prove_nothing.py`, `test_conversation_wiring.py`, `TaskScheduler`, `ToolInvoker`, `test_at003_app_launch.py`, `redact`, `ConversationEngine`, `.set_setting`, `core.py`, `AutoApprovalPort`, `tools/__init__.py`, `system_health.py`, `llm/conversation.py`, `JarvisCore`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `BrowserWorkspace` connect `BrowserWorkspace` to `BraveCdpSession`, `phase2_tools.py`, `core.py`, `PlaywrightPageDriver`, `DyingSession`, `test_browser_restart_and_tabs.py`, `JarvisCore`, `.start`, `YouTubeSearchTool`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `JarvisCore` (e.g. with `ToolCall` and `ToolInvoker`) actually correct?**
  _`JarvisCore` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `ToolCall` (e.g. with `ConversationEngine` and `Turn`) actually correct?**
  _`ToolCall` has 16 INFERRED edges - model-reasoned connections that need verification._