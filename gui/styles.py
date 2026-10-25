"""
styles.py — Dark and light theme stylesheets for the SURA GUI.
"""

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

/* Header */
#headerFrame {
    background-color: #16213e;
    border-bottom: 1px solid #0f3460;
    padding: 8px 16px;
}
#headerTitle {
    color: #e94560;
    font-size: 18px;
    font-weight: bold;
}
#headerSubtitle {
    color: #8888aa;
    font-size: 11px;
}

/* Voice Panel */
#voicePanel {
    background-color: #16213e;
    border-radius: 12px;
    padding: 20px;
    margin: 10px;
}
#statusLabel {
    color: #a0a0c0;
    font-size: 14px;
    font-weight: bold;
}

/* Microphone button */
#micButton {
    background-color: #0f3460;
    border: 2px solid #533483;
    border-radius: 35px;
    min-width: 70px;
    min-height: 70px;
    max-width: 70px;
    max-height: 70px;
    font-size: 28px;
    color: #e94560;
}
#micButton:hover {
    background-color: #1a4a7a;
    border-color: #e94560;
}
#micButton:pressed, #micButton[listening="true"] {
    background-color: #e94560;
    color: #ffffff;
}

/* Conversation Panel */
#conversationPanel {
    background-color: #16213e;
    border-radius: 12px;
    padding: 10px;
    margin: 5px 10px;
}
#conversationScroll {
    background-color: transparent;
    border: none;
}
#conversationScroll QScrollBar:vertical {
    width: 6px;
    background: transparent;
}
#conversationScroll QScrollBar::handle:vertical {
    background: #533483;
    border-radius: 3px;
}

/* Message bubbles */
.userMessage {
    background-color: #0f3460;
    border-radius: 10px;
    padding: 8px 12px;
    margin: 4px 40px 4px 10px;
    color: #e0e0e0;
}
.assistantMessage {
    background-color: #1b2838;
    border-radius: 10px;
    padding: 8px 12px;
    margin: 4px 10px 4px 40px;
    color: #e0e0e0;
}
.errorMessage {
    background-color: #3d1f1f;
    border-radius: 10px;
    padding: 8px 12px;
    margin: 4px 10px 4px 40px;
    color: #ff6b6b;
}

/* Text input area */
#inputFrame {
    background-color: #16213e;
    border-top: 1px solid #0f3460;
    padding: 8px 12px;
}
#commandInput {
    background-color: #0f3460;
    border: 1px solid #533483;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e0e0e0;
    font-size: 13px;
}
#commandInput:focus {
    border-color: #e94560;
}
#sendButton {
    background-color: #e94560;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    color: #ffffff;
    font-weight: bold;
}
#sendButton:hover {
    background-color: #ff6b81;
}

/* Bottom toolbar */
#toolbar {
    background-color: #16213e;
    border-top: 1px solid #0f3460;
    padding: 4px 8px;
}
#toolbar QPushButton {
    background-color: #0f3460;
    border: 1px solid #533483;
    border-radius: 6px;
    padding: 6px 14px;
    color: #c0c0e0;
    font-size: 12px;
}
#toolbar QPushButton:hover {
    background-color: #1a4a7a;
    color: #ffffff;
}

/* Settings panel */
#settingsPanel QLabel {
    color: #c0c0e0;
}
#settingsPanel QComboBox, #settingsPanel QSpinBox, #settingsPanel QSlider {
    background-color: #0f3460;
    border: 1px solid #533483;
    border-radius: 4px;
    padding: 4px;
    color: #e0e0e0;
}
#settingsPanel QPushButton {
    background-color: #e94560;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    color: #ffffff;
}
#settingsPanel QPushButton:hover {
    background-color: #ff6b81;
}

/* Commands panel */
#commandsPanel {
    background-color: #16213e;
    border-radius: 12px;
    padding: 10px;
    margin: 5px 10px;
}
#commandsPanel QLabel {
    color: #c0c0e0;
}
.categoryHeader {
    color: #e94560;
    font-size: 14px;
    font-weight: bold;
    padding-top: 8px;
}
.commandButton {
    background-color: #0f3460;
    border: 1px solid #533483;
    border-radius: 6px;
    padding: 6px 10px;
    color: #c0c0e0;
    text-align: left;
    font-size: 12px;
}
.commandButton:hover {
    background-color: #1a4a7a;
    color: #ffffff;
}

