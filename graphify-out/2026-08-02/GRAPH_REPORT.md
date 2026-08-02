# Graph Report - .  (2026-08-02)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 2987 nodes · 6387 edges · 154 communities (141 shown, 13 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 775 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `54c4d08b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ToolCall
- TaskState
- tools/__init__.py
- DuplexCoordinator
- TaskScheduler
- VoicePipeline
- WakeEvent
- AuditLog
- AudioUnavailable
- AppConfig
- ResourceLockManager
- test_runtime_primitives.py
- JarvisTrayIcon
- Database
- PermissionEngine
- VoiceService
- AudioChunk
- test_ollama_tool_calling.py
- test_grounding_and_history.py
- core.py
- test_config.py
- approvals.py
- test_tasks.py
- Worker
- JarvisApplication
- MainWindow
- describe_voice_stack
- ApprovalQueue
- JarvisCore
- service.py
- test_permission_engine.py
- redact
- ConversationStore
- ApprovalPanel
- test_phase0_exit_criteria.py
- RingBuffer
- OllamaChatProvider
- ConversationPanel
- test_secret_store.py
- personality.py
- conftest.py
- EventBus
- VaultPaths
- schema.py
- Conversation
- permissions/models.py
- llm/conversation.py
- test_hotkeys_and_startup.py
- test_core_lifecycle.py
- ModelRouter
- GlobalHotkeys
- main_window.py
- ApprovalRequest
- Project Jarvis (Windows Local AI Desktop Agent)
- tests/security/test_no_shell.py (AST scan of src/)
- Resource Lock Model
- pipeline.py
- OllamaHealthChecker
- VoicePanel
- Project Jarvis Implementation Backlog
- Phase 0 — Foundation and safety architecture
- Dedicated Jarvis Brave Profile
- Subscription
- Resource Locks (jarvis.tasks.locks)
- ui/__init__.py
- ProhibitedToolError
- SourceLabel
- test_lazy_audio_imports.py
- test_prohibited_capabilities.py
- Over-Permission (OP) category
- test_layering.py
- Task Scheduler (jarvis.tasks.scheduler)
- LLM Boundary (jarvis.llm)
- ADR-0003: A Closed Capability Set — No Generic Execution Primitive
- NetworkMode
- test_at014_private_session.py
- test_no_shell.py
- On-Demand Narrowly Scoped Elevated Helper Process
- SQLite (jarvis.db) Canonical Transactional Store
- jarvis.core.events In-Process Publish/Subscribe Bus
- No Shared API Keys Constraint (§18.3)
- .__init__
- Prompt Injection (PI) category
- tools/ports.py
- main
- Closed Enumerated Set of Narrow Typed Tools
- Capability Risk Classes
- WakeDetector
- T-048 Secrets leak into audit log, crash dump, or telemetry
- offerable_scopes_for
- startup.py
- task table
- Phase 2 — Deterministic desktop and browser automation
- Phase 0 security status table
- Root-scoped filesystem tools
- Tool-invocation evaluation order
- T-052 Another local Windows user reads the SQLite vault
- Emergency Stop
- JarvisCore (composition root)
- ToolInvoker (six-step pipeline)
- .__init__
- Phase 1 — Voice-first local assistant
- Automation Worker
- qwen3-embedding:0.6b Tentative Default
- Phased Delivery Plan (Phase 0-6)
- Local Wake Phrase Detection
- Jarvis Shell (GUI Process)
- denial_options_for
- is_loopback_url
- hotkeys.py
- Path
- test_no_elevation.py
- ADR-0014: Default English Voice
- MSIX Sandboxing vs Desktop Automation Tension
- Voice Pack Redistribution Licensing Gap
- Option B: Self-Signed Developer Keys
- configure_logging
- generate_voice_sample
- Five-component process model
- PermissionEvaluation
- Redaction Before Serialisation
- Architectural Drivers
- P0-SEC-03 Permission engine
- Phase 3 — Tasks, macros, and memory
- ADR-0008: Secret Storage Deferred to Phase 1
- ADR-0013: Installer Technology
- Never Claim Unverified Success
- Option B: Per-Stream Retention Defaults with Expiry
- First-Run Onboarding Wizard
- Arc Reactor Visual Motif
- _escape
- ConversationWorker
- DenyingApprovalPort Default Implementation
- Residual risks accepted for Phase 0
- _FakeResponse
- ModelRuntimeConfig
- .__init__
- test_whisper.py
- Retention and Deletion Rules
- ._supported_schema_version
- GroundingReview
- .send_message
- test_enabling_then_disabling_leaves_no_entry
- test_high_risk_cannot_be_allowed_beyond_a_single_use
- core/__init__.py
- llm/__init__.py
- .set_availability
- T-019 Mis-transcribed command causes destructive action
- UUID4 Hex Identifiers (jarvis.common.new_id)
- project-jarvis
- QWidget
- model_validator
- Exception

## God Nodes (most connected - your core abstractions)
1. `JarvisCore` - 100 edges
2. `Database` - 76 edges
3. `AudioChunk` - 71 edges
4. `ToolCall` - 65 edges
5. `EventBus` - 63 edges
6. `AuditLog` - 57 edges
7. `ApprovalQueue` - 48 edges
8. `MainWindow` - 47 edges
9. `ToolInvoker` - 46 edges
10. `JarvisApplication` - 46 edges

## Surprising Connections (you probably didn't know these)
- `Export and Import Constraints` --semantically_similar_to--> `Redaction Before Serialisation`  [INFERRED] [semantically similar]
  DATA_MODEL.md → ARCHITECTURE.md
- `Concurrency Invariants` --semantically_similar_to--> `SQLite Concurrency Strategy (WAL, per-thread connections)`  [INFERRED] [semantically similar]
  ARCHITECTURE.md → DATA_MODEL.md
- `Rust Deferred Until After Phase 3` --conceptually_related_to--> `Only L5 May Import PySide6`  [INFERRED]
  PROJECT_INPUTS.md → ARCHITECTURE.md
- `DenyingApprovalPort (silence is never consent)` --semantically_similar_to--> `permission_grant table`  [INFERRED] [semantically similar]
  ARCHITECTURE.md → DATA_MODEL.md
- `Entities Defined But Not Yet Built` --semantically_similar_to--> `Honest Degraded UI (disabled, not hidden, not fake)`  [INFERRED] [semantically similar]
  DATA_MODEL.md → ARCHITECTURE.md

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

## Communities (154 total, 13 thin omitted)

### Community 0 - "ToolCall"
Cohesion: 0.06
Nodes (70): AuditCategory, RetryPolicy, Any, AuditLog, BaseModel, EventBus, RiskLevel, Verification (+62 more)

### Community 1 - "TaskState"
Cohesion: 0.06
Nodes (58): LookupError, from_iso(), json_dumps(), json_loads(), new_id(), Any, datetime, Small shared primitives used across every layer. Kept deliberately tiny:… (+50 more)

### Community 2 - "tools/__init__.py"
Cohesion: 0.06
Nodes (54): ToolRegistered, Any, BaseModel, Enum, Exception, model_validator, Protocol, str (+46 more)

### Community 3 - "DuplexCoordinator"
Cohesion: 0.04
Nodes (55): BargeInReport, DuplexCoordinator, DuplexMode, PlaybackWindow, datetime, Enum, str, Full-duplex audio and barge-in (ADR-0028, PRD FR-015, section 11.3). ADR-0028… (+47 more)

### Community 4 - "TaskScheduler"
Cohesion: 0.05
Nodes (35): Any, BaseModel, Enum, Protocol, str, What a task actually does. Runners are the extension point that later phases…, Persist a resume point (PRD FR-128)., Record support for a completion claim (PRD FR-132). (+27 more)

