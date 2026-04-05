"""LangGraph nodes.

Each function takes the shared state and returns a partial state update.
Keeping the nodes small makes the graph easier to debug and test.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agent.guards import Guardrails
from app.agent.prompts import (
    ANSWER_FROM_KB_PROMPT,
    ANSWER_FROM_WEB_PROMPT,
    OFF_TOPIC_ANSWER,
    SYSTEM_PROMPT,
    UNSAFE_ANSWER,
)
from app.agent.state import AgentState
from app.rag.retriever import KBRetriever
from app.tools.image_search import ImageSearchTool
from app.tools.lead_capture import LeadCaptureTool
from app.tools.web_search import WebSearchTool


class AgentDependencies:
    """Container object passed into nodes so the graph stays pure-ish."""

    def __init__(
        self,
        *,
        llm: ChatOpenAI,
        guardrails: Guardrails,
        kb: KBRetriever,
        web_search: WebSearchTool,
        image_search: ImageSearchTool,
        lead_capture: LeadCaptureTool,
    ) -> None:
        self.llm = llm
        self.guardrails = guardrails
        self.kb = kb
        self.web_search = web_search
        self.image_search = image_search
        self.lead_capture = lead_capture


async def route_input(state: AgentState, deps: AgentDependencies) -> dict[str, Any]:
    """Classify the query using deterministic rules."""
    result = deps.guardrails.check(state["query"])
    return {
        "route": result.route,
        "safe": result.safe,
        "safety_reason": result.reason,
    }


async def retrieve_kb(state: AgentState, deps: AgentDependencies) -> dict[str, Any]:
    """Search the vector DB before using external search."""
    docs = deps.kb.similarity_search(state["query"], k=4)
    return {
        "kb_context": docs,
        "kb_has_answer": deps.kb.has_confident_answer(docs),
    }


async def fallback_web_search(state: AgentState, deps: AgentDependencies) -> dict[str, Any]:
    """Call web search only when KB could not answer or freshness is needed."""
    results = await deps.web_search.run(state["query"])
    return {"web_results": results}


async def image_search_node(state: AgentState, deps: AgentDependencies) -> dict[str, Any]:
    """Fetch image links relevant to the user request."""
    results = await deps.image_search.run(state["query"])

    if not results:
        answer = "Я не нашёл подходящих изображений по запросу."
    else:
        lines = ["Я нашёл подходящие изображения:"]
        for idx, item in enumerate(results, start=1):
            lines.append(f"{idx}. {item['title']} — {item['url']}")
        answer = "\n".join(lines)

    return {
        "image_results": results,
        "sources": results,
        "answer": answer,
    }


async def save_lead(state: AgentState, deps: AgentDependencies) -> dict[str, Any]:
    """Store a lead for manager follow-up."""
    result = deps.lead_capture.run(
        session_id=state["session_id"],
        query=state["query"],
        user_name=state.get("user_name"),
        user_email=state.get("user_email"),
    )

    if state.get("user_email"):
        answer = (
            "Готово — я сохранил заявку для менеджера. "
            "Менеджер сможет связаться по указанному email."
        )
    else:
        answer = (
            "Я зафиксировал намерение оставить заявку, но у меня нет контакта пользователя. "
            "Попросите его оставить email или телефон на сайте."
        )

    return {
        "lead_status": result["status"],
        "lead_payload": result["payload"],
        "answer": answer,
        "sources": [
            {
                "title": "Lead capture",
                "url": None,
                "snippet": result["message"],
                "source_type": "system",
            }
        ],
    }


async def answer_off_topic(_: AgentState, __: AgentDependencies) -> dict[str, Any]:
    """Return a controlled refusal for out-of-domain questions."""
    return {
        "answer": OFF_TOPIC_ANSWER,
        "sources": [
            {
                "title": "Domain policy",
                "url": None,
                "snippet": "Question outside allowed domain",
                "source_type": "system",
            }
        ],
    }


async def answer_unsafe(_: AgentState, __: AgentDependencies) -> dict[str, Any]:
    """Return a controlled refusal for unsafe content."""
    return {
        "answer": UNSAFE_ANSWER,
        "sources": [
            {
                "title": "Safety policy",
                "url": None,
                "snippet": "Unsafe request blocked",
                "source_type": "system",
            }
        ],
    }


async def answer_from_kb(state: AgentState, deps: AgentDependencies) -> dict[str, Any]:
    """Generate an answer grounded only in KB context."""
    context = "\n\n".join(
        f"[{idx}] {item['text']}" for idx, item in enumerate(state.get("kb_context", []), start=1)
    )
    prompt = ANSWER_FROM_KB_PROMPT.format(query=state["query"], context=context)

    response = await deps.llm.ainvoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )

    sources = [
        {
            "title": item["title"],
            "url": item.get("url"),
            "snippet": item.get("snippet"),
            "source_type": "kb",
        }
        for item in state.get("kb_context", [])
    ]
    return {"answer": response.content, "sources": sources}


async def answer_from_web(state: AgentState, deps: AgentDependencies) -> dict[str, Any]:
    """Generate an answer from normalized web search results."""
    if not state.get("web_results"):
        return {
            "answer": (
                "Я не нашёл надёжных веб-результатов по запросу. "
                "Попробуйте уточнить вопрос или пополнить базу знаний."
            ),
            "sources": [],
        }

    context = json.dumps(state["web_results"], ensure_ascii=False, indent=2)
    prompt = ANSWER_FROM_WEB_PROMPT.format(query=state["query"], context=context)

    response = await deps.llm.ainvoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
    )
    return {"answer": response.content, "sources": state["web_results"]}