/* Timestamp */
.timestamp {
    color: #666688;
    font-size: 10px;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #f5f5fa;
    color: #2d2d3d;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

#headerFrame {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e8;
    padding: 8px 16px;
}
#headerTitle {
    color: #e94560;
    font-size: 18px;
    font-weight: bold;
}
#headerSubtitle {
    color: #888899;
    font-size: 11px;
}

#voicePanel {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    margin: 10px;
    border: 1px solid #e0e0e8;
}
#statusLabel {
    color: #555566;
    font-size: 14px;
    font-weight: bold;
}

#micButton {
    background-color: #e8e8f0;
    border: 2px solid #b0b0d0;
    border-radius: 35px;
    min-width: 70px;
    min-height: 70px;
    max-width: 70px;
    max-height: 70px;
    font-size: 28px;
    color: #e94560;
}
#micButton:hover {
    background-color: #d0d0e8;
    border-color: #e94560;
}
#micButton:pressed, #micButton[listening="true"] {
    background-color: #e94560;
    color: #ffffff;
}

#conversationPanel {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 10px;
    margin: 5px 10px;
    border: 1px solid #e0e0e8;
}
#conversationScroll {
    background-color: transparent;
    border: none;
}

.userMessage {
    background-color: #e8e8f5;
    border-radius: 10px;
    padding: 8px 12px;
    margin: 4px 40px 4px 10px;
    color: #2d2d3d;
}
.assistantMessage {
    background-color: #f0f0f8;
    border-radius: 10px;
    padding: 8px 12px;
    margin: 4px 10px 4px 40px;
    color: #2d2d3d;
}
.errorMessage {
    background-color: #fde0e0;
    border-radius: 10px;
    padding: 8px 12px;
    margin: 4px 10px 4px 40px;
    color: #cc3333;
}

#inputFrame {
    background-color: #ffffff;
    border-top: 1px solid #e0e0e8;
    padding: 8px 12px;
}
#commandInput {
    background-color: #f0f0f8;
    border: 1px solid #c0c0d0;
    border-radius: 8px;
    padding: 8px 12px;
    color: #2d2d3d;
    font-size: 13px;
}
#commandInput:focus {
    border-color: #e94560;
}
#sendButton {
    background-color: #e94560;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    color: #ffffff;
    font-weight: bold;
}
#sendButton:hover {
    background-color: #ff6b81;
}

#toolbar {
    background-color: #ffffff;
    border-top: 1px solid #e0e0e8;
    padding: 4px 8px;
}
#toolbar QPushButton {
    background-color: #e8e8f0;
    border: 1px solid #c0c0d0;
    border-radius: 6px;
    padding: 6px 14px;
    color: #555566;
    font-size: 12px;
}
#toolbar QPushButton:hover {
    background-color: #d0d0e8;
    color: #2d2d3d;
}

#settingsPanel QLabel {
    color: #555566;
}
#settingsPanel QComboBox, #settingsPanel QSpinBox, #settingsPanel QSlider {
    background-color: #f0f0f8;
    border: 1px solid #c0c0d0;
    border-radius: 4px;
    padding: 4px;
    color: #2d2d3d;
}
#settingsPanel QPushButton {
    background-color: #e94560;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    color: #ffffff;
}

#commandsPanel {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 10px;
    margin: 5px 10px;
    border: 1px solid #e0e0e8;
}
.categoryHeader {
    color: #e94560;
    font-size: 14px;
    font-weight: bold;
    padding-top: 8px;
}
.commandButton {
    background-color: #e8e8f0;
    border: 1px solid #c0c0d0;
    border-radius: 6px;
    padding: 6px 10px;
    color: #555566;
    text-align: left;
    font-size: 12px;
}
.commandButton:hover {
    background-color: #d0d0e8;
    color: #2d2d3d;
}
.timestamp {
    color: #999999;
    font-size: 10px;
}
"""


def get_theme(name: str) -> str:
    """Return the stylesheet for the given theme name."""
    if name == "light":
        return LIGHT_THEME
    return DARK_THEME
