# Graph Report - .  (2026-08-04)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3833 nodes · 7503 edges · 207 communities (172 shown, 35 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 703 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `283be37b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TaskStore
- ToolCall
- types.py
- test_playback.py
- TaskScheduler
- VoicePanel
- JarvisTrayIcon
- ConversationPanel
- ApprovalPanel
- EventBus
- VoicePipeline
- JarvisApplication
- DuplexCoordinator
- tools/ports.py
- ConfigStore
- NetworkMode
- ResourceLockManager
- Database
- AuditLog
- tools/__init__.py
- VoiceService
- availability.py
- tts.py
- AudioChunk
- test_ollama_tool_calling.py
- test_web_search_and_catalogue.py
- test_config.py
- test_phase0_exit_criteria.py
- audio/ports.py
- ModelRouter
- JarvisCore
- test_audio_pipeline.py
- MainWindow
- Worker
- ConversationStore
- registry.py
- permissions/models.py
- ApprovalQueue
- OllamaChatProvider
- VoiceController
- test_wake_install.py
- test_permission_engine.py
- schema.py
- PermissionEngine
- test_grounding_and_history.py
- phase1_tools.py
- Transcript
- test_empty_model_reply.py
- redact
- speakable_text
- test_prohibited_capabilities.py
- test_voice_reply_behaviour.py
- test_conversation_wiring.py
- test_secret_store.py
- AudioUnavailable
- test_interruption.py
- PersonalityStore
- VaultPaths
- test_runtime_primitives.py
- test_offline_speech_models.py
- wake.py
- OpenWakeWordDetector
- launch.py
- main_window.py
- test_reply_speech_policy.py
- test_at003_app_launch.py
- test_voice_wiring.py
- core.py
- Project Jarvis (Windows Local AI Desktop Agent)
- test_hotkeys_and_startup.py
- test_tool_specs_are_valid.py
- test_cross_thread_marshalling.py
- Resource Lock Model
- test_stop_speaking.py
- .start
- Project Jarvis Implementation Backlog
- Phase 0 — Foundation and safety architecture
- Dedicated Jarvis Brave Profile
- grounding.py
- test_application_launch.py
- test_no_shell.py
- TtsProvider
- ui/__init__.py
- capture.py
- model_directory
- GlobalHotkeys
- Architectural Drivers
- Extension Points Table
- main.py
- ADR-0003: A Closed Capability Set — No Generic Execution Primitive
- Over-Permission (OP) category
- app.py
- test_layering.py
- test_capture_host_api.py
- Residual risks accepted for Phase 0
- offerable_scopes_for
- ApplicationCatalogue
- test_at014_private_session.py
- Typed In-Process Event Bus (jarvis.core.events)
- .ask
- ConfigStore
- On-Demand Narrowly Scoped Elevated Helper Process
- SQLite (jarvis.db) Canonical Transactional Store
- Option B: Per-Stream Retention Defaults with Expiry
- Prompt Injection (PI) category
- Five-component process model
- CaptureSession
- build_argv
- JarvisCore (composition root)
- tests/security/test_no_shell.py (AST scan of src/)
- configured_duplex_mode
- Closed Enumerated Set of Narrow Typed Tools
- Capability Risk Classes
- media.py
- Phase 0 Known Limitations
- jarvis.core.events In-Process Publish/Subscribe Bus
- service.py
- personality.py
- startup.py
- register_phase1_tools
- task table
- Phase 2 — Deterministic desktop and browser automation
- Phase 0 security status table
- Root-scoped filesystem tools
- Tool-invocation evaluation order
- ArgumentKind
- .stop_speaking
- Redaction Before Serialisation
- ToolInvoker (six-step pipeline)
- Phase 1 — Voice-first local assistant
- Automation Worker
- qwen3-embedding:0.6b Tentative Default
- test_process_detection_finds_a_process_that_is_really_running
- Phased Delivery Plan (Phase 0-6)
- Local Wake Phrase Detection
- Jarvis Shell (GUI Process)
- FakeSounddevice
- recover_interrupted_work
- denial_options_for
- ._answer
- hotkeys.py
- Path
- test_no_elevation.py
- ADR-0014: Default English Voice
- MSIX Sandboxing vs Desktop Automation Tension
- Voice Pack Redistribution Licensing Gap
- Option B: Self-Signed Developer Keys
- configure_logging
- Audit log requirements (append-only, redacted)
- P0-SEC-03 Permission engine
- Phase 3 — Tasks, macros, and memory
- ADR-0008: Secret Storage Deferred to Phase 1
- ADR-0013: Installer Technology
- Never Claim Unverified Success
- Option A: Local Backup Only, No Network Transport
- generate_voice_sample
- First-Run Onboarding Wizard
- Arc Reactor Visual Motif
- HotkeyBinding
- DenyingApprovalPort Default Implementation
- strip_wake_phrase
- .__init__
- ChatProvider
- .send_message
- ToolResult
- NotifyTool
- .quit
- test_an_interpreter_cannot_be_added_to_the_catalogue
- test_whisper.py
- Retention and Deletion Rules
- _same_microphone
- test_enabling_then_disabling_leaves_no_entry
- AppConfig
- .__init__
- .shutdown
- .recovery
- core/__init__.py
- .set_interactive
- .subscribe
- llm/__init__.py
- test_an_unparseable_hotkey_is_reported_not_raised
- T-019 Mis-transcribed command causes destructive action
- Any
- BaseModel
- Conversation
- ConversationEngine
- UUID4 Hex Identifiers (jarvis.common.new_id)
- DuplexCoordinator
- project-jarvis
- QWidget
- datetime
- AudioChunk
- Protocol
- RuntimeError
- AuditLog
- Path
- Enum
- model_validator
- str
- AppConfig
- NetworkMode
- VaultPaths
- Exception
- AppConfig
- fixture
- parametrize

## God Nodes (most connected - your core abstractions)
1. `JarvisCore` - 87 edges
2. `Database` - 71 edges
3. `JarvisApplication` - 69 edges
4. `EventBus` - 63 edges
5. `AudioChunk` - 62 edges
6. `AuditLog` - 57 edges
7. `ToolCall` - 56 edges
8. `MainWindow` - 47 edges
9. `VoicePanel` - 46 edges
10. `ResourceLockManager` - 45 edges

## Surprising Connections (you probably didn't know these)
- `Concurrency Invariants` --semantically_similar_to--> `SQLite Concurrency Strategy (WAL, per-thread connections)`  [INFERRED] [semantically similar]
  ARCHITECTURE.md → DATA_MODEL.md
- `Export and Import Constraints` --semantically_similar_to--> `Redaction Before Serialisation`  [INFERRED] [semantically similar]
  DATA_MODEL.md → ARCHITECTURE.md
- `Rust Deferred Until After Phase 3` --conceptually_related_to--> `Architectural Drivers`  [INFERRED]
  PROJECT_INPUTS.md → ARCHITECTURE.md
- `DenyingApprovalPort (silence is never consent)` --semantically_similar_to--> `permission_grant table`  [INFERRED] [semantically similar]
  ARCHITECTURE.md → DATA_MODEL.md
- `Automation Safety Defaults` --conceptually_related_to--> `Resource Locks (jarvis.tasks.locks)`  [INFERRED]
  PROJECT_INPUTS.md → ARCHITECTURE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Six-Role Agent Pipeline (Converse, Plan, Execute, Observe, Verify, Curate)** — prd_conversation_agent, prd_planner, prd_executor, prd_observer, prd_verifier, prd_memory_curator [EXTRACTED 1.00]
