"""
test_text_to_speech.py — Unit tests for TextToSpeechEngine.

pyttsx3 is mocked so these tests run without an audio device.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_pyttsx3():
    """Patch pyttsx3.init so no real audio engine is created."""
    with patch("pyttsx3.init") as mock_init:
        engine = MagicMock()
        mock_init.return_value = engine
        yield engine


@pytest.fixture
def tts(mock_pyttsx3):
    """Return a TextToSpeechEngine backed by the mock pyttsx3 engine."""
    from assistant.text_to_speech import TextToSpeechEngine
    t = TextToSpeechEngine()
    # Give the worker thread a moment to initialise
    time.sleep(0.1)
    return t


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestInit:
    def test_creates_without_error(self, mock_pyttsx3):
        from assistant.text_to_speech import TextToSpeechEngine
        t = TextToSpeechEngine()
        time.sleep(0.1)
        t.shutdown()

    def test_worker_thread_is_daemon(self, tts):
        assert tts._thread.daemon
        tts.shutdown()


# ---------------------------------------------------------------------------
# speak()
# ---------------------------------------------------------------------------

class TestSpeak:
    def test_speak_enqueues_command(self, tts, mock_pyttsx3):
        tts.speak("Hello world")
        # Allow daemon thread to dequeue and process
        time.sleep(0.2)
        mock_pyttsx3.say.assert_called()
        tts.shutdown()

    def test_speak_calls_runAndWait(self, tts, mock_pyttsx3):
        tts.speak("Testing TTS")
        time.sleep(0.2)
        mock_pyttsx3.runAndWait.assert_called()
        tts.shutdown()

    def test_speak_empty_string_ignored(self, tts, mock_pyttsx3):
        tts.speak("")
        time.sleep(0.1)
        mock_pyttsx3.say.assert_not_called()
        tts.shutdown()

    def test_speak_whitespace_only_ignored(self, tts, mock_pyttsx3):
        tts.speak("   ")
        time.sleep(0.1)
        mock_pyttsx3.say.assert_not_called()
        tts.shutdown()


# ---------------------------------------------------------------------------
# mute / unmute
# ---------------------------------------------------------------------------

class TestMuteUnmute:
    def test_mute_prevents_speech(self, tts, mock_pyttsx3):
        tts.mute()
        tts.speak("This should be muted")
        time.sleep(0.2)
        mock_pyttsx3.say.assert_not_called()
        tts.shutdown()

    def test_unmute_restores_speech(self, tts, mock_pyttsx3):
        tts.mute()
        tts.unmute()
        tts.speak("Now speaking")
        time.sleep(0.2)
        mock_pyttsx3.say.assert_called()
        tts.shutdown()


# ---------------------------------------------------------------------------
# set_rate / set_volume
# ---------------------------------------------------------------------------

class TestSettings:
    def test_set_rate_enqueues_property(self, tts, mock_pyttsx3):
        tts.set_rate(200)
        time.sleep(0.2)
        mock_pyttsx3.setProperty.assert_any_call("rate", 200)
        tts.shutdown()

    def test_set_volume_enqueues_property(self, tts, mock_pyttsx3):
        tts.set_volume(0.5)
        time.sleep(0.2)
        mock_pyttsx3.setProperty.assert_any_call("volume", 0.5)
        tts.shutdown()

    def test_set_volume_clamped_above_one(self, tts, mock_pyttsx3):
        tts.set_volume(2.0)
        time.sleep(0.2)
        calls = [str(c) for c in mock_pyttsx3.setProperty.call_args_list]
        # Volume should be clamped to 1.0
        assert any("volume" in c and "1.0" in c for c in calls)
        tts.shutdown()


# ---------------------------------------------------------------------------
# get_voices
# ---------------------------------------------------------------------------

class TestGetVoices:
    def test_returns_list(self, tts, mock_pyttsx3):
        mock_voice = MagicMock()
        mock_voice.id = "voice-1"
        mock_voice.name = "Microsoft David"
        mock_pyttsx3.getProperty.return_value = [mock_voice]

        voices = tts.get_voices()
        assert isinstance(voices, list)
        tts.shutdown()

    def test_returns_empty_on_error(self, tts, mock_pyttsx3):
        mock_pyttsx3.getProperty.side_effect = Exception("engine error")
        voices = tts.get_voices()
        assert voices == []
        tts.shutdown()


# ---------------------------------------------------------------------------
# shutdown
# ---------------------------------------------------------------------------

class TestShutdown:
    def test_shutdown_stops_worker_thread(self, mock_pyttsx3):
        from assistant.text_to_speech import TextToSpeechEngine
        t = TextToSpeechEngine()
        time.sleep(0.1)
        t.shutdown()
        # Thread should exit shortly after sentinel is enqueued
        t._thread.join(timeout=2)
        assert not t._thread.is_alive()

    def test_double_shutdown_does_not_raise(self, mock_pyttsx3):
        from assistant.text_to_speech import TextToSpeechEngine
        t = TextToSpeechEngine()
        time.sleep(0.1)
        t.shutdown()
        t.shutdown()   # second call should be a no-op
