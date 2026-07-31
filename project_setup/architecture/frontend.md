# Frontend — NiceGUI Discord-clone

> Last updated: 2026-07-31
> Xem `PROJECT_MAP.md` cho danh sách symbol đầy đủ. File này giải thích **hình dạng dữ liệu**
> và **cách mở rộng an toàn**, không lặp lại danh sách symbol.

## Message schema (trong `DiscordChatApp.messages`)

Mỗi phần tử `self.messages` là 1 dict:

```python
{
    "sender": "bot" | "user",
    "name": str,                # "Trợ lý Claude" hoặc "Học viên K4"
    "time": str,                 # "Hôm nay lúc HH:MM"
    "text": str,                 # có thể chứa **bold** và @mention — render qua render_msg_text
    "payload": dict | None,      # None với tin nhắn user; dict với tin nhắn bot có embed
    "reply_to": str,             # optional, chỉ có ở tin bot — tên người được reply
    "reactions": list[str],      # optional, chưa có nơi nào gán giá trị này hiện tại
}
```

## Payload schema (embed dưới tin nhắn bot)

Đây là **output của `ai_router.transform_backend_response_to_ui`**, không phải input thô
từ backend — xem `ai_router.md` cho input thô. `update_chat_ui` đọc payload theo thứ tự:

```python
{
    "type": "AMBIGUOUS" | "DIRECT_ANSWER" | "NO_SOURCE_ESCALATE" | "OUT_OF_SCOPE" | "CHAT_REPLY",
    "message": str,               # text hiển thị trong bong bóng chat (không phải trong embed)
    "embed_type": str,            # tên CSS class: "warning-embed" | "success-embed" | "escalate-embed" | "muted-embed"
    "title": str,                 # optional — tiêu đề trong embed
    "escalate_tag": str,          # optional — chỉ NO_SOURCE_ESCALATE, vd "@Mod / @Mentor"
    "escalate_detail": str,       # optional
    "source_info": str,           # optional — dòng "💡 ..." trong embed
    "options": [                  # optional — render thành nút bấm
        {"label": str, "value": str, "class": "disc-btn" | "disc-btn-success" | "disc-btn-danger"},
    ],
    "tracepath": dict | None,     # optional — xem cấu trúc bên dưới
}
```

`type: "CHAT_REPLY"` (từ `handle_option_selection` khi user bấm "Đã giải quyết"/"Cảm ơn") là
payload rút gọn, không có `embed_type` — `update_chat_ui` bỏ qua khối embed nếu thiếu key.

### `tracepath` (AI Tracepath & Tool Execution box)

```python
{
    "latency_ms": int,
    "confidence": float,          # 0.0–1.0, hiển thị dạng %
    "intent": str,
    "tools_used": [{"name": str, "icon": str, "status": str}],  # render thành pill nối bằng ➔
    "steps": [str],               # mỗi dòng 1 bullet ❯ trong trace-steps-list
}
```

## 4 giá trị `embed_type` ↔ CSS

| `embed_type` | CSS rule (`custom_styles.py`) | Dùng cho |
|---|---|---|
| `warning-embed` | `.discord-embed.warning-embed` | `AMBIGUOUS` |
| `success-embed` | `.discord-embed.success-embed` | `DIRECT_ANSWER` |
| `escalate-embed` | `.discord-embed.escalate-embed` | `NO_SOURCE_ESCALATE` |
| `muted-embed` | `.discord-embed.muted-embed` | `OUT_OF_SCOPE` |

**Bất biến:** mỗi `embed_type` mới trong `ai_router.py` phải có 1 rule
`.discord-embed.<embed_type>` tương ứng trong `custom_styles.py` — CSS thiếu class không
báo lỗi (xem D-005 trong `DECISIONS.md`), chỉ rơi về border màu brand mặc định.

## Cách thêm 1 loại phản hồi/embed mới

1. Thêm nhánh mới trong `ai_router.py::transform_backend_response_to_ui` (hoặc trong mock ở
   `classify_and_route`/`handle_option_selection`), trả `embed_type` mới, đặt tên rõ ràng
   (`<mô-tả>-embed`).
2. Thêm `.discord-embed.<tên>-embed { border-left-color: ...; box-shadow: ...; }` trong
   `custom_styles.py`, dùng token có sẵn (`--red`, `--amber`, `--green`, `--text-faint`, hoặc
   thêm token mới ở `:root` nếu cần màu mới).
3. Nếu loại phản hồi cần hành vi UI riêng (không chỉ đổi màu — vd. thêm icon đặc biệt), sửa
   `DiscordChatApp.update_chat_ui` trong `main.py`, đúng đoạn `if "xxx" in payload:`.
4. Cập nhật bảng trong `overview.md` (mục "4 lớp chỗ khó ↔ 4 trạng thái") nếu loại mới liên
   quan tới taxonomy đề bài.

## Điểm dễ vỡ đã biết (không phải bug cần fix ngay, nhưng cần biết trước khi sửa)

- **`open_source_modal`** (`main.py`) hard-code đọc `KNOWLEDGE_BASE["weekly_report"]` — dialog
  "Xem nguồn" luôn hiện thông tin weekly report bất kể tin nhắn nào đang được xem. Khi thêm
  knowledge base entry mới, dialog này **không** tự động đúng theo ngữ cảnh; cần truyền
  `payload["quote"]`/`payload["source_info"]` (đã có sẵn trong payload `DIRECT_ANSWER`) vào
  `open_source_modal` thay vì đọc cứng key `weekly_report`.
- **`update_chat_ui` full re-render**: mỗi lần state đổi, `messages_container.clear()` rồi vẽ
  lại toàn bộ lịch sử chat — chấp nhận được ở quy mô demo (vài chục tin nhắn), sẽ chậm dần
  nếu hội thoại dài trong 1 phiên.
- **CSS nhúng qua chuỗi Python** (`DISCORD_CSS` trong `custom_styles.py`) — không có linter/
  build step nào bắt lỗi CSS sai cú pháp; lỗi chỉ lộ ra khi mở trình duyệt bằng mắt.
