"""LangGraph workflow definition."""

from __future__ import annotations

from functools import partial

from langgraph.graph import END, START, StateGraph
from langchain_openai import ChatOpenAI

from app.agent.guards import Guardrails
from app.agent.nodes import (
    AgentDependencies,
    answer_from_kb,
    answer_from_web,
    answer_off_topic,
    answer_unsafe,
    fallback_web_search,
    image_search_node,
    retrieve_kb,
    route_input,
    save_lead,
)
from app.agent.state import AgentState
from app.config import Settings
from app.rag.retriever import KBRetriever
from app.services.lead_store import LeadStore
from app.tools.image_search import ImageSearchTool
from app.tools.lead_capture import LeadCaptureTool
from app.tools.web_search import WebSearchTool


class SiteAgent:
    """High-level wrapper around the compiled LangGraph app."""

    def __init__(self, settings: Settings) -> None:
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_chat_model,
            temperature=0,
        )
        deps = AgentDependencies(
            llm=llm,
            guardrails=Guardrails(),
            kb=KBRetriever(settings),
            web_search=WebSearchTool(
                api_key=settings.brave_search_api_key,
                max_results=settings.max_web_results,
            ),
            image_search=ImageSearchTool(
                api_key=settings.pixabay_api_key,
                max_results=settings.max_image_results,
            ),
            lead_capture=LeadCaptureTool(LeadStore(settings.leads_path)),
        )
        self.app = self._build_graph(deps)

    def _build_graph(self, deps: AgentDependencies):
        """Construct the state graph and compile it."""
        graph = StateGraph(AgentState)

        # Bind dependencies using functools.partial so node signatures remain
        # compatible with LangGraph's expected `callable(state)` style.
        graph.add_node("route_input", partial(route_input, deps=deps))
        graph.add_node("retrieve_kb", partial(retrieve_kb, deps=deps))
        graph.add_node("fallback_web_search", partial(fallback_web_search, deps=deps))
        graph.add_node("image_search", partial(image_search_node, deps=deps))
        graph.add_node("save_lead", partial(save_lead, deps=deps))
        graph.add_node("answer_off_topic", partial(answer_off_topic, deps=deps))
        graph.add_node("answer_unsafe", partial(answer_unsafe, deps=deps))
        graph.add_node("answer_from_kb", partial(answer_from_kb, deps=deps))
        graph.add_node("answer_from_web", partial(answer_from_web, deps=deps))

        # Entry point.
        graph.add_edge(START, "route_input")

        # First branch: route by intent / safety.
        graph.add_conditional_edges(
            "route_input",
            self._route_from_classifier,
            {
                "kb": "retrieve_kb",
                "web": "fallback_web_search",
                "image": "image_search",
                "lead": "save_lead",
                "off_topic": "answer_off_topic",
                "unsafe": "answer_unsafe",
            },
        )

        # Second branch: when KB is used, decide whether we can answer or need web fallback.
        graph.add_conditional_edges(
            "retrieve_kb",
            self._route_after_retrieval,
            {
                "answer_from_kb": "answer_from_kb",
                "fallback_web_search": "fallback_web_search",
            },
        )

        graph.add_edge("fallback_web_search", "answer_from_web")

        # Terminal nodes.
        graph.add_edge("image_search", END)
        graph.add_edge("save_lead", END)
        graph.add_edge("answer_off_topic", END)
        graph.add_edge("answer_unsafe", END)
        graph.add_edge("answer_from_kb", END)
        graph.add_edge("answer_from_web", END)

        return graph.compile()

    @staticmethod
    def _route_from_classifier(state: AgentState) -> str:
        """Map state.route to graph edge names."""
        return state["route"]

    @staticmethod
    def _route_after_retrieval(state: AgentState) -> str:
        """Choose answer path after retrieval."""
        return "answer_from_kb" if state.get("kb_has_answer") else "fallback_web_search"

    async def ainvoke(self, state: AgentState) -> AgentState:
        """Execute the compiled graph asynchronously."""
        result = await self.app.ainvoke(state)
        return result
