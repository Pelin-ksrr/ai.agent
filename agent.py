"""
Agent — ReAct Orchestrator (Reason → Act → Observe)
=====================================================
Core component that connects the LLM, tools, memory, and observers.

Design Patterns Applied:
  - ReAct Pattern: the chat() method drives a Reason→Act→Observe loop.
  - Strategy Pattern (via ToolRegistry): tools are selected and executed
    by name without if/elif chains inside the Agent.
  - Observer Pattern: state changes are broadcast to subscribed observers
    without the Agent knowing their concrete types.

SOLID Principles:
  - SRP: Agent orchestrates; it does not implement tool logic, memory
    storage, or logging.
  - OCP: adding tools / observers requires no Agent modification.
  - DIP: depends on BaseTool (via ToolRegistry) and BaseObserver
    abstractions, never on concrete classes.
"""

from __future__ import annotations

import os
from typing import Any

import google.generativeai as genai
import google.generativeai.protos as protos

from dotenv import load_dotenv

from memory_manager import MemoryManager
from observers.base_observer import BaseObserver
from tool_registry import ToolRegistry

# -----------------------------------------------------------------------
# System instruction sent to the LLM at the start of every session
# -----------------------------------------------------------------------
_SYSTEM_INSTRUCTION = """
You are a helpful and knowledgeable personal assistant.

You have access to the following tools. Use them proactively and reliably:
    - calculator       : for ANY mathematical computation (never calculate mentally).
    - get_datetime     : for current date/time questions.
    - get_weather      : for ALL weather-related queries (temperature, degree, weather, wind, humidity, etc). Never answer weather questions yourself; always call the get_weather tool with the city name, even if the user only says a city and a weather-related word.
    - read_file        : when asked to read or analyse a local file.
    - search_wikipedia : for factual, encyclopedic, or historical questions.

When the user asks about weather, temperature, degree, wind, humidity, or similar for any city, always call get_weather with the city name. Do not ask the user to clarify if the city is clear. If the city is not clear, politely ask for the city name.

Examples:
    User: What is the weather in Paris?
        → Call get_weather(city="Paris")
    User: degree in riga
        → Call get_weather(city="Riga")
    User: sıcaklık istanbul
        → Call get_weather(city="Istanbul")
    User: hava durumu ankara
        → Call get_weather(city="Ankara")
    User: humidity in Berlin
        → Call get_weather(city="Berlin")

For general conversation, opinion, explanation, or creative tasks respond directly.
If a tool call fails, explain the error clearly and suggest an alternative.
Keep responses concise and helpful.
"""

# Safety limit: prevent infinite tool-call loops
_MAX_TOOL_ITERATIONS = 10


