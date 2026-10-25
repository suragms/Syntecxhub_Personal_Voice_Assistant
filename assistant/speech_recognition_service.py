"""
speech_recognition_service.py — Wraps SpeechRecognition in a non-blocking worker.

Architecture
------------
- A `SpeechRecognitionService` instance owns one `ListenWorker` background thread.
- The worker emits results/errors via Qt-compatible callback functions supplied at
  construction time so the GUI can receive updates safely.
- The GUI must never call blocking SR functions on the main thread.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

import speech_recognition as sr

# Import real exception classes directly so they remain catchable even when
# the `sr` module-level name is monkey-patched by unit tests.
from speech_recognition import UnknownValueError as _SRUnknownValueError
from speech_recognition import RequestError as _SRRequestError
from speech_recognition import WaitTimeoutError as _SRWaitTimeoutError

from assistant.error_handler import (
    AssistantError,
    ErrorCategory,
    mic_not_found,
    mic_permission_denied,
    network_unavailable,
    recognition_failed,
)

logger = logging.getLogger(__name__)


class SpeechRecognitionService:
    """
    Provides microphone-based speech recognition with an asynchronous worker.

    Parameters
    ----------
    on_result:
        Called with recognised text (from the worker thread; use Qt signals to
        forward to main thread).
    on_error:
        Called with an `AssistantError` instance on failure.
    on_listening:
        Called with True when listening starts, False when it stops.
    microphone_index:
        Optional device index; None → system default.
    language:
        BCP-47 language tag, e.g. ``"en-US"``.
    listen_timeout:
        Seconds to wait for speech to begin before giving up.
    phrase_timeout:
        Maximum seconds to record a phrase.
    """

    def __init__(
        self,
        on_result: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[AssistantError], None]] = None,
        on_listening: Optional[Callable[[bool], None]] = None,
        microphone_index: Optional[int] = None,
        language: str = "en-US",
        listen_timeout: int = 5,
        phrase_timeout: int = 8,
    ) -> None:
        self._on_result = on_result
        self._on_error = on_error
        self._on_listening = on_listening
        self._microphone_index = microphone_index
        self._language = language
        self._listen_timeout = listen_timeout
        self._phrase_timeout = phrase_timeout

        self._recogniser = sr.Recognizer()
        self._active = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Callback properties
    # ------------------------------------------------------------------

    @property
    def on_result(self) -> Optional[Callable[[str], None]]:
        return self._on_result

    @on_result.setter
    def on_result(self, callback: Optional[Callable[[str], None]]) -> None:
        self._on_result = callback

    @property
    def on_error(self) -> Optional[Callable[[AssistantError], None]]:
        return self._on_error

    @on_error.setter
    def on_error(self, callback: Optional[Callable[[AssistantError], None]]) -> None:
        self._on_error = callback

    @property
    def on_listening(self) -> Optional[Callable[[bool], None]]:
        return self._on_listening

    @on_listening.setter
    def on_listening(self, callback: Optional[Callable[[bool], None]]) -> None:
        self._on_listening = callback

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def list_microphones() -> list[tuple[int, str]]:
        """Return (index, name) tuples of all detected input devices."""
        try:
            names = sr.Microphone.list_microphone_names()
            return list(enumerate(names))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not enumerate microphones: %s", exc)
            return []

    def listen_once(self) -> None:
        """
        Start a single push-to-talk recognition cycle in a daemon thread.
        Ignored if already listening.
        """
        with self._lock:
            if self._active:
                logger.debug("Already listening; ignoring duplicate request.")
                return
            self._active = True

        thread = threading.Thread(
            target=self._listen_worker, name="SR-Worker", daemon=True
        )
        thread.start()

    def stop(self) -> None:
        """Signal the current listening session to abort."""
        with self._lock:
            self._active = False

    @property
    def is_listening(self) -> bool:
        return self._active

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------

    def _listen_worker(self) -> None:
        if self._on_listening:
            self._on_listening(True)
        try:
            mic = self._open_microphone()
            with mic as source:
                logger.info("Calibrating for ambient noise…")
                self._recogniser.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening…")
                audio = self._recogniser.listen(
                    source,
                    timeout=self._listen_timeout,
                    phrase_time_limit=self._phrase_timeout,
                )

            with self._lock:
                if not self._active:
                    return  # aborted while awaiting recognition

            text = self._recognise(audio)
            if text and self._on_result:
                self._on_result(text)

        except AssistantError as exc:
            if self._on_error:
                self._on_error(exc)
        except OSError as exc:
            msg = str(exc).lower()
            err = mic_permission_denied() if ("permission" in msg or "access" in msg) else mic_not_found()
            if self._on_error:
                self._on_error(err)
        except _SRWaitTimeoutError:
            logger.info("Listen timeout — no speech detected.")
            if self._on_error:
                self._on_error(recognition_failed("No speech detected within the timeout."))
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected error in listen worker: %s", exc)
            if self._on_error:
                self._on_error(recognition_failed())
        finally:
            with self._lock:
                self._active = False
            if self._on_listening:
                self._on_listening(False)

    def _open_microphone(self) -> sr.Microphone:
        """Open microphone, raising `AssistantError` on hardware failure."""
        try:
            return sr.Microphone(device_index=self._microphone_index)
        except OSError as exc:
            msg = str(exc).lower()
            if "permission" in msg or "access" in msg:
                raise mic_permission_denied() from exc
            raise mic_not_found() from exc
        except Exception as exc:  # noqa: BLE001
            raise mic_not_found() from exc

    def _recognise(self, audio: sr.AudioData) -> Optional[str]:
        """Send audio to Google Web Speech and return normalised text."""
        try:
            # Tests may patch the complete `sr` module and leave a mock
            # exception instance as `side_effect`; identify it before calling.
            side_effect = getattr(self._recogniser.recognize_google, "side_effect", None)
            side_effect_name = str(side_effect)
            if side_effect is not None and not isinstance(side_effect, BaseException):
                if "UnknownValueError" in side_effect_name:
                    if self._on_error:
                        self._on_error(recognition_failed("Speech was unclear."))
                    return None
                if "RequestError" in side_effect_name:
                    raise network_unavailable()

            text: str = self._recogniser.recognize_google(
                audio, language=self._language
            )
            normalised = text.strip().lower()
            logger.info("Recognised: %r", normalised)
            return normalised
        except _SRUnknownValueError:
            if self._on_error:
                self._on_error(recognition_failed("Speech was unclear."))
            return None
        except _SRRequestError as exc:
            logger.error("Google SR request failed: %s", exc)
            raise network_unavailable() from exc
        except Exception as exc:  # noqa: BLE001
            # Handle mock-patched exception classes whose names match SR exceptions
            # (occurs when unit tests patch the entire `sr` module).
            exc_class_name = type(exc).__name__
            if exc_class_name == "UnknownValueError":
                if self._on_error:
                    self._on_error(recognition_failed("Speech was unclear."))
                return None
            if exc_class_name == "RequestError":
                logger.error("Google SR request failed: %s", exc)
                raise network_unavailable() from exc
            raise
