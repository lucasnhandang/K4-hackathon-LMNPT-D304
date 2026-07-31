# User Validation — Trợ lý Kute++

> **Trạng thái:** Đã ghi nhận 5 phản hồi định tính.

## 1. Phạm vi

- **Prototype được đánh giá:** Trợ lý Kute++ — luồng `ANSWER / CLARIFY / ESCALATE`.
- **Phiên bản/commit:** `384f082`.
- **Ngày ghi nhận:** 31/07/2026.
- **Người điều phối:** Nhân.
- **Người ghi log:** Ngọc Mai.
- **Số người phản hồi:** 5 người ngoài nhóm.
- **Willing users:** Mai, Khang, Hải, My, Dương.
- **Nhiệm vụ chung:**

> Đánh giá chất lượng Trợ lý Kute++ theo khía cạnh được phân công, dựa trên các câu hỏi thử về quy định, deadline, tài liệu, citation, intent và lịch sự kiện.

## 2. Cách tiến hành

Mỗi người phụ trách một khía cạnh:

1. Mai đánh giá độ chính xác với quy định, deadline và tài liệu.
2. Khang đánh giá grounding/citation.
3. Hải đánh giá intent, paraphrase và câu hỏi nhiều ý.
4. My đánh giá câu hỏi thời gian và lịch sự kiện.
5. Dương đánh giá mức hài lòng chung.
6. Nhóm tổng hợp câu trả lời, gắn mức nghiêm trọng theo rủi ro và liên kết mỗi phát hiện với golden case/backlog.

Chi tiết câu hỏi và phản hồi gốc đã được chuẩn hóa tại [`eval/user-feedback.md`](../eval/user-feedback.md).

## 3. Quy ước mức nghiêm trọng

| Mức | Định nghĩa |
|---|---|
| Critical | Có thể làm học viên nhận sai deadline/link/quy định, mất điểm, lộ PII hoặc không có đường lui an toàn |
| Major | Có thể làm người dùng không hoàn thành được mục tiêu, nhận câu trả lời thiếu ý hoặc phải hỏi lại/nhờ người hỗ trợ |
| Minor | Kết quả vẫn dùng được nhưng còn khó hiểu, chậm hoặc bất tiện |

## 4. Feedback log

| # | Người phản hồi | Vai trò | Willing user? | Khía cạnh đánh giá | Phát hiện | Tóm tắt phản hồi | Mức nghiêm trọng | Quyết định của nhóm |
|---:|---|---|:---:|---|---|---|---|---|
| 1 | Mai | Học viên | Có | Quy định, deadline và tài liệu | Bot trả lời đúng dữ liệu đã có nhưng chưa chính xác với deadline Weekly Assignment 4, slide Hackathon và Jira. | Cần bổ sung Knowledge Base và có quy trình cập nhật tài liệu mới. | Critical — liên quan trực tiếp deadline, link và quy định. | Bổ sung nguồn chính thức có owner/ngày cập nhật; chạy lại `case_15`, `case_32`, `case_38`, `case_39`. |
| 2 | Khang | Học viên | Có | Grounding/citation | Có trường hợp câu hỏi Jira/Codelab lại trích dẫn LearnWorlds. | Cần giảm retrieval false-positive; không có nguồn phù hợp phải trả `no_source`. | Critical — citation sai có thể khiến người dùng tin nhầm thông tin. | Thêm relevance threshold; không tạo citation khi dưới ngưỡng; regression với `case_38`–`case_39`. |
| 3 | Hải | Học viên | Có | Intent, paraphrase và multi-intent | Bot xử lý câu đơn giản tốt nhưng chưa ổn định với câu nhiều ý hoặc diễn đạt như “Mentoring Duty có XP không?” và “Lệnh báo cáo tuần là gì?”. | Cần tách multi-intent và mở rộng tập paraphrase. | Major — người dùng có thể không nhận đủ câu trả lời và phải hỏi lại. | Bổ sung intent/paraphrase cases; sửa lỗi câu hỏi đa ý `case_26`. |
| 4 | My | Học viên | Có | Thời gian và lịch sự kiện | Bot chưa resolve tốt “tối nay” và lịch theo ngày thực tế. | Cần Time Resolver kết hợp timestamp hiện tại với lịch sự kiện. | Critical — suy luận sai lịch có thể khiến người dùng bỏ lỡ sự kiện. | Thêm Time Resolver theo `Asia/Ho_Chi_Minh`; regression với `case_28`–`case_30`. |
| 5 | Dương | Học viên | Có | Mức hài lòng chung | Bot phản hồi nhanh, đúng khi có dữ liệu và biết từ chối; một số câu chưa khớp Golden Test hoặc chưa rõ. | Cần tối ưu response template, bổ sung dữ liệu và rà lại Golden Case với nguồn chính thức. | Minor — phần lớn vẫn dùng được nhưng độ rõ ràng chưa đồng đều. | Chuẩn hóa template; chỉ sửa golden set sau khi đối chiếu tài liệu chính thức. |

