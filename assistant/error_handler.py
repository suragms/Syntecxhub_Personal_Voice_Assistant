"""
error_handler.py — Centralised error categorisation and user-friendly messages.
"""

from __future__ import annotations

import logging
import traceback
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    MICROPHONE = auto()
    RECOGNITION = auto()
    NETWORK = auto()
    TTS = auto()
    COMMAND = auto()
    APPLICATION = auto()
    CONFIGURATION = auto()
    UNKNOWN = auto()


class AssistantError(Exception):
    """Base exception for SURA assistant errors."""

    def __init__(
        self,
        message: str | None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        original: Exception | None = None,
    ) -> None:
        super().__init__(message or "")
        self.message = message or ""
        self.category = category
        self.original = original

    def user_message(self) -> str:
        _TECHNICAL_TOKENS = ("RequestError", "Traceback", "Exception", "Error:")
        if self.message and not any(tok in self.message for tok in _TECHNICAL_TOKENS):
            return self.message
        # Return category-appropriate friendly message
        if self.category == ErrorCategory.NETWORK:
            return "A network error occurred. Please check your internet connection."
        if self.category == ErrorCategory.MICROPHONE:
            return "A microphone error occurred. Please check your audio settings."
        if self.category == ErrorCategory.RECOGNITION:
            return "Speech recognition failed. Please try speaking clearly."
        if self.category == ErrorCategory.TTS:
            return "Text-to-speech error occurred."
        return self.message or "An error occurred."


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def mic_not_found() -> AssistantError:
    return AssistantError(
        "No microphone detected. Please connect a microphone or use text mode.",
        ErrorCategory.MICROPHONE,
    )


def mic_permission_denied() -> AssistantError:
    return AssistantError(
        "Microphone access was denied. Check your Windows privacy settings.",
        ErrorCategory.MICROPHONE,
    )


def recognition_failed(detail: str = "") -> AssistantError:
    msg = "Sorry, I couldn't understand that. Please try again."
    if detail:
        msg += f" ({detail})"
    return AssistantError(msg, ErrorCategory.RECOGNITION)


def network_unavailable() -> AssistantError:
    return AssistantError(
        "Online speech recognition is unavailable. Check your internet connection "
        "or switch to offline mode.",
        ErrorCategory.NETWORK,
    )


def tts_failed(original: Exception | None = None) -> AssistantError:
    return AssistantError(
        "Text-to-speech is currently unavailable. Responses will be shown as text only.",
        ErrorCategory.TTS,
        original=original,
    )


def unsupported_command(command: str = "") -> AssistantError:
    snippet = f' "{command}"' if command else ""
    return AssistantError(
        f"I don't recognise that command{snippet} yet. "
        "Open the Commands panel to see what I can do.",
        ErrorCategory.COMMAND,
    )


def app_launch_failed(app_name: str = "") -> AssistantError:
    target = f" {app_name}" if app_name else ""
    return AssistantError(
        f"Sorry, I couldn't open{target}.",
        ErrorCategory.APPLICATION,
    )


# ---------------------------------------------------------------------------
# Central handler
# ---------------------------------------------------------------------------

class ErrorHandler:
    """Logs errors and wraps them in AssistantError for the GUI."""

    # Expose factory functions as static methods so tests can call
    # ErrorHandler.mic_not_found() etc.
    @staticmethod
    def mic_not_found() -> AssistantError:
        return mic_not_found()

    @staticmethod
    def mic_permission_denied() -> AssistantError:
        return mic_permission_denied()

    @staticmethod
    def recognition_failed(detail: str = "") -> AssistantError:
        return recognition_failed(detail)

    @staticmethod
    def network_unavailable() -> AssistantError:
        return network_unavailable()

    @staticmethod
    def tts_failed(original: Exception | None = None) -> AssistantError:
        return tts_failed(original)

    @staticmethod
    def unsupported_command(command: str = "") -> AssistantError:
        return unsupported_command(command)

    @staticmethod
    def app_launch_failed(app_name: str = "") -> AssistantError:
        return app_launch_failed(app_name)

    @staticmethod
    def handle(exc: Exception, context: str = "") -> AssistantError:
        """Wrap *exc* in an AssistantError (or pass it through) and log it."""
        if isinstance(exc, AssistantError):
            if exc.original:
                logger.error(
                    "[%s] %s | Context: %s | Original: %s",
                    exc.category.name, exc.user_message(), context, exc.original,
                )
            else:
                logger.error(
                    "[%s] %s | Context: %s",
                    exc.category.name, exc.user_message(), context,
                )
            return exc

        # Map common Python built-in exceptions to sensible categories
        if isinstance(exc, PermissionError):
            category = ErrorCategory.MICROPHONE
            message = "Microphone access was denied. Check your Windows privacy settings."
        elif isinstance(exc, OSError):
            category = ErrorCategory.MICROPHONE
            message = "No microphone detected. Please connect a microphone or use text mode."
        elif isinstance(exc, ValueError):
            category = ErrorCategory.CONFIGURATION
            message = "A configuration value is invalid. Please check your settings."
        else:
            category = ErrorCategory.UNKNOWN
            message = "An unexpected error occurred. Please try again."

        logger.error(
            "[%s] %s | Context: %s | Traceback:\n%s",
            category.name, exc, context, traceback.format_exc(),
        )
        return AssistantError(message, category, original=exc)
