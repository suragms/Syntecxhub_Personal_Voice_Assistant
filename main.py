"""
main.py — Application entry point for the SURA Voice Assistant.

Usage
-----
    python main.py [--theme dark|light] [--log-level DEBUG|INFO|WARNING]

The script:
  1. Configures logging (console + rotating file handler).
  2. Loads the QApplication and applies the initial theme.
  3. Constructs VoiceAssistant (loads config, initialises TTS + SR).
  4. Opens MainWindow and starts the Qt event loop.
  5. Calls VoiceAssistant.shutdown() on exit.
"""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)-30s  %(message)s",
        datefmt="%H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # Rotating file handler (logs/ dir, max 1 MB × 3 backups)
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    fh = RotatingFileHandler(
        log_dir / "sura.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sura",
        description="SURA Personal Voice Assistant",
    )
    parser.add_argument(
        "--theme",
        choices=["dark", "light"],
        default=None,
        help="Override the theme from settings (dark or light).",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        metavar="LEVEL",
        help="Logging verbosity: DEBUG, INFO, WARNING, ERROR (default: INFO).",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    # Bootstrap with INFO so we can log import errors; overridden below
    # once the config is loaded.
    _setup_logging(args.log_level or "INFO")
    logger = logging.getLogger(__name__)
    logger.info("Starting SURA Voice Assistant…")

    # ------------------------------------------------------------------
    # Qt application  (must be created before any Qt object)
    # ------------------------------------------------------------------
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("SURA")
    app.setOrganizationName("Syntecxhub")

    # ------------------------------------------------------------------
    # Assistant core
    # ------------------------------------------------------------------
    from assistant.config_manager import ConfigManager
    from assistant.voice_assistant import VoiceAssistant

    config = ConfigManager()

    # CLI overrides beat stored settings
    if args.theme:
        config.set("theme", args.theme)
    if args.log_level:
        config.set("log_level", args.log_level.upper())

    # Re-apply log level from (possibly overridden) config
    _setup_logging(str(config.get("log_level", "INFO")))

    assistant = VoiceAssistant(config=config)

    # ------------------------------------------------------------------
    # Main window
    # ------------------------------------------------------------------
    from gui.main_window import MainWindow

    window = MainWindow(assistant)
    window.show()

    logger.info("SURA GUI ready.")

    exit_code = app.exec()

    # Ensure clean shutdown even if the window close event wasn't fired
    if assistant.state.name != "STOPPED":
        assistant.shutdown()

    logger.info("SURA exited with code %d.", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
