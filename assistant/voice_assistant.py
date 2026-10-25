"""
voice_assistant.py — Orchestrates speech recognition, command processing,
TTS, and GUI updates through an explicit state machine.
"""

from __future__ import annotations

import datetime
import json
import logging
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal

from assistant.command_processor import CommandProcessor, CommandResult
from assistant.config_manager import ConfigManager
from assistant.error_handler import AssistantError, ErrorHandler
from assistant.speech_recognition_service import SpeechRecognitionService
from assistant.text_to_speech import TextToSpeechEngine

logger = logging.getLogger(__name__)

_HISTORY_PATH = Path(__file__).parent.parent / "command_history.json"


class AssistantState(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    EXECUTING = auto()
    SPEAKING = auto()
    ERROR = auto()
    STOPPED = auto()


class VoiceAssistant(QObject):
    """
    Central orchestrator emitting Qt signals for every state transition.

    Signals
    -------
    state_changed(state_name: str)
    result_ready(user_text: str, assistant_response: str, success: bool)
    error_occurred(message: str)
    listening_changed(is_listening: bool)
    """

    state_changed = Signal(str)
    result_ready = Signal(str, str, bool)
    error_occurred = Signal(str)
    listening_changed = Signal(bool)

    def __init__(self, config: ConfigManager | None = None) -> None:
        super().__init__()
        self._config = config or ConfigManager()
        self._state = AssistantState.IDLE

        # Sub-systems
        self._processor = CommandProcessor()
        self._tts = TextToSpeechEngine(
            speech_rate=self._config.get("speech_rate", 170),
            volume=self._config.get("volume", 0.8),
        )
        self._sr = SpeechRecognitionService(
            on_result=self._on_speech_result,
            on_error=self._on_speech_error,
            on_listening=self._on_listening_state,
            microphone_index=self._config.get("microphone_index"),
            language=self._config.get("language", "en-US"),
            listen_timeout=self._config.get("listen_timeout", 5),
            phrase_timeout=self._config.get("phrase_timeout", 8),
        )

        # History
        self._history: list[dict[str, Any]] = []
        self._load_history()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> AssistantState:
        return self._state

    @property
    def config(self) -> ConfigManager:
        return self._config

    @property
    def tts(self) -> TextToSpeechEngine:
        return self._tts

    @property
    def sr_service(self) -> SpeechRecognitionService:
        return self._sr

    @property
    def processor(self) -> CommandProcessor:
        return self._processor

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _set_state(self, new_state: AssistantState) -> None:
        if new_state == self._state:
            return
        logger.debug("State: %s → %s", self._state.name, new_state.name)
        self._state = new_state
        self.state_changed.emit(new_state.name)

    # ------------------------------------------------------------------
    # Voice commands
    # ------------------------------------------------------------------

    def start_listening(self) -> None:
        """Kick off a push-to-talk listen cycle."""
        if self._state in (AssistantState.LISTENING, AssistantState.STOPPED):
            return
        self._set_state(AssistantState.LISTENING)
        self._sr.listen_once()

    def stop_listening(self) -> None:
        """Abort current listening session."""
        self._sr.stop()
        self._set_state(AssistantState.IDLE)

    # ------------------------------------------------------------------
    # Text commands (same pipeline as voice)
    # ------------------------------------------------------------------

    def process_text(self, text: str) -> None:
        """Process a typed command through the same pipeline as voice."""
        self._handle_command(text)

    # ------------------------------------------------------------------
    # Callbacks from SpeechRecognitionService (called on worker thread)
    # ------------------------------------------------------------------

    def _on_speech_result(self, text: str) -> None:
        self._handle_command(text)

    def _on_speech_error(self, error: AssistantError) -> None:
        self._set_state(AssistantState.ERROR)
        msg = error.user_message()
        logger.warning("Speech error: %s", msg)
        self.error_occurred.emit(msg)
        self._set_state(AssistantState.IDLE)

    def _on_listening_state(self, is_listening: bool) -> None:
        self.listening_changed.emit(is_listening)
        if not is_listening and self._state == AssistantState.LISTENING:
            self._set_state(AssistantState.PROCESSING)

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    def _handle_command(self, text: str) -> None:
        self._set_state(AssistantState.PROCESSING)
        result: CommandResult = self._processor.process(text)

        self._set_state(AssistantState.EXECUTING)
        self._record_history(text, result)

        # Check for exit
        if result.data and result.data.get("action") == "exit":
            self._speak(result.message)
            self._set_state(AssistantState.STOPPED)
            self.result_ready.emit(text, result.message, result.success)
            return

        self._speak(result.message)
        self.result_ready.emit(text, result.message, result.success)
        self._set_state(AssistantState.IDLE)

    def _speak(self, text: str) -> None:
        """Transition to SPEAKING and queue TTS."""
        self._set_state(AssistantState.SPEAKING)
        if self._config.get("voice_enabled", True) and self._tts.is_ready:
            self._tts.speak(text)

    # ------------------------------------------------------------------
    # Command history
    # ------------------------------------------------------------------

    def _record_history(self, user_text: str, result: CommandResult) -> None:
        if not self._config.get("save_history", True):
            return
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "command": user_text,
            "intent": result.intent,
            "success": result.success,
            "response": result.message,
        }
        max_entries = int(self._config.get("max_history_entries", 100))
        self._history.append(entry)
        if len(self._history) > max_entries:
            self._history = self._history[-max_entries:]
        self._save_history()

    def _load_history(self) -> None:
        if _HISTORY_PATH.exists():
            try:
                self._history = json.loads(
                    _HISTORY_PATH.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                logger.warning("Corrupted history file; starting fresh.")
                self._history = []

    def _save_history(self) -> None:
        try:
            _HISTORY_PATH.write_text(
                json.dumps(self._history, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error("Failed to save history: %s", exc)

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
        if _HISTORY_PATH.exists():
            _HISTORY_PATH.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Settings bridge
    # ------------------------------------------------------------------

    def update_settings(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            self._config.set(key, value)
        # Apply TTS settings live
        if "speech_rate" in kwargs:
            self._tts.set_rate(int(kwargs["speech_rate"]))
        if "volume" in kwargs:
            self._tts.set_volume(float(kwargs["volume"]))
        if "voice_enabled" in kwargs and not kwargs["voice_enabled"]:
            self._tts.mute()
        if "voice_enabled" in kwargs and kwargs["voice_enabled"]:
            self._tts.unmute()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        """Release all resources."""
        self._sr.stop()
        self._tts.shutdown()
        self._save_history()
        self._set_state(AssistantState.STOPPED)
        logger.info("Voice assistant shut down.")