### Community 5 - "VoicePipeline"
Cohesion: 0.09
Nodes (28): Begin waiting for the wake phrase, if enrolment allows it., Stop, and forget everything held. Nothing survives in memory., F9 pressed. Capture a command without a wake phrase (FR-018)., Only ever enabled after enrolment has been measured (ADR-0016)., Capture in, commands out. Owns the listening state machine., VoicePipeline, FakeStt, FakeWake (+20 more)

### Community 6 - "WakeEvent"
Cohesion: 0.06
Nodes (25): AudioFormat, str, The wake phrase was detected., WakeEvent, build_wake_detector(), choose_threshold(), EnrolmentMeasurement, EnrolmentResult (+17 more)

### Community 7 - "AuditLog"
Cohesion: 0.08
Nodes (33): Audit logging and secret redaction., AuditLog, Any, datetime, Path, Append-only audit log with two sinks (ARCHITECTURE.md section 6.3). *…, Every record from the JSONL file, oldest first., Search the SQLite index. Falls back to the JSONL file if unavailable. (+25 more)

### Community 8 - "AudioUnavailable"
Cohesion: 0.07
Nodes (27): AudioUnavailable, Enum, RuntimeError, Audio provider boundaries (ARCHITECTURE.md section 8, PRD sections 10.2-10.4).…, A selectable voice, with the licence metadata FR-032 requires., Text in, audio out. Local by default (PRD FR-030)., An audio component cannot run, and says which and why., SynthesisResult (+19 more)

### Community 9 - "AppConfig"
Cohesion: 0.09
Nodes (29): Configuration layer (L1). Must not import anything above L1., AppConfig, The whole validated configuration tree., _atomic_write(), ConfigError, ConfigStore, deep_merge(), _delete_by_path() (+21 more)

### Community 10 - "ResourceLockManager"
Cohesion: 0.07
Nodes (29): LockAcquired, LockContended, LockReleased, StaleLockReclaimed, _Contended, LockSetLease, Exception, Resource locks (PRD FR-124, section 7.1). Only one task may hold a given named… (+21 more)

### Community 11 - "test_runtime_primitives.py"
Cohesion: 0.07
Nodes (28): AlreadyRunningError, _process_is_alive(), BaseException, Path, Single-instance enforcement (PRD FR-005). Only one interactive Jarvis may run…, Remove a lock file whose owning process is gone., Is a process with this id currently running? ``os.kill(pid, 0)`` is the POSIX…, Another instance already holds the single-instance handle. (+20 more)

### Community 12 - "JarvisTrayIcon"
Cohesion: 0.06
Nodes (30): ActivationReason, JarvisTrayIcon, System tray icon and menu (PRD sections 9.1 and 9.2). Menu entries whose…, Enable the keyboard route and say how many are waiting., Tray presence, state indication and quick controls., TaskState, test_the_tray_offers_a_keyboard_route_only_when_something_waits(), fixture (+22 more)

### Community 13 - "Database"
Cohesion: 0.08
Nodes (27): Connection, Cursor, Exception, Row, Database, DatabaseError, Any, Path (+19 more)

### Community 14 - "PermissionEngine"
Cohesion: 0.10
Nodes (26): PermissionEvaluation, PermissionGrant, PermissionRequest, PermissionEvaluated, PermissionGranted, PermissionRevoked, ProhibitedCapabilityBlocked, A prohibited tool or capability was requested. Always a security signal. (+18 more)

### Community 15 - "VoiceService"
Cohesion: 0.07
Nodes (15): No enrolment has been run in this build, so nothing has passed., Open the microphone. Returns False, honestly, if it cannot., Measure the room and apply the threshold (PRD FR-017)., Synthesise and hand back audio. Playback is the shell's job., Owns the providers, the pipeline and the capture session., VoiceService, NoiseCalibration, Enum (+7 more)

### Community 16 - "AudioChunk"
Cohesion: 0.09
Nodes (16): AudioChunk, A block of mono audio. ``samples`` is raw bytes, never a file path., TranscriptSegment, build_stt_provider(), diagnostic_audio_path(), FasterWhisperSttProvider, NullSttProvider, Path (+8 more)

### Community 17 - "test_ollama_tool_calling.py"
Cohesion: 0.10
Nodes (33): ConversationEngine, Runs one turn: prompt, model, tools, grounding, reply., ChatResponse, What a provider returned. ``text`` is for the user. ``tool_calls`` is for the…, _decode(), echo_invoker(), EchoParams, EchoResult (+25 more)

### Community 18 - "test_grounding_and_history.py"
Cohesion: 0.08
Nodes (37): claims_completion(), Whether a reply asserts that something was done., Label a reply and stop it claiming an unverified success. ``tool_results`` are…, review_response(), PersonalityStore, AuditLog, The active profile, and proposals awaiting the user's decision., parametrize (+29 more)

### Community 19 - "core.py"
Cohesion: 0.12
Nodes (29): Deliver to every matching handler. Returns the number invoked. Handler…, ApprovalRequested, ApprovalResolved, AppStarted, AppStopping, ConfigChanged, EmergencyStopCompleted, EmergencyStopRequested (+21 more)

### Community 20 - "test_config.py"
Cohesion: 0.07
Nodes (24): PathLike, expand_path(), find_defaults_config(), _platform_default_root(), Data-vault path resolution. This is the *only* module permitted to expand…, Locate the shipped ``defaults.yaml``. Order: ``JARVIS_DEFAULTS_CONFIG`` env…, Expand ``%VARS%``, ``$VARS`` and ``~`` then normalise to an absolute path., Project Jarvis — local-first Windows desktop AI agent. "Jarvis" is an internal… (+16 more)

### Community 21 - "approvals.py"
Cohesion: 0.08
Nodes (18): PendingApproval, The approval queue — step 5 of the invoker pipeline, made answerable. ADR-0027…, One unanswered request. Mutable, unlike everything on the event bus., BaseModel, A "don't ask again" choice offered alongside Deny (ADR-0027)., RememberDenialOption, ApprovalController, Decision (+10 more)

### Community 22 - "test_tasks.py"
Cohesion: 0.10
Nodes (32): CRUD plus a validated state machine over the ``task`` tables., TaskStore, Task state machine, durable store, locks and scheduler (PRD FR-120 .. FR-133)., PRD section 7.1 and AT-009: one runs, the other stays queued., A finished task is finished; a repeat is a new task., PRD FR-133 and NFR-012., The most dangerous illegal transition gets its own test., RecordingRunner (+24 more)

### Community 23 - "Worker"
Cohesion: 0.08
Nodes (16): ABC, WorkerStateChanged, PeriodicWorker, BaseException, Worker threads and their supervisor (PRD NFR-003, ARCHITECTURE.md section 4.1).…, Calls a function on an interval until stopped., Starts and stops workers in a defined order., Stop in reverse order. Returns the names that stopped cleanly. (+8 more)

### Community 24 - "JarvisApplication"
Cohesion: 0.08
Nodes (10): JarvisApplication, QObject, Runs on the Qt main thread, courtesy of the bridge., The keyboard route to a waiting request (PRD NFR-030)., Answered from the Permissions screen rather than the panel., Derive the tray state from what the runtime is actually doing., Switching mid-conversation ends the current one (PRD FR-046)., Emergency stop and push-to-talk, both configurable. Hotkey callbacks arrive on… (+2 more)

### Community 25 - "MainWindow"
Cohesion: 0.10
Nodes (13): QMainWindow, MainWindow, Navigation shell over live core state., Closing the window leaves Jarvis running in the tray (PRD FR-001)., test_the_window_says_plainly_when_nothing_is_waiting(), No placeholder screen may look like it works (ADR-0010, PRD section 1.10)., Phase 1 adds Conversation and Voice. Everything else still names its phase., PRD FR-001: Jarvis stays functional when the main window is closed. (+5 more)

