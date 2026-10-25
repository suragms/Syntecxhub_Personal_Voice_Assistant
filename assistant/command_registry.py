"""
command_registry.py — Registry of supported commands and their handlers.

Each command is registered as a ``CommandEntry`` keyed by intent name.
The registry is populated by the individual handler modules on import.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class CommandEntry:
    """Describes a single supported command."""

    intent: str
    handler: Callable[[dict[str, Any]], dict[str, Any]]
    patterns: list[str] = field(default_factory=list)
    description: str = ""
    category: str = "general"
    examples: list[str] = field(default_factory=list)


class CommandRegistry:
    """
    Central registry for command intents.

    Modules call ``register()`` to contribute their commands.
    ``CommandProcessor`` uses ``get_all()`` to build its matching table.
    """

    def __init__(self) -> None:
        self._commands: dict[str, CommandEntry] = {}

    def register(self, entry: CommandEntry) -> None:
        """Register *entry* under its intent name."""
        self._commands[entry.intent] = entry
        logger.debug("Registered command intent: %s", entry.intent)

    def get(self, intent: str) -> Optional[CommandEntry]:
        return self._commands.get(intent)

    def get_all(self) -> dict[str, CommandEntry]:
        return dict(self._commands)

    def get_by_category(self) -> dict[str, list[CommandEntry]]:
        """Group commands by their category."""
        result: dict[str, list[CommandEntry]] = {}
        for entry in self._commands.values():
            result.setdefault(entry.category, []).append(entry)
        return result


# Module-level singleton used across the application.
registry = CommandRegistry()
