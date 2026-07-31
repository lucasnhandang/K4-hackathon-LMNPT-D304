"""Response generator for the Discord student assistant.

Generates Vietnamese responses from tool results with citations.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Response templates
# ---------------------------------------------------------------------------

GREETING_RESPONSES = [
    "Xin chào! Mình là trợ lý AI của AI20K Build Phase. Bạn cần hỗ trợ gì nha? 😊",
    "Chào bạn! Mình sẵn sàng giúp đỡ về deadline, lịch sự kiện, XP, team/mentor. Hỏi mình nha! 🚀",
    "Hi bạn! Mình là trợ lý AI, có thể giúp bạn tìm thông tin về khóa học. Bạn cần gì? ✨",
]

THANKS_RESPONSES = [
    "Không có gì! Nếu cần thêm thông tin thì cứ hỏi mình nha 😊",
    "Rất vui được giúp bạn! Chúc bạn học tốt nhé 🚀",
    "OK nha! Mình luôn sẵn sàng hỗ trợ khi bạn cần 💪",
]

HELP_RESPONSE = """Mình có thể giúp bạn:

📋 **Deadline**: Hạn nộp bài, thời gian còn lại
📅 **Lịch sự kiện**: Workshop, Office Hours, Mentoring
🏆 **XP & Rank**: Quy tắc tính XP, thứ hạng
👥 **Team & Mentor**: Thông tin team và mentor
📝 **Lệnh Discord**: Hướng dẫn sử dụng slash commands
🚧 **Gate**: Điều kiện checkpoint

