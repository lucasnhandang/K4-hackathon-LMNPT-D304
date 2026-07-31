# ai_router.py
"""
AI Intent Classifier and Ground Truth Engine for Discord Student Assistant.
Supports 4 distinct Taxonomy categories + Tracepath Execution Details:
1. AMBIGUOUS (Need clarification with buttons)
2. DIRECT_ANSWER (Specific question backed by official course ground truth)
3. NO_SOURCE_ESCALATE (Escalate to @Mod / @Mentor when information is missing)
4. OUT_OF_SCOPE (Polite rejection, no Mod escalation)
"""

import os
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

# Configuration for external Backend API
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api/v1/chat")
USE_LOCAL_MOCK = os.environ.get("USE_LOCAL_MOCK", "false").lower() == "true"
BACKEND_TIMEOUT_SECONDS = 40.0

# Official Ground Truth Knowledge Base
KNOWLEDGE_BASE = {
    "weekly_report": {
        "title": "Weekly Report",
        "deadline": "12:00 trưa Thứ 4 (ngày 30/07)",
        "source": "Thông báo Weekly Report — cập nhật ngày 28/07/2026 bởi Ban Chăm sóc Học viên.",
        "quote": "Deadline nộp weekly report là 12h00 trưa trước các buổi mentor duty. Các buổi mentor duty cố định hàng tuần diễn ra vào tối thứ 4 và thứ 7."
    },
    "mentor_duty": {
        "title": "Mentor Duty",
        "schedule": "Tối Thứ 4 & Tối Thứ 7 hàng tuần (19:30 - 21:30)",
        "source": "Quy chế Mentor Duty — Khoá AI Thực Chiến K4.",
        "quote": "Học viên đăng ký Mentor Duty trước 12h00 trưa cùng ngày để BTC xếp phòng support 1-1."
    },
    "general": {
        "title": "Nội quy khoá học",
        "source": "Sổ tay Học viên K4 AI Thực Chiến.",
        "quote": "Mọi câu hỏi thắc mắc bài tập được hỗ trợ tại kênh #gỡ-vướng-học-tập."
    }
}

