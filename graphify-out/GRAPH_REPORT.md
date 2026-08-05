# Graph Report - c:\Users\sharm\source\repos\project-jarvis  (2026-08-05)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 4285 nodes · 8544 edges · 262 communities (167 shown, 95 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 943 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ebbab52c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TaskState
- types.py
- test_audio_pipeline.py
- DuplexCoordinator
- audio/ports.py
- test_automation_session.py
- ApplicationCatalogue
- CaptureSession
- Database
- PermissionEngine
- Option B: Per-Stream Retention Defaults with Expiry
- TaskScheduler
- VoicePanel
- ToolCall
- pipeline.py
- phase2_tools.py
- test_browser_restart_and_tabs.py
- VoicePipeline
- test_tasks.py
- YouTubeAdapter
- schema.py
- AuditLog
- tools/__init__.py
- system_health.py
- test_user_interruption.py
- JarvisApplication
- BraveCdpSession
- test_web_search_and_catalogue.py
- BrowserWorkspace
- VoiceService
- test_application_launch.py
- test_phase0_exit_criteria.py
- test_reply_speech_policy.py
- ObservedList
- core.py
- launch.py
- conftest.py
- VoiceController
- ConversationEngine
- JarvisTrayIcon
- permissions/models.py
- OllamaHealthChecker
- EventBus
- VoiceActivityDetector
- test_playback.py
- ApprovalQueue
- model_directory
- test_empty_model_reply.py
- test_wake_install.py
- test_permission_engine.py
- FakeBackend
- ApprovalPanel
- ToolInvoker
- test_core_lifecycle.py
- PlaywrightPageDriver
- test_speak_tool.py
- redact
- test_conversation_wiring.py
- PersonalityStore
- test_shell.py
- tts.py
- JarvisCore
- ConversationPanel
- MainWindow
- test_secret_store.py
- OllamaChatProvider
- VaultPaths
- test_voice_reply_behaviour.py
- test_offline_speech_models.py
- speakable_text
- ConversationStore
- browser.py
- module_available
- ApprovalController
- test_tool_specs_are_valid.py
- AudioChunk
- wake.py
- llm/conversation.py
- review_response
- test_prompt_injection.py
- ConfigStore
- locks.py
- test_at003_app_launch.py
- SingleInstanceGuard
- describe_challenge
- test_voice_wiring.py
- test_grounding_and_history.py
- Capability Risk Classes
- OpenWakeWordDetector
- offerable_scopes_for
- _PermissionsPanel
- test_cross_thread_marshalling.py
- test_config.py
- config/store.py
- .ask
- test_hotkeys_and_startup.py
- test_stop_speaking.py
- Phased Delivery Plan (Phase 0-6)
- ApplicationEntry
- test_no_shell.py
- ui/__init__.py
- GlobalHotkeys
- PageDriver
- Worker
- Local Wake Phrase Detection
- TaskRunContext
- test_lazy_audio_imports.py
- test_prohibited_capabilities.py
- test_runtime_primitives.py
- paths.py
- test_layering.py
- Jarvis Core
- SourceLabel
- test_at014_private_session.py
- main
- SQLite (jarvis.db) Canonical Transactional Store
- DenyingApprovalPort Default Implementation
- DyingSession
- redact_for_speech
- ConversationStore
- Closed Enumerated Set of Narrow Typed Tools
- Jarvis Core (Orchestration)
- claims_completion
- media.py
- jarvis.core.events In-Process Publish/Subscribe Bus
- ADR-0003: A Closed Capability Set — No Generic Execution Primitive
- service.py
- PendingApproval
- .stop_speaking
- startup.py
- test_browser_attach.py
- On-Demand Narrowly Scoped Elevated Helper Process
- Project Jarvis (Windows Local AI Desktop Agent)
- hotkeys.py
- PeriodicWorker
- Project State
- Never Claim Unverified Success
- Model Resource Scheduler (VRAM Arbitration)
- SingleInstanceGuard
- denial_options_for
- ._answer
- WorkerSupervisor
- ui/conversation.py
- Path
- test_no_elevation.py
- configure_logging
- UiaBackend
- test_attach_cost.py
- ADR-0008: Secret Storage Deferred to Phase 1
- generate_voice_sample
- Arc Reactor Visual Motif
- HotkeyBinding
- _escape
- test_attach_side_effects.py
- ADR-0013: Installer Technology
- Memory Candidate Review Pipeline
- single_instance.py
- .send_message
- _FakeResponse
- ADR-0029: Launching Approved Applications
- .__init__
- ToolResult
- test_whisper.py
- main_window.py
- ._persist_setting
- ._apply_state
- test_enabling_then_disabling_leaves_no_entry
- Default Configuration
- P3-TSK-01: Task tree and bounded-plan validation
- ADR-0016: Custom "Jarvis" Wake Word
- .json_schema_for_model
- .start_conversation
- vault_free_bytes
- test_a_browser_tool_owns_the_desktop
- CI dependency and licence review job
- CI headless self-check step (jarvis.main --check)
- ADR-0019: Browser Profile Isolation
- EventBridge
- P4-VIS-01: Qwen3-VL model route
- ADR-0019: Browser Profile Isolation (Option D)
- espeak-ng Pronunciation Backend
- Target Hardware Profile
- Phase 0 Scope Statement
- core/__init__.py
- llm/__init__.py
- .set_user_name
- FakeResult
- test_an_unverified_success_claim_is_rewritten
- test_an_in_progress_claim_is_hedged_even_when_a_tool_verified
- test_an_unparseable_hotkey_is_reported_not_raised
- QT_QPA_PLATFORM=offscreen in CI
- CI security-invariants job
- CI test job (Windows + Ubuntu, Python 3.11/3.12)
- Any
- ApprovalPort
- AuditLog
- Project Jarvis
- ChatMessage
- ChatProvider
- ChatResponse
- Conversation
- ConversationEngine
- Audit JSONL File
- Jarvis SQLite Database
- P3-MEM-06: Portable identity export/import (.jarvispack)
- P3-SKL-01: Macro recorder
- ADR-0018: Search Provider
- ADR-0023: Adapter Isolation
- Phase 1 — User Acceptance Testing
- Phase 0 Report — Foundation and Safety Architecture
- DuplexCoordinator
- fixture
- GlobalHotkeys
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
- model_validator
- Verification
- AppConfig
- NetworkMode
- Exception
- Path
- RuntimeError
- ValueError
- ApplicationCatalogue
- BaseModel
- ToolContext
- ToolExecution
- AppConfig
- WINDOWS_ONLY
- NetworkMode
- AudioChunk
- AudioChunk
- parametrize
- AudioChunk
- ApplicationCatalogue
- ToolCall
- ToolCallProposal
- ToolInvoker
- Turn
- VaultPaths
- VoiceActivityDetector
- VoiceStackStatus
- WakeEvent

## God Nodes (most connected - your core abstractions)
1. `JarvisCore` - 97 edges
2. `AudioChunk` - 77 edges
3. `JarvisApplication` - 77 edges
4. `ToolCall` - 75 edges
5. `Database` - 59 edges
6. `DuplexCoordinator` - 55 edges
7. `EventBus` - 54 edges
8. `BrowserWorkspace` - 54 edges
9. `AuditLog` - 49 edges
10. `ToolInvoker` - 49 edges

## Surprising Connections (you probably didn't know these)
- `test_availability_names_the_missing_component_rather_than_failing()` --calls--> `describe_voice_stack()`  [INFERRED]
  tests/security/test_lazy_audio_imports.py → src/jarvis/audio/availability.py
- `test_an_empty_name_falls_back_to_you()` --calls--> `ConversationPanel`  [INFERRED]
  tests/ui/test_voice_reply_behaviour.py → src/jarvis/ui/conversation.py
- `test_setting_the_name_programmatically_does_not_re_emit()` --calls--> `ConversationPanel`  [INFERRED]
  tests/ui/test_voice_reply_behaviour.py → src/jarvis/ui/conversation.py
- `Project State` --references--> `AutomationSession`  [EXTRACTED]
  docs/PROJECT_STATE.md → jarvis/toolbox/automation.py
- `Project State` --references--> `UiaInspector`  [EXTRACTED]
  docs/PROJECT_STATE.md → jarvis/toolbox/uia.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Browser Automation Lifecycle** — changelog_browser_restart, jarvis_toolbox_automation_session, adr_0032, adr_0019 [EXTRACTED 0.95]
- **Phase 2 Security Controls** — user_input_watcher, jarvis_toolbox_uia_inspector, adr_0031, changelog_permissions_always_allowable [EXTRACTED 0.90]
- **Jarvis Runtime Components** — architecture_md_jarvis_shell, architecture_md_jarvis_core, architecture_md_audio_worker, architecture_md_automation_worker, architecture_md_task_scheduler, architecture_md_data_vault [EXTRACTED 1.00]
- **Tool Execution Pipeline** — architecture_md_tool_invoker, architecture_md_permission_engine, architecture_md_lock_manager, architecture_md_audit_log [EXTRACTED 1.00]
- **Security and Safety Framework** — security_md_untrusted_data_rule, threat_model_md_stride, architecture_md_permission_engine, architecture_md_audit_log [INFERRED 0.80]
- **Phase 3 Task and Memory Maturity** — docs_backlog_p3_tsk_01, docs_backlog_p3_tsk_02, docs_backlog_p3_skl_01, docs_backlog_p3_mem_06 [EXTRACTED 0.90]
- **Browser Automation Security Boundary** — docs_decisions_adr_0019, docs_decisions_adr_0032, jarvis_toolbox_automation_session [EXTRACTED 0.95]
- **Data Persistence Layer** — data_model_md_jarvis_db, data_model_md_audit_jsonl, config_defaults_yaml [EXTRACTED 0.85]
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

