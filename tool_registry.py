"""
Tool Registry — Factory / Registry Pattern
==========================================
Central registry that maps tool names to their BaseTool implementations.

Design Patterns Applied:
  - Factory / Registry: dynamically instantiates and looks up tools by name.
  - OCP: registering a new tool never requires modifying this class.
  - DIP: depends only on the BaseTool abstraction.

The Agent asks the registry to execute a tool by name; it never holds a
direct reference to any concrete tool class.
"""

from typing import Any

from tools.base_tool import BaseTool


class ToolRegistry:
    """Manages registration and dynamic dispatch of agent tools.

    Usage::

        registry = ToolRegistry()
        registry.register(CalculatorTool())
        result = registry.execute("calculator", expression="2 ** 10")
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    # ------------------------------------------------------------------ #
    # Registration                                                          #
    # ------------------------------------------------------------------ #

    def register(self, tool: BaseTool) -> None:
        """Register a tool.

        Args:
            tool: A BaseTool instance to register.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if tool.name in self._tools:
            raise ValueError(
                f"A tool named '{tool.name}' is already registered. "
                "Use a unique name or unregister it first."
            )
        self._tools[tool.name] = tool

    # ------------------------------------------------------------------ #
    # Execution                                                             #
    # ------------------------------------------------------------------ #

    def execute(self, tool_name: str, **kwargs: Any) -> str:
        """Execute a registered tool by name.

        Returns a descriptive error string on any failure so the LLM can
        adapt — never raises an exception to the caller.

        Args:
            tool_name: Name as returned by the LLM's function call.
            **kwargs:  Arguments forwarded to ``BaseTool.execute()``.

        Returns:
            The tool's string result, or an ``"Error: ..."`` string.
        """
        if tool_name not in self._tools:
            available = ", ".join(self._tools) or "(none)"
            return (
                f"Error: Unknown tool '{tool_name}'. "
                f"Available tools: {available}"
            )
        try:
            return self._tools[tool_name].execute(**kwargs)
        except TypeError as exc:
            return f"Error: Invalid arguments for tool '{tool_name}': {exc}"
        except Exception as exc:
            return f"Error: Tool '{tool_name}' raised an unexpected error: {exc}"

    # ------------------------------------------------------------------ #
    # Schema access                                                         #
    # ------------------------------------------------------------------ #

    def get_declarations(self) -> list[dict]:
        """Return all function-declaration dicts for passing to the Gemini API.

        Returns:
            A flat list of declaration dicts (one per tool), each with
            ``name``, ``description``, and ``parameters`` keys.
        """
        return [tool.get_declaration() for tool in self._tools.values()]

    def get_tool_names(self) -> list[str]:
        """Return the list of registered tool names."""
        return list(self._tools.keys())

    # ------------------------------------------------------------------ #
    # Dunder helpers                                                        #
    # ------------------------------------------------------------------ #

    def __len__(self) -> int:
        return len(self._tools)

    def __repr__(self) -> str:
        return f"<ToolRegistry tools={self.get_tool_names()}>"
