# Graph Report - .  (2026-08-02)

## Corpus Check
- 116 files · ~137,316 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1891 nodes · 4329 edges · 121 communities (111 shown, 10 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 597 edges (avg confidence: 0.6)
- Token cost: 761,884 input · 0 output

## Community Hubs (Navigation)
- Task Runner Contract
- Task State Machine
- Shared Common Primitives
- Audit Log Writer
- SQLite Database Layer
- Event Bus and Tool Registry
- Worker Thread Supervisor
- Tool Contract Definition
- Prohibited Tool Guards
- Tool Invoker Pipeline Tests
- Config Schema Models
- Ollama Health Check
- Resource Lock Events
- Phase 0 Exit Criteria
- Single Instance Guard
- Domain Event Types
- Permission Engine Tests
- Tool Subsystem Entry Points
- Vault Path Layout
- Secret Redaction
- System Tray Icon
- Tool Invocation Results
- Core Lifecycle and Crash Recovery
- Permission Evaluation Engine
- Shell UI Tests
- Tray State Icons
- Config Store Persistence
- Permission Grants
- Configuration Tests
- CI Security Invariants
- Main Window Shell
- Application Composition Root
- Backlog Structure and Sizing
- Search and Browser Isolation ADRs
- Config Package Paths
- Adapters and Automation Scope
- Task Crash Recovery
- Diagnostics and Logging Setup
- Voice Audio Stack
- Agent Roles and Capability Risk
- Phase 0 Core Work Items
- Navigation Areas and Placeholders
- Permission Model Specification
- Config Store Tests
- Layering Enforcement Test
- Event Bus Tests
- Phase 1-2 App and Browser Items
- Closed Capability Set ADRs
- No-Shell Security Test
- Core Phase Work Items
- Python-First Shell ADR
- SQLite Source of Truth ADR
- Migrations and Event Models
- Export, Retention and Keys
- Threat Model Taxonomy
- Qt Event Bridge
- Capability Catalogue
- Config and Composition Invariants
- Architecture Drivers and LLM Boundary
- Process Isolation Limits
- Task Store and Network Modes
- No Generic Execution Primitive
- Five-Component Process Model
- Ollama Health Adapter
- Phase 1+ Security Controls
- ToolSpec Schema Validation
- Model Roles and Audio Settings
- Memory and Approval Design
- Product Principles and Non-Goals
- Phase 0 Security Status
- Filesystem Path Scoping
- Prohibited Capability Enforcement
- Lock Contention Threats
- Concurrency and Schema Invariants
- Deferred Vision Work Items
- VRAM Scheduler and Embeddings
- Event Subscriptions
- TTS Providers and Model Routing
- Runtime Composition Layer
- Config Validation Errors
- ADR Coverage Tests
- No Elevation Test
- Approval Port and Grant Scopes
- Default Voice ADRs
- MSIX and Plugin Signing ADRs
- Wake Word and Voice Licensing
- Code Signing Certificate Options
- IPC and Elevation Boundaries
- UI Settings and CI Licence Job
- Dual-Sink Audit Design
- Phase 3 Memory Work Items
- Secret Storage Candidates
- Installer Technology ADR
- Honest Degraded UI ADR
- Backup and Retention ADRs
- Kokoro TTS Script
- Jarvis Application Icon
- Package Entry Points
- Phase 1 Voice Work Items
- Loopback Trust Boundary ADR
- Supply Chain Threats
- Phase 6 Productisation Items
- Settings Mutation Helpers
- Process Component Inventory
- Whisper STT Script
- Privacy Retention Defaults
- Permission Evaluation Result
- Tray Exit Criteria Tests
- Emergency Stop Tests
- High Risk Permission Tests
- Idempotent Shutdown
- Vault Free Space Check
- Core Layer Package
- LLM Layer Package
- Health Check Task Queue
- Self-Inspecting Grants
- Audio Transcription Threats
- UUID Identifier Helper
- Task Scheduler
- Project Root

## God Nodes (most connected - your core abstractions)
1. `JarvisCore` - 100 edges
2. `EventBus` - 76 edges
3. `ToolCall` - 71 edges
4. `AuditLog` - 70 edges
5. `Database` - 62 edges
6. `TaskState` - 55 edges
7. `ResourceLockManager` - 50 edges
8. `ToolInvoker` - 47 edges
9. `VaultPaths` - 46 edges
10. `TaskStore` - 45 edges

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

## Communities (121 total, 10 thin omitted)

### Community 0 - "Task Runner Contract"
Cohesion: 0.05
Nodes (29): Any, Enum, Protocol, str, What a task actually does. Runners are the extension point that later phases…, Persist a resume point (PRD FR-128)., Record support for a completion claim (PRD FR-132)., Report a milestone. Visible in the Tasks screen (PRD FR-131). (+21 more)

### Community 1 - "Task State Machine"
Cohesion: 0.05
Nodes (54): BaseModel, What a runner reports when it returns., TaskOutcome, assert_transition(), can_transition(), InvalidTransitionError, Exception, An attempt was made to move a task between incompatible states. (+46 more)

### Community 2 - "Shared Common Primitives"
Cohesion: 0.10
Nodes (35): LookupError, from_iso(), json_dumps(), json_loads(), Any, datetime, Small shared primitives used across every layer. Kept deliberately tiny:…, Timezone-aware current time. Never use ``datetime.utcnow()``. (+27 more)

### Community 3 - "Audit Log Writer"
Cohesion: 0.08
Nodes (33): Audit logging and secret redaction., AuditLog, Any, datetime, Path, Append-only audit log with two sinks (ARCHITECTURE.md section 6.3). *…, Every record from the JSONL file, oldest first., Search the SQLite index. Falls back to the JSONL file if unavailable. (+25 more)

### Community 4 - "SQLite Database Layer"
Cohesion: 0.08
Nodes (29): Connection, Cursor, Row, Database, DatabaseError, Any, Exception, Path (+21 more)

### Community 5 - "Event Bus and Tool Registry"
Cohesion: 0.08
Nodes (27): EventBus, Thread-safe publish/subscribe with subclass matching., Typed event bus and the domain event vocabulary., JSON schemas the planner is offered. Nothing outside this list exists., Holds every tool the runtime may call. Nothing else can., ToolRegistry, approving_invoker(), audit() (+19 more)

### Community 6 - "Worker Thread Supervisor"
Cohesion: 0.07
Nodes (19): ABC, WorkerStateChanged, PeriodicWorker, BaseException, Worker threads and their supervisor (PRD NFR-003, ARCHITECTURE.md section 4.1).…, Calls a function on an interval until stopped., Starts and stops workers in a defined order., Stop in reverse order. Returns the names that stopped cleanly. (+11 more)

### Community 7 - "Tool Contract Definition"
Cohesion: 0.11
Nodes (34): BaseModel, Enum, Exception, str, The tool contract (PRD section 13.2). A *tool* is the only way the agent…, Per-invocation context handed to a tool. Carries no ambient authority., What a tool returns on success., Raised by a tool to report a declared failure. The code must be declared. (+26 more)

### Community 8 - "Prohibited Tool Guards"
Cohesion: 0.09
Nodes (35): ToolRegistered, Protocol, What an implementation must provide., Tool, assert_tool_id_permitted(), check_tool_id(), ProhibitedToolError, Exception (+27 more)

### Community 9 - "Tool Invoker Pipeline Tests"
Cohesion: 0.14
Nodes (36): A proposed action. Comes from the planner, the GUI, a skill or a schedule., ToolCall, allow(), make_tool(), The six-step invoker pipeline (PRD section 13.4, ARCHITECTURE.md 6.6)., ADR-0010: silence is never consent., A tool cannot invent a vague error., PRD FR-048 and AT-018: 'I clicked it' is not 'it worked'. (+28 more)

### Community 10 - "Config Schema Models"
Cohesion: 0.10
Nodes (30): field_validator, AudioConfig, _Base, ConversationLanguageConfig, DefaultPermissionPolicy, LanguageConfig, LlmConfig, LoggingConfig (+22 more)

### Community 11 - "Ollama Health Check"
Cohesion: 0.08
Nodes (25): is_loopback_url(), OllamaHealthChecker, Exception, True when the URL's host is a loopback address or resolves only to one., Checks the local model runtime. Blocking; call it from a worker thread., fake_ollama(), _FakeResponse, Any (+17 more)

### Community 12 - "Resource Lock Events"
Cohesion: 0.10
Nodes (18): LockAcquired, LockContended, LockReleased, StaleLockReclaimed, _Contended, LockSetLease, Exception, Resource locks (PRD FR-124, section 7.1). Only one task may hold a given named… (+10 more)

### Community 13 - "Phase 0 Exit Criteria"
Cohesion: 0.09
Nodes (24): JarvisCore, Everything except the user interface., Phase 0 exit criteria and hard constraints. One test (or small group) per…, Phase 0 registers exactly one tool, and it changes nothing., PRD section 13.4: free-form text can never be executed., PRD section 4.4: nothing may silently become permanent memory., test_every_tool_declares_the_full_prd_13_2_contract(), test_exit_2_only_overrides_are_persisted() (+16 more)

### Community 14 - "Single Instance Guard"
Cohesion: 0.08
Nodes (20): BaseException, Path, Remove a lock file whose owning process is gone., Acquire once at startup; release at shutdown. ``acquired`` is the only thing…, SingleInstanceGuard, test_single_instance_enforcement_blocks_a_second_core(), Single-instance guard, workers and schema migrations., test_a_lock_file_from_a_dead_process_is_reclaimed() (+12 more)

### Community 15 - "Domain Event Types"
Cohesion: 0.15
Nodes (27): AppStarted, AppStopping, ConfigChanged, EmergencyStopCompleted, EmergencyStopRequested, Event, HealthChecked, NetworkModeChanged (+19 more)

### Community 16 - "Permission Engine Tests"
Cohesion: 0.10
Nodes (27): PermissionRequest, A question put to the permission engine. Contains no side effects., test_exit_5_permission_decisions_are_deterministic_and_inspectable(), No grant, setting or approval can reach past the prohibited check., test_prohibited_capability_is_always_denied_regardless_of_grants(), Permission evaluation (PRD sections 9.9 and 11.1, ARCHITECTURE.md 6.4)., A user who denied something should not be asked again in the same scope., PRD 11.1: fresh confirmation every time. (+19 more)

### Community 17 - "Tool Subsystem Entry Points"
Cohesion: 0.12
Nodes (19): new_id(), A fresh opaque identifier. UUID4 hex, no dashes, stable length., Tool contract, allow-list registry, prohibited guard and the invoker. This…, The tool invoker — the single choke point (ARCHITECTURE.md section 6.6). PRD…, ApprovalOutcome, ApprovalPort, ApprovalRequest, DenyingApprovalPort (+11 more)

### Community 18 - "Vault Path Layout"
Cohesion: 0.13
Nodes (7): Path, Instance-scoped files such as the single-instance lock., Create the vault layout. Idempotent., Every path the application is allowed to write to, derived from one root., VaultPaths, default_log_path(), Path

### Community 19 - "Secret Redaction"
Cohesion: 0.12
Nodes (24): classify_content(), is_content_key(), is_secret_key(), Any, Secret redaction for the audit log (PRD section 11.5, FR-259). Redaction…, Return a copy of ``value`` safe to persist in the audit log. Mappings,…, Describe a value without reproducing it. Used where the *shape* of user content…, Redact secret-looking substrings, then bound the length. (+16 more)

### Community 20 - "System Tray Icon"
Cohesion: 0.10
Nodes (14): ActivationReason, QAction, QMenu, QSystemTrayIcon, JarvisTrayIcon, QObject, Tray presence, state indication and quick controls., test_available_entries_are_enabled() (+6 more)

### Community 21 - "Tool Invocation Results"
Cohesion: 0.18
Nodes (10): ToolInvocationFinished, ToolInvocationStarted, The invoker's typed answer. Success requires verification., True only when the tool ran *and* confirmed its effect., ToolResult, Any, BaseModel, Record the user's decision so a broader scope is honoured next time. (+2 more)

### Community 22 - "Core Lifecycle and Crash Recovery"
Cohesion: 0.13
Nodes (24): _new_core(), Full core lifecycle, crash recovery and settings durability., Phase 0 exit criterion., PRD NFR-011: no consequential action is repeated after a restart., Kill the process the way a crash does: threads gone, nothing cleaned up.…, simulate_crash(), test_a_clean_start_reports_nothing_to_recover(), test_a_completed_task_is_never_re_run_after_recovery() (+16 more)

### Community 23 - "Permission Evaluation Engine"
Cohesion: 0.14
Nodes (18): _canonical_folder(), _folder_contains(), Permission evaluation (ARCHITECTURE.md section 6.4). The engine answers one…, Normalise a folder scope reference for prefix comparison. Phase 0 handles…, Decision, GrantScope, PermissionError, ProhibitedCapabilityError (+10 more)

### Community 24 - "Shell UI Tests"
Cohesion: 0.09
Nodes (21): fixture, Tray, main window and the Qt event bridge. Runs under…, No placeholder screen may look like it works (ADR-0010, PRD section 1.10)., PRD FR-001: Jarvis stays functional when the main window is closed., PRD NFR-033: do not rely on colour alone., ADR-0010: visible, disabled, honest — never hidden and never faked., test_about_states_the_phase_and_the_absence_of_a_shell(), test_all_fifteen_prd_navigation_areas_are_present() (+13 more)

### Community 25 - "Tray State Icons"
Cohesion: 0.12
Nodes (15): QColor, QIcon, Enum, str, Tray state icons, drawn programmatically. Two reasons not to ship image files:…, PRD section 9.1 tray states., A non-colour distinguishing mark (PRD NFR-033)., Render the icon for a state. Colour *and* shape differ per state. (+7 more)

### Community 26 - "Config Store Persistence"
Cohesion: 0.18
Nodes (14): _atomic_write(), deep_merge(), _delete_by_path(), _env_overrides(), _get_by_path(), _parse_env_value(), Any, Layered configuration loading and override-only persistence (ADR-0006).… (+6 more)

### Community 27 - "Permission Grants"
Cohesion: 0.17
Nodes (8): PermissionEngine, Record a permission decision. Validates the permission model first., Revoke every grant tied to a session. Called at shutdown., Evaluates capability requests against persisted grants., PermissionGrant, A recorded permission decision that may apply to future requests., test_grants_persist_across_engine_instances(), test_session_grants_get_a_ttl()

### Community 28 - "Configuration Tests"
Cohesion: 0.09
Nodes (12): Path, Layered configuration (ADR-0006)., PRD FR-039: 12 GB VRAM cannot hold two heavy models at once., PRD 11.1: high risk is always 'ask'; the schema will not accept otherwise., Phase 0 exit criterion: settings persist., PRD FR-036: the configured voice must be a real selection, not a fallback., test_a_fallback_only_voice_cannot_be_the_primary(), test_deep_merge_merges_mappings_and_replaces_scalars() (+4 more)

### Community 29 - "CI Security Invariants"
Cohesion: 0.16
Nodes (19): QT_QPA_PLATFORM=offscreen in CI, CI security-invariants job, CI test job (Windows + Ubuntu, Python 3.11/3.12), Capability Catalogue (risk classification as data), Architectural Change Control, Closed Capability Set (no generic execution primitive), Six-Layer Dependency Model (L0-L5), tests/security/test_no_shell.py (AST scan of src/) (+11 more)

### Community 30 - "Main Window Shell"
Cohesion: 0.22
Nodes (4): QMainWindow, MainWindow, Navigation shell over live core state., Closing the window leaves Jarvis running in the tray (PRD FR-001).

### Community 31 - "Application Composition Root"
Cohesion: 0.14
Nodes (5): JarvisApplication, QObject, Derive the tray state from what the runtime is actually doing., Composition of core, tray and window., Runs on the Qt main thread, courtesy of the bridge.

### Community 32 - "Backlog Structure and Sizing"
Cohesion: 0.12
Nodes (18): ARCHITECTURE.md, Subsystem area codes (CFG, COR, SEC, TSK, AUD, LLM, ...), Cross-phase invariants, DATA_MODEL.md, S/M/L/XL effort sizing (not time), Project Jarvis Implementation Backlog, Invariant: phase exit criteria must be demonstrated, Invariant: no generic execution primitive (+10 more)

### Community 33 - "Search and Browser Isolation ADRs"
Cohesion: 0.16
Nodes (18): ADR-0018: Search Provider, Option C: Ask a Configured AI Website (FR-055), Untrusted Web Content Wrapping (FR-054), Visible Brave Search Mode (FR-052), ADR-0019: Browser Profile Isolation, CAPTCHA Pause-and-Ask Requirement (FR-058), Dedicated Jarvis Brave Profile, Option C: Playwright Bundled Chromium Persistent Context (+10 more)

### Community 34 - "Config Package Paths"
Cohesion: 0.15
Nodes (15): MonkeyPatch, PathLike, Configuration layer (L1). Must not import anything above L1., expand_path(), find_defaults_config(), _platform_default_root(), Data-vault path resolution. This is the *only* module permitted to expand…, Locate the shipped ``defaults.yaml``. Order: ``JARVIS_DEFAULTS_CONFIG`` env… (+7 more)

### Community 35 - "Adapters and Automation Scope"
Cohesion: 0.15
Nodes (18): Google Antigravity IDE Adapter, Application Catalogue and Aliases, Automation Worker, Dedicated Jarvis Brave Profile, Phased Delivery Plan (Phase 0-6), Deterministic Before Visual (Automation Hierarchy), Local Document Understanding, Executor Role (+10 more)

### Community 36 - "Task Crash Recovery"
Cohesion: 0.18
Nodes (13): TaskRecovered, Task subsystem (L3): state machine, durable store, locks, scheduler, recovery., close_instance(), _live_instance_ids(), Crash recovery (PRD FR-006, NFR-010, NFR-011, AT-011). On startup, work left…, Make orphaned tasks and locks safe. Never resumes anything., What startup recovery changed. Shown to the user, not swallowed., Record this launch so later launches can tell what died. (+5 more)

### Community 37 - "Diagnostics and Logging Setup"
Cohesion: 0.15
Nodes (14): ArgumentParser, Logger, QApplication, Diagnostics: application logging and, later, crash reporting., configure_logging(), Path, Structured application logging. Separate from the audit log. The audit log…, Configure the root logger once. Idempotent. (+6 more)

### Community 38 - "Voice Audio Stack"
Cohesion: 0.16
Nodes (16): Audio Worker, English-Only Language Policy, faster-whisper STT Engine, First-Run Onboarding Wizard, .jarvispack Portable Identity Package, Local Speech-to-Text, Local Text-to-Speech, openWakeWord Model Runtime (+8 more)

### Community 39 - "Agent Roles and Capability Risk"
Cohesion: 0.16
Nodes (16): Capability Risk Classes, Conversation Agent Role, Filesystem Tool Root Scoping, Windows Known Folder Resolution, Memory Curator Role, Product Non-Goals, Planner Role, Prohibited Broad Tools (+8 more)

### Community 40 - "Phase 0 Core Work Items"
Cohesion: 0.22
Nodes (15): EventBridge, Invariant: state-changing tools declare reversibility metadata, LockManager, P0-CFG-01 Layered typed configuration, P0-CFG-03 SQLite storage and versioned forward migrations, P0-COR-01 Typed event bus, P0-COR-02 Tool contract: ToolSpec with reversibility metadata, P0-LLM-01 Ollama health check (loopback-only, offline-aware) (+7 more)

### Community 41 - "Navigation Areas and Placeholders"
Cohesion: 0.27
Nodes (8): QWidget, NavArea, _NotImplementedPanel, Main window: the fifteen navigation areas of PRD section 9.3. Six areas are…, A heading, a refresh button and a read-only text area., Says exactly what is missing and when it arrives. Never a fake screen., _TablePanel, _TextPanel

### Community 42 - "Permission Model Specification"
Cohesion: 0.18
Nodes (15): Approval dialog required fields, Capability risk classification (low/medium/high/prohibited), Permission decision types, Permission model, Prohibited capability class, Over-Permission (OP) category, Open question: detecting a spoofed window, T-023 Session grant exercised beyond the prompting request (+7 more)

### Community 43 - "Config Store Tests"
Cohesion: 0.18
Nodes (8): ConfigStore, Path, Loads, validates and persists configuration. Only the *difference from…, The persisted overrides only, i.e. the diff from shipped defaults., _read_yaml_mapping(), test_environment_override_is_not_persisted(), test_environment_values_are_parsed_as_yaml_scalars(), test_environment_variables_override_files()

### Community 44 - "Layering Enforcement Test"
Cohesion: 0.26
Nodes (14): _imported_modules(), _module_name(), _package_of(), Path, Layering invariants (ARCHITECTURE.md section 5, ADR-0004). The rule that makes…, A fresh interpreter can import the whole engine with no Qt module loaded., Qt belongs to the presentation layer: ``jarvis.ui`` and the entrypoint.…, Spelled out separately because it is the invariant people break first. (+6 more)

### Community 45 - "Event Bus Tests"
Cohesion: 0.20
Nodes (14): _app_started(), Typed event bus (ADR-0005)., The audit log and the GUI both subscribe; one must not break the other., test_a_failing_handler_does_not_break_the_publisher_or_others(), test_a_subscriber_does_not_receive_unrelated_events(), test_events_are_immutable(), test_events_carry_identity_and_time(), test_publishing_a_non_event_is_rejected() (+6 more)

### Community 46 - "Phase 1-2 App and Browser Items"
Cohesion: 0.20
Nodes (14): P1-APP-01 Application launcher with launch verification, P2-BRW-01 Dedicated persistent Jarvis Brave profile, P2-BRW-02 Playwright visible-browser, DOM-first execution, P2-BRW-08 YouTube search and indexed result selection, P2-FS-01 Windows Known Folder resolution, P2-FS-06 Filesystem scoping and path validation, P2-WIN-02 UI Automation inspector, P2-WIN-04 Input ownership via foreground_desktop lock (+6 more)

### Community 47 - "Closed Capability Set ADRs"
Cohesion: 0.18
Nodes (14): One SQLite Connection Per Thread, ADR-0003: A Closed Capability Set — No Generic Execution Primitive, No Generic Execution Primitive, os.startfile Named Future Allow-Listed Exception, tests/security/test_no_shell.py Source Tree Scan, Tool Registry Identity and Pattern Denylist, ADR-0004: Single Process, Thread Isolation for Phases 0–3, Layering Rule: Core Packages Must Not Import PySide6 (+6 more)

### Community 48 - "No-Shell Security Test"
Cohesion: 0.25
Nodes (13): _findings(), parametrize, Path, The load-bearing security test (ADR-0003). Phase 0 exit criterion: *no generic…, No shipped module may start a process or evaluate generated code., A guard on the guard: prove the detector is not vacuously passing., The denylist module names these primitives in patterns; that must be fine., No function or class in the runtime is named after a prohibited tool. (+5 more)

### Community 49 - "Core Phase Work Items"
Cohesion: 0.21
Nodes (13): JarvisCore, P0-COR-04 Tool invoker six-step pipeline, P0-COR-08 Emergency stop, P0-SEC-03 Permission engine, P0-UI-01 PySide6 tray and main window shell, P1-SEC-01 Approval dialog UI replacing DenyingApprovalPort, P2-BRW-06 Untrusted web-content wrapping and prompt-injection test, P5-IDE-05 IDE permission boundary (no automatic approval) (+5 more)

### Community 50 - "Python-First Shell ADR"
Cohesion: 0.22
Nodes (13): ADR-0001: Python-First Implementation with Rust Deferred, Python 3.11 + PySide6 Implementation Stack, Qwen3-TTS Isolated Python 3.12 Worker, Rust/Tauri Native Shell Deferred Past Phase 3, Authenticated Typed IPC for Future Shell, Process-Separation Promotion Triggers, Helper IPC Discipline (Named Pipe or Loopback, Rotating Token), No Interaction with the Windows Secure Desktop or UAC Prompt (+5 more)

### Community 51 - "SQLite Source of Truth ADR"
Cohesion: 0.23
Nodes (13): ADR-0002: SQLite as the Single Source of Truth, Large Binary Artefacts Stored on Disk, Referenced by Path, Derived Rebuildable Stores Hold No Unique Information, SQLite (jarvis.db) Canonical Transactional Store, WAL Mode Concurrent Readers, ADR-0005: An In-Process Typed Event Bus, Bus Is Notification, Not System of Record, ADR-0006: Layered Configuration with Override-Only Persistence (+5 more)

### Community 52 - "Migrations and Event Models"
Cohesion: 0.17
Nodes (13): Versioned Forward-Only Migrations, Full ORM (SQLAlchemy) Rejected for Phase 0, Schema-Version Startup Check (Newer DB is Hard Failure), jarvis.core.events In-Process Publish/Subscribe Bus, Frozen Pydantic Event Models with Subclass Matching, Per-Handler Exception Isolation, ConfigChanged Runtime Event, pydantic extra="forbid" Loud Typo Failure (+5 more)

### Community 53 - "Export, Retention and Keys"
Cohesion: 0.19
Nodes (13): No Shared API Keys Constraint (§18.3), Option B: Optional User-Supplied Search API Key, Portable Identity Export (FR-168), Secret Exclusion from Normal Exports (FR-169/FR-170), Audit Log as a Safety Record, Clipboard History Retention (FR-253), Option C: One Global Retention Period, Option A: Keep Everything Until User Deletes (+5 more)

### Community 54 - "Threat Model Taxonomy"
Cohesion: 0.23
Nodes (13): Closed authority set for tool authorisation, Security Policy and Control Specification, Untrusted-data rule, The LLM as a confused deputy, Malicious web content author, Prompt Injection (PI) category, STRIDE threat classification, T-001 Web page text instructs Jarvis to act (+5 more)

### Community 55 - "Qt Event Bridge"
Cohesion: 0.18
Nodes (8): Deliver to every matching handler. Returns the number invoked. Handler…, TaskStateChanged, EventBridge, QObject, Re-emits domain events as Qt signals on the GUI thread., test_detaching_the_bridge_stops_delivery(), test_the_bridge_marshals_events_published_from_another_thread(), test_the_bridge_re_emits_domain_events_as_qt_signals()

### Community 56 - "Capability Catalogue"
Cohesion: 0.23
Nodes (11): _c(), capabilities_by_risk(), capability(), capability_ids(), The capability catalogue — PRD section 11.1 expressed as data. Risk…, Permission model, capability catalogue and evaluation engine., Capability, One thing the agent might be permitted to do. (+3 more)

### Community 57 - "Config and Composition Invariants"
Cohesion: 0.27
Nodes (12): CI headless self-check step (jarvis.main --check), Layered Configuration System (jarvis.config), extra=forbid Everywhere, JarvisCore (composition root), Override-Only Persistence, Only L5 May Import PySide6, Single-Instance Guard, VaultPaths (centralised path resolution) (+4 more)

### Community 58 - "Architecture Drivers and LLM Boundary"
Cohesion: 0.17
Nodes (12): Architectural Drivers, Typed In-Process Event Bus (jarvis.core.events), EventBridge (domain events to queued Qt signals), LLM Boundary (jarvis.llm), Loopback-Only Ollama Endpoint, Model Output Is Untrusted Input, Planner Cannot Skip the Invoker, Qt Main Thread Must Not Block (+4 more)

### Community 59 - "Process Isolation Limits"
Cohesion: 0.17
Nodes (12): Bounded Timeouts and Declared Retry Policy, In-Process Isolation Is Not a Security Boundary, Deferred Process Separation (TTS worker, elevation helper), Single-Process Multi-Thread Model, Task Scheduler (jarvis.tasks.scheduler), Phase 0 Known Limitations, tasks scheduler settings, audio.text_to_speech profiles (+4 more)

### Community 60 - "Task Store and Network Modes"
Cohesion: 0.24
Nodes (12): Crash Recovery, Offline Mode Enforced at the Adapter Boundary, Ten-State Task Machine (jarvis.tasks.states), Task Store (jarvis.tasks.store), ToolResult (typed outcomes), Success Requires Verification, network.mode (offline / local_assistant / connected), task_checkpoint table (+4 more)

### Community 61 - "No Generic Execution Primitive"
Cohesion: 0.21
Nodes (12): Closed Enumerated Set of Narrow Typed Tools, Emergent Capability From Tool Composition (Residual Risk), Hard Ceiling on Prompt Injection Impact, Sandboxed Generic Shell Rejected, ToolSpec Typed Tool Contract, Thread Isolation Is Not a Security Boundary (Gap 2), Ollama Endpoint Squatting (Unmitigated Residual Risk), Local Authenticating Proxy for Ollama Not Adopted (+4 more)

### Community 62 - "Five-Component Process Model"
Cohesion: 0.23
Nodes (12): Emergency Stop, Jarvis Core (Orchestration), Jarvis Shell (GUI Process), Authenticated Loopback IPC, PySide6 Desktop Shell Toolkit, Python 3.11 as V1 Implementation Language, Resource Lock Model, Task Checkpoints and Durability (+4 more)

### Community 63 - "Ollama Health Adapter"
Cohesion: 0.20
Nodes (7): NetworkMode, str, OllamaHealth, Ollama health check (ADR-0007). Two boundary rules are enforced here rather…, The result of one check. Never claims health it did not observe., Ollama adapter. Phase 0 implements only the health check., Check the local model runtime. Runs on a worker thread.

### Community 64 - "Phase 1+ Security Controls"
Cohesion: 0.18
Nodes (11): Audit log requirements (append-only, redacted), .jarvispack normal-export secret exclusions, Deletion is non-destructive by default, Screen capture scoping and screenshot retention, Secrets storage via DPAPI / Credential Manager, Signed installers and update packages, Telemetry off by default with content exclusions, T-048 Secrets leak into audit log, crash dump, or telemetry (+3 more)

### Community 65 - "ToolSpec Schema Validation"
Cohesion: 0.18
Nodes (8): Any, model_validator, Schema the planner sees. Free-form text can never reach the invoker., Everything a tool declares about itself., ToolSpec, test_toolspec_cannot_declare_prohibited_risk(), End to end: a tool call carrying a secret leaves no secret behind., test_secrets_passed_to_a_tool_do_not_reach_the_audit_log()

### Community 66 - "Model Roles and Audio Settings"
Cohesion: 0.22
Nodes (10): Extension Points Table, Separate Model Roles (planner, vision, embeddings, STT, TTS), model_runtime (sequential load strategy), models.* role-to-profile mapping, audio.speech_to_text settings, audio.wake_word settings, faster-whisper Speech Recognition, Target Hardware Profile (+2 more)

### Community 67 - "Memory and Approval Design"
Cohesion: 0.20
Nodes (10): Approval Dialog Design, Consequential-Action Audit Log, IDE-Agent Orchestration, jarvis.db SQLite Single Source of Truth, Bounded Definition of Learning, Memory Candidate Review Pipeline, Memory Record Schema, No Silent Learning (+2 more)

### Community 68 - "Product Principles and Non-Goals"
Cohesion: 0.27
Nodes (10): Connected Mode (Optional External Providers), Honest Task Status, Local First, Not Local Only, Offline Mode, One Action, One Verification, Project Jarvis (Windows Local AI Desktop Agent), Task Completion Evidence, Tool-Grounded Success Claims (+2 more)

### Community 69 - "Phase 0 Security Status"
Cohesion: 0.24
Nodes (10): Approval port (deny by default), Layering enforcement test (no Qt below presentation), Ollama health check (loopback-only), Phase 0 security status table, Tool invoker six-step pipeline (jarvis.core.tools.invoker), Typed event bus (jarvis.core.events), Hallucinated Success (HS) category, Open question: authenticating the Ollama endpoint (+2 more)

### Community 70 - "Filesystem Path Scoping"
Cohesion: 0.27
Nodes (10): Archive extraction protections, Absolutely denied filesystem targets, Root-scoped filesystem tools, Path canonicalisation before scope check, Phase-gated mitigation roadmap, T-038 Path traversal escapes the approved root scope, T-039 Symlink or NTFS junction escapes approved scope, T-040 TOCTOU path swap after scope validation (+2 more)

### Community 71 - "Prohibited Capability Enforcement"
Cohesion: 0.31
Nodes (10): Tool-invocation evaluation order, Static src/ scan for prohibited primitives, Named prohibited broad tools, Tool registry registration denylist, T-010 Self-injection via Jarvis's own prior output, T-011 Model invents a nonexistent tool name, T-012 Model requests a shell/code-execution tool, T-014 Valid tool call with out-of-scope parameters (+2 more)

### Community 72 - "Lock Contention Threats"
Cohesion: 0.22
Nodes (10): Resource locks (jarvis.tasks.locks), Open question: hardening %LOCALAPPDATA% ACLs at startup, Other local Windows users, T-028 Two tasks race for the foreground desktop-control lock, T-030 Foreground lock not released after Automation Worker crash, T-034 Consequential action replayed after restart, T-052 Another local Windows user reads the SQLite vault, T-067 Clipboard capture records a password or TOTP code (+2 more)

### Community 73 - "Concurrency and Schema Invariants"
Cohesion: 0.22
Nodes (9): Concurrency Invariants, Resource Locks (jarvis.tasks.locks), SQLite Concurrency Strategy (WAL, per-thread connections), Forward-Only Transactional Migrations, resource_lock table, runtime_instance table, schema_migration table, SQLite Is the Single Source of Truth (+1 more)

### Community 74 - "Deferred Vision Work Items"
Cohesion: 0.31
Nodes (9): ADR-0001 Python-first shell (native Rust/Tauri deferred), ADR-0009 Scoped elevation helper interface, Deferred beyond Version 1, P4-LLM-01 Model resource scheduler (sequential loading, VRAM checks), P4-VIS-01 Qwen3-VL vision model route, P4-VIS-02 Screenshot grounding and UIA-plus-vision fusion, P4-VIS-03 Vision action verification, P4-WIN-05 Security-settings boundary and scoped elevation helper (+1 more)

### Community 75 - "VRAM Scheduler and Embeddings"
Cohesion: 0.28
Nodes (9): Model Resource Scheduler (FR-039), Option A: Strict Mutual Exclusion Scheduling, Option B: VRAM-Budget-Aware Co-Residency, ADR-0017: Embedding Model, Option B: Dedicated Retrieval-Purpose-Built Embedding Model, Embedding Invocation Frequency Cost, Option C: First-Run Wizard Hardware Benchmark, qwen3-embedding:0.6b Tentative Default (+1 more)

### Community 76 - "Event Subscriptions"
Cohesion: 0.25
Nodes (4): E, Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe., Receive ``event_type`` and every subclass of it., Subscription

### Community 77 - "TTS Providers and Model Routing"
Cohesion: 0.31
Nodes (9): Kokoro TTS Provider, Model Resource Scheduler (VRAM Arbitration), Per-Role Model Routing, Ollama Local Model Runtime, Piper TTS Provider, qwen3:8b Planner/Conversation Model, Qwen3-TTS Expressive Provider, qwen3-vl Vision Model Route (+1 more)

### Community 78 - "Runtime Composition Layer"
Cohesion: 0.25
Nodes (7): RuntimeError, Runtime composition (L4). Wires L1-L3 together; imports no GUI code., AlreadyRunningError, _process_is_alive(), Single-instance enforcement (PRD FR-005). Only one interactive Jarvis may run…, Is a process with this id currently running? ``os.kill(pid, 0)`` is the POSIX…, Another instance already holds the single-instance handle.

### Community 79 - "Config Validation Errors"
Cohesion: 0.22
Nodes (7): AppConfig, The whole validated configuration tree., ConfigError, Exception, Configuration could not be loaded, validated or saved., test_configuration_is_typed_and_rejects_unknown_keys(), test_shipped_defaults_validate()

### Community 80 - "ADR Coverage Tests"
Cohesion: 0.22
Nodes (9): parametrize, Path, Screenshot-based computer control is out of scope for Phase 0., No autonomous self-modification: every write path targets the vault., PRD section 25 lists sixteen open decisions., test_an_adr_exists_for_every_prd_open_decision(), test_no_screenshot_or_input_automation_module_exists(), test_required_documents_and_config_exist() (+1 more)

### Community 81 - "No Elevation Test"
Cohesion: 0.31
Nodes (6): Path, Non-administrator operation (PRD FR-003, NFR-020, ADR-0009). Phase 0 must run…, Any packaging manifest must be asInvoker., _relative(), test_no_manifest_declares_an_elevated_execution_level(), test_no_module_requests_elevation()

### Community 82 - "Approval Port and Grant Scopes"
Cohesion: 0.36
Nodes (8): ApprovalPort, DenyingApprovalPort (silence is never consent), Grant Scopes (ONCE, SESSION, TASK, APPLICATION, FOLDER, ALWAYS), Permission Engine (jarvis.core.permissions), Single Choke Point for Tool Execution, ToolInvoker (six-step pipeline), permissions.default_policy, permission_grant table

### Community 83 - "Default Voice ADRs"
Cohesion: 0.39
Nodes (8): ADR-0014: Default English Voice, Kokoro bm_george Default Voice, Windows SAPI Emergency Fallback, ADR-0015: Additional TTS Providers, No Silent Voice Provider Switching (FR-036), Qwen3-TTS Isolated Python 3.12 Worker, Provider-Neutral TtsProvider Interface, Update Rollback and Schema Compatibility Checks

### Community 84 - "MSIX and Plugin Signing ADRs"
Cohesion: 0.32
Nodes (8): espeak-ng GPL-Family Licensing Consideration, ADR-0020: Plugin and Skill Signing, ADR-0022: MSIX Distribution, Option A: MSIX as Primary Distribution Format, Option B: MSIX as Secondary Optional Channel, MSIX Sandboxing vs Desktop Automation Tension, Automation Worker Adversarial Input Exposure, ADR-0026: Code-Signing and Update Infrastructure

### Community 85 - "Wake Word and Voice Licensing"
Cohesion: 0.29
Nodes (8): Per-Download Provider and Licence Disclosure, Voice Pack Redistribution Licensing Gap, ADR-0016: Custom Jarvis Wake Word, Option A: Purpose-Trained Custom Jarvis Wake Model, False-Activation Evaluation Harness, Hey Jarvis Interim Wake Phrase, Push-to-Talk Global Hotkey Fallback, Expired Screenshot Evidence Must Degrade Honestly

### Community 86 - "Code Signing Certificate Options"
Cohesion: 0.36
Nodes (8): Option C: Project-Operated Signing Authority, Option B: Self-Signed Developer Keys, Skill Manifest signed Field, Option B: EV Certificate with Optional Automatic Checks, Option A: OV Certificate with Manual Update Checks, Signature Verification Precedes Execution, SmartScreen Reputation Barrier, Update Package Format and Manifest Schema

### Community 87 - "IPC and Elevation Boundaries"
Cohesion: 0.25
Nodes (8): Emergency stop surface, Local IPC requirements (loopback, per-install token), Non-admin by default, Five-component process model, Scoped elevation helper process, Secure desktop and UAC prompts off-limits, TTS worker isolation (Qwen3-TTS, separate env), T-053 Unauthenticated loopback port accepts local tool calls

### Community 88 - "UI Settings and CI Licence Job"
Cohesion: 0.29
Nodes (7): CI dependency and licence review job, Emergency Stop, Honest Degraded UI (disabled, not hidden, not fake), Jarvis Shell (jarvis.ui tray and main window), ui settings (tray start, show_unavailable_features, emergency hotkey), Entities Defined But Not Yet Built, No Bundled Third-Party Assets

### Community 89 - "Dual-Sink Audit Design"
Cohesion: 0.43
Nodes (7): Dual-Sink Append-Only Audit Log (jarvis.core.audit), Redaction Before Serialisation, logging settings (audit_to_sqlite, max_audit_value_chars), audit_event table, Export and Import Constraints, Ten Persisted Integrity Invariants, Two Audit Sinks, One Record of Truth

### Community 90 - "Phase 3 Memory Work Items"
Cohesion: 0.43
Nodes (7): P2-WIN-03 Automation worker thread (pywinauto UIA backend), P3-CLP-01 Clipboard permissions and operations, P3-MEM-01 Memory candidate pipeline with review queue and provenance, P3-MEM-03 Forget with cascade delete from derived indexes, P3-MEM-06 Portable identity export/import (.jarvispack) with secret exclusion, P3-TSK-02 Pause/resume with mandatory state re-observation, Phase 3 — Tasks, macros, and memory

### Community 91 - "Secret Storage Candidates"
Cohesion: 0.38
Nodes (7): ADR-0008: Secret Storage Deferred to Phase 1, jarvis.core.audit.redaction Defence-in-Depth Backstop, Windows Credential Manager CredWrite/CredRead (Candidate Mechanism), DPAPI CryptProtectData via ctypes (Candidate Mechanism), Encrypted SQLite Table with DPAPI-Wrapped Key (Candidate Mechanism), No Secret Store Implemented in Phase 0, Secrets Excluded From Normal Exports

### Community 92 - "Installer Technology ADR"
Cohesion: 0.29
Nodes (7): No Elevation Manifest Security Check (asInvoker), Application Never Runs Permanently as Administrator, ADR-0013: Installer Technology, Installer Choice Sequenced Behind the MSIX Decision, NSIS (Candidate Installer), Per-User Install with No UAC Elevation, WiX Toolset MSI (Candidate Installer)

### Community 93 - "Honest Degraded UI ADR"
Cohesion: 0.29
Nodes (7): ADR-0010: Honest Degraded UI Over Fake Functionality, Unavailable Features Shown Disabled with a Phase Tooltip, Never Claim Unverified Success, Programmatically Drawn QPainter Tray Icons, ADR-0011: Public Product Name, "Jarvis" as Internal Codename Only, Trademark and Identifier Availability Criteria

### Community 94 - "Backup and Retention ADRs"
Cohesion: 0.33
Nodes (7): Rebuildable Derived Index Constraint, ADR-0021: Encrypted Sync and Backup, Option A: Local Backup Only, No Network Transport, Off-Device Backup Compromise Surface, Option B: User-Supplied Cloud Storage with Client-Side Encryption, ADR-0024: Data Retention Defaults, Cascade Deletion of Derived Data (FR-167)

### Community 95 - "Kokoro TTS Script"
Cohesion: 0.38
Nodes (6): ndarray, generate_voice_sample(), main(), normalise_audio(), Path, Convert Kokoro output into a one-dimensional NumPy array.

### Community 96 - "Jarvis Application Icon"
Cohesion: 0.52
Nodes (7): Jarvis Application Icon (Arc Reactor Mark), Arc Reactor Visual Motif, Circular Metallic Chassis Ring, Cyan-on-White Emissive Palette, Jarvis Product Brand Identity, Transparent Alpha Square Canvas, Inverted Triangular Glowing Core

### Community 97 - "Package Entry Points"
Cohesion: 0.29
Nodes (4): Project Jarvis — local-first Windows desktop AI agent. "Jarvis" is an internal…, Enum, Task state machine (PRD FR-122). Every transition is validated against an…, System tray icon and menu (PRD sections 9.1 and 9.2). Menu entries whose…

### Community 98 - "Phase 1 Voice Work Items"
Cohesion: 0.47
Nodes (6): P1-AUD-01 Wake-word detection (openWakeWord), P1-AUD-05 Local STT (faster-whisper), P1-AUD-07 Local TTS (Kokoro), P1-AUD-10 Expressive TTS worker isolation prototype (Qwen3-TTS), P1-SEC-02 DPAPI-backed secret store, Phase 1 — Voice-first local assistant

### Community 99 - "Loopback Trust Boundary ADR"
Cohesion: 0.33
Nodes (6): ADR-0007: Ollama Loopback-Only Trust Boundary, Loopback-Only Base URL Enforcement at the Adapter, Offline Mode Enforced at the Adapter Boundary, DenyingApprovalPort Default Implementation, Inno Setup (Candidate Installer), Uninstall-Time Data Deletion Must Be Opt-In

### Community 100 - "Supply Chain Threats"
Cohesion: 0.40
Nodes (6): Dependency and licence scanning CI gate, Compromised or typosquatted Python dependency, Residual risks accepted for Phase 0, T-060 DLL search-order hijacking of the packaged build, T-069 Malicious or typosquatted PyPI dependency, TB-10 Jarvis to Windows OS security boundary

### Community 101 - "Phase 6 Productisation Items"
Cohesion: 0.40
Nodes (5): P0-COR-03 Tool registry with identity and pattern denylist, P6-PKG-01 First-run onboarding wizard (steps 1-9), P6-PKG-03 Signed Windows x64 installer, P6-PKG-08 Plugin/adapter SDK groundwork, Phase 6 — Productisation

### Community 103 - "Process Component Inventory"
Cohesion: 0.40
Nodes (5): Audio Worker, Automation Worker, Jarvis Core (orchestration, permissions, audit), Jarvis Shell (PySide6 GUI and tray), Task Scheduler

### Community 104 - "Whisper STT Script"
Cohesion: 0.70
Nodes (4): list_audio_devices(), main(), record_audio(), transcribe_audio()

### Community 105 - "Privacy Retention Defaults"
Cohesion: 0.67
Nodes (4): privacy retention defaults, Retention and Deletion Rules, Soft References So Audit Survives Its Subject, Privacy Defaults (telemetry off, no raw audio)

### Community 106 - "Permission Evaluation Result"
Cohesion: 0.50
Nodes (3): PermissionEvaluation, BaseModel, The engine's answer. Never executes anything.

### Community 107 - "Tray Exit Criteria Tests"
Cohesion: 0.50
Nodes (4): PRD section 9.1 and NFR-033., test_exit_1_the_application_opens_and_provides_a_tray_presence(), test_exit_1_the_tray_communicates_state_without_relying_on_colour(), ui

### Community 108 - "Emergency Stop Tests"
Cohesion: 0.50
Nodes (4): test_emergency_stop_cancels_tasks_releases_locks_and_reports(), test_the_health_check_is_permission_checked_like_anything_else(), test_the_health_check_task_runs_through_the_whole_pipeline(), wait_for()

### Community 109 - "High Risk Permission Tests"
Cohesion: 0.50
Nodes (4): parametrize, PRD 9.9: high-risk permissions must not offer 'always allow'., test_high_risk_cannot_be_allowed_beyond_a_single_use(), test_risk_classification_matches_the_prd()

### Community 111 - "Vault Free Space Check"
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
- **48 isolated node(s):** `project-jarvis`, `openWakeWord Model Runtime`, `faster-whisper STT Engine`, `Jarvis Shell (PySide6 GUI and tray)`, `Audio Worker` (+43 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `T-030 Foreground lock not released after Automation Worker crash` and `T-034 Consequential action replayed after restart`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **What is the exact relationship between `Arc Reactor Visual Motif` and `Cyan-on-White Emissive Palette`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **What is the exact relationship between `"Jarvis" as Internal Codename Only` and `ADR-0012: Shell Technology for the First Public Build`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `JarvisCore` connect `Phase 0 Exit Criteria` to `Task Runner Contract`, `Shared Common Primitives`, `Audit Log Writer`, `SQLite Database Layer`, `Event Bus and Tool Registry`, `Worker Thread Supervisor`, `Tool Contract Definition`, `Tool Invoker Pipeline Tests`, `Ollama Health Check`, `Resource Lock Events`, `Single Instance Guard`, `Domain Event Types`, `Tool Subsystem Entry Points`, `Vault Path Layout`, `Tool Invocation Results`, `Core Lifecycle and Crash Recovery`, `Permission Grants`, `Main Window Shell`, `Application Composition Root`, `Task Crash Recovery`, `Diagnostics and Logging Setup`, `Navigation Areas and Placeholders`, `Config Store Tests`, `Ollama Health Adapter`, `Runtime Composition Layer`, `Config Validation Errors`, `ADR Coverage Tests`, `Settings Mutation Helpers`, `Emergency Stop Tests`, `Idempotent Shutdown`, `Health Check Task Queue`, `Self-Inspecting Grants`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `Database` connect `SQLite Database Layer` to `Shared Common Primitives`, `Audit Log Writer`, `Task Crash Recovery`, `Event Bus and Tool Registry`, `Worker Thread Supervisor`, `Tool Invoker Pipeline Tests`, `Resource Lock Events`, `Phase 0 Exit Criteria`, `Single Instance Guard`, `Domain Event Types`, `Tool Subsystem Entry Points`, `Tool Invocation Results`, `Core Lifecycle and Crash Recovery`, `Permission Evaluation Engine`, `Permission Grants`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `EventBus` connect `Event Bus and Tool Registry` to `Task Runner Contract`, `Shared Common Primitives`, `Audit Log Writer`, `Task Crash Recovery`, `Worker Thread Supervisor`, `Prohibited Tool Guards`, `Tool Invoker Pipeline Tests`, `Event Subscriptions`, `Phase 0 Exit Criteria`, `Resource Lock Events`, `Domain Event Types`, `Event Bus Tests`, `Tool Subsystem Entry Points`, `Qt Event Bridge`, `Tool Invocation Results`, `Permission Evaluation Engine`, `Permission Grants`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `JarvisCore` (e.g. with `VaultPaths` and `AppConfig`) actually correct?**
  _`JarvisCore` has 39 INFERRED edges - model-reasoned connections that need verification._