### Community 26 - "describe_voice_stack"
Cohesion: 0.11
Nodes (17): _capture_status(), ComponentStatus, describe_voice_stack(), module_available(), Path, What of the voice stack is actually usable right now (ADR-0010, NFR-014). Audio…, Report each component's real state, reading configuration when given., True if ``module`` could be imported, without importing it. (+9 more)

### Community 27 - "ApprovalQueue"
Cohesion: 0.14
Nodes (28): ApprovalQueue, Called whenever the pending set changes. Used by the tray., Holds requests between the thread that needs an answer and the user. Implements…, make_request(), fixture, RiskLevel, queue(), The approval queue (ADR-0027). The timeout path is the security-critical one… (+20 more)

### Community 28 - "JarvisCore"
Cohesion: 0.08
Nodes (17): OllamaHealth, RecoveryReport, JarvisCore, Any, Everything except the user interface., Grant the two strictly self-inspecting capabilities on first start.…, Reverse of start, and idempotent., Change a setting, persist the override and announce it. (+9 more)

### Community 29 - "service.py"
Cohesion: 0.11
Nodes (17): capture_available(), CaptureSession, default_input_device(), frames_from_bytes(), list_devices(), Microphone capture and playback (PRD FR-016, FR-013, ADR-0028). ``sounddevice``…, Cut a recording into frames. Used to replay fixtures through the pipeline., Enumerate devices for the Voice screen (PRD FR-016). Never raises. (+9 more)

### Community 30 - "test_permission_engine.py"
Cohesion: 0.11
Nodes (26): PermissionRequest, A question put to the permission engine. Contains no side effects., Permission evaluation (PRD sections 9.9 and 11.1, ARCHITECTURE.md 6.4)., A user who denied something should not be asked again in the same scope., PRD 11.1: fresh confirmation every time., test_a_deny_grant_outranks_an_allow_grant(), test_a_deny_grant_suppresses_the_high_risk_prompt(), test_an_expired_grant_does_not_apply() (+18 more)

### Community 31 - "redact"
Cohesion: 0.11
Nodes (26): classify_content(), is_content_key(), is_secret_key(), Any, Secret redaction for the audit log (PRD section 11.5, FR-259). Redaction…, Return a copy of ``value`` safe to persist in the audit log. Mappings,…, Describe a value without reproducing it. Used where the *shape* of user content…, Redact secret-looking substrings, then bound the length. (+18 more)

### Community 32 - "ConversationStore"
Cohesion: 0.09
Nodes (18): ConversationStore, AuditLog, Begin a conversation. ``persist=False`` is a private session., Stop recording this conversation, and erase what was recorded. Per-conversation…, Remove a conversation and its turns. Messages cascade., Creates conversations and records turns, when recording is permitted., Global history control (PRD FR-045). Affects new conversations., AT-014, structurally: not written, rather than written then removed. (+10 more)

### Community 33 - "ApprovalPanel"
Cohesion: 0.16
Nodes (26): ApprovalPanel, One pending request, rendered with the PRD section 11.2 field set., _buttons(), make_request(), panel(), _pending(), fixture, RiskLevel (+18 more)

### Community 34 - "test_phase0_exit_criteria.py"
Cohesion: 0.08
Nodes (24): Phase 0 exit criteria and hard constraints. One test (or small group) per…, Phase 0 registers exactly one tool, and it changes nothing., PRD section 13.4: free-form text can never be executed., PRD section 4.4: nothing may silently become permanent memory., PRD section 9.1 and NFR-033., test_configuration_is_typed_and_rejects_unknown_keys(), test_every_tool_declares_the_full_prd_13_2_contract(), test_exit_1_the_application_opens_and_provides_a_tray_presence() (+16 more)

### Community 35 - "RingBuffer"
Cohesion: 0.08
Nodes (13): datetime, The pre-wake ring buffer (PRD FR-012, FR-025, AT-002). Before a wake phrase is…, Forget everything held. Called whenever listening stops., Everything ever accepted, so a test can prove discarding happened., A bounded, in-memory window of the most recent audio. Thread-safe: the capture…, Append audio, discarding whatever falls out of the window., Everything currently held, as one chunk. Does not clear the buffer., The held frames individually, for a consumer that wants to keep going. (+5 more)

### Community 36 - "OllamaChatProvider"
Cohesion: 0.13
Nodes (18): _as_int(), OllamaChatProvider, Any, Ollama chat completion (PRD FR-040, section 13.4, ADR-0007). Inherits the two…, Read only the structured field. Never parse prose for an action., Chat against a loopback Ollama. Blocking; call from a worker thread., ChatMessage, ChatProviderError (+10 more)

### Community 37 - "ConversationPanel"
Cohesion: 0.11
Nodes (23): ConversationPanel, Text conversation with the local model., panel(), fixture, The Conversation screen (PRD section 9.5, FR-046, FR-047)., The distinction is the whole point of FR-047., Model output is data here too, including in the transcript., test_a_missing_reason_still_produces_an_explanation() (+15 more)

### Community 38 - "test_secret_store.py"
Cohesion: 0.14
Nodes (26): SecretStore, fixture, skipif, WINDOWS_ONLY, The secret store (ADR-0030, PRD 18.3, NFR-022, FR-169, AT-016). The assertions…, Never partial, never best-effort plaintext., Lifting a value under a different name must not decrypt it., Degrading to weaker protection would be worse than refusing (ADR-0010). (+18 more)

### Community 39 - "personality.py"
Cohesion: 0.15
Nodes (15): Formality, Humour, PersonalityProfile, PersonalityProposal, ProposalStatus, Enum, str, Personality profile and humour proposals (PRD FR-043, FR-044, section 4.4).… (+7 more)

### Community 40 - "conftest.py"
Cohesion: 0.14
Nodes (25): MonkeyPatch, QApplication, approving_invoker(), audit(), config(), config_store(), core(), database() (+17 more)

### Community 41 - "EventBus"
Cohesion: 0.13
Nodes (17): EventBus, Thread-safe publish/subscribe with subclass matching., Typed event bus and the domain event vocabulary., _app_started(), Typed event bus (ADR-0005)., The audit log and the GUI both subscribe; one must not break the other., test_a_failing_handler_does_not_break_the_publisher_or_others(), test_a_subscriber_does_not_receive_unrelated_events() (+9 more)

### Community 42 - "VaultPaths"
Cohesion: 0.14
Nodes (5): Path, Instance-scoped files such as the single-instance lock., Create the vault layout. Idempotent., Every path the application is allowed to write to, derived from one root., VaultPaths

### Community 43 - "schema.py"
Cohesion: 0.15
Nodes (24): AudioConfig, _Base, ConversationLanguageConfig, DefaultPermissionPolicy, LanguageConfig, LlmConfig, LoggingConfig, ModelProfile (+16 more)

### Community 44 - "Conversation"
Cohesion: 0.10
Nodes (15): _describe_result(), Any, Send one proposal through the invoker. Never around it., Describe only registered tools. The model cannot learn of others., Render a tool result for the model, without inflating it., One user request and everything that came of it., Turn, Conversation (+7 more)

### Community 45 - "permissions/models.py"
Cohesion: 0.16
Nodes (21): _c(), capabilities_by_risk(), capability(), capability_ids(), The capability catalogue — PRD section 11.1 expressed as data. Risk…, Permission model, capability catalogue and evaluation engine., Capability, Decision (+13 more)

### Community 46 - "llm/conversation.py"
Cohesion: 0.12
Nodes (15): The conversation engine (PRD FR-040, FR-042, FR-047, FR-048, section 13.4).…, Conversation history and private sessions (PRD FR-045, FR-046, AT-014). A…, Turns for a live conversation, from memory; otherwise from storage., StoredMessage, ChatProvider, ChatRole, ModelRole, Any (+7 more)

