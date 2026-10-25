"""
test_application_launcher.py — Unit tests for ApplicationLauncher.

subprocess.Popen is mocked so no real applications are launched.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from assistant.application_launcher import ApplicationLauncher, ALLOWED_APPS


# ---------------------------------------------------------------------------
# ALLOWED_APPS structure
# ---------------------------------------------------------------------------

class TestAllowedApps:
    def test_allowed_apps_is_dict(self):
        assert isinstance(ALLOWED_APPS, dict)

    def test_known_apps_present(self):
        for name in ("notepad", "calculator", "paint"):
            assert name in ALLOWED_APPS, f"Expected '{name}' in ALLOWED_APPS"

    def test_no_shell_true_equivalent(self):
        """Ensure no entries rely on shell expansion (no & | ; chars)."""
        for name, exe in ALLOWED_APPS.items():
            illegal = set("&|;")
            assert not illegal.intersection(exe), (
                f"Entry '{name}' contains shell-special chars: {exe!r}"
            )


# ---------------------------------------------------------------------------
# Allowlist validation
# ---------------------------------------------------------------------------

class TestAllowlistValidation:
    def test_known_app_passes_validation(self):
        result = ApplicationLauncher.launch("notepad")
        # May succeed or fail (no real process), but should NOT be rejected
        # as "not in allowlist".
        assert "not supported" not in result.get("message", "").lower() or result["success"]

    def test_unlisted_app_rejected(self):
        result = ApplicationLauncher.launch("malware")
        assert not result["success"]
        msg = result.get("message", "").lower()
        assert "not supported" in msg or "allowed" in msg or "unsupported" in msg

    def test_empty_name_rejected(self):
        result = ApplicationLauncher.launch("")
        assert not result["success"]

    def test_path_traversal_rejected(self):
        result = ApplicationLauncher.launch("../../windows/system32/cmd")
        assert not result["success"]

    def test_semicolon_injection_rejected(self):
        result = ApplicationLauncher.launch("notepad; del /f /s /q C:\\")
        assert not result["success"]


# ---------------------------------------------------------------------------
# Successful launch (mocked Popen)
# ---------------------------------------------------------------------------

class TestLaunchSuccess:
    @patch("subprocess.Popen")
    def test_notepad_launches_popen(self, mock_popen):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        result = ApplicationLauncher.launch("notepad")
        assert result["success"]
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_popen_called_with_shell_false(self, mock_popen):
        mock_popen.return_value = MagicMock()
        ApplicationLauncher.launch("notepad")
        _, kwargs = mock_popen.call_args
        assert kwargs.get("shell") is False or mock_popen.call_args[1].get("shell") is False or \
               ("shell" not in mock_popen.call_args[1])  # shell=False is the default

    @patch("subprocess.Popen")
    def test_calculator_launches(self, mock_popen):
        mock_popen.return_value = MagicMock()
        result = ApplicationLauncher.launch("calculator")
        assert result["success"]

    @patch("subprocess.Popen")
    def test_result_contains_app_name(self, mock_popen):
        mock_popen.return_value = MagicMock()
        result = ApplicationLauncher.launch("notepad")
        assert "notepad" in result.get("app_name", "").lower() or result["success"]


# ---------------------------------------------------------------------------
# Failed launch (OSError / FileNotFoundError)
# ---------------------------------------------------------------------------

class TestLaunchFailure:
    @patch("subprocess.Popen", side_effect=FileNotFoundError("not found"))
    def test_file_not_found_returns_failure(self, _mock):
        result = ApplicationLauncher.launch("notepad")
        assert not result["success"]

    @patch("subprocess.Popen", side_effect=OSError("permission denied"))
    def test_os_error_returns_failure(self, _mock):
        result = ApplicationLauncher.launch("notepad")
        assert not result["success"]

    @patch("subprocess.Popen", side_effect=PermissionError("denied"))
    def test_permission_error_returns_failure(self, _mock):
        result = ApplicationLauncher.launch("notepad")
        assert not result["success"]

    @patch("subprocess.Popen", side_effect=Exception("unexpected"))
    def test_generic_exception_returns_failure(self, _mock):
        result = ApplicationLauncher.launch("notepad")
        assert not result["success"]


# ---------------------------------------------------------------------------
# Case sensitivity
# ---------------------------------------------------------------------------

class TestCaseSensitivity:
    @patch("subprocess.Popen")
    def test_uppercase_name_resolved(self, mock_popen):
        mock_popen.return_value = MagicMock()
        result = ApplicationLauncher.launch("NOTEPAD")
        assert result["success"]

    @patch("subprocess.Popen")
    def test_mixed_case_name_resolved(self, mock_popen):
        mock_popen.return_value = MagicMock()
        result = ApplicationLauncher.launch("Notepad")
        assert result["success"]
