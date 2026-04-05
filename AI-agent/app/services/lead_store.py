"""Simple lead storage service.

In production, replace this with CRM / PostgreSQL / webhook integration.
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any


class LeadStore:
    """Append leads to a JSONL file for easy inspection."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def save(self, payload: dict[str, Any]) -> None:
        """Persist one lead as a JSON line."""
        record = {
            "created_at": datetime.now(UTC).isoformat(),
            **payload,
        }
        with self.filepath.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
