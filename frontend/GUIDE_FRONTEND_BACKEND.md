# Hướng Dẫn Cấu Hình Frontend NiceGUI & Tích Hợp Backend

Tài liệu này hướng dẫn cách chạy Frontend NiceGUI với chatbot nằm trong
`codebase/backend/chatbot_tools`.

---

## 📌 1. Tổng Quan Cấu Trúc Frontend

```text
frontend/
├── main.py                # Giao diện chính NiceGUI (Layout Discord, Chat View, Options Grid, Tracepath)
├── ai_router.py           # Adapter gọi trực tiếp codebase chatbot và ánh xạ dữ liệu sang UI
├── custom_styles.py       # Định nghĩa CSS Token, font Sora/Inter & phong cách Discord Dark Mode
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

# Cài đặt NiceGUI
pip install -r requirements.txt
```

Frontend được khóa ở NiceGUI `3.14.0` để CSS layer và DOM do Quasar sinh ra
không thay đổi ngoài kiểm soát giữa các lần cài.

### Bước 2.2: Cấu hình

Frontend không cần API key hay backend HTTP riêng. Có thể đặt `PORT` để đổi cổng
NiceGUI; mặc định là `8080`.

### Bước 2.3: Chạy ứng dụng Frontend
```bash
# Chạy trực tiếp
python main.py

# Hoặc chạy từ thư mục codebase để kiểm thử nộp bài
python ../codebase/app.py
```
Ứng dụng sẽ mở tại địa chỉ: **`http://localhost:8080`**

Khi người dùng gửi tin nhắn, console chạy NiceGUI sẽ hiện log backend dạng:

```text
INFO | chatbot_tools.orchestrator | BE chat received: trace_id=... message_length=...
INFO | chatbot_tools.orchestrator | BE intent classified: trace_id=... intent=...
INFO | chatbot_tools.orchestrator | BE chat completed: trace_id=... route=ANSWER ...
```

Log mặc định ở mức `INFO`. Có thể đặt biến môi trường `LOG_LEVEL` để đổi mức log.
Nội dung chat và giá trị slot không được in nguyên văn; log chỉ chứa metadata phục
vụ chẩn đoán để tránh lộ dữ liệu người dùng.

---

## 🔗 3. Cách Frontend Kết Nối Codebase

Mỗi phiên `DiscordChatApp` tạo một `BackendChatSession`. Session gọi
`build_chat_orchestrator()` để sử dụng OpenRouter LLM và function-calling với các
tool trong `codebase/backend/chatbot_tools`. Backend giữ `pending_clarification`
và lịch sử hội thoại riêng, tự thực thi tool, sau đó chuyển contract sang giao
diện Discord kèm **AI Tracepath & Tools Execution**.

Khi LLM chạy thành công, trace hiển thị `OpenRouter · <model>` và các tool model
đã gọi. Nếu provider lỗi, trace hiển thị `Rule-based fallback`; trường hợp này
không được hiểu là câu trả lời do LLM tạo.

---

## 📦 4. Mẫu Định Dạng Dữ Liệu Trao Đổi (INPUT & OUTPUT TEMPLATE)

### 📥 4.1. Request Template (Frontend ➔ Backend)

Frontend gọi orchestrator với các tham số sau:

```python
orchestrator.process_message(
    message="Deadline bao nhiêu z?",
    user_id="student_demo",
    session_id="nicegui_session",
    channel_id="go-vuong-hoc-tap",
    pending_clarification=None,
    conversation_history=[],
)
```

---

### 📤 4.2. Response Template với TRACEPATH (Backend ➔ Frontend)

Codebase trả contract sau; adapter tạo `tracepath` cho UI từ kết quả thực thi:

```json
{
  "schema_version": "1.0",
  "route": "CLARIFY",
  "intent": "ask_deadline",
  "confidence": 0.71,
  "response": "Bạn đang hỏi deadline của bài tập hay project nào?",
  "grounding_status": "not_required",
  "clarification": {
    "missing_field": "assignment",
    "suggested_replies": ["Weekly Assignment", "AI Log"]
  },
  "citations": [],
  "escalation": null,
  "trace_id": "..."
}
```

---

### 🎯 4.3. Bảng Ánh Xạ Trạng Thái Backend ➔ Frontend UI

| `route` từ codebase | Giao diện Frontend tự động hiển thị |
|---|---|
| `CLARIFY` | Thẻ vàng + nút từ `clarification.suggested_replies` |
| `ANSWER` | Thẻ xanh + citation thật + nút xem nguồn/phản hồi |
| `ESCALATE` | Thẻ đỏ + thông tin người/kênh tiếp nhận |

---

## ⚡ 5. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **Lỗi `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8080)`**:
   - **Nguyên nhân**: Đã có 1 tiến trình python khác đang chiếm cổng 8080.
   - **Xử lý**: Tắt tiến trình python đang chạy bằng `Ctrl + C` hoặc đổi `PORT=8081` trong file `.env`.

2. **Không import được `chatbot_tools`**:
   - Chạy từ thư mục gốc bằng `py codebase/app.py` hoặc `py frontend/main.py`.
   - Không đổi vị trí tương đối của `frontend/` và `codebase/backend/`.

3. **Màu sắc đã đúng nhưng font hoặc một số chi tiết CSS chưa cập nhật**:
   - Cài lại đúng dependency bằng `pip install -r frontend/requirements.txt`.
   - Hard refresh trình duyệt (`Ctrl+F5`) để bỏ cache stylesheet/font cũ.
   - Giao diện dùng `Inter` thay cho `gg sans`; `gg sans` là font riêng của
     Discord và không được phục vụ bởi Google Fonts.
