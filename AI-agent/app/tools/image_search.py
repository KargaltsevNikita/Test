"""Image search tool.

For the MVP we use Pixabay's API because it is simple and returns safe-ish stock
images. You can swap it for another provider later.
"""

from __future__ import annotations

from typing import Any

import httpx


class ImageSearchTool:
    """Fetch image previews relevant to the user query."""

    BASE_URL = "https://pixabay.com/api/"

    def __init__(self, api_key: str, max_results: int = 5) -> None:
        self.api_key = api_key
        self.max_results = max_results

    async def run(self, query: str) -> list[dict[str, Any]]:
        """Return a compact list of image results."""
        if not self.api_key:
            return []

        params = {
            "key": self.api_key,
            "q": query,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": self.max_results,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        return [
            {
                "title": item.get("tags", "image"),
                "url": item.get("pageURL"),
                "preview_url": item.get("previewURL"),
                "snippet": f"Preview: {item.get('previewURL', '')}",
                "source_type": "image",
            }
            for item in payload.get("hits", [])
        ]