def transform_backend_response_to_ui(backend_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms standard Backend Output JSON into Frontend Discord UI format with Tracepath metadata.
    """
    status = backend_data.get("status", "")
    action = backend_data.get("action", "")
    response_msg = backend_data.get("response", "")
    follow_up = backend_data.get("follow_up", [])
    citations = backend_data.get("citations", [])
    handoff = backend_data.get("handoff", False)
    tracepath = backend_data.get("tracepath", None)
    
    # Generate fallback tracepath if not provided by backend
    if not tracepath:
        intent = backend_data.get("intent", "general_query")
        conf = backend_data.get("confidence", 0.95)
        tracepath = {
            "latency_ms": 115,
            "confidence": conf,
            "intent": intent,
            "tools_used": [
                {"name": "Intent Classifier", "icon": "🔍", "status": "success"},
                {"name": "RAG Knowledge Retrieval", "icon": "📚", "status": "success"},
                {"name": "Taxonomy Policy Engine", "icon": "⚡", "status": "success"}
            ],
            "steps": [
                f"Phân loại Intent: {intent} ({int(conf*100)}% confidence)",
                "Truy xuất nguồn chính thức: data/vlearn-pack/knowledge_base",
                "Kiểm tra 4 lớp chỗ khó: Phân luồng xử lý tự động"
            ]
        }

    # 1. NEED CLARIFICATION / ASK FOLLOW UP
    if status == "need_clarification" or action == "ask_follow_up":
        opts = []
        for item in follow_up:
            opts.append({"label": str(item), "value": f"CAT_{str(item).upper()}", "class": "disc-btn"})
            
        return {
            "type": "AMBIGUOUS",
            "message": response_msg,
            "embed_type": "warning-embed",
            "title": "Chọn nội dung bạn cần kiểm tra",
            "options": opts,
            "tracepath": tracepath
        }
        
    # 2. ESCALATED / HANDOFF TO MOD
    elif status == "escalated" or handoff or action == "escalate_mod":
        return {
            "type": "NO_SOURCE_ESCALATE",
            "message": response_msg,
            "embed_type": "escalate-embed",
            "title": "Cần Mentor/Mod xác nhận",
            "escalate_tag": "@Mod / @Mentor",
            "escalate_detail": (
                "Đây là đề xuất chuyển tiếp; hệ thống chưa tự động gửi câu hỏi."
            ),
            "options": [],
            "tracepath": tracepath
        }
        
    # 3. OUT OF SCOPE / REJECT
    elif status == "out_of_scope" or action == "reject":
        return {
            "type": "OUT_OF_SCOPE",
            "message": response_msg,
            "embed_type": "muted-embed",
            "source_info": "Bot từ chối lịch sự và KHÔNG tag Mod.",
            "options": [],
            "tracepath": tracepath
        }
        
    # 4. RESOLVED / DIRECT ANSWER (Default)
    else:
        source_str = "Căn cứ tài liệu chính thức khóa học."
        quote_str = ""
        if citations and len(citations) > 0:
            c0 = citations[0]
            if isinstance(c0, dict):
                source_str = c0.get("source", source_str)
                quote_str = c0.get("quote", "")
            else:
                source_str = str(c0)

        return {
            "type": "DIRECT_ANSWER",
            "message": response_msg,
            "embed_type": "success-embed",
            "source_info": source_str,
            "quote": quote_str,
            "options": [
                {"label": "Đã giải quyết", "value": "FEEDBACK_RESOLVED", "class": "disc-btn-success"},
                {"label": "✕ Bot hiểu sai", "value": "FEEDBACK_WRONG", "class": "disc-btn-danger"},
                {"label": "Xem nguồn", "value": "VIEW_SOURCE", "class": "disc-btn"}
            ],
            "tracepath": tracepath
        }

async def call_backend_api_async(
    user_message: str,
    history: List[Dict[str, str]] = None,
    session_id: str | None = None,
) -> Dict[str, Any]:
    """
    Sends request to Backend API using standard Input Payload Template and transforms response.
    """
    if USE_LOCAL_MOCK:
        return classify_and_route(user_message)

    payload = {
        "metadata": {
            "message_id": f"msg_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": "student_123",
            # The UI supplies a stable ID per chat. Other callers receive an
            # isolated one-shot session instead of sharing clarification state.
            "session_id": session_id or f"discord_session_{uuid4().hex}",
            "channel_id": "gỡ-vướng-học-tập"
        },
        "message": {
            "type": "text",
            "content": user_message
        },
        "conversation": {
            "history": history or [],
            "current_step": "user_query"
        },
        "learning_context": {
            "course": "AI Thực Chiến K4",
            "cohort": "k4",
            "module": "Project",
            "lesson": None,
            "assignment": None
        },
        "runtime": {
            "language": "vi",
            "platform": "discord"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=BACKEND_TIMEOUT_SECONDS) as client:
            response = await client.post(BACKEND_URL, json=payload)
            if response.status_code == 200:
                backend_data = response.json()
                return transform_backend_response_to_ui(backend_data)
            else:
                return {
                    "type": "SYSTEM_ERROR",
                    "message": (
                        "Không thể nhận câu trả lời từ chatbot vì Backend trả về lỗi "
                        f"HTTP {response.status_code}. Vui lòng thử lại sau."
                    ),
                    "embed_type": "escalate-embed",
                    "title": "Lỗi kết nối Backend",
                    "options": [],
                    "tracepath": {
                        "latency_ms": 0,
                        "confidence": 0.0,
                        "intent": "backend_error",
                        "llm_called": False,
                        "model": None,
                        "usage": {},
                        "tools_used": [
                            {"name": "Backend API", "icon": "⚠️", "status": "error"}
                        ],
                        "steps": [
                            f"Backend trả về HTTP {response.status_code}; không dùng Local AI Router."
                        ],
                    },
                }
    except Exception as e:
        error_name = type(e).__name__
        print(f"[Error] Không thể kết nối Backend API: {error_name}: {e}")
        return {
            "type": "SYSTEM_ERROR",
            "message": (
                "Không thể kết nối tới Backend chatbot. "
                "Hệ thống không chuyển sang dữ liệu mock; vui lòng kiểm tra Backend rồi thử lại."
            ),
            "embed_type": "escalate-embed",
            "title": "Backend không khả dụng",
            "options": [],
            "tracepath": {
                "latency_ms": 0,
                "confidence": 0.0,
                "intent": "backend_unavailable",
                "llm_called": False,
                "model": None,
                "usage": {},
                "tools_used": [
                    {"name": "Backend API", "icon": "⚠️", "status": "error"}
                ],
                "steps": [
                    f"Kết nối Backend thất bại ({error_name}); không dùng Local AI Router."
                ],
            },
        }

def classify_and_route(user_message: str, context_state: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Classifies the user message into one of 4 intent categories and returns structured UI data with Tracepath.
    """
    msg_lower = user_message.strip().lower()
    
    # 1. OUT OF SCOPE / VIOLATION
    out_of_scope_keywords = ["bom", "vũ khí", "thời tiết", "tin tức", "phi pháp", "chế tạo", "ngoài phạm vi", "vi phạm", "game", "xem phim"]
    if any(kw in msg_lower for kw in out_of_scope_keywords):
        mock_output = {
            "status": "out_of_scope",
            "intent": "out_of_scope_violation",
            "confidence": 0.99,
            "action": "reject",
            "response": "Tôi là trợ lý AI hỗ trợ khóa học AI Thực Chiến K4. Hiện tại tôi không có thông tin hoặc không thể hỗ trợ giải đáp về chủ đề này.",
            "follow_up": [],
            "citations": [],
            "handoff": False,
            "tracepath": {
                "latency_ms": 42,
                "confidence": 0.99,
                "intent": "out_of_scope_violation",
                "tools_used": [
                    {"name": "Safety Guardrail Tool", "icon": "🛡️", "status": "blocked"},
                    {"name": "Policy Auditor", "icon": "⚡", "status": "rejected"}
                ],
                "steps": [
                    "Phân tích Safety: Phát hiện từ khóa nằm ngoài phạm vi khóa học",
                    "Đánh giá rủi ro (Taxonomy Class ③): Từ chối trả lời, bảo vệ tài nguyên Mod"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
    
    # 2. NO SOURCE -> ESCALATE TO MOD
    escalate_keywords = ["nộp bù", "nộp muộn", "không có căn cứ", "xin gia hạn", "đặc cách", "xin nghỉ", "bảo lưu"]
    if any(kw in msg_lower for kw in escalate_keywords):
        mock_output = {
            "status": "escalated",
            "intent": "ask_exception_policy",
            "confidence": 0.88,
            "action": "escalate_mod",
            "response": "Mình chưa tìm thấy thông tin chính thức về quy định này trong tài liệu khóa học.",
            "follow_up": [],
            "citations": [],
            "handoff": True,
            "tracepath": {
                "latency_ms": 138,
                "confidence": 0.88,
                "intent": "ask_exception_policy",
                "tools_used": [
                    {"name": "Intent Classifier", "icon": "🔍", "status": "success"},
                    {"name": "VectorDB RAG Search", "icon": "📚", "status": "no_match"},
                    {"name": "Escalation Router", "icon": "🚨", "status": "escalated"}
                ],
                "steps": [
                    "Phân loại Intent: ask_exception_policy",
                    "Tìm kiếm RAG trong tri thức khóa học: Không tìm thấy căn cứ chính thức (No Ground Truth)",
                    "Áp dụng Quy chế Taxonomy Class ①: Chuyển tự động cho @Mod/@Mentor"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
    
    # 3. DIRECT SPECIFIC ANSWER
    if ("weekly report" in msg_lower or "weekly" in msg_lower) and ("tuần này" in msg_lower or "khi nào" in msg_lower or "giờ" in msg_lower or "thời gian" in msg_lower or "rõ" in msg_lower or "bao giờ" in msg_lower or "hạn" in msg_lower):
        kb = KNOWLEDGE_BASE["weekly_report"]
        mock_output = {
            "status": "resolved",
            "intent": "ask_deadline_weekly",
            "confidence": 0.98,
            "action": "direct_answer",
            "response": f"Deadline **Weekly Report tuần này** là **{kb['deadline']}** trước buổi Mentor Duty.",
            "follow_up": [],
            "citations": [{"source": f"Nguồn căn cứ: {kb['source']}", "quote": kb['quote']}],
            "handoff": False,
            "tracepath": {
                "latency_ms": 124,
                "confidence": 0.98,
                "intent": "ask_deadline_weekly",
                "tools_used": [
                    {"name": "Intent Classifier", "icon": "🔍", "status": "success"},
                    {"name": "VectorDB RAG Search", "icon": "📚", "status": "found"},
                    {"name": "Citation Verifier", "icon": "📄", "status": "verified"}
                ],
                "steps": [
                    "Phân loại câu hỏi: ask_deadline_weekly (Độ tin cậy 98%)",
                    "Truy xuất RAG: vlearn-pack/weekly_rules.md [Đoạn 14]",
                    "Xác minh nguồn căn cứ chính thức: Thông báo Weekly Report K4"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
        
    if "mentor duty" in msg_lower or "mentor" in msg_lower:
        kb = KNOWLEDGE_BASE["mentor_duty"]
        mock_output = {
            "status": "resolved",
            "intent": "ask_schedule_mentor",
            "confidence": 0.96,
            "action": "direct_answer",
            "response": f"Lịch **Mentor Duty cố định** diễn ra vào **{kb['schedule']}**.",
            "follow_up": [],
            "citations": [{"source": f"Nguồn căn cứ: {kb['source']}", "quote": kb['quote']}],
            "handoff": False,
            "tracepath": {
                "latency_ms": 105,
                "confidence": 0.96,
                "intent": "ask_schedule_mentor",
                "tools_used": [
                    {"name": "Intent Classifier", "icon": "🔍", "status": "success"},
                    {"name": "Schedule Lookup Engine", "icon": "📅", "status": "found"}
                ],
                "steps": [
                    "Nhận diện ý định: Lịch đăng ký Mentor Duty",
                    "Truy vấn Quy chế Mentor Duty K4 AI Thực Chiến"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)

    # 4. AMBIGUOUS / VAGUE (Default fallback matching exact user provided template format!)
    mock_output = {
        "status": "need_clarification",
        "intent": "ask_deadline_vague",
        "confidence": 0.71,
        "action": "ask_follow_up",
        "response": "Bạn đang hỏi deadline của bài tập hay project nào?",
        "follow_up": [
            "Project cuối khóa",
            "Weekly Assignment",
            "Quiz",
            "Khác"
        ],
        "citations": [],
        "handoff": False,
        "tracepath": {
            "latency_ms": 89,
            "confidence": 0.71,
            "intent": "ask_deadline_vague",
            "tools_used": [
                {"name": "Intent Classifier", "icon": "🔍", "status": "ambiguous"},
                {"name": "Context Disambiguator", "icon": "❓", "status": "need_followup"}
            ],
            "steps": [
                "Phân tích ngữ cảnh: Câu hỏi ngắn/mơ hồ (Độ tin cậy 71%)",
                "Kích hoạt Taxonomy Class ②: Chủ động đưa ra các nút bấm làm rõ"
            ]
        }
    }
    return transform_backend_response_to_ui(mock_output)

def handle_option_selection(option_value: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Handles user clicks on interactive choice buttons with Tracepath updates.
    """
    val_upper = option_value.upper()
    if "PROJECT" in val_upper or "CAT_WEEKLY" in val_upper:
        mock_output = {
            "status": "need_clarification",
            "intent": "ask_deadline_project",
            "confidence": 0.85,
            "action": "ask_follow_up",
            "response": "Bạn đang muốn kiểm tra Weekly report của **tuần nào**?",
            "follow_up": ["Tuần hiện tại", "Tuần trước", "Tuần khác"],
            "citations": [],
            "handoff": False,
            "tracepath": {
                "latency_ms": 65,
                "confidence": 0.85,
                "intent": "ask_deadline_project",
                "tools_used": [
                    {"name": "Follow-up Handler", "icon": "🔘", "status": "step_2"},
                    {"name": "Time Disambiguator", "icon": "📅", "status": "need_time"}
                ],
                "steps": [
                    "Xử lý nút lựa chọn: Project / Weekly Report",
                    "Yêu cầu làm rõ bước 2: Xác định tuần cụ thể"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
        
    elif "TUẦN HIỆN TẠI" in val_upper or "TIME_CURRENT" in val_upper or "WEEKLY ASSIGNMENT" in val_upper:
        kb = KNOWLEDGE_BASE["weekly_report"]
        mock_output = {
            "status": "resolved",
            "intent": "ask_deadline",
            "confidence": 0.99,
            "action": "direct_answer",
            "response": f"Deadline **Weekly Report tuần này** là **{kb['deadline']}** trước buổi Mentor Duty.",
            "follow_up": [],
            "citations": [{"source": f"Nguồn căn cứ: {kb['source']}", "quote": kb['quote']}],
            "handoff": False,
            "tracepath": {
                "latency_ms": 92,
                "confidence": 0.99,
                "intent": "ask_deadline",
                "tools_used": [
                    {"name": "Context Disambiguator", "icon": "🎯", "status": "resolved"},
                    {"name": "VectorDB RAG Search", "icon": "📚", "status": "found"}
                ],
                "steps": [
                    "Hoàn tất làm rõ ngữ cảnh: Weekly Report Tuần Hiện Tại",
                    "Trích xuất nguồn chính thức: Thông báo Weekly Report"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
        
    elif "TUẦN TRƯỚC" in val_upper or "QUIZ" in val_upper or "KHÁC" in val_upper or "TIME_LAST" in val_upper:
        mock_output = {
            "status": "escalated",
            "intent": "ask_exception_deadline",
            "confidence": 0.90,
            "action": "escalate_mod",
            "response": "Mình chưa tìm thấy thông tin chính thức về deadline cho lựa chọn này trong tài liệu khóa học.",
            "follow_up": [],
            "citations": [],
            "handoff": True,
            "tracepath": {
                "latency_ms": 110,
                "confidence": 0.90,
                "intent": "ask_exception_deadline",
                "tools_used": [
                    {"name": "Knowledge Verifier", "icon": "📚", "status": "not_found"},
                    {"name": "Escalation Router", "icon": "🚨", "status": "escalated"}
                ],
                "steps": [
                    "Tra cứu quy định nộp bổ sung: Không có căn cứ chính thức",
                    "Chuyển tự động cho @Mod/@Mentor"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
        
    elif option_value == "FEEDBACK_RESOLVED":
        return {
            "type": "CHAT_REPLY",
            "message": "Tuyệt vời! Chúc bạn hoàn thành tốt bài tập tuần này nhé 🚀",
            "options": []
        }
    elif option_value == "FEEDBACK_WRONG":
        mock_output = {
            "status": "need_clarification",
            "intent": "feedback_wrong",
            "confidence": 0.90,
            "action": "ask_follow_up",
            "response": "Thành thật xin lỗi bạn! **Mình đã hiểu sai phần nào?**",
            "follow_up": ["↺ Chọn lại loại deadline", "✍ Nhập thêm ngữ cảnh", "⚠️ Yêu cầu chuyển Mod ngay"],
            "citations": [],
            "handoff": False,
            "tracepath": {
                "latency_ms": 45,
                "confidence": 0.90,
                "intent": "feedback_wrong",
                "tools_used": [
                    {"name": "Feedback Evaluator", "icon": "🔄", "status": "retry_prompt"}
                ],
                "steps": [
                    "Ghi nhận phản hồi: Học viên báo sai",
                    "Đưa ra các tùy chọn khắc phục"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
        
    elif "MOD" in val_upper or option_value == "FORCE_ESCALATE":
        mock_output = {
            "status": "escalated",
            "intent": "user_escalation_request",
            "confidence": 1.0,
            "action": "escalate_mod",
            "response": "Đã nhận yêu cầu trực tiếp từ học viên.",
            "follow_up": [],
            "citations": [],
            "handoff": True,
            "tracepath": {
                "latency_ms": 30,
                "confidence": 1.0,
                "intent": "user_escalation_request",
                "tools_used": [
                    {"name": "Manual Escalation Override", "icon": "🚨", "status": "forced"}
                ],
                "steps": [
                    "Yêu cầu can thiệp thủ công từ học viên",
                    "Tag trực tiếp @Mod/@Mentor"
                ]
            }
        }
        return transform_backend_response_to_ui(mock_output)
        
    return {
        "type": "CHAT_REPLY",
        "message": "Cảm ơn bạn đã phản hồi!",
        "options": []
    }
