# Graph Report - .  (2026-08-04)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3662 nodes · 7721 edges · 251 communities (149 shown, 102 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 908 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0ead59cc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TaskState
- DuplexCoordinator
- AudioUnavailable
- types.py
- test_permission_engine.py
- AudioChunk
- ResourceLockManager
- service.py
- Option B: Per-Stream Retention Defaults with Expiry
- pipeline.py
- EventBus
- VoicePipeline
- ApplicationCatalogue
- JarvisApplication
- tasks/store.py
- AppConfig
- NetworkMode
- test_phase0_exit_criteria.py
- JarvisCore
- Database
- ToolCall
- AuditLog
- test_grounding_and_history.py
- MainWindow
- test_config.py
- test_web_search_and_catalogue.py
- VoiceController
- JarvisTrayIcon
- llm/conversation.py
- tools/ports.py
- system_health.py
- ConversationEngine
- ModelRouter
- PermissionEngine
- play
- launch.py
- test_application_launch.py
- ApprovalQueue
- ApprovalPanel
- schema.py
- OllamaChatProvider
- Resource Lock Model
- redact
- ConversationStore
- tools/__init__.py
- speakable_text
- PlaybackReport
- test_wake_install.py
- test_empty_model_reply.py
- ConversationPanel
- test_secret_store.py
- Turn
- VoiceService
- VaultPaths
- test_voice_reply_behaviour.py
- ._execute
- model_directory
- Conversation
- ToolSpec
- VoicePanel
- core.py
- describe_voice_stack
- RingBuffer
- ToolInvoker
- test_approval_dialog.py
- test_reply_speech_policy.py
- test_listening_controls.py
- test_voice_wiring.py
- test_hotkeys_and_startup.py
- test_runtime_primitives.py
- test_tool_specs_are_valid.py
- test_cross_thread_marshalling.py
- module_available
- test_stop_speaking.py
- media.py
- test_no_shell.py
- ui/__init__.py
- ._record
- GlobalHotkeys
- test_at003_app_launch.py
- Worker
- Automation Worker
- Capability Risk Classes
- test_offline_speech_models.py
- main_window.py
- test_lazy_audio_imports.py
- app.py
- WorkerSupervisor
- test_layering.py
- ADR-0003: A Closed Capability Set — No Generic Execution Primitive
- single_instance.py
- AuditCategory
- ApplicationEntry
- test_at014_private_session.py
- On-Demand Narrowly Scoped Elevated Helper Process
- SQLite (jarvis.db) Canonical Transactional Store
- jarvis.core.events In-Process Publish/Subscribe Bus
- EnrolmentMeasurement
- Residual risks accepted for Phase 0
- Closed Enumerated Set of Narrow Typed Tools
- .start
- TaskCheckpoint
- Project Jarvis (Windows Local AI Desktop Agent)
- First-Run Onboarding Wizard
- offerable_scopes_for
- startup.py
- Jarvis Core
- docs/BACKLOG.md
- ADR-0019: Browser Profile Isolation
- Memory Candidate Review Pipeline
- Local Wake Phrase Detection
- Jarvis Core (Orchestration)
- hotkeys.py
- .stop_speaking
- TB-7 Core/Automation to filesystem scopes
- ConfigStore
- Planner Role
- denial_options_for
- ._answer
- ui/conversation.py
- _PermissionsPanel
- test_no_elevation.py
- Over-Permission (OP) category
- Prompt Injection (PI) category
- configure_logging
- apply_network_policy
- LockPort
- PeriodicWorker
- ADR-0008: Secret Storage Deferred to Phase 1
- ADR-0013: Installer Technology
- Never Claim Unverified Success
- generate_voice_sample
- Arc Reactor Visual Motif
- wake_model_path
- HotkeyBinding
- _escape
- DenyingApprovalPort Default Implementation
- claims_completion
- .send_message
- ToolInvoker
- .__init__
- ToolResult
- TB-9 Automation to third-party Windows applications
- TB-4 Core to Automation Worker
- test_whisper.py
- tray.py
- .__exit__
- ._apply_state
- test_enabling_then_disabling_leaves_no_entry
- TB-5 Core to Ollama loopback HTTP endpoint
- build_parser
- ADR-0016: Custom "Jarvis" Wake Word
- field_validator
- InstallReport
- vault_free_bytes
- CI dependency and licence review job
- CI headless self-check step (jarvis.main --check)
- Task Scheduler
- espeak-ng Pronunciation Backend
- Target Hardware Profile
- Phase 0 Scope Statement
- core/__init__.py
- llm/__init__.py
- .set_user_name
- .set_listening_available
- .set_listening_state
- .claims_single_word_phrase
- test_the_screen_still_refuses_to_imply_bare_jarvis_works
- test_listening_is_offered_when_the_detector_loads_not_when_enrolled
- test_an_unparseable_hotkey_is_reported_not_raised
- test_the_windows_model_is_the_onnx_one
- test_the_feature_and_vad_models_are_required_too
- T-019 Mis-transcribed command causes destructive action
- QT_QPA_PLATFORM=offscreen in CI
- CI security-invariants job
- CI test job (Windows + Ubuntu, Python 3.11/3.12)
- Any
- ApprovalPort
- ARCHITECTURE.md
- Audio Worker
- Automation Worker
- Audit Log
- AuditLog
- BaseModel
- ChatMessage
- ChatProvider
- ChatResponse
- CommandHeard
- Conversation
- ConversationEngine
- ConversationStore
- DATA_MODEL.md
- Phase 1 — User Acceptance Testing
- Phase 0 Report — Foundation and Safety Architecture
- DuplexCoordinator
- DuplexMode
- Enum
- Event
- fixture
- GlobalHotkeys
- NoiseCalibration
- parametrize
- Path
- PersonalityStore
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
- SECURITY.md
- SourceLabel
- AudioChunk
- AudioChunk
- AudioChunk
- AudioChunk
- model_validator
- Conversation
- AppConfig
- Conversation
- NetworkMode
- Exception
- ApplicationCatalogue
- str
- AppConfig
- NetworkMode
- AudioChunk
- AudioChunk
- AudioChunk
- ApplicationCatalogue
- THREAT_MODEL.md
- ToolCall
- ToolCallProposal
- ToolContext
- ToolExecution
- ToolInvoker
- Turn
- ValueError
- VaultPaths
- VoiceActivityDetector
- VoiceStackStatus
- WakeEvent
- WINDOWS_ONLY

## God Nodes (most connected - your core abstractions)
1. `JarvisCore` - 105 edges
2. `AudioChunk` - 87 edges
3. `JarvisApplication` - 78 edges
4. `Database` - 76 edges
5. `ToolCall` - 74 edges
6. `EventBus` - 63 edges
7. `DuplexCoordinator` - 60 edges
8. `AuditLog` - 57 edges
9. `VoiceService` - 54 edges
10. `VoicePipeline` - 52 edges

## Surprising Connections (you probably didn't know these)
- `test_availability_names_the_missing_component_rather_than_failing()` --calls--> `describe_voice_stack()`  [INFERRED]
  tests/security/test_lazy_audio_imports.py → src/jarvis/audio/availability.py
- `test_an_empty_name_falls_back_to_you()` --calls--> `ConversationPanel`  [INFERRED]
  tests/ui/test_voice_reply_behaviour.py → src/jarvis/ui/conversation.py
- `test_setting_the_name_programmatically_does_not_re_emit()` --calls--> `ConversationPanel`  [INFERRED]
  tests/ui/test_voice_reply_behaviour.py → src/jarvis/ui/conversation.py
- `test_deep_merge_merges_mappings_and_replaces_scalars()` --calls--> `deep_merge()`  [EXTRACTED]
  tests/unit/test_config.py → src/jarvis/config/store.py
- `test_environment_override_is_not_persisted()` --calls--> `ConfigStore`  [EXTRACTED]
  tests/unit/test_config.py → src/jarvis/config/store.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Core Engine Components** — jarvis_core, tool_invoker, permission_engine, task_scheduler, lock_manager [EXTRACTED 1.00]
