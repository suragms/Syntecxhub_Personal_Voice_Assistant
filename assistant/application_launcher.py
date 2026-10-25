"""
application_launcher.py — Launches allowlisted Windows desktop applications.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# Allowlist: display name → executable (resolved via PATH or absolute).
ALLOWED_APPS: dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "settings": "ms-settings:",
    "task manager": "taskmgr.exe",
    "command prompt": "cmd.exe",
    "wordpad": "wordpad.exe",
    "snipping tool": "snippingtool.exe",
}

# Characters that could be used for shell injection
_ILLEGAL_CHARS = set("&|;`$<>")


class ApplicationLauncher:
    """Safely launches Windows desktop applications from an allowlist."""

    @staticmethod
    def launch(app_name: str) -> dict[str, Any]:
        """
        Launch *app_name* if it is in the allowlist.

        Returns a structured result dict with ``success``, ``message``,
        and ``app_name`` keys. Never raises — errors are returned as
        ``success: False`` results.
        """
        # --- Basic validation ----------------------------------------
        if not app_name or not app_name.strip():
            return {
                "success": False,
                "message": "No application name provided.",
                "app_name": app_name,
            }

        # Reject shell-injection characters
        if any(ch in _ILLEGAL_CHARS for ch in app_name):
            return {
                "success": False,
                "message": "Application name contains invalid characters.",
                "app_name": app_name,
            }

        # Reject path traversal attempts
        if ".." in app_name or "/" in app_name or "\\" in app_name:
            return {
                "success": False,
                "message": "Application name is not supported.",
                "app_name": app_name,
            }

        key = app_name.strip().lower()
        exe = ALLOWED_APPS.get(key)
        if exe is None:
            return {
                "success": False,
                "message": f"'{app_name}' is not supported.",
                "app_name": app_name,
            }

        # --- Launch ---------------------------------------------------
        try:
            if exe.startswith("ms-"):
                # URI-scheme launch (e.g. ms-settings:)
                subprocess.Popen(  # noqa: S603
                    ["cmd", "/c", "start", exe],
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(  # noqa: S603
                    [exe],
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            logger.info("Launched application: %s (%s)", key, exe)
            return {
                "success": True,
                "message": f"Opening {app_name.title()}.",
                "app_name": app_name,
            }
        except (FileNotFoundError, PermissionError, OSError, Exception) as exc:
            logger.error("Failed to launch %s (%s): %s", key, exe, exc)
            return {
                "success": False,
                "message": f"Sorry, I couldn't open '{app_name}'.",
                "app_name": app_name,
            }

    @staticmethod
    def list_apps() -> list[str]:
        """Return sorted list of human-friendly application names."""
        seen: set[str] = set()
        result: list[str] = []
        for name in ALLOWED_APPS:
            canonical = name.replace("_", " ").title()
            if canonical not in seen:
                result.append(canonical)
                seen.add(canonical)
        return sorted(result)
