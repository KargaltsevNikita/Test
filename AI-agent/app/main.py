"""FastAPI entrypoint for the website AI agent."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import SiteAgent
from app.config import get_settings
from app.schemas import ChatRequest, ChatResponse, HealthResponse, SourceItem


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize heavy dependencies once at startup."""
    settings = get_settings()
    settings.qdrant_dir.mkdir(parents=True, exist_ok=True)
    settings.leads_path.parent.mkdir(parents=True, exist_ok=True)

    # Build the compiled agent once and reuse it across requests.
    app.state.agent = SiteAgent(settings)
    yield


app = FastAPI(
    title="Safe Website AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Simple health check for uptime probes."""
    return HealthResponse(status="ok")


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Main endpoint called by the website chat widget."""
    initial_state = {
        "query": payload.message,
        "session_id": payload.session_id,
        "user_name": payload.user_name,
        "user_email": str(payload.user_email) if payload.user_email else None,
        "history": payload.history,
    }
    result = await app.state.agent.ainvoke(initial_state)

    return ChatResponse(
        answer=result["answer"],
        route=result["route"],
        sources=[SourceItem(**item) for item in result.get("sources", [])],
        lead_required=result.get("route") == "lead" and not payload.user_email,
        safe=result.get("safe", True),
    )