## Communities (262 total, 95 thin omitted)

### Community 0 - "TaskState"
Cohesion: 0.06
Nodes (60): LookupError, from_iso(), json_dumps(), json_loads(), new_id(), Any, datetime, Small shared primitives used across every layer. Kept deliberately tiny:… (+52 more)

### Community 1 - "types.py"
Cohesion: 0.04
Nodes (61): In-process typed event bus (ADR-0005). Deliberately not a message broker: no…, Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe., Subscription, Typed event bus and the domain event vocabulary., ApprovalRequested, ApprovalResolved, AppStarted, AppStopping (+53 more)

### Community 2 - "test_audio_pipeline.py"
Cohesion: 0.05
Nodes (42): BargeInReport, DuplexMode, PlaybackWindow, datetime, Enum, str, Full-duplex audio and barge-in (ADR-0028, PRD FR-015, section 11.3). ADR-0028…, Decide whether a detection is the user or Jarvis hearing itself. (+34 more)

### Community 3 - "DuplexCoordinator"
Cohesion: 0.05
Nodes (42): DuplexCoordinator, Knows when Jarvis is speaking, and judges detections accordingly., Degrade to half duplex when full duplex cannot be made reliable., What can actually interrupt Jarvis right now (ADR-0010, NFR-014). Full duplex…, Record how loud the *room* is while Jarvis speaks (the echo floor). Called for…, The loudest the microphone has been during this utterance., Capture continues during playback. That is the point of full duplex., Whether wake detection is live right now. (+34 more)

### Community 4 - "audio/ports.py"
Cohesion: 0.05
Nodes (32): AudioFormat, AudioUnavailable, Enum, Protocol, RuntimeError, str, Audio provider boundaries (ARCHITECTURE.md section 8, PRD sections 10.2-10.4).…, A selectable voice, with the licence metadata FR-032 requires. (+24 more)

### Community 5 - "test_automation_session.py"
Cohesion: 0.06
Nodes (39): AutomationSession, DesktopBusy, LockManagerLike, Any, Protocol, RuntimeError, Owning the desktop before moving anything (FR-077, FR-078, P2-WIN-03/04/05).…, Perform one action, if the user has not taken over. ``sends_input`` must be… (+31 more)

### Community 6 - "ApplicationCatalogue"
Cohesion: 0.12
Nodes (43): ApplicationCatalogue, ArgumentKind, CatalogueError, LaunchKind, Enum, str, The user's approved applications. Seeded, editable, never model-written., A catalogue entry was refused. Raised at registration, not at launch. (+35 more)

### Community 7 - "CaptureSession"
Cohesion: 0.05
Nodes (39): capture_available(), CaptureSession, default_input_device(), frames_from_bytes(), host_api_names(), list_devices(), Microphone capture and playback (PRD FR-016, FR-013, ADR-0028). ``sounddevice``…, The best input to open, preferring WASAPI over the system default. Windows… (+31 more)

### Community 8 - "Database"
Cohesion: 0.06
Nodes (36): Connection, Cursor, datetime, Row, TaskRecovered, Conversation history and private sessions (PRD FR-045, FR-046, AT-014). A…, Database, DatabaseError (+28 more)

### Community 9 - "PermissionEngine"
Cohesion: 0.06
Nodes (35): PermissionEvaluation, PermissionGrant, PermissionRequest, _canonical_folder(), DefaultPolicy, _folder_contains(), PermissionEngine, AuditLog (+27 more)

### Community 10 - "Option B: Per-Stream Retention Defaults with Expiry"
Cohesion: 0.05
Nodes (55): ADR-0014: Default English Voice, espeak-ng GPL-Family Licensing Consideration, Kokoro bm_george Default Voice, Per-Download Provider and Licence Disclosure, Voice Pack Redistribution Licensing Gap, Windows SAPI Emergency Fallback, ADR-0015: Additional TTS Providers, Model Resource Scheduler (FR-039) (+47 more)

### Community 11 - "TaskScheduler"
Cohesion: 0.07
Nodes (27): BaseModel, Enum, Protocol, str, What a task actually does. Runners are the extension point that later phases…, A registered unit of work., Why a runner was asked to stop., What a runner reports when it returns. (+19 more)

### Community 12 - "VoicePanel"
Cohesion: 0.05
Nodes (31): QWidget, Always show the exact destination path, installed or not., Show what has been measured. Never imply more than that., Listening needs the wake model and a microphone — nothing more. ADR-0016…, Show the transcript, so a misheard word is visibly a mishearing., Say plainly whether the microphone is open (PRD FR-013)., True if anything on this screen implies bare "Jarvis" works. FR-011 forbids…, Devices, voices, wake phrase and enrolment. (+23 more)

### Community 13 - "ToolCall"
Cohesion: 0.09
Nodes (50): RetryPolicy, A proposed action. Comes from the planner, the GUI, a skill or a schedule., ToolCall, allow(), make_tool(), Params, BaseModel, RiskLevel (+42 more)

### Community 14 - "pipeline.py"
Cohesion: 0.07
Nodes (33): Cue, cue_audio(), _faded(), Short audio cues, so Jarvis is legible without looking at the screen. The…, The cues this build makes, and what each one means., Render one cue, or None if numpy is unavailable or the name is unknown. Never…, Taper both ends, or the tone starts and stops with a click., ActivationRoute (+25 more)

### Community 15 - "phase2_tools.py"
Cohesion: 0.09
Nodes (37): BaseModel, BrowserNeedsRestart, Brave is running without an automation port, and only a restart fixes it. Its…, BrowserRestartInput, BrowserRestartOutput, The Phase 2 browser tools (FR-090, FR-091, AT-006). Two narrow typed tools,…, Search YouTube in the dedicated profile and read back the results., Play a result by position, and confirm it is actually playing. (+29 more)

### Community 16 - "test_browser_restart_and_tabs.py"
Cohesion: 0.05
Nodes (39): Exception, quit_browser(), Close the browser gracefully and confirm it actually exited. Returns whether it…, BrowserRestartTool, Close Brave and reopen it ready for automation (ADR-0032). This exists because…, _context(), FakePage, _FakeSession (+31 more)

### Community 17 - "VoicePipeline"
Cohesion: 0.09
Nodes (28): Begin waiting for the wake phrase, if enrolment allows it., Stop, and forget everything held. Nothing survives in memory., F9 pressed. Capture a command without a wake phrase (FR-018)., Only ever enabled after enrolment has been measured (ADR-0016)., Capture in, commands out. Owns the listening state machine., VoicePipeline, FakeStt, FakeWake (+20 more)

### Community 18 - "test_tasks.py"
Cohesion: 0.07
Nodes (37): Release everything this runtime holds. Called during shutdown., Release locks whose owning runtime instance is gone (PRD FR-006). Without this,…, Exclusive, persisted, owner-attributed locks., ResourceLockManager, Task state machine, durable store, locks and scheduler (PRD FR-120 .. FR-133)., A partial acquisition would deadlock two tasks against each other., PRD FR-006: a crash while holding a lock must not wedge the resource., PRD section 7.1 and AT-009: one runs, the other stays queued. (+29 more)

### Community 19 - "YouTubeAdapter"
Cohesion: 0.07
Nodes (35): Search YouTube, then play a result by position., YouTubeAdapter, fixture, The Phase 2 browser tools, and the declarations they make about themselves.…, The injection defence, expressed as a tool signature. If a `title` or `query`…, Off-by-one here is the difference between passing and failing AT-006., Clicked and played are separate facts, and the tool must not merge them., test_a_click_the_player_cannot_confirm_is_unverified_not_failed() (+27 more)

### Community 20 - "schema.py"
Cohesion: 0.08
Nodes (36): field_validator, model_validator, Configuration layer (L1). Must not import anything above L1., AudioConfig, _Base, ConversationLanguageConfig, DefaultPermissionPolicy, LanguageConfig (+28 more)

### Community 21 - "AuditLog"
Cohesion: 0.09
Nodes (31): Audit logging and secret redaction., AuditLog, Any, datetime, Path, Append-only audit log with two sinks (ARCHITECTURE.md section 6.3). *…, Every record from the JSONL file, oldest first., Search the SQLite index. Falls back to the JSONL file if unavailable. (+23 more)

### Community 22 - "tools/__init__.py"
Cohesion: 0.08
Nodes (28): Decision, GrantScope, The approval queue — step 5 of the invoker pipeline, made answerable. ADR-0027…, Block the calling thread until answered, or until the request expires. Called…, Record the user's decision. Returns False if nothing was waiting. Raises…, Deny everything outstanding. Used by emergency stop and by shutdown., Tool contract, allow-list registry, prohibited guard and the invoker. This…, AuditLog (+20 more)

### Community 23 - "system_health.py"
Cohesion: 0.11
Nodes (34): BaseModel, Enum, Exception, model_validator, str, The tool contract (PRD section 13.2). A *tool* is the only way the agent…, Per-invocation context handed to a tool. Carries no ambient authority., What a tool returns on success. (+26 more)

