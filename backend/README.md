# K4 Student Assistant Backend

FastAPI backend cho trợ lý học viên trên Discord, dùng Gemini để trả lời và
MongoDB để lưu từng lượt hội thoại.

## Cài đặt

Tại thư mục `backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

Tạo `.env` từ `.env.example` và điền các giá trị thật:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=student_assistant

GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSIONS=768

VECTOR_SEARCH_INDEX=kb_vector_index
VECTOR_ANSWER_THRESHOLD=0.83
VECTOR_CLARIFY_THRESHOLD=0.80

DISCORD_BOT_TOKEN=
DISCORD_ALLOWED_CHANNEL_IDS=
BACKEND_BASE_URL=http://127.0.0.1:8000
```

Không commit `.env`, Discord token hoặc API key.

## Chạy API

Từ thư mục `backend`:

```powershell
python -m uvicorn student_assistant.main:app --app-dir src --reload --port 8000
```

Kiểm tra:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Chạy Discord bot

Mở terminal thứ hai, kích hoạt cùng `.venv`, rồi chạy:

```powershell
python -m student_assistant.integrations.discord.bot
```

Sinh viên hỏi bằng cách mention bot:

```text
@TroLyK4 deadline bài tuần này là khi nào?
```

Đối với luồng hỏi đáp, bot chỉ đọc tin nhắn mention trực tiếp và chỉ hoạt động trong
`DISCORD_ALLOWED_CHANNEL_IDS`. Danh sách rỗng cho phép mọi channel mà bot có
quyền truy cập.

### Kênh tự thu thập knowledge

Mặc định bot tự thu thập tin nhắn text không mention bot trong channel:

```text
977644669326475311
```

Cấu hình bằng:

```env
DISCORD_KB_CHANNEL_IDS=977644669326475311
```

Mỗi tin nhắn được gửi tới `POST /knowledge/discord`, mask email/SĐT, tạo
embedding và upsert vào `kb_documents` theo Discord message ID. Bot thu thập
im lặng, không reply từng message. Tin nhắn của bot, tin nhắn rỗng, secret và
prompt injection bị bỏ qua; attachment chưa được ingest trong MVP.

Kênh này được xem là nguồn dữ liệu đã được quản trị. Không dùng nó làm kênh chat
thông thường vì mọi text hợp lệ trong kênh sẽ trở thành nguồn trả lời.

## MongoDB

`conversations` lưu bản tổng quan một lượt hỏi đáp.

`chat_messages` lưu hai document cho mỗi lượt:

- `role="user"`: `author_id` là Discord user ID và có `discord_role_ids`.
- `role="assistant"`: `author_id` là Discord bot ID.

Hai document dùng chung `conversation_id`. Index duy nhất
`(conversation_id, role)` ngăn ghi trùng khi retry.

Ví dụ lọc theo một học viên trong MongoDB Compass:

```json
{"author_id": "694383988474642493", "role": "user"}
```

## Grounding và Vector Search

Endpoint `/chat` dùng MongoDB Atlas Vector Search trên collection
`kb_documents`. Gemini chỉ tạo câu trả lời khi điểm của tài liệu phù hợp nhất
đạt `VECTOR_ANSWER_THRESHOLD`.

Khởi tạo dữ liệu và index:

```powershell
python scripts/seed_kb.py
python scripts/create_vector_index.py
python scripts/check_vector_index.py
python scripts/smoke_grounding.py
python scripts/smoke_chat.py
python scripts/smoke_discord_knowledge.py
```

`seed_kb.py` tạo embedding 768 chiều bằng `gemini-embedding-2` và upsert theo
`content_hash`; script không xóa toàn bộ KB. Sau khi tạo index, chờ trạng thái
`READY` trên Atlas trước khi gọi `/chat`.

MongoDB local cũ không có `$vectorSearch` sẽ không chạy được luồng grounding.
Dùng Atlas cho môi trường dev hoặc MongoDB Community 8.2+ có Vector Search.

## Guardrails MVP

