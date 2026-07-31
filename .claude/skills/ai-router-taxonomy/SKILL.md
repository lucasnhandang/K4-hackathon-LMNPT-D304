---
name: ai-router-taxonomy
description: Sửa logic phân loại câu hỏi, knowledge base, hoặc đấu nối backend AI thật trong frontend/ai_router.py. Dùng khi task nói tới "phân loại intent", "thêm câu trả lời", "knowledge base", "nối backend thật", "escalate/chuyển Mod", "4 lớp chỗ khó", hoặc taxonomy AMBIGUOUS/DIRECT_ANSWER/NO_SOURCE_ESCALATE/OUT_OF_SCOPE.
---

# AI Router & Taxonomy

Đọc trước: `project_setup/architecture/ai_router.md` (chi tiết đầy đủ thứ tự ưu tiên mock,
cách `handle_option_selection` match chuỗi con, cách backend thật hook vào). Contract JSON
Frontend↔Backend đầy đủ: `frontend/GUIDE_FRONTEND_BACKEND.md` — **không copy lại schema vào
đây hay vào doc khác**, chỉ link.

## Bất biến bắt buộc giữ (xem D-004 trong DECISIONS.md)

4 trạng thái backend map cứng 1-1 với 4 lớp chỗ khó của đề bài
(`need_clarification`/`resolved`/`escalated`/`out_of_scope`). Thêm trạng thái thứ 5 = đổi
taxonomy — phải đồng bộ cả 3 chỗ: nhánh mới trong `transform_backend_response_to_ui`, CSS
`.discord-embed.<type>-embed` mới (xem skill `discord-ui-nicegui`), và bảng taxonomy trong
`overview.md`.

## Việc thường gặp

**Thêm ground truth mới** (câu trả lời có căn cứ): thêm entry vào `KNOWLEDGE_BASE`, thêm
nhánh keyword-match tương ứng trong `classify_and_route` (đặt đúng vị trí theo thứ tự ưu
tiên đã có — xem `ai_router.md`, đừng thêm cuối cùng nếu lẽ ra phải ưu tiên cao hơn nhánh
escalate/out-of-scope hiện có), trả `citations` trỏ về entry đó.

**Thêm nút follow-up mới:** đặt `value` không vô tình chứa các chuỗi khoá đã dùng trong
`handle_option_selection` (liệt kê đầy đủ trong `ai_router.md`) trừ khi cố ý muốn khớp nhánh
đó — hàm này match theo `in`, không match chính xác.

**Nối backend thật:** hiện `main.py::process_bot_reply` gọi thẳng `classify_and_route`
(mock, đồng bộ) — **chưa** gọi `call_backend_api_async`. Cần sửa `main.py` để dùng
`call_backend_api_async` (bất đồng bộ) thay cho `classify_and_route`, và set
`USE_LOCAL_MOCK=false` + `BACKEND_URL` trong `.env`. Không đổi payload UI output của
`transform_backend_response_to_ui` — backend mới chỉ cần trả đúng shape input JSON.

## Sau khi sửa xong

1. Test bằng tay qua UI (`cd frontend; python main.py`) — gõ thử câu trigger đúng nhánh mới.
2. Gọi skill `arch-doc-sync`: cập nhật bảng taxonomy trong `overview.md` và/hoặc
   `PROJECT_MAP.md` nếu thêm symbol công khai mới.
