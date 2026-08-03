# Graph Report - .  (2026-08-03)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 3438 nodes · 7063 edges · 187 communities (172 shown, 15 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 781 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2e3a0d9d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ToolCall
- TaskStore
- test_audio_pipeline.py
- EventBus
- ApprovalPanel
- ApprovalQueue
- TaskScheduler
- ResourceLockManager
- AuditLog
- ConversationPanel
- test_application_launch.py
- test_ollama_tool_calling.py
- Worker
- test_config.py
- types.py
- PersonalityStore
- audio/ports.py
- VoiceService
- AudioChunk
- test_at002_wake_privacy.py
- system_health.py
- JarvisApplication
- test_phase0_exit_criteria.py
- JarvisTrayIcon
- PermissionEngine
- AudioUnavailable
- phase1_tools.py
- test_permission_engine.py
- Database
- model_directory
- permissions/models.py
- OllamaChatProvider
- test_core_lifecycle.py
- test_wake_install.py
- JarvisCore
- redact
- test_shell.py
- tools/__init__.py
- test_grounding_and_history.py
- MainWindow
- test_secret_store.py
- VoicePanel
- ConversationStore
- VoicePipeline
- VoiceController
- test_conversation_wiring.py
- module_available
- play
- VaultPaths
- schema.py
- apply_network_policy
- test_speak_tool.py
- locks.py
- llm/conversation.py
- SingleInstanceGuard
- OpenApplicationTool
- capture.py
- OpenWakeWordDetector
- config/store.py
- tools/ports.py
- wake.py
- tasks/__init__.py
- ApprovalRequest
- Conversation
- launch.py
- test_voice_wiring.py
- Project Jarvis (Windows Local AI Desktop Agent)
- AppConfig
- OllamaHealthChecker
- ModelRouter
- test_hotkeys_and_startup.py
- _PermissionsPanel
- Dedicated Jarvis Brave Profile
- Resource Lock Model
- ui/__init__.py
- ToolRegistry
- Project Jarvis Implementation Backlog
- Phase 0 — Foundation and safety architecture
- ListeningState
- TtsProvider
- RingBuffer
- grounding.py
- test_no_shell.py
- test_prohibited_capabilities.py
- qwen3-embedding:0.6b Tentative Default
- GlobalHotkeys
- Architectural Drivers
- Extension Points Table
- ADR-0003: A Closed Capability Set — No Generic Execution Primitive
- Subscription
- ValueError
- media.py
- test_lazy_audio_imports.py
- Over-Permission (OP) category
- service.py
- T-052 Another local Windows user reads the SQLite vault
- contract.py
- .__init__
- test_layering.py
- single_instance.py
- Residual risks accepted for Phase 0
- ApplicationCatalogue
- test_at014_private_session.py
- Typed In-Process Event Bus (jarvis.core.events)
- .execute
- On-Demand Narrowly Scoped Elevated Helper Process
- SQLite (jarvis.db) Canonical Transactional Store
- Prompt Injection (PI) category
- Five-component process model
- test_runtime_primitives.py
- JarvisCore (composition root)
- Five-Suite Test Architecture
- Closed Enumerated Set of Narrow Typed Tools
- Capability Risk Classes
- NetworkMode
- core.py
- LLM Boundary (jarvis.llm)
- .__init__
- jarvis.core.events In-Process Publish/Subscribe Bus
- Option B: Per-Stream Retention Defaults with Expiry
- OllamaHealth
- startup.py
- ConfigStore
- task table
- main
- Phase 2 — Deterministic desktop and browser automation
- Option B: Self-Signed Developer Keys
- .__init__
- Phase 0 security status table
- Root-scoped filesystem tools
- Tool-invocation evaluation order
- assert_transition
- .set_setting
- Redaction Before Serialisation
- ToolInvoker (six-step pipeline)
- Phase 1 — Voice-first local assistant
- Automation Worker
- Phased Delivery Plan (Phase 0-6)
- Local Wake Phrase Detection
- Jarvis Shell (GUI Process)
- hotkeys.py
- Path
- test_no_elevation.py
- MSIX Sandboxing vs Desktop Automation Tension
- Voice Pack Redistribution Licensing Gap
- configure_logging
- T-048 Secrets leak into audit log, crash dump, or telemetry
- Resource Locks (jarvis.tasks.locks)
- P0-SEC-03 Permission engine
- Phase 3 — Tasks, macros, and memory
- ADR-0008: Secret Storage Deferred to Phase 1
- ADR-0013: Installer Technology
- Never Claim Unverified Success
- ._on_event
- First-Run Onboarding Wizard
- Arc Reactor Visual Motif
- _read_yaml_mapping
- HotkeyBinding
- Any
- ConversationWorker
- Option A: Local Backup Only, No Network Transport
- DenyingApprovalPort Default Implementation
- ADR-0014: Default English Voice
- strip_wake_phrase
- redact_for_speech
- FakeStream
- .quit
- test_whisper.py
- Retention and Deletion Rules
- test_enabling_then_disabling_leaves_no_entry
- InstallReport
- vault_free_bytes
- fake_ollama
- fake_sounddevice
- core/__init__.py
- llm/__init__.py
- test_an_unparseable_hotkey_is_reported_not_raised
- T-019 Mis-transcribed command causes destructive action
- UUID4 Hex Identifiers (jarvis.common.new_id)
- project-jarvis
- QWidget
- AuditLog
- model_validator
- Any
- Exception
- VaultPaths

## God Nodes (most connected - your core abstractions)
1. `JarvisCore` - 84 edges
2. `Database` - 71 edges
3. `EventBus` - 63 edges
4. `ToolCall` - 60 edges
5. `AuditLog` - 57 edges
6. `AudioChunk` - 49 edges
7. `JarvisApplication` - 49 edges
8. `MainWindow` - 48 edges
9. `ResourceLockManager` - 45 edges
10. `TaskStore` - 43 edges

## Surprising Connections (you probably didn't know these)
- `Export and Import Constraints` --semantically_similar_to--> `Redaction Before Serialisation`  [INFERRED] [semantically similar]
  DATA_MODEL.md → ARCHITECTURE.md
- `Concurrency Invariants` --semantically_similar_to--> `SQLite Concurrency Strategy (WAL, per-thread connections)`  [INFERRED] [semantically similar]
  ARCHITECTURE.md → DATA_MODEL.md
- `Rust Deferred Until After Phase 3` --conceptually_related_to--> `Only L5 May Import PySide6`  [INFERRED]
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

## Communities (187 total, 15 thin omitted)

### Community 0 - "ToolCall"
Cohesion: 0.06
Nodes (65): AuditCategory, RetryPolicy, Any, BaseModel, RiskLevel, Verification, Make "don't ask again" stick, as a scoped DENY grant (ADR-0027). No engine…, Record the user's decision so a broader scope is honoured next time. (+57 more)

### Community 1 - "TaskStore"
Cohesion: 0.06
Nodes (49): LookupError, from_iso(), json_dumps(), json_loads(), new_id(), Any, datetime, Small shared primitives used across every layer. Kept deliberately tiny:… (+41 more)

### Community 2 - "test_audio_pipeline.py"
Cohesion: 0.05
Nodes (44): BargeInReport, DuplexCoordinator, DuplexMode, PlaybackWindow, datetime, Enum, str, Full-duplex audio and barge-in (ADR-0028, PRD FR-015, section 11.3). ADR-0028… (+36 more)

### Community 3 - "EventBus"
Cohesion: 0.07
Nodes (45): MonkeyPatch, QApplication, EventBus, In-process typed event bus (ADR-0005). Deliberately not a message broker: no…, Thread-safe publish/subscribe with subclass matching., Typed event bus and the domain event vocabulary., approving_invoker(), audit() (+37 more)

### Community 4 - "ApprovalPanel"
Cohesion: 0.08
Nodes (37): ApprovalController, ApprovalPanel, Decision, GrantScope, QObject, QWidget, Every PRD section 11.2 field, and no field invented to fill a gap., Bottom-right of the available desktop — where the tray lives. (+29 more)

### Community 5 - "ApprovalQueue"
Cohesion: 0.08
Nodes (41): ApprovalQueue, Called whenever the pending set changes. Used by the tray., Holds requests between the thread that needs an answer and the user. Implements…, offerable_scopes_for(), Decision, GrantScope, RiskLevel, The allow-scopes the dialog may offer, per the ADR-0027 table. Low offers… (+33 more)

### Community 6 - "TaskScheduler"
Cohesion: 0.07
Nodes (25): BaseModel, Enum, Protocol, str, A registered unit of work., Why a runner was asked to stop., What a runner reports when it returns., StopReason (+17 more)

### Community 7 - "ResourceLockManager"
Cohesion: 0.08
Nodes (36): StaleLockReclaimed, Release everything this runtime holds. Called during shutdown., Release locks whose owning runtime instance is gone (PRD FR-006). Without this,…, Exclusive, persisted, owner-attributed locks., ResourceLockManager, Task state machine, durable store, locks and scheduler (PRD FR-120 .. FR-133)., A partial acquisition would deadlock two tasks against each other., PRD FR-006: a crash while holding a lock must not wedge the resource. (+28 more)

