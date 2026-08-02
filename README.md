# Project Jarvis

A local-first Windows desktop AI agent. **Internal codename only** — "Jarvis" is
not the public product name (PRD section 1.16, ADR-0011).

> **Current state: Phase 0 — foundation and safety architecture.**
> There is no voice input or output, no desktop or browser automation, no
> filesystem tools, no screen capture and no clipboard access. What exists is
> the machinery those capabilities will have to pass through.

---

## What Phase 0 contains

| Subsystem | What it does |
|-----------|--------------|
| Configuration | Layered, typed, `extra="forbid"`; only overrides are persisted |
| Storage | SQLite vault with WAL, foreign keys and versioned migrations |
| Event bus | Thread-safe, typed, with isolated handlers |
| Audit log | Append-only JSONL plus a SQLite search index, redacted on the way in |
| Permission engine | Capability catalogue, risk classes, scoped grants, expiry, revocation |
| Tool pipeline | Allow-list → schema → permission → locks → approval → execute |
| Task subsystem | Ten-state machine, durable store, checkpoints, evidence, resource locks, scheduler |
| Crash recovery | Interrupted tasks paused for review; stale locks reclaimed |
| Shell | PySide6 tray with seven states, and a fifteen-area main window |
| Health | Loopback-only Ollama check that honours offline mode |

## What Phase 0 deliberately does not contain

No shell, Command Prompt, PowerShell, WSL or arbitrary-code execution — and a
build test fails if one is ever introduced (ADR-0003). No administrator mode. No
silent memory creation. No screenshot-based computer control.

---

## Requirements

- Windows 11 x64 (the engine also runs on Linux for CI)
- Python 3.11 or 3.12
- [Ollama](https://ollama.com) for the health check to report a reachable runtime

## Getting started

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Run the headless self-check:

```powershell
python -m jarvis.main --check
```

Run the tray application:

```powershell
python -m jarvis.main
```

Run the tests:

```powershell
python -m pytest
```

### Useful flags

| Flag | Purpose |
|------|---------|
| `--check` | Start the core, print a status report, exit. No GUI. |
| `--data-dir DIR` | Use a different data vault. |
| `--log-level LEVEL` | Override the configured log level. |
| `--allow-multiple-instances` | Development only; skips the single-instance guard. |

## Where your data lives

Default vault: `%LOCALAPPDATA%\ProjectJarvis`. Relocate it with `--data-dir` or
the `JARVIS_DATA_DIR` environment variable.

```
ProjectJarvis/
├── config/user.yaml     your overrides only; defaults come from config/defaults.yaml
├── data/jarvis.db       the single source of truth
├── logs/audit.jsonl     append-only audit record
├── logs/app.log         diagnostic logging
├── attachments/         screenshots, evidence, audio diagnostics (later phases)
├── browser/ models/ exports/ backups/ temp/ runtime/
```

Everything personal stays on this computer. Nothing leaves it unless a
capability you approved requires it, and the network mode makes that visible.

## Configuration

Three layers, merged deepest-first:

1. `config/defaults.yaml` — shipped, version-controlled
2. `%LOCALAPPDATA%\ProjectJarvis\config\user.yaml` — your overrides only
3. `JARVIS__SECTION__KEY` environment variables — development and test

A misspelt key is a startup error naming the exact path, not a silently ignored
value.

## Documentation

| Document | What it covers |
|----------|----------------|
| [PRD.md](PRD.md) | Product requirements — the source of truth |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Process model, layering, control flow, what exists today |
| [SECURITY.md](SECURITY.md) | Security policy and controls |
| [THREAT_MODEL.md](THREAT_MODEL.md) | STRIDE plus LLM-agent threat analysis |
| [DATA_MODEL.md](DATA_MODEL.md) | Schema, entities, retention, migrations |
| [docs/BACKLOG.md](docs/BACKLOG.md) | Phased implementation backlog, Phases 0–6 |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records |
| [CHANGELOG.md](CHANGELOG.md) | What changed |

## Development notes

**Layering.** Dependencies point downward only, and only `jarvis.ui` may import
PySide6. `tests/security/test_layering.py` enforces both. The consequence worth
knowing: the whole engine is importable and testable with no Qt at all.

**Adding a capability.** Write a narrow, typed tool in `jarvis/toolbox/`,
declare its capability in the catalogue with a risk level, and register it. There
is no generic execution path, and adding one fails the build.

**Tests.** `tests/unit`, `tests/security`, `tests/integration`, `tests/ui`
(offscreen Qt) and `tests/acceptance` (one test per Phase 0 exit criterion).
Every test gets an isolated vault; none needs Ollama, a microphone, a GPU or the
network.

## Licence and assets

Pre-release, not for redistribution. No third-party models, voices, icons or
copyrighted assets are bundled. Tray icons are drawn programmatically for
exactly this reason (PRD section 17.3).
