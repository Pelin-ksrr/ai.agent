"""
Base Tool Interface — Strategy Pattern + Dependency Inversion Principle
======================================================================
All agent tools must inherit from BaseTool and implement its abstract methods.

Design Patterns Applied:
  - Strategy Pattern: each concrete tool is an interchangeable strategy.
  - DIP: Agent and ToolRegistry depend on this abstraction, never on
    concrete tool classes.
  - OCP: New tools can be added without modifying existing code.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class defining the contract for every agent tool.

    Concrete subclasses must implement:
        name            - unique snake_case identifier used by the LLM.
        description     - short human-readable purpose string.
        execute(**kwargs) - tool logic; MUST return a string, never raise.
        get_declaration() - JSON-schema dict for Gemini function calling.
    """

    # ------------------------------------------------------------------ #
    # Identity & metadata                                                  #
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique snake_case identifier.  Must match the LLM function name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short human-readable explanation of what the tool does."""

    # ------------------------------------------------------------------ #
    # Core interface                                                        #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Run the tool and return a plain-text result.

        Args:
            **kwargs: Parameters declared in ``get_declaration()``.

        Returns:
            A non-empty string result.  On failure return a descriptive
            ``"Error: ..."`` string — do **not** raise exceptions.
        """

    @abstractmethod
    def get_declaration(self) -> dict:
        """Return a Gemini-compatible function-declaration schema dict.

        Returns:
            A dict with the following structure::

                {
                    "name": "tool_name",
                    "description": "What this tool does.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "param": {
                                "type": "string",
                                "description": "What this param is."
                            }
                        },
                        "required": ["param"]   # omit or use [] if none required
                    }
                }
        """

    # ------------------------------------------------------------------ #
    # Helpers                                                               #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        return f"<Tool name={self.name!r}>"
