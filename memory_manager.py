"""
Memory Manager — Single Responsibility for Conversation History
===============================================================
Stores and manages the agent's short-term conversational memory.

Responsibility (SRP): *only* tracks user/assistant exchanges.
No AI logic, no Gemini API calls, no tool logic.

The Agent delegates every memory operation to this class, keeping
its own code focused purely on orchestration.
"""

from __future__ import annotations

from typing import Optional


class MemoryManager:
    """Stores completed conversation turns and enforces a configurable limit.

    Each "turn" is a (user_input, assistant_response) pair recorded after
    the Agent finishes processing a query (including any tool calls).

    Args:
        max_turns: Maximum number of turns to retain.  Oldest turns are
                   dropped when the limit is exceeded (sliding window).
    """

    def __init__(self, max_turns: int = 20) -> None:
        self._turns: list[dict[str, str]] = []
        self._max_turns = max(1, max_turns)

    # ------------------------------------------------------------------ #
    # Write operations                                                      #
    # ------------------------------------------------------------------ #

    def add_turn(self, user_input: str, assistant_response: str) -> None:
        """Record a completed conversation turn.

        Args:
            user_input:          The raw text the user sent.
            assistant_response:  The final text the agent replied with.
        """
        self._turns.append(
            {"user": user_input, "assistant": assistant_response}
        )
        self._trim()

    def clear(self) -> None:
        """Erase all stored conversation history."""
        self._turns.clear()

    # ------------------------------------------------------------------ #
    # Read operations                                                       #
    # ------------------------------------------------------------------ #

    def get_history(self) -> list[dict[str, str]]:
        """Return a shallow copy of all stored turns (oldest first)."""
        return list(self._turns)

    def get_last_turn(self) -> Optional[dict[str, str]]:
        """Return the most recent turn, or ``None`` if history is empty."""
        return self._turns[-1] if self._turns else None

    def get_turn_count(self) -> int:
        """Return the number of completed turns currently stored."""
        return len(self._turns)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                      #
    # ------------------------------------------------------------------ #

    def _trim(self) -> None:
        """Drop oldest turns when the sliding window limit is exceeded."""
        if len(self._turns) > self._max_turns:
            self._turns = self._turns[-self._max_turns :]

    # ------------------------------------------------------------------ #
    # Dunder helpers                                                        #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return (
            f"<MemoryManager turns={len(self._turns)}/{self._max_turns}>"
        )
