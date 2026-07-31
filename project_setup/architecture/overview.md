# Overview — Trợ lý Học viên Discord

> Last updated: 2026-07-31

Hướng đã chọn: **Hướng B — Trợ lý Học viên (Discord)**, nhánh "Tối ưu" theo `01-de-bai.md`
(nhận diện intent thật, biết-mình-không-biết → chuyển TA, trả lời logistics chỉ từ nguồn chính thức).

## Trạng thái hiện tại

Prototype ở mức **Mock** (theo thang Sketch/Mock/Working của luật chung): giao diện thật
(NiceGUI, giả lập Discord 100%), logic phân loại là **rule-based theo từ khoá**, chưa có
model/RAG thật. `frontend/ai_router.py` đã có sẵn đường gọi HTTP tới backend thật
(`call_backend_api_async`) — chỉ cần bật `USE_LOCAL_MOCK=false` khi backend sẵn sàng.

Có **≥1 lời gọi AI chạy thật** theo yêu cầu luật chung là điều kiện chưa hoàn tất ở mức
hiện tại nếu vẫn chạy 100% mock — xem `04-rubric.md` R5 trước khi demo.

## Kiến trúc

```
Discord (thật)  ─┐
                  ├──▶  [chưa build]  Backend thật (intent classifier + RAG + policy)
NiceGUI giả lập ──┘         ▲                    │
(frontend/main.py)          │                    ▼
       │                    └── HTTP JSON ──  ai_router.py::call_backend_api_async
       │                                            │ (USE_LOCAL_MOCK=true → bỏ qua, dùng mock local)
       ▼                                            ▼
render Discord UI  ◀── payload chuẩn hoá UI ──  transform_backend_response_to_ui()
(bong bóng chat, embed màu,                          ▲
 AI Tracepath box, nút follow-up)                    │
                                             classify_and_route() (mock rule-based)
```

- **Frontend** (`frontend/`): NiceGUI app giả lập 100% giao diện Discord (server list, channel
  sidebar, chat area) để demo không cần tài khoản Discord thật. Xem `architecture/frontend.md`.
- **AI router** (`frontend/ai_router.py`): điểm nối duy nhất giữa UI và "não" AI — hoặc mock
  local, hoặc gọi backend thật qua HTTP theo contract trong `frontend/GUIDE_FRONTEND_BACKEND.md`.
  Xem `architecture/ai_router.md`.
- **Backend thật**: chưa tồn tại trong repo này tại thời điểm viết doc — khi build, đặt ở thư
  mục riêng (vd. `backend/`) và implement đúng contract JSON đã định sẵn trong
  `frontend/GUIDE_FRONTEND_BACKEND.md`, không đổi shape phía frontend.

## 4 lớp "chỗ khó" ↔ 4 trạng thái backend

Đề bài (`01-de-bai.md`) yêu cầu xử lý 4 lớp chỗ khó; `ai_router.py` map cứng chúng vào
4 cặp `status`/`action` (xem D-004 trong `DECISIONS.md`):

| Lớp chỗ khó (đề bài) | `status` / `action` backend | UI type | Embed |
|---|---|---|---|
| ② Mơ hồ / thiếu thông tin | `need_clarification` / `ask_follow_up` | `AMBIGUOUS` | vàng (`warning-embed`) |
| — trả lời có căn cứ | `resolved` / `direct_answer` | `DIRECT_ANSWER` | xanh lá (`success-embed`) |
| ① Nguồn sự thật (không có căn cứ) | `escalated` / `escalate_mod` | `NO_SOURCE_ESCALATE` | đỏ (`escalate-embed`) |
| ③ Ngoài phạm vi / thẩm quyền | `out_of_scope` / `reject` | `OUT_OF_SCOPE` | xám (`muted-embed`) |

Lớp ④ (đặc thù domain — sai kiến thức làm mất niềm tin) chưa có cơ chế riêng ở mock hiện
tại; xử lý gián tiếp qua việc mọi câu `resolved` đều bắt buộc kèm `citations` trỏ về
`KNOWLEDGE_BASE` (xem `ai_router.md`).

## Dữ liệu

`data/vlearn-pack/` — chatlog + transcript + slides thật đã ẩn danh, dùng để mining bằng
chứng và xây golden set. **Không** dùng làm nguồn cho Trợ lý Học viên (đây là data của
VLearn tutor, hướng A) — hướng B tự mining trực tiếp trong Discord khoá theo `01-de-bai.md`.
Xem quy định bảo mật ở `README.md` trước khi đưa bất kỳ phần data nào vào tool ngoài.

## Đọc thêm

- Chi tiết UI: `architecture/frontend.md`
- Chi tiết router/taxonomy: `architecture/ai_router.md`
- Vì sao chọn NiceGUI, vì sao giữ 2 file `index.html` cũ, v.v.: `architecture/DECISIONS.md`
- File nào có gì, symbol nào ở đâu: `architecture/PROJECT_MAP.md`