### Community 24 - "test_user_interruption.py"
Cohesion: 0.06
Nodes (31): last_user_input_tick_ms(), monotonic_tick_ms(), Noticing that the user has taken the desktop back (FR-078, AT-008). Phase 2…, Start watching from now. Forgets anything observed before., Record that *we* just sent input, so it is not read as the user's. Call this…, Whether the user has touched the desktop since `arm()`. Raises rather than…, A millisecond tick from the same family as Win32's `GetTickCount`., When Windows last saw any input, or ``None`` where it cannot be asked. Uses… (+23 more)

### Community 25 - "JarvisApplication"
Cohesion: 0.06
Nodes (16): QApplication, JarvisApplication, QObject, Connect the voice service to the Voice screen and to push-to-talk., Runs on the audio thread, so it only queues work onto the GUI one., Runs on the Qt main thread, courtesy of the bridge., The keyboard route to a waiting request (PRD NFR-030)., Answered from the Permissions screen rather than the panel. (+8 more)

### Community 26 - "BraveCdpSession"
Cohesion: 0.07
Nodes (30): BraveCdpSession, BrowserUnavailable, _cdp_banner(), free_ephemeral_port(), An unused port, chosen per session (ADR-0031 constraint 1). A fixed, well-known…, Wait for the debugging endpoint, bounded. Loopback only., A Brave we started, attached to over CDP, and close when done. Used as a…, Whether the browser we attached to is still running. Attached is not alive: the… (+22 more)

### Community 27 - "test_web_search_and_catalogue.py"
Cohesion: 0.08
Nodes (39): build_argv(), default_catalogue(), Construct the argument vector. Pure, so it is directly testable., The Phase 1 seed: exactly the applications PRD section 21 names. Paths are the…, test_a_store_app_uses_the_fixed_explorer_broker(), test_entries_resolve_by_alias(), test_every_seeded_entry_passes_validation(), parametrize (+31 more)

### Community 28 - "BrowserWorkspace"
Cohesion: 0.06
Nodes (29): BrowserWorkspace, Close the browser and release the thread. Safe to call twice., Inject an adapter directly. Used by tests and by an open session., Open a session, and hand it back only if it is still wanted.…, Whether the browser we attached to is still there. Reported from real use,…, Run `function(adapter, *args)` on the browser's own thread. **This is the…, The adapter, opening the browser if it is not already open. Opening happens on…, Open *and* still alive. A dead session must not report as open. (+21 more)

### Community 29 - "VoiceService"
Cohesion: 0.07
Nodes (15): CommandHeard, DuplexMode, NoiseCalibration, No enrolment has been run in this build, so nothing has passed., Whether anything can actually be heard. Speaking depends on it., Open the microphone. Returns False, honestly, if it cannot., Measure the room and apply the threshold (PRD FR-017)., Choose the microphone (PRD FR-016). Reopens an open stream. (+7 more)

### Community 30 - "test_application_launch.py"
Cohesion: 0.07
Nodes (37): executable_entry(), _music_entry(), parametrize, The constrained launcher (ADR-0029). Every test here maps to one of the nine…, Adding a shell through the catalogue is still adding a shell., A document would let the file-association table choose what runs., No quoting to get wrong, because nothing parses the vector., Open Brave" is a legitimate request; it just opens the browser. (+29 more)

### Community 31 - "test_phase0_exit_criteria.py"
Cohesion: 0.05
Nodes (33): Phase 0 exit criteria and hard constraints. One test (or small group) per…, The tool set stays small and low risk. Phase 0 registered exactly one tool.…, PRD FR-048: succeeded requires verification, so it must be declared., PRD section 13.4: free-form text can never be executed., A scan that was just narrowed must be shown to still detect something. The…, PRD section 4.4: nothing may silently become permanent memory., An honest report of an unreachable runtime is a successful self-check. Settled…, Phase 1 state must be visible from the headless self-check. (+25 more)

### Community 32 - "test_reply_speech_policy.py"
Cohesion: 0.09
Nodes (36): Enum, parametrize, _asks_something(), When a spoken request deserves a spoken answer (PRD FR-030, FR-048). Answering…, The user-facing setting, ``audio.speak_replies``., What the shell should do with a finished reply., Decide how a finished turn should sound. ``spoken_request`` is the whole reason…, ReplyVoice (+28 more)

### Community 33 - "ObservedList"
Cohesion: 0.09
Nodes (28): ContentClass, ObservedItem, ObservedList, BaseModel, Enum, str, Observed content — the only shape external data may take (PRD §11.4).…, One element of an observed, ordered list. ``label`` is attacker-controlled text… (+20 more)

### Community 34 - "core.py"
Cohesion: 0.08
Nodes (21): AppConfig, The whole validated configuration tree., ModelRole, str, Which configured model profile a request should use (PRD FR-041)., ModelBusyError, ModelRouter, RuntimeError (+13 more)

### Community 35 - "launch.py"
Cohesion: 0.08
Nodes (33): _basename(), launch(), launch_argv(), LaunchOutcome, process_running(), The one authorised process-creation call site (ADR-0029). Everything about this…, What actually happened. ``verified`` is never assumed (constraint 9)., Whether any named process exists (constraint 9, verification). Uses the Windows… (+25 more)

### Community 36 - "conftest.py"
Cohesion: 0.14
Nodes (34): MonkeyPatch, ResourceLockManager, TaskScheduler, TaskStore, approving_invoker(), audit(), config(), config_store() (+26 more)

### Community 37 - "VoiceController"
Cohesion: 0.07
Nodes (13): QObject, Play a short tone. Never blocks, never raises onto the caller., Remember a worker so shutdown can wait for it, without hoarding., Silence Jarvis now. Returns whether there was anything to silence., Start or stop waiting for the wake phrase, on the user's say-so., Transcription blocks for seconds, so never on the GUI thread., Switch microphone. Reopens the stream if one is already open., Collect a few seconds of room tone, then set the threshold. (+5 more)

### Community 38 - "ConversationEngine"
Cohesion: 0.11
Nodes (29): ConversationEngine, Runs one turn: prompt, model, tools, grounding, reply., ChatResponse, What a provider returned. ``text`` is for the user. ``tool_calls`` is for the…, _decode(), EchoParams, EchoResult, EchoTool (+21 more)

### Community 39 - "JarvisTrayIcon"
Cohesion: 0.07
Nodes (19): ActivationReason, QAction, QMenu, QSystemTrayIcon, JarvisTrayIcon, QObject, Colour, shape, tooltip and accessible name all change together., Enable the keyboard route and say how many are waiting. (+11 more)

### Community 40 - "permissions/models.py"
Cohesion: 0.09
Nodes (30): _c(), capabilities_by_risk(), capability(), capability_ids(), Capability, RiskLevel, The capability catalogue — PRD section 11.1 expressed as data. Risk…, Permission model, capability catalogue and evaluation engine. (+22 more)

### Community 41 - "OllamaHealthChecker"
Cohesion: 0.08
Nodes (26): is_loopback_url(), OllamaHealth, OllamaHealthChecker, Exception, True when the URL's host is a loopback address or resolves only to one., The result of one check. Never claims health it did not observe., Checks the local model runtime. Blocking; call it from a worker thread., Ollama adapter. Phase 0 implements only the health check. (+18 more)

### Community 42 - "EventBus"
Cohesion: 0.09
Nodes (22): E, EventBus, Thread-safe publish/subscribe with subclass matching., Receive ``event_type`` and every subclass of it., Deliver to every matching handler. Returns the number invoked. Handler…, EventBridge, QObject, Re-emits domain events as Qt signals on the GUI thread. (+14 more)

### Community 43 - "VoiceActivityDetector"
Cohesion: 0.09
Nodes (17): Record how loud Jarvis's own output was. Reported, not compared., calibrate(), NoiseCalibration, Enum, str, Voice activity detection and command bounds (PRD FR-014, FR-017). Energy-based,…, Feed one frame. Returns the state after it., Root-mean-square level of a chunk, normalised to roughly 0.0-1.0. (+9 more)

### Community 44 - "test_playback.py"
Cohesion: 0.11
Nodes (32): _as_float_array(), default_output_device(), play(), playback_available(), playback_unavailable_reason(), Audio playback (PRD FR-030, FR-033, ADR-0028). The missing half of the voice…, Decode the chunk's bytes into the float32 mono array a stream wants., Play one chunk, blocking, and report what was heard. Blocking by design: the… (+24 more)

### Community 45 - "ApprovalQueue"
Cohesion: 0.12
Nodes (29): ApprovalQueue, Declare whether a user interface is actually connected. Until one is, queueing…, Called whenever the pending set changes. Used by the tray., Holds requests between the thread that needs an answer and the user. Implements…, make_request(), fixture, RiskLevel, queue() (+21 more)

### Community 46 - "model_directory"
Cohesion: 0.13
Nodes (29): ArgumentParser, install_wake_model(), installed_files(), InstallReport, missing_files(), model_directory(), Path, One-time wake-word model installation (ADR-0016, PRD section 17.2). **No wake-… (+21 more)

### Community 47 - "test_empty_model_reply.py"
Cohesion: 0.11
Nodes (24): _describe_silence(), What to say when the model returned no words at all. It happens: a small model…, Conversation, One conversation, persisted or not., _conversation(), _engine(), NoopInvoker, parametrize (+16 more)

### Community 48 - "test_wake_install.py"
Cohesion: 0.12
Nodes (30): is_installed(), All required files present. Says nothing about whether they *work*., make_files(), Path, The wake-model bootstrap (ADR-0016, PRD section 17.2). No test here downloads…, A corrupt download must not be reported as ready (ADR-0010)., The command's exit code reflects usability, not download success., Hey Travis" measured 0.489, so 0.5 left almost no margin. (+22 more)

