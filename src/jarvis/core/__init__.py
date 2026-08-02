"""Core layer (L2): events, audit, permissions and the tool machinery.

Must not import ``jarvis.tasks``, ``jarvis.llm``, ``jarvis.runtime``,
``jarvis.ui`` or PySide6 (ARCHITECTURE.md section 5, ADR-0004). Dependencies on
higher layers are expressed as protocols in ``jarvis.core.tools.ports``.
"""
