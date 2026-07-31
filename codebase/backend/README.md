# Backend tools — Trợ lý Học viên Discord

Lớp này cung cấp các tool độc lập và hybrid agent router cho chatbot. Các tool
tra cứu chạy local; khi cấu hình `OPENROUTER_API_KEY`, OpenRouter phân loại
semantic bằng forced tool call và diễn đạt câu trả lời grounded. Nếu không có
key hoặc API lỗi, router keyword/regex tiếp tục làm fallback.

> `chatbot_tools/data/official_sources.json` là **dữ liệu giả cho prototype**, không
> phải lịch thật của khóa.

## Discord collector

Collector chỉ đọc đúng 7 channel trong `COLLECT_CHANNEL_IDS`. Channel hoặc thread
khác — bao gồm `activity` — bị bỏ qua ở runtime.

Luồng collector:

1. backfill lịch sử của channel và thread được phép;
2. lần chạy sau chỉ lấy message mới hơn watermark đã lưu;
3. nghe message create/update/delete;
4. HMAC Discord user ID thành pseudonym ổn định;
5. che email, điện thoại, user mention, invite và secret/token;
6. lưu SQLite tại `runtime/discord_messages.sqlite3`;
7. xóa vĩnh viễn record quá `DATA_RETENTION_DAYS`.

Collector không lưu username, không tải file attachment và không dùng community
message làm nguồn chính thức. Trường `tier` trong database có ba giá trị:
`official`, `community`, `command`.

Cài dependency và kiểm tra cấu hình:

```powershell
python -m pip install -r requirements.txt
python -m discord_collector --validate-only
python -m discord_collector --inspect-access
```

Chạy collector:

```powershell
python -m discord_collector
```

Lần đầu với `BACKFILL_LIMIT_PER_CHANNEL=0` sẽ đọc toàn bộ lịch sử mà bot có quyền
truy cập. Khi demo nhanh có thể đặt `BACKFILL_LIMIT_PER_CHANNEL=100`.

Trước khi chạy thật, cần có sự đồng ý của admin/chủ server và thông báo phạm vi
thu thập cho thành viên. Không commit hoặc gửi file SQLite ra ngoài.

## Tool hiện có

| Tool | Mục đích |
|---|---|
| `lookup_deadline` | Tra deadline theo bài, module và khóa |
| `lookup_event` | Tra lịch sự kiện |
| `lookup_gate` | Tra đúng thuộc tính (`requirements`, `deadline`, cách nộp/chấm) của gate/checkpoint |
| `lookup_exam_slot` | Tra ca thi |
| `lookup_xp` | Tra quy tắc XP |
| `lookup_team_mentor` | Tra mentor và kênh hỗ trợ của team |
| `lookup_slash_command` | Tra cách dùng slash command |
| `search_official_sources` | BM25 trên nguồn chính thức, có lọc category/thời gian |
| `check_source_conflicts` | Phát hiện fact mâu thuẫn giữa các source ID |
| `search_similar_questions` | Tìm câu hỏi community đã được hỏi và trả link Discord |
| `offer_ticket` | Tạo bản nháp sau tối thiểu hai lần hỏi lại; chưa gửi |
| `create_ticket` | Chỉ gửi bản nháp khi `user_consent=true` |

Mọi tool trả cùng envelope:

```json
{
  "status": "ok",
  "data": {},
  "citations": [],
  "missing_fields": [],
  "conflicts": [],
  "message": "..."
}
```

`status` thuộc một trong:
`ok`, `not_found`, `unsupported`, `ambiguous`, `conflict`, `rejected`, `error`.

Router phải tuân theo:

- slot do semantic agent đề xuất chỉ được chấp nhận khi có bằng chứng trực tiếp
  trong tin nhắn hiện tại; câu hỏi deadline thiếu tên bài phải `CLARIFY`;
- intent cấu trúc có lexical anchor rõ (`deadline`, `gate`, `XP`...) không được
  semantic agent hạ xuống search intent; thiếu slot phải hỏi lại trước retrieval;
- tiếng chat deadline phổ biến (`bao h`, `nộp lúc nào`, `chừng nào`,
  `còn mấy ngày`) được chuẩn hóa trước khi route;
- các alias `weekly submit`, `/weekly submit`, `weekly report` và `báo cáo tuần`
  cùng resolve về entity deadline `weekly_report`; `weekly assignment` không kèm
  số cũng là alias này, còn `weekly assignment 3` vẫn là bài đánh số riêng;
