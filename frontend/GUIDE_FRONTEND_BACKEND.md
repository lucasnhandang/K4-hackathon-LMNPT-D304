# Hướng Dẫn Cấu Hình Frontend NiceGUI & Tích Hợp Backend

Tài liệu này hướng dẫn chi tiết cho các thành viên trong nhóm về cách thiết lập môi trường chạy Frontend NiceGUI và cách đấu nối ứng dụng với Backend API (FastAPI / Express / Flask hoặc LLM Service).

---

## 📌 1. Tổng Quan Cấu Trúc Frontend

```text
frontend/
├── main.py                # Giao diện chính NiceGUI (Layout Discord, Chat View, Options Grid, Tracepath)
├── ai_router.py           # Mô-đun phân loại Intent & Nguồn căn cứ (Local AI Router / API Client)
├── custom_styles.py       # Định nghĩa CSS Token, font Sora/Inter & phong cách Discord Dark Mode
├── .env.example           # File mẫu cấu hình biến môi trường
└── GUIDE_FRONTEND_BACKEND.md # Tài liệu hướng dẫn này
```

---

## 🚀 2. Cài Đặt Môi Trường & Chạy Frontend

### Bước 2.1: Cài đặt thư viện phụ thuộc
Đảm bảo đã kích hoạt môi trường ảo Python (`.venv`) và cài đặt các package:

```bash
cd frontend

# Kích hoạt venv (Windows)
.\.venv\Scripts\Activate

# Cài đặt NiceGUI và thư viện hỗ trợ gọi API
pip install nicegui python-dotenv httpx pydantic
```

### Bước 2.2: Khởi tạo tệp cấu hình `.env`
Tạo tệp `.env` trong thư mục `frontend/` (hoặc thư mục gốc dự án):

```env
PORT=8080
BACKEND_URL=http://localhost:8000/api/v1/chat
USE_LOCAL_MOCK=false
OPENAI_API_KEY=your_openai_api_key_here
```

### Bước 2.3: Chạy ứng dụng Frontend
```bash
# Chạy trực tiếp
python main.py

# Hoặc chạy từ thư mục codebase để kiểm thử nộp bài
python ../codebase/app.py
```
Ứng dụng sẽ mở tại địa chỉ: **`http://localhost:8080`**

---

## 🔗 3. Cách Kết Nối Frontend Với Backend API

Khi Backend chạy độc lập tại `http://localhost:8000`, hàm `call_backend_api_async` trong `ai_router.py` sẽ tự động đóng gói Request Input Payload và chuyển đổi Backend Output JSON sang giao diện Discord kèm **AI Tracepath & Tools Execution**.

---

## 📦 4. Mẫu Định Dạng Dữ Liệu Trao Đổi (INPUT & OUTPUT TEMPLATE)

### 📥 4.1. Request Template (Frontend ➔ Backend)

Backend nhận dữ liệu JSON đầu vào từ Frontend theo cấu trúc dưới đây:

```json
{
  "metadata": {
    "message_id": "msg_001",
    "timestamp": "2026-07-30T14:30:00Z",
    "user_id": "student_123",
    "session_id": "discord_session_001",
    "channel_id": "support_python"
  },

  "message": {
    "type": "text",
    "content": "Deadline bao nhiêu z?"
  },

  "conversation": {
    "history": [
      {
        "role": "user",
        "content": "Em đang làm project cuối khóa."
      },
      {
        "role": "assistant",
        "content": "Bạn đang học module nào?"
      }
    ],
    "current_step": "clarification"
  },

  "learning_context": {
    "course": "Python Foundation",
    "module": "Project",
    "lesson": null,
    "assignment": null
  },

  "runtime": {
    "language": "vi",
    "platform": "discord"
  }
}
```

---

### 📤 4.2. Response Template với TRACEPATH (Backend ➔ Frontend)

Backend cần trả về kết quả JSON bao gồm trường `tracepath` để hiển thị các công cụ đã sử dụng (`tools_used`), thời gian xử lý (`latency_ms`), độ tin cậy (`confidence`) và danh sách các bước (`steps`):

```json
{
  "status": "need_clarification",

  "intent": "ask_deadline",

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

  "handoff": false,

  "tracepath": {
    "latency_ms": 124,
    "confidence": 0.71,
    "intent": "ask_deadline",
    "tools_used": [
      { "name": "Intent Classifier", "icon": "🔍", "status": "success" },
      { "name": "VectorDB RAG Search", "icon": "📚", "status": "found" },
      { "name": "Context Disambiguator", "icon": "❓", "status": "need_followup" }
    ],
    "steps": [
      "Phân tích ý định câu hỏi: ask_deadline (Confidence: 71%)",
      "Phát hiện ngữ cảnh mơ hồ ➔ Tự động kích hoạt câu hỏi làm rõ",
      "Tạo danh sách lựa chọn follow_up cho học viên"
    ]
  }
}
```

---

### 🎯 4.3. Bảng Ánh Xạ Trạng Thái Backend ➔ Frontend UI

| Trạng thái Backend (`status` / `action`) | `handoff` | Giao diện Frontend tự động hiển thị |
|---|---|---|
| `status: "need_clarification"` (`action: "ask_follow_up"`) | `false` | Thẻ **Warning Embed** (vàng) + Tự động tạo Nút bấm từ mảng `follow_up` + **AI Tracepath Box** |
| `status: "resolved"` (`action: "direct_answer"`) | `false` | Thẻ **Success Embed** (xanh) + Nguồn `citations` + Nút phản hồi + **AI Tracepath Box** |
| `status: "escalated"` / `action: "escalate_mod"` | `true` | Thẻ **Escalate Embed** (đỏ) + Auto tag **`@Mod / @Mentor`** + **AI Tracepath Box** |
| `status: "out_of_scope"` / `action: "reject"` | `false` | Thẻ **Muted Embed** (xám) + Từ chối lịch sự, **KHÔNG tag Mod** + **AI Tracepath Box** |

---

## ⚡ 5. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **Lỗi `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8080)`**:
   - **Nguyên nhân**: Đã có 1 tiến trình python khác đang chiếm cổng 8080.
   - **Xử lý**: Tắt tiến trình python đang chạy bằng `Ctrl + C` hoặc đổi `PORT=8081` trong file `.env`.

2. **Backend chưa khởi chạy**:
   - Frontend có sẵn cơ chế **Fallback**. Nếu không gọi được Backend API, ứng dụng tự động dùng bộ Local AI Router để buổi Demo chạy liên tục không đứt đoạn.