### Community 47 - "test_hotkeys_and_startup.py"
Cohesion: 0.11
Nodes (21): parse_hotkey(), Parse ``"Ctrl+Alt+Pause"`` or ``"F9"``. Raises :class:`HotkeyError`., parametrize, skipif, Global hotkeys and start-at-sign-in (PRD section 11.3, FR-018, FR-002). Parsing…, The tray and the tests need a route that does not need a real keypress., PRD section 11.3 and config/defaults.yaml agree on this combination., FR-018 and ADR-0027 specify bare F9, with no modifier. (+13 more)

### Community 48 - "test_core_lifecycle.py"
Cohesion: 0.14
Nodes (23): _new_core(), Full core lifecycle, crash recovery and settings durability., Phase 0 exit criterion., PRD NFR-011: no consequential action is repeated after a restart., SQLite is the single source of truth (ADR-0002)., Kill the process the way a crash does: threads gone, nothing cleaned up.…, simulate_crash(), test_a_completed_task_is_never_re_run_after_recovery() (+15 more)

### Community 49 - "ModelRouter"
Cohesion: 0.11
Nodes (14): ModelBusyError, ModelRouter, RuntimeError, A heavy model is loaded and sequential loading is configured., Resolves a role to a configured profile, and gates heavy loads., Adopt changed configuration without rebuilding the router., Reserve a role's model for the duration of a call. Under sequential loading,…, RoutedModel (+6 more)

### Community 50 - "GlobalHotkeys"
Cohesion: 0.13
Nodes (10): GlobalHotkeys, HotkeyBinding, One requested hotkey and what actually became of it., Registers hotkeys on a dedicated thread and dispatches their actions. Off…, Declare a hotkey. Parsing happens now; registration happens at start., Run the registration and message loop on its own thread., Hotkeys the user asked for that are not actually working., Invoke a binding's action directly. The test and menu route. (+2 more)

### Community 51 - "main_window.py"
Cohesion: 0.19
Nodes (10): NavArea, _NotImplementedPanel, _PermissionsPanel, QWidget, Main window: the fifteen navigation areas of PRD section 9.3. Six areas are…, A heading, a refresh button and a read-only text area., Active grants, and any approval currently waiting for an answer. The panel…, Says exactly what is missing and when it arrives. Never a fake screen. (+2 more)

### Community 52 - "ApprovalRequest"
Cohesion: 0.14
Nodes (11): Decision, GrantScope, Declare whether a user interface is actually connected. Until one is, queueing…, Block the calling thread until answered, or until the request expires. Called…, Record the user's decision. Returns False if nothing was waiting. Raises…, Deny everything outstanding. Used by emergency stop and by shutdown., ApprovalOutcome, ApprovalRequest (+3 more)

### Community 53 - "Project Jarvis (Windows Local AI Desktop Agent)"
Cohesion: 0.13
Nodes (20): Application Catalogue and Aliases, Connected Mode (Optional External Providers), Deterministic Before Visual (Automation Hierarchy), Local Document Understanding, Hallucination Discipline (Epistemic Labelling), Honest Task Status, Bounded Definition of Learning, Local First, Not Local Only (+12 more)

### Community 54 - "tests/security/test_no_shell.py (AST scan of src/)"
Cohesion: 0.22
Nodes (14): QT_QPA_PLATFORM=offscreen in CI, CI security-invariants job, CI test job (Windows + Ubuntu, Python 3.11/3.12), Architectural Change Control, Closed Capability Set (no generic execution primitive), Six-Layer Dependency Model (L0-L5), tests/security/test_no_shell.py (AST scan of src/), Prohibited Tool Denylist (identity and pattern) (+6 more)

### Community 55 - "Resource Lock Model"
Cohesion: 0.12
Nodes (19): Conversation Agent Role, Emergency Stop, jarvis.db SQLite Single Source of Truth, .jarvispack Portable Identity Package, Memory Candidate Review Pipeline, Memory Curator Role, Memory Record Schema, Editable Personality Profile (+11 more)

### Community 56 - "pipeline.py"
Cohesion: 0.09
Nodes (26): ActivationRoute, CommandHeard, _join(), ListeningState, Enum, str, The voice loop (PRD sections 10.2 to 10.4, ADR-0027, ADR-0028). One place where…, F9 released. Transcribe what was captured. (+18 more)

### Community 57 - "OllamaHealthChecker"
Cohesion: 0.15
Nodes (17): OllamaHealthChecker, Checks the local model runtime. Blocking; call it from a worker thread., fake_ollama(), fixture, Ollama adapter boundary rules (ADR-0007, PRD AT-001)., PRD NFR-013: every external interaction has a timeout., Replace urlopen so no test ever touches a real socket., A remote 'local' endpoint would ship every prompt off the machine. (+9 more)

### Community 58 - "VoicePanel"
Cohesion: 0.12
Nodes (6): QWidget, State the phrase literally. Never label it 'Jarvis' (FR-011)., Show the measurement, and gate always-listening on it (ADR-0016)., True if anything on this screen implies bare "Jarvis" works. FR-011 forbids…, Devices, voices, wake phrase and enrolment., VoicePanel

### Community 59 - "Project Jarvis Implementation Backlog"
Cohesion: 0.12
Nodes (18): ARCHITECTURE.md, Subsystem area codes (CFG, COR, SEC, TSK, AUD, LLM, ...), Cross-phase invariants, DATA_MODEL.md, S/M/L/XL effort sizing (not time), Project Jarvis Implementation Backlog, Invariant: phase exit criteria must be demonstrated, Invariant: no generic execution primitive (+10 more)

### Community 60 - "Phase 0 — Foundation and safety architecture"
Cohesion: 0.15
Nodes (23): EventBridge, Invariant: state-changing tools declare reversibility metadata, JarvisCore, LockManager, P0-CFG-01 Layered typed configuration, P0-CFG-03 SQLite storage and versioned forward migrations, P0-COR-01 Typed event bus, P0-COR-02 Tool contract: ToolSpec with reversibility metadata (+15 more)

### Community 61 - "Dedicated Jarvis Brave Profile"
Cohesion: 0.16
Nodes (18): ADR-0018: Search Provider, Option C: Ask a Configured AI Website (FR-055), Untrusted Web Content Wrapping (FR-054), Visible Brave Search Mode (FR-052), ADR-0019: Browser Profile Isolation, CAPTCHA Pause-and-Ask Requirement (FR-058), Dedicated Jarvis Brave Profile, Option C: Playwright Bundled Chromium Persistent Context (+10 more)

### Community 62 - "Subscription"
Cohesion: 0.13
Nodes (8): E, Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe., Receive ``event_type`` and every subclass of it., Subscription, EventBridge, QObject, The one place the domain and Qt threading models meet (ADR-0005). Domain events…, Re-emits domain events as Qt signals on the GUI thread.

### Community 63 - "Resource Locks (jarvis.tasks.locks)"
Cohesion: 0.22
Nodes (9): Concurrency Invariants, Resource Locks (jarvis.tasks.locks), SQLite Concurrency Strategy (WAL, per-thread connections), Forward-Only Transactional Migrations, resource_lock table, runtime_instance table, schema_migration table, SQLite Is the Single Source of Truth (+1 more)

### Community 64 - "ui/__init__.py"
Cohesion: 0.16
Nodes (12): QColor, QIcon, Enum, str, Tray state icons, drawn programmatically. Two reasons not to ship image files:…, PRD section 9.1 tray states., A non-colour distinguishing mark (PRD NFR-033)., Render the icon for a state. Colour *and* shape differ per state. (+4 more)

### Community 65 - "ProhibitedToolError"
Cohesion: 0.18
Nodes (15): assert_tool_id_permitted(), check_tool_id(), ProhibitedToolError, Exception, The prohibited-capability guard (ADR-0003). Defence in depth, layer 2 of 3: 1.…, Return the reason a tool id is prohibited, or ``None`` if it is allowed., ``True`` if the tool id may be registered., Registration was refused because the tool is prohibited by policy. (+7 more)

