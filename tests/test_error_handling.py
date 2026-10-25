"""
test_error_handling.py — Unit tests for ErrorCategory, AssistantError, and ErrorHandler.

Tests error creation, categorization, factory functions, and handler behavior.
"""

from __future__ import annotations

import pytest

from assistant.error_handler import (
    ErrorCategory,
    AssistantError,
    ErrorHandler,
)


# ---------------------------------------------------------------------------
# ErrorCategory enum
# ---------------------------------------------------------------------------

class TestErrorCategory:
    def test_all_categories_present(self):
        """Ensure all documented error categories are defined."""
        required = {
            "MICROPHONE",
            "RECOGNITION",
            "NETWORK",
            "TTS",
            "COMMAND",
            "APPLICATION",
            "CONFIGURATION",
            "UNKNOWN",
        }
        actual = {cat.name for cat in ErrorCategory}
        assert required.issubset(actual), f"Missing categories: {required - actual}"


# ---------------------------------------------------------------------------
# AssistantError constructor and attributes
# ---------------------------------------------------------------------------

class TestAssistantError:
    def test_creates_with_category(self):
        err = AssistantError(
            category=ErrorCategory.MICROPHONE,
            message="Test error"
        )
        assert err.category == ErrorCategory.MICROPHONE

    def test_stores_original_exception(self):
        original = ValueError("original")
        err = AssistantError(
            category=ErrorCategory.CONFIGURATION,
            message="Wrapper",
            original=original
        )
        assert err.original is original

    def test_user_message_returns_string(self):
        err = AssistantError(
            category=ErrorCategory.TTS,
            message="TTS failed"
        )
        msg = err.user_message()
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_user_message_friendly_not_technical(self):
        """User message should be friendly, not a raw traceback."""
        err = AssistantError(
            category=ErrorCategory.NETWORK,
            message="RequestError: timeout"
        )
        msg = err.user_message()
        # Should not contain raw exception types or stack traces
        assert "RequestError" not in msg or "network" in msg.lower()


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

class TestFactoryFunctions:
    def test_mic_not_found(self):
        err = ErrorHandler.mic_not_found()
        assert err.category == ErrorCategory.MICROPHONE
        assert "microphone" in err.message.lower() or "not found" in err.message.lower()

    def test_mic_permission_denied(self):
        err = ErrorHandler.mic_permission_denied()
        assert err.category == ErrorCategory.MICROPHONE
        assert "permission" in err.message.lower() or "access" in err.message.lower()

    def test_recognition_failed(self):
        err = ErrorHandler.recognition_failed()
        assert err.category == ErrorCategory.RECOGNITION

    def test_network_unavailable(self):
        err = ErrorHandler.network_unavailable()
        assert err.category == ErrorCategory.NETWORK

    def test_tts_failed(self):
        err = ErrorHandler.tts_failed()
        assert err.category == ErrorCategory.TTS

    def test_unsupported_command(self):
        err = ErrorHandler.unsupported_command("test command")
        assert err.category == ErrorCategory.COMMAND
        assert "test command" in err.message

    def test_app_launch_failed(self):
        err = ErrorHandler.app_launch_failed("notepad")
        assert err.category == ErrorCategory.APPLICATION
        assert "notepad" in err.message.lower()


# ---------------------------------------------------------------------------
# ErrorHandler.handle() — routing to correct category
# ---------------------------------------------------------------------------

class TestErrorHandlerHandle:
    def test_handles_assistant_error(self):
        """AssistantError should pass through unchanged."""
        original = AssistantError(
            category=ErrorCategory.TTS,
            message="Test"
        )
        result = ErrorHandler.handle(original)
        assert result is original

    def test_handles_oserror_as_microphone(self):
        """OSError (device not found) → MICROPHONE category."""
        exc = OSError("No audio device")
        result = ErrorHandler.handle(exc)
        assert result.category == ErrorCategory.MICROPHONE

    def test_handles_permission_error_as_microphone(self):
        """PermissionError → MICROPHONE category."""
        exc = PermissionError("Access denied")
        result = ErrorHandler.handle(exc)
        assert result.category == ErrorCategory.MICROPHONE

    def test_handles_value_error_as_configuration(self):
        """ValueError → CONFIGURATION category."""
        exc = ValueError("Invalid setting")
        result = ErrorHandler.handle(exc)
        assert result.category == ErrorCategory.CONFIGURATION

    def test_handles_generic_exception_as_unknown(self):
        """Unknown exception type → UNKNOWN category."""
        exc = RuntimeError("Something went wrong")
        result = ErrorHandler.handle(exc)
        assert result.category == ErrorCategory.UNKNOWN

    def test_stores_original_exception(self):
        """handle() should preserve the original exception."""
        exc = ValueError("Test")
        result = ErrorHandler.handle(exc)
        assert result.original is exc


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_message(self):
        """Empty message should not crash user_message()."""
        err = AssistantError(
            category=ErrorCategory.COMMAND,
            message=""
        )
        msg = err.user_message()
        assert isinstance(msg, str)

    def test_none_original(self):
        """original=None should be allowed."""
        err = AssistantError(
            category=ErrorCategory.NETWORK,
            message="Test",
            original=None
        )
        assert err.original is None

    def test_user_message_does_not_raise(self):
        """user_message() should never raise, even with malformed data."""
        err = AssistantError(
            category=ErrorCategory.UNKNOWN,
            message=None  # type: ignore
        )
        try:
            msg = err.user_message()
            assert isinstance(msg, str)
        except Exception as e:
            pytest.fail(f"user_message() raised: {e}")
