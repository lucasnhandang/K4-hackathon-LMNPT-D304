# Kết quả eval — CP3 (KUTE 20 + Handbook 20)

**Ngày chạy:** 2026-07-31

---

## Phần 1: KUTE-REG / KUTE-NR (20 Cases)

| Case | KUTE ID | Topic | Input | Route | Intent | Confidence | Grounding |
|---|---|---|---|---|---|---|---|
| 01 | KUTE-REG-007 | Weekly Report | lệnh báo cáo tuần | CLARIFY | ask_slash_command | 0.6 | no_source |
| 02 | KUTE-REG-096 | Weekly Report | hướng dẫn nộp báo cáo tuần | ANSWER | help | 0.9 | not_required |
| 03 | KUTE-REG-180 | XP / Mentor Duty | mentor duty có xp k | CLARIFY | ask_xp | 0.6 | no_source |
| 04 | KUTE-REG-201 | Daily Stand-up | daily có tác dụng và vai trò gì | ANSWER | search_fallback | 0.5 | grounded |
| 05 | KUTE-REG-158 | Team XP | Làm sao để xem tổng điểm kinh nghiệm hiện có của nhóm | CLARIFY | ask_xp | 0.6 | no_source |
| 06 | KUTE-REG-109 | Gate + Weekly Report | gate khi nào? và nộp weekly submit khi nào? | CLARIFY | ask_event_schedule | 0.6 | no_source |
| 07 | KUTE-REG-002 | Team / Đề tài | nhóm mình có 4 người nhưng có 2 bạn nghỉ học... | CLARIFY | ask_team_mentor | 0.6 | no_source |
| 08 | KUTE-REG-189 | Lịch tối nay | tối nay | ANSWER | search_fallback | 0.5 | grounded |
| 09 | KUTE-REG-198 | Lịch tối nay | tối nay có sự kiện gì ? | CLARIFY | ask_event_schedule | 0.6 | no_source |
| 10 | KUTE-REG-216 | Lịch tối nay | tối nay có gì không nhỉ | ANSWER | search_fallback | 0.5 | grounded |
| 11 | KUTE-REG-193 | Workshop vs Mentor Duty | tối thứ 5 là workshop hay là mentor duty vậy ? | ANSWER | ask_event_schedule | 0.6 | grounded |
| 12 | KUTE-REG-226 | Link slide hackathon | cho tôi link slide buổi hackathon hôm nay | ANSWER | search_fallback | 0.5 | grounded |
| 13 | KUTE-REG-215 | Tài liệu workshop | Tìm cho tôi tài liệu workshop 2 | ANSWER | ask_event_schedule | 0.6 | grounded |
| 14 | KUTE-REG-174 | Tổng hợp tin nhắn nhóm | tổng hợp tin nhắn thông tin trong nhóm từ 18h đến 20h25 phút | CLARIFY | ask_team_mentor | 0.6 | no_source |
| 15 | KUTE-REG-176 | Đổi tên team | nhóm mọi người đặt tên ở đâu nhỉ... | CLARIFY | ask_team_mentor | 0.6 | no_source |
| 16 | KUTE-NR-001 | Kiểm tra đề tài | cách kiểm tra 1 đề tài đã có nhóm nào chọn chưa | CLARIFY | ask_team_mentor | 0.6 | no_source |
| 17 | KUTE-NR-003 | Gate 1 | Gate 1 nộp những gì và thời gian nộp là bao giờ | ANSWER | ask_gate | 0.6 | grounded |
| 18 | KUTE-NR-004 | Codelabs cá nhân | Hi. về các bài codelabs trên lớp tôi làm một bài với nhóm... | ANSWER | greeting | 0.9 | not_required |
| 19 | KUTE-NR-005 | Tìm bài Jira | tìm cho mình bài setup jira... | ANSWER | search_fallback | 0.5 | grounded |
| 20 | KUTE-REG-031 | Nộp báo cáo mentor duty | nộp báo cáo buổi mentor duty ở đâu | CLARIFY | ask_team_mentor | 0.6 | no_source |

---

## Phần 2: Handbook 20 Test Cases

### Tổng quan

| Chỉ số | Giá trị |
|---|---|
| Tổng số case | 20 |
| ✅ Pass | 5 |
| ❌ Fail | 15 |
| Tỷ lệ pass | **25.0%** |

### Phân tích theo Route

| Route | Tổng | Pass | Tỷ lệ |
|---|---|---|---|
| ANSWER | 10 | 2 | 20% |
| CLARIFY | 3 | 2 | 67% |
| ESCALATE | 7 | 1 | 14% |