- trước khi trả lời, gọi `search_similar_questions`;
- nếu `redirect_suggested=true`, hiển thị tối đa 3 link chat tương tự;
- link community chỉ để tham khảo, không thay citation chính thức;
- `ok` và có citation phù hợp → có thể `ANSWER`;
- `unsupported` → đúng entity nhưng nguồn thiếu thuộc tính được hỏi; không dùng
  citation đó để trả lời và chuyển Mod/TA;
- `ambiguous` → hỏi đúng một `missing_field` quan trọng nhất;
- `not_found` hoặc `conflict` → không tự tạo fact;
- sau hai lần làm rõ chưa giải quyết được → gọi `offer_ticket`;
- chỉ sau nút **Có, gửi ticket** → gọi `create_ticket(user_consent=true)`.

Tracepath giữ riêng nguyên nhân retrieval `no_source`, `unsupported` và
`conflict`. UI chỉ hiển thị đề xuất nhờ Mod/TA xác nhận; không được tuyên bố đã
gửi ticket khi chưa có consent.

## Chạy nhanh

Từ thư mục `codebase/backend`:

```powershell
python -m pip install -r requirements.txt
python -m chatbot_tools
python -m chatbot_tools search_official_sources --arguments-file examples/search_args.json
python -m chatbot_tools lookup_deadline --arguments-file examples/deadline_args.json
python -m chatbot_tools search_similar_questions --arguments-file examples/similar_question_args.json
```

Chạy API prototype:

```powershell
python server.py
```

`server.py`, `cli.py` và `discord_bot.py` nạp explicit `.env` trong thư mục này,
không override biến đã export. `GET /health` cho biết `routing_mode` mà không
hiển thị API key.

Prototype mặc định `DEFAULT_COHORT=k4`, và frontend gửi explicit cohort K4.
Fixture `chatbot_tools/data/official_sources.json` hiện chỉ chứa record K3 để
test. Cấu hình tạm `KNOWLEDGE_COHORT_ALIASES=k4:k3` cho phép K4 dùng nguồn K3
chung trong các category `deadline,gate,event`; tool result giữ `cohort=k4` đồng
thời ghi `source_cohort=k3`. Xóa alias sau khi nguồn K4 chính thức được ingest.

Với câu hỏi gate, router giữ semantic frame gồm `gate_name` và `requested_fact`.
Ví dụ `gate deadline bao giờ` lưu `requested_fact=deadline` trong clarification;
lượt trả lời `gate 3` chỉ bổ sung `gate_name=cp3`. Có record CP3 nhưng không có
trường `deadline` vẫn là `unsupported` và route `ESCALATE`, không phải
`grounded | ANSWER`.

Semantic frame cũng phân biệt `requirements`, `submission_method` và `grading`.
Ví dụ `gate nộp bao h` hỏi lại Gate số mấy nhưng giữ fact `deadline`;
`gate 3 nộp ở đâu` tra `submission_method`, không bị route thành kênh nộp chung.

`demo_day` và `demo_day_deliverables` là hai entity khác nhau. Follow-up
`demo day` sau câu hỏi deadline tra ngày từ nguồn sự kiện chính thức; khác biệt
giữa hai danh sách deliverable không được coi là conflict của field deadline.
Conflict detection của structured lookup chỉ so sánh đúng fact đang được hỏi.

`--arguments-file` được khuyên dùng trên Windows vì shell có thể làm mất dấu nháy
của JSON truyền trực tiếp.

Chạy test:

```powershell
python -m unittest discover -s tests -v
```

## Gắn vào LLM function-calling

```python
from chatbot_tools import build_default_registry

registry = build_default_registry()

# Gửi registry.definitions() vào trường tools của SDK/model.
definitions = registry.definitions()

# Khi model yêu cầu gọi tool:
result = registry.execute(
    "lookup_deadline",
    {
        "assignment": "weekly_assignment_3",
        "module": "rag",
        "cohort": "k4",
    },
)
```

Không cho model gọi trực tiếp Discord channel ID. `TicketTools` ánh xạ category
sang allowlist phía server. Khi nối Discord thật, thay `InMemoryTicketGateway`
bằng gateway triển khai `send(target_channel, payload)`.

`known_context` cũng dùng allowlist; các trường như Discord user ID, email, token
hoặc raw conversation sẽ bị từ chối thay vì âm thầm đưa vào ticket.

## Phần thật và phần mock

- Thật: validation slot, structured lookup, BM25, metadata time filter, citation,
  conflict check, consent gate và chống gửi ticket trùng.
- Mock: dữ liệu nguồn và gateway gửi Discord đang ở bộ nhớ.
- Chưa làm: vector search, reranker và RRF. Chỉ thêm các phần này sau khi BM25
  baseline đã được đo bằng golden set; không nên giả vờ rằng prototype đã có.
