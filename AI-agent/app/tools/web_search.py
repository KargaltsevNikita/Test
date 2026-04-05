"""Web search tool.

This implementation uses Brave Search because it has a straightforward REST API.
Replace it with another search provider if needed.
"""

from __future__ import annotations

from typing import Any

import httpx


class WebSearchTool:
    """Thin HTTP wrapper over a search provider."""

    BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str, max_results: int = 5) -> None:
        self.api_key = api_key
        self.max_results = max_results

    async def run(self, query: str) -> list[dict[str, Any]]:
        """Return normalized search results.

        If the key is missing we fail gracefully instead of crashing the agent.
        """
        if not self.api_key:
            return []

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }
        params = {
            "q": query,
            "count": self.max_results,
            "text_decorations": False,
            "extra_snippets": True,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(self.BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()

        results: list[dict[str, Any]] = []
        for item in payload.get("web", {}).get("results", []):
            results.append(
                {
                    "title": item.get("title", "Без названия"),
                    "url": item.get("url"),
                    "snippet": " ".join(item.get("extra_snippets", []) or [])
                    or item.get("description", ""),
                    "source_type": "web",
                }
            )
        return results
