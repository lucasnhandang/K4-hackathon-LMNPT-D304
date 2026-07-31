# Báo cáo tổng quan — Trợ lý Học viên Discord (K4 AI Thực Chiến)

> Tài liệu này tổng hợp lại dự án để báo cáo: vấn đề, giải pháp, kiến trúc, những gì đã build
> thật vs mock, và trạng thái hiện tại. Viết từ những gì xác minh được trong code + tài liệu
> nhóm đã có sẵn (`Canvas.txt`, `eval_golden_set.md`, `eval/`) — **không** thêm số liệu khảo
> sát/mining nào chưa được đo, đúng nguyên tắc nhóm đã đặt ra ("Chưa nên điền số khi chưa đo").
> Phần bằng chứng định lượng (§2) vẫn cần nhóm tự điền khi đã đo thật.

**Hướng đề bài:** B — Trợ lý Học viên (Discord), loại **Tối ưu tính năng có sẵn** (không phải
xây tính năng mới).

---

## 1. Vấn đề (Pain)

**Ai, đang làm gì, vướng đâu, hậu quả gì** (theo `Canvas.txt`):

Học viên đang học hoặc làm bài của khóa, bị kẹt và đặt câu hỏi trong Discord để tiếp tục học.
Khi câu hỏi **thiếu ngữ cảnh** hoặc **nằm ngoài phạm vi tài liệu**, trợ lý hiện tại (trước khi
tối ưu) có 2 cách xử lý đều có vấn đề:
- Trả lời theo nội dung gần nhất dù không liên quan → học viên nhận thông tin sai ngữ cảnh,
  có nguy cơ hiểu sai kiến thức.
- Lập tức tag Mod mà không giúp làm rõ → học viên mất thời gian chờ, tăng tải cho Mod một
  cách không cần thiết.

Ví dụ cụ thể (đã ẩn danh, trong `Canvas.txt`): học viên hỏi "*deadline bao nhiu z*" (thiếu
thông tin: deadline của cái gì), trợ lý trả lời thẳng deadline weekly report — sai vì không
biết học viên đang hỏi về bài nào.

## 2. Bằng chứng

> **Cần nhóm tự điền khi đã đo** — file này không bịa số liệu. Theo `Canvas.txt`, khung đo dự
> kiến:
> - Mining chatlog: đếm được bao nhiêu câu hỏi thiếu ngữ cảnh bị trả lời không liên quan hoặc
>   chuyển Mod ngay, trên tổng số câu hỏi quan sát (mẫu nháp CP1: 15/28 — **chưa xác nhận
>   bằng đo thật**).
> - Phỏng vấn nhanh học viên: bao nhiêu người từng phải hỏi lại/chờ Mod/tự tìm nguồn khác sau
>   khi trợ lý không giải quyết đúng vấn đề (mẫu nháp CP1: 4/7 — **chưa xác nhận**).
> - ≥5 ví dụ nguyên văn kèm nguồn — điền vào `eval/` hoặc `spec.md` §1 khi có.

## 3. Giải pháp — Lát cắt MỘT CÂU

> Khi một học viên hỏi trên Discord để gỡ vướng trong khóa, trợ lý quyết định câu hỏi đã đủ
> rõ và có đủ căn cứ để trả lời, cần hỏi lại hay phải chuyển Mod, giúp học viên nhận được một
> bước xử lý đáng tin cậy thay vì câu trả lời phỏng đoán.

| Thành phần lát cắt | Nội dung |
|---|---|
| Một người dùng | Học viên đang bị kẹt |
| Một công việc | Gỡ vướng để tiếp tục học |
| Một quyết định AI | Chọn trả lời / hỏi lại / chuyển Mod dựa trên độ rõ và căn cứ |
| Một kết quả | Học viên nhận được một bước xử lý đáng tin cậy |

**Mức độ tự động hoá:** Conditional automation — trợ lý tự trả lời khi câu hỏi đủ rõ **và** có
căn cứ chính thức; hỏi đúng 1 câu làm rõ khi thiếu thông tin; chỉ chuyển Mod khi đã làm rõ mà
vẫn ngoài phạm vi hoặc không có căn cứ. Lý do (cost-of-error): trả lời sai khiến học viên học
sai và mất niềm tin; chuyển Mod mọi trường hợp lại tăng thời gian chờ và tải việc cho Mod.

## 4. Taxonomy — 4 lớp "chỗ khó" ↔ 3 route backend

