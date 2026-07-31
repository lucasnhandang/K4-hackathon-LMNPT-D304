# Decision Log

> Last updated: 2026-07-31 (D-008)
> Mỗi quyết định thiết kế không hiển nhiên → thêm 1 mục `D-0xx` mới ở cuối. Không xoá mục cũ
> kể cả khi đã bị thay thế — ghi "Superseded by D-0xx" thay vào đó.

## D-001 — Frontend build bằng NiceGUI (Python), không phải web framework JS

**Vì sao:** Team build trong ~1 ngày (thời lượng hackathon). NiceGUI cho phép dựng UI
Discord-clone hoàn chỉnh (server list / channel sidebar / chat area / embed / modal) bằng
Python thuần, không cần dựng build pipeline JS riêng, và cùng ngôn ngữ với phần AI
router/backend → một người có thể chạm cả hai lớp.

**Đánh đổi:** Kiểm soát DOM/animation không tinh vi bằng React thật; toàn bộ style là CSS
thô nhúng qua `ui.add_head_html` (`custom_styles.py`) thay vì component styling chuẩn.

## D-002 — `USE_LOCAL_MOCK` làm fallback bắt buộc, không phải tuỳ chọn

**Vì sao:** `frontend/ai_router.py::call_backend_api_async` khi gọi backend thật thất bại
(timeout, lỗi kết nối, backend chưa build xong) sẽ **tự động rơi về** `classify_and_route`
(mock local) thay vì lỗi trắng màn hình. Mục tiêu: buổi demo không bao giờ đứng hình vì
backend chết — đánh đổi lấy rủi ro demo "trông như chạy AI thật" trong khi thực ra đang
chạy mock nếu quên set `USE_LOCAL_MOCK=false` hoặc backend down giữa demo.

**Hệ quả:** Trước CP5/CP6, phải xác nhận backend thật đang chạy và log rõ nhánh nào được
gọi (xem `[Warning] Không thể kết nối Backend API` trong log) để không vô tình demo mock
mà tưởng là thật — vi phạm luật "≥1 lời gọi AI chạy thật".

## D-003 — `index.html` (root) và `codebase/index.html` là bản tĩnh CP2 cũ, không phải nguồn hiện hành

**Vì sao:** Trước khi có app NiceGUI, team dựng 2 bản HTML/CSS tĩnh (`index.html` 1270
dòng, `codebase/index.html` 847 dòng — 2 file **khác nhau**, không phải bản sao của nhau)
để demo tại Checkpoint 2 (tiêu đề `Prototype CP2 Demo`). Sau khi build xong
`frontend/main.py`, `codebase/app.py` đã chuyển sang import trực tiếp
`frontend/main.py` — 2 file `index.html` không còn được entrypoint nào chạy.

**Hệ quả:** Không sửa 2 file `index.html` này cho tính năng mới — chúng sẽ không xuất hiện
trong bản demo NiceGUI. Giữ lại làm tài liệu tham khảo lịch sử; nếu dọn repo trước khi nộp
bài, cân nhắc xoá hoặc note rõ trong `README.md` nhóm rằng đây là artifact cũ.

## D-004 — 4 trạng thái backend map cứng 1-1 với 4 lớp "chỗ khó" trong đề bài

**Vì sao:** `01-de-bai.md` yêu cầu tự xác định 4 lớp chỗ khó (nguồn sự thật / mơ hồ / ngoài
phạm vi / đặc thù domain) và duyệt tại các mốc. Để tránh trôi giữa "taxonomy trên giấy" và
"code thực chạy", `ai_router.py::transform_backend_response_to_ui` chốt cứng 4 nhánh
(`need_clarification`, `resolved`, `escalated`, `out_of_scope`) — xem bảng map đầy đủ ở
`overview.md`.

