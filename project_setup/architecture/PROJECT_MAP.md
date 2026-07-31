# Project Map

> Last updated: 2026-07-31
> `file:symbol` để nhảy thẳng — đọc trước khi Grep/Glob. Thêm symbol công khai mới vào đây
> khi bạn thêm nó vào code (xem skill `arch-doc-sync`).

## Cấu trúc thư mục

```
K4-hackathon-LMNPT-D304/
├── CLAUDE.md                          # project memory, Claude Code tự nạp mỗi phiên
├── project_setup/architecture/        # ← bạn đang ở đây
├── frontend/                          # UI thật đang chạy — NiceGUI Discord-clone
│   ├── main.py                        # app chính: layout + state + render
│   ├── ai_router.py                   # mock intent classifier + cầu nối backend thật
│   ├── custom_styles.py               # toàn bộ CSS (design token v2)
│   ├── GUIDE_FRONTEND_BACKEND.md      # NGUỒN CHUẨN contract JSON Frontend↔Backend
│   └── requirements.txt
├── codebase/                          # entrypoint nộp bài (thư mục chấm điểm chính thức)
│   ├── app.py                         # import frontend/main.py — KHÔNG code logic ở đây
│   └── index.html                     # bản tĩnh CP2 cũ — xem DECISIONS D-003
├── index.html                         # bản tĩnh CP2 cũ khác — xem DECISIONS D-003
├── data/vlearn-pack/                  # data thật đã ẩn danh (chatlog/transcript/slides) — hướng A, không dùng cho hướng B
├── tham-khao/                         # JTBD Playbook (PDF) + worksheet
├── Canvas.txt                         # canvas nháp CP1 (JTBD 1 trang)
└── 01-de-bai.md .. 04-rubric.md, README.md   # tài liệu tổ chức hackathon, không phải code
```

## `frontend/main.py` — UI & state

| Symbol | Vai trò |
|---|---|
| `DiscordChatApp` | Class chính, giữ toàn bộ state (`self.messages`, `self.is_typing`) |
| `DiscordChatApp.reset_messages` | Tin chào mừng ban đầu |
| `DiscordChatApp.send_user_text` | User gõ Enter → append tin nhắn user → gọi `process_bot_reply` qua `ui.timer` |
| `DiscordChatApp.process_bot_reply` | Gọi `ai_router.classify_and_route`, append tin nhắn bot |
| `DiscordChatApp.handle_option_click` / `process_option_reply` | User bấm nút follow-up → gọi `ai_router.handle_option_selection` |
| `DiscordChatApp.open_source_modal` | Dialog "Xem nguồn" — hiện đang hard-code đọc `KNOWLEDGE_BASE["weekly_report"]`, chưa đọc theo payload thực tế (xem `frontend.md`) |
| `DiscordChatApp.render_msg_text` | Regex: bôi đậm `**text**`, tô màu `@mention` |
| `DiscordChatApp.render_tracepath_html` | Render "AI Tracepath & Tool Execution" box từ `payload.tracepath` |
| `DiscordChatApp.update_chat_ui` | Vẽ lại toàn bộ `self.messages` — gọi lại mỗi khi state đổi (không diff, full re-render) |
| `DiscordChatApp.build_ui` | Layout 3 cột: `.servers-column` / `.channels-sidebar` / `.chat-area` |
| `main()` | Khởi tạo `DiscordChatApp`, gọi `build_ui()` — entrypoint gọi từ `if __name__ ...` cuối file và từ `codebase/app.py` |

## `frontend/ai_router.py` — router & taxonomy

Chi tiết đầy đủ: `architecture/ai_router.md`. Tóm tắt symbol:

| Symbol | Vai trò |
|---|---|
| `KNOWLEDGE_BASE` | dict ground-truth cứng: `weekly_report`, `mentor_duty`, `general` |
| `transform_backend_response_to_ui(backend_data)` | **Điểm chuẩn hoá duy nhất** — nhận JSON kiểu backend thật (`status`/`action`/`response`/`citations`/`tracepath`...), trả payload UI (`type`/`embed_type`/`options`/`tracepath`) |
| `call_backend_api_async(user_message, history)` | Gọi HTTP tới `BACKEND_URL`; lỗi/timeout hoặc `USE_LOCAL_MOCK=true` → fallback `classify_and_route` |
| `classify_and_route(user_message, context_state=None)` | Mock rule-based theo từ khoá (4 nhánh: out_of_scope → escalate → 2 direct-answer cứng → ambiguous mặc định) |
| `handle_option_selection(option_value, context=None)` | Xử lý các `option_value` cố định (`CAT_WEEKLY`, `FEEDBACK_RESOLVED`, `FORCE_ESCALATE`, ...) — **string-matching cứng, dễ vỡ khi đổi label nút** (xem `ai_router.md`) |

## `frontend/custom_styles.py`

| Symbol | Vai trò |
|---|---|
| `DISCORD_CSS` | Toàn bộ `<style>` + Google Fonts link, nhúng qua `ui.add_head_html(DISCORD_CSS)` trong `main.py` |

Design tokens chính (CSS custom properties trong `:root`): `--brand*`, `--green*`,
`--red*`, `--amber*` (màu), `--radius-*` (bo góc), `--shadow-*`/`--shadow-glow-*` (đổ bóng),
`--grad-*` (gradient). Thêm màu/trạng thái mới → thêm token ở `:root` trước, không hard-code
màu rải rác trong rule.

## `codebase/`

| File | Vai trò |
|---|---|
| `codebase/app.py` | Entrypoint chấm điểm: `sys.path.insert` trỏ về `frontend/`, import `main` từ đó rồi `ui.run(...)`. Không viết logic ở đây. |
| `codebase/index.html` | Xem D-003 — không phải nguồn hiện hành |

## Ground truth hiện có (trong `KNOWLEDGE_BASE`)

| Key | Câu hỏi khớp (mock) |
|---|---|
| `weekly_report` | "weekly report" + ("khi nào"/"deadline"/"bao giờ"/...) |
| `mentor_duty` | chứa "mentor" |
| `general` | chỉ dùng trong dialog "Xem nguồn", chưa có route nào trả về nó |

## Chưa tồn tại trong repo (khi build sẽ cần map vào đây)

- Backend thật (intent classifier / RAG / policy engine) — hiện chỉ có contract JSON ở
  `frontend/GUIDE_FRONTEND_BACKEND.md`, chưa có server implement.
- `eval/`, `validation/`, `reflection/`, `spec.md`, `demo-slides.pdf` — theo cấu trúc nộp bài
  yêu cầu ở `README.md`, chưa tạo trong repo tại thời điểm viết doc này.
