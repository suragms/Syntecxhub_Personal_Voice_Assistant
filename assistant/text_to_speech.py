"""
text_to_speech.py — pyttsx3-backed TTS engine with thread-safe queuing.

pyttsx3 must run on the thread that initialised it (Windows SAPI5 constraint).
We create a dedicated daemon thread that owns the engine and processes a
speak-request queue. All public methods are safe to call from any thread.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

import pyttsx3

from assistant.error_handler import ErrorHandler, tts_failed

logger = logging.getLogger(__name__)

_SENTINEL = object()  # signals the worker to shut down


class TextToSpeechEngine:
    """Thread-safe wrapper around pyttsx3."""

    def __init__(self, speech_rate: int = 170, volume: float = 0.8) -> None:
        self._speech_rate = speech_rate
        self._volume = volume
        self._muted = False
        self._ready = False

        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(
            target=self._worker, name="TTS-Worker", daemon=True
        )
        self._thread.start()

    # ------------------------------------------------------------------
    # Public API (all thread-safe)
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        return self._ready

    def speak(self, text: str) -> None:
        """Queue *text* for speech. No-op when muted or whitespace-only."""
        if not text or not text.strip() or self._muted:
            return
        self._queue.put(("speak", text))

    def stop(self) -> None:
        """Interrupt any ongoing speech."""
        self._queue.put(("stop", None))

    def set_rate(self, rate: int) -> None:
        self._speech_rate = rate
        self._queue.put(("set_rate", rate))

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        self._queue.put(("set_volume", self._volume))

    def set_voice(self, voice_id: str) -> None:
        self._queue.put(("set_voice", voice_id))

    def mute(self) -> None:
        self._muted = True
        logger.info("TTS muted.")

    def unmute(self) -> None:
        self._muted = False
        logger.info("TTS unmuted.")

    @property
    def is_muted(self) -> bool:
        return self._muted

    def get_voices(self) -> list[dict]:
        """Return available voice info; called before the worker starts, so safe."""
        try:
            engine = pyttsx3.init()
            voices = [
                {"id": v.id, "name": v.name, "languages": v.languages}
                for v in engine.getProperty("voices")
            ]
            engine.stop()
            return voices
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not enumerate voices: %s", exc)
            return []

    def shutdown(self) -> None:
        """Gracefully stop the worker thread."""
        self._queue.put(_SENTINEL)
        self._thread.join(timeout=3)

    # ------------------------------------------------------------------
    # Worker (runs on dedicated thread)
    # ------------------------------------------------------------------

    def _worker(self) -> None:
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", self._speech_rate)
            engine.setProperty("volume", self._volume)
            self._ready = True
            logger.info("TTS engine initialised (rate=%d, volume=%.1f).", self._speech_rate, self._volume)
        except Exception as exc:  # noqa: BLE001
            err = tts_failed(exc)
            ErrorHandler.handle(err, context="TTS init")
            return  # engine unavailable; thread exits cleanly

        while True:
            item = self._queue.get()
            if item is _SENTINEL:
                break
            cmd, payload = item
            try:
                if cmd == "speak":
                    engine.say(payload)
                    engine.runAndWait()
                elif cmd == "stop":
                    engine.stop()
                elif cmd == "set_rate":
                    engine.setProperty("rate", payload)
                elif cmd == "set_volume":
                    engine.setProperty("volume", payload)
                elif cmd == "set_voice":
                    engine.setProperty("voice", payload)
            except Exception as exc:  # noqa: BLE001
                logger.error("TTS error during %s: %s", cmd, exc)

        try:
            engine.stop()
        except Exception:  # noqa: BLE001
            pass
        logger.info("TTS worker shut down.")