Bạn cứ hỏi mình bất cứ điều gì về khóa học nha! 😊"""


def _format_deadline_response(data: dict[str, Any], citations: list[dict]) -> str:
    """Format deadline lookup response."""
    if not data:
        return "Không tìm thấy thông tin deadline phù hợp."

    deadline = data.get("deadline", "")
    assignment = data.get("assignment", "bài")
    module = data.get("module", "")
    channel = data.get("submission_channel", "")

    parts = []

    # Display assignment title
    display_title = str(assignment).replace("_", " ").upper()
    parts.append(f"📋 **Thông tin bài nộp ({display_title})**")

    if deadline:
        # Format datetime
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(deadline)
            parts.append(f"⏰ Deadline: **{dt.strftime('%H:%M ngày %d/%m/%Y')}** (GMT+7)")
        except (ValueError, TypeError):
            parts.append(f"⏰ Deadline: **{deadline}**")

    if data.get("frequency"):
        parts.append(f"📌 Tần suất nộp: **{data['frequency']}**")

    if data.get("mandatory"):
        parts.append("⚠️ Trạng thái: **Bắt buộc**")

    if module:
        parts.append(f"📚 Module: **{module.upper()}**")

    if channel:
        parts.append(f"📤 Nộp tại: **#{channel}**")

    # If attributes didn't provide a deadline string, include the quote from citation
    if citations and citations[0].get("quote"):
        parts.append(f"📝 Nội dung quy định: {citations[0]['quote']}")

    response = "\n".join(parts)

    # Add citation source at the end
    if citations:
        source = citations[0]
        response += f"\n\n📎 Nguồn: {source.get('title', '')} ({source.get('locator', '')})"

    return response


def _format_event_response(data: dict[str, Any], citations: list[dict]) -> str:
    """Format event lookup response."""
    if not data:
        return "Không tìm thấy thông tin sự kiện phù hợp."

    event_name = data.get("event_name", "")
    cohort = data.get("cohort", "")

    parts = []

    if event_name == "timeline":
        start = data.get("start_date", "")
        end = data.get("end_date", "")
        weeks = data.get("duration_weeks", "")
        demo = data.get("demo_day", "")
        parts.append(f"📅 **Timeline AI20K {cohort.upper()}**")
        parts.append(f"Từ **{start}** đến **{end}** ({weeks} tuần)")
        if demo:
            parts.append(f"🎯 Demo Day: **{demo}**")

    elif event_name == "weekly_rhythm":
        parts.append("📅 **Nhịp học hàng tuần:**")
        parts.append(f"• {data.get('workshops_per_week', 2)} Workshop")
        parts.append("• Office Hours")
        parts.append(f"• {data.get('mentoring_duty_per_week', 2)} buổi Mentoring Duty")
        parts.append("• Stand Up hàng ngày")

    elif event_name == "workshops":
        total = data.get("total", 16)
        main = data.get("total_main", 14)
        sup = data.get("total_supplementary", 2)
        parts.append(f"📚 **Tổng cộng {total} Workshop** ({main} chính + {sup} bổ sung)")

    elif event_name == "demo_day":
        date = data.get("date", "")
        deliverables = data.get("mandatory_deliverables", 10)
        parts.append(f"🎯 **Demo Day**: {date}")
        parts.append(f"📋 **{deliverables} deliverable bắt buộc**")

    else:
        parts.append(f"📅 **Sự kiện**: {event_name}")

    if citations:
        source = citations[0]
        parts.append(f"\n📎 Nguồn: {source.get('title', '')} ({source.get('locator', '')})")

    return "\n".join(parts)


def _format_xp_response(data: dict[str, Any], citations: list[dict]) -> str:
    """Format XP lookup response."""
    if not data:
        return "Không tìm thấy thông tin XP phù hợp."

    activity = data.get("activity", "")
    xp = data.get("xp", 0)
    command = data.get("command", "")
    levels = data.get("levels", {})

    parts = []

    if activity == "daily":
        parts.append(f"🏆 **Checkin hàng ngày ({command})**: +{xp} XP")
    elif activity == "weekly_submit":
        parts.append(f"🏆 **Nộp weekly assignment ({command})**: +{xp} XP")
    elif activity == "gate_pass":
        parts.append(f"🏆 **Vượt gate**: +{xp} XP")
    elif activity == "peer_review":
        weekly_cap = data.get("weekly_cap", 3)
        parts.append(f"🏆 **Peer review**: +{xp} XP/lần (tối đa {weekly_cap} lượt/tuần)")
    else:
        parts.append(f"🏆 **{activity}**: +{xp} XP")

    if levels:
        parts.append("\n📊 **Bảng cấp độ:**")
        for level, range_str in levels.items():
            parts.append(f"• {level}: {range_str} XP")

    if command:
        parts.append(f"\n💡 Dùng `{command}` để thực hiện")

    if citations:
        source = citations[0]
        parts.append(f"\n📎 Nguồn: {source.get('title', '')} ({source.get('locator', '')})")

    return "\n".join(parts)


def _format_gate_response(data: dict[str, Any], citations: list[dict]) -> str:
    """Format gate lookup response."""
    if not data:
        return "Không tìm thấy thông tin gate phù hợp."

    gate_name = data.get("gate_name", "").upper()
    requirements = data.get("requirements", [])

    parts = [f"🚧 **{gate_name}**"]

    if requirements:
        parts.append("Yêu cầu:")
        for req in requirements:
            req_display = req.replace("_", " ").title()
            parts.append(f"• {req_display}")

    if citations:
        source = citations[0]
        parts.append(f"\n📎 Nguồn: {source.get('title', '')} ({source.get('locator', '')})")

    return "\n".join(parts)


def _format_slash_command_response(data: dict[str, Any], citations: list[dict]) -> str:
    """Format slash command lookup response."""
    if not data:
        return "Không tìm thấy thông tin lệnh phù hợp."

    command = data.get("command", "")
    usage = data.get("usage", "")
    description = data.get("description", "")

    parts = [f"💻 **{command}**"]
    if description:
        parts.append(f"Mô tả: {description}")
    if usage:
        parts.append(f"Cách dùng: `{usage}`")

    if citations:
        source = citations[0]
        parts.append(f"\n📎 Nguồn: {source.get('title', '')} ({source.get('locator', '')})")

    return "\n".join(parts)


def _format_team_mentor_response(data: dict[str, Any], citations: list[dict]) -> str:
    """Format team/mentor lookup response."""
    if not data:
        return "Không tìm thấy thông tin team/mentor phù hợp."

    parts = []

    # Handle naming convention
    if "naming_convention" in data:
        parts.append("👥 **Quy tắc đặt tên team:**")
        for key, value in data["naming_convention"].items():
            parts.append(f"• {key}: `{value}`")

    # Handle support system
    elif "support_type" in data:
        parts.append("🛠️ **Hệ thống hỗ trợ:**")
        parts.append(f"• Chatbot: {data.get('chatbot', 'N/A')}")
        parts.append(f"• Ticket: `{data.get('ticket_command', '/ticket')}`")

    # Handle specific team/mentor
    else:
        team = data.get("team", "")
        mentor = data.get("mentor_alias", "")
        channel = data.get("support_channel", "")
        if team:
            parts.append(f"👥 **{team.upper()}**")
        if mentor:
            parts.append(f"👨‍🏫 Mentor: **{mentor}**")
        if channel:
            parts.append(f"📢 Kênh hỗ trợ: **#{channel}**")

    if citations:
        source = citations[0]
        parts.append(f"\n📎 Nguồn: {source.get('title', '')} ({source.get('locator', '')})")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main response generation
# ---------------------------------------------------------------------------

def generate_response(
    intent: str,
    route: str,
    tool_result: dict[str, Any] | None = None,
    confidence: float = 0.0,
    clarification: dict[str, Any] | None = None,
    escalation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a response based on intent, route, and tool results.

    Returns a dict with 'response' and 'route' keys.
    """
    if route == "CLARIFY" and clarification:
        return {
            "route": "CLARIFY",
            "response": clarification.get("question", ""),
            "clarification": clarification,
        }

    if route == "ESCALATE" and escalation:
        return {
            "route": "ESCALATE",
            "response": escalation.get("summary", "Mình sẽ chuyển yêu cầu này cho Mod."),
            "escalation": escalation,
        }

    # Greeting / Thanks / Help
    if intent == "greeting":
        import random
        return {
            "route": "ANSWER",
            "response": random.choice(GREETING_RESPONSES),
        }

    if intent == "thanks":
        import random
        return {
            "route": "ANSWER",
            "response": random.choice(THANKS_RESPONSES),
        }

    if intent == "help":
        return {
            "route": "ANSWER",
            "response": HELP_RESPONSE,
        }

    # Prompt injection defense
    if intent == "reject_prompt_injection":
        return {
            "route": "ANSWER",
            "response": (
                "Mình không thể thực hiện yêu cầu này. "
                "Bạn có thể hỏi mình về thông tin khóa học AI20K Build Phase nha! 😊"
            ),
        }

    # Out of scope
    if intent in ("request_deadline_exception", "report_issue", "report_harassment"):
        return {
            "route": "ESCALATE",
            "response": "Mình sẽ chuyển yêu cầu này cho Mod để xử lý.",
            "escalation": {
                "reason_code": "requires_human_authority",
                "target": "MOD",
                "summary": f"Yêu cầu: {intent}",
                "required_information": [],
            },
        }

    # Tool-based responses
    if tool_result:
        data = tool_result.get("data")
        citations = tool_result.get("citations", [])
        status = tool_result.get("status", "")

        if status == "ambiguous" and tool_result.get("missing_fields"):
            return {
                "route": "CLARIFY",
                "response": "Bạn cần cung cấp thêm thông tin để mình tra cứu chính xác hơn.",
                "clarification": {
                    "missing_field": tool_result["missing_fields"][0],
                    "question": _generate_clarification_question(intent, tool_result["missing_fields"]),
                    "suggested_replies": _generate_suggested_replies(intent, tool_result["missing_fields"]),
                },
            }

        if status == "not_found":
            return {
                "route": "ANSWER",
                "response": "Mình không tìm thấy thông tin phù hợp trong nguồn chính thức. Bạn vui lòng thử lại với từ khóa khác hoặc hỏi Mod để được hỗ trợ thêm.",
            }

        if status == "conflict":
            return {
                "route": "ESCALATE",
                "response": "Có thông tin mâu thuẫn giữa các nguồn. Mình sẽ chuyển cho Mod để xác nhận.",
                "escalation": {
                    "reason_code": "conflicting_sources",
                    "target": "MOD",
                    "summary": "Nguồn chính thức có thông tin mâu thuẫn.",
                    "required_information": [],
                },
            }

        if data:
            # Format based on intent
            if intent == "ask_deadline":
                response_text = _format_deadline_response(data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}, citations)
            elif intent == "ask_event_schedule":
                response_text = _format_event_response(data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}, citations)
            elif intent == "ask_xp":
                response_text = _format_xp_response(data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}, citations)
            elif intent == "ask_gate":
                response_text = _format_gate_response(data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}, citations)
            elif intent == "ask_slash_command":
                response_text = _format_slash_command_response(data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}, citations)
            elif intent == "ask_team_mentor":
                response_text = _format_team_mentor_response(data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}, citations)
            elif intent == "ask_exam_slot":
                response_text = _format_deadline_response(data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}, citations)
            else:
                # Generic search result
                if isinstance(data, list):
                    response_text = f"Tìm thấy {len(data)} kết quả phù hợp."
                else:
                    response_text = "Đã tìm thấy thông tin."

            return {
                "route": "ANSWER",
                "response": response_text,
            }

    # Fallback
    return {
        "route": "ANSWER",
        "response": "Mình chưa hiểu rõ câu hỏi. Bạn có thể hỏi lại hoặc thử từ khóa khác nha! 😊",
    }


