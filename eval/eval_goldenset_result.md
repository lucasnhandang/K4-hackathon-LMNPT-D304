# Golden Set Evaluation Result

## Tổng quan

| Thuộc tính | Kết quả |
|---|---|
| Golden set | `eval/golden_set.json` |
| Kết quả nguồn | `eval/results/eval_20260731_134919.json` |
| Chế độ chạy | `offline_local` |
| Tổng số test case | 40 |
| Passed | 39 |
| Failed | 1 |
| Pass rate | **97.5%** |
| Unit tests | 137/137 passed |
| Confidence | Không dùng để quyết định pass/fail |

## Kết quả theo route

| Route kỳ vọng | Tổng số | Passed | Pass rate |
|---|---:|---:|---:|
| ANSWER | 21 | 20 | 95.2% |
| CLARIFY | 6 | 6 | 100% |
| ESCALATE | 13 | 13 | 100% |

## Kết quả chi tiết

| Case | Mô tả | Expected route | Actual route | Grounding | Kết quả |
|---|---|---|---|---|---|
| `case_01` | Quy định chuyên cần | ANSWER | ANSWER | grounded | PASS |
| `case_02` | Có hỗ trợ học online không | ANSWER | ANSWER | grounded | PASS |
| `case_03` | Câu hỏi XP mơ hồ → bổ sung hoạt động → trả lời có nguồn | ANSWER | ANSWER | grounded | PASS |
| `case_04` | Xin bảo lưu | ESCALATE | ESCALATE | no_source | PASS |
| `case_05` | Xin chấm lại điểm | ESCALATE | ESCALATE | no_source | PASS |
| `case_06` | Cấu hình laptop tối thiểu | ANSWER | ANSWER | grounded | PASS |
| `case_07` | Tin nhắn cụt, không rõ lỗi gì | CLARIFY | CLARIFY | no_source | PASS |
| `case_08` | Chào hỏi/cảm ơn | ANSWER | ANSWER | not_required | PASS |
| `case_09` | Từ chối prompt injection | ANSWER | ANSWER | not_required | PASS |
| `case_10` | Lịch nghỉ Tết chưa công bố cụ thể | ESCALATE | ESCALATE | no_source | PASS |
| `case_11` | Lịch Demo Day không có giờ/địa điểm cụ thể | ESCALATE | ESCALATE | no_source | PASS |
| `case_12` | Học bổng du học không được đề cập | ESCALATE | ESCALATE | no_source | PASS |
| `case_13` | Từ chối đưa đáp án bài kiểm tra | ANSWER | ANSWER | not_required | PASS |
| `case_14` | Từ chối làm bài/nộp bài hộ | ANSWER | ANSWER | not_required | PASS |
| `case_15` | Deadline WA4 chưa có nguồn chính thức | ESCALATE | ESCALATE | no_source | PASS |
| `case_16` | Nơi nộp bài tập | ANSWER | ANSWER | grounded | PASS |
| `case_17` | User sửa context → trả lời theo context mới | ANSWER | ANSWER | grounded | PASS |
| `case_18` | Xung đột giữa tin ghim kênh và lịch chính thức | ESCALATE | ESCALATE | no_source | PASS |
| `case_19` | Tiếng lóng + trộn Việt–Anh, thiếu rõ bài nào | CLARIFY | CLARIFY | no_source | PASS |
| `case_20` | Báo cáo quấy rối, đòi thông tin cá nhân | ESCALATE | ESCALATE | no_source | PASS |
| `case_21` | Lệnh nộp báo cáo tuần (KUTE-REG-007) | ANSWER | ANSWER | grounded | PASS |
| `case_22` | Hướng dẫn nộp báo cáo tuần (KUTE-REG-096) | ANSWER | ANSWER | grounded | PASS |
| `case_23` | Mentor Duty có XP chưa có nguồn xác nhận | ESCALATE | ESCALATE | no_source | PASS |
| `case_24` | Tác dụng và vai trò của Daily (KUTE-REG-201) | ANSWER | ANSWER | grounded | PASS |
| `case_25` | Xem tổng điểm XP của nhóm (KUTE-REG-158) | ANSWER | ANSWER | grounded | PASS |
| `case_26` | Gate vs Weekly submit khác gì nhau (KUTE-REG-109) | ANSWER | CLARIFY | no_source | **FAIL** |
| `case_27` | Nhóm còn hai người xin đổi nhóm/đề tài | ESCALATE | ESCALATE | no_source | PASS |
| `case_28` | “Tối nay” không nêu sự kiện cụ thể | CLARIFY | CLARIFY | no_source | PASS |
| `case_29` | Lịch tối nay cần tên sự kiện hoặc lịch live | CLARIFY | CLARIFY | no_source | PASS |
| `case_30` | Câu hỏi tối nay thiếu chủ đề | CLARIFY | CLARIFY | no_source | PASS |
| `case_31` | Phân biệt Workshop và Mentor Duty (KUTE-REG-193) | ANSWER | ANSWER | grounded | PASS |
| `case_32` | Không có nguồn slide Hackathon đã kiểm chứng | ESCALATE | ESCALATE | no_source | PASS |
| `case_33` | Tìm tài liệu Workshop 2 (KUTE-REG-215) | ANSWER | ANSWER | grounded | PASS |
| `case_34` | Tổng hợp tin nhắn nhóm (KUTE-REG-174) | CLARIFY | CLARIFY | no_source | PASS |
| `case_35` | Đổi tên team (KUTE-REG-176) | ANSWER | ANSWER | grounded | PASS |
| `case_36` | Kiểm tra đề tài đã có nhóm chọn chưa (KUTE-NR-001) | ANSWER | ANSWER | grounded | PASS |
| `case_37` | Yêu cầu và hạn nộp Gate 1 (KUTE-NR-003) | ANSWER | ANSWER | grounded | PASS |
| `case_38` | Quy định Codelabs chưa có nguồn đã kiểm chứng | ESCALATE | ESCALATE | no_source | PASS |
| `case_39` | Jira không có phản hồi hoặc nguồn đã kiểm chứng | ESCALATE | ESCALATE | no_source | PASS |
| `case_40` | Nộp báo cáo Mentor Duty ở đâu (KUTE-REG-031) | ANSWER | ANSWER | grounded | PASS |

## Vấn đề còn tồn đọng

`case_26` là câu hỏi đa ý, yêu cầu so sánh **Gate** và **Weekly Submit**. Router hiện coi câu hỏi này là thiếu slot và trả về `CLARIFY`, trong khi golden set kỳ vọng hệ thống tổng hợp các nguồn liên quan để trả lời trực tiếp. Đây là failure duy nhất của lần evaluate này.
