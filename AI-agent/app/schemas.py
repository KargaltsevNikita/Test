"""API request and response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, EmailStr


class ChatRequest(BaseModel):
    """Incoming user message from the website chat widget."""

    session_id: str = Field(..., description="Unique user session identifier")
    message: str = Field(..., min_length=1, description="Raw user message")
    user_name: str | None = Field(default=None)
    user_email: EmailStr | None = Field(default=None)
    history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Short chat history with role/content entries",
    )


class SourceItem(BaseModel):
    """Source shown to the frontend so answers are auditable."""

    title: str
    url: str | None = None
    snippet: str | None = None
    source_type: Literal["kb", "web", "image", "system"]


class ChatResponse(BaseModel):
    """Final answer returned to the website."""

    answer: str
    route: str
    sources: list[SourceItem] = Field(default_factory=list)
    lead_required: bool = False
    safe: bool = True


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str
