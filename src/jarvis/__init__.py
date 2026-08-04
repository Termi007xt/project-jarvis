"""Project Jarvis — local-first Windows desktop AI agent.

"Jarvis" is an internal codename only (PRD section 1.16). The public product
name is an open decision recorded in docs/decisions/ADR-0011-public-product-name.md.

Layering rule (ARCHITECTURE.md section 5), enforced by tests/security/test_layering.py:
only ``jarvis.ui`` may import PySide6.
"""

from __future__ import annotations

__all__ = ["APP_NAME", "APP_CODENAME", "APP_VERSION", "VAULT_DIR_NAME"]

APP_CODENAME = "Jarvis"
APP_NAME = "Project Jarvis"
APP_VERSION = "0.2.0.dev0"

#: Directory name used under %LOCALAPPDATA% for the data vault (PRD section 14.2).
VAULT_DIR_NAME = "ProjectJarvis"
