"""
main_window.py — Primary application window for the SURA Voice Assistant.

Layout (top → bottom)
  ┌─────────────────────────────────────┐
  │  Header (title, subtitle, buttons)  │
  ├──────────────┬──────────────────────┤
  │  VoicePanel  │  ConversationPanel   │  ← central splitter
  │  (mic, state)│  (chat history)      │
  ├──────────────┴──────────────────────┤
  │  Text input row (QLineEdit + Send)  │
  ├─────────────────────────────────────┤
  │  Toolbar (Commands | History | Sett)│
  └─────────────────────────────────────┘

Side panels (Commands, History, Settings) are shown in a stacked widget
below the main splitter when a toolbar button is active.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.conversation_panel import ConversationPanel
from gui.styles import get_theme
from gui.voice_panel import VoicePanel

if TYPE_CHECKING:
    from assistant.voice_assistant import VoiceAssistant

logger = logging.getLogger(__name__)

# Indices for the side-panel stack
_SIDE_NONE = -1
_SIDE_COMMANDS = 0
_SIDE_HISTORY = 1
_SIDE_SETTINGS = 2


class MainWindow(QMainWindow):
    """Top-level window; owns all GUI sub-panels and wires assistant signals."""

    def __init__(self, assistant: "VoiceAssistant") -> None:
        super().__init__()
        self._assistant = assistant
        self._active_side: int = _SIDE_NONE

        self.setWindowTitle("SURA — Personal Voice Assistant")
        self.setMinimumSize(720, 540)
        self.resize(900, 620)

        # Apply initial theme
        theme_name = assistant.config.get("theme", "dark")
        self.setStyleSheet(get_theme(theme_name))

        self._build_ui()
        self._connect_signals()

        # Populate history panel from saved data
        self._history_panel.load_history(assistant.get_history())

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._make_header())

        # Central splitter: voice panel left, conversation right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        self._voice_panel = VoicePanel()
        self._voice_panel.setMinimumWidth(160)
        self._voice_panel.setMaximumWidth(220)
        splitter.addWidget(self._voice_panel)

        self._conv_panel = ConversationPanel()
        self._conv_panel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        splitter.addWidget(self._conv_panel)
        splitter.setStretchFactor(1, 3)

        root_layout.addWidget(splitter, stretch=1)

        # Side panel stack (Commands / History / Settings)
        self._side_stack = QStackedWidget()
        self._side_stack.setVisible(False)
        self._side_stack.setMaximumHeight(240)

        self._commands_panel = self._make_commands_panel()
        self._history_panel = self._make_history_panel_widget()
        self._settings_panel = self._make_settings_panel()

        self._side_stack.addWidget(self._commands_panel)   # index 0
        self._side_stack.addWidget(self._history_panel)    # index 1
        self._side_stack.addWidget(self._settings_panel)   # index 2

        root_layout.addWidget(self._side_stack)
        root_layout.addWidget(self._make_input_row())
        root_layout.addWidget(self._make_toolbar())

    def _make_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("headerFrame")
        row = QHBoxLayout(frame)
        row.setContentsMargins(16, 8, 16, 8)

        title = QLabel("SURA")
        title.setObjectName("headerTitle")
        row.addWidget(title)

        subtitle = QLabel("Personal Voice Assistant · Syntecxhub AI Internship")
        subtitle.setObjectName("headerSubtitle")
        row.addWidget(subtitle)

        row.addStretch()

        self._status_dot = QLabel("●")
        self._status_dot.setStyleSheet("color: #4caf50; font-size: 12px;")
        self._status_dot.setToolTip("Assistant status")
        row.addWidget(self._status_dot)

        return frame

    def _make_input_row(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("inputFrame")
        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(8)

        self._input_field = QLineEdit()
        self._input_field.setObjectName("commandInput")
        self._input_field.setPlaceholderText("Type a command and press Enter…")
        self._input_field.returnPressed.connect(self._on_send)
        row.addWidget(self._input_field, stretch=1)

        send_btn = QPushButton("Send")
        send_btn.setObjectName("sendButton")
        send_btn.clicked.connect(self._on_send)
        row.addWidget(send_btn)

        return frame

    def _make_toolbar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("toolbar")
        row = QHBoxLayout(frame)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(6)

        self._btn_commands = QPushButton("📋 Commands")
        self._btn_commands.setCheckable(True)
        self._btn_commands.clicked.connect(lambda: self._toggle_side(_SIDE_COMMANDS))
        row.addWidget(self._btn_commands)

        self._btn_history = QPushButton("🕒 History")
        self._btn_history.setCheckable(True)
        self._btn_history.clicked.connect(lambda: self._toggle_side(_SIDE_HISTORY))
        row.addWidget(self._btn_history)

        self._btn_settings = QPushButton("⚙ Settings")
        self._btn_settings.setCheckable(True)
        self._btn_settings.clicked.connect(lambda: self._toggle_side(_SIDE_SETTINGS))
        row.addWidget(self._btn_settings)

        row.addStretch()

        return frame

    # ------------------------------------------------------------------
    # Side panel factories
    # ------------------------------------------------------------------

    def _make_commands_panel(self) -> QWidget:
        """Build the sample-commands quick-reference panel."""
        from gui.command_history import CommandHistoryPanel as _CH  # reuse layout
        from PySide6.QtWidgets import QScrollArea, QVBoxLayout as _VBL

        outer = QWidget()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(8, 4, 8, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        container_layout.setSpacing(4)

        samples = self._assistant.processor.get_sample_commands()
        for category, commands in samples.items():
            cat_label = QLabel(category)
            cat_label.setProperty("class", "categoryHeader")
            container_layout.addWidget(cat_label)

            for item in commands:
                btn = QPushButton(item["command"])
                btn.setProperty("class", "commandButton")
                btn.setToolTip(item["description"])
                cmd_text = item["command"]
                btn.clicked.connect(lambda _, t=cmd_text: self._run_typed_command(t))
                container_layout.addWidget(btn)

        scroll.setWidget(container)
        layout.addWidget(scroll)
        return outer

    def _make_history_panel_widget(self):
        from gui.command_history import CommandHistoryPanel
        panel = CommandHistoryPanel()
        panel.replay_requested.connect(self._run_typed_command)
        return panel

    def _make_settings_panel(self):
        from gui.settings_panel import SettingsPanel
        panel = SettingsPanel(self._assistant)
        panel.theme_changed.connect(self._apply_theme)
        panel.history_clear_requested.connect(self._on_clear_history)
        return panel

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        asst = self._assistant

        asst.state_changed.connect(self._on_state_changed)
        asst.result_ready.connect(self._on_result_ready)
        asst.error_occurred.connect(self._on_error)

        self._voice_panel.mic_clicked.connect(self._on_mic_clicked)

    # ------------------------------------------------------------------
    # Slots — assistant signals
    # ------------------------------------------------------------------

    @Slot(str)
    def _on_state_changed(self, state_name: str) -> None:
        self._voice_panel.set_state(state_name)

        # Update header dot colour
        colours = {
            "IDLE": "#4caf50",
            "LISTENING": "#2196f3",
            "PROCESSING": "#ff9800",
            "EXECUTING": "#ff9800",
            "SPEAKING": "#9c27b0",
            "ERROR": "#e94560",
            "STOPPED": "#666688",
        }
        self._status_dot.setStyleSheet(
            f"color: {colours.get(state_name, '#4caf50')}; font-size: 12px;"
        )

        if state_name == "STOPPED":
            QApplication.quit()

    @Slot(str, str, bool)
    def _on_result_ready(self, user_text: str, response: str, success: bool) -> None:
        self._conv_panel.add_user_message(user_text)
        if success:
            self._conv_panel.add_assistant_message(response)
        else:
            self._conv_panel.add_error_message(response)

        # Prepend to history panel
        import datetime
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "command": user_text,
            "intent": "—",
            "success": success,
            "response": response,
        }
        self._history_panel.prepend_entry(entry)

    @Slot(str)
    def _on_error(self, message: str) -> None:
        self._conv_panel.add_error_message(message)

    # ------------------------------------------------------------------
    # Slots — local UI
    # ------------------------------------------------------------------

    @Slot()
    def _on_mic_clicked(self) -> None:
        from assistant.voice_assistant import AssistantState
        if self._assistant.state == AssistantState.LISTENING:
            self._assistant.stop_listening()
        else:
            self._assistant.start_listening()

    @Slot()
    def _on_send(self) -> None:
        text = self._input_field.text().strip()
        if not text:
            return
        self._input_field.clear()
        self._assistant.process_text(text)

    def _run_typed_command(self, text: str) -> None:
        """Inject a command as if the user had typed and sent it."""
        self._input_field.setText(text)
        self._on_send()

    def _toggle_side(self, panel_idx: int) -> None:
        """Show/hide the bottom side panel."""
        buttons = [self._btn_commands, self._btn_history, self._btn_settings]

        if self._active_side == panel_idx:
            # Collapse
            self._side_stack.setVisible(False)
            self._active_side = _SIDE_NONE
            for btn in buttons:
                btn.setChecked(False)
        else:
            self._side_stack.setCurrentIndex(panel_idx)
            self._side_stack.setVisible(True)
            self._active_side = panel_idx
            for i, btn in enumerate(buttons):
                btn.setChecked(i == panel_idx)

    def _apply_theme(self, theme_name: str) -> None:
        self.setStyleSheet(get_theme(theme_name))

    def _on_clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Delete all saved command history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._assistant.clear_history()
            self._history_panel.clear()

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        self._assistant.shutdown()
        event.accept()
