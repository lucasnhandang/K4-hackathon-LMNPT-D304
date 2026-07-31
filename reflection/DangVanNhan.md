# Reflection — Nhân

> Bản nháp dựng từ nhật ký kỹ thuật thật trong repo (`spec.md` §1–§2, §9 Changelog, `validation/feedback-log.md`). Điền lại bằng lời của chính mình và số liệu/cảm nhận thật trước khi nộp — CP5/CP6 sẽ hỏi ngẫu nhiên đúng phần này.

## Vai trò

Product / evidence / validation. Tôi giữ bài toán ở gốc: pain là gì, ai xác nhận, và vì sao chọn quyết định `ANSWER / CLARIFY / ESCALATE` làm lát cắt thay vì bốn ứng viên khác.

## Phần mình làm

- Viết JTBD, problem statement và core JTBD (`spec.md` §1.1–§1.3) từ Canvas ban đầu.
- Chạy khảo sát 20 người ngoài nhóm, tổng hợp thành `spec.md` §1.4A: 13/20 muốn bot hỏi lại khi thiếu thông tin, 19/20 từng gặp ít nhất một vấn đề.
- Dựng bảng impact 3 ứng viên và lý do loại hai ứng viên còn lại (`spec.md` §2, §2.1) bằng số thay vì cảm tính.
- Điều phối 5 willing users (Mai, Khang, Hải, My, Dương) cho vòng validation CP5 và tổng hợp `validation/feedback-log.md`.
- Theo dõi và cập nhật `spec.md` §9 Changelog mỗi khi có thay đổi đủ lớn để cần giải trình.

## AI hỗ trợ thế nào

Dùng AI để nháp câu hỏi khảo sát trước khi tự chỉnh lại theo phản hồi thật của lớp, và để tổng hợp/đối chiếu số liệu khảo sát thành bảng — nhưng mọi con số trong `spec.md` §1–§2 đều do tôi tự đếm lại thủ công từ câu trả lời gốc trước khi chốt, vì đây là phần bị chấm điểm dựa trên bằng chứng kiểm lại được.

## Một bài học từ case fail của nhóm

Evidence mạnh nhất của nhóm (13/20, 19/20) đến từ khảo sát trực tiếp, nhưng phần "Mining data pack" (`spec.md` §1.4B) lại lấy từ chatlog VLearn tutor — không phải từ chính Trợ lý Kute++ trên Discord. Ban đầu tôi suýt dùng con số 46,2% "không có citation" của VLearn để nói về Kute++, tới khi Phụng và Thịnh chỉ ra đây là hai hệ thống khác nhau mới sửa lại thành "bằng chứng bổ trợ về bối cảnh" và giữ nguyên mục §1.4D "Evidence Discord cần bổ sung" là `[CẦN ĐO]` thay vì bịa số cho đẹp. Bài học: bằng chứng mạnh ở đâu phải nói rõ mạnh cho *cái gì* — trộn nguồn khác hệ thống để lấp chỗ trống là cách nhanh nhất để mất điểm phúc khảo.