### Community 49 - "test_permission_engine.py"
Cohesion: 0.10
Nodes (28): PermissionRequest, A question put to the permission engine. Contains no side effects., parametrize, Permission evaluation (PRD sections 9.9 and 11.1, ARCHITECTURE.md 6.4)., A user who denied something should not be asked again in the same scope., PRD 11.1: fresh confirmation every time., PRD 9.9: high-risk permissions must not offer 'always allow'., test_a_deny_grant_outranks_an_allow_grant() (+20 more)

### Community 50 - "FakeBackend"
Cohesion: 0.09
Nodes (19): Reads windows. Changes nothing. Deliberately has no `click`, `invoke`, `type`…, Read one window's controls. Raises `UiaUnavailable` when the tree cannot be…, UiaInspector, FakeBackend, inspector(), fixture, FR-071: reading the UI Automation tree, before anything can act on it. Phase 2…, The desktop version of the web attack, and the same defence. A window can name… (+11 more)

### Community 51 - "ApprovalPanel"
Cohesion: 0.15
Nodes (27): ApprovalPanel, The approval surface (PRD section 11.2, ADR-0027). Tray-anchored and **non-…, One pending request, rendered with the PRD section 11.2 field set., _buttons(), make_request(), panel(), _pending(), fixture (+19 more)

### Community 52 - "ToolInvoker"
Cohesion: 0.15
Nodes (16): AuditCategory, Event, Any, BaseModel, RiskLevel, ToolContext, ToolExecution, Make "don't ask again" stick, as a scoped DENY grant (ADR-0027). No engine… (+8 more)

### Community 53 - "test_core_lifecycle.py"
Cohesion: 0.11
Nodes (29): _new_core(), Full core lifecycle, crash recovery and settings durability., Phase 0 exit criterion., PRD NFR-011: no consequential action is repeated after a restart., Kill the process the way a crash does: threads gone, nothing cleaned up.…, simulate_crash(), test_a_clean_start_reports_nothing_to_recover(), test_a_completed_task_is_never_re_run_after_recovery() (+21 more)

### Community 54 - "PlaywrightPageDriver"
Cohesion: 0.11
Nodes (18): RuntimeError, BrowserThreadViolation, PlaywrightPageDriver, Any, `PageDriver` against a real page. Positional throughout. Note what is absent:…, Refuse, legibly, rather than fail illegibly somewhere else later.…, Undo Playwright's own emulation, so this looks like the owner's tab. Playwright…, The page, replaced if the owner closed it. Reported 2026-08-05 as *"the YouTube… (+10 more)

### Community 55 - "test_speak_tool.py"
Cohesion: 0.12
Nodes (22): PlaybackReport, What playback actually did. Never assumed by the caller., FakeStream, Records what was written, like a speaker that keeps receipts., test_a_report_describes_itself_honestly(), _audio(), ``voice.speak`` must not claim speech it cannot evidence (FR-048, AT-018). The…, FR-034: say something was withheld rather than quietly changing it. (+14 more)

### Community 56 - "redact"
Cohesion: 0.11
Nodes (26): classify_content(), is_content_key(), is_secret_key(), Any, Secret redaction for the audit log (PRD section 11.5, FR-259). Redaction…, Return a copy of ``value`` safe to persist in the audit log. Mappings,…, Describe a value without reproducing it. Used where the *shape* of user content…, Redact secret-looking substrings, then bound the length. (+18 more)

### Community 57 - "test_conversation_wiring.py"
Cohesion: 0.12
Nodes (24): One user request and everything that came of it., Turn, application(), ExplodingEngine, FakeEngine, _pump(), fixture, The wiring between the Conversation screen and the engine. The panel tests… (+16 more)

### Community 58 - "PersonalityStore"
Cohesion: 0.15
Nodes (16): Formality, Humour, PersonalityProfile, PersonalityProposal, PersonalityStore, ProposalStatus, AuditLog, Enum (+8 more)

### Community 59 - "test_shell.py"
Cohesion: 0.07
Nodes (24): fixture, Tray, main window and the Qt event bridge. Runs under…, No placeholder screen may look like it works (ADR-0010, PRD section 1.10)., Phase 1 adds Conversation and Voice. Everything else still names its phase., PRD FR-001: Jarvis stays functional when the main window is closed., PRD NFR-033: do not rely on colour alone., ADR-0010: visible, disabled, honest — never hidden and never faked., test_about_states_the_phase_and_the_absence_of_a_shell() (+16 more)

### Community 60 - "tts.py"
Cohesion: 0.08
Nodes (15): Match, Load the speech models now, so the first command is not the slow one. Both…, build_tts_provider(), KokoroTtsProvider, Text to speech (PRD FR-030 to FR-034, ADR-0014, ADR-0015). Kokoro `bm_george`…, A URL read aloud in full is unbearable; the host is the useful part., Kokoro-82M. Loaded lazily and kept, because loading is slow., Load the voice model. Slow; call it from a worker at start-up. Public… (+7 more)

### Community 61 - "JarvisCore"
Cohesion: 0.08
Nodes (14): OllamaHealth, RecoveryReport, JarvisCore, Any, Everything except the user interface., Let the shell supply what only it can: desktop notifications. ``notify.show``…, Warm the speech models in the background, off the start-up path. The speech…, Open Brave on the dedicated Jarvis profile, attached over CDP. The browser is… (+6 more)

### Community 62 - "ConversationPanel"
Cohesion: 0.11
Nodes (21): ConversationPanel, Text conversation with the local model., panel(), fixture, The Conversation screen (PRD section 9.5, FR-046, FR-047)., The distinction is the whole point of FR-047., Model output is data here too, including in the transcript., test_a_missing_reason_still_produces_an_explanation() (+13 more)

### Community 63 - "MainWindow"
Cohesion: 0.14
Nodes (7): QMainWindow, MainWindow, Navigation shell over live core state., Closing the window leaves Jarvis running in the tray (PRD FR-001)., test_the_window_says_plainly_when_nothing_is_waiting(), test_conversation_is_a_live_area_not_a_phase_placeholder(), test_the_home_screen_reports_the_voice_stack_honestly()

### Community 64 - "test_secret_store.py"
Cohesion: 0.14
Nodes (26): SecretStore, fixture, skipif, WINDOWS_ONLY, The secret store (ADR-0030, PRD 18.3, NFR-022, FR-169, AT-016). The assertions…, Never partial, never best-effort plaintext., Lifting a value under a different name must not decrypt it., Degrading to weaker protection would be worse than refusing (ADR-0010). (+18 more)

### Community 65 - "OllamaChatProvider"
Cohesion: 0.13
Nodes (17): _as_int(), _neutralise_delimiters(), OllamaChatProvider, Any, Ollama chat completion (PRD FR-040, section 13.4, ADR-0007). Inherits the two…, Read only the structured field. Never parse prose for an action., Stop observed content from closing the wrapper that quotes it. The delimiters…, Chat against a loopback Ollama. Blocking; call from a worker thread. (+9 more)

### Community 66 - "VaultPaths"
Cohesion: 0.14
Nodes (5): Path, Instance-scoped files such as the single-instance lock., Create the vault layout. Idempotent., Every path the application is allowed to write to, derived from one root., VaultPaths

### Community 67 - "test_voice_reply_behaviour.py"
Cohesion: 0.11
Nodes (17): application(), FakeEngine, _pump(), fixture, How Jarvis behaves when it was spoken to, and who it thinks you are. From a…, Typing means you are looking at the screen. Do not talk over it., Otherwise a voice failure is completely silent and invisible., It did this every time, including from the tray with nothing open. (+9 more)

### Community 68 - "test_offline_speech_models.py"
Cohesion: 0.13
Nodes (21): ConfigStore, apply_network_policy(), _clear_mark(), hub_is_offline(), _mark_set_here(), Keep the speech model hubs off the network in offline mode (PRD AT-001). The…, Pin the hubs to their local cache when offline. Returns True if offline.…, _was_set_here() (+13 more)

### Community 69 - "speakable_text"
Cohesion: 0.13
Nodes (24): Strip what a phonemiser would recite rather than say (PRD FR-030). Presentation…, speakable_text(), parametrize, What Jarvis says aloud is not the same string as what it writes down. From a…, Stripping runs first, so emphasis cannot hide a key from the patterns., The caller decides what to do with nothing; this does not invent words., Stripping every underscore would mangle identifiers the user asked about., test_a_bare_url_is_read_as_its_host() (+16 more)

### Community 70 - "ConversationStore"
Cohesion: 0.11
Nodes (11): ConversationStore, AuditLog, Begin a conversation. ``persist=False`` is a private session., Stop recording this conversation, and erase what was recorded. Per-conversation…, Turns for a live conversation, from memory; otherwise from storage., Remove a conversation and its turns. Messages cascade., Creates conversations and records turns, when recording is permitted., Global history control (PRD FR-045). Affects new conversations. (+3 more)

### Community 71 - "browser.py"
Cohesion: 0.10
Nodes (20): ApplicationEntry, Path, brave_user_data_dir(), browser_windows(), close_window(), existing_debug_port(), _pids_for(), Driving the dedicated Brave profile over CDP (FR-056, FR-072, ADR-0031). Phase… (+12 more)

