"""
File Reader Tool  (Custom Tool #1)
==================================
Reads the text content of a local file and returns it as a string.

Security controls:
  - Allowed file extensions whitelist (no executables, no binaries).
  - Maximum file-size cap (50 KB) to prevent large memory consumption.
  - No path-traversal check needed for local use, but the resolved path is
    displayed so the user can verify what was read.
"""

from pathlib import Path

from tools.base_tool import BaseTool

_MAX_BYTES = 50_000  # 50 KB
_ALLOWED_EXTENSIONS = frozenset(
    {".txt", ".md", ".csv", ".json", ".log", ".py", ".html", ".xml", ".yaml", ".yml"}
)


class FileReaderTool(BaseTool):
    """Reads a local text file and returns its contents."""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Reads and returns the text contents of a local file."

    def execute(self, file_path: str) -> str:
        try:
            path = Path(file_path.strip()).resolve()
        except Exception as exc:
            return f"Error: Invalid file path '{file_path}': {exc}"

        # Extension whitelist
        if path.suffix.lower() not in _ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(_ALLOWED_EXTENSIONS))
            return (
                f"Error: File type '{path.suffix}' is not allowed. "
                f"Supported extensions: {allowed}"
            )

        if not path.exists():
            return f"Error: File not found — '{file_path}'"
        if not path.is_file():
            return f"Error: '{file_path}' is not a regular file."

        size = path.stat().st_size
        if size > _MAX_BYTES:
            return (
                f"Error: File is too large ({size // 1024} KB). "
                f"Maximum allowed size is {_MAX_BYTES // 1024} KB."
            )

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except PermissionError:
            return f"Error: Permission denied when reading '{file_path}'."
        except Exception as exc:
            return f"Error reading '{file_path}': {exc}"

        line_count = content.count("\n") + 1
        return f"File: {path.name}  ({line_count} lines, {size} bytes)\n---\n{content}"

    def get_declaration(self) -> dict:
        return {
            "name": self.name,
            "description": (
                "Reads and returns the text contents of a local file. "
                "Supports: .txt, .md, .csv, .json, .log, .py, .html, .xml, .yaml, .yml. "
                "Maximum file size: 50 KB."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": (
                            "Absolute or relative path to the file. "
                            "Examples: 'notes.txt', 'C:/Users/user/report.md'."
                        ),
                    }
                },
                "required": ["file_path"],
            },
        }
