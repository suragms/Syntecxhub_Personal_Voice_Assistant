"""
test_command_processor.py — Unit tests for CommandProcessor intent matching.

Covers intent recognition, aliases, entity extraction, rejection of empty /
unsupported input, and result structure.
"""

from __future__ import annotations

import pytest

from assistant.command_processor import CommandProcessor, CommandResult


@pytest.fixture
def processor() -> CommandProcessor:
    return CommandProcessor()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(result: CommandResult) -> None:
    """Assert the result indicates success."""
    assert result.success, f"Expected success but got: {result.message}"


def _fail(result: CommandResult) -> None:
    """Assert the result indicates failure."""
    assert not result.success, "Expected failure but got a success result"


# ---------------------------------------------------------------------------
# Greeting intent
# ---------------------------------------------------------------------------

class TestGreetIntent:
    def test_hello(self, processor):
        r = processor.process("hello")
        _ok(r)
        assert r.intent == "greet"

    def test_hi_sura(self, processor):
        r = processor.process("hi sura")
        _ok(r)
        assert r.intent == "greet"

    def test_good_morning(self, processor):
        r = processor.process("good morning")
        _ok(r)
        assert r.intent == "greet"

    def test_hey_there(self, processor):
        r = processor.process("hey there")
        _ok(r)
        assert r.intent == "greet"


# ---------------------------------------------------------------------------
# Time / Date intents
# ---------------------------------------------------------------------------

class TestTimeDate:
    def test_what_time(self, processor):
        r = processor.process("what time is it")
        _ok(r)
        assert r.intent == "get_time"

    def test_tell_me_the_time(self, processor):
        r = processor.process("tell me the time")
        _ok(r)
        assert r.intent == "get_time"

    def test_what_is_today(self, processor):
        r = processor.process("what is today's date")
        _ok(r)
        assert r.intent == "get_date"

    def test_what_day(self, processor):
        r = processor.process("what day is it")
        _ok(r)
        assert r.intent == "get_day"

    def test_time_response_contains_colon(self, processor):
        """Returned message should look like HH:MM AM/PM."""
        r = processor.process("what time is it")
        assert ":" in r.message


# ---------------------------------------------------------------------------
# Open application intent
# ---------------------------------------------------------------------------

class TestOpenApp:
    def test_open_notepad(self, processor):
        r = processor.process("open notepad")
        # May succeed or fail depending on whether Notepad is on this system;
        # intent detection is what we're checking here.
        assert r.intent == "open_app"

    def test_launch_calculator(self, processor):
        r = processor.process("launch calculator")
        assert r.intent == "open_app"

    def test_start_paint(self, processor):
        r = processor.process("start paint")
        assert r.intent == "open_app"

    def test_open_file_explorer(self, processor):
        r = processor.process("open file explorer")
        assert r.intent == "open_app"

    def test_open_disallowed_app_fails(self, processor):
        r = processor.process("open malware.exe")
        # Either classified as unsupported command *or* open_app that fails
        if r.intent == "open_app":
            assert not r.success
        else:
            assert r.intent == "unsupported"


# ---------------------------------------------------------------------------
# Web search intent
# ---------------------------------------------------------------------------

class TestWebSearch:
    def test_search_python(self, processor):
        r = processor.process("search for python tutorials")
        assert r.intent == "web_search"
        assert r.success

    def test_google_pandas(self, processor):
        r = processor.process("google pandas dataframe")
        assert r.intent == "web_search"
        assert r.success

    def test_search_query_in_data(self, processor):
        r = processor.process("search for machine learning")
        assert "machine learning" in r.data.get("query", "").lower()

    def test_open_youtube(self, processor):
        r = processor.process("open youtube")
        assert r.intent in ("open_site", "web_search", "open_app")
        assert r.success

    def test_open_github(self, processor):
        r = processor.process("go to github")
        assert r.success


# ---------------------------------------------------------------------------
# About / Help / Thanks / Goodbye
# ---------------------------------------------------------------------------

class TestMeta:
    def test_about(self, processor):
        r = processor.process("who are you")
        _ok(r)
        assert r.intent == "about"

    def test_what_can_you_do(self, processor):
        r = processor.process("what can you do")
        _ok(r)
        assert r.intent == "help"

    def test_help(self, processor):
        r = processor.process("help")
        _ok(r)
        assert r.intent == "help"

    def test_thank_you(self, processor):
        r = processor.process("thank you")
        _ok(r)
        assert r.intent == "thanks"

    def test_goodbye(self, processor):
        r = processor.process("goodbye")
        _ok(r)
        assert r.intent == "goodbye"

    def test_goodbye_has_exit_action(self, processor):
        r = processor.process("goodbye")
        assert r.data.get("action") == "exit"

    def test_how_are_you(self, processor):
        r = processor.process("how are you")
        _ok(r)
        assert r.intent == "how_are_you"


# ---------------------------------------------------------------------------
# Unsupported / edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_string(self, processor):
        r = processor.process("")
        _fail(r)

    def test_whitespace_only(self, processor):
        r = processor.process("   ")
        _fail(r)

    def test_gibberish(self, processor):
        r = processor.process("xkqzw fjqpv yzmn")
        _fail(r)
        assert r.intent == "unsupported"

    def test_mixed_case_normalized(self, processor):
        r1 = processor.process("HELLO")
        r2 = processor.process("hello")
        assert r1.intent == r2.intent

    def test_extra_whitespace_normalized(self, processor):
        r = processor.process("  what   time   is   it  ")
        assert r.intent == "get_time"


# ---------------------------------------------------------------------------
# Sample commands structure
# ---------------------------------------------------------------------------

class TestSampleCommands:
    def test_returns_dict(self, processor):
        samples = processor.get_sample_commands()
        assert isinstance(samples, dict)

    def test_has_categories(self, processor):
        samples = processor.get_sample_commands()
        assert len(samples) > 0

    def test_each_entry_has_command_and_description(self, processor):
        samples = processor.get_sample_commands()
        for category, items in samples.items():
            for item in items:
                assert "command" in item
                assert "description" in item
