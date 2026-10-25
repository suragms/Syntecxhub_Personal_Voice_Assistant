"""
system_commands.py — Date, time, and conversational commands.
"""

from __future__ import annotations

import datetime
from typing import Any


class SystemCommands:
    """Stateless helper for time/date and conversational responses."""

    GREETINGS = {
        "hello", "hi", "hey", "hey there", "hi sura", "hello sura",
        "hey sura", "good morning", "good afternoon", "good evening",
    }

    ABOUT_PHRASES = {
        "who are you", "what is your name", "what's your name",
        "tell me about yourself",
    }

    HELP_PHRASES = {
        "what can you do", "help", "show commands", "list commands",
        "what are your commands",
    }

    THANKS_PHRASES = {"thank you", "thanks", "thank you sura", "thanks sura"}

    GOODBYE_PHRASES = {
        "goodbye", "bye", "see you", "see you later", "bye sura",
        "goodbye sura", "exit",
    }

    HOW_ARE_YOU_PHRASES = {
        "how are you", "how are you doing", "how do you feel",
        "how are you sura",
    }

    # ------------------------------------------------------------------
    # Time / Date
    # ------------------------------------------------------------------

    @staticmethod
    def get_time() -> dict[str, Any]:
        now = datetime.datetime.now()
        time_str = now.strftime("%I:%M %p")
        return {
            "success": True,
            "message": f"The current time is {time_str}.",
        }

    @staticmethod
    def get_date() -> dict[str, Any]:
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return {
            "success": True,
            "message": f"Today is {date_str}.",
        }

    @staticmethod
    def get_day() -> dict[str, Any]:
        now = datetime.datetime.now()
        return {
            "success": True,
            "message": f"Today is {now.strftime('%A')}.",
        }

    # ------------------------------------------------------------------
    # Conversational
    # ------------------------------------------------------------------

    @staticmethod
    def greet() -> dict[str, Any]:
        return {
            "success": True,
            "message": "Hello! I'm SURA, your personal voice assistant. How can I help you?",
        }

    @staticmethod
    def about() -> dict[str, Any]:
        return {
            "success": True,
            "message": (
                "I'm SURA — a personal voice assistant built for the "
                "Syntecxhub AI Internship. I can open apps, search the web, "
                "tell you the time, and more!"
            ),
        }

    @staticmethod
    def help_text() -> dict[str, Any]:
        return {
            "success": True,
            "message": (
                "I can help with:\n"
                "• Opening applications (Notepad, Calculator, Paint...)\n"
                '• Searching the web ("Search Google for ...")\n'
                "• Telling the time and date\n"
                "• Opening websites (YouTube, GitHub...)\n"
                "Open the Commands panel for the full list."
            ),
        }

    @staticmethod
    def thanks() -> dict[str, Any]:
        return {
            "success": True,
            "message": "You're welcome! Let me know if there's anything else I can do.",
        }

    @staticmethod
    def goodbye() -> dict[str, Any]:
        return {
            "success": True,
            "message": "Goodbye! Have a great day.",
            "action": "exit",
        }

    @staticmethod
    def how_are_you() -> dict[str, Any]:
        return {
            "success": True,
            "message": "I'm doing great, thank you for asking! How can I help you today?",
        }
