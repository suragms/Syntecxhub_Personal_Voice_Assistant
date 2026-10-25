"""
web_search.py — Opens the default browser with search queries or direct URLs.
"""

from __future__ import annotations

import logging
import urllib.parse
import webbrowser
from typing import Any

logger = logging.getLogger(__name__)

# Quick-access websites
QUICK_SITES: dict[str, str] = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "wikipedia": "https://www.wikipedia.org",
    "stackoverflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
}


class WebSearch:
    """Opens web pages and search queries via the system browser."""

    @staticmethod
    def search(query: str) -> dict[str, Any]:
        """Search Google for *query*."""
        if not query or not query.strip():
            return {
                "success": False,
                "message": "No search query provided.",
            }

        q = query.strip()
        encoded = urllib.parse.quote_plus(q)
        url = f"https://www.google.com/search?q={encoded}"
        result = WebSearch._open(url, f"Searching Google for {q}.")
        if result["success"]:
            result["data"] = {"query": q}
        return result

    @staticmethod
    def open_site(site_name: str) -> dict[str, Any]:
        """Open a known quick-access website."""
        if not site_name or not site_name.strip():
            return {
                "success": False,
                "message": "No site name provided.",
            }
        key = site_name.strip().lower()
        url = QUICK_SITES.get(key)
        if url is None:
            return {
                "success": False,
                "message": f'I don\'t have a shortcut for "{site_name}". Try a search instead.',
            }
        return WebSearch._open(url, f"Opening {site_name.title()}.")

    @staticmethod
    def list_sites() -> list[str]:
        """Return supported site names."""
        return sorted(QUICK_SITES.keys())

    @staticmethod
    def _open(url: str, message: str) -> dict[str, Any]:
        """Open *url* in the default browser."""
        try:
            webbrowser.open(url)
            logger.info("Opened URL: %s", url)
            return {"success": True, "message": message, "url": url}
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to open browser: %s", exc)
            return {
                "success": False,
                "message": "Sorry, I couldn't open the browser.",
            }
