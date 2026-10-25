"""
voice_panel.py — Microphone button and listening / speaking status display.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class VoicePanel(QFrame):
    """Displays the mic button and current assistant state."""

    mic_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("voicePanel")
        self._build_ui()
        self._listening = False

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        self._mic_btn = QPushButton("🎤")
        self._mic_btn.setObjectName("micButton")
        self._mic_btn.setToolTip("Click to start listening (push-to-talk)")
        self._mic_btn.clicked.connect(self.mic_clicked.emit)
        layout.addWidget(self._mic_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self._mode_label = QLabel("Push to Talk")
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mode_label.setStyleSheet("color: #666688; font-size: 11px;")
        layout.addWidget(self._mode_label)

    # ------------------------------------------------------------------
    # State updates (called from the main thread)
    # ------------------------------------------------------------------

    def set_state(self, state_name: str) -> None:
        labels = {
            "IDLE": "Ready",
            "LISTENING": "Listening…",
            "PROCESSING": "Processing…",
            "EXECUTING": "Executing…",
            "SPEAKING": "Speaking…",
            "ERROR": "Error",
            "STOPPED": "Stopped",
        }
        self._status_label.setText(labels.get(state_name, state_name))

        is_listening = state_name == "LISTENING"
        self._mic_btn.setProperty("listening", is_listening)
        # Force style recalculation
        self._mic_btn.style().unpolish(self._mic_btn)
        self._mic_btn.style().polish(self._mic_btn)
        self._listening = is_listening

    def set_recognition_mode(self, mode: str) -> None:
        self._mode_label.setText(f"Push to Talk • {mode.title()} recognition")