**Hệ quả:** Thêm trạng thái backend thứ 5 (vd. tách riêng lớp ④ "đặc thù domain") **bắt
buộc** đồng bộ cả 3 nơi: `ai_router.py` (nhánh transform mới) + `custom_styles.py`
(`.discord-embed.<type>-embed` mới) + bảng trong `overview.md`. Thiếu 1 trong 3 → style vỡ
hoặc doc sai (xem skill `arch-doc-sync`).

## D-005 — Embed thiếu style rơi về mặc định thay vì báo lỗi

**Quan sát:** `ai_router.py` trả `embed_type: "muted-embed"` cho `OUT_OF_SCOPE`, nhưng CSS
gốc chưa từng định nghĩa `.discord-embed.muted-embed` — NiceGUI/CSS không báo lỗi, chỉ âm
thầm dùng border màu brand mặc định của `.discord-embed`. Đã bổ sung class này trong
`custom_styles.py` (2026-07-31, cùng đợt hoàn thiện CSS v2).

**Vì sao ghi lại:** Đây là failure mode dễ tái diễn — thêm `embed_type` mới trong
`ai_router.py` mà quên thêm CSS tương ứng sẽ không có cảnh báo nào, chỉ lộ ra khi nhìn
bằng mắt. Khi thêm `embed_type` mới, luôn `grep "embed_type" frontend/ai_router.py` rồi đối
chiếu với `grep "discord-embed\." frontend/custom_styles.py` để đảm bảo khớp 1-1.

## D-006 — Lời gọi AI thật đặt ở `codebase/backend/llm_client.py`, ngoài `chatbot_tools/`, chỉ polish câu trả lời đã có căn cứ

**Bối cảnh:** Backend thật (merge vào `fe` qua commit "noi backend voi frontend") không có
lời gọi AI/LLM nào — toàn bộ intent classification (regex/normalize tiếng Việt), retrieval
(BM25), và response generation (template tiếng Việt cứng) đều rule-based. `.env.example` có
sẵn biến `OPENROUTER_*` nhưng không nơi nào trong code dùng tới. Rủi ro không đạt luật chung
"mọi mức prototype đều bắt buộc ≥1 lời gọi AI chạy thật".

**Quyết định:**
- Thêm `codebase/backend/llm_client.py` (module mới, **ngoài** `chatbot_tools/`) gọi
  OpenRouter Chat Completions bằng `urllib` (stdlib, không thêm dependency cho lời gọi HTTP) —
  giữ đúng bất biến đã ghi trong `chatbot_tools/README.md`: *"Không cần API key hoặc package
  ngoài Python standard library"*. Chỉ thêm `python-dotenv` (để đọc `.env`, giống cách
  `frontend/ai_router.py` đã làm) vào `codebase/backend/requirements.txt`.
- Trong `server.py::chat()`, chỉ gọi `llm_client.polish_response(...)` khi
  `route == "ANSWER"` **và** đã có `citations` (đúng nhánh `resolved`/`direct_answer` —
  câu trả lời đã có căn cứ từ tool). Không áp dụng cho greeting/clarify/escalate.
- Prompt hệ thống trong `llm_client.py` chỉ cho phép **diễn đạt lại**, cấm tuyệt đối thêm
  fact mới ngoài `original_text` + `citations` truyền vào — giữ nguyên bất biến taxonomy lớp
  ① (nguồn sự thật, AI không được bịa).
- `is_configured()` trả `False` nếu key/model vẫn là placeholder `.env.example`
  (`replace_with_...`) — không gọi mạng vô ích khi chưa cấu hình.
- `polish_response()` **không bao giờ raise** — mọi lỗi (thiếu key, network, timeout, JSON lỗi)
  bắt hết và trả `None`; `server.py` fallback về `response` gốc của orchestrator. Cùng triết
  lý "AI layer không được làm sập demo" như `USE_LOCAL_MOCK` ở D-002.