- **Safety and Architecture Documentation** — security_policy, architecture_doc, threat_model, data_model [EXTRACTED 1.00]
- **Core Safety Pipeline** — architecture_md_tool_invoker, architecture_md_permission_engine, architecture_md_lock_manager, architecture_md_audit_log [EXTRACTED 1.00]
- **Task Execution Flow** — architecture_md_task_scheduler, architecture_md_automation_worker, architecture_md_lock_manager [EXTRACTED 0.90]
- **Data Persistence Layer** — data_model_md_jarvis_db, data_model_md_audit_jsonl, config_defaults_yaml [EXTRACTED 0.85]
- **Phase 1 Security Architecture** — docs_decisions_adr_0027_approval_and_activation_interaction_model_md, docs_decisions_adr_0029_approved_application_launch_md, docs_decisions_adr_0030_secret_store_mechanism_md [EXTRACTED 0.90]
- **Phase 2 Browser Automation Strategy** — docs_decisions_adr_0019_browser_profile_isolation_md, docs_decisions_adr_0031_browser_automation_attaches_over_cdp_md, docs_phase_plans_phase_02_plan_md [EXTRACTED 0.95]
- **Six-Role Agent Pipeline (Converse, Plan, Execute, Observe, Verify, Curate)** — prd_conversation_agent, prd_planner, prd_executor, prd_observer, prd_verifier, prd_memory_curator [EXTRACTED 1.00]
- **Jarvis Process Model (Shell, Core, Audio, Automation, Scheduler)** — prd_jarvis_shell, prd_jarvis_core, prd_audio_worker, prd_automation_worker, prd_task_scheduler_process, prd_local_ipc [EXTRACTED 1.00]
- **Guardrail and Permission Stack** — prd_capability_risk_classes, prd_approval_design, prd_audit_log, prd_prompt_injection_defence, prd_emergency_stop, prd_prohibited_broad_tools, prd_structured_model_output [EXTRACTED 1.00]
- **Threats live in Phase 0** — threat_model_phase_0_residual_risks, threat_model_t_048, threat_model_t_052, threat_model_t_053, threat_model_t_057, threat_model_t_060, threat_model_t_069 [EXTRACTED 1.00]
- **TTS Provider Stack and GPU Resource Arbitration** — docs_decisions_adr_0015_additional_tts_providers_ttsprovider_interface, docs_decisions_adr_0014_default_english_voice_kokoro_bm_george, docs_decisions_adr_0014_default_english_voice_windows_sapi_fallback, docs_decisions_adr_0015_additional_tts_providers_qwen3_tts_isolated_worker, docs_decisions_adr_0015_additional_tts_providers_model_resource_scheduler, docs_decisions_adr_0017_embedding_model_qwen3_embedding_0_6b [EXTRACTED 1.00]
- **Artefact Trust and Provenance Chain** — docs_decisions_adr_0026_code_signing_and_updates_signature_verification_before_execution, docs_decisions_adr_0026_code_signing_and_updates_ov_manual_updates, docs_decisions_adr_0020_plugin_and_skill_signing_signed_manifest_field, docs_decisions_adr_0020_plugin_and_skill_signing_jarvispack_import, docs_decisions_adr_0022_msix_distribution_msix_secondary_channel, docs_decisions_adr_0014_default_english_voice_redistribution_licensing_gap [INFERRED 0.85]
- **Vault Data Lifecycle and Exposure Control** — docs_decisions_adr_0024_data_retention_defaults_per_stream_defaults, docs_decisions_adr_0024_data_retention_defaults_cascade_on_expiry, docs_decisions_adr_0025_screenshot_retention_task_only_default, docs_decisions_adr_0021_encrypted_sync_and_backup_secret_exclusion_rule, docs_decisions_adr_0021_encrypted_sync_and_backup_portable_identity_export, docs_decisions_adr_0017_embedding_model_rebuildable_derived_index [EXTRACTED 1.00]
- **Arc Reactor Icon Composition (chassis + core + emissive palette)** — resources_icons_jarvis_icon, resources_icons_jarvis_icon_circular_chassis, resources_icons_jarvis_icon_triangular_core, resources_icons_jarvis_icon_cyan_glow_palette [EXTRACTED 1.00]
- **Windows Shell Asset Readiness Constraints** — resources_icons_jarvis_icon, resources_icons_jarvis_icon_transparent_alpha_canvas, resources_icons_jarvis_icon_circular_chassis, resources_icons_jarvis_icon_product_brand_identity [INFERRED 0.75]
- **Phase 0 Structural Enforcement Mechanisms (Tests and Schema Guards)** — docs_decisions_adr_0003_closed_capability_set_no_generic_execution_test_no_shell_scan, docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_test_layering, docs_decisions_adr_0006_layered_configuration_override_only_persistence_extra_forbid, docs_decisions_adr_0002_sqlite_single_source_of_truth_schema_version_startup_check, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_no_elevation_manifest_check [INFERRED 0.85]
- **Process-Separation Promotion Path and Its Triggers** — docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_single_process_worker_threads, docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_process_promotion_triggers, docs_decisions_adr_0001_python_first_rust_deferred_qwen3_tts_worker, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_scoped_helper_process, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_helper_ipc_discipline, docs_decisions_adr_0001_python_first_rust_deferred_typed_ipc [EXTRACTED 1.00]
- **Open Phase 6 Productisation Decisions** — docs_decisions_adr_0011_public_product_name_adr, docs_decisions_adr_0012_shell_technology_for_first_public_build_adr, docs_decisions_adr_0013_installer_technology_adr, docs_decisions_adr_0013_installer_technology_msix_sequencing_dependency, docs_decisions_adr_0011_public_product_name_trademark_screen_criteria [EXTRACTED 1.00]

## Communities (251 total, 102 thin omitted)

### Community 0 - "TaskState"
Cohesion: 0.05
Nodes (52): Task subsystem (L3): state machine, durable store, locks, scheduler, recovery., BaseModel, Task records (PRD FR-120 .. FR-133)., One unit of work with a durable state machine., Support for a completion claim (PRD FR-132)., ResourceLockRecord, Task, TaskEvidence (+44 more)

### Community 1 - "DuplexCoordinator"
Cohesion: 0.03
Nodes (59): BargeInReport, DuplexCoordinator, DuplexMode, PlaybackWindow, datetime, Enum, str, Full-duplex audio and barge-in (ADR-0028, PRD FR-015, section 11.3). ADR-0028… (+51 more)

### Community 2 - "AudioUnavailable"
Cohesion: 0.05
Nodes (40): Cue, cue_audio(), _faded(), Short audio cues, so Jarvis is legible without looking at the screen. The…, The cues this build makes, and what each one means., Render one cue, or None if numpy is unavailable or the name is unknown. Never…, Taper both ends, or the tone starts and stops with a click., AudioFormat (+32 more)

### Community 3 - "types.py"
Cohesion: 0.05
Nodes (43): datetime, In-process typed event bus (ADR-0005). Deliberately not a message broker: no…, Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe., Subscription, Typed event bus and the domain event vocabulary., Event, LockAcquired, LockContended (+35 more)

### Community 4 - "test_permission_engine.py"
Cohesion: 0.05
Nodes (60): _c(), capabilities_by_risk(), capability(), capability_ids(), The capability catalogue — PRD section 11.1 expressed as data. Risk…, Permission model, capability catalogue and evaluation engine., Capability, Decision (+52 more)

### Community 5 - "AudioChunk"
Cohesion: 0.04
Nodes (60): frames_from_bytes(), Cut a recording into frames. Used to replay fixtures through the pipeline., Record how loud Jarvis's own output was. Reported, not compared., Watch raw frames, for measuring the room (PRD FR-017). Observers see frames…, AudioChunk, A block of mono audio. ``samples`` is raw bytes, never a file path., Measure the room and apply the threshold (PRD FR-017)., VoiceStatus (+52 more)

### Community 6 - "ResourceLockManager"
Cohesion: 0.06
Nodes (48): Release everything this runtime holds. Called during shutdown., Release locks whose owning runtime instance is gone (PRD FR-006). Without this,…, Exclusive, persisted, owner-attributed locks., ResourceLockManager, CRUD plus a validated state machine over the ``task`` tables., TaskStore, Task state machine, durable store, locks and scheduler (PRD FR-120 .. FR-133)., A partial acquisition would deadlock two tasks against each other. (+40 more)

### Community 7 - "service.py"
Cohesion: 0.06
Nodes (38): capture_available(), CaptureSession, default_input_device(), host_api_names(), list_devices(), Microphone capture and playback (PRD FR-016, FR-013, ADR-0028). ``sounddevice``…, The best input to open, preferring WASAPI over the system default. Windows…, Match device names across host APIs, which truncate them differently. (+30 more)

### Community 8 - "Option B: Per-Stream Retention Defaults with Expiry"
Cohesion: 0.05
Nodes (55): ADR-0014: Default English Voice, espeak-ng GPL-Family Licensing Consideration, Kokoro bm_george Default Voice, Per-Download Provider and Licence Disclosure, Voice Pack Redistribution Licensing Gap, Windows SAPI Emergency Fallback, ADR-0015: Additional TTS Providers, Model Resource Scheduler (FR-039) (+47 more)

### Community 9 - "pipeline.py"
Cohesion: 0.05
Nodes (40): ActivationRoute, CommandHeard, _join(), ListeningState, Enum, str, The voice loop (PRD sections 10.2 to 10.4, ADR-0027, ADR-0028). One place where…, F9 released. Transcribe what was captured. (+32 more)

### Community 10 - "EventBus"
Cohesion: 0.07
Nodes (43): E, MonkeyPatch, EventBus, Thread-safe publish/subscribe with subclass matching., Receive ``event_type`` and every subclass of it., Deliver to every matching handler. Returns the number invoked. Handler…, approving_invoker(), audit() (+35 more)

