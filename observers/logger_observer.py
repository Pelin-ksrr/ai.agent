"""
Logger Observer — Bonus Observer Pattern Implementation
=======================================================
Writes agent events to a rotating log file (and optionally to the console).

Demonstrates Observer Pattern: this class reacts to agent state changes
without being coupled to Agent's core logic.  The Agent just calls
``notify()``; it has no idea who is listening.
"""

import logging
import logging.handlers
from typing import Any

from observers.base_observer import BaseObserver


class LoggerObserver(BaseObserver):
    """Records every agent event to a log file.

    Args:
        log_file:   Path to the output log file.
        verbose:    If ``True``, also prints log lines to the terminal.
        max_bytes:  Rotate the log file after this many bytes (default 1 MB).
        backup_count: Number of rotated backup files to keep.
    """

    # Maps event names to concise labels for the log lines
    _LABELS: dict[str, str] = {
        "user_input":     "[USER    ]",
        "tool_called":    "[TOOL    ]",
        "tool_result":    "[RESULT  ]",
        "tool_error":     "[ERR-TOOL]",
        "agent_response": "[AGENT   ]",
        "session_clear":  "[CLEAR   ]",
        "error":          "[ERROR   ]",
    }

    def __init__(
        self,
        log_file: str = "agent.log",
        verbose: bool = False,
        max_bytes: int = 1_048_576,
        backup_count: int = 3,
    ) -> None:
        self._verbose = verbose
        self._logger = logging.getLogger(f"AgentLogger.{id(self)}")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False

        fmt = logging.Formatter(
            "%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Rotating file handler — prevents unbounded log growth
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        self._logger.addHandler(file_handler)

        if verbose:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("[LOG] %(message)s"))
            self._logger.addHandler(console_handler)

    # ------------------------------------------------------------------ #
    # BaseObserver interface                                                #
    # ------------------------------------------------------------------ #

    def update(self, event: str, data: dict[str, Any]) -> None:
        """Format and log the event.  Never raises — log failures are silent."""
        try:
            label = self._LABELS.get(event, f"[{event.upper()[:8]:8}]")
            message = self._format(event, data)
            self._logger.info("%s %s", label, message)
        except Exception:
            pass  # Observer errors must never affect the agent

    # ------------------------------------------------------------------ #
    # Private helpers                                                       #
    # ------------------------------------------------------------------ #

    def _format(self, event: str, data: dict[str, Any]) -> str:
        """Produce a human-readable summary line for an event."""
        if event == "user_input":
            text = str(data.get("text", ""))
            return f"input='{self._truncate(text)}'"

        if event == "tool_called":
            name = data.get("tool_name", "?")
            args = data.get("args", {})
            return f"tool='{name}'  args={args}"

        if event in ("tool_result", "tool_error"):
            name = data.get("tool_name", "?")
            result = str(data.get("result", ""))
            return f"tool='{name}'  result='{self._truncate(result)}'"

        if event == "agent_response":
            text = str(data.get("text", ""))
            return f"response='{self._truncate(text)}'"

        if event == "error":
            return f"message='{data.get('message', '')}'"

        return str(data)

    @staticmethod
    def _truncate(text: str, limit: int = 120) -> str:
        return text[:limit] + "..." if len(text) > limit else text