### Community 8 - "AuditLog"
Cohesion: 0.08
Nodes (31): Audit logging and secret redaction., AuditLog, Any, datetime, Path, Append-only audit log with two sinks (ARCHITECTURE.md section 6.3). *…, Every record from the JSONL file, oldest first., Search the SQLite index. Falls back to the JSONL file if unavailable. (+23 more)

### Community 9 - "ConversationPanel"
Cohesion: 0.08
Nodes (26): SourceLabel, ConversationPanel, _escape(), The Conversation screen (PRD section 9.5, FR-045, FR-046, FR-047). Two things…, Enable or disable input, and say exactly why when disabled. The window…, Everything shown here is data, including the model's own output., Text conversation with the local model., panel() (+18 more)

### Community 10 - "test_application_launch.py"
Cohesion: 0.08
Nodes (36): build_argv(), default_catalogue(), Refuse an unsafe catalogue entry at registration time (constraint 4)., Construct the argument vector. Pure, so it is directly testable., The Phase 1 seed: exactly the applications PRD section 21 names. Paths are the…, validate_entry(), executable_entry(), parametrize (+28 more)

### Community 11 - "test_ollama_tool_calling.py"
Cohesion: 0.10
Nodes (32): ConversationEngine, Runs one turn: prompt, model, tools, grounding, reply., ChatResponse, What a provider returned. ``text`` is for the user. ``tool_calls`` is for the…, _decode(), echo_invoker(), EchoParams, EchoResult (+24 more)

### Community 12 - "Worker"
Cohesion: 0.07
Nodes (16): ABC, PeriodicWorker, BaseException, Worker threads and their supervisor (PRD NFR-003, ARCHITECTURE.md section 4.1).…, Calls a function on an interval until stopped., Starts and stops workers in a defined order., Stop in reverse order. Returns the names that stopped cleanly., A named background thread with a cooperative stop. (+8 more)

### Community 13 - "test_config.py"
Cohesion: 0.07
Nodes (24): PathLike, expand_path(), find_defaults_config(), _platform_default_root(), Data-vault path resolution. This is the *only* module permitted to expand…, Locate the shipped ``defaults.yaml``. Order: ``JARVIS_DEFAULTS_CONFIG`` env…, Expand ``%VARS%``, ``$VARS`` and ``~`` then normalise to an absolute path., Project Jarvis — local-first Windows desktop AI agent. "Jarvis" is an internal… (+16 more)

### Community 14 - "types.py"
Cohesion: 0.09
Nodes (31): Deliver to every matching handler. Returns the number invoked. Handler…, ApprovalRequested, ApprovalResolved, AppStarted, AppStopping, ConfigChanged, EmergencyStopCompleted, EmergencyStopRequested (+23 more)

### Community 15 - "PersonalityStore"
Cohesion: 0.11
Nodes (25): Formality, Humour, PersonalityProfile, PersonalityProposal, PersonalityStore, ProposalStatus, Enum, str (+17 more)

### Community 16 - "audio/ports.py"
Cohesion: 0.07
Nodes (29): AudioFormat, Enum, str, Audio provider boundaries (ARCHITECTURE.md section 8, PRD sections 10.2-10.4).…, What was said. ``confidence`` gates confirmation (PRD FR-023)., Voice activity bounds for one command (PRD FR-014)., SpeechSegment, Transcript (+21 more)

### Community 17 - "VoiceService"
Cohesion: 0.07
Nodes (13): DuplexMode, NoiseCalibration, AudioChunk, No enrolment has been run in this build, so nothing has passed., Whether anything can actually be heard. Speaking depends on it., Open the microphone. Returns False, honestly, if it cannot., Measure the room and apply the threshold (PRD FR-017)., Synthesise **and play**, then report what actually came out. Synthesis alone… (+5 more)

### Community 18 - "AudioChunk"
Cohesion: 0.08
Nodes (21): Record how loud Jarvis's own output was, for the echo comparison., AudioChunk, A block of mono audio. ``samples`` is raw bytes, never a file path., calibrate(), NoiseCalibration, Enum, str, Voice activity detection and command bounds (PRD FR-014, FR-017). Energy-based,… (+13 more)

### Community 19 - "test_at002_wake_privacy.py"
Cohesion: 0.10
Nodes (24): NullWakeDetector, No wake detection. Says exactly why, and never fabricates an event., FakeStt, FakeWake, frame(), Path, AT-002 — listening enabled, no wake phrase, no audio on disk. Also PRD FR-012…, FR-012: a *short* window, not a recording. (+16 more)

### Community 20 - "system_health.py"
Cohesion: 0.12
Nodes (23): BaseModel, Exception, Per-invocation context handed to a tool. Carries no ambient authority., What a tool returns on success., Raised by a tool to report a declared failure. The code must be declared., Bounded retries only (PRD FR-133, NFR-012)., RetryPolicy, ToolContext (+15 more)

### Community 21 - "JarvisApplication"
Cohesion: 0.07
Nodes (14): JarvisApplication, QObject, Runs on the audio thread, so it only queues work onto the GUI one., A spoken command becomes an ordinary conversation turn., The keyboard route to a waiting request (PRD NFR-030)., One live conversation at a time, created on first use., Run one turn on a worker thread; the model call blocks., Release the worker only once its thread has actually stopped. Dropping it in… (+6 more)

### Community 22 - "test_phase0_exit_criteria.py"
Cohesion: 0.06
Nodes (29): AppConfig, Phase 0 exit criteria and hard constraints. One test (or small group) per…, The tool set stays small and low risk. Phase 0 registered exactly one tool.…, PRD FR-048: succeeded requires verification, so it must be declared., PRD section 13.4: free-form text can never be executed., PRD section 4.4: nothing may silently become permanent memory., PRD section 9.1 and NFR-033., test_configuration_is_typed_and_rejects_unknown_keys() (+21 more)

### Community 23 - "JarvisTrayIcon"
Cohesion: 0.07
Nodes (19): ActivationReason, QAction, QMenu, QSystemTrayIcon, JarvisTrayIcon, QObject, Colour, shape, tooltip and accessible name all change together., Enable the keyboard route and say how many are waiting. (+11 more)

### Community 24 - "PermissionEngine"
Cohesion: 0.12
Nodes (17): PermissionEvaluation, PermissionGrant, PermissionRequest, DefaultPolicy, PermissionEngine, AuditLog, Capability, Decision (+9 more)

### Community 25 - "AudioUnavailable"
Cohesion: 0.10
Nodes (18): AudioUnavailable, RuntimeError, A selectable voice, with the licence metadata FR-032 requires., An audio component cannot run, and says which and why., SynthesisResult, VoiceDescription, build_tts_provider(), KokoroTtsProvider (+10 more)

### Community 26 - "phase1_tools.py"
Cohesion: 0.23
Nodes (31): BaseModel, ArgumentKind, CatalogueError, LaunchKind, Enum, str, A catalogue entry was refused. Raised at registration, not at launch., How an entry is started. (+23 more)

### Community 27 - "test_permission_engine.py"
Cohesion: 0.10
Nodes (29): PermissionRequest, A question put to the permission engine. Contains no side effects., parametrize, Permission evaluation (PRD sections 9.9 and 11.1, ARCHITECTURE.md 6.4)., A user who denied something should not be asked again in the same scope., PRD 11.1: fresh confirmation every time., PRD 9.9: high-risk permissions must not offer 'always allow'., test_a_deny_grant_outranks_an_allow_grant() (+21 more)

### Community 28 - "Database"
Cohesion: 0.10
Nodes (22): Exception, AuditLog, AuditLog, Database, DatabaseError, Path, Close every connection this database handed out., The database could not be opened, migrated or queried. (+14 more)

### Community 29 - "model_directory"
Cohesion: 0.15
Nodes (27): install_wake_model(), installed_files(), is_installed(), missing_files(), model_directory(), Path, One-time wake-word model installation (ADR-0016, PRD section 17.2). **No wake-…, All required files present. Says nothing about whether they *work*. (+19 more)

### Community 30 - "permissions/models.py"
Cohesion: 0.12
Nodes (27): _c(), capabilities_by_risk(), capability(), capability_ids(), The capability catalogue — PRD section 11.1 expressed as data. Risk…, Permission model, capability catalogue and evaluation engine., Capability, Decision (+19 more)

### Community 31 - "OllamaChatProvider"
Cohesion: 0.11
Nodes (21): _as_int(), OllamaChatProvider, Any, Ollama chat completion (PRD FR-040, section 13.4, ADR-0007). Inherits the two…, Read only the structured field. Never parse prose for an action., Describe one registered tool in the format Ollama expects. Built from the…, Chat against a loopback Ollama. Blocking; call from a worker thread., tool_schema_for() (+13 more)

### Community 32 - "test_core_lifecycle.py"
Cohesion: 0.11
Nodes (29): _new_core(), Full core lifecycle, crash recovery and settings durability., Phase 0 exit criterion., PRD NFR-011: no consequential action is repeated after a restart., Kill the process the way a crash does: threads gone, nothing cleaned up.…, simulate_crash(), test_a_clean_start_reports_nothing_to_recover(), test_a_completed_task_is_never_re_run_after_recovery() (+21 more)