### Community 66 - "SourceLabel"
Cohesion: 0.14
Nodes (12): GroundedClaim, _hedge(), Enum, str, Where an answer came from, and what counts as done (PRD FR-047, FR-048). Two…, The verification value of a succeeded result; empty if it did not succeed., Replace an unverified success claim with what is actually known., PRD FR-047's five categories, and nothing outside them. (+4 more)

### Community 67 - "test_lazy_audio_imports.py"
Cohesion: 0.20
Nodes (15): _module_name(), _module_scope_imports(), parametrize, Path, Audio dependencies stay optional and lazily imported (ADR-0010, NFR-014).…, The property all of the above exists to protect., Imports at module level only — imports inside a function are the point., A guard on the guard: prove the detector is not vacuously passing. (+7 more)

### Community 68 - "test_prohibited_capabilities.py"
Cohesion: 0.16
Nodes (14): The prohibited-capability guard (ADR-0003, PRD sections 11.1 and 13.3)., No grant, setting or approval can reach past the prohibited check., PRD section 11.1's prohibited list is represented in the catalogue., In a fully wired runtime, nothing is registered against a prohibited class., test_catalogue_covers_every_prd_prohibited_class(), test_no_tool_may_ever_be_registered_for_a_prohibited_capability(), test_prohibited_capability_is_always_denied_regardless_of_grants(), test_registry_refuses_a_prohibited_tool() (+6 more)

### Community 69 - "Over-Permission (OP) category"
Cohesion: 0.18
Nodes (15): Approval dialog required fields, Capability risk classification (low/medium/high/prohibited), Permission decision types, Permission model, Prohibited capability class, Over-Permission (OP) category, Open question: detecting a spoofed window, T-023 Session grant exercised beyond the prompting request (+7 more)

### Community 70 - "test_layering.py"
Cohesion: 0.26
Nodes (14): _imported_modules(), _module_name(), _package_of(), Path, Layering invariants (ARCHITECTURE.md section 5, ADR-0004). The rule that makes…, A fresh interpreter can import the whole engine with no Qt module loaded., Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.…, Spelled out separately because it is the invariant people break first. (+6 more)

### Community 71 - "Task Scheduler (jarvis.tasks.scheduler)"
Cohesion: 0.17
Nodes (12): Bounded Timeouts and Declared Retry Policy, In-Process Isolation Is Not a Security Boundary, Deferred Process Separation (TTS worker, elevation helper), Single-Process Multi-Thread Model, Task Scheduler (jarvis.tasks.scheduler), Phase 0 Known Limitations, tasks scheduler settings, audio.text_to_speech profiles (+4 more)

### Community 72 - "LLM Boundary (jarvis.llm)"
Cohesion: 0.18
Nodes (12): LLM Boundary (jarvis.llm), Loopback-Only Ollama Endpoint, Separate Model Roles (planner, vision, embeddings, STT, TTS), Planner Cannot Skip the Invoker, system.health (the one registered Phase 0 tool), llm.ollama settings (loopback base_url, require_loopback), model_runtime (sequential load strategy), models.* role-to-profile mapping (+4 more)

### Community 73 - "ADR-0003: A Closed Capability Set — No Generic Execution Primitive"
Cohesion: 0.15
Nodes (16): One SQLite Connection Per Thread, ADR-0003: A Closed Capability Set — No Generic Execution Primitive, No Generic Execution Primitive, os.startfile Named Future Allow-Listed Exception, tests/security/test_no_shell.py Source Tree Scan, Tool Registry Identity and Pattern Denylist, ADR-0004: Single Process, Thread Isolation for Phases 0–3, Layering Rule: Core Packages Must Not Import PySide6 (+8 more)

### Community 74 - "NetworkMode"
Cohesion: 0.16
Nodes (7): NetworkMode, Enum, str, OllamaHealth, Ollama health check (ADR-0007). Two boundary rules are enforced here rather…, The result of one check. Never claims health it did not observe., Ollama adapter. Phase 0 implements only the health check.

### Community 75 - "test_at014_private_session.py"
Cohesion: 0.18
Nodes (13): parametrize, AT-014 — a private session produces no permanent record after it ends. Asserted…, Everything the vault has written, as raw bytes., A control: prove the byte search would have found it if written., Privacy is not the same as invisibility: the event is auditable., test_a_normal_session_is_recorded_so_the_test_above_means_something(), test_a_private_conversation_is_marked_private_to_the_user(), test_a_private_session_leaves_no_record_anywhere() (+5 more)

### Community 76 - "test_no_shell.py"
Cohesion: 0.25
Nodes (13): _findings(), parametrize, Path, The load-bearing security test (ADR-0003). Phase 0 exit criterion: *no generic…, No shipped module may start a process or evaluate generated code., A guard on the guard: prove the detector is not vacuously passing., The denylist module names these primitives in patterns; that must be fine., No function or class in the runtime is named after a prohibited tool. (+5 more)

### Community 77 - "On-Demand Narrowly Scoped Elevated Helper Process"
Cohesion: 0.22
Nodes (13): ADR-0001: Python-First Implementation with Rust Deferred, Python 3.11 + PySide6 Implementation Stack, Qwen3-TTS Isolated Python 3.12 Worker, Rust/Tauri Native Shell Deferred Past Phase 3, Authenticated Typed IPC for Future Shell, Process-Separation Promotion Triggers, Helper IPC Discipline (Named Pipe or Loopback, Rotating Token), No Interaction with the Windows Secure Desktop or UAC Prompt (+5 more)

### Community 78 - "SQLite (jarvis.db) Canonical Transactional Store"
Cohesion: 0.23
Nodes (13): ADR-0002: SQLite as the Single Source of Truth, Large Binary Artefacts Stored on Disk, Referenced by Path, Derived Rebuildable Stores Hold No Unique Information, SQLite (jarvis.db) Canonical Transactional Store, WAL Mode Concurrent Readers, ADR-0005: An In-Process Typed Event Bus, Bus Is Notification, Not System of Record, ADR-0006: Layered Configuration with Override-Only Persistence (+5 more)

### Community 79 - "jarvis.core.events In-Process Publish/Subscribe Bus"
Cohesion: 0.20
Nodes (11): Versioned Forward-Only Migrations, Full ORM (SQLAlchemy) Rejected for Phase 0, Schema-Version Startup Check (Newer DB is Hard Failure), jarvis.core.events In-Process Publish/Subscribe Bus, Frozen Pydantic Event Models with Subclass Matching, Per-Handler Exception Isolation, ConfigChanged Runtime Event, pydantic extra="forbid" Loud Typo Failure (+3 more)

### Community 80 - "No Shared API Keys Constraint (§18.3)"
Cohesion: 0.29
Nodes (7): No Shared API Keys Constraint (§18.3), Option B: Optional User-Supplied Search API Key, Portable Identity Export (FR-168), Secret Exclusion from Normal Exports (FR-169/FR-170), Blocked-Capture Application Exclusions (FR-273), Option C: Diagnostic Mode with Global Disk Budget, Option B: Extended Retention for Failed Tasks

### Community 81 - ".__init__"
Cohesion: 0.18
Nodes (6): QAction, QMenu, QSystemTrayIcon, QObject, Colour, shape, tooltip and accessible name all change together., TrayState

### Community 82 - "Prompt Injection (PI) category"
Cohesion: 0.23
Nodes (13): Closed authority set for tool authorisation, Security Policy and Control Specification, Untrusted-data rule, The LLM as a confused deputy, Malicious web content author, Prompt Injection (PI) category, STRIDE threat classification, T-001 Web page text instructs Jarvis to act (+5 more)

