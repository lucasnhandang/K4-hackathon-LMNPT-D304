# AI Router — taxonomy, mock, backend contract

> Last updated: 2026-07-31
> Contract JSON đầy đủ (request/response mẫu) **sống ở**
> [`frontend/GUIDE_FRONTEND_BACKEND.md`](../../frontend/GUIDE_FRONTEND_BACKEND.md) — file này
> không copy lại schema, chỉ giải thích cách `ai_router.py` dùng nó và cách mở rộng.

## Hai chế độ hoạt động

`ai_router.py` có đúng **một** điểm vào từ UI: `main.py` gọi `classify_and_route()` trực
tiếp (đồng bộ, mock). Đường gọi backend thật (`call_backend_api_async`, bất đồng bộ) **hiện
chưa được `main.py` gọi tới** — cần sửa `process_bot_reply` trong `main.py` để `await
call_backend_api_async(...)` thay vì gọi thẳng `classify_and_route(...)` khi muốn dùng
backend thật thay vì mock.

| Biến môi trường | Ảnh hưởng |
|---|---|
| `USE_LOCAL_MOCK` (mặc định `true`) | `true` → `call_backend_api_async` không gọi mạng, dùng `classify_and_route` luôn |
| `BACKEND_URL` (mặc định `http://localhost:8000/api/v1/chat`) | Endpoint backend thật khi `USE_LOCAL_MOCK=false` |

Khi backend thật lỗi hoặc timeout (8s), `call_backend_api_async` tự fallback về
`classify_and_route` và in `[Warning] Không thể kết nối Backend API` ra log — xem D-002.

## `transform_backend_response_to_ui` — điểm chuẩn hoá duy nhất

Đây là hàm **duy nhất** biết cách JSON kiểu backend (`status`/`action`/`response`/
`follow_up`/`citations`/`handoff`/`tracepath`) map sang payload UI (`type`/`embed_type`/
`options`). Backend thật chỉ cần trả đúng shape trong `GUIDE_FRONTEND_BACKEND.md` §4.2 —
không cần biết gì về NiceGUI/CSS. Logic map:

```
status == "need_clarification" hoặc action == "ask_follow_up"   → AMBIGUOUS
status == "escalated" hoặc handoff hoặc action == "escalate_mod" → NO_SOURCE_ESCALATE
status == "out_of_scope" hoặc action == "reject"                 → OUT_OF_SCOPE
(mặc định)                                                        → DIRECT_ANSWER
```

Nếu backend không gửi `tracepath`, hàm tự sinh 1 bản tracepath mặc định từ `intent` +
`confidence` — nghĩa là **backend thật không bắt buộc** phải trả `tracepath`, nhưng nếu trả
sẽ hiển thị chính xác hơn là bản tự sinh.

## Mock hiện tại (`classify_and_route`) — thứ tự ưu tiên

Rule-based theo từ khoá, xét theo đúng thứ tự (dừng ở nhánh khớp đầu tiên):

1. **Out of scope**: khớp 1 trong các từ khoá an toàn (`bom`, `vũ khí`, `thời tiết`, `game`, ...)
2. **Escalate**: khớp từ khoá "không có nguồn chuẩn trong data" (`nộp bù`, `xin gia hạn`, `bảo lưu`, ...)
3. **Direct answer — weekly report**: chứa "weekly"/"weekly report" **và** 1 từ hỏi thời gian
4. **Direct answer — mentor duty**: chứa "mentor"
5. **Mặc định → Ambiguous**: mọi câu còn lại, luôn hỏi lại "bài tập hay project nào?"

**Hệ quả của thứ tự này**: câu hỏi vừa khớp escalate-keyword vừa khớp weekly-keyword sẽ luôn
đi vào nhánh escalate (kiểm tra trước). Khi thêm từ khoá mới, thêm đúng đoạn tương ứng —
đừng thêm 1 nhánh mới ở cuối nếu nó lẽ ra phải ưu tiên cao hơn nhánh có sẵn.

## `handle_option_selection` — dễ vỡ khi đổi label nút

Hàm này dùng `option_value.upper()` rồi kiểm tra **chuỗi con** (`"PROJECT" in val_upper`,
`"MOD" in val_upper`, ...) — không phải so khớp chính xác theo key. Khi thêm nút follow-up
mới trong `classify_and_route`/`transform_backend_response_to_ui`, `value` của nút đó phải
**không** vô tình chứa 1 trong các chuỗi khoá đã dùng (`PROJECT`, `CAT_WEEKLY`, `TUẦN HIỆN
TẠI`, `TIME_CURRENT`, `WEEKLY ASSIGNMENT`, `TUẦN TRƯỚC`, `QUIZ`, `KHÁC`, `TIME_LAST`, `MOD`,
`FORCE_ESCALATE`, hoặc đúng bằng `FEEDBACK_RESOLVED`/`FEEDBACK_WRONG`) trừ khi cố ý muốn nó
rơi vào nhánh đó.

## `KNOWLEDGE_BASE` — ground truth cứng

3 entry (`weekly_report`, `mentor_duty`, `general`) là **toàn bộ** nguồn sự thật hiện có
trong mock. Đây không phải data thật từ `data/vlearn-pack/` (data đó thuộc VLearn tutor,
hướng A) — đây là quy chế khoá tự soạn cho hướng B, đặt trực tiếp trong code. Khi build
backend thật với RAG, `KNOWLEDGE_BASE` này nên trở thành seed data hoặc bị thay hoàn toàn
bởi retrieval — quyết định đó chưa chốt, ghi `D-00x` mới trong `DECISIONS.md` khi chốt.

## Khi build backend thật

1. Implement server trả đúng response shape ở `GUIDE_FRONTEND_BACKEND.md` §4.2 tại route
   khớp `BACKEND_URL`.
2. Sửa `main.py::process_bot_reply` (và `process_option_reply` nếu cần) gọi
   `await call_backend_api_async(raw_user_text, history=...)` thay vì
   `classify_and_route(raw_user_text)` — hiện `process_bot_reply` không async, cần đổi
   `ui.timer` callback hoặc dùng `asyncio.create_task`.
3. Set `USE_LOCAL_MOCK=false` trong `.env` (xem `GUIDE_FRONTEND_BACKEND.md` §2.2).
4. Không đổi shape payload UI (`transform_backend_response_to_ui` output) — nếu backend cần
   thêm field mới, thêm vào input JSON (backend response), map thêm trong
   `transform_backend_response_to_ui`, giữ nguyên payload UI cũ tương thích ngược.
