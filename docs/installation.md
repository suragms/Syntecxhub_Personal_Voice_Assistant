# Windows Installation and Deployment

## 1. Prerequisites

Install the following before setting up SURA:

- Windows 10 or Windows 11
- Python 3.11+ from [python.org](https://www.python.org/downloads/)
- A working microphone for voice input
- Internet access for Google Web Speech recognition
- Windows audio output and an installed SAPI5 voice for spoken replies

During Python installation, enable **Add Python to PATH**.

## 2. Get the Project

Open a terminal in the project folder:

```bash
cd path\to\Syntecxhub_Personal_Voice_Assistant
```

## 3. Create a Virtual Environment

```bash
py -m venv .venv
```

```bash
.venv\Scripts\activate
```

If activation is blocked by a PowerShell execution policy, use Command Prompt or follow your organisation's approved policy procedure; do not disable security controls globally just for this project.

## 4. Upgrade Packaging Tools

```bash
py -m pip install --upgrade pip setuptools wheel
```

## 5. Install Dependencies

```bash
py -m pip install -r requirements.txt
```

SURA uses:

- `PySide6` for the desktop UI.
- `SpeechRecognition` for microphone capture and Google Web Speech integration.
- `pyttsx3` for local Windows SAPI5 speech synthesis.
- `PyAudio` as the microphone backend.

## 6. PyAudio Troubleshooting

PyAudio may not provide a ready-built wheel for every Python release. If the normal dependency installation fails:

1. Confirm your Python version and CPU architecture.
2. Obtain a PyAudio wheel that exactly matches both values from a trusted Python package source.
3. Install the local wheel explicitly.

Example structure only (replace with the actual compatible filename):

```bash
py -m pip install C:\Downloads\PyAudio-compatible-wheel.whl
```

Then rerun:

```bash
py -m pip install -r requirements.txt
```

Do not download executable installers or wheels from unknown sources.

## 7. Start the Application

```bash
py main.py
```

Optional launch settings:

```bash
py main.py --theme light --log-level DEBUG
```

## 8. Allow Microphone Access

If Windows denies microphone use:

1. Open **Settings** → **Privacy & security** → **Microphone**.
2. Enable **Microphone access**.
3. Enable **Let desktop apps access your microphone**.
4. Verify the selected device in **Settings** → **System** → **Sound**.
5. Restart SURA and try the microphone button again.

## 9. Test Typed Commands First

Before testing hardware, enter a typed command such as:

```text
What time is it?
```

Then test an allowlisted action such as `Open Notepad`. Typed commands are useful when diagnosing microphone or connectivity problems.

## 10. Verify Voice Input

1. Click the microphone button.
2. Wait for **Listening**.
3. Say `Hello SURA` or `What time is it?`.
4. Confirm that text appears in the conversation panel.
5. Confirm the spoken reply only if voice output is enabled and Windows audio is available.

Google Web Speech is online. A network error does not indicate a local microphone failure; it means SURA could not complete the recognition request.

## 11. Settings and Local Data

- Defaults: `config/default_settings.json`
- Local user changes: `user_settings.json`
- Optional history: `command_history.json`
- Logs: `logs/sura.log`

The local settings, history, and logs are excluded from Git. Do not commit a populated `.env`, history file, or log file.

## 12. Run Automated Tests

```bash
py -m pytest tests/ -v
```

The tests mock microphone, TTS, browser, and launcher behaviour. They verify program logic, not the physical hardware connected to the computer.

## 13. Build a Windows Executable

Install PyInstaller in the virtual environment:

```bash
py -m pip install pyinstaller
```

Build the package:

```bash
py scripts/build_windows.py
```

The helper creates `dist/SURA/SURA.exe` and bundles the default configuration. PyInstaller's `build/` and `dist/` folders are generated output and are ignored by Git.

## 14. Test the Packaged Application

On a clean Windows test machine where possible:

1. Copy the entire `dist/SURA/` folder, not just `SURA.exe`.
2. Run `SURA.exe`.
3. Test typed commands, the Commands panel, and Settings.
4. Test microphone permissions, online recognition, and spoken responses.
5. Verify failure messages with the network disconnected and microphone disabled.

## 15. Uninstall / Cleanup

SURA does not install a system service. To remove a portable build, delete its distribution folder. To remove local data, delete `user_settings.json`, `command_history.json`, and `logs/` from the application folder after backing up anything needed.