### Community 83 - "tools/ports.py"
Cohesion: 0.19
Nodes (9): ApprovalPort, LockLease, LockPort, Protocol, Ports the tool invoker depends on, so ``jarvis.core`` stays free of Qt and of…, Return a lease, or ``None`` if the whole set could not be taken., Asks the user. The core asks; the shell answers., A held set of resource locks. (+1 more)

### Community 84 - "main"
Cohesion: 0.20
Nodes (11): ArgumentParser, build_parser(), main(), Entry point. jarvis start the tray application jarvis --check start the core…, _run_check(), An honest report of an unreachable runtime is a successful self-check. Settled…, Phase 1 state must be visible from the headless self-check., test_check_reports_the_voice_stack_and_secret_store() (+3 more)

### Community 85 - "Closed Enumerated Set of Narrow Typed Tools"
Cohesion: 0.21
Nodes (12): Closed Enumerated Set of Narrow Typed Tools, Emergent Capability From Tool Composition (Residual Risk), Hard Ceiling on Prompt Injection Impact, Sandboxed Generic Shell Rejected, ToolSpec Typed Tool Contract, Thread Isolation Is Not a Security Boundary (Gap 2), Ollama Endpoint Squatting (Unmitigated Residual Risk), Local Authenticating Proxy for Ollama Not Adopted (+4 more)

### Community 86 - "Capability Risk Classes"
Cohesion: 0.29
Nodes (12): Approval Dialog Design, Consequential-Action Audit Log, Capability Risk Classes, Executor Role, Jarvis Core (Orchestration), Password and Credential Field Protection, Planner Role, Prompt-Injection Defence (+4 more)

### Community 87 - "WakeDetector"
Cohesion: 0.17
Nodes (5): Protocol, Streams frames in, yields a wake event when the phrase is heard., Audio in, transcript out. Local by default (PRD FR-020)., SttProvider, WakeDetector

### Community 88 - "T-048 Secrets leak into audit log, crash dump, or telemetry"
Cohesion: 0.18
Nodes (11): Audit log requirements (append-only, redacted), .jarvispack normal-export secret exclusions, Deletion is non-destructive by default, Screen capture scoping and screenshot retention, Secrets storage via DPAPI / Credential Manager, Signed installers and update packages, Telemetry off by default with content exclusions, T-048 Secrets leak into audit log, crash dump, or telemetry (+3 more)

### Community 89 - "offerable_scopes_for"
Cohesion: 0.18
Nodes (11): offerable_scopes_for(), RiskLevel, The allow-scopes the dialog may offer, per the ADR-0027 table. Low offers…, PRD 9.9 and 11.1: fresh confirmation every time., The engine still supports SESSION; the dialog deliberately does not., test_a_prohibited_capability_is_offered_nothing(), test_allow_for_this_session_is_never_offered(), test_high_risk_is_offered_single_use_only() (+3 more)

### Community 90 - "startup.py"
Cohesion: 0.36
Nodes (10): available(), describe(), is_enabled(), Start at sign-in (PRD FR-002). Uses the per-user…, Only Windows has the Run key this uses., The command Windows would run at sign-in. ``pythonw.exe`` rather than…, Add or remove the sign-in entry. Never requires administrator rights., set_enabled() (+2 more)

### Community 91 - "task table"
Cohesion: 0.24
Nodes (12): Crash Recovery, Offline Mode Enforced at the Adapter Boundary, Ten-State Task Machine (jarvis.tasks.states), Task Store (jarvis.tasks.store), ToolResult (typed outcomes), Success Requires Verification, network.mode (offline / local_assistant / connected), task_checkpoint table (+4 more)

### Community 92 - "Phase 2 — Deterministic desktop and browser automation"
Cohesion: 0.20
Nodes (14): P1-APP-01 Application launcher with launch verification, P2-BRW-01 Dedicated persistent Jarvis Brave profile, P2-BRW-02 Playwright visible-browser, DOM-first execution, P2-BRW-08 YouTube search and indexed result selection, P2-FS-01 Windows Known Folder resolution, P2-FS-06 Filesystem scoping and path validation, P2-WIN-02 UI Automation inspector, P2-WIN-04 Input ownership via foreground_desktop lock (+6 more)

### Community 93 - "Phase 0 security status table"
Cohesion: 0.24
Nodes (10): Approval port (deny by default), Layering enforcement test (no Qt below presentation), Ollama health check (loopback-only), Phase 0 security status table, Tool invoker six-step pipeline (jarvis.core.tools.invoker), Typed event bus (jarvis.core.events), Hallucinated Success (HS) category, Open question: authenticating the Ollama endpoint (+2 more)

### Community 94 - "Root-scoped filesystem tools"
Cohesion: 0.27
Nodes (10): Archive extraction protections, Absolutely denied filesystem targets, Root-scoped filesystem tools, Path canonicalisation before scope check, Phase-gated mitigation roadmap, T-038 Path traversal escapes the approved root scope, T-039 Symlink or NTFS junction escapes approved scope, T-040 TOCTOU path swap after scope validation (+2 more)

### Community 95 - "Tool-invocation evaluation order"
Cohesion: 0.31
Nodes (10): Tool-invocation evaluation order, Static src/ scan for prohibited primitives, Named prohibited broad tools, Tool registry registration denylist, T-010 Self-injection via Jarvis's own prior output, T-011 Model invents a nonexistent tool name, T-012 Model requests a shell/code-execution tool, T-014 Valid tool call with out-of-scope parameters (+2 more)

### Community 96 - "T-052 Another local Windows user reads the SQLite vault"
Cohesion: 0.22
Nodes (10): Resource locks (jarvis.tasks.locks), Open question: hardening %LOCALAPPDATA% ACLs at startup, Other local Windows users, T-028 Two tasks race for the foreground desktop-control lock, T-030 Foreground lock not released after Automation Worker crash, T-034 Consequential action replayed after restart, T-052 Another local Windows user reads the SQLite vault, T-067 Clipboard capture records a password or TOTP code (+2 more)

### Community 97 - "Emergency Stop"
Cohesion: 0.29
Nodes (7): CI dependency and licence review job, Emergency Stop, Honest Degraded UI (disabled, not hidden, not fake), Jarvis Shell (jarvis.ui tray and main window), ui settings (tray start, show_unavailable_features, emergency hotkey), Entities Defined But Not Yet Built, No Bundled Third-Party Assets

### Community 98 - "JarvisCore (composition root)"
Cohesion: 0.27
Nodes (12): CI headless self-check step (jarvis.main --check), Layered Configuration System (jarvis.config), extra=forbid Everywhere, JarvisCore (composition root), Override-Only Persistence, Only L5 May Import PySide6, Single-Instance Guard, VaultPaths (centralised path resolution) (+4 more)

### Community 99 - "ToolInvoker (six-step pipeline)"
Cohesion: 0.17
Nodes (16): ApprovalPort, Capability Catalogue (risk classification as data), DenyingApprovalPort (silence is never consent), Extension Points Table, Grant Scopes (ONCE, SESSION, TASK, APPLICATION, FOLDER, ALWAYS), Permission Engine (jarvis.core.permissions), Single Choke Point for Tool Execution, ToolInvoker (six-step pipeline) (+8 more)

### Community 100 - ".__init__"
Cohesion: 0.25
Nodes (7): ConfigStore, SingleInstanceGuard, default_log_path(), Path, test_exit_3_a_second_instance_is_refused(), test_the_task_state_machine_is_persistent(), VaultPaths

### Community 101 - "Phase 1 — Voice-first local assistant"
Cohesion: 0.16
Nodes (18): ADR-0001 Python-first shell (native Rust/Tauri deferred), ADR-0009 Scoped elevation helper interface, Deferred beyond Version 1, P1-AUD-01 Wake-word detection (openWakeWord), P1-AUD-05 Local STT (faster-whisper), P1-AUD-07 Local TTS (Kokoro), P1-AUD-10 Expressive TTS worker isolation prototype (Qwen3-TTS), P1-SEC-02 DPAPI-backed secret store (+10 more)

