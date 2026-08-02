"""User interface layer (L5). The only package permitted to import PySide6."""

from __future__ import annotations

__all__ = ["JarvisApplication", "MainWindow", "JarvisTrayIcon", "TrayState", "EventBridge"]


def __getattr__(name: str) -> object:
    # Lazy so that importing jarvis.ui does not construct Qt types until needed.
    if name == "JarvisApplication":
        from jarvis.ui.app import JarvisApplication

        return JarvisApplication
    if name == "MainWindow":
        from jarvis.ui.main_window import MainWindow

        return MainWindow
    if name == "JarvisTrayIcon":
        from jarvis.ui.tray import JarvisTrayIcon

        return JarvisTrayIcon
    if name == "TrayState":
        from jarvis.ui.icons import TrayState

        return TrayState
    if name == "EventBridge":
        from jarvis.ui.qt_bridge import EventBridge

        return EventBridge
    raise AttributeError(f"module 'jarvis.ui' has no attribute '{name}'")
