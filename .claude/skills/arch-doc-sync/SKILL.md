---
name: arch-doc-sync
description: Đồng bộ project_setup/architecture/*.md sau khi sửa code, để phiên làm việc sau không phải quét lại repo. Dùng ngay sau bất kỳ thay đổi nào ảnh hưởng cấu trúc, taxonomy, schema payload, hoặc luồng dữ liệu — hoặc khi phát hiện code và doc đang lệch nhau.
---

# Đồng bộ tài liệu kiến trúc

Giữ lớp kiến thức bền vững (`project_setup/architecture/`) khớp với code, để phiên sau
không cần re-scan toàn repo.

## Khi nào dùng

- Ngay sau khi sửa code ảnh hưởng cấu trúc/luồng dữ liệu/taxonomy.
- Khi phát hiện code và doc mâu thuẫn nhau — **code thắng**, sửa doc cho khớp.

## Cách làm

1. **Map thay đổi vào đúng file:**

   | Thay đổi | Cập nhật |
   |---|---|
   | Thêm/sửa `embed_type` hoặc trạng thái backend | `overview.md` (bảng taxonomy) + `frontend.md` (bảng embed↔CSS) |
   | Thêm/sửa symbol công khai trong `main.py`/`ai_router.py`/`custom_styles.py` | `PROJECT_MAP.md` |
   | Đổi contract JSON Frontend↔Backend | `frontend/GUIDE_FRONTEND_BACKEND.md` (nguồn chuẩn) — KHÔNG sửa `ai_router.md`, nó chỉ link tới file đó |
   | Thêm/sửa entry `KNOWLEDGE_BASE` hoặc thứ tự ưu tiên mock | `ai_router.md` |
   | Quyết định thiết kế không hiển nhiên (đổi lib, đổi cách fallback, giữ/xoá file cũ) | thêm mục `D-0xx` mới vào cuối `DECISIONS.md` — không xoá mục cũ |
   | Luồng dữ liệu tổng thể / kiến trúc hệ thống | `overview.md` |

2. **Sửa surgically** — chỉ đoạn liên quan, giữ mỗi mục 1–2 dòng, không viết lại cả file.
3. **Bump** dòng `> Last updated:` ở đầu file đã sửa thành ngày hiện tại.
4. **Canonical ownership**: mỗi sự thật sống ở đúng 1 file — nếu thấy thông tin đã có ở file
   khác, link tới đó thay vì copy lại (vd. `ai_router.md` link tới
   `GUIDE_FRONTEND_BACKEND.md`, không lặp schema).
5. **Kiểm tra khớp `embed_type`**: `grep "embed_type" frontend/ai_router.py` phải khớp 1-1
   với `grep "discord-embed\." frontend/custom_styles.py` (xem D-005) — nếu lệch, đây là bug
   thật, không chỉ là doc thiếu.
6. Nếu thêm/xoá skill trong `.claude/skills/`, chạy `python bundle_skills.py` để regenerate
   `skills.json`.