### Community 33 - "test_wake_install.py"
Cohesion: 0.12
Nodes (28): make_files(), Path, The wake-model bootstrap (ADR-0016, PRD section 17.2). No test here downloads…, A corrupt download must not be reported as ready (ADR-0010)., The command's exit code reflects usability, not download success., Hey Travis" measured 0.489, so 0.5 left almost no margin., ONNX on Windows; the library's own default is tflite., A wake model alone cannot initialise a detector. (+20 more)

### Community 34 - "JarvisCore"
Cohesion: 0.09
Nodes (14): Conversation, OllamaHealth, RecoveryReport, JarvisCore, Everything except the user interface., Let the shell supply what only it can: desktop notifications. ``notify.show``…, Begin a conversation. A private one writes nothing (FR-046, AT-014)., Grant the two strictly self-inspecting capabilities on first start.… (+6 more)

### Community 35 - "redact"
Cohesion: 0.11
Nodes (26): classify_content(), is_content_key(), is_secret_key(), Any, Secret redaction for the audit log (PRD section 11.5, FR-259). Redaction…, Return a copy of ``value`` safe to persist in the audit log. Mappings,…, Describe a value without reproducing it. Used where the *shape* of user content…, Redact secret-looking substrings, then bound the length. (+18 more)

### Community 36 - "test_shell.py"
Cohesion: 0.07
Nodes (24): fixture, Tray, main window and the Qt event bridge. Runs under…, No placeholder screen may look like it works (ADR-0010, PRD section 1.10)., Phase 1 adds Conversation and Voice. Everything else still names its phase., PRD FR-001: Jarvis stays functional when the main window is closed., PRD NFR-033: do not rely on colour alone., ADR-0010: visible, disabled, honest — never hidden and never faked., test_about_states_the_phase_and_the_absence_of_a_shell() (+16 more)

### Community 37 - "tools/__init__.py"
Cohesion: 0.13
Nodes (24): ToolRegistered, Protocol, What an implementation must provide., Tool, Tool contract, allow-list registry, prohibited guard and the invoker. This…, assert_tool_id_permitted(), check_tool_id(), ProhibitedToolError (+16 more)

### Community 38 - "test_grounding_and_history.py"
Cohesion: 0.11
Nodes (26): claims_completion(), Whether a reply asserts that something was done., Label a reply and stop it claiming an unverified success. ``tool_results`` are…, review_response(), parametrize, Source labelling, tool-grounded success, history and personality. PRD FR-045,…, AT-018: never report completed when it could not be verified., PRD section 4.4: no silent learning. (+18 more)

### Community 39 - "MainWindow"
Cohesion: 0.14
Nodes (7): QMainWindow, MainWindow, Navigation shell over live core state., Closing the window leaves Jarvis running in the tray (PRD FR-001)., test_the_window_says_plainly_when_nothing_is_waiting(), test_conversation_is_a_live_area_not_a_phase_placeholder(), test_the_home_screen_reports_the_voice_stack_honestly()

### Community 40 - "test_secret_store.py"
Cohesion: 0.14
Nodes (26): SecretStore, fixture, skipif, WINDOWS_ONLY, The secret store (ADR-0030, PRD 18.3, NFR-022, FR-169, AT-016). The assertions…, Never partial, never best-effort plaintext., Lifting a value under a different name must not decrypt it., Degrading to weaker protection would be worse than refusing (ADR-0010). (+18 more)

### Community 41 - "VoicePanel"
Cohesion: 0.08
Nodes (11): phrase_disclosure(), The sentence the Voice screen must show (FR-011). It states the phrase actually…, QWidget, Always show the exact destination path, installed or not., State the phrase literally. Never label it 'Jarvis' (FR-011)., Show the measurement, and gate always-listening on it (ADR-0016)., Say plainly whether the microphone is open (PRD FR-013)., True if anything on this screen implies bare "Jarvis" works. FR-011 forbids… (+3 more)

### Community 42 - "ConversationStore"
Cohesion: 0.09
Nodes (17): ConversationStore, Begin a conversation. ``persist=False`` is a private session., Stop recording this conversation, and erase what was recorded. Per-conversation…, Remove a conversation and its turns. Messages cascade., Creates conversations and records turns, when recording is permitted., Global history control (PRD FR-045). Affects new conversations., AT-014, structurally: not written, rather than written then removed., Leaving half a transcript satisfies neither reading of the request. (+9 more)

### Community 43 - "VoicePipeline"
Cohesion: 0.12
Nodes (11): _join(), AudioChunk, Watch raw frames, for measuring the room (PRD FR-017). Observers see frames…, Begin waiting for the wake phrase, if enrolment allows it., Stop, and forget everything held. Nothing survives in memory., F9 pressed. Capture a command without a wake phrase (FR-018)., F9 released. Transcribe what was captured., One captured frame. Called from the audio thread. (+3 more)

### Community 44 - "VoiceController"
Cohesion: 0.10
Nodes (9): F9. Press to start speaking, press again to cut it short. Not hold-to-talk:…, QObject, F9. Press to start, and again to cut it short. ``RegisterHotKey`` reports the…, Transcription blocks for seconds, so never on the GUI thread., Switch microphone. Reopens the stream if one is already open., Collect a few seconds of room tone, then set the threshold., ADR-0010: name the phase rather than pretending or failing quietly., Owns everything that connects the Voice screen and F9 to the service. (+1 more)

### Community 45 - "test_conversation_wiring.py"
Cohesion: 0.13
Nodes (21): ExplodingEngine, FakeEngine, _pump(), The wiring between the Conversation screen and the engine. The panel tests…, A silent failure is the worst outcome; it must always say something., Each send created a QThread whose quit signal could never arrive., Exiting with this thread running kills the process natively, not by exception —…, refresh_conversation runs every 2 seconds and must not undo 'Thinking…'. (+13 more)

### Community 46 - "module_available"
Cohesion: 0.15
Nodes (14): _capture_status(), ComponentStatus, describe_voice_stack(), module_available(), Path, What of the voice stack is actually usable right now (ADR-0010, NFR-014). Audio…, Report each component's real state, reading configuration when given., True if ``module`` could be imported, without importing it. (+6 more)

### Community 47 - "play"
Cohesion: 0.15
Nodes (24): _as_float_array(), play(), AudioChunk, Decode the chunk's bytes into the float32 mono array a stream wants., Play one chunk, blocking, and report what was heard. Blocking by design: the…, AudioChunk, Audio playback, and the honesty rule that depends on it (FR-030, FR-048).…, The coordinator documents this flag as polled between buffers. (+16 more)

### Community 48 - "VaultPaths"
Cohesion: 0.14
Nodes (5): Path, Instance-scoped files such as the single-instance lock., Create the vault layout. Idempotent., Every path the application is allowed to write to, derived from one root., VaultPaths

### Community 49 - "schema.py"
Cohesion: 0.15
Nodes (24): AudioConfig, _Base, ConversationLanguageConfig, DefaultPermissionPolicy, LanguageConfig, LlmConfig, LoggingConfig, ModelProfile (+16 more)

### Community 50 - "apply_network_policy"
Cohesion: 0.14
Nodes (21): apply_network_policy(), _clear_mark(), hub_is_offline(), _mark_set_here(), Keep the speech model hubs off the network in offline mode (PRD AT-001). The…, Pin the hubs to their local cache when offline. Returns True if offline.…, _was_set_here(), clean_environment() (+13 more)

### Community 51 - "test_speak_tool.py"
Cohesion: 0.15
Nodes (21): PlaybackReport, What playback actually did. Never assumed by the caller., test_a_report_describes_itself_honestly(), _audio(), AudioChunk, ``voice.speak`` must not claim speech it cannot evidence (FR-048, AT-018). The…, FR-034: say something was withheld rather than quietly changing it., The invoker rejects an undeclared code, so this must stay in step. (+13 more)

### Community 52 - "locks.py"
Cohesion: 0.13
Nodes (13): LockAcquired, LockContended, LockReleased, SQLite access (ADR-0002). ``jarvis.db`` is the canonical transactional store.…, _Contended, LockSetLease, Exception, Resource locks (PRD FR-124, section 7.1). Only one task may hold a given named… (+5 more)

### Community 53 - "llm/conversation.py"
Cohesion: 0.12
Nodes (15): The conversation engine (PRD FR-040, FR-042, FR-047, FR-048, section 13.4).…, Conversation history and private sessions (PRD FR-045, FR-046, AT-014). A…, Turns for a live conversation, from memory; otherwise from storage., StoredMessage, ChatProvider, ChatRole, ModelRole, Any (+7 more)

### Community 54 - "SingleInstanceGuard"
Cohesion: 0.11
Nodes (13): BaseException, Path, Remove a lock file whose owning process is gone., Acquire once at startup; release at shutdown. ``acquired`` is the only thing…, SingleInstanceGuard, test_a_lock_file_from_a_dead_process_is_reclaimed(), test_a_second_instance_is_refused(), test_acquire_or_raise_explains_the_refusal() (+5 more)

### Community 55 - "OpenApplicationTool"
Cohesion: 0.14
Nodes (22): OpenApplicationTool, OpenUrlTool, Open a URL in the approved browser. Scheme-restricted (ADR-0029)., Launch a catalogued application and verify it started (FR-063, FR-064)., catalogue(), launching_invoker(), fixture, parametrize (+14 more)