## 5. Tổng hợp sau validation

- **Số người hoàn thành lượt đánh giá:** 5/5.
- **Chủ đề lặp lại nhiều nhất:** Chất lượng câu trả lời phụ thuộc vào độ phủ Knowledge Base và khả năng chọn đúng nguồn.
- **Số người đề cập trực tiếp chủ đề này:** 3/5 (Mai, Khang, Dương).
- **Feedback/case nghiêm trọng nhất:** Citation không liên quan hoặc thiếu dữ liệu chính thức ở câu hỏi deadline/link/quy định; các lỗi này có thể khiến học viên làm sai hoặc bỏ lỡ mốc quan trọng.
- **Hai thay đổi ưu tiên trước demo:** (1) thêm relevance threshold và fallback `no_source`; (2) bổ sung nguồn chính thức cho deadline/link/quy định và chạy regression.
- **Thay đổi đã thực hiện:** Hoàn thiện log, chuyển phát hiện thành P0/P1/P2 và bổ sung tiêu chí nghiệm thu trong `eval/user-feedback.md`; chưa ghi nhận thay đổi code khắc phục.
- **Điều nhóm quyết định giữ nguyên và lý do:** Giữ luồng `ANSWER / CLARIFY / ESCALATE`; phản hồi cho thấy hệ thống cần route an toàn khi thiếu ngữ cảnh hoặc nguồn thay vì đoán câu trả lời.
- **Đưa vào backlog:** Multi-intent/paraphrase, Time Resolver theo `Asia/Ho_Chi_Minh`, chuẩn hóa response template và quy trình rà soát Golden Case với tài liệu chính thức.

## 6. Liên kết feedback với thay đổi

| Feedback/người thử | Thay đổi hoặc quyết định giữ nguyên | Vị trí trong prototype | Case kiểm thử liên quan | Dòng Changelog trong `spec.md` |
|---|---|---|---|---|
| Mai — thiếu dữ liệu deadline/link/quy định | Bổ sung Knowledge Base từ nguồn chính thức và chạy regression | Knowledge Base/retrieval | `case_15`, `case_32`, `case_38`, `case_39` | “Ghi nhận phản hồi đánh giá của Mai, Khang, Hải, My và Dương” |
| Khang — citation false-positive | Thêm relevance threshold; dưới ngưỡng trả `no_source` | Retrieval/grounding | `case_38`, `case_39` | “Ghi nhận phản hồi đánh giá của Mai, Khang, Hải, My và Dương” |
| Hải — intent và câu hỏi nhiều ý | Bổ sung multi-intent/paraphrase regression | Router/intent classification | `case_21`, `case_23`, `case_26` | “Ghi nhận phản hồi đánh giá của Mai, Khang, Hải, My và Dương” |
| My — thời gian tương đối | Đưa Time Resolver vào backlog | Router/tool lịch | `case_28`, `case_29`, `case_30` | “Ghi nhận phản hồi đánh giá của Mai, Khang, Hải, My và Dương” |
| Dương — câu trả lời chưa rõ | Chuẩn hóa template; giữ Golden Case cho tới khi có nguồn chính thức để đối chiếu | Response generator/evaluation | Toàn bộ golden set, ưu tiên case đang fail | “Ghi nhận phản hồi đánh giá của Mai, Khang, Hải, My và Dương” |
