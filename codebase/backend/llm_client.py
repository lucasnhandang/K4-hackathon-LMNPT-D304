# llm_client.py
"""LLM-backed response polishing via OpenRouter — the backend's real AI call.

Deliberately lives outside `chatbot_tools/` (which documents itself as
needing "Không cần API key hoặc package ngoài Python standard library" —
see chatbot_tools/README.md). This module is the one place in the backend
that makes an outbound call to a real LLM; everything else (intent
classification, BM25 retrieval, tool lookups, citation/conflict checks)
stays deterministic and dependency-free.

Design: chatbot_tools remains the only source of *facts* — dates, XP rules,
channel IDs, citations. This module only rephrases an already-grounded
answer into more natural Vietnamese; the prompt explicitly forbids adding
any fact not already present in the input. If the API key is missing, the
call fails, or times out, callers must fall back to the original
deterministic text — same "never let the AI layer break the demo" pattern
as frontend/ai_router.py's USE_LOCAL_MOCK fallback (see
project_setup/architecture/DECISIONS.md D-002 and D-006).

Uses only the Python standard library (urllib) — no new pip dependency for
the HTTP call itself; only python-dotenv is added, to load .env the same
way frontend/ai_router.py already does.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 6.0
_PLACEHOLDER_PREFIX = "replace_with_"

_SYSTEM_PROMPT = (
    "Bạn là biên tập viên câu trả lời cho trợ lý học viên khóa AI20K Build Phase. "
    "Nhiệm vụ DUY NHẤT: diễn đạt lại câu trả lời đã cho bằng tiếng Việt tự nhiên, "
    "thân thiện, ngắn gọn (tối đa 3 câu). "
    "TUYỆT ĐỐI KHÔNG được thêm, đoán, hoặc suy diễn bất kỳ thông tin nào "
    "(ngày giờ, con số, tên kênh, quy định...) không có trong nội dung gốc bên dưới. "
    "Nếu không chắc phần nào, giữ nguyên nguyên văn phần đó. "
    "Không thêm lời chào, không hỏi thêm câu hỏi mới, không thêm emoji ngoài văn bản gốc."
)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def is_configured() -> bool:
    """True when OPENROUTER_API_KEY + OPENROUTER_MODEL are actually set.

    Returns False for the untouched `.env.example` placeholders
    (`replace_with_...`), so a freshly-copied `.env` with no real key is
    correctly treated as "not configured" instead of attempting (and
    failing) a network call on every request.
    """
    key = _env("OPENROUTER_API_KEY")
    model = _env("OPENROUTER_MODEL")
    if not key or key.startswith(_PLACEHOLDER_PREFIX):
        return False
    if not model or model.startswith(_PLACEHOLDER_PREFIX):
        return False
    return True


def polish_response(original_text: str, citations: list[dict] | None = None) -> str | None:
    """Rephrase `original_text` via OpenRouter chat completions.

    `citations` are `Citation`-shaped dicts (source_id/title/locator/quote/
    updated_at, see chatbot_tools/models.py) already selected by the
    deterministic tools — passed as read-only reference so the model has
    the exact grounded facts in front of it and no reason to invent
    anything.

    Returns the polished text, or None on any failure (not configured,
    network error, malformed response, empty output) — callers MUST fall
    back to `original_text` when this returns None. Never raises.
    """
    if not is_configured():
        return None
    if not original_text or not original_text.strip():
        return None

    citations = citations or []
    reference = "\n".join(
        f"- {c.get('title', '')}: {c.get('quote', '')}" for c in citations if c.get("quote")
    )
    user_content = original_text
    if reference:
        user_content += (
            "\n\n[Nguồn tham chiếu — chỉ để đối chiếu, KHÔNG thêm gì ngoài đây]\n" + reference
        )

    body = {
        "model": _env("OPENROUTER_MODEL"),
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "max_tokens": 300,
    }

    base_url = _env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_env('OPENROUTER_API_KEY')}",
            # Recommended by OpenRouter for attribution/rate-limit routing — see
            # https://openrouter.ai/docs — harmless to omit but nice to keep.
            "HTTP-Referer": _env("OPENROUTER_SITE_URL", "http://localhost"),
            "X-Title": _env("OPENROUTER_APP_NAME", "AI20K-Student-Assistant"),
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        text = payload["choices"][0]["message"]["content"].strip()
        return text or None
    except urllib.error.HTTPError as exc:
        # OpenRouter puts the useful message in the response body (e.g. "model
        # unavailable, use this slug instead: ...") — the exception str() alone
        # only has the generic status text, which isn't enough to debug from logs.
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001 - body already consumed/unreadable, non-fatal
            detail = "<no body>"
        logger.warning("OpenRouter call failed (HTTP %s), falling back to deterministic response: %s", exc.code, detail)
        return None
    except Exception as exc:  # noqa: BLE001 - must never crash the request; log and fall back
        logger.warning("OpenRouter call failed, falling back to deterministic response: %s", exc)
        return None
