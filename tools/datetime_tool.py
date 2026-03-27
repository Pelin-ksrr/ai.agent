"""
DateTime Tool — returns the current date and time.

Optionally accepts an IANA timezone name (e.g. 'Europe/Istanbul').
Falls back to UTC when an unrecognised timezone is supplied, and
reports the issue to the caller.
"""

import zoneinfo
from datetime import datetime, timezone

from tools.base_tool import BaseTool


class DateTimeTool(BaseTool):
    """Returns the current date/time, optionally in a specified timezone."""

    @property
    def name(self) -> str:
        return "get_datetime"

    @property
    def description(self) -> str:
        return "Gets the current date and time, optionally for a given timezone."

    def execute(self, timezone_name: str = "UTC") -> str:
        try:
            if timezone_name.upper() == "UTC":
                tz = timezone.utc
            else:
                tz = zoneinfo.ZoneInfo(timezone_name)
            now = datetime.now(tz)
            return now.strftime(
                f"Current date/time in {timezone_name}: %A, %B %d, %Y  %H:%M:%S %Z"
            )
        except zoneinfo.ZoneInfoNotFoundError:
            now = datetime.now(timezone.utc)
            return (
                f"Unknown timezone '{timezone_name}'. "
                f"UTC time: {now.strftime('%A, %B %d, %Y  %H:%M:%S UTC')}"
            )
        except Exception as exc:
            return f"Error retrieving date/time: {exc}"

    def get_declaration(self) -> dict:
        return {
            "name": self.name,
            "description": (
                "Returns the current date and time. "
                "Accepts an optional IANA timezone name; defaults to UTC."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone_name": {
                        "type": "string",
                        "description": (
                            "IANA timezone name, e.g. 'America/New_York', "
                            "'Europe/Istanbul', 'Asia/Tokyo'. Defaults to 'UTC'."
                        ),
                    }
                },
                "required": [],
            },
        }
