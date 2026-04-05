"""Shared state passed between LangGraph nodes."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


RouteName = Literal[
    "kb",
    "web",
    "image",
    "lead",
    "off_topic",
    "unsafe",
]


class AgentState(TypedDict, total=False):
    # Raw user input
    query: str
    session_id: str
    user_name: str | None
    user_email: str | None
    history: list[dict[str, str]]

    # Routing and safety
    route: RouteName
    safe: bool
    safety_reason: str

    # Retrieval / tools
    kb_context: list[dict[str, Any]]
    kb_has_answer: bool
    web_results: list[dict[str, Any]]
    image_results: list[dict[str, Any]]

    # Business flow
    lead_status: str
    lead_payload: dict[str, Any]

    # Final output
    answer: str
    sources: list[dict[str, Any]]
