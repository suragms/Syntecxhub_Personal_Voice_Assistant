"""
test_speech_recognition.py — Unit tests for SpeechRecognitionService.

All hardware interaction (microphone, audio) is mocked so the tests run
in CI without a physical microphone.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from assistant.error_handler import ErrorCategory
from assistant.speech_recognition_service import SpeechRecognitionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def service() -> SpeechRecognitionService:
    """Return a fresh SpeechRecognitionService with no callbacks attached."""
    return SpeechRecognitionService()


# ---------------------------------------------------------------------------
# Constructor / configuration
# ---------------------------------------------------------------------------

class TestInit:
    def test_creates_instance(self, service):
        assert service is not None

    def test_not_active_initially(self, service):
        assert not service._active


# ---------------------------------------------------------------------------
# list_microphones — static method
# ---------------------------------------------------------------------------

class TestListMicrophones:
    @patch("speech_recognition.Microphone.list_microphone_names")
    def test_returns_list_of_tuples(self, mock_names):
        mock_names.return_value = ["Default Mic", "USB Mic"]
        mics = SpeechRecognitionService.list_microphones()
        assert isinstance(mics, list)
        for idx, name in mics:
            assert isinstance(idx, int)
            assert isinstance(name, str)

    @patch("speech_recognition.Microphone.list_microphone_names", side_effect=OSError("no audio"))
    def test_returns_empty_list_on_error(self, _mock):
        mics = SpeechRecognitionService.list_microphones()
        assert mics == []


# ---------------------------------------------------------------------------
# on_result / on_error / on_listening callbacks
# ---------------------------------------------------------------------------

class TestCallbacks:
    def test_set_on_result(self, service):
        cb = MagicMock()
        service.on_result = cb
        assert service.on_result is cb

    def test_set_on_error(self, service):
        cb = MagicMock()
        service.on_error = cb
        assert service.on_error is cb

    def test_set_on_listening(self, service):
        cb = MagicMock()
        service.on_listening = cb
        assert service.on_listening is cb


# ---------------------------------------------------------------------------
# stop() — should be safe even without an active listen
# ---------------------------------------------------------------------------

class TestStop:
    def test_stop_when_idle_does_not_raise(self, service):
        service.stop()  # should not throw


# ---------------------------------------------------------------------------
# listen_once — success path (mocked microphone + recognizer)
# ---------------------------------------------------------------------------

class TestListenOnceSuccess:
    @patch("assistant.speech_recognition_service.sr")
    def test_calls_on_result_with_text(self, mock_sr):
        """When recognition succeeds, on_result should receive the text."""
        # Set up mock recognizer and microphone
        mock_recognizer = MagicMock()
        mock_recognizer.recognize_google.return_value = "open notepad"
        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.Microphone.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_sr.Microphone.return_value.__exit__ = MagicMock(return_value=False)

        service = SpeechRecognitionService()
        result_holder = []

        def on_result(text):
            result_holder.append(text)

        service.on_result = on_result
        service.listen_once()

        # Wait for the daemon thread to finish (up to 3 s)
        deadline = time.time() + 3
        while not result_holder and time.time() < deadline:
            time.sleep(0.05)

        assert result_holder == ["open notepad"]

    @patch("assistant.speech_recognition_service.sr")
    def test_calls_on_listening_true_then_false(self, mock_sr):
        """on_listening should be called with True (start) then False (stop)."""
        mock_recognizer = MagicMock()
        mock_recognizer.recognize_google.return_value = "hello"
        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.Microphone.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_sr.Microphone.return_value.__exit__ = MagicMock(return_value=False)

        service = SpeechRecognitionService()
        calls = []
        service.on_listening = lambda v: calls.append(v)
        service.listen_once()

        deadline = time.time() + 3
        while len(calls) < 2 and time.time() < deadline:
            time.sleep(0.05)

        assert True in calls
        assert False in calls


# ---------------------------------------------------------------------------
# listen_once — error paths (mocked)
# ---------------------------------------------------------------------------

class TestListenOnceErrors:
    @patch("assistant.speech_recognition_service.sr")
    def test_unknown_value_error_calls_on_error(self, mock_sr):
        """UnknownValueError → recognition_failed AssistantError."""
        mock_recognizer = MagicMock()
        mock_recognizer.recognize_google.side_effect = mock_sr.UnknownValueError()
        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.Microphone.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_sr.Microphone.return_value.__exit__ = MagicMock(return_value=False)
        mock_sr.UnknownValueError = type("UnknownValueError", (Exception,), {})

        service = SpeechRecognitionService()
        errors = []
        service.on_error = lambda e: errors.append(e)
        service.listen_once()

        deadline = time.time() + 3
        while not errors and time.time() < deadline:
            time.sleep(0.05)

        assert errors
        assert errors[0].category == ErrorCategory.RECOGNITION

    @patch("assistant.speech_recognition_service.sr")
    def test_request_error_calls_on_error_network(self, mock_sr):
        """RequestError → network_unavailable AssistantError."""
        mock_recognizer = MagicMock()
        mock_recognizer.recognize_google.side_effect = mock_sr.RequestError("no network")
        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.Microphone.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_sr.Microphone.return_value.__exit__ = MagicMock(return_value=False)
        mock_sr.RequestError = type("RequestError", (Exception,), {})

        service = SpeechRecognitionService()
        errors = []
        service.on_error = lambda e: errors.append(e)
        service.listen_once()

        deadline = time.time() + 3
        while not errors and time.time() < deadline:
            time.sleep(0.05)

        assert errors
        assert errors[0].category == ErrorCategory.NETWORK

    @patch("assistant.speech_recognition_service.sr")
    def test_oserror_calls_on_error_microphone(self, mock_sr):
        """OSError (device not found) → mic AssistantError."""
        mock_recognizer = MagicMock()
        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.Microphone.return_value.__enter__ = MagicMock(side_effect=OSError("no mic"))
        mock_sr.Microphone.return_value.__exit__ = MagicMock(return_value=False)

        service = SpeechRecognitionService()
        errors = []
        service.on_error = lambda e: errors.append(e)
        service.listen_once()

        deadline = time.time() + 3
        while not errors and time.time() < deadline:
            time.sleep(0.05)

        assert errors
        assert errors[0].category == ErrorCategory.MICROPHONE