Đề bài yêu cầu xử lý 4 lớp chỗ khó cho mọi hướng; hệ thống map chúng vào 3 route
(`ANSWER` / `CLARIFY` / `ESCALATE`) + 1 nhánh từ chối riêng (prompt injection / ngoài phạm vi
hội thoại):

| Lớp chỗ khó (đề bài) | Route / xử lý | Ví dụ |
|---|---|---|
| ① Nguồn sự thật — AI không được bịa | `ESCALATE` khi không tìm thấy căn cứ (`grounding_status: no_source`) | Hỏi quy định chưa có trong tài liệu chính thức |
| ② Mơ hồ / thiếu thông tin | `CLARIFY` — hỏi lại đúng 1 slot còn thiếu quan trọng nhất, kèm gợi ý lựa chọn | "Deadline bao nhiêu" (chưa rõ bài nào) |
| ③ Ngoài phạm vi / thẩm quyền | `ANSWER` với từ chối lịch sự (`reject_prompt_injection`), không tag Mod | Đòi đáp án bài kiểm tra, yêu cầu nằm ngoài vai trò trợ lý |
| ④ Đặc thù domain — sai gây hậu quả thật | Ràng buộc bằng citation bắt buộc trên mọi `ANSWER` có claim + `check_source_conflicts` phát hiện mâu thuẫn nguồn → `ESCALATE` | Sai deadline/quy định làm học viên nộp muộn, mất điểm |

Cả 4 lớp đều được phủ trong golden set (`eval/test_cases_handbook_20.md`, 20 case, mỗi lớp
≥2 test — xem §6).

## 5. Kiến trúc hệ thống

```
Discord (thật, tương lai)  ─┐
                             ├──▶  FastAPI backend (codebase/backend/server.py)
NiceGUI — giả lập Discord ───┘         │
(frontend/main.py,                     ├─ ChatbotOrchestrator: normalize → classify intent
 giao diện demo/CP2)                   │   → chọn tool → check confidence/conflict → response
                                        │
                                        └─ (tuỳ chọn) llm_client.py → OpenRouter: diễn đạt lại
                                            câu trả lời đã có căn cứ bằng LLM thật, cấm bịa
                                            thêm fact ngoài citation
```

- **Frontend** (`frontend/`): NiceGUI, giả lập 100% giao diện Discord (server list, channel
  sidebar, chat area, embed màu theo trạng thái, "AI Tracepath" box hiển thị các bước xử lý)
  — dùng để demo không cần tài khoản Discord thật.
- **Backend** (`codebase/backend/`): FastAPI, expose `POST /api/v1/chat`. Lõi xử lý là
  `ChatbotOrchestrator` — rule-based, không phụ thuộc API key nào để chạy (xem §5).
- **Discord collector** (`codebase/backend/discord_collector/`): bot Discord thật để tự mining
  dữ liệu từ kênh khoá (đề bài Hướng B không có data pack sẵn) — ẩn danh user ID (HMAC), che
  PII, giới hạn đúng 7 kênh được phép, tự xoá dữ liệu quá hạn lưu trữ.

Chi tiết đầy đủ (schema, symbol, quyết định thiết kế): `CLAUDE.md` + `project_setup/architecture/`.

## 6. Đã build gì — thật vs mock

| Thành phần | Trạng thái | Ghi chú |
|---|---|---|
| Phân loại intent (tiếng Việt, có tolerate lỗi chính tả/dấu) | **Thật** | Rule-based, `chatbot_tools/intent_classifier.py` |
| Tra cứu có cấu trúc (deadline, lịch, XP, gate, slash command, team/mentor) | **Thật** | Structured lookup + validation slot |
| Tìm kiếm nguồn chính thức (BM25) + lọc theo category/thời gian | **Thật** | `chatbot_tools/retrieval.py` |
| Phát hiện mâu thuẫn giữa các nguồn | **Thật** | `check_source_conflicts` |
| Citation cho mọi câu trả lời có claim | **Thật** | Bắt buộc trong response_generator |
| Tìm câu hỏi tương tự đã hỏi trong cộng đồng | **Thật** | `search_similar_questions` |
| Tạo ticket chuyển Mod (2 bước, có consent gate) | **Thật** (gateway gửi Discord là mock — xem dưới) | `offer_ticket` → `create_ticket(user_consent=true)` |
| **Diễn đạt lại câu trả lời bằng LLM thật** (OpenRouter) | **Thật khi có API key** | Chỉ áp dụng cho câu đã có căn cứ (citation) — LLM bị cấm thêm fact mới, chỉ được viết lại tự nhiên hơn. Không có key → tự động rơi về câu trả lời mẫu, không lỗi |
| Dữ liệu nguồn chính thức (`official_sources.json`) | **Mock** | Dữ liệu giả cho prototype, không phải lịch/quy định thật của khóa |
| Gateway gửi ticket vào Discord thật | **Mock** | Đang ở bộ nhớ (`InMemoryTicketGateway`); khi nối Discord thật cần thay bằng gateway triển khai `send()` |
| Vector search / reranker / RRF | **Chưa làm** | Cố tình để sau — chỉ thêm khi đã đo baseline BM25 bằng golden set, tránh "giả vờ đã có" |