### Community 102 - "Automation Worker"
Cohesion: 0.22
Nodes (9): TaskScheduler, Automation Worker, Dedicated Jarvis Brave Profile, Foreground Desktop-Control Lock, Playwright Browser Automation Layer, Explicit Search Modes, Visible Browser Search, Jarvis Core (orchestration, permissions, audit) (+1 more)

### Community 103 - "qwen3-embedding:0.6b Tentative Default"
Cohesion: 0.24
Nodes (11): Model Resource Scheduler (FR-039), Option A: Strict Mutual Exclusion Scheduling, Option B: VRAM-Budget-Aware Co-Residency, Option B: Dedicated Retrieval-Purpose-Built Embedding Model, Embedding Invocation Frequency Cost, qwen3-embedding:0.6b Tentative Default, Rebuildable Derived Index Constraint, Option A: Local Backup Only, No Network Transport (+3 more)

### Community 104 - "Phased Delivery Plan (Phase 0-6)"
Cohesion: 0.25
Nodes (9): Google Antigravity IDE Adapter, Phased Delivery Plan (Phase 0-6), Filesystem Tool Root Scoping, IDE-Agent Orchestration, Windows Known Folder Resolution, Product Non-Goals, Prohibited Broad Tools, Safe Jarvis Workspace (+1 more)

### Community 105 - "Local Wake Phrase Detection"
Cohesion: 0.28
Nodes (9): Audio Worker, English-Only Language Policy, faster-whisper STT Engine, Local Speech-to-Text, Local Text-to-Speech, openWakeWord Model Runtime, Privacy-Preserving Audio Ring Buffer, Push-to-Talk Hotkey (+1 more)

### Community 106 - "Jarvis Shell (GUI Process)"
Cohesion: 0.31
Nodes (9): Jarvis Shell (GUI Process), Kokoro TTS Provider, Authenticated Loopback IPC, Piper TTS Provider, PySide6 Desktop Shell Toolkit, Python 3.11 as V1 Implementation Language, Qwen3-TTS Expressive Provider, Provider-Neutral TTS Interface (+1 more)

### Community 107 - "denial_options_for"
Cohesion: 0.22
Nodes (9): denial_options_for(), Capability, Don't ask again" options, when the capability has a meaningful target. A…, The button must not overstate what a remembered denial covers., test_a_folder_scoped_capability_offers_a_folder_denial(), test_a_url_capability_says_site_rather_than_application(), test_an_application_scoped_capability_offers_to_remember_the_denial(), test_nothing_is_offered_for_a_capability_with_no_scope_kind() (+1 more)

### Community 108 - "is_loopback_url"
Cohesion: 0.25
Nodes (6): is_loopback_url(), Exception, True when the URL's host is a loopback address or resolves only to one., parametrize, test_loopback_urls_are_recognised(), test_non_loopback_urls_are_rejected()

### Community 109 - "hotkeys.py"
Cohesion: 0.22
Nodes (7): available(), Hotkey, HotkeyError, Global hotkeys (PRD section 11.3, FR-018, ADR-0027). Two hotkeys exist in Phase…, A hotkey string could not be understood., Global hotkeys are a Windows facility in this build., A parsed combination, ready for ``RegisterHotKey``.

### Community 110 - "Path"
Cohesion: 0.22
Nodes (9): parametrize, Path, Screenshot-based computer control is still out of scope. Phase 1 legitimately…, No autonomous self-modification: every write path targets the vault., PRD section 25 lists sixteen open decisions., test_an_adr_exists_for_every_prd_open_decision(), test_no_screenshot_or_input_automation_module_exists(), test_required_documents_and_config_exist() (+1 more)

### Community 111 - "test_no_elevation.py"
Cohesion: 0.31
Nodes (6): Path, Non-administrator operation (PRD FR-003, NFR-020, ADR-0009). Phase 0 must run…, Any packaging manifest must be asInvoker., _relative(), test_no_manifest_declares_an_elevated_execution_level(), test_no_module_requests_elevation()

### Community 112 - "ADR-0014: Default English Voice"
Cohesion: 0.39
Nodes (8): ADR-0014: Default English Voice, Kokoro bm_george Default Voice, Windows SAPI Emergency Fallback, ADR-0015: Additional TTS Providers, No Silent Voice Provider Switching (FR-036), Qwen3-TTS Isolated Python 3.12 Worker, Provider-Neutral TtsProvider Interface, Update Rollback and Schema Compatibility Checks

### Community 113 - "MSIX Sandboxing vs Desktop Automation Tension"
Cohesion: 0.32
Nodes (8): espeak-ng GPL-Family Licensing Consideration, ADR-0020: Plugin and Skill Signing, ADR-0022: MSIX Distribution, Option A: MSIX as Primary Distribution Format, Option B: MSIX as Secondary Optional Channel, MSIX Sandboxing vs Desktop Automation Tension, Automation Worker Adversarial Input Exposure, ADR-0026: Code-Signing and Update Infrastructure

### Community 114 - "Voice Pack Redistribution Licensing Gap"
Cohesion: 0.29
Nodes (8): Per-Download Provider and Licence Disclosure, Voice Pack Redistribution Licensing Gap, ADR-0016: Custom Jarvis Wake Word, Option A: Purpose-Trained Custom Jarvis Wake Model, False-Activation Evaluation Harness, Hey Jarvis Interim Wake Phrase, Push-to-Talk Global Hotkey Fallback, Expired Screenshot Evidence Must Degrade Honestly

### Community 115 - "Option B: Self-Signed Developer Keys"
Cohesion: 0.36
Nodes (8): Option C: Project-Operated Signing Authority, Option B: Self-Signed Developer Keys, Skill Manifest signed Field, Option B: EV Certificate with Optional Automatic Checks, Option A: OV Certificate with Manual Update Checks, Signature Verification Precedes Execution, SmartScreen Reputation Barrier, Update Package Format and Manifest Schema

### Community 116 - "configure_logging"
Cohesion: 0.29
Nodes (6): Logger, Diagnostics: application logging and, later, crash reporting., configure_logging(), Path, Structured application logging. Separate from the audit log. The audit log…, Configure the root logger once. Idempotent.

### Community 117 - "generate_voice_sample"
Cohesion: 0.32
Nodes (7): ndarray, RuntimeError, generate_voice_sample(), main(), normalise_audio(), Path, Convert Kokoro output into a one-dimensional NumPy array.

### Community 118 - "Five-component process model"
Cohesion: 0.25
Nodes (8): Emergency stop surface, Local IPC requirements (loopback, per-install token), Non-admin by default, Five-component process model, Scoped elevation helper process, Secure desktop and UAC prompts off-limits, TTS worker isolation (Qwen3-TTS, separate env), T-053 Unauthenticated loopback port accepts local tool calls

### Community 119 - "PermissionEvaluation"
Cohesion: 0.25
Nodes (6): PermissionEvaluation, PermissionGrant, BaseModel, datetime, The engine's answer. Never executes anything., A recorded permission decision that may apply to future requests.

### Community 120 - "Redaction Before Serialisation"
Cohesion: 0.43
Nodes (7): Dual-Sink Append-Only Audit Log (jarvis.core.audit), Redaction Before Serialisation, logging settings (audit_to_sqlite, max_audit_value_chars), audit_event table, Export and Import Constraints, Ten Persisted Integrity Invariants, Two Audit Sinks, One Record of Truth

### Community 121 - "Architectural Drivers"
Cohesion: 0.29
Nodes (7): Architectural Drivers, Typed In-Process Event Bus (jarvis.core.events), EventBridge (domain events to queued Qt signals), Model Output Is Untrusted Input, Qt Main Thread Must Not Block, Untrusted Content Enters as Delimited Observations, Rust Deferred Until After Phase 3

