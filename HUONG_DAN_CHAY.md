# Hướng dẫn khởi chạy dự án (Backend + Frontend)

Dự án gồm 2 service chạy độc lập, mỗi cái có venv Python riêng:

| Service | Thư mục | Cổng mặc định | Vai trò |
|---|---|---|---|
| Backend | `codebase/backend/` | `8000` | FastAPI — orchestrator, tools, (tuỳ chọn) gọi OpenRouter |
| Frontend | `frontend/` | `8080` | NiceGUI — giao diện Discord-clone |

Frontend gọi sang backend qua HTTP (`BACKEND_URL`, mặc định
`http://localhost:8000/api/v1/chat`) — nên **bật backend trước, frontend sau**. Nếu lỡ bật
ngược, frontend không lỗi, chỉ là tin nhắn đầu tiên sẽ không có phản hồi AI thật cho tới khi
backend lên.

Chi tiết kiến trúc/luồng dữ liệu: xem `CLAUDE.md` + `project_setup/architecture/`. File này
chỉ nói **cách chạy**.

---

## 1. Cài đặt lần đầu (chỉ cần làm 1 lần, hoặc sau khi xoá `.venv`)

Mở PowerShell, đứng ở thư mục gốc `K4-hackathon-LMNPT-D304`.

**Backend:**

```powershell
cd codebase\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Frontend** (cửa sổ PowerShell khác, hoặc `cd` lại về gốc trước):

```powershell
cd frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Cấu hình `.env` cho backend (tuỳ chọn — có AI thật hay không)

`codebase/backend/.env` (copy từ `.env.example` nếu chưa có) quyết định backend có gọi AI
thật (OpenRouter) hay chỉ trả lời bằng template có sẵn:

```env
OPENROUTER_API_KEY=sk-or-v1-...        # lấy tại https://openrouter.ai/keys
OPENROUTER_MODEL=openai/gpt-oss-20b:free   # hoặc model free khác — xem openrouter.ai/models
```

Không điền / để nguyên placeholder `replace_with_...` → backend vẫn chạy bình thường, chỉ là
câu trả lời không được LLM diễn đạt lại (tracepath sẽ hiện `not_configured`) — **không lỗi,
không cần sửa gì thêm**.

Frontend **không cần** file `.env` — mặc định đã đúng cho chạy local (`BACKEND_URL=http://localhost:8000/api/v1/chat`,
`USE_LOCAL_MOCK=false`). Chỉ tạo `frontend/.env` nếu muốn đổi cổng hoặc trỏ sang backend khác.

## 3. Chạy hằng ngày

Mở **2 cửa sổ PowerShell riêng** (mỗi server chạy nền, chiếm 1 cửa sổ — đừng đóng khi đang
dùng):

**Cửa sổ 1 — Backend:**

```powershell
cd codebase\backend
.\.venv\Scripts\Activate.ps1
python server.py
```

Thấy dòng `Uvicorn running on http://0.0.0.0:8000` là backend đã lên.

**Cửa sổ 2 — Frontend:**

```powershell
cd frontend
.\.venv\Scripts\Activate.ps1
python main.py
```

Thấy dòng `NiceGUI ready to go on http://localhost:8080` là xong. Mở trình duyệt:
**http://localhost:8080**

## 4. Kiểm tra backend còn sống (không cần mở trình duyệt)

```powershell
curl http://localhost:8000/health
```

Trả về `{"status":"ok"}` là backend ổn. **Mở `http://localhost:8000/` (không có `/health`) sẽ
báo lỗi 404 "Not Found" — đây là bình thường**, vì backend không có trang chủ, chỉ có
`/health` và `/api/v1/chat`.

## 5. Dừng server

`Ctrl + C` trong cửa sổ PowerShell tương ứng.

## 6. Lỗi thường gặp

**`[Errno 10048]` / `address already in use` khi bật server:** cổng đó đang bị 1 tiến trình cũ
chiếm (thường là quên tắt lần chạy trước). Tìm và tắt:

```powershell
netstat -ano | findstr ":8000"    # hoặc ":8080" cho frontend
taskkill /PID <số_PID_ở_cột_cuối> /F
```

rồi chạy lại bước 3.

**Sửa code xong không thấy đổi trên trình duyệt:** cả 2 server không tự reload khi sửa file —
phải `Ctrl+C` rồi chạy lại `python server.py` / `python main.py`.

**Backend báo lỗi liên quan `OPENROUTER_API_KEY`/gọi mạng thất bại:** không sao, đây là lời
gọi AI tuỳ chọn — backend tự động rơi về câu trả lời mẫu, không ảnh hưởng phần còn lại. Xem
`project_setup/architecture/DECISIONS.md` D-006.

## 7. Deploy public (không bắt buộc cho hackathon)

Đề bài không yêu cầu deploy. Nếu muốn có link demo public: xem `render.yaml` ở gốc repo +
`project_setup/architecture/DECISIONS.md` D-008 (vì sao dùng Render, không phải Vercel).