### Phân tích theo Lớp chỗ khó

| Lớp | Case | Tổng | Pass | Tỷ lệ |
|---|---|---|---|---|
| ① nguồn sự thật | 10, 11, 12, 18 | 4 | 0 | 0% |
| ② mơ hồ/thiếu thông tin | 3, 7, 19 | 3 | 2 | 67% |
| ③ ngoài phạm vi/thẩm quyền | 4, 5, 13, 14 | 4 | 0 | 0% |
| ④ đặc thù domain | 1, 15, 16 | 3 | 1 | 33% |

### Chi tiết từng Case

| Case | Route | Intent | Pass | Confidence | Grounding | Response preview |
|---|---|---|---|---|---|---|
| 1 | 🟢 ANSWER→ANSWER | 🔴 ask_attendance_policy | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác... |
| 2 | 🟢 ANSWER→ANSWER | 🔴 ask_online_learning_availability | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác... |
| 3 | 🟢 CLARIFY→CLARIFY | 🟢 ask_deadline | ✅ | 0.70 | no_source | Bạn đang hỏi deadline của bài nào? |
| 4 | 🔴 ESCALATE→CLARIFY | 🔴 request_leave_of_absence | ❌ | 0.60 | no_source | Bạn muốn biết XP của hoạt động nào? |
| 5 | 🔴 ESCALATE→CLARIFY | 🔴 request_grade_review | ❌ | 0.60 | no_source | Bạn muốn biết XP của hoạt động nào? |
| 6 | 🟢 ANSWER→ANSWER | 🔴 ask_laptop_requirements | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác... |
| 7 | 🔴 CLARIFY→ESCALATE | 🔴 ask_technical_help | ❌ | 1.00 | no_source | Mình sẽ chuyển yêu cầu này cho Mod... |
| 8 | 🟢 ANSWER→ANSWER | 🔴 acknowledge_thanks | ❌ | 0.90 | not_required | Không có gì! Nếu cần thêm thông tin... |
| 9 | 🟢 ANSWER→ANSWER | 🟢 reject_prompt_injection | ✅ | 1.00 | not_required | Mình không thể thực hiện yêu cầu này... |
| 10 | 🔴 ESCALATE→ANSWER | 🔴 ask_holiday_schedule | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác... |
| 11 | 🔴 ESCALATE→ANSWER | 🟢 ask_event_schedule | ❌ | 0.60 | grounded | Chào bạn! Mình xin giải đáp thông tin... |
| 12 | 🔴 ESCALATE→ANSWER | 🔴 ask_scholarship_info | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác... |
| 13 | 🟢 ANSWER→ANSWER | 🔴 reject_answer_key_request | ❌ | 0.50 | grounded | Mình chưa tìm thấy thông tin chính xác... |
| 14 | 🔴 ANSWER→CLARIFY | 🔴 reject_do_assignment_for_user | ❌ | 0.60 | no_source | Bạn đang hỏi deadline của bài nào? |
| 15 | 🟢 ANSWER→ANSWER | 🟢 ask_deadline | ✅ | 0.70 | grounded | Chào bạn! 😊 Mình chưa tìm thấy... |
| 16 | 🟢 ANSWER→ANSWER | 🔴 ask_submission_channel | ❌ | 0.50 | grounded | Chào bạn! Để nộp Weekly Assignment... |
| 17 | 🟢 ANSWER→ANSWER | 🔴 update_track_selection | ❌ | 0.50 | grounded | Chào bạn! Rất vui được hỗ trợ bạn... |
| 18 | 🔴 ESCALATE→ANSWER | 🔴 ask_deadline | ❌ | 0.60 | grounded | Mình chưa tìm thấy thông tin chính xác... |
| 19 | 🟢 CLARIFY→CLARIFY | 🟢 ask_deadline_flexibility | ✅ | 0.70 | no_source | Bạn đang hỏi deadline của bài nào? |
| 20 | 🟢 ESCALATE→ESCALATE | 🟢 report_harassment | ✅ | 0.80 | no_source | Mình sẽ chuyển yêu cầu này cho Mod... |

### Chi tiết các Case FAIL

#### Case 1: ANSWER · Quy định chuyên cần (lớp ④ đặc thù domain)
- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_attendance_policy` → **Actual:** `search_fallback` ❌
- **Response:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

#### Case 2: ANSWER · Có hỗ trợ học online không
- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_online_learning_availability` → **Actual:** `search_fallback` ❌
- **Response:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

