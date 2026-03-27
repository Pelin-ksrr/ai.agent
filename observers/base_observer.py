"""
Base Observer — Observer Pattern
==================================
Abstract interface for all event listeners attached to the Agent.

Design Patterns Applied:
  - Observer Pattern: observers subscribe to agent events and react
    without the Agent knowing (or depending on) their concrete type.
  - OCP: new observer types can be added without touching the Agent.
  - DIP: Agent depends on this abstraction, not on LoggerObserver etc.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseObserver(ABC):
    """Abstract base class for all agent event observers.

    Concrete subclasses implement ``update()`` to react to state changes
    such as tool invocations, user inputs, or errors.
    """

    @abstractmethod
    def update(self, event: str, data: dict[str, Any]) -> None:
        """Called by the Agent when a noteworthy event occurs.

        Args:
            event: A short identifier for the event type.
                   Known events:
                     - ``"user_input"``    — user sent a message.
                     - ``"tool_called"``   — a tool is about to run.
                     - ``"tool_result"``   — a tool returned successfully.
                     - ``"tool_error"``    — a tool returned an error string.
                     - ``"agent_response"``— agent produced a final reply.
                     - ``"session_clear"`` — memory was cleared by the user.
                     - ``"error"``         — an unexpected exception occurred.
            data:  A dictionary carrying event-specific payload fields.
        """
