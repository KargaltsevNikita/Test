"""Tool for capturing a lead from chat."""

from __future__ import annotations

from typing import Any

from app.services.lead_store import LeadStore


class LeadCaptureTool:
    """Business tool that saves a manager request."""

    def __init__(self, store: LeadStore) -> None:
        self.store = store

    def run(
        self,
        *,
        session_id: str,
        query: str,
        user_name: str | None,
        user_email: str | None,
    ) -> dict[str, Any]:
        """Save minimal information required for follow-up.

        The current MVP stores only the essentials. In production you may add
        phone number, company, product line, consent flags, and CRM ID.
        """
        payload = {
            "session_id": session_id,
            "user_name": user_name,
            "user_email": user_email,
            "request": query,
        }
        self.store.save(payload)
        return {
            "status": "saved",
            "message": (
                "Заявка сохранена. Менеджер сможет связаться с пользователем по указанным контактам."
            ),
            "payload": payload,
        }