class Agent:
    """Personal assistant agent implementing the ReAct loop with Gemini.

    Args:
        registry:    Populated ToolRegistry instance.
        memory:      MemoryManager instance for conversation history.
        model_name:  Gemini model identifier (default: gemini-2.5-flash-lite).

    Raises:
        EnvironmentError: If ``GEMINI_API_KEY`` is not set.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        memory: MemoryManager,
        model_name: str = "gemini-2.5-flash-lite",  # Updated default model
    ) -> None:
        self._registry = registry
        self._memory = memory
        self._model_name = model_name
        self._observers: list[BaseObserver] = []

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY environment variable is not set.\n"
                "  1. Go to https://aistudio.google.com/ and create a free API key.\n"
                "  2. Run:  set GEMINI_API_KEY=your_key_here   (Windows)\n"
                "        or export GEMINI_API_KEY=your_key_here (Linux/macOS)"
            )

        genai.configure(api_key=api_key)

        
        gemini_tools = self._build_gemini_tools()

        self._model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=_SYSTEM_INSTRUCTION,
            tools=gemini_tools if gemini_tools else None,
        )

        # One persistent chat session per Agent lifetime
        self._chat: genai.ChatSession = self._model.start_chat(history=[])

    # ------------------------------------------------------------------ #
    # Public interface                                                      #
    # ------------------------------------------------------------------ #

    def add_observer(self, observer: BaseObserver) -> None:
        """Subscribe an observer to receive agent events."""
        self._observers.append(observer)

    def chat(self, user_input: str) -> str:
        """Process a user message and return the agent's response.

        Drives the full ReAct loop internally:
          Reason  → send to Gemini
          Act     → execute any requested tools
          Observe → feed results back to Gemini
          (repeat until a final text answer is produced)

        Args:
            user_input: The user's natural-language query.

        Returns:
            The agent's final natural-language response string.
        """
        user_input = user_input.strip()
        if not user_input:
            return "Please enter a message."

        self._notify("user_input", {"text": user_input})

        try:
            final_response = self._react_loop(user_input)
        except Exception as exc:
            final_response = (
                "I encountered an unexpected error while processing your request. "
                f"Details: {exc}"
            )
            self._notify("error", {"message": str(exc)})

        self._memory.add_turn(user_input, final_response)
        self._notify("agent_response", {"text": final_response})
        return final_response

    def clear_memory(self) -> None:
        """Clear conversation history and reset the Gemini chat session."""
        self._memory.clear()
        self._chat = self._model.start_chat(history=[])
        self._notify("session_clear", {})

    def get_turn_count(self) -> int:
        """Return the number of completed conversation turns."""
        return self._memory.get_turn_count()

    def get_tool_names(self) -> list[str]:
        """Return the names of all registered tools."""
        return self._registry.get_tool_names()

    # ------------------------------------------------------------------ #
    # ReAct loop                                                            #
    # ------------------------------------------------------------------ #

    def _react_loop(self, user_input: str) -> str:
        """Reason → Act → Observe loop.

        1. Send user input to Gemini.
        2. If the model requests tool calls → execute them (Act).
        3. Send all tool results back to Gemini (Observe).
        4. Repeat until the model returns plain text (final answer).
        """
        response = self._chat.send_message(user_input)

        for _ in range(_MAX_TOOL_ITERATIONS):
            fn_calls = self._extract_function_calls(response)

            if not fn_calls:
                # Model produced a final text answer — we're done.
                return self._safe_text(response)

            # ACT: execute every requested tool (handles parallel calls)
            tool_response_parts: list[protos.Part] = []
            for fn_call in fn_calls:
                tool_name = fn_call.name
                tool_args = dict(fn_call.args)

                self._notify("tool_called", {"tool_name": tool_name, "args": tool_args})
                result = self._registry.execute(tool_name, **tool_args)

                event = "tool_error" if result.startswith("Error:") else "tool_result"
                self._notify(event, {"tool_name": tool_name, "result": result})

                tool_response_parts.append(
                    protos.Part(
                        function_response=protos.FunctionResponse(
                            name=tool_name,
                            response={"result": result},
                        )
                    )
                )

            response = self._chat.send_message(tool_response_parts)

        return (
            "I could not complete this task within the allowed number of steps. "
            "Please try breaking your request into smaller parts."
        )

    # ------------------------------------------------------------------ #
    # Private helpers                                                       #
    # ------------------------------------------------------------------ #

    def _extract_function_calls(self, response: Any) -> list:
        """Return all function-call parts from a Gemini response (may be empty)."""
        calls = []
        try:
            for part in response.parts:
                if hasattr(part, "function_call") and part.function_call.name:
                    calls.append(part.function_call)
        except (AttributeError, ValueError):
            pass
        return calls

    @staticmethod
    def _safe_text(response: Any) -> str:
        """Extract response text; return a user-friendly message if blocked or missing."""
        text = getattr(response, "text", None)
        if text:
            return text
        parts = getattr(response, "parts", None)
        if parts and isinstance(parts, (list, tuple)):
            for part in parts:
                part_text = getattr(part, "text", None)
                if part_text:
                    return part_text
        return (
            "Yanıt üretilemedi veya güvenlik filtresine takıldı. Lütfen isteğinizi daha açık ve şehir ismini net belirterek tekrar deneyin. "
            "(Not: Eğer sorun devam ederse, farklı bir şehir veya daha basit bir cümleyle tekrar deneyin.)"
        )

    def _notify(self, event: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all subscribed observers."""
        for observer in self._observers:
            try:
                observer.update(event, data)
            except Exception:
                pass 

    def _build_gemini_tools(self) -> list[protos.Tool]:
        """Convert plain-dict declarations to Gemini protos.Tool objects.

        Keeps tool/registry code free of Gemini-specific types (DIP).
        """
        declarations = self._registry.get_declarations()
        if not declarations:
            return []

        fn_decls: list[protos.FunctionDeclaration] = []
        for decl in declarations:
            params_dict = decl.get("parameters", {"type": "object"})
            fn_decls.append(
                protos.FunctionDeclaration(
                    name=decl["name"],
                    description=decl.get("description", ""),
                    parameters=self._dict_to_schema(params_dict),
                )
            )
        return [protos.Tool(function_declarations=fn_decls)]

    def _dict_to_schema(self, d: dict) -> protos.Schema:
        """Recursively convert a JSON-Schema dict to a protos.Schema object."""
        _TYPE_MAP: dict[str, int] = {
            "string":  protos.Type.STRING,
            "number":  protos.Type.NUMBER,
            "integer": protos.Type.INTEGER,
            "boolean": protos.Type.BOOLEAN,
            "array":   protos.Type.ARRAY,
            "object":  protos.Type.OBJECT,
        }
        schema_type = _TYPE_MAP.get(
            d.get("type", "string").lower(), protos.Type.STRING
        )

        props = {
            k: self._dict_to_schema(v)
            for k, v in d.get("properties", {}).items()
        }

        kwargs: dict[str, Any] = {
            "type_": schema_type,
            "description": d.get("description", ""),
        }
        if props:
            kwargs["properties"] = props
        if d.get("required"):
            kwargs["required"] = d["required"]
        if "items" in d:
            kwargs["items"] = self._dict_to_schema(d["items"])

        return protos.Schema(**kwargs)
