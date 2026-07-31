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

import time
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import llm_client
from chatbot_tools.orchestrator import ChatbotOrchestrator

app = FastAPI(title="AI20K Student Assistant API")

# Prototype runs on localhost only; open CORS so the NiceGUI frontend (any
# local port) can call it during the hackathon demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = ChatbotOrchestrator()

# Clarification is a multi-turn negotiation (see orchestrator._handle_clarification_response).
# The frontend doesn't round-trip the clarification state itself, so we keep it
# here keyed by session_id between requests.
_session_clarifications: dict[str, dict[str, Any] | None] = {}

_GROUNDING_TOOL = {
    "grounded": {"name": "RAG Knowledge Retrieval", "icon": "📚", "status": "found"},
    "no_source": {"name": "RAG Knowledge Retrieval", "icon": "📚", "status": "no_match"},
    "not_required": {"name": "Small Talk Handler", "icon": "💬", "status": "success"},
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
    llm_status: str | None = None,
) -> dict[str, Any]:
    tools = [{"name": "Intent Classifier", "icon": "🔍", "status": "success"}]
    tool = _GROUNDING_TOOL.get(grounding_status)
    if tool:
        tools.append(tool)
    if route == "CLARIFY":
        tools.append({"name": "Context Disambiguator", "icon": "❓", "status": "need_followup"})
    elif route == "ESCALATE":
        tools.append({"name": "Escalation Router", "icon": "🚨", "status": "escalated"})

    steps = [
        f"Phân loại Intent: {intent} ({int(confidence * 100)}% confidence)",
        f"Grounding: {grounding_status} | Route: {route}",
    ]
    # llm_status is only set when this route was eligible for LLM polishing
    # (see chat() below) — surfaces whether the real OpenRouter call actually
    # ran, so it's auditable from the demo instead of a silent side effect.
    if llm_status is not None:
        tools.append({"name": "OpenRouter LLM Writer", "icon": "🤖", "status": llm_status})
        if llm_status == "success":
            steps.append("Diễn đạt lại câu trả lời bằng LLM thật (OpenRouter) — giữ nguyên số liệu/nguồn")
        elif llm_status == "not_configured":
            steps.append("Bỏ qua LLM polish: chưa cấu hình OPENROUTER_API_KEY trong .env")
        else:
            steps.append("Bỏ qua LLM polish: gọi OpenRouter lỗi/timeout, dùng câu trả lời gốc")

    return {
        "latency_ms": latency_ms,
        "confidence": confidence,
        "intent": intent,
        "tools_used": tools,
        "steps": steps,
    }


def _adapt_response(orch_result: dict[str, Any], latency_ms: int, llm_status: str | None = None) -> dict[str, Any]:
    """Map ChatbotOrchestrator's native output to the documented API response shape."""
    route = orch_result["route"]
    intent = orch_result["intent"]
    confidence = orch_result["confidence"]
    grounding = orch_result["grounding_status"]
    tracepath = _build_tracepath(route, intent, confidence, grounding, latency_ms, llm_status)

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

    # route == "ANSWER": the orchestrator has no separate "out of scope" route,
    # it answers prompt-injection attempts directly with a polite refusal.
    if intent == "reject_prompt_injection":
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
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/chat")
async def chat(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = payload.get("metadata") or {}
    message = payload.get("message") or {}
    conversation = payload.get("conversation") or {}

    session_id = metadata.get("session_id") or "default_session"
    user_id = metadata.get("user_id") or "anonymous"
    channel_id = metadata.get("channel_id") or "support_general"
    user_text = message.get("content", "")

    pending = _session_clarifications.get(session_id)

    start = time.perf_counter()
    result = orchestrator.process_message(
        message=user_text,
        user_id=user_id,
        session_id=session_id,
        channel_id=channel_id,
        pending_clarification=pending,
        conversation_history=conversation.get("history", []),
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    _session_clarifications[session_id] = (
        result.get("clarification") if result["route"] == "CLARIFY" else None
    )

    # Real AI call happens here: only for grounded direct answers (route ==
    # "ANSWER" with citations from a deterministic tool lookup) — greetings/
    # clarifications/escalations keep their structured text untouched.
    # polish_response() never raises and returns None on any failure, so a
    # missing key or a network error silently falls back to the original
    # deterministic response instead of breaking the request.
    llm_status: str | None = None
    if result["route"] == "ANSWER" and result.get("citations"):
        if not llm_client.is_configured():
            llm_status = "not_configured"
        else:
            polished = llm_client.polish_response(result["response"], result["citations"])
            if polished:
                result["response"] = polished
                llm_status = "success"
            else:
                llm_status = "error"

    return _adapt_response(result, latency_ms, llm_status)


if __name__ == "__main__":
    import os

    import uvicorn

    # PaaS hosts (Render, Railway, ...) assign a dynamic port via $PORT and
    # route traffic to it — a hardcoded 8000 would make the deployed service
    # unreachable. Falls back to 8000 for local dev, matching frontend's
    # BACKEND_URL default (see project_setup/architecture/DECISIONS.md D-008).
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
