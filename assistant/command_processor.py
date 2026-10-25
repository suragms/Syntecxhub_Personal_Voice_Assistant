"""
command_processor.py — Rule-based intent recognition and command dispatch.

Architecture
-----------
1. Normalise → strip, lowercase, collapse spaces.
2. Match    → iterate intents in priority order; first match wins.
3. Extract  → pull entities from the recognised pattern.
4. Validate → check that extracted entities are non-empty / allowed.
5. Execute  → delegate to the matching handler.
6. Respond  → return structured result dict consumed by the GUI layer.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from assistant.application_launcher import ApplicationLauncher
from assistant.error_handler import ErrorHandler, unsupported_command
from assistant.system_commands import SystemCommands
from assistant.web_search import WebSearch

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Structured outcome of processing a single command."""

    success: bool
    intent: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


class CommandProcessor:
    """
    Rule-based intent matcher.

    Patterns are tried in registration order (most-specific first).
    """

    def __init__(self) -> None:
        self._patterns: list[tuple[re.Pattern, str, str]] = []  # (regex, intent, category)
        self._register_all()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, text: str) -> CommandResult:
        """Recognise *text* and execute the matching handler."""
        normalised = self._normalise(text)
        if not normalised:
            return CommandResult(
                success=False,
                intent="empty",
                message="I didn't receive a command. Could you try again?",
            )

        intent, match = self._match(normalised)
        if intent is None:
            err = unsupported_command(text)
            return CommandResult(
                success=False,
                intent="unsupported",
                message=err.user_message(),
            )

        try:
            result = self._dispatch(intent, normalised, match)
            # Flatten 'data' subdict into the top-level result dict so
            # callers can access result.data['query'] directly.
            data = dict(result)
            if "data" in result and isinstance(result["data"], dict):
                data.update(result["data"])

            return CommandResult(
                success=result.get("success", True),
                intent=intent,
                message=result.get("message", "Done."),
                data=data,
            )
        except Exception as exc:  # noqa: BLE001
            err_obj = ErrorHandler.handle(exc, context=f"command:{intent}")
            return CommandResult(
                success=False,
                intent=intent,
                message=err_obj.user_message(),
            )

    def get_sample_commands(self) -> dict[str, list[dict[str, str]]]:
        """Return command samples grouped by category for the UI panel."""
        return {
            "Applications": [
                {"command": "Open Notepad", "description": "Launch Windows Notepad"},
                {"command": "Open Calculator", "description": "Launch Calculator"},
                {"command": "Open Paint", "description": "Launch MS Paint"},
                {"command": "Open File Explorer", "description": "Launch File Explorer"},
                {"command": "Open Settings", "description": "Open Windows Settings"},
            ],
            "Web": [
                {"command": "Search Google for Python tutorials", "description": "Web search"},
                {"command": "Open YouTube", "description": "Open youtube.com"},
                {"command": "Open GitHub", "description": "Open github.com"},
            ],
            "Date & Time": [
                {"command": "What time is it?", "description": "Current clock time"},
                {"command": "What's today's date?", "description": "Today's date"},
                {"command": "What day is it?", "description": "Day of the week"},
            ],
            "Conversation": [
                {"command": "Hello", "description": "Greet the assistant"},
                {"command": "Who are you?", "description": "About SURA"},
                {"command": "What can you do?", "description": "List capabilities"},
                {"command": "Thank you", "description": "Express thanks"},
                {"command": "Goodbye", "description": "Exit the assistant"},
            ],
        }

    # ------------------------------------------------------------------
    # Pattern registration
    # ------------------------------------------------------------------

    def _add(self, pattern: str, intent: str, category: str = "general") -> None:
        self._patterns.append((re.compile(pattern, re.IGNORECASE), intent, category))

    def _register_all(self) -> None:
        # --- Date / Time FIRST (before open_app catches "what day…") ----
        self._add(
            r"(?:what(?:'?s| is) the (?:current )?time|tell (?:me )?the (?:current )?time|what time is it)",
            "get_time",
            "datetime",
        )
        self._add(
            r"(?:what(?:'?s| is) (?:today(?:'?s)? )?(?:the )?date|tell (?:me )?the (?:current )?date|today(?:'?s)? date)",
            "get_date",
            "datetime",
        )
        self._add(
            r"(?:what day (?:is (?:it|today)|of the week)|tell (?:me )?the day)",
            "get_day",
            "datetime",
        )

        # --- Conversation (before open_app so "help" isn't mis-matched) -
        greet_alts = "|".join(re.escape(g) for g in sorted(SystemCommands.GREETINGS, key=len, reverse=True))
        self._add(rf"^(?:{greet_alts})\.?$", "greet", "conversation")

        about_alts = "|".join(re.escape(a) for a in SystemCommands.ABOUT_PHRASES)
        self._add(rf"^(?:{about_alts})\??$", "about", "conversation")

        how_alts = "|".join(re.escape(h) for h in SystemCommands.HOW_ARE_YOU_PHRASES)
        self._add(rf"^(?:{how_alts})\??$", "how_are_you", "conversation")

        help_alts = "|".join(re.escape(h) for h in SystemCommands.HELP_PHRASES)
        self._add(rf"^(?:{help_alts})\??$", "help", "conversation")

        thanks_alts = "|".join(re.escape(t) for t in SystemCommands.THANKS_PHRASES)
        self._add(rf"^(?:{thanks_alts})\!?\.?$", "thanks", "conversation")

        bye_alts = "|".join(re.escape(b) for b in SystemCommands.GOODBYE_PHRASES)
        self._add(rf"^(?:{bye_alts})\.?$", "goodbye", "conversation")

        # --- Web search -----------------------------------------------
        self._add(
            r"^(?:search(?: for)?|search google for|google|search the web for|look up|find)\s+(.+)$",
            "web_search",
            "web",
        )
        # Explicit "go to" for known sites
        self._add(
            r"^(?:go to|visit)\s+(google|youtube|github|wikipedia|stackoverflow|reddit)$",
            "open_site",
            "web",
        )

        # --- Application commands -------------------------------------
        self._add(
            r"^(?:open|launch|start|run)\s+(.+)$",
            "open_app",
            "applications",
        )

    # ------------------------------------------------------------------
    # Normalisation & matching
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        normalised = text.strip().lower()
        normalised = re.sub(r"\s+", " ", normalised)
        return normalised

    def _match(self, text: str) -> tuple[Optional[str], Optional[re.Match]]:
        for regex, intent, _ in self._patterns:
            m = regex.search(text)
            if m:
                return intent, m
        return None, None

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, intent: str, text: str, match: re.Match | None) -> dict[str, Any]:
        if intent == "open_app":
            app_name = match.group(1).strip() if match else text
            # Check if this is actually a website name
            site_key = app_name.lower()
            if site_key in WebSearch.list_sites():
                return WebSearch.open_site(site_key)
            result = ApplicationLauncher.launch(app_name)
            return result

        if intent == "web_search":
            # group(2) when the pattern has two capture groups; group(1) otherwise
            try:
                query = match.group(2).strip() if match else text
            except IndexError:
                query = match.group(1).strip() if match else text
            return WebSearch.search(query)

        if intent == "open_site":
            site = match.group(1).strip() if match else text
            return WebSearch.open_site(site)

        if intent == "get_time":
            return SystemCommands.get_time()

        if intent == "get_date":
            return SystemCommands.get_date()

        if intent == "get_day":
            return SystemCommands.get_day()

        if intent == "greet":
            return SystemCommands.greet()

        if intent == "about":
            return SystemCommands.about()

        if intent == "how_are_you":
            return SystemCommands.how_are_you()

        if intent == "help":
            return SystemCommands.help_text()

        if intent == "thanks":
            return SystemCommands.thanks()

        if intent == "goodbye":
            return SystemCommands.goodbye()

        raise unsupported_command(text)
