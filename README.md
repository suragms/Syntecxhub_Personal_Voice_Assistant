# SURA Voice Assistant

> A Windows desktop voice assistant built with Python and PySide6 for **Syntecxhub AI Internship — Task 4, Project 1**.

**Developed by:** Surag M S  
**Target platform:** Windows 10/11  
**Python:** 3.11 or newer

## 1. Overview

SURA is a resource-conscious personal voice assistant with a desktop interface. It accepts typed commands and push-to-talk speech input, maps recognised requests to a small safe set of actions, and responds visually and (when available) through text-to-speech.

## 2. Internship Deliverables

| Deliverable | Implementation |
| --- | --- |
| Speech-to-text | `SpeechRecognition` microphone capture with 0.5-second ambient calibration and Google Web Speech recognition. |
| Rule-based commands | Ordered regular-expression intent matching for applications, web, date/time, and conversation. |
| Text-to-speech | `pyttsx3` on a dedicated worker thread with a queue-based command loop. |
| Error handling | Centralised error categories and non-technical messages for common failures. |
| Command documentation | In-app Commands panel plus [command reference](docs/commands.md). |

## 3. Features

- Push-to-talk microphone capture without blocking the Qt GUI.
- Typed-command fallback using the same command pipeline.
- Ambient-noise calibration before each recognition cycle.
- State feedback: Ready, Listening, Processing, Executing, Speaking, Error, and Stopped.
- Allowlisted Windows application launching.
- Google web search with URL encoding.
- Quick links for Google, YouTube, GitHub, Wikipedia, Stack Overflow, and Reddit.
- Local date, time, and day-of-week responses.
- Conversational greetings, help, thanks, and exit intent.
- Thread-isolated Windows SAPI5 text-to-speech.
- Command history, configurable speech settings, theme settings, and an in-app sample-command catalog.

## 4. Safety Model

SURA deliberately has a narrow command surface:

- It does **not** use `eval`.
- It does **not** execute arbitrary PowerShell, Command Prompt, or shell text.
- Application launch targets must match a fixed allowlist.
- Application input containing paths, path traversal, or shell metacharacters is rejected.
- Search text is encoded with `urllib.parse.quote_plus` before opening the browser.
- Raw microphone audio is not saved or logged.
- No API keys or credentials are required or stored.

See [Architecture](docs/architecture.md) for details.

## 5. Supported Applications

| Spoken or typed name | Windows target |
| --- | --- |
| Notepad | `notepad.exe` |
| Calculator | `calc.exe` |
| Paint | `mspaint.exe` |
| File Explorer / Explorer | `explorer.exe` |
| Settings | `ms-settings:` |
| Task Manager | `taskmgr.exe` |
| Command Prompt | `cmd.exe` |
| WordPad | `wordpad.exe` |
| Snipping Tool | `snippingtool.exe` |

The assistant will reject applications outside this list instead of guessing a command.

## 6. Supported Commands

Examples include:

```text
Open Notepad
Search Google for Python tutorials
Open YouTube
What time is it?
What's today's date?
Hello
What can you do?
```

Read the complete [command catalog](docs/commands.md).

## 7. Requirements

- Windows 10 or Windows 11
- Python 3.11+
- A microphone and permission to use it for voice input
- Internet access for Google Web Speech recognition and browser searches
- A Windows speech voice for spoken responses

## 8. Quick Start

```bash
py -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
py -m pip install --upgrade pip
```

```bash
py -m pip install -r requirements.txt
```

```bash
py main.py
```

Detailed Windows and PyAudio instructions are in [Installation](docs/installation.md).

## 9. Run Options

```bash
py main.py --theme dark --log-level INFO
```

Available arguments:

- `--theme dark|light` — override the saved theme for this launch.
- `--log-level DEBUG|INFO|WARNING|ERROR` — set diagnostic verbosity.

## 10. Using the Interface

1. Click the microphone button to start a push-to-talk recognition cycle.
2. Speak after the status changes to **Listening**.
3. Or type a command into the command field and press **Enter** or **Send**.
4. Use **Commands** for one-click examples.
5. Use **History** to review and replay saved commands.
6. Use **Settings** to adjust voice, volume, rate, theme, and history preferences.

## 11. Speech Recognition Behaviour

Each microphone request runs outside the GUI thread:

1. Open the configured/default microphone.
2. Calibrate ambient noise for 0.5 seconds.
3. Wait up to five seconds for speech by default.
4. Record up to eight seconds for a phrase by default.
5. Send the audio to Google Web Speech using `en-US` by default.
6. Normalise recognised text and process it through the rule-based dispatcher.

Google recognition requires connectivity. If it is unavailable, SURA explains that the online service cannot be reached; typed commands remain usable. The repository does not currently include an implemented offline recognition engine.