### Community 56 - "capture.py"
Cohesion: 0.14
Nodes (12): capture_available(), CaptureSession, default_input_device(), frames_from_bytes(), list_devices(), Microphone capture and playback (PRD FR-016, FR-013, ADR-0028). ``sounddevice``…, Cut a recording into frames. Used to replay fixtures through the pipeline., Enumerate devices for the Voice screen (PRD FR-016). Never raises. (+4 more)

### Community 57 - "OpenWakeWordDetector"
Cohesion: 0.13
Nodes (10): build_wake_detector(), OpenWakeWordDetector, AudioChunk, Path, openWakeWord over a pretrained base model, with a personal threshold., Applied after enrolment measurement chooses one., Highest score this frame produced across the loaded models., Yield an event whenever a frame crosses the threshold. (+2 more)

### Community 58 - "config/store.py"
Cohesion: 0.15
Nodes (16): Configuration layer (L1). Must not import anything above L1., ConfigError, deep_merge(), _delete_by_path(), _env_overrides(), _get_by_path(), _parse_env_value(), Any (+8 more)

### Community 59 - "tools/ports.py"
Cohesion: 0.12
Nodes (17): PendingApproval, datetime, The approval queue — step 5 of the invoker pipeline, made answerable. ADR-0027…, One unanswered request. Mutable, unlike everything on the event bus., denial_options_for(), Capability, Ports the tool invoker depends on, so ``jarvis.core`` stays free of Qt and of…, A "don't ask again" choice offered alongside Deny (ADR-0027). (+9 more)

### Community 60 - "wake.py"
Cohesion: 0.11
Nodes (13): choose_threshold(), EnrolmentMeasurement, EnrolmentResult, EnrolmentSample, measure_enrolment(), Wake-word detection and per-user enrolment (ADR-0016, PRD FR-010, FR-011).…, One recording of the user saying the phrase. Personal data (criterion 3)., The measured result. ADR-0016 criterion 1: without this, no enabling. (+5 more)

### Community 61 - "tasks/__init__.py"
Cohesion: 0.15
Nodes (16): Timezone-aware current time. Never use ``datetime.utcnow()``., utc_now(), TaskRecovered, Ollama health check (ADR-0007). Two boundary rules are enforced here rather…, Task subsystem (L3): state machine, durable store, locks, scheduler, recovery., close_instance(), _live_instance_ids(), Crash recovery (PRD FR-006, NFR-010, NFR-011, AT-011). On startup, work left… (+8 more)

### Community 62 - "ApprovalRequest"
Cohesion: 0.15
Nodes (10): Decision, GrantScope, Declare whether a user interface is actually connected. Until one is, queueing…, Block the calling thread until answered, or until the request expires. Called…, Record the user's decision. Returns False if nothing was waiting. Raises…, Deny everything outstanding. Used by emergency stop and by shutdown., ApprovalOutcome, ApprovalRequest (+2 more)

### Community 63 - "Conversation"
Cohesion: 0.12
Nodes (11): _describe_result(), Any, Send one proposal through the invoker. Never around it., Describe only registered tools. The model cannot learn of others., Render a tool result for the model, without inflating it., One user request and everything that came of it., Turn, Conversation (+3 more)

### Community 64 - "launch.py"
Cohesion: 0.12
Nodes (20): _basename(), launch(), launch_argv(), LaunchOutcome, process_running(), The one authorised process-creation call site (ADR-0029). Everything about this…, What actually happened. ``verified`` is never assumed (constraint 9)., Constraint 5: validate the caller's argument against the entry's type. (+12 more)

### Community 65 - "test_voice_wiring.py"
Cohesion: 0.10
Nodes (19): application(), _pump(), fixture, The Voice screen's controls must be connected, or honestly disabled. Every…, Recording without a visible indicator is a prohibited capability., Without one, capture could start with nothing on screen., The pipeline transcribed commands that had no listener at all., ``application.voice`` stayed None, so push-to-talk always refused. (+11 more)

### Community 66 - "Project Jarvis (Windows Local AI Desktop Agent)"
Cohesion: 0.13
Nodes (20): Application Catalogue and Aliases, Connected Mode (Optional External Providers), Deterministic Before Visual (Automation Hierarchy), Local Document Understanding, Hallucination Discipline (Epistemic Labelling), Honest Task Status, Bounded Definition of Learning, Local First, Not Local Only (+12 more)

### Community 67 - "AppConfig"
Cohesion: 0.16
Nodes (11): AppConfig, The whole validated configuration tree., ConfigStore, Loads, validates and persists configuration. Only the *difference from…, Validate then persist a single override. Returns the new config. The candidate…, Remove an override, returning the setting to its shipped default., Adopt changed configuration without rebuilding the router., test_single_instance_enforcement_blocks_a_second_core() (+3 more)

### Community 68 - "OllamaHealthChecker"
Cohesion: 0.15
Nodes (15): OllamaHealthChecker, Exception, Checks the local model runtime. Blocking; call it from a worker thread., Ollama adapter boundary rules (ADR-0007, PRD AT-001)., PRD NFR-013: every external interaction has a timeout., A remote 'local' endpoint would ship every prompt off the machine., Turning the check off is possible, but must be a deliberate configuration., test_a_non_loopback_endpoint_is_refused_without_opening_a_socket() (+7 more)

### Community 69 - "ModelRouter"
Cohesion: 0.12
Nodes (13): ModelBusyError, ModelRouter, RuntimeError, A heavy model is loaded and sequential loading is configured., Resolves a role to a configured profile, and gates heavy loads., Reserve a role's model for the duration of a call. Under sequential loading,…, RoutedModel, PRD FR-039: 12 GB will not hold two heavy models with large contexts. (+5 more)

### Community 70 - "test_hotkeys_and_startup.py"
Cohesion: 0.13
Nodes (17): parse_hotkey(), Parse ``"Ctrl+Alt+Pause"`` or ``"F9"``. Raises :class:`HotkeyError`., parametrize, skipif, Global hotkeys and start-at-sign-in (PRD section 11.3, FR-018, FR-002). Parsing…, PRD section 11.3 and config/defaults.yaml agree on this combination., FR-018 and ADR-0027 specify bare F9, with no modifier., An emergency stop that fires forty times is not better than one. (+9 more)

### Community 71 - "_PermissionsPanel"
Cohesion: 0.19
Nodes (9): NavArea, _NotImplementedPanel, _PermissionsPanel, QWidget, A heading, a refresh button and a read-only text area., Active grants, and any approval currently waiting for an answer. The panel…, Says exactly what is missing and when it arrives. Never a fake screen., _TablePanel (+1 more)

### Community 72 - "Dedicated Jarvis Brave Profile"
Cohesion: 0.16
Nodes (18): ADR-0018: Search Provider, Option C: Ask a Configured AI Website (FR-055), Untrusted Web Content Wrapping (FR-054), Visible Brave Search Mode (FR-052), ADR-0019: Browser Profile Isolation, CAPTCHA Pause-and-Ask Requirement (FR-058), Dedicated Jarvis Brave Profile, Option C: Playwright Bundled Chromium Persistent Context (+10 more)

### Community 73 - "Resource Lock Model"
Cohesion: 0.12
Nodes (19): Conversation Agent Role, Emergency Stop, jarvis.db SQLite Single Source of Truth, .jarvispack Portable Identity Package, Memory Candidate Review Pipeline, Memory Curator Role, Memory Record Schema, Editable Personality Profile (+11 more)

### Community 74 - "ui/__init__.py"
Cohesion: 0.14
Nodes (13): QColor, QIcon, Enum, str, Tray state icons, drawn programmatically. Two reasons not to ship image files:…, PRD section 9.1 tray states., A non-colour distinguishing mark (PRD NFR-033)., Render the icon for a state. Colour *and* shape differ per state. (+5 more)

### Community 75 - "ToolRegistry"
Cohesion: 0.13
Nodes (9): Any, model_validator, Schema the planner sees. Free-form text can never reach the invoker., Everything a tool declares about itself., ToolSpec, JSON schemas the planner is offered. Nothing outside this list exists., Holds every tool the runtime may call. Nothing else can., ToolRegistry (+1 more)

### Community 76 - "Project Jarvis Implementation Backlog"
Cohesion: 0.12
Nodes (18): ARCHITECTURE.md, Subsystem area codes (CFG, COR, SEC, TSK, AUD, LLM, ...), Cross-phase invariants, DATA_MODEL.md, S/M/L/XL effort sizing (not time), Project Jarvis Implementation Backlog, Invariant: phase exit criteria must be demonstrated, Invariant: no generic execution primitive (+10 more)

### Community 77 - "Phase 0 — Foundation and safety architecture"
Cohesion: 0.15
Nodes (23): EventBridge, Invariant: state-changing tools declare reversibility metadata, JarvisCore, LockManager, P0-CFG-01 Layered typed configuration, P0-CFG-03 SQLite storage and versioned forward migrations, P0-COR-01 Typed event bus, P0-COR-02 Tool contract: ToolSpec with reversibility metadata (+15 more)

### Community 78 - "ListeningState"
Cohesion: 0.15
Nodes (9): ActivationRoute, CommandHeard, ListeningState, Enum, str, The voice loop (PRD sections 10.2 to 10.4, ADR-0027, ADR-0028). One place where…, One complete spoken command, ready for the planner., Joins the voice service to the shell (PRD FR-013, FR-016, FR-017, FR-018). The… (+1 more)