- Trạng thái polish (`success` / `not_configured` / `error`) được thêm vào `tracepath` như 1
  tool entry (`🤖 OpenRouter LLM Writer`) — để việc có/không gọi AI thật là **quan sát được**
  từ response, không phải side effect âm thầm.

**Đánh đổi:** Chỉ nhánh `DIRECT_ANSWER` được polish — `AMBIGUOUS`/`NO_SOURCE_ESCALATE` vẫn
100% template cứng. Đủ để thoả luật "≥1 lời gọi AI chạy thật" khi có key thật, nhưng chưa
polish toàn bộ trải nghiệm; nếu muốn mở rộng, cân nhắc kỹ vì greeting/escalate không có
`citations` để ràng buộc model — rủi ro bịa cao hơn.

**Đã test:** `unittest discover -s tests` (82 test, không đổi vì không chạm `chatbot_tools/`);
`is_configured()==False` với `.env` mới copy từ `.env.example` (placeholder); `polish_response`
với key giả → bắt được `HTTPError 401`, trả `None`, không crash request.

**Chưa đồng bộ:** `PROJECT_MAP.md`/`overview.md`/`ai_router.md` vẫn mô tả backend theo trạng
thái *trước* commit "noi backend voi frontend" (viết lúc backend chưa tồn tại) — cần một lượt
`arch-doc-sync` riêng để khớp lại toàn bộ `codebase/backend/` (orchestrator, tools, discord
collector), việc đó lớn hơn phạm vi D-006 này.

## D-007 — Bug: fallback backend-lỗi từng crash vì `print()` tiếng Việt trên Windows, làm UI treo vô hạn

**Triệu chứng quan sát được:** user gửi câu hỏi trên UI Discord-clone, bot hiện "Trợ lý Kute
đang gõ câu trả lời..." rồi **treo mãi**, không bao giờ có phản hồi (kể cả fallback).

**Nguyên nhân gốc (2 lớp cộng dồn):**
1. `frontend/ai_router.py::call_backend_api_async` chờ backend tối đa `timeout=8.0` (httpx),
   nhưng backend gọi LLM thật (D-006) có thể mất tới ~6-7s (network + OpenRouter latency) +
   xử lý orchestrator — thường xuyên vượt 8s → `httpx.ReadTimeout`.
2. Nhánh `except Exception as e:` định fallback về `classify_and_route` (mock), nhưng dòng
   `print(f"[Warning] ... {e}. Đang chuyển về Local AI Router.")` chứa dấu tiếng Việt lại tự
   crash với `UnicodeEncodeError: 'charmap' codec can't encode...` vì Windows console/log file
   mặc định encode `cp1252` (không phải UTF-8, không encode được dấu tiếng Việt). Exception mới
   này đè lên exception gốc → hàm `call_backend_api_async` không bao giờ return →
   `DiscordChatApp.process_bot_reply` không bao giờ chạy tới đoạn `self.is_typing = False` +
   `update_chat_ui()` → bong bóng "đang gõ..." treo vĩnh viễn. NiceGUI nuốt exception trong
   `ui.timer` callback (chỉ log ra console backend của uvicorn/nicegui, không crash cả app),
   nên lỗi này **không có traceback nào hiện trên UI** — chỉ thấy được trong log tiến trình.

**Quyết định sửa:**
- `frontend/main.py`: `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` +
  tương tự cho `stderr`, chạy **trước** mọi import khác ở đầu file — sửa tận gốc cho toàn bộ
  app (mọi `print()` tiếng Việt trong tương lai đều an toàn), không vá riêng lẻ từng chỗ gọi
  `print()`.
- `frontend/ai_router.py`: tăng `httpx.AsyncClient(timeout=...)` từ `8.0` lên `15.0` — đủ dư
  so với timeout 6s phía backend (`llm_client._TIMEOUT_SECONDS`) cộng overhead mạng/FastAPI,
  giảm tần suất rơi vào nhánh fallback một cách không cần thiết.

