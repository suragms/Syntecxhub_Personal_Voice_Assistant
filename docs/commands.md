# SURA Command Catalog

SURA normalises spacing and letter case before matching commands. Commands can be typed or spoken. The application starts only the applications and sites documented below.

## Applications

Use `Open`, `Launch`, `Start`, or `Run` followed by an allowlisted name.

| Example | Result |
| --- | --- |
| `Open Notepad` | Opens Windows Notepad. |
| `Launch Calculator` | Opens Calculator. |
| `Start Paint` | Opens Microsoft Paint. |
| `Open File Explorer` | Opens File Explorer. |
| `Open Explorer` | Opens File Explorer. |
| `Open Settings` | Opens Windows Settings through `ms-settings:`. |
| `Open Task Manager` | Opens Task Manager. |
| `Open Command Prompt` | Opens Command Prompt. |
| `Open WordPad` | Opens WordPad where available on Windows. |
| `Open Snipping Tool` | Opens Snipping Tool. |

### Application restrictions

SURA rejects targets that are not in the allowlist. It also refuses paths, `..`, slash/backslash characters, and common shell metacharacters. It does not execute arbitrary terminal commands.

## Web Search

| Example | Result |
| --- | --- |
| `Search Google for Python tutorials` | Opens a Google search for the query. |
| `Search for weather tomorrow` | Opens a Google search for the query. |
| `Google PySide6 signals` | Opens a Google search for the query. |
| `Search the web for Windows accessibility` | Opens a Google search for the query. |
| `Look up SpeechRecognition documentation` | Opens a Google search for the query. |
| `Find PyAudio installation` | Opens a Google search for the query. |

Search terms are URL-encoded before the default browser is opened.

## Quick-Access Websites

| Example | Result |
| --- | --- |
| `Open Google` | Opens Google. |
| `Open YouTube` | Opens YouTube. |
| `Open GitHub` | Opens GitHub. |
| `Go to Wikipedia` | Opens Wikipedia. |
| `Visit StackOverflow` | Opens Stack Overflow. |
| `Go to Reddit` | Opens Reddit. |

The `Open <site>` form is supported for these same configured quick sites. The accepted names are `google`, `youtube`, `github`, `wikipedia`, `stackoverflow`, and `reddit`.

## Date and Time

| Example | Result |
| --- | --- |
| `What time is it?` | Reports the local clock time. |
| `Tell me the current time` | Reports the local clock time. |
| `What's today's date?` | Reports the local date. |
| `Tell me the current date` | Reports the local date. |
| `What day is it?` | Reports the local day of the week. |
| `What day of the week is it?` | Reports the local day of the week. |

## Conversation

| Example | Result |
| --- | --- |
| `Hello` / `Hi SURA` / `Good morning` | Greets the user. |
| `Who are you?` | Describes SURA. |
| `How are you?` | Returns a conversational reply. |
| `What can you do?` / `Help` | Explains capabilities. |
| `Thank you` | Acknowledges thanks. |
| `Goodbye` / `Bye SURA` / `Exit` | Responds and closes the application. |

## Empty or Unsupported Input

- An empty command receives a retry prompt.
- Unsupported phrases receive a prompt to open the Commands panel.
- If speech is unclear, the assistant asks the user to try again.
- If the online recognition service cannot be reached, the assistant explains that connectivity is needed for voice recognition; typed commands can still be used.

## One-Click Examples

The **Commands** panel in the desktop application displays grouped sample commands. Clicking one injects it into the normal typed-command pipeline, so it behaves exactly as if the command had been typed and sent.