- Tối đa 2.000 ký tự mỗi tin nhắn.
- Rate limit trong process: 5 request/phút/user và 30 request/phút/channel.
- Chặn secret/token; email và số điện thoại được mask trước khi gửi Gemini.
- Structured Output giới hạn phản hồi Gemini thành `action`, `reasoning`,
  `reply`; output scanner kiểm tra lại trước khi trả Discord.
- `grounding_score >= 0.83`: tạo câu trả lời từ KB.
- `0.80 <= grounding_score < 0.83`: hỏi lại để làm rõ.
- `grounding_score < 0.80`: hỏi sinh viên có muốn nhờ Mod không.
- Raw message hết hạn sau 30 ngày; dữ liệu đã mask hết hạn sau 180 ngày bằng
  MongoDB TTL index.

Rate limit hiện tại phù hợp một API process. Khi scale nhiều replica cần chuyển
bộ đếm sang Redis.

Hai ngưỡng vector được hiệu chỉnh bước đầu trên KB mẫu. Tiếp tục đo trên golden
set thật trước khi dùng cho production; score không phải xác suất tuyệt đối.

## Bộ nhớ tên người dùng

Bot lưu tên khi người dùng chủ động nói:

```text
@bot tôi tên là Thịnh
@bot tôi tên là Thịnh, từ giờ hãy gọi tôi như vậy
@bot tôi tên là Thịnh, bạn có thể làm những gì?
@bot đổi lại tôi tên là Quang
@bot tôi tên là gì?
@bot hãy quên tên tôi
```

Tên được lưu trong `user_memories` theo cặp `(student_id, guild_id)` và tự hết
hạn sau 180 ngày. Các lệnh nhớ/đọc/xóa tên chạy trước Vector Search nên không bị
phân loại thành câu ngoài knowledge base. MVP chỉ cho phép lưu
`preferred_name`; bot không tự rút trích và lưu các thông tin cá nhân khác.
Parser hỗ trợ câu ghép và các cách viết chat như `j`, nên phần memory không bị
đẩy nhầm sang Vector Search.

Các câu hỏi về phạm vi của bot như `bạn có những thông tin j`, `bot biết gì`
hoặc `bạn hỗ trợ được gì` được trả lời trực tiếp bằng danh mục kiến thức hiện có.

Lời chào và phản hồi Gemini dùng giọng “mình – bạn”, ngắn gọn và tự nhiên.
Nếu đã lưu tên, câu `@bot xin chào` sẽ được cá nhân hóa theo tên đó.

Kiểm tra kết nối MongoDB cho user memory:

```powershell
python scripts/smoke_user_memory.py
```

## Seed và evaluation

Các script yêu cầu package đã được cài editable bằng `pip install -e .`.

```powershell
python scripts/seed_kb.py
python scripts/create_vector_index.py
python scripts/run_eval.py
```

Golden set và CSV evaluation nằm trong `backend/data`.

## Tests

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Unit tests không gọi Gemini hoặc ghi MongoDB.

## Cấu trúc

```text
backend/
├── data/
│   └── golden_set.json
├── scripts/
│   ├── run_eval.py
│   └── seed_kb.py
├── src/
│   └── student_assistant/
│       ├── main.py
│       ├── api/
│       │   ├── router.py
│       │   ├── routes/
│       │   └── schemas/
│       ├── core/
│       ├── domain/
│       ├── integrations/
│       │   └── discord/
│       ├── repositories/
│       └── services/
├── tests/
├── .env.example
├── pyproject.toml
└── requirements.txt
```

Phân lớp:

- `api`: HTTP routes và Pydantic schemas.
- `services`: nghiệp vụ Gemini, routing và lưu hội thoại.
- `repositories`: truy cập MongoDB.
- `integrations/discord`: Discord Gateway và backend HTTP client.
- `core`: cấu hình và logging.
- `domain`: enum/model không phụ thuộc framework.

Package `src/app` và `src/discord_bot` chỉ còn compatibility shim cho lệnh cũ.
Code mới phải import từ `student_assistant`.

## Endpoint

### `POST /chat`

Discord bot dùng endpoint này để gọi Gemini và lưu MongoDB.

### `POST /ask`

Luồng knowledge-base cũ dùng Anthropic và fuzzy retrieval.

### `GET /health`

Kiểm tra process API đang hoạt động.