### Community 72 - "module_available"
Cohesion: 0.16
Nodes (14): _capture_status(), ComponentStatus, describe_voice_stack(), module_available(), Path, What of the voice stack is actually usable right now (ADR-0010, NFR-014). Audio…, Report each component's real state, reading configuration when given., True if ``module`` could be imported, without importing it. (+6 more)

### Community 73 - "ApprovalController"
Cohesion: 0.11
Nodes (11): ApprovalController, Decision, GrantScope, QObject, QWidget, Every PRD section 11.2 field, and no field invented to fill a gap., Bottom-right of the available desktop — where the tray lives., Connects the queue to the panel, on the Qt thread. The queue is answered from… (+3 more)

### Community 74 - "test_tool_specs_are_valid.py"
Cohesion: 0.12
Nodes (23): Every registered tool's declared contract must actually be usable.…, The invoker validates locks before doing anything. Prove it passes., CLAUDE.md: every external interaction declares a timeout., FR-048: `succeeded` requires verification, so it must be described., The invoker rejects an undeclared code, turning a handled failure into a crash,…, A capability the catalogue has never heard of can never be granted., Every spec the real core registers, plus the shell-only ones., A lock name the manager rejects makes the tool permanently unusable. (+15 more)

### Community 75 - "AudioChunk"
Cohesion: 0.06
Nodes (16): Watch raw frames, for measuring the room (PRD FR-017). Observers see frames…, One captured frame. Called from the audio thread., AudioChunk, A block of mono audio. ``samples`` is raw bytes, never a file path., datetime, The pre-wake ring buffer (PRD FR-012, FR-025, AT-002). Before a wake phrase is…, Forget everything held. Called whenever listening stops., Everything ever accepted, so a test can prove discarding happened. (+8 more)

### Community 76 - "wake.py"
Cohesion: 0.10
Nodes (14): choose_threshold(), EnrolmentMeasurement, measure_enrolment(), phrase_disclosure(), Wake-word detection and per-user enrolment (ADR-0016, PRD FR-010, FR-011).…, The measured result. ADR-0016 criterion 1: without this, no enabling., Good enough to enable always-listening (criterion 2)., Score held-out positives and negatives at a threshold. Kept free of any model… (+6 more)

### Community 77 - "llm/conversation.py"
Cohesion: 0.11
Nodes (16): Observation, A piece of content from outside the trust boundary. Deliberately minimal. Every…, How this content is labelled wherever it is shown or quoted., Record *that* untrusted content arrived, never *what it said*., The conversation engine (PRD FR-040, FR-042, FR-047, FR-048, section 13.4).…, ChatProvider, ChatRole, Any (+8 more)

### Community 78 - "review_response"
Cohesion: 0.09
Nodes (23): _hedge(), _hedge_in_progress(), The verification value of a succeeded result; empty if it did not succeed., Label a reply and stop it claiming an unverified success. ``tool_results`` are…, Say plainly that nothing is happening, and keep the words that claimed it. The…, Replace an unverified success claim with what is actually known., review_response(), _verification_of() (+15 more)

### Community 79 - "test_prompt_injection.py"
Cohesion: 0.10
Nodes (20): The only route from observed content into a prompt. ``untrusted`` is set here,…, parametrize, AT-007: web content can inform a plan; it can never authorise a capability.…, The delimiters are known, published strings. A page can contain them. If…, The audit log and GUI learn that untrusted data arrived, not what it said., Nothing about observed content can name a capability or an approval. An…, AT-006 and AT-007 meet here. "Play the second video" must resolve by ordinal.…, The structural control, asserted structurally. If any method resolved an item… (+12 more)

### Community 80 - "ConfigStore"
Cohesion: 0.14
Nodes (12): _atomic_write(), ConfigStore, _delete_by_path(), Path, Loads, validates and persists configuration. Only the *difference from…, The persisted overrides only, i.e. the diff from shipped defaults., Remove an override, returning the setting to its shipped default., Write via a temporary file in the same directory, then replace. A crash mid-… (+4 more)

### Community 81 - "locks.py"
Cohesion: 0.14
Nodes (11): LockAcquired, LockContended, _Contended, LockSetLease, Exception, Resource locks (PRD FR-124, section 7.1). Only one task may hold a given named…, Take the whole set or nothing. Returns ``None`` if unavailable., Release named locks, or every lock held by ``owner_id``. (+3 more)

### Community 82 - "test_at003_app_launch.py"
Cohesion: 0.11
Nodes (20): AutoApprovalPort, Test double. Never wire this into a running application. Guarded so a mistake…, catalogue(), launching_invoker(), fixture, parametrize, AT-003 — "Jarvis, open Sea of Thieves" launches it and verifies it. > When the…, AT-018: unverified is a distinct outcome, not a quiet success. (+12 more)

### Community 83 - "SingleInstanceGuard"
Cohesion: 0.12
Nodes (10): BaseException, Path, Remove a lock file whose owning process is gone., Acquire once at startup; release at shutdown. ``acquired`` is the only thing…, SingleInstanceGuard, test_a_lock_file_from_a_dead_process_is_reclaimed(), test_a_second_instance_is_refused(), test_acquire_or_raise_explains_the_refusal() (+2 more)

### Community 84 - "describe_challenge"
Cohesion: 0.13
Nodes (19): challenge_in(), ChallengeDetected, describe_challenge(), RuntimeError, Stopping at an anti-bot challenge, and handing it to the user (FR-058). Phase 2…, An anti-bot challenge is on screen. Automation stops here., Name the challenge on the page, or ``None`` if there is not one., Raise if the page is a challenge. Returns nothing when it is not. Deliberately… (+11 more)

### Community 85 - "test_voice_wiring.py"
Cohesion: 0.10
Nodes (19): application(), _pump(), fixture, The Voice screen's controls must be connected, or honestly disabled. Every…, Recording without a visible indicator is a prohibited capability., Without one, capture could start with nothing on screen., The pipeline transcribed commands that had no listener at all., ``application.voice`` stayed None, so push-to-talk always refused. (+11 more)

### Community 86 - "test_grounding_and_history.py"
Cohesion: 0.14
Nodes (14): PersonalityStore, Source labelling, tool-grounded success, history and personality. PRD FR-045,…, PRD FR-039: 12 GB will not hold two heavy models with large contexts., PRD section 4.4: no silent learning., test_a_default_profile_is_created_once(), test_a_proposal_cannot_be_decided_twice(), test_a_proposal_changes_nothing_until_the_user_accepts(), test_a_proposal_for_an_unknown_field_is_refused() (+6 more)

### Community 87 - "Capability Risk Classes"
Cohesion: 0.13
Nodes (20): Approval Dialog Design, Consequential-Action Audit Log, Capability Risk Classes, Conversation Agent Role, Filesystem Tool Root Scoping, IDE-Agent Orchestration, jarvis.db SQLite Single Source of Truth, Windows Known Folder Resolution (+12 more)

### Community 88 - "OpenWakeWordDetector"
Cohesion: 0.14
Nodes (10): build_wake_detector(), OpenWakeWordDetector, Path, openWakeWord over a pretrained base model, with a personal threshold., Applied after enrolment measurement chooses one., Highest score this frame produced across the loaded models., Yield an event whenever a frame crosses the threshold., Construct the configured detector, or a Null one that explains itself. (+2 more)

### Community 89 - "offerable_scopes_for"
Cohesion: 0.10
Nodes (19): offerable_scopes_for(), Decision, GrantScope, RiskLevel, The allow-scopes the dialog may offer, per the ADR-0027 table. Low offers…, PRD 9.9 and 11.1: fresh confirmation every time., The engine still supports SESSION; the dialog deliberately does not., test_a_prohibited_capability_is_offered_nothing() (+11 more)

### Community 90 - "_PermissionsPanel"
Cohesion: 0.19
Nodes (9): NavArea, _NotImplementedPanel, _PermissionsPanel, QWidget, A heading, a refresh button and a read-only text area., Active grants, and any approval currently waiting for an answer. The panel…, Says exactly what is missing and when it arrives. Never a fake screen., _TablePanel (+1 more)

### Community 91 - "test_cross_thread_marshalling.py"
Cohesion: 0.17
Nodes (18): application(), _FakeReport, _from_a_plain_thread(), _pump(), fixture, Work handed to the GUI thread from a non-Qt thread must actually arrive.…, The tool reported success for a notification that never appeared., Any new QTimer.singleShot in the shell must be on the GUI thread. Checked by… (+10 more)

### Community 92 - "test_config.py"
Cohesion: 0.10
Nodes (10): Layered configuration (ADR-0006)., PRD FR-039: 12 GB VRAM cannot hold two heavy models at once., PRD 11.1: high risk is always 'ask'; the schema will not accept otherwise., Phase 0 exit criterion: settings persist., PRD FR-036: the configured voice must be a real selection, not a fallback., test_a_fallback_only_voice_cannot_be_the_primary(), test_high_risk_default_policy_cannot_be_relaxed(), test_sequential_loading_forbids_parallel_heavy_models() (+2 more)

### Community 93 - "config/store.py"
Cohesion: 0.19
Nodes (14): ConfigError, deep_merge(), _env_overrides(), _get_by_path(), _parse_env_value(), Any, Exception, Layered configuration loading and override-only persistence (ADR-0006).… (+6 more)

### Community 94 - ".ask"
Cohesion: 0.13
Nodes (12): _describe_result(), Any, Conversation, An identity for one spoken or typed request. "Allow for this task" was offered…, Send one proposal through the invoker. Never around it., Describe only registered tools. The model cannot learn of others., Render a tool result for the model, without inflating it., Describe one registered tool in the format Ollama expects. Built from the… (+4 more)

