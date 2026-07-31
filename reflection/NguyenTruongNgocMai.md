# Reflection — Ngọc Mai

> Bản nháp dựng từ nhật ký kỹ thuật thật trong repo (`eval/golden_set.json`, `eval/eval_goldenset_result.md`, `spec.md` §7). Điền lại bằng lời của chính mình trước khi nộp — CP5/CP6 sẽ hỏi ngẫu nhiên đúng phần này.

## Vai trò

Evaluation & quality. Tôi định nghĩa "đạt" nghĩa là gì cho từng chiều chất lượng, xây golden set, và là người duy nhất được chốt/đọc quality bar sau 23:59 ngày 1 — không ai trong nhóm được đổi bar để "cho đẹp".

## Phần mình làm

- Định nghĩa 9 chiều chất lượng C1–C9 (Contract, Routing, Grounding, Clarification, Escalation, Relevance, Language, Traceability, Safety) sao cho người ngoài nhóm chấm cũng ra cùng kết quả (`spec.md` §7.1).
- Xây `eval/golden_set.json` 40 case: phủ đủ 4 lớp chỗ khó (①②③④), 8–10 case thường, case hiếm/adversarial, và ≥10 case lấy/phát triển từ chatlog thật.
- Vận hành eval runner, chạy trọn bộ và giữ nguyên cả case fail trong bảng kết quả thay vì lọc bớt.
- Ghi log validation cùng Nhân, gắn từng phát hiện của willing user với case golden set liên quan.

## AI hỗ trợ thế nào

Dùng AI để nháp thêm case golden set từ các đoạn chatlog thật (transcript có mã đoạn), sau đó tự đọc lại từng case để gán đúng lớp chỗ khó và route kỳ vọng — AI giúp tăng tốc độ viết case nhưng không được giao quyền quyết định case nào PASS/FAIL, vì đó là phần quality bar phải kiểm chứng lại được bằng tay.

## Một bài học từ case fail của nhóm

Lượt chạy mới nhất đạt 39/40 (97,5%), vượt xa quality bar 80% đã chốt — nhưng case fail duy nhất, `case_26` ("Gate vs Weekly submit khác gì nhau"), lại lộ một lỗ hổng thiết kế chứ không phải lỗi vặt: đây là câu hỏi đa ý, router coi là thiếu slot nên trả `CLARIFY`, trong khi golden set kỳ vọng bot tổng hợp cả hai nguồn để `ANSWER` trực tiếp. Nếu tôi chỉ nhìn con số 97,5% mà không đọc kỹ case fail, sẽ dễ kết luận "đạt bar, xong việc". Bài học: pass rate cao không tự động nghĩa là an toàn để demo — phải luôn hỏi case fail còn lại thuộc loại nào, vì multi-intent là dạng câu hỏi học viên thật sự hay hỏi, không phải case hiếm có thể bỏ qua.