## 7. Kiểm thử & đánh giá

- **82 unit test** (`codebase/backend/tests/`) — phủ intent classifier, tool integration,
  conversation search, Discord collector (privacy/pseudonym/retention), tất cả đang pass.
- **Golden set 20 case** (`eval/test_cases_handbook_20.md`, dựa trên Sổ tay học viên chính
  thức) — mỗi lớp trong 4 lớp chỗ khó có ≥2 test, theo đúng format `template_in_out.md`.
- **7 chiều chất lượng** định nghĩa trong `eval_golden_set.md`: Contract, Routing, Grounding
  (không bịa claim), Clarification (hỏi đúng 1 câu), Escalation, Relevance, Language.
- **Bộ test regression** (`bo_test_regression_tro_ly_Kute.md`) — tạo từ các case trợ lý từng
  trả lời sai/thiếu/không phản hồi trong thực tế, dùng để tránh tái diễn lỗi cũ.

## 8. Đội ngũ & phân công (theo `Canvas.txt`)

| Người | Owner chính | Deliverable |
|---|---|---|
| Nhân | Product, evidence, validation | JTBD/problem statement, bảng impact, evidence log, `spec.md` §1–§3, tuyển người thử |
| Phụng | Data, retrieval và tools | Pipeline mining/ẩn danh, index nguồn chính thức, tool retrieve/search/escalate |
| Ngọc Mai | Evaluation & quality | Metric, golden set, quality bar, eval runner, regression, `spec.md` §5/§7 |
| Thịnh | AI behavior & backend orchestration | Router ANSWER/CLARIFY/ESCALATE, prompt, grounding/confidence policy, `spec.md` §4/§6 |
| Lợi | UI, UX, integration, repo, demo | Discord-like flow, nối frontend–backend, README, demo script |

**Người thử đã lên kế hoạch** (theo Canvas nháp CP1): Nhân, Mai, Phụng — cần xác nhận lại tên
thật + kết quả thử trước khi đưa vào `validation/` (tiêu chí nghiệm thu #5 yêu cầu ≥3 người
thật ngoài nhóm, có tên cụ thể).

## 9. Trạng thái hiện tại & việc còn thiếu (so với 5 tiêu chí nghiệm thu)

| # Tiêu chí | Trạng thái |
|---|---|
| 1. Pain cụ thể | Đã có trong Canvas.txt, cần chuyển vào `spec.md` §1 |
| 2. Bằng chứng (≥20 khảo sát hoặc mining có đếm được) | **Chưa đo** — Canvas mới có số nháp, chưa xác nhận |
| 3. Problem statement + impact (bảng ≥3 ứng viên) | **Chưa có** bảng impact trong repo |
| 4. Lát cắt prototype được | **Đạt** — demo được, đã build (xem §5, §6) |
| 5. User sẵn sàng thử (≥3 người thật, có tên) | **Chưa xác nhận** — mới có kế hoạch, chưa có cam kết ghi lại |
| `spec.md` (deliverable chính, nộp 23:59 N1) | **Chưa tạo** trong repo tại thời điểm viết báo cáo này |
| `validation/`, `eval/` (kết quả golden set thật) | `eval/` đã có case, **chưa có bảng kết quả chạy** |

## 10. Vận hành

- Cách chạy backend + frontend local: `HUONG_DAN_CHAY.md`.
- Kiến trúc chi tiết cho AI agent (Claude Code) tiếp tục phát triển: `CLAUDE.md` +
  `project_setup/architecture/`.
- Deploy public (không bắt buộc theo đề bài): `render.yaml` + `project_setup/architecture/DECISIONS.md` D-008.
