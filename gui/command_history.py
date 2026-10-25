"""
command_history.py — Panel displaying past commands with timestamps,
intents, and success/failure indicators.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _HistoryEntry(QFrame):
    """One row in the history list — command text + metadata."""

    replay_requested = Signal(str)

    def __init__(self, entry: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(8)

        # Success indicator dot
        dot = QLabel("●")
        dot.setFixedWidth(14)
        colour = "#4caf50" if entry.get("success") else "#e94560"
        dot.setStyleSheet(f"color: {colour}; font-size: 10px;")
        row.addWidget(dot)

        # Command + intent
        info_col = QVBoxLayout()
        info_col.setSpacing(0)

        cmd_label = QLabel(entry.get("command", ""))
        cmd_label.setWordWrap(True)
        cmd_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_col.addWidget(cmd_label)

        intent_ts = QLabel(
            f"{entry.get('intent', '—')} · {entry.get('timestamp', '')[:16]}"
        )
        intent_ts.setStyleSheet("color: #666688; font-size: 10px;")
        info_col.addWidget(intent_ts)

        row.addLayout(info_col)

        # Replay button
        play_btn = QPushButton("▶")
        play_btn.setFixedSize(24, 24)
        play_btn.setToolTip("Re-run this command")
        cmd_text = entry.get("command", "")
        play_btn.clicked.connect(lambda: self.replay_requested.emit(cmd_text))
        row.addWidget(play_btn)


class CommandHistoryPanel(QFrame):
    """
    Scrollable list of executed commands.

    Signals
    -------
    replay_requested(command: str)   — user clicked the replay button
    """

    replay_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("commandsPanel")
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("Command History")
        title.setProperty("class", "categoryHeader")
        title.setObjectName("categoryHeader")
        title.setContentsMargins(8, 8, 8, 4)
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(8, 4, 8, 8)

        self._empty_label = QLabel("No commands yet.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #666688; font-size: 12px; padding: 20px;")
        self._layout.addWidget(self._empty_label)

        scroll.setWidget(self._container)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_history(self, entries: list[dict[str, Any]]) -> None:
        """Populate the panel with *entries* (newest first)."""
        # Clear existing rows (keep empty label logic)
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not entries:
            self._layout.addWidget(self._empty_label)
            self._empty_label.setVisible(True)
            return

        self._empty_label.setParent(None)

        for entry in reversed(entries):          # newest at the top
            row = _HistoryEntry(entry, parent=self._container)
            row.replay_requested.connect(self.replay_requested.emit)
            self._layout.addWidget(row)

    def prepend_entry(self, entry: dict[str, Any]) -> None:
        """Insert a single entry at the top of the list."""
        if self._empty_label.isVisible():
            self._empty_label.setVisible(False)
            self._empty_label.setParent(None)

        row = _HistoryEntry(entry, parent=self._container)
        row.replay_requested.connect(self.replay_requested.emit)
        self._layout.insertWidget(0, row)

    def clear(self) -> None:
        """Remove all rows and show the empty placeholder."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._empty_label.setParent(self._container)
        self._layout.addWidget(self._empty_label)
        self._empty_label.setVisible(True)