### Community 95 - "test_hotkeys_and_startup.py"
Cohesion: 0.14
Nodes (16): parse_hotkey(), Parse ``"Ctrl+Alt+Pause"`` or ``"F9"``. Raises :class:`HotkeyError`., parametrize, skipif, Global hotkeys and start-at-sign-in (PRD section 11.3, FR-018, FR-002). Parsing…, PRD section 11.3 and config/defaults.yaml agree on this combination., FR-018 and ADR-0027 specify bare F9, with no modifier., An emergency stop that fires forty times is not better than one. (+8 more)

### Community 96 - "test_stop_speaking.py"
Cohesion: 0.13
Nodes (15): application(), fixture, Making Jarvis shut up — the route that does not depend on tuning. Reported from…, ADR-0028: barge-in is not emergency stop, and conflating them is exactly how…, The tray entry exists whether or not Kokoro is installed., Put the pipeline into the state it is in while Kokoro plays., Silencing speech must not have replaced what it already did., _Report (+7 more)

### Community 97 - "Phased Delivery Plan (Phase 0-6)"
Cohesion: 0.15
Nodes (18): Google Antigravity IDE Adapter, Application Catalogue and Aliases, Automation Worker, Dedicated Jarvis Brave Profile, Phased Delivery Plan (Phase 0-6), Deterministic Before Visual (Automation Hierarchy), Local Document Understanding, Executor Role (+10 more)

### Community 98 - "ApplicationEntry"
Cohesion: 0.14
Nodes (12): ApplicationEntry, _normalise_name(), One application the user has approved Jarvis to open. Created by the user,…, Fold the separators a model guesses between, and nothing else. "youtube-music",…, Refuse an unsafe catalogue entry at registration time (constraint 4)., Constraint 5: validate the caller's argument against the entry's type., Find an entry by id, display name or alias. Never by path., _validate_argument() (+4 more)

### Community 99 - "test_no_shell.py"
Cohesion: 0.20
Nodes (17): _findings(), parametrize, Path, The load-bearing security test (ADR-0003). Phase 0 exit criterion: *no generic…, No shipped module may start a process or evaluate generated code., ADR-0029 authorises one call site. A second is a new ADR, not a row here. This…, The allow-list entry must describe reality, not a module that moved., A guard on the guard: prove the detector is not vacuously passing. (+9 more)

### Community 100 - "ui/__init__.py"
Cohesion: 0.16
Nodes (12): QColor, QIcon, Enum, str, Tray state icons, drawn programmatically. Two reasons not to ship image files:…, PRD section 9.1 tray states., A non-colour distinguishing mark (PRD NFR-033)., Render the icon for a state. Colour *and* shape differ per state. (+4 more)

### Community 101 - "GlobalHotkeys"
Cohesion: 0.14
Nodes (9): GlobalHotkeys, Registers hotkeys on a dedicated thread and dispatches their actions. Off…, Run the registration and message loop on its own thread., Invoke a binding's action directly. The test and menu route., The tray and the tests need a route that does not need a real keypress., test_a_binding_can_be_triggered_directly(), test_a_disabled_manager_registers_nothing_and_says_so(), test_bindings_are_addressable_by_name() (+1 more)

### Community 102 - "PageDriver"
Cohesion: 0.15
Nodes (8): PageDriver, PlaybackReport, Any, Protocol, Search, and return the results as untrusted, positional content., Play the result at `position`, and confirm that it is playing. `position` is an…, The browser operations this adapter needs. Deliberately tiny, and deliberately…, What actually happened. `clicked` and `verified` are separate facts.

### Community 103 - "Worker"
Cohesion: 0.15
Nodes (6): ABC, BaseException, A named background thread with a cooperative stop., Signal and wait. Returns ``True`` when the thread actually stopped., Run until :attr:`stop_requested`. Check it often., Worker

### Community 104 - "Local Wake Phrase Detection"
Cohesion: 0.16
Nodes (16): Audio Worker, English-Only Language Policy, faster-whisper STT Engine, First-Run Onboarding Wizard, .jarvispack Portable Identity Package, Local Speech-to-Text, Local Text-to-Speech, openWakeWord Model Runtime (+8 more)

### Community 105 - "TaskRunContext"
Cohesion: 0.14
Nodes (7): Any, Persist a resume point (PRD FR-128)., Record support for a completion claim (PRD FR-132)., Report a milestone. Visible in the Tasks screen (PRD FR-131)., Everything a runner is allowed to touch. No ambient authority., Call this at every safe point. Pause lands here (PRD FR-125)., TaskRunContext

### Community 106 - "test_lazy_audio_imports.py"
Cohesion: 0.20
Nodes (15): _module_name(), _module_scope_imports(), parametrize, Path, Audio dependencies stay optional and lazily imported (ADR-0010, NFR-014).…, The property all of the above exists to protect., Imports at module level only — imports inside a function are the point., A guard on the guard: prove the detector is not vacuously passing. (+7 more)

### Community 107 - "test_prohibited_capabilities.py"
Cohesion: 0.16
Nodes (14): The prohibited-capability guard (ADR-0003, PRD sections 11.1 and 13.3)., No grant, setting or approval can reach past the prohibited check., PRD section 11.1's prohibited list is represented in the catalogue., In a fully wired runtime, nothing is registered against a prohibited class., test_catalogue_covers_every_prd_prohibited_class(), test_no_tool_may_ever_be_registered_for_a_prohibited_capability(), test_prohibited_capability_is_always_denied_regardless_of_grants(), test_registry_refuses_a_prohibited_tool() (+6 more)

### Community 108 - "test_runtime_primitives.py"
Cohesion: 0.15
Nodes (11): _CountingWorker, Single-instance guard, workers and schema migrations., test_a_worker_runs_off_the_calling_thread(), test_a_worker_stops_cooperatively(), test_acquiring_twice_is_idempotent(), test_duplicate_worker_names_are_refused(), test_every_phase_0_table_exists(), test_foreign_keys_and_wal_are_enabled() (+3 more)

### Community 109 - "paths.py"
Cohesion: 0.17
Nodes (13): PathLike, expand_path(), find_defaults_config(), _platform_default_root(), Data-vault path resolution. This is the *only* module permitted to expand…, Locate the shipped ``defaults.yaml``. Order: ``JARVIS_DEFAULTS_CONFIG`` env…, Expand ``%VARS%``, ``$VARS`` and ``~`` then normalise to an absolute path., Path (+5 more)

### Community 110 - "test_layering.py"
Cohesion: 0.26
Nodes (14): _imported_modules(), _module_name(), _package_of(), Path, Layering invariants (ARCHITECTURE.md section 5, ADR-0004). The rule that makes…, A fresh interpreter can import the whole engine with no Qt module loaded., Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.…, Spelled out separately because it is the invariant people break first. (+6 more)

### Community 111 - "Jarvis Core"
Cohesion: 0.14
Nodes (14): Audio Worker, Audit Log, Automation Worker, Data Vault, Jarvis Core, Jarvis Shell, Lock Manager, Ollama (+6 more)

### Community 112 - "SourceLabel"
Cohesion: 0.15
Nodes (10): GroundedClaim, GroundingReview, Enum, str, Where an answer came from, and what counts as done (PRD FR-047, FR-048). Two…, One statement and the label that must accompany it., The verdict on a proposed reply., True when nothing in the reply overstates what actually happened. (+2 more)

### Community 113 - "test_at014_private_session.py"
Cohesion: 0.18
Nodes (13): parametrize, AT-014 — a private session produces no permanent record after it ends. Asserted…, Everything the vault has written, as raw bytes., A control: prove the byte search would have found it if written., Privacy is not the same as invisibility: the event is auditable., test_a_normal_session_is_recorded_so_the_test_above_means_something(), test_a_private_conversation_is_marked_private_to_the_user(), test_a_private_session_leaves_no_record_anywhere() (+5 more)

### Community 114 - "main"
Cohesion: 0.29
Nodes (8): free_port(), http_json(), main(), Any, Can Jarvis drive one tab without touching any of the others? The spike behind…, One Chromium tab, driven over its own WebSocket. Nothing else is reachable., Tab, wait_for_port()

### Community 115 - "SQLite (jarvis.db) Canonical Transactional Store"
Cohesion: 0.23
Nodes (13): ADR-0002: SQLite as the Single Source of Truth, Large Binary Artefacts Stored on Disk, Referenced by Path, Derived Rebuildable Stores Hold No Unique Information, SQLite (jarvis.db) Canonical Transactional Store, WAL Mode Concurrent Readers, ADR-0005: An In-Process Typed Event Bus, Bus Is Notification, Not System of Record, ADR-0006: Layered Configuration with Override-Only Persistence (+5 more)

### Community 116 - "DenyingApprovalPort Default Implementation"
Cohesion: 0.33
Nodes (6): ADR-0007: Ollama Loopback-Only Trust Boundary, Loopback-Only Base URL Enforcement at the Adapter, Offline Mode Enforced at the Adapter Boundary, DenyingApprovalPort Default Implementation, Inno Setup (Candidate Installer), Uninstall-Time Data Deletion Must Be Opt-In

