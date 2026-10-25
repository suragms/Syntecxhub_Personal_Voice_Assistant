# SURA Architecture

## Purpose

SURA is an event-driven Windows desktop assistant designed to keep the PySide6 GUI responsive while it performs microphone capture, online speech recognition, and speech synthesis.

## Component Map

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         PySide6 Main Thread                         │
│                                                                     │
│  MainWindow ── VoicePanel / ConversationPanel / Settings / History  │
│       │                                                             │
│       ├── typed text ──────────────────────────────────────────┐    │
│       └── microphone click ───────────────┐                     │    │
└───────────────────────────────────────────┼─────────────────────┼────┘
                                            │                     │
                                    ┌───────▼────────┐    ┌──────▼────────┐
                                    │ Speech Service │    │VoiceAssistant │
                                    │ daemon worker  │───▶│ state machine │
                                    └───────┬────────┘    └──────┬────────┘
                                            │                     │
                                  Google Web Speech      ┌────────▼──────────┐
                                            │            │ CommandProcessor  │
                                            │            └──┬─────┬─────┬────┘
                                            │               │     │     │
                                            │             apps   web  system
                                            │               │     │     │
                                            │          allowlist browser date/time
                                            │
                                    ┌───────▼────────┐
                                    │ TextToSpeech   │ ◀── response queue
                                    │ dedicated      │
                                    │ SAPI5 thread   │
                                    └────────────────┘
```

## Module Responsibilities

| Module | Responsibility |
| --- | --- |
| `main.py` | Parses launch options, configures logging, starts Qt, and performs shutdown. |
| `assistant/voice_assistant.py` | Coordinates components and exposes Qt signals/state transitions. |
| `assistant/speech_recognition_service.py` | Captures microphone audio and sends it to Google recognition on a daemon thread. |
| `assistant/command_processor.py` | Normalises text, prioritises regex intents, and dispatches actions. |
| `assistant/application_launcher.py` | Validates and starts only fixed allowlisted Windows targets. |
| `assistant/web_search.py` | URL-encodes queries and opens fixed quick-access URLs. |
| `assistant/system_commands.py` | Produces local date/time and conversation responses. |
| `assistant/text_to_speech.py` | Runs pyttsx3/SAPI5 only in a dedicated queue-processing thread. |
| `assistant/error_handler.py` | Wraps exceptions in user-friendly error categories. |
| `assistant/config_manager.py` | Loads defaults and persists local user preference changes. |
| `gui/` | Contains the PySide6 presentation layer and panels. |

## Command Flow

### Typed command

```text
QLineEdit → MainWindow._on_send()
          → VoiceAssistant.process_text()
          → VoiceAssistant._handle_command()
          → CommandProcessor.process()
          → handler result
          → Qt result_ready signal
          → conversation/history UI + queued TTS
```

### Voice command

```text
Microphone button → VoiceAssistant.start_listening()
                  → SpeechRecognitionService.listen_once()
                  → daemon worker:
                       open microphone
                       calibrate ambient noise (0.5 sec)
                       listen with configured timeouts
                       call Google Web Speech
                  → callback → VoiceAssistant._handle_command()
                  → same command path as typed input
```

## State Machine

`VoiceAssistant` transitions through these states:

| State | Meaning |
| --- | --- |
| `IDLE` | Ready for a typed or microphone command. |
| `LISTENING` | The speech worker is calibrating/capturing audio. |
| `PROCESSING` | Recognition result or text command is being interpreted. |
| `EXECUTING` | The recognised intent is being dispatched. |
| `SPEAKING` | A response has been queued for the TTS worker. |
| `ERROR` | A recoverable failure is reported to the UI. |
| `STOPPED` | Application shutdown or goodbye action was requested. |

The state changes are emitted through Qt `Signal`s so widgets can update status indicators without polling.

## Concurrency Model

### GUI thread

The GUI thread owns the `QApplication`, `MainWindow`, buttons, text fields, panels, and signal delivery. It must not wait for microphone recording, network recognition, or speech playback.

### Speech-recognition daemon thread

`SpeechRecognitionService.listen_once()` creates a daemon `threading.Thread`. The worker performs calibration, `Recognizer.listen`, and `recognize_google`. It invokes supplied callbacks after it has a result or a classified failure.

### Text-to-speech worker thread

`TextToSpeechEngine` starts one dedicated worker that creates and controls the pyttsx3 engine. A `queue.Queue` transports commands such as `speak`, `stop`, `set_rate`, `set_volume`, and `set_voice`. Shutdown sends a unique sentinel through the queue and joins the worker. This keeps SAPI5/COM activity in one thread and avoids blocking the GUI.

## Error Model

`AssistantError` carries an `ErrorCategory` and safe user message. The supported categories are:

- `MICROPHONE`
- `RECOGNITION`
- `NETWORK`
- `TTS`
- `COMMAND`
- `APPLICATION`
- `CONFIGURATION`
- `UNKNOWN`

The `ErrorHandler` logs diagnostic detail but returns non-technical messages for display. Microphone open/context failures, recognition uncertainty, Google request failures, unsupported commands, and TTS initialization failures are handled separately.

## Security Boundaries

### Application launching

`ApplicationLauncher` maps normalised names to a fixed dictionary of executables or Windows URI targets. It rejects blank names, path separators, `..`, and shell metacharacters. It calls `subprocess.Popen` with `shell=False`; no arbitrary command string is constructed.

### Web searching

`WebSearch.search()` strips the query and uses `urllib.parse.quote_plus` before building the Google search URL. `open_site()` is limited to a small dictionary of HTTPS URLs.

### Secrets and audio

The project uses no API keys. Default logging does not write raw microphone audio, and the application does not persist recorded audio. Command-history persistence is local and configurable.

## Resource Profile

The assistant favors low-overhead standard Python and PySide6 mechanisms:

- One short-lived daemon thread per microphone request.
- One long-lived TTS worker thread.
- No local large-language model or continuously running inference service.
- Rule-based intent matching instead of model inference.
- Capped command history and rotating log files.

This design targets systems with 4 GB RAM and integrated graphics, though exact consumption depends on installed drivers and the Windows speech stack.

## Extensibility Rules

To extend SURA safely:

1. Add a specific pattern before greedy command patterns in `CommandProcessor._register_all()`.
2. Keep handlers structured: `success`, `message`, and optional data.
3. Add application targets only after they have a fixed canonical name and non-shell launch strategy.
4. Add unit tests for happy paths and denial/error paths.
5. Preserve background execution for operations that may wait on I/O.

## Known Boundaries

- Google Web Speech is an online provider; SURA reports network failure rather than silently falling back to an unimplemented offline engine.
- Physical microphone, speaker, and browser behaviour depends on the target Windows device and should be verified during deployment.
- The built-in application allowlist intentionally does not support arbitrary executable paths.
