# server.py
"""HTTP entry point for the chatbot backend.

Exposes POST /api/v1/chat following the contract documented in
frontend/GUIDE_FRONTEND_BACKEND.md (Request Template / Response Template with
tracepath). Internally it drives chatbot_tools.orchestrator.ChatbotOrchestrator,
whose native output shape (route/clarification/escalation/grounding_status)
is adapted here into the status/action/follow_up/handoff contract the
frontend's ai_router.py already expects.

Run from this directory:
    python server.py
or:
    uvicorn server:app --reload --port 8000
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from chatbot_tools.llm_client import load_backend_env
from chatbot_tools.orchestrator import ChatbotOrchestrator

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load backend configuration before freezing the orchestrator clients."""
    load_backend_env()
    active_orchestrator = ChatbotOrchestrator()
    app.state.orchestrator = active_orchestrator
    logger.info(
        "OpenRouter configured=%s model=%s",
        active_orchestrator.llm_client.is_available(),
        active_orchestrator.llm_client.config.model,
    )
    yield


app = FastAPI(title="AI20K Student Assistant API", lifespan=lifespan)

# Prototype runs on localhost only; open CORS so the NiceGUI frontend (any
# local port) can call it during the hackathon demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clarification is a multi-turn negotiation (see orchestrator._handle_clarification_response).
# The frontend doesn't round-trip the clarification state itself, so we keep it
# here keyed by session_id between requests.
_session_clarifications: dict[str, dict[str, Any] | None] = {}

_GROUNDING_TOOL = {
    "grounded": {"name": "RAG Knowledge Retrieval", "icon": "📚", "status": "found"},
    "no_source": {"name": "RAG Knowledge Retrieval", "icon": "📚", "status": "no_match"},
    "unsupported": {"name": "RAG Knowledge Retrieval", "icon": "📚", "status": "unsupported"},
    "conflict": {"name": "RAG Knowledge Retrieval", "icon": "📚", "status": "conflict"},
    "not_required": {"name": "Small Talk Handler", "icon": "💬", "status": "success"},
}

_ESCALATION_RETRIEVAL_STATUS = {
    "conflicting_sources": "conflict",
    "related_knowledge_gap": "unsupported",
    "official_source_not_found": "no_source",
}


def _to_frontend_citations(citations: list[dict[str, Any]]) -> list[dict[str, str]]:
    result = []
    for c in citations:
        title = c.get("title", "")
        locator = c.get("locator", "")
        source = f"{title} ({locator})" if locator else title
        result.append({"source": f"Nguồn căn cứ: {source}", "quote": c.get("quote", "")})
    return result


