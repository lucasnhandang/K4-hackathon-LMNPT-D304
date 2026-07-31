---
name: discord-ui-nicegui
description: Sửa layout, style, hoặc thêm loại tin nhắn/embed mới trong giao diện Discord-clone (frontend/main.py, frontend/custom_styles.py). Dùng khi task nói tới "giao diện", "CSS", "embed", "màu sắc", "layout Discord", "AI Tracepath box", hoặc thêm nút bấm/loại phản hồi mới trên UI.
---

# Discord UI (NiceGUI)

Đọc trước: `project_setup/architecture/frontend.md` (schema message/payload/tracepath đầy
đủ) và `project_setup/architecture/DECISIONS.md` D-003/D-005.

## Việc thường gặp

**Thêm 1 loại embed mới (vd. thêm màu cho lớp chỗ khó thứ 5):**
1. Đảm bảo `ai_router.py` trả `embed_type` mới (xem skill `ai-router-taxonomy`).
2. Thêm rule `.discord-embed.<tên>-embed` trong `custom_styles.py`, dùng token có sẵn ở
   `:root` (`--red`, `--amber`, `--green`, `--text-faint`, `--shadow-glow-*`) thay vì hard-code
   màu mới trừ khi thực sự cần — nếu cần màu mới, thêm token vào `:root` trước.
3. Nếu cần hành vi khác màu sắc (icon riêng, layout khác), sửa
   `DiscordChatApp.update_chat_ui` trong `main.py`.
4. **Bắt buộc kiểm tra khớp 1-1**: `grep "embed_type" frontend/ai_router.py` phải khớp với
   `grep "discord-embed\." frontend/custom_styles.py` — CSS thiếu class không báo lỗi, chỉ
   im lặng rơi về border brand mặc định (D-005).

**Sửa style/design token:** đổi ở `:root` trong `DISCORD_CSS` (`custom_styles.py`), không
hard-code giá trị màu/bo góc/bóng rải rác trong từng rule — dùng `var(--token)`.

**Đổi layout 3 cột (server list / channel sidebar / chat area):** trong
`DiscordChatApp.build_ui` (`main.py`) — mỗi cột là 1 class CSS riêng
(`.servers-column`/`.channels-sidebar`/`.chat-area`), style tương ứng cùng tên trong
`custom_styles.py`.

## Sau khi sửa xong

1. Chạy thử: `cd frontend; python main.py` (hoặc `.venv/Scripts/python.exe main.py` nếu
   venv riêng), mở `http://localhost:8080`, thử ít nhất 1 câu trigger mỗi loại embed đã đổi.
   Nếu port 8080 đang bị chiếm bởi phiên chạy trước, tắt tiến trình cũ trước khi chạy lại.
2. Gọi skill `arch-doc-sync` nếu thay đổi ảnh hưởng schema/danh sách embed (không cần cho
   thay đổi CSS thuần tuý thẩm mỹ, không đổi cấu trúc dữ liệu).
