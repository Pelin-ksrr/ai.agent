"""
Wikipedia Tool  (Custom Tool #2)
=================================
Fetches a concise summary for any topic from Wikipedia using the
official REST API (no API key required).

Endpoint: https://en.wikipedia.org/api/rest_v1/page/summary/{title}
"""

from urllib.parse import quote

import requests

from tools.base_tool import BaseTool

_BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_TIMEOUT = 10  # seconds
_USER_AGENT = "AIAgentAssistant/1.0 (educational project; contact: student)"


class WikipediaTool(BaseTool):
    """Fetches a concise Wikipedia summary for a given topic."""

    @property
    def name(self) -> str:
        return "search_wikipedia"

    @property
    def description(self) -> str:
        return "Searches Wikipedia and returns a summary for a topic or keyword."

    def execute(self, topic: str) -> str:
        encoded = quote(topic.strip().replace(" ", "_"))
        url = _BASE_URL.format(title=encoded)
        try:
            response = requests.get(
                url,
                timeout=_TIMEOUT,
                headers={"User-Agent": _USER_AGENT},
            )
            if response.status_code == 404:
                return (
                    f"No Wikipedia article found for '{topic}'. "
                    "Try rephrasing or using the exact article title."
                )
            response.raise_for_status()
            data = response.json()

            title   = data.get("title", topic)
            extract = data.get("extract", "No summary available.")
            page_url = (
                data.get("content_urls", {}).get("desktop", {}).get("page", "")
            )

            result = f"Wikipedia — {title}\n\n{extract}"
            if page_url:
                result += f"\n\nRead more: {page_url}"
            return result

        except requests.exceptions.Timeout:
            return f"Error: Timed out while fetching Wikipedia article for '{topic}'."
        except requests.exceptions.HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else "?"
            return f"Error: Wikipedia returned HTTP {code} for '{topic}'."
        except (KeyError, ValueError) as exc:
            return f"Error: Unexpected response format from Wikipedia ({exc})."
        except requests.exceptions.RequestException as exc:
            return f"Error: Network failure while contacting Wikipedia ({exc})."

    def get_declaration(self) -> dict:
        return {
            "name": self.name,
            "description": (
                "Searches Wikipedia and returns a short summary for the given topic. "
                "Useful for factual questions, definitions, historical events, "
                "science concepts, famous people, and general encyclopedic knowledge."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": (
                            "The topic or keyword to look up, e.g. "
                            "'Python programming language', 'Eiffel Tower', "
                            "'Quantum entanglement', 'Mustafa Kemal Ataturk'."
                        ),
                    }
                },
                "required": ["topic"],
            },
        }