#### Case 4: ESCALATE · Xin bảo lưu (lớp ③ ngoài phạm vi/thẩm quyền)
- **Expected route:** `ESCALATE` → **Actual:** `CLARIFY` ❌
- **Expected intent:** `request_leave_of_absence` → **Actual:** `ask_xp` ❌
- **Response:** Bạn muốn biết XP của hoạt động nào?

#### Case 5: ESCALATE · Xin chấm lại điểm (lớp ③ ngoài phạm vi/thẩm quyền)
- **Expected route:** `ESCALATE` → **Actual:** `CLARIFY` ❌
- **Expected intent:** `request_grade_review` → **Actual:** `ask_xp` ❌
- **Response:** Bạn muốn biết XP của hoạt động nào?

#### Case 6: ANSWER · Cấu hình laptop tối thiểu
- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_laptop_requirements` → **Actual:** `search_fallback` ❌
- **Response:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

#### Case 7: CLARIFY · Tin nhắn cụt, không rõ lỗi gì (lớp ② mơ hồ/thiếu thông tin)
- **Expected route:** `CLARIFY` → **Actual:** `ESCALATE` ❌
- **Expected intent:** `ask_technical_help` → **Actual:** `report_issue` ❌
- **Response:** Mình sẽ chuyển yêu cầu này cho Mod để xử lý.

#### Case 8: ANSWER · Chào hỏi/cảm ơn (không cần nguồn)
- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `acknowledge_thanks` → **Actual:** `thanks` ❌
- **Response:** Không có gì! Nếu cần thêm thông tin thì cứ hỏi mình nha 😊

#### Case 10: ESCALATE · Lịch nghỉ Tết chưa công bố cụ thể (lớp ① nguồn sự thật)
- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_holiday_schedule` → **Actual:** `search_fallback` ❌
- **Response:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

#### Case 11: ESCALATE · Lịch Demo Day không có trong sổ tay (lớp ① nguồn sự thật)
- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_event_schedule` → **Actual:** `ask_event_schedule` ✅
- **Response:** Chào bạn! Mình xin giải đáp thông tin về sự kiện Demo Day như sau: Thời gian: Sự kiện Demo Day sẽ diễn ra vào ngày 01/09/2026. 🗓️

#### Case 12: ESCALATE · Học bổng du học không được đề cập (lớp ① nguồn sự thật)
- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_scholarship_info` → **Actual:** `search_fallback` ❌
- **Response:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Bạn thử hỏi lại với từ khóa khác hoặc gửi ticket hỗ trợ nha! 😊

#### Case 13: ANSWER · Từ chối đưa đáp án bài kiểm tra (lớp ③ ngoài phạm vi/thẩm quyền)
- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `reject_answer_key_request` → **Actual:** `search_fallback` ❌
- **Response:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Để tạo ticket hỗ trợ, bạn có thể dùng lệnh: /ticket

#### Case 14: ANSWER · Từ chối làm bài/nộp bài hộ (lớp ③ ngoài phạm vi/thẩm quyền)
- **Expected route:** `ANSWER` → **Actual:** `CLARIFY` ❌
- **Expected intent:** `reject_do_assignment_for_user` → **Actual:** `ask_deadline` ❌
- **Response:** Bạn đang hỏi deadline của bài nào? (VD: Weekly Assignment, AI Log, Demo Day...)

#### Case 16: ANSWER · Nơi nộp bài tập (lớp ④ đặc thù domain)
- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `ask_submission_channel` → **Actual:** `search_fallback` ❌
- **Response:** Chào bạn! Để nộp Weekly Assignment, bạn hãy sử dụng lệnh /weekly submit ngay trên Discord nhé! 😊

#### Case 17: ANSWER · Correction — học viên sửa lại track đã chọn
- **Expected route:** `ANSWER` → **Actual:** `ANSWER` ✅
- **Expected intent:** `update_track_selection` → **Actual:** `search_fallback` ❌
- **Response:** Chào bạn! Rất vui được hỗ trợ bạn trong khóa học AI20K. 😊 Dựa trên thông tin về CP3 (thuộc track AI Application), đây là các yêu cầu bắt buộc...

#### Case 18: ESCALATE · Xung đột giữa tin ghim kênh và lịch chính thức (lớp ① nguồn sự thật)
- **Expected route:** `ESCALATE` → **Actual:** `ANSWER` ❌
- **Expected intent:** `ask_deadline` → **Actual:** `ask_slash_command` ❌
- **Response:** Mình chưa tìm thấy thông tin chính xác về câu hỏi này. Để gửi ticket hỗ trợ, bạn có thể sử dụng lệnh /ticket trên server nhé! 🎫
