# CP3 — Input/Output contract

Tài liệu này chốt contract giữa UI/integration, AI core, tools và eval cho lát cắt:
trợ lý quyết định `ANSWER / CLARIFY / ESCALATE` đối với câu hỏi của học viên trên
Discord.

## 1. Kết luận về format đề xuất ban đầu

Format ban đầu đã có các nhóm dữ liệu cần thiết: metadata, tin nhắn hiện tại, lịch
sử hội thoại, context hoạt động của cộng đồng và output cho nhánh hỏi lại. Tuy
nhiên cần sửa các điểm sau trước khi dùng làm contract:

1. Dùng đúng một trường quyết định chuẩn là `route`, với ba giá trị viết hoa
   `ANSWER`, `CLARIFY`, `ESCALATE`. Không đồng thời dùng `status`, `action` và
   `handoff` để biểu diễn cùng một quyết định vì chúng có thể mâu thuẫn.
2. `conversation.current_step: "clarification"` dễ làm router bị bias và không cho
   biết đang thiếu thông tin gì. Thay bằng `pending_clarification`; để `null` nếu đây
   là câu hỏi mới.
3. Thêm `schema_version` để các thành viên thay đổi contract có kiểm soát.
4. `confidence` phải là độ tin cậy của **quyết định route**, không phải độ chắc chắn
   chung chung của mô hình. Không dùng một ngưỡng confidence đơn lẻ để thay cho
   kiểm tra nguồn.
5. Citation cần là object có `source_id`, `title`, `locator` và `quote`, không chỉ là
   chuỗi hoặc số trang. Nhờ vậy evaluator có thể kiểm tra từng claim.
6. Thêm `grounding_status` để phân biệt: đã tìm thấy căn cứ, không cần căn cứ, hoặc
   không tìm thấy căn cứ.
7. Trace tool call là artifact nội bộ, không phải nội dung gửi cho học viên. Output
   chỉ trả `trace_id`; log tương ứng được lưu riêng, không lưu chain-of-thought và
   không chứa API key/PII.
8. `context` là mô tả phạm vi hoạt động của chatbot trong cộng đồng AI20K Build
   Phase. Đây phải là trusted context do backend cấp, không lấy từ nội dung do
   người dùng gửi.
9. ID người dùng phải là ID giả/đã băm. Timestamp dùng ISO 8601 và ghi rõ timezone.
10. `follow_up` chỉ là gợi ý chọn nhanh, không thay thế câu hỏi làm rõ. Với nhánh
   `CLARIFY`, trợ lý chỉ hỏi **một câu** để lấy thông tin còn thiếu quan trọng nhất.

## 2. Quy ước contract

### Trường input

| Trường | Bắt buộc | Quy ước |
|---|:---:|---|
| `schema_version` | Có | Hiện tại là `1.0` |
| `metadata.message_id` | Có | Duy nhất trong hệ thống |
| `metadata.timestamp` | Có | ISO 8601 có timezone |
| `metadata.user_id` | Có | ID giả/đã băm, không dùng tên thật |
| `metadata.session_id` | Có | Dùng nối các turn |
| `metadata.channel_id` | Có | Kênh mà bot được phép đọc |
| `message.type` | Có | CP3 chỉ hỗ trợ `text` |
| `message.content` | Có | Chuỗi không rỗng sau khi trim |
| `conversation.history` | Có | Có thể là `[]`; sắp từ cũ đến mới |
| `conversation.pending_clarification` | Có | `null` hoặc thông tin slot đang hỏi |
| `context` | Có | Trusted context mô tả mục tiêu và phạm vi hỗ trợ trong AI20K Build Phase |
| `runtime.language` | Có | CP3: `vi` |
| `runtime.platform` | Có | CP3: `discord` |

### Trường output

| Trường | Bắt buộc | Quy ước |
|---|:---:|---|
| `schema_version` | Có | Cùng major version với input |
| `message_id` | Có | Echo `metadata.message_id` để ghép request/response |
| `route` | Có | Chỉ một trong `ANSWER`, `CLARIFY`, `ESCALATE` |
| `intent` | Có | Nhãn intent ổn định, dạng `snake_case` |
| `confidence` | Có | Số `[0,1]`, độ tin cậy của route |
| `grounding_status` | Có | `grounded`, `not_required`, hoặc `no_source` |
| `response` | Có | Nội dung cuối cùng hiển thị cho học viên |
| `clarification` | Có | Object khi `CLARIFY`, nếu không là `null` |
| `citations` | Có | Mảng citation; không có thì `[]` |
| `escalation` | Có | Object khi `ESCALATE`, nếu không là `null` |
| `trace_id` | Có | Khóa tra log router/retrieval/tool; không phải chain-of-thought |

Các bất biến phải được validate:

- `ANSWER` → có ít nhất một citation chính thức cho mọi claim logistics/kiến thức;
  `grounding_status = "grounded"`.
- `CLARIFY` → `clarification` khác `null`, chỉ có một câu hỏi chính, không tự đoán
  câu trả lời; thông thường `citations = []`.
- `ESCALATE` → `escalation` khác `null`, nêu lý do và bước tiếp theo; không bịa câu
  trả lời thay Mod/TA.