def _build_tracepath(
    route: str,
    intent: str,
    confidence: float,
    grounding_status: str,
    latency_ms: int,
    llm: dict[str, Any] | None = None,
    escalation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    retrieval_status = _ESCALATION_RETRIEVAL_STATUS.get(
        (escalation or {}).get("reason_code"),
        grounding_status,
    )
    tools = [{"name": "Intent Classifier", "icon": "🔍", "status": "success"}]
    tool = _GROUNDING_TOOL.get(retrieval_status)
    if tool:
        tools.append(tool)
    if route == "CLARIFY":
        tools.append({"name": "Context Disambiguator", "icon": "❓", "status": "need_followup"})
    elif route == "ESCALATE":
        tools.append({"name": "Escalation Router", "icon": "🚨", "status": "escalated"})

    steps = [
        f"Phân loại Intent: {intent} ({int(confidence * 100)}% confidence)",
        f"Grounding: {retrieval_status} | Route: {route}",
    ]
    llm_called = bool(llm and llm.get("called"))
    llm_model = llm.get("model") if llm else None
    llm_usage = llm.get("usage", {}) if llm else {}
    if llm_called:
        llm_status = llm.get("status", "unknown")
        tools.append(
            {
                "name": f"OpenRouter · {llm_model or 'unknown model'}",
                "icon": "🤖",
                "status": llm_status,
            }
        )
        total_tokens = llm_usage.get("total_tokens", 0)
        steps.append(
            f"OpenRouter: {llm_status} | model: {llm_model or 'unknown'} "
            f"| total tokens: {total_tokens}"
        )

    return {
        "latency_ms": latency_ms,
        "confidence": confidence,
        "intent": intent,
        "grounding_status": retrieval_status,
        "llm_called": llm_called,
        "model": llm_model,
        "usage": llm_usage,
        "llm_stage": llm.get("stage") if llm else None,
        "llm_stages": llm.get("stages", []) if llm else [],
        "agent_decision": llm.get("decision") if llm else None,
        "tools_used": tools,
        "steps": steps,
    }


def _adapt_response(orch_result: dict[str, Any], latency_ms: int) -> dict[str, Any]:
    """Map ChatbotOrchestrator's native output to the documented API response shape."""
    route = orch_result["route"]
    intent = orch_result["intent"]
    confidence = orch_result["confidence"]
    grounding = orch_result["grounding_status"]
    tracepath = _build_tracepath(
        route,
        intent,
        confidence,
        grounding,
        latency_ms,
        orch_result.get("llm"),
        orch_result.get("escalation"),
    )

    if route == "CLARIFY":
        clarification = orch_result.get("clarification") or {}
        return {
            "status": "need_clarification",
            "intent": intent,
            "confidence": confidence,
            "action": "ask_follow_up",
            "response": orch_result["response"],
            "follow_up": clarification.get("suggested_replies", []),
            "citations": [],
            "handoff": False,
            "tracepath": tracepath,
        }

    if route == "ESCALATE":
        return {
            "status": "escalated",
            "intent": intent,
            "confidence": confidence,
            "action": "escalate_mod",
            "response": orch_result["response"],
            "follow_up": [],
            "citations": _to_frontend_citations(orch_result.get("citations", [])),
            "handoff": True,
            "tracepath": tracepath,
        }

    # Policy refusals are ANSWER routes internally so they never enter the
    # handoff path, but the frontend should render them as out-of-scope/reject.
    if intent in {"out_of_domain", "reject_prompt_injection"}:
        return {
            "status": "out_of_scope",
            "intent": intent,
            "confidence": confidence,
            "action": "reject",
            "response": orch_result["response"],
            "follow_up": [],
            "citations": [],
            "handoff": False,
            "tracepath": tracepath,
        }

    return {
        "status": "resolved",
        "intent": intent,
        "confidence": confidence,
        "action": "direct_answer",
        "response": orch_result["response"],
        "follow_up": [],
        "citations": _to_frontend_citations(orch_result.get("citations", [])),
        "handoff": False,
        "tracepath": tracepath,
    }


@app.get("/health")
def health(request: Request) -> dict[str, Any]:
    active_orchestrator = request.app.state.orchestrator
    return {
        "status": "ok",
        "openrouter_configured": active_orchestrator.llm_client.is_available(),
        "openrouter_model": active_orchestrator.llm_client.config.model,
        "default_cohort": active_orchestrator.default_cohort,
        "knowledge_cohort_aliases": (
            active_orchestrator.registry.knowledge.cohort_aliases
        ),
        "knowledge_cohort_alias_categories": sorted(
            active_orchestrator.registry.knowledge.cohort_alias_categories
        ),
        "routing_mode": (
            "hybrid_agent"
            if active_orchestrator.llm_client.is_available()
            else "deterministic_fallback"
        ),
    }


@app.post("/api/v1/chat")
async def chat(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    metadata = payload.get("metadata") or {}
    message = payload.get("message") or {}
    conversation = payload.get("conversation") or {}
    learning_context = payload.get("learning_context") or {}
    runtime = payload.get("runtime") or {}

    session_id = metadata.get("session_id") or "default_session"
    user_id = metadata.get("user_id") or "anonymous"
    channel_id = metadata.get("channel_id") or "support_general"
    user_text = message.get("content", "")

    pending = _session_clarifications.get(session_id)

    start = time.perf_counter()
    result = request.app.state.orchestrator.process_message(
        message=user_text,
        user_id=user_id,
        session_id=session_id,
        channel_id=channel_id,
        pending_clarification=pending,
        conversation_history=conversation.get("history", []),
        cohort=(
            learning_context.get("cohort")
            or runtime.get("cohort")
            or None
        ),
        at=metadata.get("timestamp"),
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    _session_clarifications[session_id] = (
        result.get("clarification") if result["route"] == "CLARIFY" else None
    )

    return _adapt_response(result, latency_ms)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