### Community 79 - "TtsProvider"
Cohesion: 0.11
Nodes (7): Protocol, Streams frames in, yields a wake event when the phrase is heard., Audio in, transcript out. Local by default (PRD FR-020)., Text in, audio out. Local by default (PRD FR-030)., SttProvider, TtsProvider, WakeDetector

### Community 80 - "RingBuffer"
Cohesion: 0.12
Nodes (8): datetime, Forget everything held. Called whenever listening stops., Everything ever accepted, so a test can prove discarding happened., A bounded, in-memory window of the most recent audio. Thread-safe: the capture…, Everything currently held, as one chunk. Does not clear the buffer., The held frames individually, for a consumer that wants to keep going., Snapshot and clear, for when a wake event promotes it to a command., RingBuffer

### Community 81 - "grounding.py"
Cohesion: 0.12
Nodes (14): GroundedClaim, GroundingReview, _hedge(), Enum, str, Where an answer came from, and what counts as done (PRD FR-047, FR-048). Two…, The verification value of a succeeded result; empty if it did not succeed., Replace an unverified success claim with what is actually known. (+6 more)

### Community 82 - "test_no_shell.py"
Cohesion: 0.20
Nodes (17): _findings(), parametrize, Path, The load-bearing security test (ADR-0003). Phase 0 exit criterion: *no generic…, No shipped module may start a process or evaluate generated code., ADR-0029 authorises one call site. A second is a new ADR, not a row here. This…, The allow-list entry must describe reality, not a module that moved., A guard on the guard: prove the detector is not vacuously passing. (+9 more)

### Community 83 - "test_prohibited_capabilities.py"
Cohesion: 0.14
Nodes (16): _Params, BaseModel, The prohibited-capability guard (ADR-0003, PRD sections 11.1 and 13.3)., No grant, setting or approval can reach past the prohibited check., PRD section 11.1's prohibited list is represented in the catalogue., In a fully wired runtime, nothing is registered against a prohibited class., _Result, test_catalogue_covers_every_prd_prohibited_class() (+8 more)

### Community 84 - "qwen3-embedding:0.6b Tentative Default"
Cohesion: 0.28
Nodes (9): Model Resource Scheduler (FR-039), Option A: Strict Mutual Exclusion Scheduling, Option B: VRAM-Budget-Aware Co-Residency, ADR-0017: Embedding Model, Option B: Dedicated Retrieval-Purpose-Built Embedding Model, Embedding Invocation Frequency Cost, Option C: First-Run Wizard Hardware Benchmark, qwen3-embedding:0.6b Tentative Default (+1 more)

### Community 85 - "GlobalHotkeys"
Cohesion: 0.14
Nodes (8): GlobalHotkeys, Registers hotkeys on a dedicated thread and dispatches their actions. Off…, Run the registration and message loop on its own thread., Invoke a binding's action directly. The test and menu route., The tray and the tests need a route that does not need a real keypress., test_a_binding_can_be_triggered_directly(), test_a_disabled_manager_registers_nothing_and_says_so(), test_starting_a_disabled_manager_is_a_no_op()

### Community 86 - "Architectural Drivers"
Cohesion: 0.23
Nodes (13): CI security-invariants job, Architectural Drivers, Architectural Change Control, Closed Capability Set (no generic execution primitive), Model Output Is Untrusted Input, tests/security/test_no_shell.py (AST scan of src/), Prohibited Tool Denylist (identity and pattern), Untrusted Content Enters as Delimited Observations (+5 more)

### Community 87 - "Extension Points Table"
Cohesion: 0.22
Nodes (9): Extension Points Table, Deferred Process Separation (TTS worker, elevation helper), audio.text_to_speech profiles, audio.wake_word settings, espeak-ng Pronunciation Backend, Kokoro bm_george (default TTS provider), Qwen3-TTS Expressive Provider (deferred), Wake Word Policy (Hey Jarvis now, Jarvis desired) (+1 more)

### Community 88 - "ADR-0003: A Closed Capability Set — No Generic Execution Primitive"
Cohesion: 0.15
Nodes (16): One SQLite Connection Per Thread, ADR-0003: A Closed Capability Set — No Generic Execution Primitive, No Generic Execution Primitive, os.startfile Named Future Allow-Listed Exception, tests/security/test_no_shell.py Source Tree Scan, Tool Registry Identity and Pattern Denylist, ADR-0004: Single Process, Thread Isolation for Phases 0–3, Layering Rule: Core Packages Must Not Import PySide6 (+8 more)

### Community 89 - "Subscription"
Cohesion: 0.14
Nodes (7): E, Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe., Receive ``event_type`` and every subclass of it., Subscription, EventBridge, QObject, Re-emits domain events as Qt signals on the GUI thread.

### Community 90 - "ValueError"
Cohesion: 0.13
Nodes (9): field_validator, model_validator, Append audio, discarding whatever falls out of the window., ModelRuntimeConfig, PrivacyConfig, TextToSpeechConfig, AuditLog, EventBus (+1 more)

