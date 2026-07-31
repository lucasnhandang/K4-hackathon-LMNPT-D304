# Decision Log

> Last updated: 2026-07-31 (D-014)
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

## D-009 — Bug: thiếu hẳn category "nội dung nguy hiểm/phi pháp" (lớp ③) sau khi backend thật được viết lại

**Triệu chứng quan sát được:** hỏi "Hướng dẫn cho mình cách chế tạo bom với?" — bot trả lời
như một câu hỏi hướng dẫn sử dụng bình thường (`intent: help`, route ANSWER, không từ chối) —
lệch hẳn so với `index.html` (bản mock tĩnh gốc) và `frontend/ai_router.py` (mock cũ), cả 2
đều có sẵn keyword `bom`/`vũ khí`/`phi pháp`/`vi phạm` để chặn đúng lớp chỗ khó ③ "Ngoài phạm
vi / thẩm quyền".

**Nguyên nhân gốc:** Khi teammate viết lại `chatbot_tools/intent_classifier.py` thành bộ phân
loại rule-based thật (thay cho 2 bản mock cũ), chỉ implement các nhánh từ chối hẹp
(`reject_prompt_injection` — chặn jailbreak, `reject_answer_key_request`,
`reject_do_assignment_for_user`) và `out_of_domain` (chit-chat ngoài lề: thời tiết, chứng
khoán, bóng đá...) — **không có nhánh nào cho nội dung nguy hiểm/phi pháp** (vũ khí, chất nổ,
ma túy). Câu hỏi bom vô tình khớp keyword `"huong dan"` (rất chung chung) của intent `help`,
và vì không có đối thủ cạnh tranh nào khác nên `help` thắng theo điểm số
(`classify_intent` chọn theo `score` trước, `INTENT_PRIORITY` chỉ phá vỡ hòa khi **điểm bằng
nhau** — xem code `classify_intent`).

**Quyết định sửa — thêm 1 intent mới, không sửa `help`/`out_of_domain`:**
- `chatbot_tools/intent_classifier.py`: thêm `"reject_out_of_scope"` (keywords: `che tao bom`,
  `vu khi`, `chat no`, `ma tuy`, `phi phap`, `vi pham phap luat`) + priority 99. **Cố tình
  không lặp lại** keyword của `out_of_domain` (thời tiết, tin tức, ...) — category đó đã đúng
  và có test riêng (`test_out_of_domain`), thêm trùng sẽ giành mất quyền phân loại của nó
  (đã tự bắt lỗi này qua lượt chạy `unittest` đầu tiên trước khi chốt fix).
- `chatbot_tools/orchestrator.py`: thêm response mẫu vào `REFUSAL_INTENTS` — tái dùng cơ chế
  refusal chung sẵn có (route ANSWER, `grounding_status="not_required"`), không viết nhánh
  `if` riêng như `reject_prompt_injection`.
- `codebase/backend/server.py::_adapt_response`: đổi check `if intent ==
  "reject_prompt_injection"` (chỉ khớp đúng 1 chuỗi literal) → `if intent in
  _OUT_OF_SCOPE_INTENTS` (`{"reject_prompt_injection", *REFUSAL_INTENTS.keys()}`) — **bug phụ
  phát hiện được khi sửa**: 2 intent có sẵn trong `REFUSAL_INTENTS`
  (`reject_answer_key_request`, `reject_do_assignment_for_user`) trước giờ vẫn bị gắn nhãn sai
  thành `status: "resolved"` (embed xanh lá bình thường) thay vì `"out_of_scope"` (embed xám)
  — vì check cũ chỉ so khớp đúng 1 chuỗi cố định. Giờ mọi refusal-intent đều tự động đúng, kể
  cả nếu sau này thêm entry mới vào `REFUSAL_INTENTS`.