### Community 118 - "redact_for_speech"
Cohesion: 0.17
Nodes (10): AudioChunk, prepare_for_speech(), Make text legible aloud, then remove anything secret-shaped. Order matters:…, Replace anything secret-shaped with a description of what it was., redact_for_speech(), SynthesisResult, parametrize, FR-034: speaking a password is not recoverable by apologising. (+2 more)

### Community 119 - "ConversationStore"
Cohesion: 0.17
Nodes (12): ConversationStore, AT-014, structurally: not written, rather than written then removed., Leaving half a transcript satisfies neither reading of the request., test_a_normal_conversation_is_recorded(), test_a_private_conversation_still_works_in_memory(), test_a_private_session_writes_nothing_at_all(), test_adding_to_an_unknown_conversation_is_an_error(), test_all_history_can_be_deleted() (+4 more)

### Community 120 - "Closed Enumerated Set of Narrow Typed Tools"
Cohesion: 0.21
Nodes (12): Closed Enumerated Set of Narrow Typed Tools, Emergent Capability From Tool Composition (Residual Risk), Hard Ceiling on Prompt Injection Impact, Sandboxed Generic Shell Rejected, ToolSpec Typed Tool Contract, Thread Isolation Is Not a Security Boundary (Gap 2), Ollama Endpoint Squatting (Unmitigated Residual Risk), Local Authenticating Proxy for Ollama Not Adopted (+4 more)

### Community 121 - "Jarvis Core (Orchestration)"
Cohesion: 0.23
Nodes (12): Emergency Stop, Jarvis Core (Orchestration), Jarvis Shell (GUI Process), Authenticated Loopback IPC, PySide6 Desktop Shell Toolkit, Python 3.11 as V1 Implementation Language, Resource Lock Model, Task Checkpoints and Durability (+4 more)

### Community 122 - "claims_completion"
Cohesion: 0.23
Nodes (12): claims_completion(), claims_in_progress(), Whether a reply asserts that something was done, or is being done., Whether a reply asserts an action is under way right now. Questions are…, parametrize, Now searching" asserts an action as firmly as "I searched". `SUCCESS_PHRASES`…, The control. Hedging a question would make Jarvis unusable to talk to., test_a_present_tense_claim_is_a_completion_claim() (+4 more)