**Đã test:** mô phỏng backend không phản hồi (`BACKEND_URL` trỏ tới cổng chết) sau khi sửa —
`print()` chạy được, hàm trả về đúng payload `AMBIGUOUS` từ mock, không crash, không treo.

**Vì sao ghi lại:** Đây là failure mode nguy hiểm nhất trong 3 bug đã ghi (D-005, D-006, D-007)
vì nó **im lặng hoàn toàn** — không exception nào lộ ra UI, không request nào trả lỗi HTTP, chỉ
đơn giản là treo. Nếu sau này thêm `print()`/`logger` nào in text tiếng Việt ở bất kỳ module
nào chạy trên Windows mà chưa qua `main.py` (vd. một script CLI/test riêng), khả năng cao vẫn
dính lỗi encoding này — áp dụng `sys.stdout.reconfigure(encoding="utf-8")` ở đầu entrypoint đó.

## D-008 — Deploy lên Render, không phải Vercel — NiceGUI cần tiến trình sống lâu + WebSocket

**Vì sao không phải Vercel:** Vercel chỉ chạy serverless function (mỗi request 1 lần, không
tiến trình sống lâu, model không hợp WebSocket giữ-state kiểu NiceGUI).
`frontend/main.py` (NiceGUI) giữ toàn bộ state hội thoại (`DiscordChatApp.messages`) trong bộ
nhớ 1 tiến trình Python chạy liên tục, giao tiếp UI real-time qua WebSocket — **không thể**
chạy trên serverless dưới bất kỳ hình thức nào, không phải vấn đề cấu hình. Ngay cả
`codebase/backend/server.py` (FastAPI) cũng khó hợp Vercel serverless nếu không sửa: state
`_session_clarifications` (dict Python trong bộ nhớ, giữ ngữ cảnh hỏi-lại-làm-rõ nhiều lượt)
sẽ mất giữa các lần gọi vì mỗi request serverless có thể rơi vào instance khác nhau.

**Quyết định:** Deploy cả 2 service lên **Render** (free tier, hỗ trợ tiến trình chạy liên tục
+ WebSocket, có blueprint `render.yaml` deploy nhiều service từ 1 repo). Không đổi kiến trúc
code để hợp Vercel (không đáng — sẽ phải viết lại frontend bằng framework web thật, bỏ
NiceGUI, và làm `_session_clarifications` stateless).

**Thay đổi code cần thiết:**
- `codebase/backend/server.py`: đổi `port=8000` hardcode → đọc từ `os.environ.get("PORT",
  8000)` — PaaS gán cổng động qua biến `PORT`, hardcode sẽ làm service không thể truy cập
  được từ ngoài. `frontend/main.py` đã đọc `PORT` từ trước, không cần sửa.
- `render.yaml` (root repo): định nghĩa 2 service (`rootDir: codebase/backend` và
  `rootDir: frontend`), mỗi service `pip install -r requirements.txt` rồi chạy đúng entrypoint
  (`python server.py` / `python main.py`). `OPENROUTER_API_KEY` đánh dấu `sync: false` — Render
  hỏi nhập trong dashboard, không bao giờ nằm trong file commit.

**Việc thủ công còn lại sau lần deploy đầu:** Render không hỗ trợ nối chuỗi URL của service
khác ngay trong `render.yaml`, nên `BACKEND_URL` của frontend service phải **tự tay** cập nhật
sau khi biết URL thật của backend service (deploy backend trước, copy URL, dán vào biến
`BACKEND_URL` của frontend kèm `/api/v1/chat`, redeploy frontend).

**Đánh đổi đã biết:** Free tier của Render tự **spin down sau ~15 phút không hoạt động**, lần
gọi đầu tiên sau đó mất tới ~50s để tỉnh lại — cần "đánh thức" cả 2 service (mở URL 1 lần)
trước buổi demo, đừng để BTC bấm vào lúc service đang nguội.
