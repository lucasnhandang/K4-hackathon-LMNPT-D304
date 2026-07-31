# Reflection — Thịnh

> Bản nháp dựng từ nhật ký kỹ thuật thật trong repo (`codebase/backend/chatbot_tools/orchestrator.py`, `llm_client.py`, `spec.md` §9 Changelog). Điền lại bằng lời của chính mình trước khi nộp — CP5/CP6 sẽ hỏi ngẫu nhiên đúng phần này.

## Vai trò

AI behavior & backend orchestration. Tôi giữ quyết định trung tâm của prototype: router chọn `ANSWER / CLARIFY / ESCALATE` dựa trên độ rõ của câu hỏi và độ chắc của nguồn.

## Phần mình làm

- Viết router và orchestrator (`chatbot_tools/orchestrator.py`) nối intent/slot classification với retrieval của Phụng.
- Wiring lời gọi AI thật qua OpenRouter (`llm_client.py`, model `google/gemini-2.0-flash-001`) cho cả bước phân loại semantic và bước diễn đạt câu trả lời grounded; khi thiếu API key hoặc lỗi mạng, router rơi về keyword/regex fallback thay vì crash hoặc bịa câu trả lời.
- Cài chính sách grounding/confidence: chỉ `ANSWER` khi có citation hợp lệ, `CLARIFY` khi thiếu đúng một slot quan trọng, `ESCALATE` khi ngoài phạm vi hoặc nguồn xung đột (`spec.md` §4, §6).
- Xử lý bốn đường đi trải nghiệm: happy path, low-confidence, failure/không căn cứ, correction.

## AI hỗ trợ thế nào

Dùng AI để nháp phần cấu trúc gọi tool (function calling) sang OpenRouter và để rà lỗi logic khi regression fail, nhưng chính sách "khi nào được tự trả lời — khi nào phải hỏi lại — khi nào phải chuyển người" là phần tôi tự thiết kế và test bằng tay, vì đây là chỗ sai một quyết định có thể khiến học viên tin nhầm deadline.

## Một bài học từ case fail của nhóm

Changelog (`spec.md` §9) ghi lại ít nhất ba lần tôi phải sửa lại đúng vấn đề "router đoán quá tay": chặn agent tự điền slot không có trong câu hỏi, khoá precedence của intent cấu trúc trước semantic search sau khi regression "deadline bao h" bị đổi nhầm thành search intent rồi trả lời sai Weekly Report, và tách Mentoring Duty khỏi intent mentor của team sau khi phát hiện nhầm lẫn tương tự. Mẫu số chung của cả ba lần: router "thông minh" quá — cố suy luận thêm dữ kiện người dùng không nói ra — lại chính là nguồn lỗi nguy hiểm nhất, vì nó biến một câu hỏi mơ hồ (lớp ②) thành một câu trả lời tự tin nhưng sai (lớp ①). Bài học: với domain có hậu quả thật, "không chắc thì hỏi lại" phải thắng "cố trả lời cho mượt" — kể cả khi điều đó làm chatbot trông kém mượt mà hơn trong demo.