- **Jarvis Process Model (Shell, Core, Audio, Automation, Scheduler)** — prd_jarvis_shell, prd_jarvis_core, prd_audio_worker, prd_automation_worker, prd_task_scheduler_process, prd_local_ipc [EXTRACTED 1.00]
- **Guardrail and Permission Stack** — prd_capability_risk_classes, prd_approval_design, prd_audit_log, prd_prompt_injection_defence, prd_emergency_stop, prd_prohibited_broad_tools, prd_structured_model_output [EXTRACTED 1.00]
- **Layered prohibited-capability enforcement** — security_prohibited_capabilities, security_prohibited_tool_list, security_tool_registry_denylist, security_prohibited_primitive_scan, threat_model_t_012 [EXTRACTED 1.00]
- **End-to-end tool-call validation pipeline** — security_evaluation_order, security_tool_invoker_pipeline, security_permission_model, security_resource_locks, security_approval_dialog, security_approval_port [EXTRACTED 1.00]
- **Threats live in Phase 0** — threat_model_phase_0_residual_risks, threat_model_t_048, threat_model_t_052, threat_model_t_053, threat_model_t_057, threat_model_t_060, threat_model_t_069 [EXTRACTED 1.00]
- **TTS Provider Stack and GPU Resource Arbitration** — docs_decisions_adr_0015_additional_tts_providers_ttsprovider_interface, docs_decisions_adr_0014_default_english_voice_kokoro_bm_george, docs_decisions_adr_0014_default_english_voice_windows_sapi_fallback, docs_decisions_adr_0015_additional_tts_providers_qwen3_tts_isolated_worker, docs_decisions_adr_0015_additional_tts_providers_model_resource_scheduler, docs_decisions_adr_0017_embedding_model_qwen3_embedding_0_6b [EXTRACTED 1.00]
- **Artefact Trust and Provenance Chain** — docs_decisions_adr_0026_code_signing_and_updates_signature_verification_before_execution, docs_decisions_adr_0026_code_signing_and_updates_ov_manual_updates, docs_decisions_adr_0020_plugin_and_skill_signing_signed_manifest_field, docs_decisions_adr_0020_plugin_and_skill_signing_jarvispack_import, docs_decisions_adr_0022_msix_distribution_msix_secondary_channel, docs_decisions_adr_0014_default_english_voice_redistribution_licensing_gap [INFERRED 0.85]
- **Vault Data Lifecycle and Exposure Control** — docs_decisions_adr_0024_data_retention_defaults_per_stream_defaults, docs_decisions_adr_0024_data_retention_defaults_cascade_on_expiry, docs_decisions_adr_0025_screenshot_retention_task_only_default, docs_decisions_adr_0021_encrypted_sync_and_backup_secret_exclusion_rule, docs_decisions_adr_0021_encrypted_sync_and_backup_portable_identity_export, docs_decisions_adr_0017_embedding_model_rebuildable_derived_index [EXTRACTED 1.00]
- **Arc Reactor Icon Composition (chassis + core + emissive palette)** — resources_icons_jarvis_icon, resources_icons_jarvis_icon_circular_chassis, resources_icons_jarvis_icon_triangular_core, resources_icons_jarvis_icon_cyan_glow_palette [EXTRACTED 1.00]
- **Windows Shell Asset Readiness Constraints** — resources_icons_jarvis_icon, resources_icons_jarvis_icon_transparent_alpha_canvas, resources_icons_jarvis_icon_circular_chassis, resources_icons_jarvis_icon_product_brand_identity [INFERRED 0.75]
- **Six-Step Tool Invocation Pipeline** — architecture_tool_invoker, architecture_toolspec, architecture_permission_engine, architecture_resource_locks, architecture_approvalport, architecture_audit_log, architecture_verification_requirement [EXTRACTED 1.00]
- **Three-Layer Enforcement of No Generic Execution** — architecture_closed_capability_set, architecture_prohibited_tool_denylist, architecture_no_shell_scan, architecture_test_layering, _github_workflows_ci_security_job, changelog_three_layer_shell_enforcement [EXTRACTED 1.00]
- **Startup Crash Recovery Flow** — architecture_jarviscore, architecture_crash_recovery, data_model_runtime_instance, data_model_task_table, data_model_resource_lock_table, architecture_audit_log [EXTRACTED 1.00]
- **Phase 0 auditable choke-point spine** — docs_backlog_p0_cor_02, docs_backlog_p0_cor_03, docs_backlog_p0_cor_04, docs_backlog_p0_sec_03, docs_backlog_p0_sec_01 [EXTRACTED 1.00]
- **Untrusted-content / prompt-injection defence** — docs_backlog_p2_brw_06, docs_backlog_test_prompt_injection, docs_backlog_p5_ide_08, docs_backlog_p0_sec_03 [INFERRED 0.85]
- **Reversibility declaration to exercised rollback chain** — docs_backlog_invariant_reversibility_metadata, docs_backlog_p0_cor_02, docs_backlog_p3_fs_02, docs_backlog_p3_fs_04 [EXTRACTED 1.00]
- **Phase 0 Structural Enforcement Mechanisms (Tests and Schema Guards)** — docs_decisions_adr_0003_closed_capability_set_no_generic_execution_test_no_shell_scan, docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_test_layering, docs_decisions_adr_0006_layered_configuration_override_only_persistence_extra_forbid, docs_decisions_adr_0002_sqlite_single_source_of_truth_schema_version_startup_check, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_no_elevation_manifest_check [INFERRED 0.85]
- **Process-Separation Promotion Path and Its Triggers** — docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_single_process_worker_threads, docs_decisions_adr_0004_single_process_thread_isolation_phases_0_3_process_promotion_triggers, docs_decisions_adr_0001_python_first_rust_deferred_qwen3_tts_worker, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_scoped_helper_process, docs_decisions_adr_0009_scoped_elevation_via_separate_helper_helper_ipc_discipline, docs_decisions_adr_0001_python_first_rust_deferred_typed_ipc [EXTRACTED 1.00]
- **Open Phase 6 Productisation Decisions** — docs_decisions_adr_0011_public_product_name_adr, docs_decisions_adr_0012_shell_technology_for_first_public_build_adr, docs_decisions_adr_0013_installer_technology_adr, docs_decisions_adr_0013_installer_technology_msix_sequencing_dependency, docs_decisions_adr_0011_public_product_name_trademark_screen_criteria [EXTRACTED 1.00]

## Communities (207 total, 35 thin omitted)

### Community 0 - "TaskStore"
Cohesion: 0.06
Nodes (60): from_iso(), json_dumps(), json_loads(), new_id(), Any, datetime, Small shared primitives used across every layer. Kept deliberately tiny:…, A fresh opaque identifier. UUID4 hex, no dashes, stable length. (+52 more)

### Community 1 - "ToolCall"
Cohesion: 0.06
Nodes (65): AuditCategory, RetryPolicy, Any, BaseModel, RiskLevel, Verification, Make "don't ask again" stick, as a scoped DENY grant (ADR-0027). No engine…, Record the user's decision so a broader scope is honoured next time. (+57 more)

### Community 2 - "types.py"
Cohesion: 0.05
Nodes (50): LookupError, In-process typed event bus (ADR-0005). Deliberately not a message broker: no…, Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe., Subscription, Typed event bus and the domain event vocabulary., AppStarted, AppStopping, ConfigChanged (+42 more)

### Community 3 - "test_playback.py"
Cohesion: 0.05
Nodes (57): _as_float_array(), default_output_device(), play(), playback_available(), playback_unavailable_reason(), PlaybackReport, AudioChunk, Audio playback (PRD FR-030, FR-033, ADR-0028). The missing half of the voice… (+49 more)

### Community 4 - "TaskScheduler"
Cohesion: 0.05
Nodes (32): Any, BaseModel, Enum, Protocol, str, Persist a resume point (PRD FR-128)., Record support for a completion claim (PRD FR-132)., Report a milestone. Visible in the Tasks screen (PRD FR-131). (+24 more)