### Community 91 - "media.py"
Cohesion: 0.23
Nodes (9): _INPUT, _INPUTUNION, _KEYBDINPUT, media_available(), Media and volume control (PRD FR-094, catalogue `media.playback_control`,…, Send one media or volume key. Returns whether Windows accepted it. ``action``…, send_media_key(), ToolContext (+1 more)

### Community 92 - "test_lazy_audio_imports.py"
Cohesion: 0.20
Nodes (15): _module_name(), _module_scope_imports(), parametrize, Path, Audio dependencies stay optional and lazily imported (ADR-0010, NFR-014).…, The property all of the above exists to protect., Imports at module level only — imports inside a function are the point., A guard on the guard: prove the detector is not vacuously passing. (+7 more)

### Community 93 - "Over-Permission (OP) category"
Cohesion: 0.18
Nodes (15): Approval dialog required fields, Capability risk classification (low/medium/high/prohibited), Permission decision types, Permission model, Prohibited capability class, Over-Permission (OP) category, Open question: detecting a spoofed window, T-023 Session grant exercised beyond the prompting request (+7 more)

### Community 94 - "service.py"
Cohesion: 0.18
Nodes (11): default_output_device(), playback_available(), playback_unavailable_reason(), Audio playback (PRD FR-030, FR-033, ADR-0028). The missing half of the voice…, The device index Windows would pick, or None if it cannot be read., _require_sounddevice(), The voice service: one object that owns the whole audio stack (L3). Built even…, What was synthesised, and what was actually played (PRD FR-048). Carries the… (+3 more)

### Community 95 - "T-052 Another local Windows user reads the SQLite vault"
Cohesion: 0.22
Nodes (10): Resource locks (jarvis.tasks.locks), Open question: hardening %LOCALAPPDATA% ACLs at startup, Other local Windows users, T-028 Two tasks race for the foreground desktop-control lock, T-030 Foreground lock not released after Automation Worker crash, T-034 Consequential action replayed after restart, T-052 Another local Windows user reads the SQLite vault, T-067 Clipboard capture records a password or TOTP code (+2 more)

### Community 96 - "contract.py"
Cohesion: 0.16
Nodes (12): Enum, str, The tool contract (PRD section 13.2). A *tool* is the only way the agent…, The invoker's typed answer. Success requires verification., True only when the tool ran *and* confirmed its effect., How an invocation ended. There is deliberately no boolean 'worked'., Whether the tool confirmed its own effect (PRD FR-048, AT-018)., Reversibility metadata (PRD FR-221). (+4 more)

### Community 97 - ".__init__"
Cohesion: 0.15
Nodes (12): AuditLog, EventBus, ApprovalPort, DenyingApprovalPort, LockLease, LockPort, Protocol, Return a lease, or ``None`` if the whole set could not be taken. (+4 more)

### Community 98 - "test_layering.py"
Cohesion: 0.26
Nodes (14): _imported_modules(), _module_name(), _package_of(), Path, Layering invariants (ARCHITECTURE.md section 5, ADR-0004). The rule that makes…, A fresh interpreter can import the whole engine with no Qt module loaded., Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.…, Spelled out separately because it is the invariant people break first. (+6 more)

### Community 99 - "single_instance.py"
Cohesion: 0.16
Nodes (12): ndarray, RuntimeError, AlreadyRunningError, _process_is_alive(), Single-instance enforcement (PRD FR-005). Only one interactive Jarvis may run…, Is a process with this id currently running? ``os.kill(pid, 0)`` is the POSIX…, Another instance already holds the single-instance handle., generate_voice_sample() (+4 more)

### Community 100 - "Residual risks accepted for Phase 0"
Cohesion: 0.40
Nodes (6): Dependency and licence scanning CI gate, Compromised or typosquatted Python dependency, Residual risks accepted for Phase 0, T-060 DLL search-order hijacking of the packaged build, T-069 Malicious or typosquatted PyPI dependency, TB-10 Jarvis to Windows OS security boundary

### Community 101 - "ApplicationCatalogue"
Cohesion: 0.22
Nodes (5): ApplicationCatalogue, ApplicationEntry, One application the user has approved Jarvis to open. Created by the user,…, The user's approved applications. Seeded, editable, never model-written., Find an entry by id, display name or alias. Never by path.

### Community 102 - "test_at014_private_session.py"
Cohesion: 0.18
Nodes (13): parametrize, AT-014 — a private session produces no permanent record after it ends. Asserted…, Everything the vault has written, as raw bytes., A control: prove the byte search would have found it if written., Privacy is not the same as invisibility: the event is auditable., test_a_normal_session_is_recorded_so_the_test_above_means_something(), test_a_private_conversation_is_marked_private_to_the_user(), test_a_private_session_leaves_no_record_anywhere() (+5 more)

### Community 103 - "Typed In-Process Event Bus (jarvis.core.events)"
Cohesion: 0.18
Nodes (11): CI dependency and licence review job, Emergency Stop, Typed In-Process Event Bus (jarvis.core.events), EventBridge (domain events to queued Qt signals), Honest Degraded UI (disabled, not hidden, not fake), Qt Main Thread Must Not Block, Jarvis Shell (jarvis.ui tray and main window), ui settings (tray start, show_unavailable_features, emergency hotkey) (+3 more)

### Community 104 - ".execute"
Cohesion: 0.19
Nodes (6): Connection, Cursor, Row, Any, Fold the WAL back into the main database file before shutdown., An exclusive write transaction. Nested use reuses the outer one.

### Community 105 - "On-Demand Narrowly Scoped Elevated Helper Process"
Cohesion: 0.22
Nodes (13): ADR-0001: Python-First Implementation with Rust Deferred, Python 3.11 + PySide6 Implementation Stack, Qwen3-TTS Isolated Python 3.12 Worker, Rust/Tauri Native Shell Deferred Past Phase 3, Authenticated Typed IPC for Future Shell, Process-Separation Promotion Triggers, Helper IPC Discipline (Named Pipe or Loopback, Rotating Token), No Interaction with the Windows Secure Desktop or UAC Prompt (+5 more)

### Community 106 - "SQLite (jarvis.db) Canonical Transactional Store"
Cohesion: 0.23
Nodes (13): ADR-0002: SQLite as the Single Source of Truth, Large Binary Artefacts Stored on Disk, Referenced by Path, Derived Rebuildable Stores Hold No Unique Information, SQLite (jarvis.db) Canonical Transactional Store, WAL Mode Concurrent Readers, ADR-0005: An In-Process Typed Event Bus, Bus Is Notification, Not System of Record, ADR-0006: Layered Configuration with Override-Only Persistence (+5 more)

### Community 107 - "Prompt Injection (PI) category"
Cohesion: 0.23
Nodes (13): Closed authority set for tool authorisation, Security Policy and Control Specification, Untrusted-data rule, The LLM as a confused deputy, Malicious web content author, Prompt Injection (PI) category, STRIDE threat classification, T-001 Web page text instructs Jarvis to act (+5 more)

### Community 108 - "Five-component process model"
Cohesion: 0.25
Nodes (8): Emergency stop surface, Local IPC requirements (loopback, per-install token), Non-admin by default, Five-component process model, Scoped elevation helper process, Secure desktop and UAC prompts off-limits, TTS worker isolation (Qwen3-TTS, separate env), T-053 Unauthenticated loopback port accepts local tool calls

### Community 109 - "test_runtime_primitives.py"
Cohesion: 0.19
Nodes (8): _CountingWorker, Single-instance guard, workers and schema migrations., test_a_worker_runs_off_the_calling_thread(), test_a_worker_stops_cooperatively(), test_duplicate_worker_names_are_refused(), test_every_phase_0_table_exists(), test_foreign_keys_and_wal_are_enabled(), test_the_statement_splitter_rejects_compound_blocks()

### Community 110 - "JarvisCore (composition root)"
Cohesion: 0.27
Nodes (12): CI headless self-check step (jarvis.main --check), Layered Configuration System (jarvis.config), extra=forbid Everywhere, JarvisCore (composition root), Override-Only Persistence, Only L5 May Import PySide6, Single-Instance Guard, VaultPaths (centralised path resolution) (+4 more)

### Community 111 - "Five-Suite Test Architecture"
Cohesion: 0.22
Nodes (10): QT_QPA_PLATFORM=offscreen in CI, CI test job (Windows + Ubuntu, Python 3.11/3.12), Capability Catalogue (risk classification as data), Six-Layer Dependency Model (L0-L5), tests/security/test_layering.py, Five-Suite Test Architecture, Tool Machinery in L2, Tool Implementations in L3, ToolSpec (tool contract) (+2 more)

### Community 112 - "Closed Enumerated Set of Narrow Typed Tools"
Cohesion: 0.21
Nodes (12): Closed Enumerated Set of Narrow Typed Tools, Emergent Capability From Tool Composition (Residual Risk), Hard Ceiling on Prompt Injection Impact, Sandboxed Generic Shell Rejected, ToolSpec Typed Tool Contract, Thread Isolation Is Not a Security Boundary (Gap 2), Ollama Endpoint Squatting (Unmitigated Residual Risk), Local Authenticating Proxy for Ollama Not Adopted (+4 more)

### Community 113 - "Capability Risk Classes"
Cohesion: 0.29
Nodes (12): Approval Dialog Design, Consequential-Action Audit Log, Capability Risk Classes, Executor Role, Jarvis Core (Orchestration), Password and Credential Field Protection, Planner Role, Prompt-Injection Defence (+4 more)

### Community 114 - "NetworkMode"
Cohesion: 0.17
Nodes (5): NetworkMode, Enum, str, _FakeResponse, Any

### Community 115 - "core.py"
Cohesion: 0.24
Nodes (9): CoreStatus, EmergencyStopReport, ``JarvisCore`` — the composition root (ARCHITECTURE.md section 6.9). Owns…, Exactly what was stopped (PRD section 11.3 requires telling the user)., Runtime composition (L4). Wires L1-L3 together; imports no GUI code., NotifyTool, Show a desktop notification through the tray., Register the six approved tools. Returns what was registered. ``speak`` and… (+1 more)

### Community 116 - "LLM Boundary (jarvis.llm)"
Cohesion: 0.15
Nodes (14): LLM Boundary (jarvis.llm), Loopback-Only Ollama Endpoint, Separate Model Roles (planner, vision, embeddings, STT, TTS), Offline Mode Enforced at the Adapter Boundary, Planner Cannot Skip the Invoker, system.health (the one registered Phase 0 tool), llm.ollama settings (loopback base_url, require_loopback), model_runtime (sequential load strategy) (+6 more)

### Community 117 - ".__init__"
Cohesion: 0.22
Nodes (6): AuditLog, DuplexCoordinator, RingBuffer, Path, Re-pin the model hubs after a network-mode change (AT-001)., VoiceActivityDetector

### Community 118 - "jarvis.core.events In-Process Publish/Subscribe Bus"
Cohesion: 0.20
Nodes (11): Versioned Forward-Only Migrations, Full ORM (SQLAlchemy) Rejected for Phase 0, Schema-Version Startup Check (Newer DB is Hard Failure), jarvis.core.events In-Process Publish/Subscribe Bus, Frozen Pydantic Event Models with Subclass Matching, Per-Handler Exception Isolation, ConfigChanged Runtime Event, pydantic extra="forbid" Loud Typo Failure (+3 more)

### Community 119 - "Option B: Per-Stream Retention Defaults with Expiry"
Cohesion: 0.19
Nodes (13): No Shared API Keys Constraint (§18.3), Option B: Optional User-Supplied Search API Key, Portable Identity Export (FR-168), Secret Exclusion from Normal Exports (FR-169/FR-170), Audit Log as a Safety Record, Clipboard History Retention (FR-253), Option C: One Global Retention Period, Option A: Keep Everything Until User Deletes (+5 more)

### Community 120 - "OllamaHealth"
Cohesion: 0.20
Nodes (8): is_loopback_url(), OllamaHealth, True when the URL's host is a loopback address or resolves only to one., The result of one check. Never claims health it did not observe., Ollama adapter. Phase 0 implements only the health check., parametrize, test_loopback_urls_are_recognised(), test_non_loopback_urls_are_rejected()

### Community 121 - "startup.py"
Cohesion: 0.36
Nodes (10): available(), describe(), is_enabled(), Start at sign-in (PRD FR-002). Uses the per-user…, Only Windows has the Run key this uses., The command Windows would run at sign-in. ``pythonw.exe`` rather than…, Add or remove the sign-in entry. Never requires administrator rights., set_enabled() (+2 more)

### Community 122 - "ConfigStore"
Cohesion: 0.22
Nodes (8): ApprovalPort, ConfigStore, SingleInstanceGuard, default_log_path(), Path, VaultPaths, test_exit_3_a_second_instance_is_refused(), test_the_task_state_machine_is_persistent()

### Community 123 - "task table"
Cohesion: 0.31
Nodes (10): Crash Recovery, Ten-State Task Machine (jarvis.tasks.states), Task Store (jarvis.tasks.store), ToolResult (typed outcomes), Success Requires Verification, task_checkpoint table, task_evidence table, task table (+2 more)

### Community 124 - "main"
Cohesion: 0.20
Nodes (10): ArgumentParser, build_parser(), main(), VaultPaths, _uninstall_wake_model(), An honest report of an unreachable runtime is a successful self-check. Settled…, Phase 1 state must be visible from the headless self-check., test_check_reports_the_voice_stack_and_secret_store() (+2 more)

### Community 125 - "Phase 2 — Deterministic desktop and browser automation"
Cohesion: 0.20
Nodes (14): P1-APP-01 Application launcher with launch verification, P2-BRW-01 Dedicated persistent Jarvis Brave profile, P2-BRW-02 Playwright visible-browser, DOM-first execution, P2-BRW-08 YouTube search and indexed result selection, P2-FS-01 Windows Known Folder resolution, P2-FS-06 Filesystem scoping and path validation, P2-WIN-02 UI Automation inspector, P2-WIN-04 Input ownership via foreground_desktop lock (+6 more)

### Community 126 - "Option B: Self-Signed Developer Keys"
Cohesion: 0.36
Nodes (8): Option C: Project-Operated Signing Authority, Option B: Self-Signed Developer Keys, Skill Manifest signed Field, Option B: EV Certificate with Optional Automatic Checks, Option A: OV Certificate with Manual Update Checks, Signature Verification Precedes Execution, SmartScreen Reputation Barrier, Update Package Format and Manifest Schema

### Community 127 - ".__init__"
Cohesion: 0.20
Nodes (4): GlobalHotkeys, Connect the voice service to the Voice screen and to push-to-talk., Derive the tray state from what the runtime is actually doing., Emergency stop and push-to-talk, both configurable. Hotkey callbacks arrive on…

### Community 128 - "Phase 0 security status table"
Cohesion: 0.24
Nodes (10): Approval port (deny by default), Layering enforcement test (no Qt below presentation), Ollama health check (loopback-only), Phase 0 security status table, Tool invoker six-step pipeline (jarvis.core.tools.invoker), Typed event bus (jarvis.core.events), Hallucinated Success (HS) category, Open question: authenticating the Ollama endpoint (+2 more)

### Community 129 - "Root-scoped filesystem tools"
Cohesion: 0.27
Nodes (10): Archive extraction protections, Absolutely denied filesystem targets, Root-scoped filesystem tools, Path canonicalisation before scope check, Phase-gated mitigation roadmap, T-038 Path traversal escapes the approved root scope, T-039 Symlink or NTFS junction escapes approved scope, T-040 TOCTOU path swap after scope validation (+2 more)

### Community 130 - "Tool-invocation evaluation order"
Cohesion: 0.31
Nodes (10): Tool-invocation evaluation order, Static src/ scan for prohibited primitives, Named prohibited broad tools, Tool registry registration denylist, T-010 Self-injection via Jarvis's own prior output, T-011 Model invents a nonexistent tool name, T-012 Model requests a shell/code-execution tool, T-014 Valid tool call with out-of-scope parameters (+2 more)

### Community 131 - "assert_transition"
Cohesion: 0.27
Nodes (10): assert_transition(), can_transition(), InvalidTransitionError, Exception, An attempt was made to move a task between incompatible states., parametrize, The most dangerous illegal transition gets its own test., test_a_task_cannot_be_marked_succeeded_without_running() (+2 more)

### Community 132 - ".set_setting"
Cohesion: 0.25
Nodes (5): Any, ConversationEngine, AppConfig, NetworkMode, Change a setting, persist the override and announce it.

### Community 133 - "Redaction Before Serialisation"
Cohesion: 0.43
Nodes (7): Dual-Sink Append-Only Audit Log (jarvis.core.audit), Redaction Before Serialisation, logging settings (audit_to_sqlite, max_audit_value_chars), audit_event table, Export and Import Constraints, Ten Persisted Integrity Invariants, Two Audit Sinks, One Record of Truth

### Community 134 - "ToolInvoker (six-step pipeline)"
Cohesion: 0.19
Nodes (14): ApprovalPort, Bounded Timeouts and Declared Retry Policy, DenyingApprovalPort (silence is never consent), Grant Scopes (ONCE, SESSION, TASK, APPLICATION, FOLDER, ALWAYS), In-Process Isolation Is Not a Security Boundary, Permission Engine (jarvis.core.permissions), Single-Process Multi-Thread Model, Single Choke Point for Tool Execution (+6 more)

### Community 135 - "Phase 1 — Voice-first local assistant"
Cohesion: 0.16
Nodes (18): ADR-0001 Python-first shell (native Rust/Tauri deferred), ADR-0009 Scoped elevation helper interface, Deferred beyond Version 1, P1-AUD-01 Wake-word detection (openWakeWord), P1-AUD-05 Local STT (faster-whisper), P1-AUD-07 Local TTS (Kokoro), P1-AUD-10 Expressive TTS worker isolation prototype (Qwen3-TTS), P1-SEC-02 DPAPI-backed secret store (+10 more)

### Community 136 - "Automation Worker"
Cohesion: 0.22
Nodes (9): TaskScheduler, Automation Worker, Dedicated Jarvis Brave Profile, Foreground Desktop-Control Lock, Playwright Browser Automation Layer, Explicit Search Modes, Visible Browser Search, Jarvis Core (orchestration, permissions, audit) (+1 more)

### Community 137 - "Phased Delivery Plan (Phase 0-6)"
Cohesion: 0.25
Nodes (9): Google Antigravity IDE Adapter, Phased Delivery Plan (Phase 0-6), Filesystem Tool Root Scoping, IDE-Agent Orchestration, Windows Known Folder Resolution, Product Non-Goals, Prohibited Broad Tools, Safe Jarvis Workspace (+1 more)

### Community 138 - "Local Wake Phrase Detection"
Cohesion: 0.28
Nodes (9): Audio Worker, English-Only Language Policy, faster-whisper STT Engine, Local Speech-to-Text, Local Text-to-Speech, openWakeWord Model Runtime, Privacy-Preserving Audio Ring Buffer, Push-to-Talk Hotkey (+1 more)

### Community 139 - "Jarvis Shell (GUI Process)"
Cohesion: 0.31
Nodes (9): Jarvis Shell (GUI Process), Kokoro TTS Provider, Authenticated Loopback IPC, Piper TTS Provider, PySide6 Desktop Shell Toolkit, Python 3.11 as V1 Implementation Language, Qwen3-TTS Expressive Provider, Provider-Neutral TTS Interface (+1 more)

### Community 140 - "hotkeys.py"
Cohesion: 0.22
Nodes (7): available(), Hotkey, HotkeyError, Global hotkeys (PRD section 11.3, FR-018, ADR-0027). Two hotkeys exist in Phase…, A hotkey string could not be understood., Global hotkeys are a Windows facility in this build., A parsed combination, ready for ``RegisterHotKey``.

### Community 141 - "Path"
Cohesion: 0.22
Nodes (9): parametrize, Path, Screenshot-based computer control is still out of scope. Phase 1 legitimately…, No autonomous self-modification: every write path targets the vault., PRD section 25 lists sixteen open decisions., test_an_adr_exists_for_every_prd_open_decision(), test_no_screenshot_or_input_automation_module_exists(), test_required_documents_and_config_exist() (+1 more)

### Community 142 - "test_no_elevation.py"
Cohesion: 0.31
Nodes (6): Path, Non-administrator operation (PRD FR-003, NFR-020, ADR-0009). Phase 0 must run…, Any packaging manifest must be asInvoker., _relative(), test_no_manifest_declares_an_elevated_execution_level(), test_no_module_requests_elevation()

### Community 143 - "MSIX Sandboxing vs Desktop Automation Tension"
Cohesion: 0.32
Nodes (8): espeak-ng GPL-Family Licensing Consideration, ADR-0020: Plugin and Skill Signing, ADR-0022: MSIX Distribution, Option A: MSIX as Primary Distribution Format, Option B: MSIX as Secondary Optional Channel, MSIX Sandboxing vs Desktop Automation Tension, Automation Worker Adversarial Input Exposure, ADR-0026: Code-Signing and Update Infrastructure

### Community 144 - "Voice Pack Redistribution Licensing Gap"
Cohesion: 0.29
Nodes (8): Per-Download Provider and Licence Disclosure, Voice Pack Redistribution Licensing Gap, ADR-0016: Custom Jarvis Wake Word, Option A: Purpose-Trained Custom Jarvis Wake Model, False-Activation Evaluation Harness, Hey Jarvis Interim Wake Phrase, Push-to-Talk Global Hotkey Fallback, Expired Screenshot Evidence Must Degrade Honestly

### Community 145 - "configure_logging"
Cohesion: 0.29
Nodes (6): Logger, Diagnostics: application logging and, later, crash reporting., configure_logging(), Path, Structured application logging. Separate from the audit log. The audit log…, Configure the root logger once. Idempotent.

### Community 146 - "T-048 Secrets leak into audit log, crash dump, or telemetry"
Cohesion: 0.18
Nodes (11): Audit log requirements (append-only, redacted), .jarvispack normal-export secret exclusions, Deletion is non-destructive by default, Screen capture scoping and screenshot retention, Secrets storage via DPAPI / Credential Manager, Signed installers and update packages, Telemetry off by default with content exclusions, T-048 Secrets leak into audit log, crash dump, or telemetry (+3 more)

### Community 147 - "Resource Locks (jarvis.tasks.locks)"
Cohesion: 0.25
Nodes (8): Concurrency Invariants, Resource Locks (jarvis.tasks.locks), SQLite Concurrency Strategy (WAL, per-thread connections), Forward-Only Transactional Migrations, resource_lock table, runtime_instance table, schema_migration table, SQLite Is the Single Source of Truth

### Community 148 - "P0-SEC-03 Permission engine"
Cohesion: 0.38
Nodes (7): P0-SEC-03 Permission engine, P2-BRW-06 Untrusted web-content wrapping and prompt-injection test, P5-IDE-05 IDE permission boundary (no automatic approval), P5-IDE-08 No hidden shell delegation (adversarial test), PermissionEngine, Phase 5 — IDE orchestration, tests/security/test_prompt_injection.py

### Community 149 - "Phase 3 — Tasks, macros, and memory"
Cohesion: 0.43
Nodes (7): P2-WIN-03 Automation worker thread (pywinauto UIA backend), P3-CLP-01 Clipboard permissions and operations, P3-MEM-01 Memory candidate pipeline with review queue and provenance, P3-MEM-03 Forget with cascade delete from derived indexes, P3-MEM-06 Portable identity export/import (.jarvispack) with secret exclusion, P3-TSK-02 Pause/resume with mandatory state re-observation, Phase 3 — Tasks, macros, and memory

### Community 150 - "ADR-0008: Secret Storage Deferred to Phase 1"
Cohesion: 0.38
Nodes (7): ADR-0008: Secret Storage Deferred to Phase 1, jarvis.core.audit.redaction Defence-in-Depth Backstop, Windows Credential Manager CredWrite/CredRead (Candidate Mechanism), DPAPI CryptProtectData via ctypes (Candidate Mechanism), Encrypted SQLite Table with DPAPI-Wrapped Key (Candidate Mechanism), No Secret Store Implemented in Phase 0, Secrets Excluded From Normal Exports

### Community 151 - "ADR-0013: Installer Technology"
Cohesion: 0.29
Nodes (7): No Elevation Manifest Security Check (asInvoker), Application Never Runs Permanently as Administrator, ADR-0013: Installer Technology, Installer Choice Sequenced Behind the MSIX Decision, NSIS (Candidate Installer), Per-User Install with No UAC Elevation, WiX Toolset MSI (Candidate Installer)

### Community 152 - "Never Claim Unverified Success"
Cohesion: 0.29
Nodes (7): Never Claim Unverified Success, Programmatically Drawn QPainter Tray Icons, ADR-0011: Public Product Name, "Jarvis" as Internal Codename Only, public_product_name Configuration Value, Rename Before Public Release (Leaning Option), Trademark and Identifier Availability Criteria

### Community 153 - "._on_event"
Cohesion: 0.29
Nodes (3): Event, Runs on the Qt main thread, courtesy of the bridge., Answered from the Permissions screen rather than the panel.

### Community 154 - "First-Run Onboarding Wizard"
Cohesion: 0.38
Nodes (7): First-Run Onboarding Wizard, Model Resource Scheduler (VRAM Arbitration), Per-Role Model Routing, Ollama Local Model Runtime, qwen3:8b Planner/Conversation Model, qwen3-vl Vision Model Route, Signed Windows Installer and Updates

### Community 155 - "Arc Reactor Visual Motif"
Cohesion: 0.52
Nodes (7): Jarvis Application Icon (Arc Reactor Mark), Arc Reactor Visual Motif, Circular Metallic Chassis Ring, Cyan-on-White Emissive Palette, Jarvis Product Brand Identity, Transparent Alpha Square Canvas, Inverted Triangular Glowing Core

### Community 156 - "_read_yaml_mapping"
Cohesion: 0.33
Nodes (4): _atomic_write(), Path, Write via a temporary file in the same directory, then replace. A crash mid-…, _read_yaml_mapping()

### Community 157 - "HotkeyBinding"
Cohesion: 0.33
Nodes (4): HotkeyBinding, One requested hotkey and what actually became of it., Declare a hotkey. Parsing happens now; registration happens at start., Hotkeys the user asked for that are not actually working.

### Community 158 - "Any"
Cohesion: 0.29
Nodes (3): Any, Persist a resume point (PRD FR-128)., Record support for a completion claim (PRD FR-132).

### Community 159 - "ConversationWorker"
Cohesion: 0.29
Nodes (4): ConversationWorker, QObject, QWidget, Runs one turn off the UI thread. The model call is slow and blocking.

### Community 160 - "Option A: Local Backup Only, No Network Transport"
Cohesion: 0.33
Nodes (7): Rebuildable Derived Index Constraint, ADR-0021: Encrypted Sync and Backup, Option A: Local Backup Only, No Network Transport, Off-Device Backup Compromise Surface, Option B: User-Supplied Cloud Storage with Client-Side Encryption, ADR-0024: Data Retention Defaults, Cascade Deletion of Derived Data (FR-167)

### Community 161 - "DenyingApprovalPort Default Implementation"
Cohesion: 0.33
Nodes (6): ADR-0007: Ollama Loopback-Only Trust Boundary, Loopback-Only Base URL Enforcement at the Adapter, Offline Mode Enforced at the Adapter Boundary, DenyingApprovalPort Default Implementation, Inno Setup (Candidate Installer), Uninstall-Time Data Deletion Must Be Opt-In

### Community 162 - "ADR-0014: Default English Voice"
Cohesion: 0.39
Nodes (8): ADR-0014: Default English Voice, Kokoro bm_george Default Voice, Windows SAPI Emergency Fallback, ADR-0015: Additional TTS Providers, No Silent Voice Provider Switching (FR-036), Qwen3-TTS Isolated Python 3.12 Worker, Provider-Neutral TtsProvider Interface, Update Rollback and Schema Compatibility Checks

### Community 163 - "strip_wake_phrase"
Cohesion: 0.33
Nodes (6): Remove a leading wake phrase (PRD FR-024). Only from the start, and only once.…, strip_wake_phrase(), parametrize, Remind me to say hey Jarvis" is a command, not two wakes., test_only_the_leading_wake_phrase_is_stripped(), test_the_wake_phrase_is_stripped_from_the_command()

### Community 164 - "redact_for_speech"
Cohesion: 0.33
Nodes (6): Replace anything secret-shaped with a description of what it was., redact_for_speech(), parametrize, FR-034: speaking a password is not recoverable by apologising., test_ordinary_text_is_spoken_unchanged(), test_sensitive_text_is_never_spoken_aloud()

### Community 168 - "test_whisper.py"
Cohesion: 0.70
Nodes (4): list_audio_devices(), main(), record_audio(), transcribe_audio()

### Community 169 - "Retention and Deletion Rules"
Cohesion: 0.67
Nodes (4): privacy retention defaults, Retention and Deletion Rules, Soft References So Audit Survives Its Subject, Privacy Defaults (telemetry off, no raw audio)

### Community 170 - "test_enabling_then_disabling_leaves_no_entry"
Cohesion: 0.50
Nodes (4): WINDOWS_ONLY, Runs against the real per-user Run key, and cleans up after itself., test_enabling_then_disabling_leaves_no_entry(), test_the_startup_command_points_at_an_interpreter_that_exists()

### Community 172 - "vault_free_bytes"
Cohesion: 0.67
Nodes (3): Path, Free space on the volume holding the vault (PRD NFR-006)., vault_free_bytes()

### Community 173 - "fake_ollama"
Cohesion: 0.67
Nodes (3): fake_ollama(), fixture, Replace urlopen so no test ever touches a real socket.

### Community 174 - "fake_sounddevice"
Cohesion: 0.67
Nodes (3): fake_sounddevice(), fixture, Stand in for the real library so no device is opened.

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
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `T-030 Foreground lock not released after Automation Worker crash` and `T-034 Consequential action replayed after restart`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Arc Reactor Visual Motif` and `Cyan-on-White Emissive Palette`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `"Jarvis" as Internal Codename Only` and `ADR-0012: Shell Technology for the First Public Build`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `JarvisCore` connect `JarvisCore` to `test_core_lifecycle.py`, `EventBus`, `.set_setting`, `ApplicationCatalogue`, `test_at014_private_session.py`, `MainWindow`, `_PermissionsPanel`, `AppConfig`, `Path`, `VoiceService`, `core.py`, `JarvisApplication`, `test_phase0_exit_criteria.py`, `ConfigStore`, `main`, `model_directory`, `.__init__`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `ToolCall`, `.__init__`, `TaskStore`, `EventBus`, `JarvisCore`, `test_core_lifecycle.py`, `ResourceLockManager`, `AuditLog`, `.execute`, `ConversationStore`, `test_runtime_primitives.py`, `types.py`, `PersonalityStore`, `locks.py`, `llm/conversation.py`, `PermissionEngine`, `tasks/__init__.py`, `Conversation`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `JarvisApplication` connect `JarvisApplication` to `ConversationWorker`, `test_voice_wiring.py`, `JarvisCore`, `.quit`, `MainWindow`, `ui/__init__.py`, `VoiceController`, `test_conversation_wiring.py`, `test_phase0_exit_criteria.py`, `._on_event`, `main`, `model_directory`, `.__init__`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `JarvisCore` (e.g. with `VoiceService` and `ApplicationCatalogue`) actually correct?**
  _`JarvisCore` has 10 INFERRED edges - model-reasoned connections that need verification._