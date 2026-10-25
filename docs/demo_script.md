# SURA Demonstration Script

Use this nine-scenario script for an internship review. It separates tested functionality from device-specific checks and gives a clear fallback demonstration when hardware is unavailable.

## Preparation

1. Start SURA with `py main.py`.
2. Ensure the screen shows the main window and the microphone device is connected if voice testing is planned.
3. Keep the Commands panel available for the final scenario.
4. Do not use real credentials or private searches during a recorded demonstration.

## Scenario 1 — Application Introduction

**Action:** Point out the SURA title, status dot, microphone button, typed-command field, and toolbar.

**Say:**

> SURA is a PySide6 desktop assistant. It accepts push-to-talk speech and typed input, and its state is visible in the interface.

**Expected result:** The interface starts in **Ready** / `IDLE` state.

## Scenario 2 — Typed Conversation

**Action:** Type `Hello` and press Enter.

**Expected result:** The conversation panel displays SURA's greeting; voice output plays only when it is enabled and available.

**What this proves:** Typed commands use the same central command pipeline as speech results.

## Scenario 3 — Date and Time Intent

**Action:** Type `What time is it?`.

**Expected result:** SURA returns the current local time.

**Follow-up:** Type `What's today's date?`.

**What this proves:** Specific date/time patterns have priority before generic application patterns.

## Scenario 4 — Safe Application Launch

**Action:** Type `Open Notepad`.

**Expected result:** Windows Notepad opens and the UI responds with an opening message.

**Safety explanation:** The launcher uses a fixed allowlist and `shell=False`; it does not pass the spoken text to a command shell.

## Scenario 5 — Application Rejection

**Action:** Type `Open C:\Windows\System32\cmd.exe` or `Open unknown application`.

**Expected result:** SURA refuses the request as unsupported instead of attempting path-based execution.

**What this proves:** Input validation prevents arbitrary application/path dispatch.

## Scenario 6 — Web Search and Quick Site

**Action:** Type `Search Google for PySide6 documentation`.

**Expected result:** The default browser opens an encoded Google query.

**Follow-up:** Type `Open GitHub`.

**Expected result:** GitHub opens through the fixed quick-site list.

## Scenario 7 — Voice Recognition (Hardware Check)

**Action:** Click the microphone, wait for **Listening**, then say `What day is it?`.

**Expected result:** The status progresses through Listening and Processing, then the recognised command and response appear in the conversation panel.

**Important:** This scenario requires a working microphone and internet access. If either is unavailable, show the friendly error message and proceed with typed commands; do not claim a successful live recognition result without observing it.

## Scenario 8 — Error Handling and Text Fallback

**Action:** Temporarily disable the microphone in Windows or disconnect network access, then click the microphone button.

**Expected result:** SURA gives a clear, non-technical microphone or network message. Type `What time is it?` afterward.

**Expected result:** The typed command continues to work.

**What this proves:** Voice failures are recoverable and do not block the desktop UI.

## Scenario 9 — Command Catalog, History, and Settings

**Action:** Open **Commands**, search visually through categories, and click `Open Calculator` or `What can you do?`.

**Expected result:** The sample command runs through the standard typed pipeline.

**Follow-up:** Open **History** to show the recorded request and **Settings** to show voice/theme controls.

## Closing Statement

> SURA keeps resource-intensive or blocking voice operations off the GUI thread, applies rule-based command handling, restricts desktop launching to an allowlist, and provides clear recovery guidance for microphone, network, and speech failures.

## Evidence Checklist

- [ ] Screenshot or screen recording of the main interface.
- [ ] Typed greeting and date/time response.
- [ ] Allowlisted application launch.
- [ ] Unsupported application rejection.
- [ ] Browser search / quick site.
- [ ] Voice success, if hardware and internet are available.
- [ ] Error/fallback demonstration.
- [ ] Commands, history, and settings panels.
- [ ] Automated test output showing the current full pass count.
