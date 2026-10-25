"""Build a Windows distribution of the SURA Voice Assistant with PyInstaller.

Run from the repository root:
    py -m pip install pyinstaller
    py scripts/build_windows.py

The generated application is placed in ``dist/SURA/``. This script packages the
application only; test the resulting executable on the target Windows machine
before distributing it.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = PROJECT_ROOT / "main.py"
CONFIG_DIR = PROJECT_ROOT / "config"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"


def _require_windows() -> None:
    if sys.platform != "win32":
        raise SystemExit("This packaging helper supports Windows builds only.")


def _require_entry_files() -> None:
    missing = [path for path in (ENTRY_POINT, CONFIG_DIR) if not path.exists()]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise SystemExit(f"Required project files are missing: {missing_text}")


def _require_pyinstaller() -> None:
    if shutil.which("pyinstaller") is None:
        try:
            __import__("PyInstaller")
        except ImportError as exc:
            raise SystemExit(
                "PyInstaller is not installed. Run: py -m pip install pyinstaller"
            ) from exc


def build() -> None:
    """Invoke PyInstaller with the project's Windows bundle settings."""
    _require_windows()
    _require_entry_files()
    _require_pyinstaller()

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "SURA",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--add-data",
        f"{CONFIG_DIR};config",
        "--hidden-import",
        "pyttsx3.drivers.sapi5",
        "--hidden-import",
        "speech_recognition",
        str(ENTRY_POINT),
    ]

    print("Building SURA Windows distribution...")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)
    print(f"Build complete: {DIST_DIR / 'SURA' / 'SURA.exe'}")


if __name__ == "__main__":
    build()