def _generate_clarification_question(intent: str, missing_fields: list[str]) -> str:
    """Generate a clarification question based on missing fields."""
    field_questions = {
        "assignment": "Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...)",
        "module": "Bạn đang học module nào?",
        "event_name": "Bạn muốn biết về sự kiện nào? (Workshop, Office Hours, Mentoring...)",
        "gate_name": "Bạn muốn biết về gate nào? (CP1, CP2, CP3...)",
        "exam_name": "Bạn muốn biết về kỳ thi nào?",
        "team": "Bạn thuộc team nào?",
        "activity": "Bạn muốn biết XP của hoạt động nào?",
        "command": "Bạn muốn biết về lệnh nào?",
        "query": "Bạn có thể nói rõ hơn về vấn đề cần hỗ trợ không?",
    }

    for field in missing_fields:
        if field in field_questions:
            return field_questions[field]

    return "Bạn có thể cung cấp thêm thông tin được không?"


def _generate_suggested_replies(intent: str, missing_fields: list[str]) -> list[str]:
    """Generate suggested replies based on intent and missing fields."""
    suggestions = {
        "ask_deadline": {
            "assignment": ["Weekly Assignment", "AI Log", "Demo Day deliverables"],
        },
        "ask_event_schedule": {
            "event_name": ["Workshop", "Office Hours", "Mentoring Duty", "Demo Day"],
        },
        "ask_gate": {
            "gate_name": ["CP1", "CP2", "CP3", "Final Gate"],
        },
        "ask_xp": {
            "activity": ["Daily checkin", "Weekly submit", "Peer review", "Gate pass"],
        },
        "ask_slash_command": {
            "command": ["/daily", "/weekly", "/exam", "/gate", "/myteam", "/rank", "/ticket", "/ask"],
        },
    }

    if intent in suggestions:
        for field in missing_fields:
            if field in suggestions[intent]:
                return suggestions[intent][field]

    return []
