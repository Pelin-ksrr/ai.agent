"""
main.py — CLI Entry Point for the AI Personal Assistant
=========================================================
Wires up all components via Dependency Injection and runs the
interactive command-line loop.

Commands:
    /help     Show available commands.
    /clear    Reset conversation memory.
    /tools    List registered tools.
    /history  Print recent conversation turns.
    /quit     Exit.
"""

import sys
import os
from dotenv import load_dotenv

from agent import Agent
from memory_manager import MemoryManager
from observers.logger_observer import LoggerObserver
from tool_registry import ToolRegistry
from tools.calculator_tool import CalculatorTool
from tools.datetime_tool import DateTimeTool
from tools.file_reader_tool import FileReaderTool
from tools.weather_tool import WeatherTool
from tools.wikipedia_tool import WikipediaTool

# -----------------------------------------------------------------------
# UI strings
# -----------------------------------------------------------------------

_BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║        AI Personal Assistant  ·  Powered by Gemini      ║
║   Type /help for commands          Ctrl-C to quit        ║
╚══════════════════════════════════════════════════════════╝
"""

_HELP = """
Commands:
  /clear    — Erase conversation memory and start fresh.
  /tools    — List all registered tools.
  /history  — Print recent conversation turns.
  /help     — Show this help message.
  /quit     — Exit the assistant.
"""


# -----------------------------------------------------------------------
# Dependency wiring
# -----------------------------------------------------------------------

def build_registry() -> ToolRegistry:
    """Instantiate and register all tools.  Extend here to add new tools."""
    registry = ToolRegistry()
    registry.register(CalculatorTool())          # built-in tool 1
    registry.register(DateTimeTool())            # built-in tool 2
    registry.register(WeatherTool())             # built-in tool 3
    registry.register(FileReaderTool())          # custom tool 1
    registry.register(WikipediaTool())           # custom tool 2
    return registry


# -----------------------------------------------------------------------
# CLI command handlers
# -----------------------------------------------------------------------

def handle_command(
    command: str,
    agent: Agent,
    memory: MemoryManager,
) -> bool:
    """Handle a /command.

    Returns:
        ``True`` to continue the main loop, ``False`` to exit.
    """
    cmd = command.strip().lower()

    if cmd == "/quit":
        print("Goodbye!")
        return False

    if cmd == "/clear":
        agent.clear_memory()
        print("\n[Conversation memory cleared.  Starting fresh.]\n")
        return True

    if cmd == "/tools":
        names = agent.get_tool_names()
        print(f"\nRegistered tools ({len(names)}):")
        for name in names:
            print(f"  • {name}")
        print()
        return True

    if cmd == "/history":
        turns = memory.get_history()
        if not turns:
            print("\n[No conversation history yet.]\n")
            return True
        print(f"\n--- Conversation History ({len(turns)} turn(s)) ---")
        for i, turn in enumerate(turns, start=1):
            user_text = turn["user"]
            asst_text = turn["assistant"]
            # Truncate long responses for display
            if len(asst_text) > 300:
                asst_text = asst_text[:300] + " …"
            print(f"\n[Turn {i}]")
            print(f"  You       : {user_text}")
            print(f"  Assistant : {asst_text}")
        print()
        return True

    if cmd == "/help":
        print(_HELP)
        return True

    print(f"\nUnknown command '{command}'. Type /help for available commands.\n")
    return True


# -----------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------

def main() -> None:
    print(_BANNER)

    # --- Wire up components (Dependency Injection) ---
    memory   = MemoryManager(max_turns=20)
    registry = build_registry()


    # Load environment variables from .env file
    load_dotenv()

    # Retrieve GEMINI_API_KEY from environment
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        print("[Error] GEMINI_API_KEY is not set in the environment.")
        sys.exit(1)

    try:
        agent = Agent(registry=registry, memory=memory)
    except EnvironmentError as exc:
        print(f"[Setup Error]\n{exc}\n")
        sys.exit(1)

    # Attach the logger observer (bonus Observer Pattern)
    logger_observer = LoggerObserver(log_file="agent.log", verbose=False)
    agent.add_observer(logger_observer)

    tool_list = ", ".join(registry.get_tool_names())
    print(f"Ready!  {len(registry)} tool(s) loaded: {tool_list}\n")

    # --- Interactive loop ---
    while True:
        try:
            raw = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        if raw.startswith("/"):
            should_continue = handle_command(raw, agent, memory)
            if not should_continue:
                break
            continue

        # Normal user message → send to agent
        print("\nAssistant: ", end="", flush=True)
        response = agent.chat(raw)
        print(response)
        print()


if __name__ == "__main__":
    main()
