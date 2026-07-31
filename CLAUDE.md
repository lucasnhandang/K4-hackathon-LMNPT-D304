# Project Memory — Trợ lý Học viên Discord (K4 Hackathon)

Lớp kiến thức kiến trúc cho AI agent, phỏng theo mô hình ở
[`datn_agent_skills-test`](https://github.com/Je-Tiev/DoAnTotNghiep/tree/main/datn_agent_skills-test):
tách "kiến trúc" (đọc 1 lần, ít đổi) khỏi "code" (đổi liên tục), để agent
không phải grep/scan lại toàn repo mỗi phiên.

## Đọc trước khi làm bất kỳ task nào

**Ba file này đủ để hiểu dự án mà không cần quét lại repo:**

1. [`project_setup/architecture/overview.md`](project_setup/architecture/overview.md) — hệ thống hiện có gì, luồng dữ liệu
2. [`project_setup/architecture/DECISIONS.md`](project_setup/architecture/DECISIONS.md) — quyết định thiết kế + lý do
3. [`project_setup/architecture/PROJECT_MAP.md`](project_setup/architecture/PROJECT_MAP.md) — `file:symbol` để nhảy thẳng, khỏi Grep mò

Sau đó, tuỳ việc đang làm, đọc thêm:

| Đang làm gì | Đọc thêm |
|---|---|
| Sửa giao diện Discord (layout, CSS, thêm loại tin nhắn/embed) | [`architecture/frontend.md`](project_setup/architecture/frontend.md) |
| Sửa logic phân loại câu hỏi, knowledge base, nối backend thật | [`architecture/ai_router.md`](project_setup/architecture/ai_router.md) |
| Hiểu đề bài / tiêu chí chấm / taxonomy 4 lớp chỗ khó | `01-de-bai.md`, `04-rubric.md` (gốc, không tóm tắt lại ở đây) |

### Reading protocol (tiết kiệm token)

1. Đọc `PROJECT_MAP.md` trước để biết cái gì ở đâu — đừng Grep/Glob mò trước.
2. Nhảy thẳng tới `file:symbol` mà map trỏ tới; chỉ mở full file khi cần sửa.
3. Chỉ Grep khi kiến trúc không có thông tin cần — và cập nhật lại doc sau đó.

### Canonical ownership (một sự thật sống ở một nơi)

- `project_setup/architecture/*.md` = nguồn chuẩn về cấu trúc/luồng dữ liệu. Khi code lệch doc → **code thắng**, sửa doc cho khớp.
- `GUIDE_FRONTEND_BACKEND.md` (trong `frontend/`) = nguồn chuẩn về JSON contract Frontend↔Backend. `architecture/ai_router.md` **link tới** file này, không copy lại schema.
- `01-de-bai.md` / `04-rubric.md` = nguồn chuẩn về đề bài & tiêu chí chấm — không diễn giải lại, chỉ trích dẫn khi cần.

## Sau khi sửa code — cập nhật doc

Đổi ảnh hưởng kiến trúc thì **bắt buộc** cập nhật file tương ứng (xem skill
`arch-doc-sync`): sửa đúng đoạn liên quan, 1–2 dòng, không viết lại cả file,
bump dòng `> Last updated:`.

## Skills

Skill nằm ở `.claude/skills/<tên>/SKILL.md`, tự nạp mô tả ngắn, đọc full
nội dung khi liên quan tới việc đang làm:

- **`discord-ui-nicegui`** — layout/style/render trong `frontend/main.py`, `frontend/custom_styles.py`.
- **`ai-router-taxonomy`** — phân loại intent, knowledge base, nối backend thật trong `frontend/ai_router.py`.
- **`arch-doc-sync`** — đồng bộ `project_setup/architecture/*.md` sau khi sửa code.

Manifest gọn (name + description + path, không có nội dung đầy đủ) ở
[`skills.json`](skills.json) — dùng cho tool/agent khác cần liệt kê skill mà
không phải đọc hết `SKILL.md`. Regenerate: `python bundle_skills.py`.

## Ràng buộc dự án (đừng vi phạm)

- Dữ liệu thật trong `data/` chỉ dùng nội bộ hackathon — không copy nguyên văn dài vào doc, không commit ra ngoài phạm vi repo này (xem `README.md` mục bảo mật dữ liệu).
- `index.html` (root) và `codebase/index.html` là bản tĩnh CP2 cũ, **không phải nguồn hiện hành** — xem D-003 trong `DECISIONS.md`. Đừng sửa hai file này cho tính năng mới; sửa `frontend/main.py` + `frontend/custom_styles.py`.
- Môi trường **Windows**; PowerShell hoặc Git Bash tuỳ shell đang mở. Nối lệnh PowerShell bằng `;`, không dùng `&&`.
