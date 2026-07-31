# Phản hồi người dùng về chất lượng Trợ lý Kute++

## 1. Phạm vi và người phản hồi

- **Mục tiêu:** Ghi nhận đánh giá định tính về chất lượng câu trả lời của Trợ lý Kute++.
- **Số người phản hồi:** 5 người ngoài nhóm.
- **Mapping:** Câu 1 — Mai; câu 2 — Khang; câu 3 — Hải; câu 4 — My; câu 5 — Dương.
- **Lưu ý phương pháp:** Mỗi người phụ trách một câu hỏi. Vì vậy kết quả dùng để tìm vấn đề và xác định backlog, không dùng để tính tỷ lệ hài lòng đại diện cho cả 5 người.

## 2. Kết quả chi tiết

| # | Người phản hồi | Câu hỏi khảo sát | Phản hồi ghi nhận | Góp ý / Nhận xét |
|---:|---|---|---|---|
| 1 | Mai | Chatbot có trả lời đúng các câu hỏi liên quan đến quy định, deadline và tài liệu của chương trình không? | Chatbot trả lời đúng các thông tin đã có trong Knowledge Base. Tuy nhiên một số câu hỏi như deadline Weekly Assignment 4, link slide Hackathon hoặc quy định Jira vẫn chưa có câu trả lời chính xác. | Cần bổ sung thêm dữ liệu vào Knowledge Base và cập nhật thường xuyên các tài liệu mới để giảm số lượng câu trả lời thiếu thông tin hoặc phải từ chối trả lời. |
| 2 | Khang | Chatbot có cung cấp đúng nguồn tham khảo (grounding/citation) cho câu trả lời không? | Đa số câu trả lời đều dẫn nguồn đúng. Tuy nhiên vẫn xuất hiện một số trường hợp chatbot lấy nhầm tài liệu, ví dụ câu hỏi về Jira hoặc Codelab nhưng lại trích dẫn tài liệu LearnWorlds. | Cần cải thiện Retrieval để giảm hiện tượng false-positive. Khi không tìm thấy tài liệu phù hợp nên trả về trạng thái `no_source` thay vì sử dụng nguồn không liên quan. |
| 3 | Hải | Chatbot có hiểu đúng ý định của người dùng khi câu hỏi chứa nhiều nội dung hoặc diễn đạt khác nhau không? | Chatbot xử lý tốt các câu hỏi đơn giản nhưng còn gặp khó khăn với câu hỏi chứa nhiều ý hoặc cách diễn đạt khác nhau như “Mentoring Duty có XP không?” hoặc “Lệnh báo cáo tuần là gì?”. | Nên cải thiện Intent Classification và hỗ trợ Multi-intent để chatbot có thể tách và xử lý nhiều yêu cầu trong cùng một câu hỏi. Đồng thời mở rộng bộ dữ liệu huấn luyện với nhiều cách diễn đạt khác nhau. |
| 4 | My | Chatbot có xử lý chính xác các câu hỏi liên quan đến thời gian hoặc lịch sự kiện không? | Chatbot chưa xử lý tốt các câu hỏi sử dụng thời gian tương đối như “tối nay”, hoặc các câu hỏi yêu cầu xác định lịch theo ngày thực tế. | Cần bổ sung cơ chế Time Resolver kết hợp timestamp hiện tại và lịch sự kiện để chatbot có thể suy luận chính xác hơn thay vì chỉ dựa vào intent. |
| 5 | Dương | Mức độ hài lòng của bạn đối với chất lượng câu trả lời của chatbot? | Nhìn chung chatbot trả lời nhanh, đúng với các thông tin đã có trong hệ thống và biết từ chối khi thiếu dữ liệu. Tuy nhiên vẫn còn một số câu trả lời chưa đúng kỳ vọng của bộ Golden Test hoặc chưa đủ rõ ràng. | Nên tiếp tục tối ưu template phản hồi, bổ sung dữ liệu còn thiếu và rà soát lại các Golden Case có dấu hiệu mâu thuẫn với tài liệu chính thức để nâng cao độ chính xác của hệ thống. |

## 3. Tổng hợp phát hiện

| Mức ưu tiên | Phát hiện | Evidence liên quan | Hành động đề xuất |
|---|---|---|---|
| P0 | Retrieval có thể gắn nguồn không liên quan cho Jira/Codelab. | Phản hồi của Khang; nhóm case `case_38`–`case_39` trong golden set. | Thêm ngưỡng relevance; không đạt ngưỡng thì route an toàn với `grounding_status: no_source`. |
| P0 | Knowledge Base thiếu dữ liệu có thể ảnh hưởng deadline, link và quy định. | Phản hồi của Mai; `case_15`, `case_32`, `case_38`, `case_39`. | Bổ sung nguồn chính thức có owner và ngày cập nhật; chạy regression sau mỗi lần cập nhật. |
| P1 | Câu hỏi nhiều ý hoặc paraphrase chưa được hiểu ổn định. | Phản hồi của Hải; `case_21`, `case_23`, `case_26`. | Tách multi-intent, mở rộng paraphrase và thêm regression cases. |
| P1 | Cụm thời gian tương đối chưa được resolve theo thời điểm thực. | Phản hồi của My; `case_28`–`case_30`. | Thêm Time Resolver với timezone `Asia/Ho_Chi_Minh`, timestamp hiện tại và lịch sự kiện có nguồn. |
| P2 | Một số câu trả lời đúng route nhưng chưa đủ rõ hoặc chưa khớp Golden Test. | Phản hồi của Dương; báo cáo `eval/eval_goldenset_result.md`. | Chuẩn hóa response template và chỉ sửa Golden Case sau khi đối chiếu tài liệu chính thức. |

## 4. Tiêu chí nghiệm thu cho vòng tiếp theo

1. Câu hỏi Jira/Codelab không được trích dẫn LearnWorlds nếu tài liệu đó không trực tiếp hỗ trợ câu trả lời.
2. Khi không có nguồn phù hợp, output phải dùng `grounding_status: no_source` và không tạo citation.
3. Câu hỏi nhiều ý phải được tách để trả lời đủ từng ý hoặc hỏi đúng phần thông tin còn thiếu.
4. “Tối nay” và các cụm thời gian tương đối phải được quy đổi theo `Asia/Ho_Chi_Minh` và lịch sự kiện hiện hành.
5. Mọi thay đổi Knowledge Base, retrieval, router hoặc template phải chạy lại golden set và không tạo critical failure ở deadline, link hoặc quy định.

## 5. Tài liệu liên quan

- [`eval/eval_goldenset_result.md`](eval_goldenset_result.md)
- [`eval/golden_set.json`](golden_set.json)
- [`spec.md` — §8](../spec.md#8-phân-công--kế-hoạch)
- [`validation/feedback-log.md`](../validation/feedback-log.md)