### Community 11 - "VoicePipeline"
Cohesion: 0.07
Nodes (31): Begin waiting for the wake phrase, if enrolment allows it., Stop, and forget everything held. Nothing survives in memory., F9 pressed. Capture a command without a wake phrase (FR-018)., One captured frame. Called from the audio thread., Only ever enabled after enrolment has been measured (ADR-0016)., Capture in, commands out. Owns the listening state machine., VoicePipeline, NullWakeDetector (+23 more)

### Community 12 - "ApplicationCatalogue"
Cohesion: 0.15
Nodes (44): ApplicationCatalogue, ArgumentKind, CatalogueError, LaunchKind, str, ValueError, The user's approved applications. Seeded, editable, never model-written., A catalogue entry was refused. Raised at registration, not at launch. (+36 more)

### Community 13 - "JarvisApplication"
Cohesion: 0.05
Nodes (22): QApplication, JarvisApplication, QObject, Connect the voice service to the Voice screen and to push-to-talk., A choice made on the Voice screen must survive a restart., Runs on the audio thread, so it only queues work onto the GUI one., Runs on the Qt main thread, courtesy of the bridge., The keyboard route to a waiting request (PRD NFR-030). (+14 more)

### Community 14 - "tasks/store.py"
Cohesion: 0.08
Nodes (31): LookupError, from_iso(), new_id(), datetime, Small shared primitives used across every layer. Kept deliberately tiny:…, A fresh opaque identifier. UUID4 hex, no dashes, stable length., Timezone-aware current time. Never use ``datetime.utcnow()``., Serialise to ISO-8601 with an explicit offset, or ``None``. (+23 more)

### Community 15 - "AppConfig"
Cohesion: 0.10
Nodes (28): Configuration layer (L1). Must not import anything above L1., AppConfig, The whole validated configuration tree., _atomic_write(), ConfigError, ConfigStore, deep_merge(), _delete_by_path() (+20 more)

### Community 16 - "NetworkMode"
Cohesion: 0.07
Nodes (31): NetworkMode, str, is_loopback_url(), OllamaHealth, OllamaHealthChecker, Exception, Ollama health check (ADR-0007). Two boundary rules are enforced here rather…, True when the URL's host is a loopback address or resolves only to one. (+23 more)

### Community 17 - "test_phase0_exit_criteria.py"
Cohesion: 0.05
Nodes (38): parametrize, Path, Phase 0 exit criteria and hard constraints. One test (or small group) per…, The tool set stays small and low risk. Phase 0 registered exactly one tool.…, PRD FR-048: succeeded requires verification, so it must be declared., PRD section 13.4: free-form text can never be executed., Screenshot-based computer control is still out of scope. Phase 1 legitimately…, PRD section 4.4: nothing may silently become permanent memory. (+30 more)

### Community 18 - "JarvisCore"
Cohesion: 0.08
Nodes (37): RecoveryReport, JarvisCore, Everything except the user interface., Let the shell supply what only it can: desktop notifications. ``notify.show``…, Reverse of start, and idempotent., Queue a health check through the task machinery. Returns the task id., _new_core(), Full core lifecycle, crash recovery and settings durability. (+29 more)

### Community 19 - "Database"
Cohesion: 0.08
Nodes (27): Connection, Cursor, Exception, Row, AuditLog, Database, DatabaseError, Any (+19 more)

### Community 20 - "ToolCall"
Cohesion: 0.11
Nodes (42): RetryPolicy, A proposed action. Comes from the planner, the GUI, a skill or a schedule., ToolCall, allow(), make_tool(), RiskLevel, Verification, The six-step invoker pipeline (PRD section 13.4, ARCHITECTURE.md 6.6). (+34 more)

### Community 21 - "AuditLog"
Cohesion: 0.09
Nodes (29): json_dumps(), json_loads(), Any, Deterministic JSON for storage and for the append-only audit log., AuditLog, Any, datetime, Path (+21 more)

### Community 22 - "test_grounding_and_history.py"
Cohesion: 0.10
Nodes (28): Formality, Humour, PersonalityProfile, PersonalityProposal, PersonalityStore, ProposalStatus, Enum, str (+20 more)

### Community 23 - "MainWindow"
Cohesion: 0.07
Nodes (29): QMainWindow, MainWindow, Navigation shell over live core state., Closing the window leaves Jarvis running in the tray (PRD FR-001)., test_the_window_says_plainly_when_nothing_is_waiting(), test_conversation_is_a_live_area_not_a_phase_placeholder(), test_the_home_screen_reports_the_voice_stack_honestly(), fixture (+21 more)

### Community 24 - "test_config.py"
Cohesion: 0.06
Nodes (27): PathLike, expand_path(), find_defaults_config(), _platform_default_root(), Data-vault path resolution. This is the *only* module permitted to expand…, Locate the shipped ``defaults.yaml``. Order: ``JARVIS_DEFAULTS_CONFIG`` env…, Expand ``%VARS%``, ``$VARS`` and ``~`` then normalise to an absolute path., Path (+19 more)

### Community 25 - "test_web_search_and_catalogue.py"
Cohesion: 0.08
Nodes (36): build_argv(), default_catalogue(), Construct the argument vector. Pure, so it is directly testable., The Phase 1 seed: exactly the applications PRD section 21 names. Paths are the…, parametrize, Searching, and opening an application that takes an optional argument. Both…, The model sometimes passes a URL anyway. It becomes a search for it., The owner's own default. It was DuckDuckGo; they asked for Google. Pinned by a… (+28 more)

### Community 26 - "VoiceController"
Cohesion: 0.07
Nodes (13): QObject, Play a short tone. Never blocks, never raises onto the caller., Remember a worker so shutdown can wait for it, without hoarding., Silence Jarvis now. Returns whether there was anything to silence., Start or stop waiting for the wake phrase, on the user's say-so., Transcription blocks for seconds, so never on the GUI thread., Switch microphone. Reopens the stream if one is already open., Collect a few seconds of room tone, then set the threshold. (+5 more)

### Community 27 - "JarvisTrayIcon"
Cohesion: 0.07
Nodes (21): ActivationReason, QAction, QMenu, QSystemTrayIcon, JarvisTrayIcon, QObject, Colour, shape, tooltip and accessible name all change together., Enable the keyboard route and say how many are waiting. (+13 more)

### Community 28 - "llm/conversation.py"
Cohesion: 0.06
Nodes (32): The conversation engine (PRD FR-040, FR-042, FR-047, FR-048, section 13.4).…, GroundedClaim, GroundingReview, _hedge(), Enum, str, Where an answer came from, and what counts as done (PRD FR-047, FR-048). Two…, The verification value of a succeeded result; empty if it did not succeed. (+24 more)

### Community 29 - "tools/ports.py"
Cohesion: 0.09
Nodes (22): ApprovalRequested, ApprovalResolved, A tool is waiting on the user. The tray must make this impossible to miss.…, Decision, GrantScope, The approval queue — step 5 of the invoker pipeline, made answerable. ADR-0027…, Declare whether a user interface is actually connected. Until one is, queueing…, Block the calling thread until answered, or until the request expires. Called… (+14 more)

### Community 30 - "system_health.py"
Cohesion: 0.12
Nodes (28): BaseModel, Enum, Exception, str, The tool contract (PRD section 13.2). A *tool* is the only way the agent…, Per-invocation context handed to a tool. Carries no ambient authority., What a tool returns on success., Raised by a tool to report a declared failure. The code must be declared. (+20 more)

### Community 31 - "ConversationEngine"
Cohesion: 0.11
Nodes (29): ConversationEngine, Runs one turn: prompt, model, tools, grounding, reply., ChatResponse, What a provider returned. ``text`` is for the user. ``tool_calls`` is for the…, _decode(), EchoParams, EchoResult, EchoTool (+21 more)

