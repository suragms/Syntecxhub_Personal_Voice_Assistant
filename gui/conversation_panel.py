"""
conversation_panel.py — Scrollable chat-style conversation history.

Messages are displayed as styled bubbles: user on the left, assistant on
the right, errors with a red tint.  Each entry shows a timestamp.
"""

from __future__ import annotations

import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _MessageBubble(QFrame):
    """A single message bubble with text and timestamp."""

    def __init__(
        self,
        text: str,
        sender: str,          # "user" | "assistant" | "error"
        timestamp: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        css_class = {
            "user": "userMessage",
            "assistant": "assistantMessage",
            "error": "errorMessage",
        }.get(sender, "assistantMessage")

        self.setProperty("class", css_class)
        self.setObjectName(css_class)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Sender label
        sender_label = QLabel(
            "You" if sender == "user" else ("SURA" if sender == "assistant" else "⚠ Error")
        )
        sender_label.setStyleSheet(
            "font-weight: bold; font-size: 11px; color: #e94560;"
            if sender == "user"
            else "font-weight: bold; font-size: 11px; color: #8888cc;"
        )
        layout.addWidget(sender_label)

        # Message text (word-wrap)
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        layout.addWidget(msg_label)

        # Timestamp
        ts_label = QLabel(timestamp)
        ts_label.setProperty("class", "timestamp")
        ts_label.setObjectName("timestamp")
        ts_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(ts_label)


class ConversationPanel(QFrame):
    """Scrollable panel that displays the conversation history."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("conversationPanel")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("conversationScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._container_layout.setSpacing(6)
        self._container_layout.setContentsMargins(8, 8, 8, 8)

        # Welcome message
        self._add_bubble(
            "Hello! I'm SURA, your personal voice assistant. "
            "Click the microphone or type a command to get started.",
            sender="assistant",
        )

        self._scroll.setWidget(self._container)
        outer_layout.addWidget(self._scroll)

    # ------------------------------------------------------------------
    # Public API (called from the main thread via Qt signals)
    # ------------------------------------------------------------------

    def add_user_message(self, text: str) -> None:
        """Append a user-originating message bubble."""
        self._add_bubble(text, sender="user")

    def add_assistant_message(self, text: str) -> None:
        """Append an assistant-originating message bubble."""
        self._add_bubble(text, sender="assistant")

    def add_error_message(self, text: str) -> None:
        """Append an error message bubble."""
        self._add_bubble(text, sender="error")

    def clear(self) -> None:
        """Remove all message bubbles."""
        while self._container_layout.count():
            item = self._container_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _add_bubble(self, text: str, sender: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M")
        bubble = _MessageBubble(text, sender=sender, timestamp=ts, parent=self._container)
        self._container_layout.addWidget(bubble)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """Scroll to the newest message after the layout has settled."""
        # Use the scroll bar's maximum to jump to the end
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
        # Also schedule a deferred scroll in case layout isn't complete yet
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, lambda: sb.setValue(sb.maximum()))
