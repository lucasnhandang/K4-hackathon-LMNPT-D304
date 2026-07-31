# Reflection — Phụng

> Bản nháp dựng từ nhật ký kỹ thuật thật trong repo (`codebase/backend/chatbot_tools/retrieval.py`, `tools.py`, `validation/feedback-log.md` mục Khang). Điền lại bằng lời của chính mình trước khi nộp — CP5/CP6 sẽ hỏi ngẫu nhiên đúng phần này.

## Vai trò

Data, retrieval và tools. Tôi chịu trách nhiệm cho phần "nguồn sự thật" của trợ lý: dữ liệu vào từ đâu, tra cứu bằng gì, và tool nào được phép trả lời/chuyển Mod.

## Phần mình làm

- Thiết kế pipeline mining/ẩn danh dữ liệu Discord theo đúng luật bảo mật data pack của khoá.
- Xây index nguồn chính thức (`official_sources.json` — dữ liệu giả cho prototype, ghi rõ trong `codebase/backend/README.md`) và các tool `search`, `retrieve`, `escalate`.
- Viết retrieval BM25 dùng cho route `ANSWER`, đảm bảo mọi câu trả lời có citation trỏ đúng locator hoặc trả `no_source`.
- Giữ trace cho mọi lệnh gọi tool để phục vụ debug và audit (`spec.md` §4.3 "Phần chạy thật").

## AI hỗ trợ thế nào

Dùng AI để sinh khung code cho các tool tra cứu (structured lookup, BM25 wrapper) rồi tự viết lại phần so khớp locator và ngưỡng relevance, vì đây là chỗ quyết định một câu trả lời có được tính là "grounded" hay không — không thể để AI tự quyết ngưỡng mà không kiểm tra bằng tay trên vài case thật.

## Một bài học từ case fail của nhóm

Trong vòng validation, Khang (willing user) phát hiện có trường hợp câu hỏi về Jira/Codelab lại bị bot trích dẫn nhầm sang nguồn LearnWorlds (`validation/feedback-log.md` #2) — retrieval của tôi trả về kết quả gần đúng nhất theo điểm số, nhưng "gần đúng nhất" không đồng nghĩa "đủ liên quan". Vì citation sai có thể khiến học viên tin nhầm thông tin, nhóm xếp đây là mức Critical chứ không phải Minor. Bài học: retrieval cho một trợ lý phải trả lời đúng những câu hỏi có hậu quả thật (deadline, link, quy định) cần một ngưỡng relevance cứng và một đường lui `no_source` rõ ràng — trả lời gần đúng còn nguy hiểm hơn từ chối trả lời.