### Community 122 - "P0-SEC-03 Permission engine"
Cohesion: 0.38
Nodes (7): P0-SEC-03 Permission engine, P2-BRW-06 Untrusted web-content wrapping and prompt-injection test, P5-IDE-05 IDE permission boundary (no automatic approval), P5-IDE-08 No hidden shell delegation (adversarial test), PermissionEngine, Phase 5 — IDE orchestration, tests/security/test_prompt_injection.py

### Community 123 - "Phase 3 — Tasks, macros, and memory"
Cohesion: 0.43
Nodes (7): P2-WIN-03 Automation worker thread (pywinauto UIA backend), P3-CLP-01 Clipboard permissions and operations, P3-MEM-01 Memory candidate pipeline with review queue and provenance, P3-MEM-03 Forget with cascade delete from derived indexes, P3-MEM-06 Portable identity export/import (.jarvispack) with secret exclusion, P3-TSK-02 Pause/resume with mandatory state re-observation, Phase 3 — Tasks, macros, and memory

### Community 124 - "ADR-0008: Secret Storage Deferred to Phase 1"
Cohesion: 0.38
Nodes (7): ADR-0008: Secret Storage Deferred to Phase 1, jarvis.core.audit.redaction Defence-in-Depth Backstop, Windows Credential Manager CredWrite/CredRead (Candidate Mechanism), DPAPI CryptProtectData via ctypes (Candidate Mechanism), Encrypted SQLite Table with DPAPI-Wrapped Key (Candidate Mechanism), No Secret Store Implemented in Phase 0, Secrets Excluded From Normal Exports

### Community 125 - "ADR-0013: Installer Technology"
Cohesion: 0.29
Nodes (7): No Elevation Manifest Security Check (asInvoker), Application Never Runs Permanently as Administrator, ADR-0013: Installer Technology, Installer Choice Sequenced Behind the MSIX Decision, NSIS (Candidate Installer), Per-User Install with No UAC Elevation, WiX Toolset MSI (Candidate Installer)

### Community 126 - "Never Claim Unverified Success"
Cohesion: 0.29
Nodes (7): Never Claim Unverified Success, Programmatically Drawn QPainter Tray Icons, ADR-0011: Public Product Name, "Jarvis" as Internal Codename Only, public_product_name Configuration Value, Rename Before Public Release (Leaning Option), Trademark and Identifier Availability Criteria

### Community 127 - "Option B: Per-Stream Retention Defaults with Expiry"
Cohesion: 0.24
Nodes (11): ADR-0017: Embedding Model, Option C: First-Run Wizard Hardware Benchmark, ADR-0021: Encrypted Sync and Backup, ADR-0024: Data Retention Defaults, Audit Log as a Safety Record, Clipboard History Retention (FR-253), Option C: One Global Retention Period, Option A: Keep Everything Until User Deletes (+3 more)

### Community 128 - "First-Run Onboarding Wizard"
Cohesion: 0.38
Nodes (7): First-Run Onboarding Wizard, Model Resource Scheduler (VRAM Arbitration), Per-Role Model Routing, Ollama Local Model Runtime, qwen3:8b Planner/Conversation Model, qwen3-vl Vision Model Route, Signed Windows Installer and Updates

### Community 129 - "Arc Reactor Visual Motif"
Cohesion: 0.52
Nodes (7): Jarvis Application Icon (Arc Reactor Mark), Arc Reactor Visual Motif, Circular Metallic Chassis Ring, Cyan-on-White Emissive Palette, Jarvis Product Brand Identity, Transparent Alpha Square Canvas, Inverted Triangular Glowing Core

### Community 131 - "ConversationWorker"
Cohesion: 0.29
Nodes (4): ConversationWorker, QObject, QWidget, Runs one turn off the UI thread. The model call is slow and blocking.

### Community 133 - "DenyingApprovalPort Default Implementation"
Cohesion: 0.33
Nodes (6): ADR-0007: Ollama Loopback-Only Trust Boundary, Loopback-Only Base URL Enforcement at the Adapter, Offline Mode Enforced at the Adapter Boundary, DenyingApprovalPort Default Implementation, Inno Setup (Candidate Installer), Uninstall-Time Data Deletion Must Be Opt-In

### Community 134 - "Residual risks accepted for Phase 0"
Cohesion: 0.40
Nodes (6): Dependency and licence scanning CI gate, Compromised or typosquatted Python dependency, Residual risks accepted for Phase 0, T-060 DLL search-order hijacking of the packaged build, T-069 Malicious or typosquatted PyPI dependency, TB-10 Jarvis to Windows OS security boundary

### Community 137 - "ModelRuntimeConfig"
Cohesion: 0.40
Nodes (3): model_validator, ModelRuntimeConfig, TextToSpeechConfig

### Community 138 - ".__init__"
Cohesion: 0.40
Nodes (3): AuditLog, datetime, EventBus

### Community 139 - "test_whisper.py"
Cohesion: 0.70
Nodes (4): list_audio_devices(), main(), record_audio(), transcribe_audio()

### Community 140 - "Retention and Deletion Rules"
Cohesion: 0.67
Nodes (4): privacy retention defaults, Retention and Deletion Rules, Soft References So Audit Survives Its Subject, Privacy Defaults (telemetry off, no raw audio)

### Community 142 - "GroundingReview"
Cohesion: 0.50
Nodes (3): GroundingReview, The verdict on a proposed reply., True when nothing in the reply overstates what actually happened.

### Community 144 - "test_enabling_then_disabling_leaves_no_entry"
Cohesion: 0.50
Nodes (4): WINDOWS_ONLY, Runs against the real per-user Run key, and cleans up after itself., test_enabling_then_disabling_leaves_no_entry(), test_the_startup_command_points_at_an_interpreter_that_exists()

### Community 145 - "test_high_risk_cannot_be_allowed_beyond_a_single_use"
Cohesion: 0.50
Nodes (4): parametrize, PRD 9.9: high-risk permissions must not offer 'always allow'., test_high_risk_cannot_be_allowed_beyond_a_single_use(), test_risk_classification_matches_the_prd()

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
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `T-030 Foreground lock not released after Automation Worker crash` and `T-034 Consequential action replayed after restart`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Arc Reactor Visual Motif` and `Cyan-on-White Emissive Palette`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `"Jarvis" as Internal Codename Only` and `ADR-0012: Shell Technology for the First Public Build`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `JarvisCore` connect `JarvisCore` to `ToolCall`, `AppConfig`, `test_runtime_primitives.py`, `Database`, `PermissionEngine`, `VoiceService`, `test_ollama_tool_calling.py`, `test_grounding_and_history.py`, `core.py`, `JarvisApplication`, `MainWindow`, `ApprovalQueue`, `ConversationStore`, `test_phase0_exit_criteria.py`, `OllamaChatProvider`, `conftest.py`, `Conversation`, `test_core_lifecycle.py`, `ModelRouter`, `main_window.py`, `NetworkMode`, `test_at014_private_session.py`, `main`, `.__init__`, `Path`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `Database` connect `Database` to `ToolCall`, `ConversationStore`, `TaskState`, `AuditLog`, `personality.py`, `conftest.py`, `ResourceLockManager`, `test_runtime_primitives.py`, `Conversation`, `llm/conversation.py`, `PermissionEngine`, `test_core_lifecycle.py`, `test_grounding_and_history.py`, `core.py`, `test_tasks.py`, `JarvisCore`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `VoiceService` connect `VoiceService` to `DuplexCoordinator`, `RingBuffer`, `VoicePipeline`, `AudioUnavailable`, `Database`, `AudioChunk`, `core.py`, `pipeline.py`, `JarvisCore`, `service.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 29 inferred relationships involving `JarvisCore` (e.g. with `VoiceService` and `AppConfig`) actually correct?**
  _`JarvisCore` has 29 INFERRED edges - model-reasoned connections that need verification._