## 12. Text-to-Speech Behaviour

SURA initializes `pyttsx3` in one background worker thread. The GUI only adds commands to a thread-safe queue, preventing voice playback from locking the UI. The worker supports speak, stop, rate, volume, voice selection, mute, and sentinel-based shutdown.

## 13. Configuration

Default settings are stored in [`config/default_settings.json`](config/default_settings.json). User changes are persisted locally in `user_settings.json`, which is excluded from version control.

Key settings include:

| Setting | Purpose |
| --- | --- |
| `theme` | `dark` or `light` UI theme |
| `language` | Google recognition language tag |
| `speech_rate` | pyttsx3 words-per-minute setting |
| `volume` | Speech volume from 0.0 to 1.0 |
| `microphone_index` | Audio input device index or `null` for default |
| `voice_enabled` | Enables or mutes spoken replies |
| `listen_timeout` | Seconds to wait for speech to begin |
| `phrase_timeout` | Maximum phrase recording time |
| `save_history` | Enables local command-history persistence |

## 14. Microphone Selection

The assistant exposes available devices as `(index, name)` pairs through its speech-recognition service. Select an index in the settings UI when multiple microphones are connected. If microphone access is denied or the device is unavailable, use typed commands while resolving the Windows audio setting.

## 15. Error Handling

The error handler classifies microphone, recognition, network, TTS, command, application, configuration, and unexpected failures. The UI receives actionable messages rather than stack traces, for example:

- *No microphone detected. Please connect a microphone or use text mode.*
- *Microphone access was denied. Check your Windows privacy settings.*
- *Online speech recognition is unavailable. Check your internet connection or switch to offline mode.*
- *Sorry, I couldn't understand that. Please try again.*

## 16. Command History and Privacy

When history is enabled, recognised or typed **command text** and assistant responses are stored in `command_history.json` on the local machine. Raw audio is never stored. Turn history off in Settings or remove history from the UI to delete the file.

Do not enter credentials, personal identifiers, or other sensitive content as commands if history storage is enabled.

## 17. Logging

Application logs are written to `logs/sura.log` with rotation (1 MB per file, three backups). Logs support troubleshooting but should be handled as local diagnostic data. They are excluded from Git.

## 18. Project Layout

```text
SURA Voice Assistant/
├── assistant/          # Recognition, TTS, commands, error handling, orchestration
├── config/             # Default application settings
├── docs/               # Architecture, installation, commands, demo guide
├── gui/                # PySide6 windows and panels
├── scripts/            # Windows packaging helper
├── tests/              # Hardware-mocked unit tests
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── README.md
```

## 19. Architecture

The application follows an event-driven design built around `VoiceAssistant` and Qt signals. Long-running speech capture and SAPI5 work are kept off the interface thread. See [Architecture](docs/architecture.md).

## 20. Testing

Run the automated test suite with:

```bash
py -m pytest tests/ -v
```

The suite mocks hardware and browser integrations. The current suite contains **119 automated tests**, covering command processing, launcher validation, web searches, centralised errors, speech-service paths, and text-to-speech queue behaviour.

## 21. Test Result

The full automated suite was last run in this workspace with:

```text
119 passed, 1 warning in 5.13s
```

The warning is emitted by the installed `SpeechRecognition` dependency under Python 3.14 because it references the removed standard-library `aifc` module via its compatibility dependency. It did not affect test outcomes.

## 22. Hardware Verification Boundary

The automated tests simulate microphone, network, browser, and speech-engine interactions. They validate the code paths but do **not** constitute verification on a specific physical microphone, speaker, SAPI5 voice, or Google service connection. Perform the checks in the [demo script](docs/demo_script.md) on the target Windows machine before presenting.

## 23. Windows Packaging

Build a distributable executable after installing PyInstaller:

```bash
py -m pip install pyinstaller
```

```bash
py scripts/build_windows.py
```

The generated application is written under `dist/SURA/`. Read [Installation](docs/installation.md) for prerequisites and packaging notes.

## 24. Troubleshooting

| Symptom | Action |
| --- | --- |
| `PyAudio` does not install | Use a wheel compatible with your Python version and architecture; see the installation guide. |
| Mic button reports no device | Confirm the microphone is connected and selected in Windows Sound settings. |
| Access denied | Enable desktop-app microphone access in Windows Privacy & security settings. |
| Recognition cannot connect | Verify network access; use typed commands until it is restored. |
| No spoken response | Ensure voice is enabled, a Windows voice is installed, and Windows output is working. |
| Application not supported | Use one of the allowlisted names in the command catalog. |

## 25. License

This project is released under the [MIT License](LICENSE).

---

For an evaluator walkthrough, use the [nine-scenario demo script](docs/demo_script.md).
