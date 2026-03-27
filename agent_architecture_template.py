"""
agent_architecture_template.py
================================
Conceptual scaffold showing the four main architectural components
and how they relate to each other.

This file is provided for study purposes.
The full, runnable implementation lives in:
    agent.py, memory_manager.py, tool_registry.py, tools/, observers/

Do NOT run this file directly.
"""

# ===========================================================================
# COMPONENT 1 — Tool Interface  (Strategy Pattern + OCP + DIP)
# ===========================================================================
# Every tool is a ConcreteStrategy that the Agent can invoke interchangeably.
# Adding a new tool never requires modifying Agent or ToolRegistry.
# ===========================================================================

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base — all tools implement this contract."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique snake_case identifier used by the LLM function call."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short human-readable explanation of the tool."""

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Run the tool; return string result; never raise."""

    @abstractmethod
    def get_declaration(self) -> dict:
        """Return Gemini function-declaration schema dict."""


# Example concrete tool (ConcreteStrategy)
class ExampleCalculatorTool(BaseTool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Evaluates a math expression."

    def execute(self, expression: str) -> str:
        return f"Result of '{expression}' would be computed here."

    def get_declaration(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A math expression, e.g. '2 + 2'.",
                    }
                },
                "required": ["expression"],
            },
        }


# ===========================================================================
# COMPONENT 2 — Tool Registry  (Factory / Registry Pattern)
# ===========================================================================
# Maps tool names to implementations.  Agent never uses if/elif chains.
# ===========================================================================

class ToolRegistry:
    """Registers and dynamically dispatches tools by name."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Add a tool.  Raises ValueError on duplicate names."""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered.")
        self._tools[tool.name] = tool

    def execute(self, tool_name: str, **kwargs: Any) -> str:
        """Dispatch execution; return error string on failure (never raise)."""
        if tool_name not in self._tools:
            return f"Error: Unknown tool '{tool_name}'."
        try:
            return self._tools[tool_name].execute(**kwargs)
        except Exception as exc:
            return f"Error: Tool '{tool_name}' failed: {exc}"

    def get_declarations(self) -> list[dict]:
        """Return all declaration dicts for the Gemini API."""
        return [t.get_declaration() for t in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())


# ===========================================================================
# COMPONENT 3 — Memory Manager  (SRP)
# ===========================================================================
# Single purpose: store and retrieve conversation history.
# The Agent delegates ALL memory operations here.
# ===========================================================================

class MemoryManager:
    """Manages a sliding window of conversation turns."""

    def __init__(self, max_turns: int = 20) -> None:
        self._turns: list[dict[str, str]] = []
        self._max_turns = max_turns

    def add_turn(self, user_input: str, assistant_response: str) -> None:
        self._turns.append({"user": user_input, "assistant": assistant_response})
        if len(self._turns) > self._max_turns:
            self._turns = self._turns[-self._max_turns:]

    def get_history(self) -> list[dict[str, str]]:
        return list(self._turns)

    def clear(self) -> None:
        self._turns.clear()

    def get_turn_count(self) -> int:
        return len(self._turns)


# ===========================================================================
# COMPONENT 4 — Agent  (ReAct Orchestrator)
# ===========================================================================
# Drives the Reason → Act → Observe loop.
# Depends on abstractions (BaseTool via Registry, BaseObserver) — DIP.
# Does NOT implement tool logic, memory storage, or logging — SRP.
# ===========================================================================

class AgentTemplate:
    """Skeleton of the ReAct agent — see agent.py for full implementation."""

    def __init__(
        self,
        registry: ToolRegistry,
        memory: MemoryManager,
    ) -> None:
        self._registry = registry
        self._memory   = memory
        # self._model = genai.GenerativeModel(...)  # Gemini LLM
        # self._chat  = self._model.start_chat(history=[])

    def chat(self, user_input: str) -> str:
        """ReAct loop entry point."""


        raise NotImplementedError("See agent.py for the full implementation.")


# ===========================================================================
# BONUS — Observer Pattern (EventEmitter + BaseObserver)
# ===========================================================================
# Observers subscribe to agent events for logging, analytics, UI updates,
# etc., without being coupled to Agent's core logic.
# ===========================================================================

class BaseObserver(ABC):
    @abstractmethod
    def update(self, event: str, data: dict[str, Any]) -> None:
        """React to an agent event."""


class AgentEventEmitter:
    """Mix-in that gives any class the ability to broadcast events."""

    def __init__(self) -> None:
        self._observers: list[BaseObserver] = []

    def add_observer(self, observer: BaseObserver) -> None:
        self._observers.append(observer)

    def _notify(self, event: str, data: dict[str, Any]) -> None:
        for obs in self._observers:
            try:
                obs.update(event, data)
            except Exception:
                pass  # Never let observer failure affect the agent
