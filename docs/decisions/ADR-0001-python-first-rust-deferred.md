# ADR-0001: Python-First Implementation with Rust Deferred

## Decision

Project Jarvis Version 1 will use Python 3.11.

Rust or Tauri may later replace the native application shell, but only after
Phase 3 and only if performance or distribution measurements justify it.

## Rationale

The selected AI, speech, browser automation, and Windows automation stack has
strong first-class Python support. Rewriting these integrations in Rust would
increase development and packaging complexity without materially reducing
model-inference latency.

## Consequences

- Phase 0 through Phase 3 use Python and PySide6.
- Core interfaces remain typed and process-compatible.
- Qwen3-TTS uses an isolated Python 3.12 worker if enabled.
- A future Rust shell must communicate through authenticated typed IPC.
- No Rust migration begins without measured acceptance criteria.
