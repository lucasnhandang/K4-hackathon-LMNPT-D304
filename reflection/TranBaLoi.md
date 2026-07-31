# Reflection — Trần Bá Lợi

> Bản nháp dựng từ nhật ký kỹ thuật thật trong repo (`frontend/main.py`, `run_app.sh`, `validation/feedback-log.md` mục My, `README.md`). Điền lại bằng lời của chính mình trước khi nộp — CP5/CP6 sẽ hỏi ngẫu nhiên đúng phần này.

## Vai trò

UI, integration, repo và demo. Tôi là người ghép các phần việc của Nhân, Phụng, Ngọc Mai và Thịnh thành một prototype bấm được từ đầu đến cuối, và chịu trách nhiệm cho phần trình bày cuối cùng (README, slide, demo, backup).

## Phần mình làm

- Dựng giao diện dạng Discord (`frontend/main.py`, NiceGUI) hiển thị hội thoại, nguồn trích dẫn, trạng thái clarify/escalate và consent gate trước khi "gửi ticket".
- Nối frontend với backend orchestrator của Thịnh qua `run_app.sh` (dựng venv, chạy `uvicorn` cho backend và NiceGUI cho frontend cùng lúc).
- Viết lại `README.md` để có mục nhóm/phân công/trạng thái nộp bài, và ghép `demo-slides.pdf` từ số liệu thật trong `spec.md` và `eval/`.
- Chuẩn bị backup demo và chạy dry run có bấm giờ trước CP6.

## AI hỗ trợ thế nào

Dùng AI để viết phần lặp lại của UI (render bong bóng chat, badge nguồn, style CSS) và để soạn khung `demo-slides.pdf`/README từ dữ liệu có sẵn trong `spec.md`, `eval/`, `validation/` — nhưng tự tay kiểm tra lại từng con số trước khi đưa vào slide, vì luật "không có bằng chứng thì không có slide" nghĩa là mỗi số trên slide phải trỏ được về đúng file nguồn khi giám khảo hỏi lại.

## Một bài học từ case fail của nhóm

My (willing user) phản hồi rằng bot chưa xử lý tốt các cách hỏi thời gian tương đối như "tối nay" (`validation/feedback-log.md` #4) — nhìn từ góc UI, đây không chỉ là lỗi logic của Thịnh mà còn là lỗi hiển thị: khi bot rơi vào `CLARIFY` vì không resolve được "tối nay" thành một mốc cụ thể, giao diện chỉ hỏi lại chung chung thay vì gợi ý sẵn danh sách sự kiện gần nhất, khiến người dùng thấy như bot "không hiểu" thay vì "đang hỏi lại có lý do". Bài học của tôi: một quyết định `CLARIFY` đúng về mặt kỹ thuật vẫn có thể gây bực bội nếu UI không giải thích được *vì sao* bot hỏi lại — phần trải nghiệm và phần logic phải được thiết kế cùng nhau, không thể để UI chỉ là lớp vẽ lên trên sau cùng.