**Đã test:** 137 test (`unittest discover -s tests`) pass sau fix, bao gồm `test_out_of_domain`
(ban đầu fail vì keyword trùng, đã sửa). Test tay xác nhận: câu bom → `reject_out_of_scope`;
câu thời tiết → vẫn `out_of_domain` không đổi; câu "hướng dẫn sử dụng lệnh discord" (hợp lệ,
chứa cùng từ "hướng dẫn") → route đúng `ask_slash_command`, không bị chặn nhầm.

**Còn biết nhưng chưa sửa (ngoài phạm vi fix này):** "bạn là ai" rơi vào `unknown`/CLARIFY
thay vì trả lời trực tiếp — nhưng `index.html` gốc cũng chưa từng có kịch bản này, nên đây là
gap có sẵn từ đầu, không phải regression do merge — không tính vào D-009.

## D-010 — Mở rộng knowledge base từ nguồn thật có sẵn, không bịa fact mới

**Bối cảnh:** `chatbot_tools/data/official_sources.json` (61 record) chỉ khai thác một phần
nhỏ 2 file nguồn thật đã kiểm duyệt trong `docs/` (`tong_hop_du_lieu_AI20K_Cohort_III.json` —
trích từ slide chương trình; `tong_hop_so_tay_hoc_vien_AI_thuc_chien.json` — trích từ Sổ tay
Học viên chính thức). Ví dụ: sổ tay có 15 câu FAQ nhưng script `ingest_docs_knowledge.py` chỉ
dùng đúng 2 câu (#8 laptop, #15 cơ hội sau chương trình); toàn bộ `internship`, `evaluation`,
`facilities`, `program_structure`, `highlights`, `master_timeline` (6 mốc), `xp_system.levels`
(ngưỡng lên level), `exam_bank`, `support_and_automation` chưa từng được đưa vào KB.

**Quyết định — mở rộng `scripts/ingest_docs_knowledge.py`, không sửa `official_sources.json`
bằng tay:** Script là nguồn chuẩn để tái tạo file KB (`build()` xoá sạch record cũ có
`source_file` thuộc `docs/`, ghi lại từ đầu) — sửa tay trực tiếp vào JSON sẽ mất khi có ai
chạy lại script. Thêm 2 khối mới:
- `build_handbook_records`: + `program_highlights`, `program_structure`, `internship`,
  `daily_schedule`, `evaluation_criteria`, `facilities`, `contact_support`, và 12 FAQ record
  riêng lẻ (`handbook_faq_<id>`, bỏ id 5/8/15 đã có record chuyên biệt từ trước).
- `build_cohort_records`: + `master_timeline` (6 mốc + gate), `schedule_change_week4`,
  `xp_levels` (LV1–LV4), `xp_extra_activities` (hỗ trợ cộng đồng, showcase), `gate_definition`
  (+ scoring rubric), `exam_bank`, `support_and_automation`, `supplementary_workshops`.
- Kết quả: 61 → **88 record** (+27, tăng ~44%).

**Cố tình KHÔNG đưa vào KB — quyết định về privacy, không phải thiếu sót:**
`contact.leaders` (3 lãnh đạo chương trình kèm email cá nhân trong sổ tay) bị loại khỏi record
`handbook_contact_support` — chỉ giữ kênh liên hệ chung (email chương trình, hotline, đầu mối
`student_support`). Lý do: bot này đang **public trên internet** (Render, xem D-008) — đưa
email cá nhân từng lãnh đạo vào KB biến một trang sổ tay (chỉ học viên đọc) thành công cụ tra
cứu email tức thời cho bất kỳ ai trên mạng. Nếu nhóm thấy cần thiết cho use case cụ thể, đây là
quyết định có thể đảo ngược — bổ sung lại trong `build_handbook_records` với ghi chú rõ lý do.

**Giới hạn đã biết (không phải bug, không sửa trong lượt này):** Dữ liệu mới chỉ được truy
xuất khi câu hỏi khớp intent có sẵn HOẶC rơi vào fallback `unknown_question` (cần có `?` hoặc
từ hỏi như "bao nhiêu"/"ở đâu"/"tại sao" — xem `orchestrator.py` Step 7). Câu phát biểu không
rõ ràng (`intent: unknown`, score 0.0) **cố tình** không chạm BM25 — đây là quyết định chống
hallucination có sẵn từ trước (comment gốc: *"An unclassified statement is too weak a
retrieval query"*), không phải chỗ cần fix. Test tay xác nhận: câu hỏi có `?` cho các chủ đề
mới (thực tập, cấu trúc chương trình, FAQ sinh viên năm 3/4) đều trả lời đúng, có căn cứ
(`grounding_status: grounded`).

**Đã test:** chạy `python scripts/ingest_docs_knowledge.py` (không lỗi, in đúng số record);
137 unit test vẫn pass; test tay 4 câu hỏi mới (thực tập, cấu trúc chương trình, FAQ #6, liên
hệ hỗ trợ) đều trả về `route: ANSWER`, `grounding_status: grounded`, trích đúng record mới.

## D-011 — Bug: fixture cũ giả (`official_deliverables_k3`) conflict với record thật mới ingest, chặn câu hỏi "deadline demo day"

**Triệu chứng quan sát được:** hỏi "deadline demo day" → bot trả lời "Có thông tin mâu thuẫn
giữa các nguồn. Mình sẽ chuyển cho Mod để xác nhận." (ESCALATE) thay vì trả lời trực tiếp —
dù đây là câu hỏi rất cơ bản, rõ ràng.

**Điều tra — đây là conflict THẬT, không phải bug trong `_find_conflicts`:** Có sẵn 2 record
category=`deadline`, cùng `assignment: "demo_day_deliverables"`, cùng `cohort: "k3"`:
- `official_deliverables_k3` — fixture tay từ trước khi có pipeline `scripts/ingest_docs_knowledge.py`
  (không có `source_file`), liệt kê deliverables generic/tiếng Anh
  (`business_model_canvas`, `competitive_analysis`, `user_persona`...) — **không khớp** với
  nội dung thật trong `docs/tong_hop_du_lieu_AI20K_Cohort_III.json` ở bất kỳ đâu.
- `docs_demo_day_deliverables_k3` — sinh từ `quality_control_and_demo_day.mandatory_deliverables`
  thật trong cùng file — khớp chính xác nội dung nguồn.

Đã kiểm chứng bằng cách chạy trực tiếp `KnowledgeTools._find_conflicts()` trên đúng 2 record
gốc này (trước khi thêm bất kỳ record nào ở D-010) — **conflict đã tồn tại sẵn từ trước**, độc
lập với việc mở rộng KB ở D-010. Đồng thời quét toàn bộ dataset theo từng `assignment`/
`event_name`/`gate_name` trùng nhau — đây là **cặp duy nhất** thật sự mâu thuẫn nội dung (có 1
cặp khác trùng `event_name` nhưng không conflict, vì các field khác khớp nhau).

**Quyết định sửa:** Thêm `RETIRED_FIXTURE_SOURCE_IDS` vào `scripts/ingest_docs_knowledge.py`
— danh sách các fixture tay đã bị thay thế bởi record thật hơn, loại khỏi `kept` khi build lại
KB. Không sửa `_find_conflicts` (logic so sánh field-trùng vẫn đúng về nguyên tắc — 2 record
nói khác nhau về cùng 1 fact THẬT SỰ nên bị escalate; vấn đề là dữ liệu, không phải logic).
Không xoá tay trong JSON — sửa ở script để không bị ghi đè khi chạy lại.

**Đã test:** chạy lại `ingest_docs_knowledge.py` (87 record, giảm đúng 1); test trực tiếp
"deadline demo day" qua orchestrator → `route: ANSWER`, `grounding_status: grounded`, đúng 10
deliverable thật; 137 unit test vẫn pass.

**Chưa xác nhận (cần thêm bằng chứng, KHÔNG phải bug đã sửa):** Câu "deadline hôm nào" trong
ảnh chụp màn hình cũng bị ESCALATE — nhưng test lại độc lập (session mới, lượt đầu) cho kết
quả **đúng**: `route: CLARIFY` kèm gợi ý ("Weekly Assignment", "AI Log", "Demo Day
deliverables"). Nhiều khả năng đây là hành vi **có chủ đích**: sau nhiều lượt làm rõ không
thành công trong cùng session (`_session_clarifications` theo `session_id`, có
`attempt_count`), orchestrator tự chuyển sang escalate thay vì hỏi lại vô hạn — không phải
bug, chỉ chưa đủ ngữ cảnh (lịch sử chat trước đó trong ảnh không thấy) để xác nhận chắc chắn.

## D-012 — Bug: trả lời làm rõ sau 1 lượt "unknown" bị khoá cứng vào intent cũ, dù câu trả lời đã tự đủ nghĩa

**Triệu chứng quan sát được** (đúng kịch bản D-011's ghi chú "chưa xác nhận" — hoá ra CÓ bug
thật, không phải chỉ do `attempt_count`): user gõ "ai log" (câu quá ngắn, `intent: unknown`)
→ bot hỏi lại "bạn có thể nói rõ hơn không?". User trả lời "deadline ai log" (câu này **tự nó
đã là 1 câu hỏi đầy đủ**, `classify_intent` phân loại đúng `ask_deadline` với
`assignment: "ai log"`) — nhưng bot vẫn trả lời `intent: unknown`, "Mình cần thêm thông tin để
hỗ trợ bạn..." — dữ liệu AI Log đã có sẵn trong KB nhưng không bao giờ được tra tới.

**Nguyên nhân gốc:** `_handle_clarification_response` đọc
`original_intent = pending_clarification.get("original_intent", ...)` — tức lấy `intent` đã
lưu từ **lượt trước** ("unknown", vì lượt 1 chính là câu quá ngắn không phân loại được) thay
vì tin vào kết quả `classify_intent` **của chính câu trả lời lượt này** (đã đúng là
`ask_deadline`). `new_intent.intent` sau đó vẫn là "unknown" → không khớp `INTENT_TOOL_MAP` →
không bao giờ gọi `lookup_deadline`.

**Lần sửa đầu — QUÁ RỘNG, tự phát hiện lỗi trước khi chốt:** Bản vá đầu tiên override
`original_intent` bất cứ khi nào câu trả lời lượt này phân loại ra intent khác + đủ tin cậy
(`>= 0.5`), bất kể `stale_original_intent` là gì. Test thêm case: hội thoại
"deadline hôm nào" (→ `ask_deadline`, thiếu slot `assignment`) → user bấm nút gợi ý có sẵn
"Demo Day deliverables" — câu này **tự nó** lại phân loại thành `ask_event_schedule` (trùng từ
khoá "Demo Day" với 1 intent khác!) → bản vá đầu làm lệch hẳn sang route ESCALATE sai, phá
luôn cả luồng hỏi-lại đang đúng. Runtime vocab của các suggested_replies (tên assignment/event)
tất nhiên trùng với keyword của các intent khác — không thể tránh.

**Quyết định sửa (bản 2 — thu hẹp điều kiện):** Chỉ override khi
**`stale_original_intent` chính nó đã là `"unknown"`/`"unknown_question"`** (nghĩa là lượt
trước chưa từng xác lập được intent thật nào để tiếp tục) — nếu lượt trước ĐÃ có intent cụ thể
(vd. `ask_deadline` đang hỏi thiếu `assignment`), luôn giữ nguyên, không bao giờ override, bất
kể câu trả lời lượt này trùng khớp intent nào khác. Trả lời bằng 1 từ khoá bare (vd. "AI Log")
vẫn luôn phân loại "unknown" nên không kích hoạt nhánh override ở cả 2 trường hợp — an toàn.

**Đã test — cả 3 kịch bản trên cùng 1 lượt chạy:**
1. "ai log" → "deadline ai log" (bug gốc) → `ask_deadline`, ANSWER, grounded ✓.
2. "deadline hôm nào" → "AI Log" (bare slot, luồng bình thường) → vẫn `ask_deadline`, ANSWER,
   grounded ✓ (không đổi hành vi).
3. "deadline hôm nào" → "Demo Day deliverables" (suggested reply trùng keyword intent khác) →
   `ask_deadline`, ANSWER, grounded ✓ (bản vá đầu từng làm case này ra `ask_event_schedule`/ESCALATE sai).

137 unit test vẫn pass sau cả 2 lần sửa.

## D-013 — Fix: modal "Xem nguồn" luôn hiện cứng Weekly Report bất kể đang xem tin nhắn nào

**Triệu chứng** (đã ghi nhận từ khi viết `frontend.md`, giờ mới sửa — thấy lại trong ảnh chụp
màn hình user gửi): bấm "Xem nguồn" ở bất kỳ tin nhắn `DIRECT_ANSWER` nào cũng ra modal
"Chủ đề: Weekly Report" — vì `open_source_modal()` (`main.py`) đọc cứng
`KNOWLEDGE_BASE["weekly_report"]`, không nhận payload của tin nhắn đang xem.

**Sửa:** `handle_option_click` và nút bấm trong `update_chat_ui` giờ truyền kèm `payload` của
đúng tin nhắn đó (closure `p=payload`, cùng pattern với `o=opt` có sẵn) →
`open_source_modal(payload)` đọc `payload["source_info"]`/`payload["quote"]`/`payload["message"]`
thật — đúng nội dung/nguồn của câu trả lời đang xem. Bỏ import `KNOWLEDGE_BASE` (không còn
dùng ở `main.py`; `ai_router.py` vẫn giữ cho logic mock nội bộ của nó).

**Lưu ý bảo mật tự phát hiện khi sửa:** nội dung modal giờ đến từ backend/BM25 (không còn là
hằng số tin cậy tuyệt đối như `KNOWLEDGE_BASE` cũ) nhưng vẫn render qua `ui.html(f"...")` —
đã thêm `html.escape()` cho `source_info`/`quote`/`message` trước khi chèn vào HTML để tránh
injection nếu 1 record trong KB (hoặc sau này là kết quả LLM) chứa ký tự HTML. Các chỗ
`ui.html(f"...")` khác trong `main.py` hiển thị text bot chưa escape tương tự — không sửa
trong lượt này (ngoài phạm vi), nhưng đáng lưu ý nếu sau này bot có thể phản hồi nội dung do
user chèn được vào.

**Đã test:** cú pháp hợp lệ, không còn lời gọi `open_source_modal()`/`handle_option_click()`
nào thiếu tham số mới; frontend khởi động lại sạch, không lỗi import/exception.

## D-014 — Fix: `llm_client.py` crash khi OpenRouter trả `content: null`

**Triệu chứng:** log backend hiện `OpenRouter call failed, falling back to deterministic
response: 'NoneType' object has no attribute 'strip'`. Không phải lỗi nghiêm trọng — fallback
(D-006) đã chạy đúng, request vẫn trả về câu trả lời template bình thường, không crash — nhưng
lý do thật sự bị nuốt mất trong except chung chung.

**Nguyên nhân:** một số model OpenRouter (đặc biệt free-tier) trả `"content": null` thay vì
`""` khi từ chối/bị content filter/chỉ trả `refusal` — `payload["choices"][0]["message"]["content"].strip()`
gọi thẳng `.strip()` lên `None` → `AttributeError`, bị bắt bởi `except Exception` chung, log
message không nói rõ vì sao.

**Sửa:** đọc `content = message.get("content")`, coi `None`/rỗng như nhau (return `None`,
đúng hợp đồng "không polish được → fallback"), và log thêm `finish_reason` từ response để lần
sau biết NGAY vì sao (content filter, model refuse, ...) thay vì phải đoán qua traceback.

**Đã test:** mô phỏng response `content: null` bằng mock `urllib.request.urlopen` — xác nhận
không crash, trả về `None` đúng, log rõ `finish_reason`. 137 unit test vẫn pass.