### Community 123 - "media.py"
Cohesion: 0.27
Nodes (11): _INPUT, _INPUTUNION, _KEYBDINPUT, media_available(), MediaAction, Enum, str, Media and volume control (PRD FR-094, catalogue `media.playback_control`,… (+3 more)

### Community 124 - "jarvis.core.events In-Process Publish/Subscribe Bus"
Cohesion: 0.20
Nodes (11): Versioned Forward-Only Migrations, Full ORM (SQLAlchemy) Rejected for Phase 0, Schema-Version Startup Check (Newer DB is Hard Failure), jarvis.core.events In-Process Publish/Subscribe Bus, Frozen Pydantic Event Models with Subclass Matching, Per-Handler Exception Isolation, ConfigChanged Runtime Event, pydantic extra="forbid" Loud Typo Failure (+3 more)

### Community 125 - "ADR-0003: A Closed Capability Set — No Generic Execution Primitive"
Cohesion: 0.15
Nodes (16): One SQLite Connection Per Thread, ADR-0003: A Closed Capability Set — No Generic Execution Primitive, No Generic Execution Primitive, os.startfile Named Future Allow-Listed Exception, tests/security/test_no_shell.py Source Tree Scan, Tool Registry Identity and Pattern Denylist, ADR-0004: Single Process, Thread Isolation for Phases 0–3, Layering Rule: Core Packages Must Not Import PySide6 (+8 more)

### Community 126 - "service.py"
Cohesion: 0.18
Nodes (6): The voice service: one object that owns the whole audio stack (L3). Built even…, What can interrupt Jarvis right now, given the microphone's state., Synthesise **and play**, then report what actually came out. Synthesis alone…, What was synthesised, and what was actually played (PRD FR-048). Carries the…, SpokenResult, VoiceStatus

### Community 127 - "PendingApproval"
Cohesion: 0.20
Nodes (5): PendingApproval, AuditLog, datetime, EventBus, One unanswered request. Mutable, unlike everything on the event bus.

### Community 128 - ".stop_speaking"
Cohesion: 0.20
Nodes (4): Runs on the GUI thread, whatever thread pressed the key., F9. Press to start speaking, press again to cut it short. Not hold-to-talk:…, Interrupt speech, and nothing else (ADR-0028). Deliberately not routed through…, F9. Press to start, and again to cut it short. ``RegisterHotKey`` reports the…

### Community 129 - "startup.py"
Cohesion: 0.36
Nodes (10): available(), describe(), is_enabled(), Start at sign-in (PRD FR-002). Uses the per-user…, Only Windows has the Run key this uses., The command Windows would run at sign-in. ``pythonw.exe`` rather than…, Add or remove the sign-in entry. Never requires administrator rights., set_enabled() (+2 more)

### Community 130 - "test_browser_attach.py"
Cohesion: 0.22
Nodes (10): parametrize, Path, _python_sources(), ADR-0031: Playwright is a client of a browser we started, never a launcher.…, A scan over nothing passes trivially; make that impossible., No `src/` module may call a Playwright API that starts a process., ADR-0031 consumes ADR-0029's exception; it must not have widened it., test_playwright_is_never_asked_to_launch_a_browser() (+2 more)

### Community 131 - "On-Demand Narrowly Scoped Elevated Helper Process"
Cohesion: 0.22
Nodes (13): ADR-0001: Python-First Implementation with Rust Deferred, Python 3.11 + PySide6 Implementation Stack, Qwen3-TTS Isolated Python 3.12 Worker, Rust/Tauri Native Shell Deferred Past Phase 3, Authenticated Typed IPC for Future Shell, Process-Separation Promotion Triggers, Helper IPC Discipline (Named Pipe or Loopback, Rotating Token), No Interaction with the Windows Secure Desktop or UAC Prompt (+5 more)

### Community 132 - "Project Jarvis (Windows Local AI Desktop Agent)"
Cohesion: 0.27
Nodes (10): Connected Mode (Optional External Providers), Honest Task Status, Local First, Not Local Only, Offline Mode, One Action, One Verification, Project Jarvis (Windows Local AI Desktop Agent), Task Completion Evidence, Tool-Grounded Success Claims (+2 more)

### Community 133 - "hotkeys.py"
Cohesion: 0.20
Nodes (8): available(), Hotkey, HotkeyError, ValueError, Global hotkeys (PRD section 11.3, FR-018, ADR-0027). Two hotkeys exist in Phase…, A hotkey string could not be understood., Global hotkeys are a Windows facility in this build., A parsed combination, ready for ``RegisterHotKey``.

### Community 134 - "PeriodicWorker"
Cohesion: 0.22
Nodes (5): PeriodicWorker, Calls a function on an interval until stopped., Sleep, but wake immediately on stop. Returns ``True`` if stopping., test_a_periodic_worker_calls_its_action(), test_one_bad_tick_does_not_kill_a_periodic_worker()

### Community 135 - "Project State"
Cohesion: 0.25
Nodes (9): ADR-0031: Browser Automation Security, ADR-0032: Browser Lifecycle and Permissions, browser.restart, permissions.always_allowable_capabilities, Project State, JarvisCore, AutomationSession, UiaInspector (+1 more)

### Community 136 - "Never Claim Unverified Success"
Cohesion: 0.29
Nodes (7): Never Claim Unverified Success, Programmatically Drawn QPainter Tray Icons, ADR-0011: Public Product Name, "Jarvis" as Internal Codename Only, public_product_name Configuration Value, Rename Before Public Release (Leaning Option), Trademark and Identifier Availability Criteria

### Community 137 - "Model Resource Scheduler (VRAM Arbitration)"
Cohesion: 0.31
Nodes (9): Kokoro TTS Provider, Model Resource Scheduler (VRAM Arbitration), Per-Role Model Routing, Ollama Local Model Runtime, Piper TTS Provider, qwen3:8b Planner/Conversation Model, Qwen3-TTS Expressive Provider, qwen3-vl Vision Model Route (+1 more)

### Community 138 - "SingleInstanceGuard"
Cohesion: 0.22
Nodes (7): SingleInstanceGuard, default_log_path(), ConfigStore, Path, VaultPaths, test_exit_3_a_second_instance_is_refused(), test_single_instance_enforcement_blocks_a_second_core()

### Community 139 - "denial_options_for"
Cohesion: 0.22
Nodes (9): denial_options_for(), Capability, Don't ask again" options, when the capability has a meaningful target. A…, The button must not overstate what a remembered denial covers., test_a_folder_scoped_capability_offers_a_folder_denial(), test_a_url_capability_says_site_rather_than_application(), test_an_application_scoped_capability_offers_to_remember_the_denial(), test_nothing_is_offered_for_a_capability_with_no_scope_kind() (+1 more)

### Community 141 - "WorkerSupervisor"
Cohesion: 0.22
Nodes (4): Starts and stops workers in a defined order., Stop in reverse order. Returns the names that stopped cleanly., WorkerSupervisor, test_the_supervisor_starts_and_stops_in_order()

### Community 142 - "ui/conversation.py"
Cohesion: 0.22
Nodes (5): ConversationWorker, QObject, QWidget, The Conversation screen (PRD section 9.5, FR-045, FR-046, FR-047). Two things…, Runs one turn off the UI thread. The model call is slow and blocking.

### Community 143 - "Path"
Cohesion: 0.22
Nodes (9): parametrize, Path, Screenshot-based computer control is still out of scope. Phase 1 legitimately…, No autonomous self-modification: every write path targets the vault., PRD section 25 lists sixteen open decisions., test_an_adr_exists_for_every_prd_open_decision(), test_no_screenshot_or_input_automation_module_exists(), test_required_documents_and_config_exist() (+1 more)

### Community 144 - "test_no_elevation.py"
Cohesion: 0.31
Nodes (6): Path, Non-administrator operation (PRD FR-003, NFR-020, ADR-0009). Phase 0 must run…, Any packaging manifest must be asInvoker., _relative(), test_no_manifest_declares_an_elevated_execution_level(), test_no_module_requests_elevation()

### Community 145 - "configure_logging"
Cohesion: 0.29
Nodes (6): Logger, Diagnostics: application logging and, later, crash reporting., configure_logging(), Path, Structured application logging. Separate from the audit log. The audit log…, Configure the root logger once. Idempotent.

### Community 146 - "UiaBackend"
Cohesion: 0.25
Nodes (4): Any, Protocol, What the inspector needs from a UI Automation implementation., UiaBackend

### Community 147 - "test_attach_cost.py"
Cohesion: 0.39
Nodes (7): free_port(), main(), How much does `connect_over_cdp` cost as the browser's tab count grows? Phase…, The browser's own view of its tabs, read over plain HTTP. Deliberately *not*…, run_case(), targets(), wait_for_banner()

### Community 148 - "ADR-0008: Secret Storage Deferred to Phase 1"
Cohesion: 0.38
Nodes (7): ADR-0008: Secret Storage Deferred to Phase 1, jarvis.core.audit.redaction Defence-in-Depth Backstop, Windows Credential Manager CredWrite/CredRead (Candidate Mechanism), DPAPI CryptProtectData via ctypes (Candidate Mechanism), Encrypted SQLite Table with DPAPI-Wrapped Key (Candidate Mechanism), No Secret Store Implemented in Phase 0, Secrets Excluded From Normal Exports

### Community 149 - "generate_voice_sample"
Cohesion: 0.38
Nodes (6): ndarray, generate_voice_sample(), main(), normalise_audio(), Path, Convert Kokoro output into a one-dimensional NumPy array.

### Community 150 - "Arc Reactor Visual Motif"
Cohesion: 0.52
Nodes (7): Jarvis Application Icon (Arc Reactor Mark), Arc Reactor Visual Motif, Circular Metallic Chassis Ring, Cyan-on-White Emissive Palette, Jarvis Product Brand Identity, Transparent Alpha Square Canvas, Inverted Triangular Glowing Core

### Community 151 - "HotkeyBinding"
Cohesion: 0.33
Nodes (4): HotkeyBinding, One requested hotkey and what actually became of it., Declare a hotkey. Parsing happens now; registration happens at start., Hotkeys the user asked for that are not actually working.

### Community 153 - "test_attach_side_effects.py"
Cohesion: 0.43
Nodes (6): free_port(), main(), playback_positions(), Does merely *attaching* Playwright start the browser's other videos? Reported…, Read `currentTime` from every tab, over raw CDP rather than Playwright.…, wait_for_banner()

### Community 154 - "ADR-0013: Installer Technology"
Cohesion: 0.29
Nodes (7): No Elevation Manifest Security Check (asInvoker), Application Never Runs Permanently as Administrator, ADR-0013: Installer Technology, Installer Choice Sequenced Behind the MSIX Decision, NSIS (Candidate Installer), Per-User Install with No UAC Elevation, WiX Toolset MSI (Candidate Installer)

### Community 155 - "Memory Candidate Review Pipeline"
Cohesion: 0.33
Nodes (6): Bounded Definition of Learning, Memory Candidate Review Pipeline, Memory Record Schema, No Silent Learning, Editable Personality Profile, Private Session Mode

### Community 156 - "single_instance.py"
Cohesion: 0.33
Nodes (5): AlreadyRunningError, _process_is_alive(), Single-instance enforcement (PRD FR-005). Only one interactive Jarvis may run…, Is a process with this id currently running? ``os.kill(pid, 0)`` is the POSIX…, Another instance already holds the single-instance handle.

### Community 157 - ".send_message"
Cohesion: 0.33
Nodes (3): A spoken command becomes an ordinary conversation turn. The window is…, One live conversation at a time, created on first use., Run one turn on a worker thread; the model call blocks.

### Community 159 - "ADR-0029: Launching Approved Applications"
Cohesion: 0.40
Nodes (5): ADR-0029: Launching Approved Applications, ADR-0030: Secret Store Mechanism, ADR-0031: Browser Automation Attaches Over CDP, Phase 2 Plan — Deterministic Desktop and Browser Automation, Phase 1 Report — Voice-First Local Assistant

### Community 160 - ".__init__"
Cohesion: 0.40
Nodes (3): AuditLog, Path, Re-pin the model hubs after a network-mode change (AT-001).

### Community 161 - "ToolResult"
Cohesion: 0.40
Nodes (3): The invoker's typed answer. Success requires verification., True only when the tool ran *and* confirmed its effect., ToolResult

### Community 162 - "test_whisper.py"
Cohesion: 0.70
Nodes (4): list_audio_devices(), main(), record_audio(), transcribe_audio()

### Community 166 - "test_enabling_then_disabling_leaves_no_entry"
Cohesion: 0.50
Nodes (4): WINDOWS_ONLY, Runs against the real per-user Run key, and cleans up after itself., test_enabling_then_disabling_leaves_no_entry(), test_the_startup_command_points_at_an_interpreter_that_exists()

### Community 167 - "Default Configuration"
Cohesion: 0.67
Nodes (3): Audio Configuration, Permissions Configuration, Default Configuration

### Community 168 - "P3-TSK-01: Task tree and bounded-plan validation"
Cohesion: 0.67
Nodes (3): P3-TSK-01: Task tree and bounded-plan validation, P3-TSK-02: Pause/resume with state re-observation, P5-IDE-01: Antigravity adapter

### Community 169 - "ADR-0016: Custom "Jarvis" Wake Word"
Cohesion: 0.67
Nodes (3): ADR-0016: Custom "Jarvis" Wake Word, ADR-0027: Approval Dialog and Activation Interaction Model, ADR-0028: Barge-in and Full-Duplex Audio

### Community 172 - "vault_free_bytes"
Cohesion: 0.67
Nodes (3): Path, Free space on the volume holding the vault (PRD NFR-006)., vault_free_bytes()

### Community 173 - "test_a_browser_tool_owns_the_desktop"
Cohesion: 0.67
Nodes (3): parametrize, The stage 2 rule, now with something real to bind to., test_a_browser_tool_owns_the_desktop()

## Ambiguous Edges - Review These
- `Arc Reactor Visual Motif` → `Cyan-on-White Emissive Palette`  [AMBIGUOUS]
  resources/icons/jarvis_icon.png · relation: references
- `"Jarvis" as Internal Codename Only` → `ADR-0012: Shell Technology for the First Public Build`  [AMBIGUOUS]
  docs/decisions/ADR-0011-public-product-name.md · relation: conceptually_related_to

## Knowledge Gaps
- **72 isolated node(s):** `openWakeWord Model Runtime`, `faster-whisper STT Engine`, `Per-Download Provider and Licence Disclosure`, `Expired Screenshot Evidence Must Degrade Honestly`, `Project Jarvis (local-first Windows desktop AI agent)` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **95 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Arc Reactor Visual Motif` and `Cyan-on-White Emissive Palette`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `"Jarvis" as Internal Codename Only` and `ADR-0012: Shell Technology for the First Public Build`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `JarvisCore` connect `JarvisCore` to `types.py`, `ApplicationCatalogue`, `PermissionEngine`, `SingleInstanceGuard`, `ToolCall`, `Path`, `schema.py`, `tools/__init__.py`, `JarvisApplication`, `BraveCdpSession`, `BrowserWorkspace`, `VoiceService`, `test_phase0_exit_criteria.py`, `core.py`, `main_window.py`, `conftest.py`, `ConversationEngine`, `.start_conversation`, `model_directory`, `ToolInvoker`, `test_core_lifecycle.py`, `MainWindow`, `OllamaChatProvider`, `_PermissionsPanel`, `test_at014_private_session.py`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `JarvisApplication` connect `JarvisApplication` to `.stop_speaking`, `types.py`, `._answer`, `VoicePanel`, `pipeline.py`, `schema.py`, `.send_message`, `test_reply_speech_policy.py`, `._persist_setting`, `VoiceController`, `JarvisTrayIcon`, `model_directory`, `test_conversation_wiring.py`, `JarvisCore`, `MainWindow`, `test_voice_reply_behaviour.py`, `ApprovalController`, `test_voice_wiring.py`, `test_cross_thread_marshalling.py`, `test_stop_speaking.py`, `ui/__init__.py`, `GlobalHotkeys`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `BrowserWorkspace` connect `BrowserWorkspace` to `core.py`, `conftest.py`, `browser.py`, `phase2_tools.py`, `test_browser_restart_and_tabs.py`, `YouTubeAdapter`, `DyingSession`, `PlaywrightPageDriver`, `BraveCdpSession`, `JarvisCore`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `JarvisCore` (e.g. with `VoiceService` and `AppConfig`) actually correct?**
  _`JarvisCore` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `AudioChunk` (e.g. with `CaptureSession` and `Cue`) actually correct?**
  _`AudioChunk` has 27 INFERRED edges - model-reasoned connections that need verification._