### Community 5 - "VoicePanel"
Cohesion: 0.04
Nodes (34): QWidget, The Voice screen (PRD FR-011, FR-016, FR-017, FR-021, FR-031, FR-032,…, Always show the exact destination path, installed or not., State the phrase literally. Never label it 'Jarvis' (FR-011)., Show what has been measured. Never imply more than that., Listening needs the wake model and a microphone — nothing more. ADR-0016…, Show the transcript, so a misheard word is visibly a mishearing., Say plainly whether the microphone is open (PRD FR-013). (+26 more)

### Community 6 - "JarvisTrayIcon"
Cohesion: 0.05
Nodes (36): ActivationReason, QAction, QMenu, QSystemTrayIcon, JarvisTrayIcon, QObject, System tray icon and menu (PRD sections 9.1 and 9.2). Menu entries whose…, Colour, shape, tooltip and accessible name all change together. (+28 more)

### Community 7 - "ConversationPanel"
Cohesion: 0.06
Nodes (33): SourceLabel, ConversationPanel, ConversationWorker, _escape(), QObject, QWidget, The Conversation screen (PRD section 9.5, FR-045, FR-046, FR-047). Two things…, Enable or disable input, and say exactly why when disabled. The window… (+25 more)

### Community 8 - "ApprovalPanel"
Cohesion: 0.08
Nodes (37): ApprovalController, ApprovalPanel, Decision, GrantScope, QObject, QWidget, Every PRD section 11.2 field, and no field invented to fill a gap., Bottom-right of the available desktop — where the tray lives. (+29 more)

### Community 9 - "EventBus"
Cohesion: 0.07
Nodes (43): E, MonkeyPatch, EventBus, Thread-safe publish/subscribe with subclass matching., Receive ``event_type`` and every subclass of it., Deliver to every matching handler. Returns the number invoked. Handler…, approving_invoker(), audit() (+35 more)

### Community 10 - "VoicePipeline"
Cohesion: 0.07
Nodes (31): Begin waiting for the wake phrase, if enrolment allows it., Stop, and forget everything held. Nothing survives in memory., F9 pressed. Capture a command without a wake phrase (FR-018)., One captured frame. Called from the audio thread., Only ever enabled after enrolment has been measured (ADR-0016)., Capture in, commands out. Owns the listening state machine., VoicePipeline, NullWakeDetector (+23 more)

### Community 11 - "JarvisApplication"
Cohesion: 0.05
Nodes (23): Event, GlobalHotkeys, QApplication, JarvisApplication, QObject, Connect the voice service to the Voice screen and to push-to-talk., A choice made on the Voice screen must survive a restart., Runs on the audio thread, so it only queues work onto the GUI one. (+15 more)

### Community 12 - "DuplexCoordinator"
Cohesion: 0.06
Nodes (27): datetime, BargeInReport, DuplexCoordinator, DuplexMode, PlaybackWindow, Enum, str, Full-duplex audio and barge-in (ADR-0028, PRD FR-015, section 11.3). ADR-0028… (+19 more)

### Community 13 - "tools/ports.py"
Cohesion: 0.07
Nodes (32): ApprovalRequested, ApprovalResolved, A tool is waiting on the user. The tray must make this impossible to miss.…, PendingApproval, datetime, Decision, GrantScope, The approval queue — step 5 of the invoker pipeline, made answerable. ADR-0027… (+24 more)

### Community 14 - "ConfigStore"
Cohesion: 0.10
Nodes (26): _atomic_write(), ConfigError, ConfigStore, deep_merge(), _delete_by_path(), _env_overrides(), _get_by_path(), _parse_env_value() (+18 more)

### Community 15 - "NetworkMode"
Cohesion: 0.06
Nodes (32): Enum, NetworkMode, is_loopback_url(), OllamaHealth, OllamaHealthChecker, Exception, Ollama health check (ADR-0007). Two boundary rules are enforced here rather…, True when the URL's host is a loopback address or resolves only to one. (+24 more)

### Community 16 - "ResourceLockManager"
Cohesion: 0.07
Nodes (37): Release everything this runtime holds. Called during shutdown., Release locks whose owning runtime instance is gone (PRD FR-006). Without this,…, Exclusive, persisted, owner-attributed locks., ResourceLockManager, Task state machine, durable store, locks and scheduler (PRD FR-120 .. FR-133)., A partial acquisition would deadlock two tasks against each other., PRD FR-006: a crash while holding a lock must not wedge the resource., PRD section 7.1 and AT-009: one runs, the other stays queued. (+29 more)

### Community 17 - "Database"
Cohesion: 0.09
Nodes (27): Connection, Cursor, Exception, Row, Database, DatabaseError, Any, Path (+19 more)

### Community 18 - "AuditLog"
Cohesion: 0.09
Nodes (31): Audit logging and secret redaction., AuditLog, Any, datetime, Path, Append-only audit log with two sinks (ARCHITECTURE.md section 6.3). *…, Every record from the JSONL file, oldest first., Search the SQLite index. Falls back to the JSONL file if unavailable. (+23 more)

### Community 19 - "tools/__init__.py"
Cohesion: 0.10
Nodes (35): BaseModel, Enum, Exception, str, The tool contract (PRD section 13.2). A *tool* is the only way the agent…, Per-invocation context handed to a tool. Carries no ambient authority., What a tool returns on success., Raised by a tool to report a declared failure. The code must be declared. (+27 more)

### Community 20 - "VoiceService"
Cohesion: 0.07
Nodes (15): CommandHeard, NoiseCalibration, AudioChunk, No enrolment has been run in this build, so nothing has passed., Whether anything can actually be heard. Speaking depends on it., Open the microphone. Returns False, honestly, if it cannot., Measure the room and apply the threshold (PRD FR-017)., Choose the microphone (PRD FR-016). Reopens an open stream. (+7 more)

### Community 21 - "availability.py"
Cohesion: 0.09
Nodes (29): _capture_status(), ComponentStatus, describe_voice_stack(), module_available(), Path, What of the voice stack is actually usable right now (ADR-0010, NFR-014). Audio…, Report each component's real state, reading configuration when given., True if ``module`` could be imported, without importing it. (+21 more)

### Community 22 - "tts.py"
Cohesion: 0.07
Nodes (22): A selectable voice, with the licence metadata FR-032 requires., SynthesisResult, VoiceDescription, build_tts_provider(), KokoroTtsProvider, NullTtsProvider, prepare_for_speech(), Text to speech (PRD FR-030 to FR-034, ADR-0014, ADR-0015). Kokoro `bm_george`… (+14 more)

### Community 23 - "AudioChunk"
Cohesion: 0.07
Nodes (18): Record how loud Jarvis's own output was. Reported, not compared., Watch raw frames, for measuring the room (PRD FR-017). Observers see frames…, AudioChunk, A block of mono audio. ``samples`` is raw bytes, never a file path., calibrate(), NoiseCalibration, Enum, str (+10 more)

### Community 24 - "test_ollama_tool_calling.py"
Cohesion: 0.10
Nodes (32): ConversationEngine, Runs one turn: prompt, model, tools, grounding, reply., ChatResponse, What a provider returned. ``text`` is for the user. ``tool_calls`` is for the…, _decode(), echo_invoker(), EchoParams, EchoResult (+24 more)

### Community 25 - "test_web_search_and_catalogue.py"
Cohesion: 0.07
Nodes (28): fixture, parametrize, catalogue(), ApplicationCatalogue, Searching, and opening an application that takes an optional argument. Both…, The model sometimes passes a URL anyway. It becomes a search for it., The owner's own default. It was DuckDuckGo; they asked for Google. Pinned by a…, Changing the default must not remove the choice. (+20 more)

### Community 26 - "test_config.py"
Cohesion: 0.07
Nodes (24): PathLike, Configuration layer (L1). Must not import anything above L1., expand_path(), find_defaults_config(), _platform_default_root(), Data-vault path resolution. This is the *only* module permitted to expand…, Locate the shipped ``defaults.yaml``. Order: ``JARVIS_DEFAULTS_CONFIG`` env…, Expand ``%VARS%``, ``$VARS`` and ``~`` then normalise to an absolute path. (+16 more)

### Community 27 - "test_phase0_exit_criteria.py"
Cohesion: 0.06
Nodes (29): Phase 0 exit criteria and hard constraints. One test (or small group) per…, The tool set stays small and low risk. Phase 0 registered exactly one tool.…, PRD FR-048: succeeded requires verification, so it must be declared., PRD section 13.4: free-form text can never be executed., PRD section 4.4: nothing may silently become permanent memory., An honest report of an unreachable runtime is a successful self-check. Settled…, Phase 1 state must be visible from the headless self-check., PRD section 9.1 and NFR-033. (+21 more)

### Community 28 - "audio/ports.py"
Cohesion: 0.07
Nodes (21): Cue, cue_audio(), _faded(), Short audio cues, so Jarvis is legible without looking at the screen. The…, The cues this build makes, and what each one means., Render one cue, or None if numpy is unavailable or the name is unknown. Never…, Taper both ends, or the tone starts and stops with a click., AudioFormat (+13 more)

### Community 29 - "ModelRouter"
Cohesion: 0.08
Nodes (23): Conversation history and private sessions (PRD FR-045, FR-046, AT-014). A…, Turns for a live conversation, from memory; otherwise from storage., StoredMessage, ChatRole, ModelRole, Enum, str, The chat provider boundary (ARCHITECTURE.md section 8, PRD FR-040, section… (+15 more)

### Community 30 - "JarvisCore"
Cohesion: 0.11
Nodes (34): JarvisCore, Everything except the user interface., _new_core(), Full core lifecycle, crash recovery and settings durability., Phase 0 exit criterion., PRD NFR-011: no consequential action is repeated after a restart., SQLite is the single source of truth (ADR-0002)., Kill the process the way a crash does: threads gone, nothing cleaned up.… (+26 more)

### Community 31 - "test_audio_pipeline.py"
Cohesion: 0.08
Nodes (31): Collect a few seconds of room tone, then set the threshold., FakeStt, frame(), Full-duplex audio, barge-in, TTS and STT (ADR-0028, PRD FR-015, 10.3, 10.4).…, Conflating this with emergency stop would make "stop talking" destructive., ADR-0028 keeps push-to-talk as the reliable interruption path., People pause mid-sentence; cutting there truncates the command., Ported from tools/voice-lab, not re-guessed. (+23 more)

### Community 32 - "MainWindow"
Cohesion: 0.10
Nodes (14): QMainWindow, MainWindow, Navigation shell over live core state., Report the voice stack exactly as it is (ADR-0010, FR-011)., Closing the window leaves Jarvis running in the tray (PRD FR-001)., test_the_window_says_plainly_when_nothing_is_waiting(), No placeholder screen may look like it works (ADR-0010, PRD section 1.10)., Phase 1 adds Conversation and Voice. Everything else still names its phase. (+6 more)

### Community 33 - "Worker"
Cohesion: 0.07
Nodes (14): ABC, PeriodicWorker, BaseException, Calls a function on an interval until stopped., Starts and stops workers in a defined order., Stop in reverse order. Returns the names that stopped cleanly., A named background thread with a cooperative stop., Signal and wait. Returns ``True`` when the thread actually stopped. (+6 more)

### Community 34 - "ConversationStore"
Cohesion: 0.07
Nodes (20): Conversation, ConversationStore, AuditLog, Begin a conversation. ``persist=False`` is a private session., Stop recording this conversation, and erase what was recorded. Per-conversation…, Remove a conversation and its turns. Messages cascade., One conversation, persisted or not., Creates conversations and records turns, when recording is permitted. (+12 more)

### Community 35 - "registry.py"
Cohesion: 0.09
Nodes (20): ToolRegistered, Any, model_validator, Protocol, Schema the planner sees. Free-form text can never reach the invoker., What an implementation must provide., Everything a tool declares about itself., Tool (+12 more)

### Community 36 - "permissions/models.py"
Cohesion: 0.11
Nodes (28): _c(), capabilities_by_risk(), capability(), capability_ids(), The capability catalogue — PRD section 11.1 expressed as data. Risk…, Permission model, capability catalogue and evaluation engine., Capability, Decision (+20 more)

### Community 37 - "ApprovalQueue"
Cohesion: 0.13
Nodes (27): ApprovalQueue, Holds requests between the thread that needs an answer and the user. Implements…, make_request(), fixture, RiskLevel, queue(), The approval queue (ADR-0027). The timeout path is the security-critical one…, A UI defect must not be able to widen a high-risk approval. (+19 more)

### Community 38 - "OllamaChatProvider"
Cohesion: 0.10
Nodes (23): _as_int(), OllamaChatProvider, Any, Ollama chat completion (PRD FR-040, section 13.4, ADR-0007). Inherits the two…, Read only the structured field. Never parse prose for an action., Describe one registered tool in the format Ollama expects. Built from the…, The instruction that accompanies every wrapped observation., Chat against a loopback Ollama. Blocking; call from a worker thread. (+15 more)

### Community 39 - "VoiceController"
Cohesion: 0.08
Nodes (11): QObject, Play a short tone. Never blocks, never raises onto the caller., Remember a worker so shutdown can wait for it, without hoarding., Silence Jarvis now. Returns whether there was anything to silence., Start or stop waiting for the wake phrase, on the user's say-so., Transcription blocks for seconds, so never on the GUI thread., Switch microphone. Reopens the stream if one is already open., ADR-0010: name the phase rather than pretending or failing quietly. (+3 more)

### Community 40 - "test_wake_install.py"
Cohesion: 0.13
Nodes (27): make_files(), Path, The wake-model bootstrap (ADR-0016, PRD section 17.2). No test here downloads…, A corrupt download must not be reported as ready (ADR-0010)., The command's exit code reflects usability, not download success., Hey Travis" measured 0.489, so 0.5 left almost no margin., ONNX on Windows; the library's own default is tflite., A wake model alone cannot initialise a detector. (+19 more)

### Community 41 - "test_permission_engine.py"
Cohesion: 0.10
Nodes (28): PermissionRequest, A question put to the permission engine. Contains no side effects., parametrize, Permission evaluation (PRD sections 9.9 and 11.1, ARCHITECTURE.md 6.4)., A user who denied something should not be asked again in the same scope., PRD 11.1: fresh confirmation every time., PRD 9.9: high-risk permissions must not offer 'always allow'., test_a_deny_grant_outranks_an_allow_grant() (+20 more)

### Community 42 - "schema.py"
Cohesion: 0.12
Nodes (28): model_validator, AudioConfig, _Base, ConversationLanguageConfig, DefaultPermissionPolicy, LanguageConfig, LlmConfig, LoggingConfig (+20 more)

### Community 43 - "PermissionEngine"
Cohesion: 0.13
Nodes (16): PermissionEvaluation, PermissionGrant, PermissionRequest, _canonical_folder(), DefaultPolicy, _folder_contains(), PermissionEngine, Decision (+8 more)

### Community 44 - "test_grounding_and_history.py"
Cohesion: 0.10
Nodes (29): claims_completion(), Whether a reply asserts that something was done., Label a reply and stop it claiming an unverified success. ``tool_results`` are…, review_response(), parametrize, Source labelling, tool-grounded success, history and personality. PRD FR-045,…, AT-018: never report completed when it could not be verified., A state-changing tool that could not confirm has not established a fact. (+21 more)

### Community 45 - "phase1_tools.py"
Cohesion: 0.13
Nodes (23): MediaControlInput, MediaControlOutput, MediaControlTool, NotifyInput, NotifyOutput, OpenApplicationInput, OpenApplicationOutput, OpenUrlInput (+15 more)

### Community 46 - "Transcript"
Cohesion: 0.10
Nodes (17): RingBuffer, ActivationRoute, CommandHeard, _join(), ListeningState, Enum, str, The voice loop (PRD sections 10.2 to 10.4, ADR-0027, ADR-0028). One place where… (+9 more)

### Community 47 - "test_empty_model_reply.py"
Cohesion: 0.12
Nodes (23): ChatResponse, _describe_silence(), What to say when the model returned no words at all. It happens: a small model…, _conversation(), _engine(), NoopInvoker, parametrize, A model that returns nothing must not produce a blank, confident answer. From a… (+15 more)

### Community 48 - "redact"
Cohesion: 0.11
Nodes (26): classify_content(), is_content_key(), is_secret_key(), Any, Secret redaction for the audit log (PRD section 11.5, FR-259). Redaction…, Return a copy of ``value`` safe to persist in the audit log. Mappings,…, Describe a value without reproducing it. Used where the *shape* of user content…, Redact secret-looking substrings, then bound the length. (+18 more)

### Community 49 - "speakable_text"
Cohesion: 0.11
Nodes (27): Match, A URL read aloud in full is unbearable; the host is the useful part., Strip what a phonemiser would recite rather than say (PRD FR-030). Presentation…, speakable_text(), _spoken_host(), parametrize, What Jarvis says aloud is not the same string as what it writes down. From a…, Stripping runs first, so emphasis cannot hide a key from the patterns. (+19 more)

### Community 50 - "test_prohibited_capabilities.py"
Cohesion: 0.11
Nodes (25): assert_tool_id_permitted(), check_tool_id(), The prohibited-capability guard (ADR-0003). Defence in depth, layer 2 of 3: 1.…, Return the reason a tool id is prohibited, or ``None`` if it is allowed., ``True`` if the tool id may be registered., why_prohibited(), parametrize, The prohibited-capability guard (ADR-0003, PRD sections 11.1 and 13.3). (+17 more)

### Community 51 - "test_voice_reply_behaviour.py"
Cohesion: 0.11
Nodes (18): The conversation engine (PRD FR-040, FR-042, FR-047, FR-048, section 13.4).…, One user request and everything that came of it., Turn, FakeEngine, _pump(), How Jarvis behaves when it was spoken to, and who it thinks you are. From a…, Typing means you are looking at the screen. Do not talk over it., Otherwise a voice failure is completely silent and invisible. (+10 more)

### Community 52 - "test_conversation_wiring.py"
Cohesion: 0.12
Nodes (23): application(), ExplodingEngine, FakeEngine, _pump(), fixture, The wiring between the Conversation screen and the engine. The panel tests…, A silent failure is the worst outcome; it must always say something., Each send created a QThread whose quit signal could never arrive. (+15 more)

### Community 53 - "test_secret_store.py"
Cohesion: 0.14
Nodes (26): SecretStore, fixture, skipif, WINDOWS_ONLY, The secret store (ADR-0030, PRD 18.3, NFR-022, FR-169, AT-016). The assertions…, Never partial, never best-effort plaintext., Lifting a value under a different name must not decrypt it., Degrading to weaker protection would be worse than refusing (ADR-0010). (+18 more)

### Community 54 - "AudioUnavailable"
Cohesion: 0.11
Nodes (16): AudioUnavailable, An audio component cannot run, and says which and why., TranscriptSegment, build_stt_provider(), diagnostic_audio_path(), FasterWhisperSttProvider, needs_confirmation(), NullSttProvider (+8 more)

### Community 55 - "test_interruption.py"
Cohesion: 0.10
Nodes (21): _detection(), _frame(), AudioChunk, Interrupting Jarvis mid-sentence — why it never worked, and what fixed it.…, A loud synthesised waveform must not raise the bar for the user., A shout during one reply must not deafen Jarvis for the next., Playback has only just begun; there is nothing to compare against., Full duplex plus a closed microphone is not an interruptible Jarvis. (+13 more)

### Community 56 - "PersonalityStore"
Cohesion: 0.13
Nodes (15): PersonalityProfile, PersonalityProposal, PersonalityStore, AuditLog, Change the profile. Only the user reaches this (PRD section 4.4)., Record a suggested adjustment. Changes nothing by itself., Apply or reject a proposal. This is the only path from proposal to change., Turn the profile into instructions. Style only, never authority. (+7 more)

### Community 57 - "VaultPaths"
Cohesion: 0.14
Nodes (5): Path, Instance-scoped files such as the single-instance lock., Create the vault layout. Idempotent., Every path the application is allowed to write to, derived from one root., VaultPaths

### Community 58 - "test_runtime_primitives.py"
Cohesion: 0.07
Nodes (24): _process_is_alive(), BaseException, Path, Remove a lock file whose owning process is gone., Is a process with this id currently running? ``os.kill(pid, 0)`` is the POSIX…, Acquire once at startup; release at shutdown. ``acquired`` is the only thing…, SingleInstanceGuard, _CountingWorker (+16 more)

### Community 59 - "test_offline_speech_models.py"
Cohesion: 0.14
Nodes (21): apply_network_policy(), _clear_mark(), hub_is_offline(), _mark_set_here(), Keep the speech model hubs off the network in offline mode (PRD AT-001). The…, Pin the hubs to their local cache when offline. Returns True if offline.…, _was_set_here(), clean_environment() (+13 more)

### Community 60 - "wake.py"
Cohesion: 0.10
Nodes (15): choose_threshold(), EnrolmentMeasurement, EnrolmentResult, EnrolmentSample, measure_enrolment(), phrase_disclosure(), Wake-word detection and per-user enrolment (ADR-0016, PRD FR-010, FR-011).…, One recording of the user saying the phrase. Personal data (criterion 3). (+7 more)

### Community 61 - "OpenWakeWordDetector"
Cohesion: 0.13
Nodes (10): build_wake_detector(), OpenWakeWordDetector, AudioChunk, Path, openWakeWord over a pretrained base model, with a personal threshold., Applied after enrolment measurement chooses one., Highest score this frame produced across the loaded models., Yield an event whenever a frame crosses the threshold. (+2 more)

### Community 62 - "launch.py"
Cohesion: 0.20
Nodes (15): _basename(), CatalogueError, launch(), launch_argv(), LaunchOutcome, process_running(), The one authorised process-creation call site (ADR-0029). Everything about this…, What actually happened. ``verified`` is never assumed (constraint 9). (+7 more)

### Community 63 - "main_window.py"
Cohesion: 0.19
Nodes (10): NavArea, _NotImplementedPanel, _PermissionsPanel, QWidget, Main window: the fifteen navigation areas of PRD section 9.3. Six areas are…, A heading, a refresh button and a read-only text area., Active grants, and any approval currently waiting for an answer. The panel…, Says exactly what is missing and when it arrives. Never a fake screen. (+2 more)

### Community 64 - "test_reply_speech_policy.py"
Cohesion: 0.16
Nodes (20): _decide(), parametrize, When Jarvis should open its mouth, and when a beep is the right answer.…, Otherwise Jarvis waits silently for an answer nobody knows it wants., A bad config value must not silently make Jarvis mute., what's the volume?" runs device.volume and still deserves an answer., _Result, test_a_command_that_worked_gets_a_cue_not_a_sentence() (+12 more)

### Community 65 - "test_at003_app_launch.py"
Cohesion: 0.17
Nodes (20): OpenApplicationTool, Launch a catalogued application and verify it started (FR-063, FR-064)., catalogue(), launching_invoker(), fixture, parametrize, AT-003 — "Jarvis, open Sea of Thieves" launches it and verifies it. > When the…, ADR-0029 constraint 8: no direct path from a plan to Popen. (+12 more)

### Community 66 - "test_voice_wiring.py"
Cohesion: 0.10
Nodes (19): application(), _pump(), fixture, The Voice screen's controls must be connected, or honestly disabled. Every…, Recording without a visible indicator is a prohibited capability., Without one, capture could start with nothing on screen., The pipeline transcribed commands that had no listener at all., ``application.voice`` stayed None, so push-to-talk always refused. (+11 more)

### Community 67 - "core.py"
Cohesion: 0.11
Nodes (14): OllamaHealth, CoreStatus, default_log_path(), EmergencyStopReport, Path, ``JarvisCore`` — the composition root (ARCHITECTURE.md section 6.9). Owns…, Stop all automation without stopping the application., Check the local model runtime. Runs on a worker thread. (+6 more)

### Community 68 - "Project Jarvis (Windows Local AI Desktop Agent)"
Cohesion: 0.13
Nodes (20): Application Catalogue and Aliases, Connected Mode (Optional External Providers), Deterministic Before Visual (Automation Hierarchy), Local Document Understanding, Hallucination Discipline (Epistemic Labelling), Honest Task Status, Bounded Definition of Learning, Local First, Not Local Only (+12 more)

### Community 69 - "test_hotkeys_and_startup.py"
Cohesion: 0.13
Nodes (17): parse_hotkey(), Parse ``"Ctrl+Alt+Pause"`` or ``"F9"``. Raises :class:`HotkeyError`., parametrize, skipif, Global hotkeys and start-at-sign-in (PRD section 11.3, FR-018, FR-002). Parsing…, PRD section 11.3 and config/defaults.yaml agree on this combination., FR-018 and ADR-0027 specify bare F9, with no modifier., An emergency stop that fires forty times is not better than one. (+9 more)

### Community 70 - "test_tool_specs_are_valid.py"
Cohesion: 0.14
Nodes (19): Every registered tool's declared contract must actually be usable.…, A capability the catalogue has never heard of can never be granted., Every spec the real core registers, plus the shell-only ones., A lock name the manager rejects makes the tool permanently unusable., Named explicitly: this is the one that was wrong., The invoker validates locks before doing anything. Prove it passes., CLAUDE.md: every external interaction declares a timeout., FR-048: `succeeded` requires verification, so it must be described. (+11 more)

### Community 71 - "test_cross_thread_marshalling.py"
Cohesion: 0.17
Nodes (18): application(), _FakeReport, _from_a_plain_thread(), _pump(), fixture, Work handed to the GUI thread from a non-Qt thread must actually arrive.…, The tool reported success for a notification that never appeared., Any new QTimer.singleShot in the shell must be on the GUI thread. Checked by… (+10 more)

### Community 72 - "Resource Lock Model"
Cohesion: 0.12
Nodes (19): Conversation Agent Role, Emergency Stop, jarvis.db SQLite Single Source of Truth, .jarvispack Portable Identity Package, Memory Candidate Review Pipeline, Memory Curator Role, Memory Record Schema, Editable Personality Profile (+11 more)

### Community 73 - "test_stop_speaking.py"
Cohesion: 0.13
Nodes (15): application(), fixture, Making Jarvis shut up — the route that does not depend on tuning. Reported from…, ADR-0028: barge-in is not emergency stop, and conflating them is exactly how…, The tray entry exists whether or not Kokoro is installed., Put the pipeline into the state it is in while Kokoro plays., Silencing speech must not have replaced what it already did., _Report (+7 more)

### Community 74 - ".start"
Cohesion: 0.12
Nodes (9): ChatProvider, ConversationStore, PersonalityStore, Any, Conversation, Begin a conversation. A private one writes nothing (FR-046, AT-014)., Grant the two strictly self-inspecting capabilities on first start.…, Change a setting, persist the override and announce it. (+1 more)

### Community 75 - "Project Jarvis Implementation Backlog"
Cohesion: 0.12
Nodes (18): ARCHITECTURE.md, Subsystem area codes (CFG, COR, SEC, TSK, AUD, LLM, ...), Cross-phase invariants, DATA_MODEL.md, S/M/L/XL effort sizing (not time), Project Jarvis Implementation Backlog, Invariant: phase exit criteria must be demonstrated, Invariant: no generic execution primitive (+10 more)

### Community 76 - "Phase 0 — Foundation and safety architecture"
Cohesion: 0.15
Nodes (23): EventBridge, Invariant: state-changing tools declare reversibility metadata, JarvisCore, LockManager, P0-CFG-01 Layered typed configuration, P0-CFG-03 SQLite storage and versioned forward migrations, P0-COR-01 Typed event bus, P0-COR-02 Tool contract: ToolSpec with reversibility metadata (+15 more)

### Community 77 - "Dedicated Jarvis Brave Profile"
Cohesion: 0.16
Nodes (18): ADR-0018: Search Provider, Option C: Ask a Configured AI Website (FR-055), Untrusted Web Content Wrapping (FR-054), Visible Brave Search Mode (FR-052), ADR-0019: Browser Profile Isolation, CAPTCHA Pause-and-Ask Requirement (FR-058), Dedicated Jarvis Brave Profile, Option C: Playwright Bundled Chromium Persistent Context (+10 more)

### Community 78 - "grounding.py"
Cohesion: 0.12
Nodes (14): GroundedClaim, GroundingReview, _hedge(), Enum, str, Where an answer came from, and what counts as done (PRD FR-047, FR-048). Two…, The verification value of a succeeded result; empty if it did not succeed., Replace an unverified success claim with what is actually known. (+6 more)

### Community 79 - "test_application_launch.py"
Cohesion: 0.09
Nodes (21): default_catalogue(), The Phase 1 seed: exactly the applications PRD section 21 names. Paths are the…, The constrained launcher (ADR-0029). Every test here maps to one of the nine…, A document would let the file-association table choose what runs., PRD section 21: Brave, YouTube, YouTube Music, Xbox, Sea of Thieves., Otherwise a launch could only ever be reported as unverified., A composed path with '..' in it resolved somewhere nonsensical., FR-048 and AT-018: launched is not the same as running. (+13 more)

### Community 80 - "test_no_shell.py"
Cohesion: 0.20
Nodes (17): _findings(), parametrize, Path, The load-bearing security test (ADR-0003). Phase 0 exit criterion: *no generic…, No shipped module may start a process or evaluate generated code., ADR-0029 authorises one call site. A second is a new ADR, not a row here. This…, The allow-list entry must describe reality, not a module that moved., A guard on the guard: prove the detector is not vacuously passing. (+9 more)

### Community 81 - "TtsProvider"
Cohesion: 0.12
Nodes (7): Protocol, Streams frames in, yields a wake event when the phrase is heard., Audio in, transcript out. Local by default (PRD FR-020)., Text in, audio out. Local by default (PRD FR-030)., SttProvider, TtsProvider, WakeDetector

### Community 82 - "ui/__init__.py"
Cohesion: 0.16
Nodes (12): QColor, QIcon, Enum, str, Tray state icons, drawn programmatically. Two reasons not to ship image files:…, PRD section 9.1 tray states., A non-colour distinguishing mark (PRD NFR-033)., Render the icon for a state. Colour *and* shape differ per state. (+4 more)

### Community 83 - "capture.py"
Cohesion: 0.18
Nodes (15): capture_available(), default_input_device(), frames_from_bytes(), host_api_names(), list_devices(), Microphone capture and playback (PRD FR-016, FR-013, ADR-0028). ``sounddevice``…, The best input to open, preferring WASAPI over the system default. Windows…, Cut a recording into frames. Used to replay fixtures through the pipeline. (+7 more)

### Community 84 - "model_directory"
Cohesion: 0.20
Nodes (19): install_wake_model(), installed_files(), InstallReport, is_installed(), missing_files(), model_directory(), Path, One-time wake-word model installation (ADR-0016, PRD section 17.2). **No wake-… (+11 more)

### Community 85 - "GlobalHotkeys"
Cohesion: 0.14
Nodes (8): GlobalHotkeys, Registers hotkeys on a dedicated thread and dispatches their actions. Off…, Run the registration and message loop on its own thread., Invoke a binding's action directly. The test and menu route., The tray and the tests need a route that does not need a real keypress., test_a_binding_can_be_triggered_directly(), test_a_disabled_manager_registers_nothing_and_says_so(), test_starting_a_disabled_manager_is_a_no_op()

### Community 86 - "Architectural Drivers"
Cohesion: 0.19
Nodes (13): Architectural Drivers, LLM Boundary (jarvis.llm), Loopback-Only Ollama Endpoint, Model Output Is Untrusted Input, Planner Cannot Skip the Invoker, Untrusted Content Enters as Delimited Observations, Release 0.1.0.dev0 - Phase 0 Foundation and Safety Architecture, system.health (the one registered Phase 0 tool) (+5 more)

### Community 87 - "Extension Points Table"
Cohesion: 0.18
Nodes (12): Extension Points Table, Separate Model Roles (planner, vision, embeddings, STT, TTS), model_runtime (sequential load strategy), models.* role-to-profile mapping, audio.speech_to_text settings, audio.wake_word settings, espeak-ng Pronunciation Backend, faster-whisper Speech Recognition (+4 more)

### Community 88 - "main.py"
Cohesion: 0.20
Nodes (14): ArgumentParser, Delete the whole model directory. The documented removal step., uninstall_wake_model(), Where the pretrained base model is expected to live (PRD section 17.2).…, wake_model_path(), build_parser(), _install_wake_model(), main() (+6 more)

### Community 89 - "ADR-0003: A Closed Capability Set — No Generic Execution Primitive"
Cohesion: 0.15
Nodes (16): One SQLite Connection Per Thread, ADR-0003: A Closed Capability Set — No Generic Execution Primitive, No Generic Execution Primitive, os.startfile Named Future Allow-Listed Exception, tests/security/test_no_shell.py Source Tree Scan, Tool Registry Identity and Pattern Denylist, ADR-0004: Single Process, Thread Isolation for Phases 0–3, Layering Rule: Core Packages Must Not Import PySide6 (+8 more)

### Community 90 - "Over-Permission (OP) category"
Cohesion: 0.18
Nodes (15): Approval dialog required fields, Capability risk classification (low/medium/high/prohibited), Permission decision types, Permission model, Prohibited capability class, Over-Permission (OP) category, Open question: detecting a spoofed window, T-023 Session grant exercised beyond the prompting request (+7 more)

### Community 91 - "app.py"
Cohesion: 0.21
Nodes (13): _asks_something(), Enum, str, When a spoken request deserves a spoken answer (PRD FR-030, FR-048). Answering…, The user-facing setting, ``audio.speak_replies``., What the shell should do with a finished reply., Decide how a finished turn should sound. ``spoken_request`` is the whole reason…, ReplyVoice (+5 more)

### Community 92 - "test_layering.py"
Cohesion: 0.26
Nodes (14): _imported_modules(), _module_name(), _package_of(), Path, Layering invariants (ARCHITECTURE.md section 5, ADR-0004). The rule that makes…, A fresh interpreter can import the whole engine with no Qt module loaded., Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.…, Spelled out separately because it is the invariant people break first. (+6 more)

### Community 93 - "test_capture_host_api.py"
Cohesion: 0.13
Nodes (13): parametrize, Opening the microphone must match the device's host API (PRD FR-016). Windows…, ADR-0028 defence 2 — echo cancellation is why WASAPI is preferred., FR-013 in reverse: the indicator must not survive a failed start., Four identically-named entries are not a choice a user can make., It opened on none of them: the settings never matched the device., test_a_device_that_cannot_open_at_all_says_so(), test_a_failed_open_leaves_no_recording_indicator_lit() (+5 more)

### Community 94 - "Residual risks accepted for Phase 0"
Cohesion: 0.16
Nodes (14): Dependency and licence scanning CI gate, Screen capture scoping and screenshot retention, Telemetry off by default with content exclusions, Compromised or typosquatted Python dependency, Open question: hardening %LOCALAPPDATA% ACLs at startup, Other local Windows users, Residual risks accepted for Phase 0, T-034 Consequential action replayed after restart (+6 more)

### Community 95 - "offerable_scopes_for"
Cohesion: 0.14
Nodes (13): offerable_scopes_for(), Decision, GrantScope, RiskLevel, The allow-scopes the dialog may offer, per the ADR-0027 table. Low offers…, PRD 9.9 and 11.1: fresh confirmation every time., The engine still supports SESSION; the dialog deliberately does not., test_a_prohibited_capability_is_offered_nothing() (+5 more)

### Community 96 - "ApplicationCatalogue"
Cohesion: 0.22
Nodes (6): ApplicationCatalogue, ApplicationEntry, One application the user has approved Jarvis to open. Created by the user,…, The user's approved applications. Seeded, editable, never model-written., Find an entry by id, display name or alias. Never by path., test_resolving_by_name_never_resolves_a_path()

### Community 97 - "test_at014_private_session.py"
Cohesion: 0.18
Nodes (13): parametrize, AT-014 — a private session produces no permanent record after it ends. Asserted…, Everything the vault has written, as raw bytes., A control: prove the byte search would have found it if written., Privacy is not the same as invisibility: the event is auditable., test_a_normal_session_is_recorded_so_the_test_above_means_something(), test_a_private_conversation_is_marked_private_to_the_user(), test_a_private_session_leaves_no_record_anywhere() (+5 more)

### Community 98 - "Typed In-Process Event Bus (jarvis.core.events)"
Cohesion: 0.18
Nodes (11): CI dependency and licence review job, Emergency Stop, Typed In-Process Event Bus (jarvis.core.events), EventBridge (domain events to queued Qt signals), Honest Degraded UI (disabled, not hidden, not fake), Qt Main Thread Must Not Block, Jarvis Shell (jarvis.ui tray and main window), ui settings (tray start, show_unavailable_features, emergency hotkey) (+3 more)

### Community 99 - ".ask"
Cohesion: 0.22
Nodes (8): ChatMessage, _describe_result(), Any, Conversation, Send one proposal through the invoker. Never around it., Describe only registered tools. The model cannot learn of others., Render a tool result for the model, without inflating it., ToolCallProposal

### Community 100 - "ConfigStore"
Cohesion: 0.33
Nodes (5): ApprovalPort, ConfigStore, SingleInstanceGuard, test_exit_3_a_second_instance_is_refused(), test_the_task_state_machine_is_persistent()

### Community 101 - "On-Demand Narrowly Scoped Elevated Helper Process"
Cohesion: 0.22
Nodes (13): ADR-0001: Python-First Implementation with Rust Deferred, Python 3.11 + PySide6 Implementation Stack, Qwen3-TTS Isolated Python 3.12 Worker, Rust/Tauri Native Shell Deferred Past Phase 3, Authenticated Typed IPC for Future Shell, Process-Separation Promotion Triggers, Helper IPC Discipline (Named Pipe or Loopback, Rotating Token), No Interaction with the Windows Secure Desktop or UAC Prompt (+5 more)

### Community 102 - "SQLite (jarvis.db) Canonical Transactional Store"
Cohesion: 0.23
Nodes (13): ADR-0002: SQLite as the Single Source of Truth, Large Binary Artefacts Stored on Disk, Referenced by Path, Derived Rebuildable Stores Hold No Unique Information, SQLite (jarvis.db) Canonical Transactional Store, WAL Mode Concurrent Readers, ADR-0005: An In-Process Typed Event Bus, Bus Is Notification, Not System of Record, ADR-0006: Layered Configuration with Override-Only Persistence (+5 more)

### Community 103 - "Option B: Per-Stream Retention Defaults with Expiry"
Cohesion: 0.19
Nodes (13): No Shared API Keys Constraint (§18.3), Option B: Optional User-Supplied Search API Key, Portable Identity Export (FR-168), Secret Exclusion from Normal Exports (FR-169/FR-170), Audit Log as a Safety Record, Clipboard History Retention (FR-253), Option C: One Global Retention Period, Option A: Keep Everything Until User Deletes (+5 more)

### Community 104 - "Prompt Injection (PI) category"
Cohesion: 0.23
Nodes (13): Closed authority set for tool authorisation, Security Policy and Control Specification, Untrusted-data rule, The LLM as a confused deputy, Malicious web content author, Prompt Injection (PI) category, STRIDE threat classification, T-001 Web page text instructs Jarvis to act (+5 more)

### Community 105 - "Five-component process model"
Cohesion: 0.17
Nodes (13): Emergency stop surface, Local IPC requirements (loopback, per-install token), Non-admin by default, Five-component process model, Resource locks (jarvis.tasks.locks), Scoped elevation helper process, Secure desktop and UAC prompts off-limits, TTS worker isolation (Qwen3-TTS, separate env) (+5 more)

### Community 106 - "CaptureSession"
Cohesion: 0.23
Nodes (3): CaptureSession, An open microphone. Frames arrive on the audio thread. Use as a context manager…, The settings to try, best first, for whichever device was chosen. A WASAPI…

### Community 107 - "build_argv"
Cohesion: 0.22
Nodes (13): build_argv(), Construct the argument vector. Pure, so it is directly testable., executable_entry(), No quoting to get wrong, because nothing parses the vector., Open Brave" is a legitimate request; it just opens the browser., The model proposes which entry; it can never propose which binary., test_a_browser_opens_with_no_url_at_all(), test_a_model_supplied_path_cannot_become_the_executable() (+5 more)

### Community 108 - "JarvisCore (composition root)"
Cohesion: 0.17
Nodes (17): CI headless self-check step (jarvis.main --check), Layered Configuration System (jarvis.config), extra=forbid Everywhere, JarvisCore (composition root), Override-Only Persistence, Only L5 May Import PySide6, Single-Instance Guard, VaultPaths (centralised path resolution) (+9 more)

### Community 109 - "tests/security/test_no_shell.py (AST scan of src/)"
Cohesion: 0.18
Nodes (16): QT_QPA_PLATFORM=offscreen in CI, CI security-invariants job, CI test job (Windows + Ubuntu, Python 3.11/3.12), Capability Catalogue (risk classification as data), Architectural Change Control, Closed Capability Set (no generic execution primitive), Six-Layer Dependency Model (L0-L5), tests/security/test_no_shell.py (AST scan of src/) (+8 more)

### Community 110 - "configured_duplex_mode"
Cohesion: 0.17
Nodes (10): AuditLog, DuplexMode, Path, configured_duplex_mode(), Re-pin the model hubs after a network-mode change (AT-001)., Read ``audio.duplex_mode``, degrading rather than over-claiming. Anything…, Failing towards "you cannot interrupt me" is the honest direction., test_an_unreadable_setting_degrades_rather_than_over_claiming() (+2 more)

### Community 111 - "Closed Enumerated Set of Narrow Typed Tools"
Cohesion: 0.21
Nodes (12): Closed Enumerated Set of Narrow Typed Tools, Emergent Capability From Tool Composition (Residual Risk), Hard Ceiling on Prompt Injection Impact, Sandboxed Generic Shell Rejected, ToolSpec Typed Tool Contract, Thread Isolation Is Not a Security Boundary (Gap 2), Ollama Endpoint Squatting (Unmitigated Residual Risk), Local Authenticating Proxy for Ollama Not Adopted (+4 more)

### Community 112 - "Capability Risk Classes"
Cohesion: 0.29
Nodes (12): Approval Dialog Design, Consequential-Action Audit Log, Capability Risk Classes, Executor Role, Jarvis Core (Orchestration), Password and Credential Field Protection, Planner Role, Prompt-Injection Defence (+4 more)

### Community 113 - "media.py"
Cohesion: 0.27
Nodes (11): _INPUT, _INPUTUNION, _KEYBDINPUT, media_available(), MediaAction, Enum, str, Media and volume control (PRD FR-094, catalogue `media.playback_control`,… (+3 more)

### Community 114 - "Phase 0 Known Limitations"
Cohesion: 0.29
Nodes (7): In-Process Isolation Is Not a Security Boundary, Deferred Process Separation (TTS worker, elevation helper), Single-Process Multi-Thread Model, Phase 0 Known Limitations, audio.text_to_speech profiles, Qwen3-TTS Expressive Provider (deferred), Windows SAPI Fallback Voice

### Community 115 - "jarvis.core.events In-Process Publish/Subscribe Bus"
Cohesion: 0.20
Nodes (11): Versioned Forward-Only Migrations, Full ORM (SQLAlchemy) Rejected for Phase 0, Schema-Version Startup Check (Newer DB is Hard Failure), jarvis.core.events In-Process Publish/Subscribe Bus, Frozen Pydantic Event Models with Subclass Matching, Per-Handler Exception Isolation, ConfigChanged Runtime Event, pydantic extra="forbid" Loud Typo Failure (+3 more)

### Community 116 - "service.py"
Cohesion: 0.18
Nodes (6): The voice service: one object that owns the whole audio stack (L3). Built even…, What can interrupt Jarvis right now, given the microphone's state., Synthesise **and play**, then report what actually came out. Synthesis alone…, What was synthesised, and what was actually played (PRD FR-048). Carries the…, SpokenResult, VoiceStatus

### Community 117 - "personality.py"
Cohesion: 0.40
Nodes (9): Formality, Humour, ProposalStatus, Enum, str, Personality profile and humour proposals (PRD FR-043, FR-044, section 4.4).…, Verbosity, FakeResult (+1 more)

### Community 118 - "startup.py"
Cohesion: 0.36
Nodes (10): available(), describe(), is_enabled(), Start at sign-in (PRD FR-002). Uses the per-user…, Only Windows has the Run key this uses., The command Windows would run at sign-in. ``pythonw.exe`` rather than…, Add or remove the sign-in entry. Never requires administrator rights., set_enabled() (+2 more)

### Community 119 - "register_phase1_tools"
Cohesion: 0.22
Nodes (7): OpenUrlTool, ApplicationCatalogue, Open a URL in the approved browser. Scheme-restricted (ADR-0029)., Search the web for a phrase, in the approved browser. Exists because asking the…, Register the six approved tools. Returns what was registered. ``speak`` and…, register_phase1_tools(), WebSearchTool

### Community 120 - "task table"
Cohesion: 0.24
Nodes (12): Crash Recovery, Offline Mode Enforced at the Adapter Boundary, Ten-State Task Machine (jarvis.tasks.states), Task Store (jarvis.tasks.store), ToolResult (typed outcomes), Success Requires Verification, network.mode (offline / local_assistant / connected), task_checkpoint table (+4 more)

### Community 121 - "Phase 2 — Deterministic desktop and browser automation"
Cohesion: 0.20
Nodes (14): P1-APP-01 Application launcher with launch verification, P2-BRW-01 Dedicated persistent Jarvis Brave profile, P2-BRW-02 Playwright visible-browser, DOM-first execution, P2-BRW-08 YouTube search and indexed result selection, P2-FS-01 Windows Known Folder resolution, P2-FS-06 Filesystem scoping and path validation, P2-WIN-02 UI Automation inspector, P2-WIN-04 Input ownership via foreground_desktop lock (+6 more)

### Community 122 - "Phase 0 security status table"
Cohesion: 0.24
Nodes (10): Approval port (deny by default), Layering enforcement test (no Qt below presentation), Ollama health check (loopback-only), Phase 0 security status table, Tool invoker six-step pipeline (jarvis.core.tools.invoker), Typed event bus (jarvis.core.events), Hallucinated Success (HS) category, Open question: authenticating the Ollama endpoint (+2 more)

### Community 123 - "Root-scoped filesystem tools"
Cohesion: 0.27
Nodes (10): Archive extraction protections, Absolutely denied filesystem targets, Root-scoped filesystem tools, Path canonicalisation before scope check, Phase-gated mitigation roadmap, T-038 Path traversal escapes the approved root scope, T-039 Symlink or NTFS junction escapes approved scope, T-040 TOCTOU path swap after scope validation (+2 more)

### Community 124 - "Tool-invocation evaluation order"
Cohesion: 0.31
Nodes (10): Tool-invocation evaluation order, Static src/ scan for prohibited primitives, Named prohibited broad tools, Tool registry registration denylist, T-010 Self-injection via Jarvis's own prior output, T-011 Model invents a nonexistent tool name, T-012 Model requests a shell/code-execution tool, T-014 Valid tool call with out-of-scope parameters (+2 more)

### Community 125 - "ArgumentKind"
Cohesion: 0.40
Nodes (6): ArgumentKind, LaunchKind, Enum, str, How an entry is started., Constraint 5: what a per-entry argument is allowed to be.

### Community 126 - ".stop_speaking"
Cohesion: 0.22
Nodes (4): Runs on the GUI thread, whatever thread pressed the key., F9. Press to start speaking, press again to cut it short. Not hold-to-talk:…, Interrupt speech, and nothing else (ADR-0028). Deliberately not routed through…, F9. Press to start, and again to cut it short. ``RegisterHotKey`` reports the…

### Community 127 - "Redaction Before Serialisation"
Cohesion: 0.43
Nodes (7): Dual-Sink Append-Only Audit Log (jarvis.core.audit), Redaction Before Serialisation, logging settings (audit_to_sqlite, max_audit_value_chars), audit_event table, Export and Import Constraints, Ten Persisted Integrity Invariants, Two Audit Sinks, One Record of Truth

### Community 128 - "ToolInvoker (six-step pipeline)"
Cohesion: 0.21
Nodes (13): ApprovalPort, Bounded Timeouts and Declared Retry Policy, Concurrency Invariants, DenyingApprovalPort (silence is never consent), Grant Scopes (ONCE, SESSION, TASK, APPLICATION, FOLDER, ALWAYS), Permission Engine (jarvis.core.permissions), Resource Locks (jarvis.tasks.locks), Single Choke Point for Tool Execution (+5 more)

### Community 129 - "Phase 1 — Voice-first local assistant"
Cohesion: 0.16
Nodes (18): ADR-0001 Python-first shell (native Rust/Tauri deferred), ADR-0009 Scoped elevation helper interface, Deferred beyond Version 1, P1-AUD-01 Wake-word detection (openWakeWord), P1-AUD-05 Local STT (faster-whisper), P1-AUD-07 Local TTS (Kokoro), P1-AUD-10 Expressive TTS worker isolation prototype (Qwen3-TTS), P1-SEC-02 DPAPI-backed secret store (+10 more)

### Community 130 - "Automation Worker"
Cohesion: 0.22
Nodes (9): TaskScheduler, Automation Worker, Dedicated Jarvis Brave Profile, Foreground Desktop-Control Lock, Playwright Browser Automation Layer, Explicit Search Modes, Visible Browser Search, Jarvis Core (orchestration, permissions, audit) (+1 more)

### Community 131 - "qwen3-embedding:0.6b Tentative Default"
Cohesion: 0.28
Nodes (9): Model Resource Scheduler (FR-039), Option A: Strict Mutual Exclusion Scheduling, Option B: VRAM-Budget-Aware Co-Residency, ADR-0017: Embedding Model, Option B: Dedicated Retrieval-Purpose-Built Embedding Model, Embedding Invocation Frequency Cost, Option C: First-Run Wizard Hardware Benchmark, qwen3-embedding:0.6b Tentative Default (+1 more)

### Community 132 - "test_process_detection_finds_a_process_that_is_really_running"
Cohesion: 0.67
Nodes (3): The verification path has to actually work, or FR-064 is theatre., test_process_detection_finds_a_process_that_is_really_running(), WINDOWS_ONLY

### Community 133 - "Phased Delivery Plan (Phase 0-6)"
Cohesion: 0.25
Nodes (9): Google Antigravity IDE Adapter, Phased Delivery Plan (Phase 0-6), Filesystem Tool Root Scoping, IDE-Agent Orchestration, Windows Known Folder Resolution, Product Non-Goals, Prohibited Broad Tools, Safe Jarvis Workspace (+1 more)

### Community 134 - "Local Wake Phrase Detection"
Cohesion: 0.28
Nodes (9): Audio Worker, English-Only Language Policy, faster-whisper STT Engine, Local Speech-to-Text, Local Text-to-Speech, openWakeWord Model Runtime, Privacy-Preserving Audio Ring Buffer, Push-to-Talk Hotkey (+1 more)

### Community 135 - "Jarvis Shell (GUI Process)"
Cohesion: 0.31
Nodes (9): Jarvis Shell (GUI Process), Kokoro TTS Provider, Authenticated Loopback IPC, Piper TTS Provider, PySide6 Desktop Shell Toolkit, Python 3.11 as V1 Implementation Language, Qwen3-TTS Expressive Provider, Provider-Neutral TTS Interface (+1 more)

### Community 136 - "FakeSounddevice"
Cohesion: 0.22
Nodes (5): RuntimeError, fake_sounddevice(), FakeSounddevice, fixture, Refuses the wrong settings exactly as PortAudio does.

### Community 137 - "recover_interrupted_work"
Cohesion: 0.28
Nodes (7): TaskRecovered, _live_instance_ids(), Make orphaned tasks and locks safe. Never resumes anything., What startup recovery changed. Shown to the user, not swallowed., Instances that never recorded a clean shutdown, excluding this one. Only the…, recover_interrupted_work(), RecoveryReport

### Community 138 - "denial_options_for"
Cohesion: 0.22
Nodes (9): denial_options_for(), Capability, Don't ask again" options, when the capability has a meaningful target. A…, The button must not overstate what a remembered denial covers., test_a_folder_scoped_capability_offers_a_folder_denial(), test_a_url_capability_says_site_rather_than_application(), test_an_application_scoped_capability_offers_to_remember_the_denial(), test_nothing_is_offered_for_a_capability_with_no_scope_kind() (+1 more)

### Community 140 - "hotkeys.py"
Cohesion: 0.22
Nodes (7): available(), Hotkey, HotkeyError, Global hotkeys (PRD section 11.3, FR-018, ADR-0027). Two hotkeys exist in Phase…, A hotkey string could not be understood., Global hotkeys are a Windows facility in this build., A parsed combination, ready for ``RegisterHotKey``.

### Community 141 - "Path"
Cohesion: 0.22
Nodes (9): parametrize, Path, Screenshot-based computer control is still out of scope. Phase 1 legitimately…, No autonomous self-modification: every write path targets the vault., PRD section 25 lists sixteen open decisions., test_an_adr_exists_for_every_prd_open_decision(), test_no_screenshot_or_input_automation_module_exists(), test_required_documents_and_config_exist() (+1 more)

### Community 142 - "test_no_elevation.py"
Cohesion: 0.31
Nodes (6): Path, Non-administrator operation (PRD FR-003, NFR-020, ADR-0009). Phase 0 must run…, Any packaging manifest must be asInvoker., _relative(), test_no_manifest_declares_an_elevated_execution_level(), test_no_module_requests_elevation()

### Community 143 - "ADR-0014: Default English Voice"
Cohesion: 0.39
Nodes (8): ADR-0014: Default English Voice, Kokoro bm_george Default Voice, Windows SAPI Emergency Fallback, ADR-0015: Additional TTS Providers, No Silent Voice Provider Switching (FR-036), Qwen3-TTS Isolated Python 3.12 Worker, Provider-Neutral TtsProvider Interface, Update Rollback and Schema Compatibility Checks

### Community 144 - "MSIX Sandboxing vs Desktop Automation Tension"
Cohesion: 0.32
Nodes (8): espeak-ng GPL-Family Licensing Consideration, ADR-0020: Plugin and Skill Signing, ADR-0022: MSIX Distribution, Option A: MSIX as Primary Distribution Format, Option B: MSIX as Secondary Optional Channel, MSIX Sandboxing vs Desktop Automation Tension, Automation Worker Adversarial Input Exposure, ADR-0026: Code-Signing and Update Infrastructure

### Community 145 - "Voice Pack Redistribution Licensing Gap"
Cohesion: 0.29
Nodes (8): Per-Download Provider and Licence Disclosure, Voice Pack Redistribution Licensing Gap, ADR-0016: Custom Jarvis Wake Word, Option A: Purpose-Trained Custom Jarvis Wake Model, False-Activation Evaluation Harness, Hey Jarvis Interim Wake Phrase, Push-to-Talk Global Hotkey Fallback, Expired Screenshot Evidence Must Degrade Honestly

### Community 146 - "Option B: Self-Signed Developer Keys"
Cohesion: 0.36
Nodes (8): Option C: Project-Operated Signing Authority, Option B: Self-Signed Developer Keys, Skill Manifest signed Field, Option B: EV Certificate with Optional Automatic Checks, Option A: OV Certificate with Manual Update Checks, Signature Verification Precedes Execution, SmartScreen Reputation Barrier, Update Package Format and Manifest Schema

### Community 147 - "configure_logging"
Cohesion: 0.29
Nodes (6): Logger, Diagnostics: application logging and, later, crash reporting., configure_logging(), Path, Structured application logging. Separate from the audit log. The audit log…, Configure the root logger once. Idempotent.

### Community 148 - "Audit log requirements (append-only, redacted)"
Cohesion: 0.25
Nodes (8): Audit log requirements (append-only, redacted), .jarvispack normal-export secret exclusions, Deletion is non-destructive by default, Secrets storage via DPAPI / Credential Manager, Signed installers and update packages, T-050 Normal .jarvispack export includes cookies or tokens, T-072 Imported skill pack bundles pre-approved high-risk permissions, TB-12 Import/export boundary (.jarvispack)

### Community 150 - "P0-SEC-03 Permission engine"
Cohesion: 0.38
Nodes (7): P0-SEC-03 Permission engine, P2-BRW-06 Untrusted web-content wrapping and prompt-injection test, P5-IDE-05 IDE permission boundary (no automatic approval), P5-IDE-08 No hidden shell delegation (adversarial test), PermissionEngine, Phase 5 — IDE orchestration, tests/security/test_prompt_injection.py

### Community 151 - "Phase 3 — Tasks, macros, and memory"
Cohesion: 0.43
Nodes (7): P2-WIN-03 Automation worker thread (pywinauto UIA backend), P3-CLP-01 Clipboard permissions and operations, P3-MEM-01 Memory candidate pipeline with review queue and provenance, P3-MEM-03 Forget with cascade delete from derived indexes, P3-MEM-06 Portable identity export/import (.jarvispack) with secret exclusion, P3-TSK-02 Pause/resume with mandatory state re-observation, Phase 3 — Tasks, macros, and memory

### Community 152 - "ADR-0008: Secret Storage Deferred to Phase 1"
Cohesion: 0.38
Nodes (7): ADR-0008: Secret Storage Deferred to Phase 1, jarvis.core.audit.redaction Defence-in-Depth Backstop, Windows Credential Manager CredWrite/CredRead (Candidate Mechanism), DPAPI CryptProtectData via ctypes (Candidate Mechanism), Encrypted SQLite Table with DPAPI-Wrapped Key (Candidate Mechanism), No Secret Store Implemented in Phase 0, Secrets Excluded From Normal Exports

### Community 153 - "ADR-0013: Installer Technology"
Cohesion: 0.29
Nodes (7): No Elevation Manifest Security Check (asInvoker), Application Never Runs Permanently as Administrator, ADR-0013: Installer Technology, Installer Choice Sequenced Behind the MSIX Decision, NSIS (Candidate Installer), Per-User Install with No UAC Elevation, WiX Toolset MSI (Candidate Installer)

### Community 154 - "Never Claim Unverified Success"
Cohesion: 0.29
Nodes (7): Never Claim Unverified Success, Programmatically Drawn QPainter Tray Icons, ADR-0011: Public Product Name, "Jarvis" as Internal Codename Only, public_product_name Configuration Value, Rename Before Public Release (Leaning Option), Trademark and Identifier Availability Criteria

### Community 155 - "Option A: Local Backup Only, No Network Transport"
Cohesion: 0.33
Nodes (7): Rebuildable Derived Index Constraint, ADR-0021: Encrypted Sync and Backup, Option A: Local Backup Only, No Network Transport, Off-Device Backup Compromise Surface, Option B: User-Supplied Cloud Storage with Client-Side Encryption, ADR-0024: Data Retention Defaults, Cascade Deletion of Derived Data (FR-167)

### Community 156 - "generate_voice_sample"
Cohesion: 0.38
Nodes (6): ndarray, generate_voice_sample(), main(), normalise_audio(), Path, Convert Kokoro output into a one-dimensional NumPy array.

### Community 157 - "First-Run Onboarding Wizard"
Cohesion: 0.38
Nodes (7): First-Run Onboarding Wizard, Model Resource Scheduler (VRAM Arbitration), Per-Role Model Routing, Ollama Local Model Runtime, qwen3:8b Planner/Conversation Model, qwen3-vl Vision Model Route, Signed Windows Installer and Updates

### Community 158 - "Arc Reactor Visual Motif"
Cohesion: 0.52
Nodes (7): Jarvis Application Icon (Arc Reactor Mark), Arc Reactor Visual Motif, Circular Metallic Chassis Ring, Cyan-on-White Emissive Palette, Jarvis Product Brand Identity, Transparent Alpha Square Canvas, Inverted Triangular Glowing Core

### Community 159 - "HotkeyBinding"
Cohesion: 0.33
Nodes (4): HotkeyBinding, One requested hotkey and what actually became of it., Declare a hotkey. Parsing happens now; registration happens at start., Hotkeys the user asked for that are not actually working.

### Community 161 - "DenyingApprovalPort Default Implementation"
Cohesion: 0.33
Nodes (6): ADR-0007: Ollama Loopback-Only Trust Boundary, Loopback-Only Base URL Enforcement at the Adapter, Offline Mode Enforced at the Adapter Boundary, DenyingApprovalPort Default Implementation, Inno Setup (Candidate Installer), Uninstall-Time Data Deletion Must Be Opt-In

### Community 162 - "strip_wake_phrase"
Cohesion: 0.33
Nodes (6): Remove a leading wake phrase (PRD FR-024). Only from the start, and only once.…, strip_wake_phrase(), parametrize, Remind me to say hey Jarvis" is a command, not two wakes., test_only_the_leading_wake_phrase_is_stripped(), test_the_wake_phrase_is_stripped_from_the_command()

### Community 163 - ".__init__"
Cohesion: 0.33
Nodes (4): AuditLog, Capability, EventBus, The catalogue entry, or ``None`` if it is not a declared capability.

### Community 164 - "ChatProvider"
Cohesion: 0.33
Nodes (4): ChatProvider, Any, Protocol, Completes a conversation. Implementations are adapters over a runtime.

### Community 165 - ".send_message"
Cohesion: 0.33
Nodes (3): A spoken command becomes an ordinary conversation turn. The window is…, One live conversation at a time, created on first use., Run one turn on a worker thread; the model call blocks.

### Community 167 - "ToolResult"
Cohesion: 0.40
Nodes (3): The invoker's typed answer. Success requires verification., True only when the tool ran *and* confirmed its effect., ToolResult

### Community 168 - "NotifyTool"
Cohesion: 0.40
Nodes (3): Let the shell supply what only it can: desktop notifications. ``notify.show``…, NotifyTool, Show a desktop notification through the tray.

### Community 170 - "test_an_interpreter_cannot_be_added_to_the_catalogue"
Cohesion: 0.40
Nodes (5): parametrize, Adding a shell through the catalogue is still adding a shell., test_a_malformed_aumid_is_refused(), test_a_non_http_url_is_refused(), test_an_interpreter_cannot_be_added_to_the_catalogue()

### Community 171 - "test_whisper.py"
Cohesion: 0.70
Nodes (4): list_audio_devices(), main(), record_audio(), transcribe_audio()

### Community 172 - "Retention and Deletion Rules"
Cohesion: 0.67
Nodes (4): privacy retention defaults, Retention and Deletion Rules, Soft References So Audit Survives Its Subject, Privacy Defaults (telemetry off, no raw audio)

### Community 173 - "_same_microphone"
Cohesion: 0.50
Nodes (4): Match device names across host APIs, which truncate them differently., _same_microphone(), MME truncates names, so an exact comparison never matches., test_matching_the_same_microphone_across_host_apis()

### Community 174 - "test_enabling_then_disabling_leaves_no_entry"
Cohesion: 0.50
Nodes (4): WINDOWS_ONLY, Runs against the real per-user Run key, and cleans up after itself., test_enabling_then_disabling_leaves_no_entry(), test_the_startup_command_points_at_an_interpreter_that_exists()

### Community 175 - "AppConfig"
Cohesion: 0.18
Nodes (6): field_validator, AppConfig, The whole validated configuration tree., Adopt changed configuration without rebuilding the router., test_configuration_is_typed_and_rejects_unknown_keys(), test_shipped_defaults_validate()

## Ambiguous Edges - Review These
- `T-030 Foreground lock not released after Automation Worker crash` → `T-034 Consequential action replayed after restart`  [AMBIGUOUS]
  THREAT_MODEL.md · relation: semantically_similar_to
- `Arc Reactor Visual Motif` → `Cyan-on-White Emissive Palette`  [AMBIGUOUS]
  resources/icons/jarvis_icon.png · relation: references
- `"Jarvis" as Internal Codename Only` → `ADR-0012: Shell Technology for the First Public Build`  [AMBIGUOUS]
  docs/decisions/ADR-0011-public-product-name.md · relation: conceptually_related_to

## Knowledge Gaps
- **45 isolated node(s):** `openWakeWord Model Runtime`, `faster-whisper STT Engine`, `Jarvis Shell (PySide6 GUI and tray)`, `TB-3 Core to Audio Worker`, `Other local Windows users` (+40 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `T-030 Foreground lock not released after Automation Worker crash` and `T-034 Consequential action replayed after restart`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Arc Reactor Visual Motif` and `Cyan-on-White Emissive Palette`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `"Jarvis" as Internal Codename Only` and `ADR-0012: Shell Technology for the First Public Build`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `JarvisCore` connect `JarvisCore` to `EventBus`, `JarvisApplication`, `Path`, `NetworkMode`, `VoiceService`, `test_ollama_tool_calling.py`, `test_phase0_exit_criteria.py`, `MainWindow`, `NotifyTool`, `AppConfig`, `.shutdown`, `.recovery`, `main_window.py`, `core.py`, `.start`, `model_directory`, `main.py`, `app.py`, `ApplicationCatalogue`, `test_at014_private_session.py`, `ConfigStore`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `TaskStore`, `ToolCall`, `types.py`, `.__init__`, `ConversationStore`, `recover_interrupted_work`, `EventBus`, `PermissionEngine`, `tools/ports.py`, `ResourceLockManager`, `AuditLog`, `personality.py`, `PersonalityStore`, `test_runtime_primitives.py`, `ModelRouter`, `JarvisCore`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `VoiceService` connect `VoiceService` to `core.py`, `VoiceController`, `.start`, `configured_duplex_mode`, `service.py`, `test_offline_speech_models.py`, `JarvisCore`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `JarvisCore` (e.g. with `VoiceService` and `AppConfig`) actually correct?**
  _`JarvisCore` has 13 INFERRED edges - model-reasoned connections that need verification._