### Community 32 - "ModelRouter"
Cohesion: 0.08
Nodes (23): Conversation history and private sessions (PRD FR-045, FR-046, AT-014). A…, Turns for a live conversation, from memory; otherwise from storage., StoredMessage, ChatRole, ModelRole, Enum, str, The chat provider boundary (ARCHITECTURE.md section 8, PRD FR-040, section… (+15 more)

### Community 33 - "PermissionEngine"
Cohesion: 0.11
Nodes (18): PermissionEvaluation, PermissionGrant, PermissionRequest, DefaultPolicy, PermissionEngine, AuditLog, Capability, Decision (+10 more)

### Community 34 - "play"
Cohesion: 0.08
Nodes (35): _as_float_array(), default_output_device(), play(), playback_available(), playback_unavailable_reason(), Audio playback (PRD FR-030, FR-033, ADR-0028). The missing half of the voice…, Decode the chunk's bytes into the float32 mono array a stream wants., Play one chunk, blocking, and report what was heard. Blocking by design: the… (+27 more)

### Community 35 - "launch.py"
Cohesion: 0.08
Nodes (32): _basename(), launch(), launch_argv(), LaunchOutcome, process_running(), Enum, The one authorised process-creation call site (ADR-0029). Everything about this…, What actually happened. ``verified`` is never assumed (constraint 9). (+24 more)

### Community 36 - "test_application_launch.py"
Cohesion: 0.08
Nodes (31): Refuse an unsafe catalogue entry at registration time (constraint 4)., validate_entry(), executable_entry(), parametrize, The constrained launcher (ADR-0029). Every test here maps to one of the nine…, Adding a shell through the catalogue is still adding a shell., A document would let the file-association table choose what runs., No quoting to get wrong, because nothing parses the vector. (+23 more)

### Community 37 - "ApprovalQueue"
Cohesion: 0.13
Nodes (28): ApprovalQueue, Called whenever the pending set changes. Used by the tray., Holds requests between the thread that needs an answer and the user. Implements…, make_request(), fixture, RiskLevel, queue(), The approval queue (ADR-0027). The timeout path is the security-critical one… (+20 more)

### Community 38 - "ApprovalPanel"
Cohesion: 0.10
Nodes (18): PendingApproval, One unanswered request. Mutable, unlike everything on the event bus., ApprovalController, ApprovalPanel, Decision, GrantScope, QObject, QWidget (+10 more)

### Community 39 - "schema.py"
Cohesion: 0.11
Nodes (29): model_validator, AudioConfig, _Base, ConversationLanguageConfig, DefaultPermissionPolicy, LanguageConfig, LlmConfig, LoggingConfig (+21 more)

### Community 40 - "OllamaChatProvider"
Cohesion: 0.11
Nodes (21): _as_int(), OllamaChatProvider, Any, Ollama chat completion (PRD FR-040, section 13.4, ADR-0007). Inherits the two…, Read only the structured field. Never parse prose for an action., Describe one registered tool in the format Ollama expects. Built from the…, Chat against a loopback Ollama. Blocking; call from a worker thread., tool_schema_for() (+13 more)

### Community 41 - "Resource Lock Model"
Cohesion: 0.22
Nodes (11): Approval Dialog Design, Consequential-Action Audit Log, Emergency Stop, IDE-Agent Orchestration, jarvis.db SQLite Single Source of Truth, Resource Lock Model, Task Checkpoints and Durability, Task Completion Evidence (+3 more)

### Community 42 - "redact"
Cohesion: 0.10
Nodes (27): Audit logging and secret redaction., classify_content(), is_content_key(), is_secret_key(), Any, Secret redaction for the audit log (PRD section 11.5, FR-259). Redaction…, Return a copy of ``value`` safe to persist in the audit log. Mappings,…, Describe a value without reproducing it. Used where the *shape* of user content… (+19 more)

### Community 43 - "ConversationStore"
Cohesion: 0.08
Nodes (20): ConversationStore, AuditLog, Begin a conversation. ``persist=False`` is a private session., Stop recording this conversation, and erase what was recorded. Per-conversation…, Remove a conversation and its turns. Messages cascade., Creates conversations and records turns, when recording is permitted., Global history control (PRD FR-045). Affects new conversations., history() (+12 more)

### Community 44 - "tools/__init__.py"
Cohesion: 0.12
Nodes (26): ProhibitedCapabilityBlocked, A prohibited tool or capability was requested. Always a security signal., ToolRegistered, Protocol, What an implementation must provide., Tool, Tool contract, allow-list registry, prohibited guard and the invoker. This…, assert_tool_id_permitted() (+18 more)

### Community 45 - "speakable_text"
Cohesion: 0.11
Nodes (27): Match, A URL read aloud in full is unbearable; the host is the useful part., Strip what a phonemiser would recite rather than say (PRD FR-030). Presentation…, speakable_text(), _spoken_host(), parametrize, What Jarvis says aloud is not the same string as what it writes down. From a…, Stripping runs first, so emphasis cannot hide a key from the patterns. (+19 more)

### Community 46 - "PlaybackReport"
Cohesion: 0.15
Nodes (21): PlaybackReport, What playback actually did. Never assumed by the caller., What was synthesised, and what was actually played (PRD FR-048). Carries the…, SpokenResult, _audio(), ``voice.speak`` must not claim speech it cannot evidence (FR-048, AT-018). The…, FR-034: say something was withheld rather than quietly changing it., The invoker rejects an undeclared code, so this must stay in step. (+13 more)

### Community 47 - "test_wake_install.py"
Cohesion: 0.14
Nodes (26): is_installed(), All required files present. Says nothing about whether they *work*., make_files(), Path, The wake-model bootstrap (ADR-0016, PRD section 17.2). No test here downloads…, A corrupt download must not be reported as ready (ADR-0010)., The command's exit code reflects usability, not download success., Hey Travis" measured 0.489, so 0.5 left almost no margin. (+18 more)

### Community 48 - "test_empty_model_reply.py"
Cohesion: 0.13
Nodes (22): _describe_silence(), What to say when the model returned no words at all. It happens: a small model…, _conversation(), _engine(), NoopInvoker, parametrize, A model that returns nothing must not produce a blank, confident answer. From a…, It reports what ran. It must not guess what the model meant to say. (+14 more)

### Community 49 - "ConversationPanel"
Cohesion: 0.11
Nodes (21): ConversationPanel, Text conversation with the local model., panel(), fixture, The Conversation screen (PRD section 9.5, FR-046, FR-047)., The distinction is the whole point of FR-047., Model output is data here too, including in the transcript., test_a_missing_reason_still_produces_an_explanation() (+13 more)

### Community 50 - "test_secret_store.py"
Cohesion: 0.14
Nodes (26): SecretStore, fixture, skipif, WINDOWS_ONLY, The secret store (ADR-0030, PRD 18.3, NFR-022, FR-169, AT-016). The assertions…, Never partial, never best-effort plaintext., Lifting a value under a different name must not decrypt it., Degrading to weaker protection would be worse than refusing (ADR-0010). (+18 more)

### Community 51 - "Turn"
Cohesion: 0.13
Nodes (22): One user request and everything that came of it., Turn, ExplodingEngine, FakeEngine, _pump(), The wiring between the Conversation screen and the engine. The panel tests…, A silent failure is the worst outcome; it must always say something., Each send created a QThread whose quit signal could never arrive. (+14 more)

### Community 52 - "VoiceService"
Cohesion: 0.08
Nodes (8): What can interrupt Jarvis right now, given the microphone's state., No enrolment has been run in this build, so nothing has passed., Whether anything can actually be heard. Speaking depends on it., Re-pin the model hubs after a network-mode change (AT-001)., Attach the recording indicator (PRD FR-013). Capture may not start without…, Where a finished spoken command goes. Nothing listened before., Owns the providers, the pipeline and the capture session., VoiceService

### Community 53 - "VaultPaths"
Cohesion: 0.14
Nodes (5): Path, Instance-scoped files such as the single-instance lock., Create the vault layout. Idempotent., Every path the application is allowed to write to, derived from one root., VaultPaths

### Community 54 - "test_voice_reply_behaviour.py"
Cohesion: 0.11
Nodes (17): application(), FakeEngine, _pump(), fixture, How Jarvis behaves when it was spoken to, and who it thinks you are. From a…, Typing means you are looking at the screen. Do not talk over it., Otherwise a voice failure is completely silent and invisible., It did this every time, including from the tray with nothing open. (+9 more)

### Community 55 - "._execute"
Cohesion: 0.16
Nodes (13): AuditCategory, Any, BaseModel, RiskLevel, ToolContext, ToolExecution, Verification, Make "don't ask again" stick, as a scoped DENY grant (ADR-0027). No engine… (+5 more)

### Community 56 - "model_directory"
Cohesion: 0.19
Nodes (23): install_wake_model(), installed_files(), missing_files(), model_directory(), Path, One-time wake-word model installation (ADR-0016, PRD section 17.2). **No wake-…, The keyword arguments that point openWakeWord at the vault's copies.…, Actually initialise the detector (ADR-0010). "The files are on disk" is not the… (+15 more)

### Community 57 - "Conversation"
Cohesion: 0.10
Nodes (13): _describe_result(), Any, Send one proposal through the invoker. Never around it., Describe only registered tools. The model cannot learn of others., Render a tool result for the model, without inflating it., Conversation, One conversation, persisted or not., The instruction that accompanies every wrapped observation. (+5 more)

### Community 58 - "ToolSpec"
Cohesion: 0.12
Nodes (18): Any, model_validator, Schema the planner sees. Free-form text can never reach the invoker., Everything a tool declares about itself., ToolSpec, _Params, BaseModel, The prohibited-capability guard (ADR-0003, PRD sections 11.1 and 13.3). (+10 more)

### Community 59 - "VoicePanel"
Cohesion: 0.09
Nodes (7): QWidget, Always show the exact destination path, installed or not., State the phrase literally. Never label it 'Jarvis' (FR-011)., Show what has been measured. Never imply more than that., Show the transcript, so a misheard word is visibly a mishearing., Devices, voices, wake phrase and enrolment., VoicePanel

### Community 60 - "core.py"
Cohesion: 0.18
Nodes (15): OllamaHealth, AppStarted, AppStopping, ConfigChanged, EmergencyStopCompleted, EmergencyStopRequested, HealthChecked, NetworkModeChanged (+7 more)

### Community 61 - "describe_voice_stack"
Cohesion: 0.16
Nodes (12): _capture_status(), ComponentStatus, describe_voice_stack(), Path, What of the voice stack is actually usable right now (ADR-0010, NFR-014). Audio…, Report each component's real state, reading configuration when given., One part of the voice stack, and why it is or is not usable., _stt_status() (+4 more)

### Community 62 - "RingBuffer"
Cohesion: 0.10
Nodes (9): datetime, Forget everything held. Called whenever listening stops., Everything ever accepted, so a test can prove discarding happened., A bounded, in-memory window of the most recent audio. Thread-safe: the capture…, Append audio, discarding whatever falls out of the window., Everything currently held, as one chunk. Does not clear the buffer., The held frames individually, for a consumer that wants to keep going., Snapshot and clear, for when a wake event promotes it to a command. (+1 more)

### Community 63 - "ToolInvoker"
Cohesion: 0.12
Nodes (18): AuditLog, EventBus, Validates, permits, locks, approves, executes and audits. In that order., ToolInvoker, AutoApprovalPort, Decision, GrantScope, Test double. Never wire this into a running application. Guarded so a mistake… (+10 more)

### Community 64 - "test_approval_dialog.py"
Cohesion: 0.21
Nodes (21): _buttons(), make_request(), panel(), _pending(), fixture, RiskLevel, queue(), The approval surface (PRD section 11.2, ADR-0027). Runs offscreen. What is… (+13 more)

### Community 65 - "test_reply_speech_policy.py"
Cohesion: 0.16
Nodes (20): _decide(), parametrize, When Jarvis should open its mouth, and when a beep is the right answer.…, Otherwise Jarvis waits silently for an answer nobody knows it wants., A bad config value must not silently make Jarvis mute., what's the volume?" runs device.volume and still deserves an answer., _Result, test_a_command_that_worked_gets_a_cue_not_a_sentence() (+12 more)

### Community 66 - "test_listening_controls.py"
Cohesion: 0.10
Nodes (18): application(), _pump(), fixture, Turning listening on and off, and saying what was heard. Two changes the owner…, Otherwise a refresh every 2 seconds would restart the microphone., It said that permanently, with no way for the user to change it., Off must mean off — not "opens the mic and says it is off"., test_a_heard_command_reaches_the_screen() (+10 more)

### Community 67 - "test_voice_wiring.py"
Cohesion: 0.10
Nodes (19): application(), _pump(), fixture, The Voice screen's controls must be connected, or honestly disabled. Every…, Recording without a visible indicator is a prohibited capability., Without one, capture could start with nothing on screen., The pipeline transcribed commands that had no listener at all., ``application.voice`` stayed None, so push-to-talk always refused. (+11 more)

### Community 68 - "test_hotkeys_and_startup.py"
Cohesion: 0.13
Nodes (17): parse_hotkey(), Parse ``"Ctrl+Alt+Pause"`` or ``"F9"``. Raises :class:`HotkeyError`., parametrize, skipif, Global hotkeys and start-at-sign-in (PRD section 11.3, FR-018, FR-002). Parsing…, PRD section 11.3 and config/defaults.yaml agree on this combination., FR-018 and ADR-0027 specify bare F9, with no modifier., An emergency stop that fires forty times is not better than one. (+9 more)

### Community 69 - "test_runtime_primitives.py"
Cohesion: 0.13
Nodes (14): Path, Acquire once at startup; release at shutdown. ``acquired`` is the only thing…, SingleInstanceGuard, Single-instance guard, workers and schema migrations., test_a_lock_file_from_a_dead_process_is_reclaimed(), test_a_second_instance_is_refused(), test_acquire_or_raise_explains_the_refusal(), test_acquiring_twice_is_idempotent() (+6 more)

### Community 70 - "test_tool_specs_are_valid.py"
Cohesion: 0.14
Nodes (19): Every registered tool's declared contract must actually be usable.…, A capability the catalogue has never heard of can never be granted., Every spec the real core registers, plus the shell-only ones., A lock name the manager rejects makes the tool permanently unusable., Named explicitly: this is the one that was wrong., The invoker validates locks before doing anything. Prove it passes., CLAUDE.md: every external interaction declares a timeout., FR-048: `succeeded` requires verification, so it must be described. (+11 more)

### Community 71 - "test_cross_thread_marshalling.py"
Cohesion: 0.17
Nodes (18): application(), _FakeReport, _from_a_plain_thread(), _pump(), fixture, Work handed to the GUI thread from a non-Qt thread must actually arrive.…, The tool reported success for a notification that never appeared., Any new QTimer.singleShot in the shell must be on the GUI thread. Checked by… (+10 more)

### Community 72 - "module_available"
Cohesion: 0.14
Nodes (9): module_available(), True if ``module`` could be imported, without importing it., build_wake_detector(), OpenWakeWordDetector, openWakeWord over a pretrained base model, with a personal threshold., Applied after enrolment measurement chooses one., Highest score this frame produced across the loaded models., Yield an event whenever a frame crosses the threshold. (+1 more)

### Community 73 - "test_stop_speaking.py"
Cohesion: 0.13
Nodes (15): application(), fixture, Making Jarvis shut up — the route that does not depend on tuning. Reported from…, ADR-0028: barge-in is not emergency stop, and conflating them is exactly how…, The tray entry exists whether or not Kokoro is installed., Put the pipeline into the state it is in while Kokoro plays., Silencing speech must not have replaced what it already did., _Report (+7 more)

### Community 74 - "media.py"
Cohesion: 0.20
Nodes (10): _INPUT, _INPUTUNION, _KEYBDINPUT, media_available(), Enum, Media and volume control (PRD FR-094, catalogue `media.playback_control`,…, Send one media or volume key. Returns whether Windows accepted it. ``action``…, send_media_key() (+2 more)

### Community 75 - "test_no_shell.py"
Cohesion: 0.20
Nodes (17): _findings(), parametrize, Path, The load-bearing security test (ADR-0003). Phase 0 exit criterion: *no generic…, No shipped module may start a process or evaluate generated code., ADR-0029 authorises one call site. A second is a new ADR, not a row here. This…, The allow-list entry must describe reality, not a module that moved., A guard on the guard: prove the detector is not vacuously passing. (+9 more)

### Community 76 - "ui/__init__.py"
Cohesion: 0.16
Nodes (12): QColor, QIcon, Enum, str, Tray state icons, drawn programmatically. Two reasons not to ship image files:…, PRD section 9.1 tray states., A non-colour distinguishing mark (PRD NFR-033)., Render the icon for a state. Colour *and* shape differ per state. (+4 more)

### Community 77 - "._record"
Cohesion: 0.14
Nodes (6): Open the microphone. Returns False, honestly, if it cannot., Synthesise **and play**, then report what actually came out. Synthesis alone…, Choose the microphone (PRD FR-016). Reopens an open stream., Cut playback short. Speech only — never locks, never tasks. The deterministic…, Listen for the wake phrase. Returns (started, why not). ADR-0016 originally…, Close the microphone and forget everything buffered.

### Community 78 - "GlobalHotkeys"
Cohesion: 0.14
Nodes (8): GlobalHotkeys, Registers hotkeys on a dedicated thread and dispatches their actions. Off…, Run the registration and message loop on its own thread., Invoke a binding's action directly. The test and menu route., The tray and the tests need a route that does not need a real keypress., test_a_binding_can_be_triggered_directly(), test_bindings_are_addressable_by_name(), test_starting_a_disabled_manager_is_a_no_op()

### Community 79 - "test_at003_app_launch.py"
Cohesion: 0.13
Nodes (16): catalogue(), fixture, parametrize, AT-003 — "Jarvis, open Sea of Thieves" launches it and verifies it. > When the…, ADR-0029 constraint 8: no direct path from a plan to Popen., Capture argv instead of starting anything, and control verification., AT-018: unverified is a distinct outcome, not a quiet success., recorded_launches() (+8 more)

### Community 80 - "Worker"
Cohesion: 0.15
Nodes (6): ABC, BaseException, A named background thread with a cooperative stop., Signal and wait. Returns ``True`` when the thread actually stopped., Run until :attr:`stop_requested`. Check it often., Worker

### Community 81 - "Automation Worker"
Cohesion: 0.16
Nodes (17): Google Antigravity IDE Adapter, Application Catalogue and Aliases, Automation Worker, Dedicated Jarvis Brave Profile, Phased Delivery Plan (Phase 0-6), Deterministic Before Visual (Automation Hierarchy), Local Document Understanding, Executor Role (+9 more)

### Community 82 - "Capability Risk Classes"
Cohesion: 0.18
Nodes (14): Capability Risk Classes, Filesystem Tool Root Scoping, .jarvispack Portable Identity Package, Windows Known Folder Resolution, Password and Credential Field Protection, Privacy-Preserving Audio Ring Buffer, Tool Reversibility Metadata, Safe Deletion via Recycle Bin (+6 more)

### Community 83 - "test_offline_speech_models.py"
Cohesion: 0.18
Nodes (14): hub_is_offline(), clean_environment(), FakeConfig, fixture, Offline mode must silence the speech model hubs too (PRD AT-001). The Ollama…, Local assistant still permits fetching a model the user asked for., Someone who exported these wants local-only loading. Do not undo it., The switch is read when a model loads, which is long after start-up. (+6 more)

### Community 84 - "main_window.py"
Cohesion: 0.24
Nodes (8): NavArea, _NotImplementedPanel, QWidget, Main window: the fifteen navigation areas of PRD section 9.3. Six areas are…, A heading, a refresh button and a read-only text area., Says exactly what is missing and when it arrives. Never a fake screen., _TablePanel, _TextPanel

### Community 85 - "test_lazy_audio_imports.py"
Cohesion: 0.20
Nodes (15): _module_name(), _module_scope_imports(), parametrize, Path, Audio dependencies stay optional and lazily imported (ADR-0010, NFR-014).…, The property all of the above exists to protect., Imports at module level only — imports inside a function are the point., A guard on the guard: prove the detector is not vacuously passing. (+7 more)

### Community 86 - "app.py"
Cohesion: 0.21
Nodes (13): _asks_something(), Enum, str, When a spoken request deserves a spoken answer (PRD FR-030, FR-048). Answering…, The user-facing setting, ``audio.speak_replies``., What the shell should do with a finished reply., Decide how a finished turn should sound. ``spoken_request`` is the whole reason…, ReplyVoice (+5 more)

### Community 87 - "WorkerSupervisor"
Cohesion: 0.15
Nodes (8): Starts and stops workers in a defined order., Stop in reverse order. Returns the names that stopped cleanly., WorkerSupervisor, _CountingWorker, test_a_worker_runs_off_the_calling_thread(), test_a_worker_stops_cooperatively(), test_duplicate_worker_names_are_refused(), test_the_supervisor_starts_and_stops_in_order()

### Community 88 - "test_layering.py"
Cohesion: 0.26
Nodes (14): _imported_modules(), _module_name(), _package_of(), Path, Layering invariants (ARCHITECTURE.md section 5, ADR-0004). The rule that makes…, A fresh interpreter can import the whole engine with no Qt module loaded., Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.…, Spelled out separately because it is the invariant people break first. (+6 more)

### Community 89 - "ADR-0003: A Closed Capability Set — No Generic Execution Primitive"
Cohesion: 0.15
Nodes (16): One SQLite Connection Per Thread, ADR-0003: A Closed Capability Set — No Generic Execution Primitive, No Generic Execution Primitive, os.startfile Named Future Allow-Listed Exception, tests/security/test_no_shell.py Source Tree Scan, Tool Registry Identity and Pattern Denylist, ADR-0004: Single Process, Thread Isolation for Phases 0–3, Layering Rule: Core Packages Must Not Import PySide6 (+8 more)

### Community 90 - "single_instance.py"
Cohesion: 0.15
Nodes (7): RuntimeError, AlreadyRunningError, _process_is_alive(), Single-instance enforcement (PRD FR-005). Only one interactive Jarvis may run…, Remove a lock file whose owning process is gone., Is a process with this id currently running? ``os.kill(pid, 0)`` is the POSIX…, Another instance already holds the single-instance handle.

### Community 91 - "AuditCategory"
Cohesion: 0.18
Nodes (7): AuditCategory, Enum, str, Why the record exists. Used for filtering in the GUI., JSON schemas the planner is offered. Nothing outside this list exists., Holds every tool the runtime may call. Nothing else can., ToolRegistry

### Community 92 - "ApplicationEntry"
Cohesion: 0.18
Nodes (8): ApplicationEntry, One application the user has approved Jarvis to open. Created by the user,…, Constraint 5: validate the caller's argument against the entry's type., Find an entry by id, display name or alias. Never by path., _validate_argument(), test_a_store_app_uses_the_fixed_explorer_broker(), catalogue(), fixture

### Community 93 - "test_at014_private_session.py"
Cohesion: 0.18
Nodes (13): parametrize, AT-014 — a private session produces no permanent record after it ends. Asserted…, Everything the vault has written, as raw bytes., A control: prove the byte search would have found it if written., Privacy is not the same as invisibility: the event is auditable., test_a_normal_session_is_recorded_so_the_test_above_means_something(), test_a_private_conversation_is_marked_private_to_the_user(), test_a_private_session_leaves_no_record_anywhere() (+5 more)

### Community 94 - "On-Demand Narrowly Scoped Elevated Helper Process"
Cohesion: 0.22
Nodes (13): ADR-0001: Python-First Implementation with Rust Deferred, Python 3.11 + PySide6 Implementation Stack, Qwen3-TTS Isolated Python 3.12 Worker, Rust/Tauri Native Shell Deferred Past Phase 3, Authenticated Typed IPC for Future Shell, Process-Separation Promotion Triggers, Helper IPC Discipline (Named Pipe or Loopback, Rotating Token), No Interaction with the Windows Secure Desktop or UAC Prompt (+5 more)

### Community 95 - "SQLite (jarvis.db) Canonical Transactional Store"
Cohesion: 0.23
Nodes (13): ADR-0002: SQLite as the Single Source of Truth, Large Binary Artefacts Stored on Disk, Referenced by Path, Derived Rebuildable Stores Hold No Unique Information, SQLite (jarvis.db) Canonical Transactional Store, WAL Mode Concurrent Readers, ADR-0005: An In-Process Typed Event Bus, Bus Is Notification, Not System of Record, ADR-0006: Layered Configuration with Override-Only Persistence (+5 more)

### Community 96 - "jarvis.core.events In-Process Publish/Subscribe Bus"
Cohesion: 0.20
Nodes (11): Versioned Forward-Only Migrations, Full ORM (SQLAlchemy) Rejected for Phase 0, Schema-Version Startup Check (Newer DB is Hard Failure), jarvis.core.events In-Process Publish/Subscribe Bus, Frozen Pydantic Event Models with Subclass Matching, Per-Handler Exception Isolation, ConfigChanged Runtime Event, pydantic extra="forbid" Loud Typo Failure (+3 more)

### Community 97 - "EnrolmentMeasurement"
Cohesion: 0.17
Nodes (7): choose_threshold(), EnrolmentMeasurement, measure_enrolment(), The measured result. ADR-0016 criterion 1: without this, no enabling., Good enough to enable always-listening (criterion 2)., Score held-out positives and negatives at a threshold. Kept free of any model…, Pick the threshold that separates this speaker best. This is the personal part…

### Community 98 - "Residual risks accepted for Phase 0"
Cohesion: 0.22
Nodes (11): Compromised or typosquatted Python dependency, Open question: hardening %LOCALAPPDATA% ACLs at startup, Other local Windows users, Residual risks accepted for Phase 0, T-048 Secrets leak into audit log, crash dump, or telemetry, T-052 Another local Windows user reads the SQLite vault, T-053 Unauthenticated loopback port accepts local tool calls, T-060 DLL search-order hijacking of the packaged build (+3 more)

### Community 99 - "Closed Enumerated Set of Narrow Typed Tools"
Cohesion: 0.21
Nodes (12): Closed Enumerated Set of Narrow Typed Tools, Emergent Capability From Tool Composition (Residual Risk), Hard Ceiling on Prompt Injection Impact, Sandboxed Generic Shell Rejected, ToolSpec Typed Tool Contract, Thread Isolation Is Not a Security Boundary (Gap 2), Ollama Endpoint Squatting (Unmitigated Residual Risk), Local Authenticating Proxy for Ollama Not Adopted (+4 more)

### Community 100 - ".start"
Cohesion: 0.17
Nodes (4): Any, Begin a conversation. A private one writes nothing (FR-046, AT-014)., Grant the two strictly self-inspecting capabilities on first start.…, Change a setting, persist the override and announce it.

### Community 101 - "TaskCheckpoint"
Cohesion: 0.20
Nodes (5): Durable resume point (PRD FR-128)., TaskCheckpoint, Any, Persist a resume point (PRD FR-128)., Record support for a completion claim (PRD FR-132).

### Community 102 - "Project Jarvis (Windows Local AI Desktop Agent)"
Cohesion: 0.24
Nodes (10): Connected Mode (Optional External Providers), Hallucination Discipline (Epistemic Labelling), Honest Task Status, Local First, Not Local Only, Offline Mode, One Action, One Verification, Project Jarvis (Windows Local AI Desktop Agent), Tool-Grounded Success Claims (+2 more)

### Community 103 - "First-Run Onboarding Wizard"
Cohesion: 0.38
Nodes (7): First-Run Onboarding Wizard, Model Resource Scheduler (VRAM Arbitration), Per-Role Model Routing, Ollama Local Model Runtime, qwen3:8b Planner/Conversation Model, qwen3-vl Vision Model Route, Signed Windows Installer and Updates

### Community 104 - "offerable_scopes_for"
Cohesion: 0.18
Nodes (11): offerable_scopes_for(), RiskLevel, The allow-scopes the dialog may offer, per the ADR-0027 table. Low offers…, PRD 9.9 and 11.1: fresh confirmation every time., The engine still supports SESSION; the dialog deliberately does not., test_a_prohibited_capability_is_offered_nothing(), test_allow_for_this_session_is_never_offered(), test_high_risk_is_offered_single_use_only() (+3 more)

### Community 105 - "startup.py"
Cohesion: 0.36
Nodes (10): available(), describe(), is_enabled(), Start at sign-in (PRD FR-002). Uses the per-user…, Only Windows has the Run key this uses., The command Windows would run at sign-in. ``pythonw.exe`` rather than…, Add or remove the sign-in entry. Never requires administrator rights., set_enabled() (+2 more)

### Community 107 - "Jarvis Core"
Cohesion: 0.20
Nodes (10): Audit Log, Event Bus, Jarvis Core, Jarvis Shell, Lock Manager, Permission Engine, ToolInvoker, Default Configuration (+2 more)

### Community 108 - "docs/BACKLOG.md"
Cohesion: 0.36
Nodes (7): Phase 0: Foundation and Safety Architecture, Phase 1: Voice-first Local Assistant, Phase 2: Deterministic Desktop and Browser Automation, Phase 3: Tasks, Macros, and Memory, Phase 4: Vision Fallback and Long-running Workflows, Phase 5: IDE Orchestration, Phase 6: Productisation

### Community 109 - "ADR-0019: Browser Profile Isolation"
Cohesion: 0.24
Nodes (10): ADR-0018: Search Provider, ADR-0019: Browser Profile Isolation, ADR-0023: Adapter Isolation, ADR-0029: Launching Approved Applications, ADR-0030: Secret Store Mechanism, ADR-0031: Browser Automation Attaches Over CDP, Phase 2 — User Acceptance Testing, Phase 2 Plan — Deterministic Desktop and Browser Automation (+2 more)

### Community 110 - "Memory Candidate Review Pipeline"
Cohesion: 0.33
Nodes (6): Bounded Definition of Learning, Memory Candidate Review Pipeline, Memory Record Schema, No Silent Learning, Editable Personality Profile, Private Session Mode

### Community 111 - "Local Wake Phrase Detection"
Cohesion: 0.24
Nodes (10): Audio Worker, English-Only Language Policy, faster-whisper STT Engine, Local Speech-to-Text, Local Text-to-Speech, openWakeWord Model Runtime, Push-to-Talk Hotkey, Local Wake Phrase Detection (+2 more)

### Community 112 - "Jarvis Core (Orchestration)"
Cohesion: 0.29
Nodes (10): Jarvis Core (Orchestration), Jarvis Shell (GUI Process), Kokoro TTS Provider, Authenticated Loopback IPC, Piper TTS Provider, PySide6 Desktop Shell Toolkit, Python 3.11 as V1 Implementation Language, Qwen3-TTS Expressive Provider (+2 more)

### Community 113 - "hotkeys.py"
Cohesion: 0.20
Nodes (8): available(), Hotkey, HotkeyError, ValueError, Global hotkeys (PRD section 11.3, FR-018, ADR-0027). Two hotkeys exist in Phase…, A hotkey string could not be understood., Global hotkeys are a Windows facility in this build., A parsed combination, ready for ``RegisterHotKey``.

### Community 114 - ".stop_speaking"
Cohesion: 0.22
Nodes (4): Runs on the GUI thread, whatever thread pressed the key., F9. Press to start speaking, press again to cut it short. Not hold-to-talk:…, Interrupt speech, and nothing else (ADR-0028). Deliberately not routed through…, F9. Press to start, and again to cut it short. ``RegisterHotKey`` reports the…

### Community 115 - "TB-7 Core/Automation to filesystem scopes"
Cohesion: 0.20
Nodes (10): Phase-gated mitigation roadmap, T-012 Model requests a shell/code-execution tool, T-038 Path traversal escapes the approved root scope, T-039 Symlink or NTFS junction escapes approved scope, T-040 TOCTOU path swap after scope validation, T-043 File-read tool pointed at a credential store or session DB, T-050 Normal .jarvispack export includes cookies or tokens, T-072 Imported skill pack bundles pre-approved high-risk permissions (+2 more)

### Community 116 - "ConfigStore"
Cohesion: 0.25
Nodes (7): ConfigStore, SingleInstanceGuard, default_log_path(), Path, VaultPaths, test_exit_3_a_second_instance_is_refused(), test_the_task_state_machine_is_persistent()

### Community 117 - "Planner Role"
Cohesion: 0.29
Nodes (8): Conversation Agent Role, Memory Curator Role, Product Non-Goals, Planner Role, Prohibited Broad Tools, Prompt-Injection Defence, Structured Model Output Gate, Untrusted Content Boundary

### Community 118 - "denial_options_for"
Cohesion: 0.22
Nodes (9): denial_options_for(), Capability, Don't ask again" options, when the capability has a meaningful target. A…, The button must not overstate what a remembered denial covers., test_a_folder_scoped_capability_offers_a_folder_denial(), test_a_url_capability_says_site_rather_than_application(), test_an_application_scoped_capability_offers_to_remember_the_denial(), test_nothing_is_offered_for_a_capability_with_no_scope_kind() (+1 more)

### Community 120 - "ui/conversation.py"
Cohesion: 0.22
Nodes (5): ConversationWorker, QObject, QWidget, The Conversation screen (PRD section 9.5, FR-045, FR-046, FR-047). Two things…, Runs one turn off the UI thread. The model call is slow and blocking.

### Community 122 - "test_no_elevation.py"
Cohesion: 0.31
Nodes (6): Path, Non-administrator operation (PRD FR-003, NFR-020, ADR-0009). Phase 0 must run…, Any packaging manifest must be asInvoker., _relative(), test_no_manifest_declares_an_elevated_execution_level(), test_no_module_requests_elevation()

### Community 123 - "Over-Permission (OP) category"
Cohesion: 0.31
Nodes (9): Hallucinated Success (HS) category, Over-Permission (OP) category, STRIDE threat classification, T-023 Session grant exercised beyond the prompting request, T-026 Task grant reused after a silent replan, T-027 In-flight tool call runs after mid-task revocation, T-078 Task reported complete without verification, TB-2 Jarvis Shell to Jarvis Core (+1 more)

### Community 124 - "Prompt Injection (PI) category"
Cohesion: 0.36
Nodes (9): The LLM as a confused deputy, Malicious web content author, Prompt Injection (PI) category, T-001 Web page text instructs Jarvis to act, T-010 Self-injection via Jarvis's own prior output, T-015 Web content instructs Jarvis to click Allow, T-018 Web content instructs Jarvis to self-grant permission, TB-8 Automation to browser and remote web content (+1 more)

### Community 125 - "configure_logging"
Cohesion: 0.29
Nodes (6): Logger, Diagnostics: application logging and, later, crash reporting., configure_logging(), Path, Structured application logging. Separate from the audit log. The audit log…, Configure the root logger once. Idempotent.

### Community 126 - "apply_network_policy"
Cohesion: 0.36
Nodes (6): apply_network_policy(), _clear_mark(), _mark_set_here(), Keep the speech model hubs off the network in offline mode (PRD AT-001). The…, Pin the hubs to their local cache when offline. Returns True if offline.…, _was_set_here()

### Community 127 - "LockPort"
Cohesion: 0.29
Nodes (6): LockLease, LockPort, Protocol, Return a lease, or ``None`` if the whole set could not be taken., A held set of resource locks., All-or-nothing acquisition of a declared lock set (PRD FR-124).

### Community 128 - "PeriodicWorker"
Cohesion: 0.29
Nodes (5): PeriodicWorker, Calls a function on an interval until stopped., Sleep, but wake immediately on stop. Returns ``True`` if stopping., test_a_periodic_worker_calls_its_action(), test_one_bad_tick_does_not_kill_a_periodic_worker()

### Community 129 - "ADR-0008: Secret Storage Deferred to Phase 1"
Cohesion: 0.38
Nodes (7): ADR-0008: Secret Storage Deferred to Phase 1, jarvis.core.audit.redaction Defence-in-Depth Backstop, Windows Credential Manager CredWrite/CredRead (Candidate Mechanism), DPAPI CryptProtectData via ctypes (Candidate Mechanism), Encrypted SQLite Table with DPAPI-Wrapped Key (Candidate Mechanism), No Secret Store Implemented in Phase 0, Secrets Excluded From Normal Exports

### Community 130 - "ADR-0013: Installer Technology"
Cohesion: 0.29
Nodes (7): No Elevation Manifest Security Check (asInvoker), Application Never Runs Permanently as Administrator, ADR-0013: Installer Technology, Installer Choice Sequenced Behind the MSIX Decision, NSIS (Candidate Installer), Per-User Install with No UAC Elevation, WiX Toolset MSI (Candidate Installer)

### Community 131 - "Never Claim Unverified Success"
Cohesion: 0.29
Nodes (7): Never Claim Unverified Success, Programmatically Drawn QPainter Tray Icons, ADR-0011: Public Product Name, "Jarvis" as Internal Codename Only, public_product_name Configuration Value, Rename Before Public Release (Leaning Option), Trademark and Identifier Availability Criteria

### Community 132 - "generate_voice_sample"
Cohesion: 0.38
Nodes (6): ndarray, generate_voice_sample(), main(), normalise_audio(), Path, Convert Kokoro output into a one-dimensional NumPy array.

### Community 133 - "Arc Reactor Visual Motif"
Cohesion: 0.52
Nodes (7): Jarvis Application Icon (Arc Reactor Mark), Arc Reactor Visual Motif, Circular Metallic Chassis Ring, Cyan-on-White Emissive Palette, Jarvis Product Brand Identity, Transparent Alpha Square Canvas, Inverted Triangular Glowing Core

### Community 134 - "wake_model_path"
Cohesion: 0.33
Nodes (4): Path, Where the pretrained base model is expected to live (PRD section 17.2).…, wake_model_path(), Report the voice stack exactly as it is (ADR-0010, FR-011).

### Community 135 - "HotkeyBinding"
Cohesion: 0.33
Nodes (4): HotkeyBinding, One requested hotkey and what actually became of it., Declare a hotkey. Parsing happens now; registration happens at start., Hotkeys the user asked for that are not actually working.

### Community 137 - "DenyingApprovalPort Default Implementation"
Cohesion: 0.33
Nodes (6): ADR-0007: Ollama Loopback-Only Trust Boundary, Loopback-Only Base URL Enforcement at the Adapter, Offline Mode Enforced at the Adapter Boundary, DenyingApprovalPort Default Implementation, Inno Setup (Candidate Installer), Uninstall-Time Data Deletion Must Be Opt-In

### Community 138 - "claims_completion"
Cohesion: 0.47
Nodes (6): claims_completion(), Whether a reply asserts that something was done., parametrize, test_completion_claims_are_recognised(), test_done_as_a_whole_statement_is_still_a_completion_claim(), test_ordinary_sentences_are_not_completion_claims()

### Community 139 - ".send_message"
Cohesion: 0.33
Nodes (3): A spoken command becomes an ordinary conversation turn. The window is…, One live conversation at a time, created on first use., Run one turn on a worker thread; the model call blocks.

### Community 140 - "ToolInvoker"
Cohesion: 0.40
Nodes (5): JarvisCore, LockManager, PermissionEngine, TaskScheduler, ToolInvoker

### Community 141 - ".__init__"
Cohesion: 0.40
Nodes (3): AuditLog, datetime, EventBus

### Community 142 - "ToolResult"
Cohesion: 0.40
Nodes (3): The invoker's typed answer. Success requires verification., True only when the tool ran *and* confirmed its effect., ToolResult

### Community 143 - "TB-9 Automation to third-party Windows applications"
Cohesion: 0.40
Nodes (5): Open question: detecting a spoofed window, T-059 Malicious app spoofs a trusted window title, T-080 Jarvis auto-approves an IDE agent's broad request, T-081 IDE agent used as a hidden policy-bypass route, TB-9 Automation to third-party Windows applications

### Community 144 - "TB-4 Core to Automation Worker"
Cohesion: 0.40
Nodes (5): T-028 Two tasks race for the foreground desktop-control lock, T-030 Foreground lock not released after Automation Worker crash, T-034 Consequential action replayed after restart, T-067 Clipboard capture records a password or TOTP code, TB-4 Core to Automation Worker

### Community 145 - "test_whisper.py"
Cohesion: 0.70
Nodes (4): list_audio_devices(), main(), record_audio(), transcribe_audio()

### Community 149 - "test_enabling_then_disabling_leaves_no_entry"
Cohesion: 0.50
Nodes (4): WINDOWS_ONLY, Runs against the real per-user Run key, and cleans up after itself., test_enabling_then_disabling_leaves_no_entry(), test_the_startup_command_points_at_an_interpreter_that_exists()

### Community 150 - "TB-5 Core to Ollama loopback HTTP endpoint"
Cohesion: 0.40
Nodes (6): Open question: authenticating the Ollama endpoint, T-011 Model invents a nonexistent tool name, T-014 Valid tool call with out-of-scope parameters, T-057 Rogue process impersonates the Ollama HTTP API, TB-5 Core to Ollama loopback HTTP endpoint, Tool Misuse (TM) category

### Community 151 - "build_parser"
Cohesion: 0.67
Nodes (3): ArgumentParser, build_parser(), test_the_install_and_uninstall_flags_exist()

### Community 152 - "ADR-0016: Custom "Jarvis" Wake Word"
Cohesion: 0.67
Nodes (3): ADR-0016: Custom "Jarvis" Wake Word, ADR-0027: Approval Dialog and Activation Interaction Model, ADR-0028: Barge-in and Full-Duplex Audio

### Community 155 - "vault_free_bytes"
Cohesion: 0.67
Nodes (3): Path, Free space on the volume holding the vault (PRD NFR-006)., vault_free_bytes()

## Ambiguous Edges - Review These
- `T-030 Foreground lock not released after Automation Worker crash` → `T-034 Consequential action replayed after restart`  [AMBIGUOUS]
  THREAT_MODEL.md · relation: semantically_similar_to
- `Arc Reactor Visual Motif` → `Cyan-on-White Emissive Palette`  [AMBIGUOUS]
  resources/icons/jarvis_icon.png · relation: references
- `"Jarvis" as Internal Codename Only` → `ADR-0012: Shell Technology for the First Public Build`  [AMBIGUOUS]
  docs/decisions/ADR-0011-public-product-name.md · relation: conceptually_related_to

## Knowledge Gaps
- **68 isolated node(s):** `openWakeWord Model Runtime`, `faster-whisper STT Engine`, `Jarvis Shell (PySide6 GUI and tray)`, `TB-3 Core to Audio Worker`, `Other local Windows users` (+63 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **102 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `T-030 Foreground lock not released after Automation Worker crash` and `T-034 Consequential action replayed after restart`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Arc Reactor Visual Motif` and `Cyan-on-White Emissive Palette`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `"Jarvis" as Internal Codename Only` and `ADR-0012: Shell Technology for the First Public Build`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `JarvisCore` connect `JarvisCore` to `EventBus`, `ApplicationCatalogue`, `JarvisApplication`, `AppConfig`, `NetworkMode`, `test_phase0_exit_criteria.py`, `Database`, `ToolCall`, `test_grounding_and_history.py`, `MainWindow`, `ConversationEngine`, `ModelRouter`, `PermissionEngine`, `ApprovalQueue`, `OllamaChatProvider`, `ConversationStore`, `VoiceService`, `model_directory`, `Conversation`, `core.py`, `ToolInvoker`, `main_window.py`, `app.py`, `test_at014_private_session.py`, `.start`, `ConfigStore`, `_PermissionsPanel`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `ModelRouter`, `PermissionEngine`, `types.py`, `.start`, `test_runtime_primitives.py`, `ResourceLockManager`, `EventBus`, `ConversationStore`, `tasks/store.py`, `JarvisCore`, `ToolCall`, `AuditLog`, `test_grounding_and_history.py`, `WorkerSupervisor`, `Conversation`, `core.py`, `ToolInvoker`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **Why does `JarvisApplication` connect `JarvisApplication` to `AudioUnavailable`, `types.py`, `.send_message`, `NetworkMode`, `test_phase0_exit_criteria.py`, `JarvisCore`, `MainWindow`, `VoiceController`, `JarvisTrayIcon`, `tools/ports.py`, `ApprovalPanel`, `Turn`, `test_voice_reply_behaviour.py`, `model_directory`, `core.py`, `test_listening_controls.py`, `test_voice_wiring.py`, `test_cross_thread_marshalling.py`, `test_stop_speaking.py`, `ui/__init__.py`, `GlobalHotkeys`, `app.py`, `.stop_speaking`, `._answer`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `JarvisCore` (e.g. with `VoiceService` and `AppConfig`) actually correct?**
  _`JarvisCore` has 31 INFERRED edges - model-reasoned connections that need verification._