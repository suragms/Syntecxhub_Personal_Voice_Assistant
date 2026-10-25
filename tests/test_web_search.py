"""
test_web_search.py — Unit tests for WebSearch and open_site helpers.

webbrowser.open is mocked so no real browser is launched.
"""

from __future__ import annotations

from urllib.parse import quote_plus
from unittest.mock import patch

import pytest

from assistant.web_search import WebSearch, QUICK_SITES


# ---------------------------------------------------------------------------
# QUICK_SITES structure
# ---------------------------------------------------------------------------

class TestQuickSites:
    def test_is_dict(self):
        assert isinstance(QUICK_SITES, dict)

    def test_known_sites_present(self):
        for site in ("google", "youtube", "github"):
            assert site in QUICK_SITES

    def test_all_values_are_https_urls(self):
        for name, url in QUICK_SITES.items():
            assert url.startswith("https://"), f"Site '{name}' URL is not HTTPS: {url}"


# ---------------------------------------------------------------------------
# search()
# ---------------------------------------------------------------------------

class TestSearch:
    @patch("webbrowser.open")
    def test_search_opens_browser(self, mock_open):
        WebSearch.search("python tutorials")
        mock_open.assert_called_once()

    @patch("webbrowser.open")
    def test_search_url_contains_encoded_query(self, mock_open):
        query = "machine learning"
        WebSearch.search(query)
        called_url = mock_open.call_args[0][0]
        assert quote_plus(query) in called_url or query.replace(" ", "+") in called_url.replace("%20", "+")

    @patch("webbrowser.open")
    def test_search_uses_google_by_default(self, mock_open):
        WebSearch.search("test query")
        called_url = mock_open.call_args[0][0]
        assert "google.com" in called_url

    @patch("webbrowser.open")
    def test_search_returns_success(self, mock_open):
        result = WebSearch.search("anything")
        assert result["success"]

    @patch("webbrowser.open", side_effect=Exception("browser error"))
    def test_search_browser_error_returns_failure(self, _mock):
        result = WebSearch.search("test")
        assert not result["success"]

    @patch("webbrowser.open")
    def test_search_empty_query_rejected(self, mock_open):
        result = WebSearch.search("")
        assert not result["success"]
        mock_open.assert_not_called()

    @patch("webbrowser.open")
    def test_search_whitespace_only_rejected(self, mock_open):
        result = WebSearch.search("   ")
        assert not result["success"]
        mock_open.assert_not_called()

    @patch("webbrowser.open")
    def test_search_special_chars_encoded(self, mock_open):
        WebSearch.search("C++ templates & <generics>")
        called_url = mock_open.call_args[0][0]
        assert "+" not in called_url.split("?")[-1].replace("%2B", "") or "%" in called_url

    @patch("webbrowser.open")
    def test_result_contains_query_field(self, mock_open):
        result = WebSearch.search("pytest fixtures")
        assert "query" in result.get("data", result)


# ---------------------------------------------------------------------------
# open_site()
# ---------------------------------------------------------------------------

class TestOpenSite:
    @patch("webbrowser.open")
    def test_open_known_site_succeeds(self, mock_open):
        result = WebSearch.open_site("youtube")
        assert result["success"]
        mock_open.assert_called_once()

    @patch("webbrowser.open")
    def test_open_site_uses_correct_url(self, mock_open):
        WebSearch.open_site("github")
        called_url = mock_open.call_args[0][0]
        assert "github.com" in called_url

    @patch("webbrowser.open")
    def test_open_unknown_site_returns_failure(self, mock_open):
        result = WebSearch.open_site("nonexistent_site_xyz")
        assert not result["success"]
        mock_open.assert_not_called()

    @patch("webbrowser.open")
    def test_open_site_case_insensitive(self, mock_open):
        result = WebSearch.open_site("YOUTUBE")
        assert result["success"]

    @patch("webbrowser.open")
    def test_open_site_empty_name_rejected(self, mock_open):
        result = WebSearch.open_site("")
        assert not result["success"]
        mock_open.assert_not_called()

    @patch("webbrowser.open", side_effect=Exception("no browser"))
    def test_browser_error_returns_failure(self, _mock):
        result = WebSearch.open_site("google")
        assert not result["success"]