- `clarification` và `escalation` không được cùng khác `null`.
- Nếu input là chào hỏi/cảm ơn và không có claim cần kiểm chứng, có thể `ANSWER`
  với `grounding_status = "not_required"` và `citations = []`.

## 3. Ví dụ input — câu hỏi thiếu đối tượng

```json
{
  "schema_version": "1.0",
  "metadata": {
    "message_id": "msg_001",
    "timestamp": "2026-07-30T14:30:00+07:00",
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
    "pending_clarification": null
  },
  "context": {
    "description": "Mục tiêu của chatbot là trở thành một người bạn đồng hành năng động, giúp các thành viên của cộng đồng **AI20K Build Phase** dễ dàng tìm kiếm thông tin và giải đáp các thắc mắc thường gặp (FAQ) đó! ✨\n\nCụ thể, mình ở đây để giúp bạn:\n**Giải đáp thắc mắc:** Về quy định server, hệ thống role, và cách tham gia các hoạt động.\n**\"Chỉ đường\" nhanh chóng:** Giúp bạn tìm đúng kênh Discord hoặc tài liệu bạn đang cần (như slide bài học, link nộp bài...).\n**Cập nhật thông tin:** Nhắc lịch các buổi Workshop, Office Hours hoặc các sự kiện quan trọng của cộng đồng.\n**Hỗ trợ tinh thần \"Build\":** Luôn sẵn sàng giải đáp để bạn không bị \"kẹt\" và có thể tập trung tối đa vào việc học tập và phát triển dự án.\n\nNói chung, cứ có gì thắc mắc về hoạt động của AI20K Build Phase thì bạn cứ hỏi mình nha, mình sẽ cố gắng hỗ trợ hết mình!"
  },
  "runtime": {
    "language": "vi",
    "platform": "discord"
  }
}
```

## 4. Ví dụ output — `CLARIFY`

```json
{
  "schema_version": "1.0",
  "message_id": "msg_001",
  "route": "CLARIFY",
  "intent": "ask_deadline",
  "confidence": 0.91,
  "grounding_status": "no_source",
  "response": "Bạn đang hỏi deadline của project cuối khóa, Weekly Assignment hay bài nào khác?",
  "clarification": {
    "missing_field": "assignment",
    "question": "Bạn đang hỏi deadline của project cuối khóa, Weekly Assignment hay bài nào khác?",
    "suggested_replies": [
      "Project cuối khóa",
      "Weekly Assignment",
      "Bài khác"
    ]
  },
  "citations": [],
  "escalation": null,
  "trace_id": "trace_001"
}
```

Lưu ý: lịch sử có nhắc “project cuối khóa” nhưng người dùng chưa xác nhận đó là đối
tượng của câu hỏi hiện tại. Router không được suy diễn deadline từ nội dung gần nhất.

## 5. Ví dụ rút gọn cho hai route còn lại

### `ANSWER`

```json
{
  "schema_version": "1.0",
  "message_id": "msg_002",
  "route": "ANSWER",
  "intent": "ask_deadline",
  "confidence": 0.96,
  "grounding_status": "grounded",
  "response": "Deadline của Weekly Assignment 3 là 12:00 ngày 31/07/2026 (GMT+7).",
  "clarification": null,
  "citations": [
    {
      "source_id": "official_schedule_2026_07",
      "title": "Lịch nộp bài chính thức",
      "locator": "Weekly Assignment 3",
      "quote": "Hạn nộp: 12:00 31/07/2026 (GMT+7)"
    }
  ],
  "escalation": null,
  "trace_id": "trace_002"
}
```

### `ESCALATE`

```json
{
  "schema_version": "1.0",
  "message_id": "msg_003",
  "route": "ESCALATE",
  "intent": "request_deadline_exception",
  "confidence": 0.94,
  "grounding_status": "no_source",
  "response": "Mình không có quyền duyệt gia hạn. Mình sẽ chuyển yêu cầu này cho Mod; bạn vui lòng nêu mã bài và lý do cần gia hạn.",
  "clarification": null,
  "citations": [],
  "escalation": {
    "reason_code": "requires_human_authority",
    "target": "MOD",
    "summary": "Học viên đề nghị gia hạn deadline; cần người có thẩm quyền xem xét.",
    "required_information": [
      "assignment",
      "reason"
    ]
  },
  "trace_id": "trace_003"
}
```

## 6. Format trace nội bộ

Mỗi `trace_id` trỏ tới một JSON log riêng. Trace chỉ ghi quyết định quan sát được,
không ghi suy luận ẩn của mô hình:

```json
{
  "trace_id": "trace_002",
  "message_id": "msg_002",
  "router": {
    "route": "ANSWER",
    "intent": "ask_deadline",
    "confidence": 0.96
  },
  "tool_calls": [
    {
      "tool": "search_official_sources",
      "query": "Weekly Assignment 3 deadline",
      "status": "success",
      "result_ids": ["official_schedule_2026_07"],
      "latency_ms": 184
    }
  ],
  "validation": {
    "schema_valid": true,
    "citation_ids_exist": true
  }
}
```

Không ghi API key, token bí mật, tên/ID Discord thật, toàn bộ tài liệu nguồn hoặc
chain-of-thought vào trace.
