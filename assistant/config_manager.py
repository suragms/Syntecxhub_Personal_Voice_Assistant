"""
config_manager.py — Loads, validates, and persists assistant settings.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Path to the shipped defaults alongside the bundled config/ directory
_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "default_settings.json"
# User-overrideable settings file (not committed to git)
_USER_CONFIG_PATH = Path(__file__).parent.parent / "user_settings.json"

# Boundaries for numeric settings
_BOUNDS: dict[str, tuple[float, float]] = {
    "speech_rate": (50, 400),
    "volume": (0.0, 1.0),
    "listen_timeout": (1, 30),
    "phrase_timeout": (1, 60),
    "max_history_entries": (10, 10000),
}

_VALID_THEMES = {"dark", "light"}
_VALID_RECOGNITION_MODES = {"online", "offline"}
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ConfigManager:
    """Manages application configuration with validation and persistence."""

    def __init__(self) -> None:
        self._settings: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return a setting value, falling back to *default*."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Update a setting and persist to the user config file."""
        self._settings[key] = value
        self._save()

    def get_all(self) -> dict[str, Any]:
        """Return a shallow copy of all settings."""
        return dict(self._settings)

    def reset_to_defaults(self) -> None:
        """Restore factory defaults and remove the user config file."""
        if _USER_CONFIG_PATH.exists():
            _USER_CONFIG_PATH.unlink()
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load defaults and overlay user settings, then validate."""
        defaults = self._read_json(_DEFAULT_CONFIG_PATH) or {}
        user = self._read_json(_USER_CONFIG_PATH) or {}
        merged = {**defaults, **user}
        self._settings = self._validate(merged)

    def _save(self) -> None:
        """Persist current settings to the user config file."""
        try:
            _USER_CONFIG_PATH.write_text(
                json.dumps(self._settings, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.error("Failed to save user settings: %s", exc)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any] | None:
        """Read and return parsed JSON from *path*, or None on failure."""
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read config %s: %s", path, exc)
            return None

    def _validate(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Validate and coerce numeric/enum settings; apply safe defaults."""
        # Numeric range validation
        for key, (lo, hi) in _BOUNDS.items():
            if key in settings:
                try:
                    val = float(settings[key])
                    if not lo <= val <= hi:
                        logger.warning(
                            "Setting %r value %s out of range [%s, %s]; resetting.",
                            key, val, lo, hi,
                        )
                        settings[key] = lo if val < lo else hi
                    else:
                        settings[key] = type(settings[key])(val)
                except (TypeError, ValueError):
                    logger.warning("Setting %r has invalid type; removing.", key)
                    settings.pop(key)

        # Enum validation
        if settings.get("theme") not in _VALID_THEMES:
            settings["theme"] = "dark"
        if settings.get("recognition_mode") not in _VALID_RECOGNITION_MODES:
            settings["recognition_mode"] = "online"
        if settings.get("log_level") not in _VALID_LOG_LEVELS:
            settings["log_level"] = "INFO"

        return settings
