"""
settings_panel.py — Persistent settings panel (microphone, voice, rate,
volume, recognition mode, theme, history management).

All changes are applied immediately via VoiceAssistant.update_settings()
and saved to user_settings.json through ConfigManager.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from assistant.voice_assistant import VoiceAssistant


class SettingsPanel(QFrame):
    """
    Expandable settings panel.

    Signals
    -------
    theme_changed(theme_name: str)   — emitted when the user switches theme
    history_clear_requested()        — emitted when the user clicks Clear History
    """

    theme_changed = Signal(str)
    history_clear_requested = Signal()

    def __init__(self, assistant: "VoiceAssistant", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsPanel")
        self._assistant = assistant
        self._build_ui()
        self._load_current_settings()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("settingsScroll")

        content = QWidget()
        content.setObjectName("settingsContent")
        form = QFormLayout(content)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setSpacing(10)
        form.setContentsMargins(12, 12, 12, 12)

        # -- Microphone --------------------------------------------------
        self._mic_combo = QComboBox()
        self._mic_combo.setToolTip("Select the input microphone device")
        self._populate_microphones()
        self._mic_combo.currentIndexChanged.connect(self._on_mic_changed)
        form.addRow(QLabel("Microphone:"), self._mic_combo)

        # -- Recognition mode --------------------------------------------
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Google (online)", "Offline (Vosk)"])
        self._mode_combo.setToolTip("Speech recognition backend")
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        form.addRow(QLabel("Recognition:"), self._mode_combo)

        # -- Language ----------------------------------------------------
        self._lang_combo = QComboBox()
        languages = [
            ("English (US)", "en-US"),
            ("English (UK)", "en-GB"),
            ("Spanish", "es-ES"),
            ("French", "fr-FR"),
            ("German", "de-DE"),
        ]
        for label, code in languages:
            self._lang_combo.addItem(label, userData=code)
        self._lang_combo.currentIndexChanged.connect(self._on_lang_changed)
        form.addRow(QLabel("Language:"), self._lang_combo)

        # -- Voice (TTS) -------------------------------------------------
        self._voice_combo = QComboBox()
        self._populate_voices()
        self._voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        form.addRow(QLabel("Voice:"), self._voice_combo)

        # -- Speech rate -------------------------------------------------
        rate_widget = QWidget()
        rate_layout = QHBoxLayout(rate_widget)
        rate_layout.setContentsMargins(0, 0, 0, 0)
        self._rate_spin = QSpinBox()
        self._rate_spin.setRange(50, 400)
        self._rate_spin.setSingleStep(10)
        self._rate_spin.setSuffix(" wpm")
        self._rate_spin.valueChanged.connect(self._on_rate_changed)
        rate_layout.addWidget(self._rate_spin)
        form.addRow(QLabel("Speech Rate:"), rate_widget)

        # -- Volume ------------------------------------------------------
        vol_widget = QWidget()
        vol_layout = QHBoxLayout(vol_widget)
        vol_layout.setContentsMargins(0, 0, 0, 0)
        self._vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._vol_slider.setRange(0, 100)
        self._vol_slider.setTickInterval(10)
        self._vol_label = QLabel("80%")
        self._vol_label.setMinimumWidth(36)
        self._vol_slider.valueChanged.connect(self._on_volume_changed)
        vol_layout.addWidget(self._vol_slider)
        vol_layout.addWidget(self._vol_label)
        form.addRow(QLabel("Volume:"), vol_widget)

        # -- Theme -------------------------------------------------------
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        form.addRow(QLabel("Theme:"), self._theme_combo)

        # -- Actions -----------------------------------------------------
        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        clear_btn = QPushButton("Clear History")
        clear_btn.setToolTip("Delete all saved command history")
        clear_btn.clicked.connect(self.history_clear_requested.emit)
        btn_layout.addWidget(clear_btn)

        reset_btn = QPushButton("Reset Defaults")
        reset_btn.setToolTip("Reset all settings to factory defaults")
        reset_btn.clicked.connect(self._on_reset_defaults)
        btn_layout.addWidget(reset_btn)

        form.addRow("", btn_row)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Populate dynamic controls
    # ------------------------------------------------------------------

    def _populate_microphones(self) -> None:
        """Fill the microphone combo from the SR service."""
        self._mic_combo.clear()
        self._mic_combo.addItem("System Default", userData=None)
        try:
            from assistant.speech_recognition_service import SpeechRecognitionService
            mics = SpeechRecognitionService.list_microphones()
            for idx, name in mics:
                self._mic_combo.addItem(name, userData=idx)
        except Exception:
            pass  # SR not available — keep "System Default" only

    def _populate_voices(self) -> None:
        """Fill the voice combo from the TTS engine."""
        self._voice_combo.clear()
        self._voice_combo.addItem("Default", userData=None)
        try:
            voices = self._assistant.tts.get_voices()
            for v in voices:
                display = v.get("name", v.get("id", "Unknown"))
                self._voice_combo.addItem(display, userData=v.get("id"))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Load current settings into controls
    # ------------------------------------------------------------------

    def _load_current_settings(self) -> None:
        cfg = self._assistant.config

        # Speech rate
        self._rate_spin.blockSignals(True)
        self._rate_spin.setValue(int(cfg.get("speech_rate", 170)))
        self._rate_spin.blockSignals(False)

        # Volume
        vol = float(cfg.get("volume", 0.8))
        self._vol_slider.blockSignals(True)
        self._vol_slider.setValue(int(vol * 100))
        self._vol_label.setText(f"{int(vol * 100)}%")
        self._vol_slider.blockSignals(False)

        # Theme
        theme = cfg.get("theme", "dark")
        self._theme_combo.blockSignals(True)
        self._theme_combo.setCurrentIndex(0 if theme == "dark" else 1)
        self._theme_combo.blockSignals(False)

        # Language
        lang = cfg.get("language", "en-US")
        for i in range(self._lang_combo.count()):
            if self._lang_combo.itemData(i) == lang:
                self._lang_combo.setCurrentIndex(i)
                break

        # Recognition mode
        mode = cfg.get("recognition_mode", "google")
        self._mode_combo.setCurrentIndex(0 if mode == "google" else 1)

        # Microphone index
        mic_idx = cfg.get("microphone_index")
        for i in range(self._mic_combo.count()):
            if self._mic_combo.itemData(i) == mic_idx:
                self._mic_combo.setCurrentIndex(i)
                break

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_mic_changed(self, index: int) -> None:
        mic_idx = self._mic_combo.itemData(index)
        self._assistant.update_settings(microphone_index=mic_idx)

    def _on_mode_changed(self, index: int) -> None:
        mode = "google" if index == 0 else "vosk"
        self._assistant.update_settings(recognition_mode=mode)

    def _on_lang_changed(self, index: int) -> None:
        lang = self._lang_combo.itemData(index)
        self._assistant.update_settings(language=lang)

    def _on_voice_changed(self, index: int) -> None:
        voice_id = self._voice_combo.itemData(index)
        if voice_id is not None:
            self._assistant.update_settings(voice_id=voice_id)

    def _on_rate_changed(self, value: int) -> None:
        self._assistant.update_settings(speech_rate=value)

    def _on_volume_changed(self, value: int) -> None:
        self._vol_label.setText(f"{value}%")
        self._assistant.update_settings(volume=value / 100.0)

    def _on_theme_changed(self, index: int) -> None:
        theme = "dark" if index == 0 else "light"
        self._assistant.update_settings(theme=theme)
        self.theme_changed.emit(theme)

    def _on_reset_defaults(self) -> None:
        self._assistant.config.reset_to_defaults()
        self._load_current_settings()
        # Re-apply TTS defaults
        cfg = self._assistant.config
        self._assistant.update_settings(
            speech_rate=int(cfg.get("speech_rate", 170)),
            volume=float(cfg.get("volume", 0.8)),
        )
